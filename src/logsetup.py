import logging
from datetime import datetime
import sys
import os

"""Custom formatter that indents newlines the same amount as the first line
Requires %(message)s to be the last thing"""
class CustMultiLineFormatter(logging.Formatter):
    """Adapted from logging.Formatter"""
    def format(self, record: logging.LogRecord):
        # Change it so we save the initial string (without extras), and are not reliant on implementation
        record.message = record.getMessage()
        msg = record.message
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        initial_str = self.formatMessage(record)
        s = initial_str

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        if record.stack_info:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + self.formatStack(record.stack_info)

        # Replace newlines with indentation
        header_length = 0
        if initial_str.endswith(msg):
            header_length = len(initial_str) - len(msg)
        replace_str = '\n' + ' ' * header_length
        if header_length >= 2:
            replace_str = replace_str[:-2] + '| '
        s = s.replace('\n', replace_str)

        return s

class LogSetup:
    @staticmethod
    def setup(stdout: bool, file: bool, location: str):
        # Basic setup
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        log_formatter = CustMultiLineFormatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s")
        log_formatter.default_msec_format = '%s.%03d'

        # Disable requests and urllib3 library (blacklist). If more issues come up then I'll have to refactor
        logging.getLogger("requests").setLevel(logging.INFO)
        logging.getLogger("urllib3").setLevel(logging.INFO)

        # Setup standard output and file output logging
        if stdout:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(log_formatter)
            console_handler.setLevel(logging.DEBUG)
            logger.addHandler(console_handler)
            
        if file:
            if not os.path.isdir(location):
                os.makedirs(location, exist_ok=True)

            file_handler = logging.FileHandler(f"{location}/" + datetime.now().strftime("%Y-%m-%d %H;%M;%S") + ".txt")
            file_handler.setFormatter(log_formatter)
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)

        # Override default handling of uncaught exceptions (program crash)
        sys.excepthook = LogSetup.handle_top_exception

        logger.info("Logging initialised")

    # noinspection PyUnusedLocal
    @staticmethod
    def handle_top_exception(exctype, value, traceback):
        logging.exception("An unhandled exception occurred", exc_info=(exctype, value, traceback))
