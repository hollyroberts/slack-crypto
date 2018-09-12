import argparse
from src.server import CommandHandler

# region Argparse
parser = argparse.ArgumentParser(description="Post messages to slack if a cryptocurrency has changed price significantly")
parser.add_argument("signing secret",
                    help="Slack signing secret")
parser.add_argument("--port", "-p", default=80, type=int,
                    help="Web server port to run on")
args = parser.parse_args()
# endregion

CommandHandler.SIGNING_SECRET = getattr(args, "signing secret")
CommandHandler.run(args.port)
