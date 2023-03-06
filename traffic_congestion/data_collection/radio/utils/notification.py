import sys
from pathlib import Path

import requests

sys.path.append(
    Path(__file__).parent.parent.absolute().as_posix()
)  # Add radio/ to root path

from configs import TeleBotConfiguration


def telebot_send_message(bot_message: str):
    bot_token = TeleBotConfiguration.BOT_TOKEN
    bot_chatID = TeleBotConfiguration.BOT_CHATID

    send_text = (
        "https://api.telegram.org/bot"
        + bot_token
        + "/sendMessage?chat_id="
        + bot_chatID
        + "&parse_mode=Markdown&text="
        + bot_message
    )
    response = requests.get(send_text)
    return response.json()


if __name__ == "__main__":
    test = telebot_send_message("Test message.")
