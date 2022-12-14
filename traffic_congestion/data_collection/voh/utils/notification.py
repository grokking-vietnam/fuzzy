import requests
import sys
from pathlib import Path

sys.path.append(Path(__file__).parent.parent.absolute().as_posix())  # Add voh/ to root path

from configs.voh import VohConfiguration


def telegram_bot_send_message(bot_message):

    bot_token = VohConfiguration.BOT_TOKEN
    bot_chatID = VohConfiguration.BOT_CHATID

    send_text = 'https://api.telegram.org/bot' + bot_token + \
        '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message

    response = requests.get(send_text)

    return response.json()


if __name__ == "__main__":
    test = telegram_bot_send_message("Test message.")

    
    