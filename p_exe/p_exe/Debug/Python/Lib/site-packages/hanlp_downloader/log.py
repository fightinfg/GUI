import logging
import sys

from hanlp_downloader import Downloader, term, down

logger = logging.getLogger(__name__)
_root_handler = None


def setup_logging(enabled=True, level=logging.DEBUG):
    global _root_handler
    if _root_handler is not None and _root_handler in logging.root.handler:
        logging.root.removeHandler(_root_handler)
    logging.root.setLevel(logging.NOTSET)
    _root_handler = logging.StreamHandler() if enabled else logging.NullHandler()
    _root_handler.addFilter(logging.Filter("pget"))
    _root_handler.setLevel(level)

    logging.root.addHandler(_root_handler)


def human_time_delta(days, hours, minutes, seconds, delimiter=' ') -> str:
    units = locals().copy()
    units.pop('delimiter')
    non_zero = False
    result = []
    for key, val in sorted(units.items()):
        append = False
        if non_zero:
            append = True
        elif val:
            non_zero = True
            append = True
        if append:
            result.append('{:2} {}'.format(val, key[0]))
    if not non_zero:
        return ' 0 s'
    return delimiter.join(result)


def seconds_to_time_delta(seconds):
    seconds = round(seconds)
    days = seconds // 86400
    hours = seconds // 3600 % 24
    minutes = seconds // 60 % 60
    seconds = seconds % 60
    return days, hours, minutes, seconds


def report_time_delta(seconds, human=True):
    days, hours, minutes, seconds = seconds_to_time_delta(seconds)
    if human:
        return human_time_delta(days, hours, minutes, seconds)
    return days, hours, minutes, seconds


class DownloadCallback(object):
    def __init__(self, show_header=True, out=sys.stderr) -> None:
        super().__init__()
        self.show_header = show_header
        self.out = out

    def __call__(self, downloader: Downloader):
        if self.show_header:
            self.out.write(f"Downloading {downloader.url} to {downloader.file_name}\n")
            self.show_header = False

        term_width, term_height = term.getTerminalSize()
        if term_width >= 100:
            term_width = 100

        if downloader.get_state() == Downloader.DOWNLOADING:
            written_update = "{:3}% {} {}/s ETA: {}"
            percent_downloaded = int(100 * (float(downloader.total_downloaded) / downloader.total_length)) \
                if downloader.total_length else -1
            written_update = written_update.format(
                percent_downloaded,
                down.readable_bytes(downloader.total_length),
                downloader.readable_speed,
                report_time_delta((downloader.total_length - downloader.total_downloaded) // max(1, downloader.speed))
                if downloader.total_length else 'Unknown'
            )

            if len(written_update) < term_width * 3 / 4:
                fill_in_area = term_width - (len(written_update) + 3)
                done = int(fill_in_area * percent_downloaded / 100) * '='
                remaining = (fill_in_area - len(done)) * ' '
                written_update += ' [{}{}]'.format(done, remaining)
            else:
                written_update += (' ' * (term_width - len(written_update)))

            if downloader.total_downloaded == downloader.total_length:
                written_update += '\n'

            self.out.write('\r' + written_update)
            self.out.flush()
        elif downloader.get_state() == Downloader.MERGING:
            written_update = "[Merging {:5}/{:5}]".format(down.readable_bytes(downloader.total_merged),
                                                          down.readable_bytes(downloader.total_length))
            if len(written_update) < term_width * 3 / 4:
                fill_in_area = term_width - (len(written_update) + 3)
                done = int((downloader.total_merged * fill_in_area) / downloader.total_length) * '=' \
                    if downloader.total_length else 'Unknown'
                remaining = (fill_in_area - len(done)) * ' '
                written_update += ' [{}{}]'.format(done, remaining)
            else:
                written_update += (' ' * (term_width - len(written_update)))

            if downloader.total_merged == downloader.total_length:
                written_update = ' ' * term_width + '\r'

            self.out.write('\r' + written_update)
            self.out.flush()
