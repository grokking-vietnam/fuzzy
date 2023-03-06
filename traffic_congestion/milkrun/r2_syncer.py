import os
import sqlite3
from typing import List


def get_objects(from_side: str) -> List[str]:
    """"""
    if from_side == "request":
        with sqlite3.connect("objects.db") as con:
            cur = con.cursor()
            return cur.execute("SELECT * FROM objects WHERE active IS TRUE").fetchall()


def clean_up():
    """"""
    1


if __name__ == "__main__":
    # Init the objects.db database
    if not os.path.exists("objects.db"):
        with sqlite3.connect("objects.db") as con:
            cur = con.cursor()
            cur.execute(
                "CREATE TABLE objects(id INTEGER PRIMARY KEY, src TEXT, dst TEXT, active INTEGER)"
            )
            con.commit()
