"""Database class to interact with SQLite3 database"""
import logging
import sqlite3
from pathlib import Path
from typing import List

import pandas as pd

from blinkdetector.utils.return_dict import ReturnDict

LOGGER = logging.getLogger(__name__)


class BlinkHistory:
    """Database class to interact with SQLite3 database"""

    def __init__(self, db_path: Path) -> None:
        """Create the SQLite3 Database and table if not exist

        :param db_path: Path to were to store the database
        """
        self._db_path = db_path
        self.db_con = self._create_connection()

    def _create_connection(self) -> sqlite3.Connection:
        """Create the SQLite3 connection

        :return: connection to the database
        """
        if get_sqlite3_thread_safety() == 3:
            check_same_thread = False
        else:
            check_same_thread = True
        return sqlite3.connect(self._db_path, check_same_thread=check_same_thread)

    def get_blink_history_count(self) -> int:
        """Fetch the count of blink history records in SQLite DB"""
        with self.db_con:
            count = int(self.db_con.execute("SELECT COUNT(*) FROM blink_history").fetchone()[0])
        return count

    def fetch_last_n_blink(self, n_last_blink: int) -> List:
        """Fetch the last 'n_last_blink' records from the SQLite DB and return as a List

        :param n_last_blink: number of blink to fetch, starting from the most recent
        :return: list of the n last blink in ascending order
        """
        with self.db_con:
            cursor = self.db_con.execute(
                """SELECT * FROM blink_history
                ORDER BY frame_number DESC LIMIT (?)""",
                (n_last_blink,))
            rows = cursor.fetchall()
        return rows

    def fetch_last_n_blink(self, n_last_blink: int) -> List:
        """Fetch the last 'n_last_blink' records from the SQLite DB and return as a List

        :param n_last_blink: number of blink to fetch, starting from the most recent
        :return: list of the n last blink in ascending order
        """
        with self.db_con:
            cursor = self.db_con.execute(
                """
                SELECT strftime('%Y-%m-%d %H:%M', blink_time, 'unixepoch') AS minute,
                       COUNT(*) / 60 AS events_per_minute
                FROM blink_history
                WHERE blink_value = 1
                GROUP BY minute;""",
                (n_last_blink,))
            rows = cursor.fetchall()
        return rows

def get_sqlite3_thread_safety() -> int:
    """Get the SQLite3 thread safety value

    :return: thread safety value
    """
    sqlite_threadsafe2python_dbapi = {0: 0, 2: 1, 1: 3}
    conn = sqlite3.connect(":memory:")
    threadsafety = conn.execute(
        """
    select * from pragma_compile_options
    where compile_options like 'THREADSAFE=%'
    """
    ).fetchone()[0]
    conn.close()

    threadsafety_value = int(threadsafety.split("=")[1])

    return sqlite_threadsafe2python_dbapi[threadsafety_value]
