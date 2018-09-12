import logging
from datetime import datetime
import sys
import os


class LogSetup:
    @staticmethod
    def setup(stdout: bool, file: bool, location: str):
        logger = logging.getLogger()
        log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

        if stdout:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(log_formatter)
            logger.addHandler(console_handler)
            
        if file:
            if not os.path.isdir(location):
                os.mkdir(location)

            file_handler = logging.FileHandler(f"{location}/" + datetime.now().strftime("%Y-%m-%d %H;%M;%S") + ".txt")
            file_handler.setFormatter(log_formatter)
            logger.addHandler(file_handler)

        logger.info("Logging initialised")
