# Borrowed from https://github.com/halilozercan/pget with modifications, Apache License 2.0
import tempfile
import threading
import time
import warnings
# noinspection PyPackageRequirements
from typing import List, Dict
import logging
from urllib.error import HTTPError

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from .chunk import Chunk

logger = logging.getLogger('hanlp')


def readable_bytes(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1000.0:
            return "{:5.1f} {}{}".format(num, unit, suffix)
        num /= 1024.0
    return "{:5.1f} {}{}".format(num, 'Yi', suffix)


class Downloader(object):
    # States
    INIT = 0
    DOWNLOADING = 1
    PAUSED = 2
    MERGING = 3
    FINISHED = 4
    STOPPED = 5

    def __init__(self, url, file_name, chunk_count, high_speed=False, headers: Dict[str, str] = None):
        self.url = url
        self.file_name = file_name
        self.chunk_count = chunk_count
        self.high_speed = high_speed
        if headers is None:
            headers = {}
        self.headers = headers

        self.total_length = 0
        self.total_downloaded = 0
        self.total_merged = 0
        self.__chunks: List[Chunk] = []

        self.last_total = 0
        self.speed = 0
        self.readable_speed = readable_bytes(self.speed)

        self.__state = Downloader.INIT
        self.__subs = []

        self.__progress_lock = threading.Lock()

        self.__async = True
        self.thread = threading.Thread(target=self.run)

    # This function registers a callback.
    # sub_callable: must take at least one argument. (Downloader)
    # rate: defines the amount of kilobytes that should be downloaded in
    #   a second at least to fire an update for subscriber.
    def subscribe(self, sub_callable, rate=1):
        self.__subs.append([sub_callable, rate])

    def notify_subs(self, force=False):
        if force:
            self.total_downloaded = 0
            for chunk in self.__chunks:
                self.total_downloaded += chunk.progress

            self.speed = self.total_downloaded - self.last_total
            self.readable_speed = readable_bytes(self.speed)
            self.last_total = self.total_downloaded
        for sub in self.__subs:
            if self.speed > (sub[1] * 1024) or force:
                sub[0](self)

    def get_state(self):
        return self.__state

    def speed_func(self):
        while self.__state != Downloader.STOPPED and self.__state != Downloader.MERGING:
            self.total_downloaded = 0
            for chunk in self.__chunks:
                self.total_downloaded += chunk.progress

            self.speed = self.total_downloaded - self.last_total
            self.readable_speed = readable_bytes(self.speed)
            self.last_total = self.total_downloaded

            self.notify_subs()
            time.sleep(1)

    def stop(self):
        for chunk in self.__chunks:
            chunk.stop()
        self.__state = Downloader.STOPPED

    def start(self):
        if self.__state != Downloader.INIT:
            raise RuntimeError('Download has already been started.')

        self.thread.start()

    def start_sync(self):
        if self.__state != Downloader.INIT:
            raise RuntimeError('Download has already been started.')

        self.run()

    def pause(self):
        if self.__state == Downloader.INIT:
            warnings.warn("Download has not been started yet.")
            return

        for chunk in self.__chunks:
            chunk.pause()

        self.__state = Downloader.PAUSED

    def resume(self):
        if self.__state != Downloader.PAUSED:
            warnings.warn("Resume is not applicable at this stage.")
            logger.warn("Resume is not applicable at this stage.")
            return
        for chunk in self.__chunks:
            chunk.resume()

        self.__state = Downloader.DOWNLOADING

    def wait_for_finish(self):
        if self.__async:
            while self.thread.is_alive():
                continue
            self.thread.join()
        else:
            warnings.warn('Downloader was set to run as synchronous. This function will not work')

    def run(self):
        self.__state = Downloader.DOWNLOADING

        s = requests.Session()
        adapter = HTTPAdapter(max_retries=Retry(total=8, backoff_factor=0.1))
        s.mount('http://', adapter)
        s.mount('https://', adapter)

        r = s.get(self.url, stream=True, headers=self.headers)
        if r.status_code != 200:
            raise HTTPError(self.url, r.status_code, f'Internet error', r.headers, None)
        try:
            self.total_length = int(r.headers.get('Content-Length'))
            if r.headers.get('Accept-Ranges') != 'bytes':
                raise NotImplemented('URL does not support ranged requests.')
        except:
            self.chunk_count = 0
            # warnings.warn(
            #     'This url does not support parallel downloading. Normal download will continue.',
            #     RuntimeWarning)

        self.url = r.url
        if self.chunk_count == 0 or self.total_length < self.chunk_count:
            chunk_file = tempfile.TemporaryFile()
            new_chunk = Chunk(self, self.url, file=chunk_file, high_speed=self.high_speed, headers=self.headers)
            self.__chunks.append(new_chunk)
            new_chunk.start()
        else:
            chunk_size = self.total_length // self.chunk_count

            for chunk_number in range(self.chunk_count):
                chunk_file = tempfile.TemporaryFile()

                if chunk_number != self.chunk_count - 1:
                    new_chunk = Chunk(
                        self, self.url, chunk_file,
                        start_byte=chunk_number * chunk_size,
                        end_byte=((chunk_number + 1) * chunk_size) - 1,
                        number=chunk_number,
                        high_speed=self.high_speed,
                        headers=self.headers)
                else:
                    new_chunk = Chunk(
                        self, self.url, chunk_file,
                        start_byte=chunk_number * chunk_size,
                        end_byte=self.total_length - 1,
                        number=chunk_number,
                        high_speed=self.high_speed,
                        headers=self.headers)

                self.__chunks.append(new_chunk)
                new_chunk.start()

        speed_thread = threading.Thread(target=self.speed_func)
        speed_thread.start()

        try:
            while any(chunk.thread.is_alive() for chunk in self.__chunks):
                for chunk in self.__chunks:
                    chunk.thread.join(1)
        except KeyboardInterrupt as e:
            self.stop()
            raise e

        for chunk in self.__chunks:
            if chunk.error:
                self.__state = Downloader.STOPPED
                raise chunk.error

        if self.__state == Downloader.STOPPED:
            return

        # Forcefully update subscribers for last time.
        self.notify_subs(True)

        self.__state = Downloader.MERGING
        speed_thread.join()

        # time to put together all parts
        with open(self.file_name, 'wb') as fout:
            for chunk in self.__chunks:
                # Go to first byte of temporary file
                chunk.file.seek(0)
                while True:
                    readbytes = chunk.file.read(1024 * 1024 * 10)
                    self.total_merged += len(readbytes)
                    if readbytes:
                        fout.write(readbytes)
                        self.notify_subs(force=True)
                    else:
                        break
                chunk.file.close()
            if self.total_length and fout.tell() != self.total_length:
                raise IOError('Failed to merge files due to mismatch size')
            self.notify_subs(force=True)  # Tell the callback merging is done

        self.__state = Downloader.FINISHED
