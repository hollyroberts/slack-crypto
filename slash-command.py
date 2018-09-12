import argparse
import logging
from datetime import datetime
import sys
import os

from src.server import CommandHandler

# region Argparse
parser = argparse.ArgumentParser(description="Post messages to slack if a cryptocurrency has changed price significantly")
parser.add_argument("signing secret",
                    help="Slack signing secret")
parser.add_argument("--port", "-p", default=80, type=int,
                    help="Web server port to run on")
parser.add_argument("--log-file", "-lf", action="store_true",
                    help="Output log files to /log folder (name is time that program was started at)")
args = parser.parse_args()

# region Logging
logger = logging.getLogger()
logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)

if args.log_file:
    if not os.path.isdir("log"):
        os.mkdir("log")

    fileHandler = logging.FileHandler("log/" + datetime.now().strftime("%Y-%m-%d %H;%M;%S") + ".txt")
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

# Run server
CommandHandler.SIGNING_SECRET = getattr(args, "signing secret")
CommandHandler.run(args.port)
