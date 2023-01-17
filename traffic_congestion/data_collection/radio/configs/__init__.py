import os

from dotenv import load_dotenv

load_dotenv()


class TeleBotConfiguration:
    BOT_TOKEN = os.environ["BOT_TOKEN"]
    BOT_CHATID = os.environ["BOT_CHATID"]

    assert BOT_TOKEN is not None, "Not found BOT_TOKEN."
    assert BOT_CHATID is not None, "Not found BOT_CHATID."


class S3Configuration:
    AWS_SEAWEEDFS_KEY_ID = os.environ["AWS_SEAWEEDFS_KEY_ID"]
    AWS_SEAWEEDFS_SECRET = os.environ["AWS_SEAWEEDFS_SECRET"]
    AWS_KEY_ID = os.environ["AWS_KEY_ID"]
    AWS_SECRET = os.environ["AWS_SECRET"]

    assert AWS_SEAWEEDFS_KEY_ID is not None, "Not found AWS_SEAWEEDFS_KEY_ID."
    assert AWS_SEAWEEDFS_SECRET is not None, "Not found AWS_SEAWEEDFS_SECRET."
    assert AWS_KEY_ID is not None, "Not found AWS_KEY_ID."
    assert AWS_SECRET is not None, "Not found AWS_SECRET."
