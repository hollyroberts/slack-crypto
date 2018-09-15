import logging
from datetime import datetime
import sys
import os


class LogSetup:
    @staticmethod
    def setup(stdout: bool, file: bool, location: str):
        # Basic setup
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        log_formatter.default_msec_format = '%s.%03d'

        # Setup standard output and file output logging
        if stdout:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(log_formatter)
            logger.addHandler(console_handler)
            
        if file:
            if not os.path.isdir(location):
                os.makedirs(location, exist_ok=True)

            file_handler = logging.FileHandler(f"{location}/" + datetime.now().strftime("%Y-%m-%d %H;%M;%S") + ".txt")
            file_handler.setFormatter(log_formatter)
            logger.addHandler(file_handler)

        # Override default handling of uncaught exceptions (program crash)
        sys.excepthook = LogSetup.handle_top_exception

        logger.info("Logging initialised")

    # noinspection PyUnusedLocal
    @staticmethod
    def handle_top_exception(exctype, value, traceback):
        logging.exception("An unhandled exception occurred", exc_info=(exctype, value, traceback))
