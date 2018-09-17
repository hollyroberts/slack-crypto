import argparse

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
parser.add_argument("--disable-stdout", "-dso", action="store_true",
                    help="Disable log messages lower than ERROR from appearing in stdout")
parser.add_argument("--disable-stderr", "-dse", action="store_true",
                    help="Disable error messages from appearing in stdout (requires --disable-stdout to also be set)")
parser.add_argument("--max-days", "-md", type=int, default=10,
                    help="Maximum number of days allowed to retrieve")
args = parser.parse_args()

# Setup and run
LogSetup.setup(not args.disable_stdout, not args.disable_stderr, args.log_file, LOG_LOC)

CommandHandler.SIGNING_SECRET = getattr(args, "signing secret")
CommandHandler.MAX_DAYS = args.max_days
CommandHandler.run(args.port)
