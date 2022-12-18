import os

from dotenv import load_dotenv

load_dotenv()


class TeleBotConfiguration:
    BOT_TOKEN = os.environ["BOT_TOKEN"]
    BOT_CHATID = os.environ["BOT_CHATID"]

    assert BOT_TOKEN is not None, "Not found BOT_TOKEN."
    assert BOT_CHATID is not None, "Not found BOT_CHATID."
