# Borrowed from https://github.com/halilozercan/pget with modifications, Apache License 2.0
import logging
import threading
import time
import warnings
# noinspection PyPackageRequirements
from typing import BinaryIO

import requests

logger = logging.getLogger('hanlp')


class Chunk(object):
    INIT = 0
    DOWNLOADING = 1
    PAUSED = 2
    FINISHED = 3
    STOPPED = 4

    def __init__(self, downloader, url, file, start_byte=-1, end_byte=-1, number=-1,
                 high_speed=False, headers=None, max_retries=8):
        self.max_retries = max_retries
        self.url = url
        self.start_byte = int(start_byte)
        self.end_byte = int(end_byte)
        self.file: BinaryIO = file
        self.number = number
        self.downloader = downloader
        self.high_speed = high_speed
        if headers is None:
            headers = {}
        self.headers = dict(headers.items())

        self.__state = Chunk.INIT

        self.progress = 0
        self.total_length = 0
        if self.high_speed:
            self.download_iter_size = 1024 * 512  # Half a megabyte
        else:
            self.download_iter_size = 1024  # a kilobyte
        self.error = None

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.__state = Chunk.STOPPED

    def pause(self):
        if self.__state == Chunk.DOWNLOADING:
            self.__state = Chunk.PAUSED
        else:
            warnings.warn("Cannot pause at this stage")

    def resume(self):
        if self.__state == Chunk.PAUSED:
            logger.debug(self.__paused_request)
            self.thread = threading.Thread(target=self.run, kwargs={'r': self.__paused_request}, daemon=True)
            self.thread.start()
            logger.debug("chunk thread started")

    def run(self, r=None):
        self.__state = Chunk.DOWNLOADING
        retry = 0
        while retry < self.max_retries:
            try:
                if r is None:
                    if self.start_byte == -1 and self.end_byte == -1:
                        self.file.seek(0)  # We need to seek to the head if prev request failed
                        self.progress = 0  # as no range is supported
                        r = requests.get(self.url, stream=True, headers=self.headers)
                    else:
                        start_byte = self.start_byte + self.file.tell()
                        self.headers['Range'] = "bytes=" + str(start_byte) + "-" + str(self.end_byte)
                        if 'range' in self.headers:
                            del self.headers['range']
                        r = requests.get(self.url, stream=True, headers=self.headers)
                        content_length = r.headers.get("content-length")
                        if content_length is None:
                            if not self.total_length:
                                raise requests.exceptions.RequestException('No content-length header')
                        else:
                            self.total_length = int(content_length)

                break_flag = False
                for part in r.iter_content(chunk_size=self.download_iter_size):
                    if part and self.__state != Chunk.STOPPED:  # filter out keep-alive new chunks
                        self.file.write(part)
                        self.progress = self.file.tell()
                        # if retry == 0:
                        #     raise requests.exceptions.ConnectionError('debug')
                        if self.__state == Chunk.PAUSED:
                            self.__paused_request = r
                            break_flag = True
                            break
                    elif self.__state == Chunk.STOPPED:
                        break_flag = True
                        break

                if not break_flag:
                    if not (self.start_byte == -1 and self.end_byte == -1):
                        expected_size = self.end_byte - self.start_byte + 1
                        if expected_size != self.progress:
                            error = f'Chunk {self.number} downloaded size {self.file.tell()} mismatches with ' \
                                    f'expected size {expected_size}'
                            self.file.seek(0)  # Reset
                            self.progress = 0
                            raise requests.exceptions.RequestException(error)
                    self.__state = Chunk.FINISHED
                break
            except requests.exceptions.RequestException as e:
                r = None
                retry += 1
                # logger.warning(f'Chunk#{self.number} Retry {retry}', exc_info=e)
                if retry == self.max_retries:
                    if hasattr(e, 'args') and isinstance(e.args, tuple) and e.args and isinstance(e.args[0], str):
                        import traceback
                        e.args = (e.args[0] + traceback.format_exc(),) + e.args[1:]
                        self.error = e
                else:
                    time.sleep(1)
                # print(f'retry {retry}')

    def is_finished(self):
        return self.__state == Chunk.FINISHED
