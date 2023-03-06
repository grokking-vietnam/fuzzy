import sys
import time
from pathlib import Path

sys.path.append(
    Path(__file__).parent.parent.absolute().as_posix()
)  # Add radio/ to root path

from utils.notification import telebot_send_message


def test_send_warning():
    try:
        # Fake processing time
        time.sleep(5)

        # Silmulate an exception
        a = 1 / 0

    except ZeroDivisionError as e:
        telebot_send_message(f"WARNING: {type(e).__name__}!")
