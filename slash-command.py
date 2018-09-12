import argparse
import logging

from src.logsetup import LogSetup
from src.server import CommandHandler

# Constants
LOG_LOC = "log_slash_command_server"

# Argparse
parser = argparse.ArgumentParser(description="Post messages to slack if a cryptocurrency has changed price significantly")
parser.add_argument("signing secret",
                    help="Slack signing secret")
parser.add_argument("--port", "-p", default=80, type=int,
                    help="Web server port to run on")
parser.add_argument("--log-file", "-lf", action="store_true",
                    help=f"Output logs into files in /{LOG_LOC}")
parser.add_argument("--disable-stdout", "-dstd", action="store_true",
                    help="Disable logging output to stdout")
args = parser.parse_args()

# Setup and run
LogSetup.setup(not args.disable_stdout, args.log_file, LOG_LOC)

CommandHandler.SIGNING_SECRET = getattr(args, "signing secret")
CommandHandler.run(args.port)
