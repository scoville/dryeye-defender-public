"""Database class to interact with SQLite3 database"""
import logging
import sqlite3
from pathlib import Path
from typing import List

from typing import Optional

LOGGER = logging.getLogger(__name__)


class BlinkHistory:
    """Database class to interact with SQLite3 database"""

    def __init__(self, db_path: Optional[Path] = None, db_con: bool = None) -> None:
        """Create the SQLite3 Database and table if not exist

        :param db_path: if db_con not provided, provide a path to were to store the database
        :param db_con: Optionally, a direct connection object to a database can be provided
        instead of the path to the database itself, useful for testing.
        """
        if (not db_path) and (not db_con):
            raise RuntimeError("Either db_path or db_con must be provided")

        if db_con:
            self.db_con = db_con
        else:
            self.db_con = self._create_connection(db_path)

    def _create_connection(self, db_path) -> sqlite3.Connection:
        """Create the SQLite3 connection

        :param db_path: Path to sqlite3 database on disk
        :return: connection to the database
        """
        if get_sqlite3_thread_safety() == 3:
            check_same_thread = False
        else:
            check_same_thread = True
        return sqlite3.connect(db_path, check_same_thread=check_same_thread)

    def _display_all_rows(self) -> int:
        """A debugging function to display all rows of DB up to max of 100"""
        with self.db_con:
            result = self.db_con.execute("SELECT * FROM blink_history LIMIT 100").fetchall()
        return result

    def query_blink_history_groupby_minute_since(self, since: float) -> List:
        """Fetch the last blink history (blink_marker) from since provided timestamp,
        groupby minutes

        :param since: Only consider timestamps after this, a unix timestamp
        :return: list of the n last blink in ascending order (oldest first)
        """
        with self.db_con:
            cursor = self.db_con.execute(
                """
                SELECT strftime('%Y-%m-%d %H:%M', blink_time, 'unixepoch') AS minute_utc,
                       COUNT(*) AS events_per_minute
                FROM blink_history
                WHERE blink_marker = 1 AND blink_time >= ?
                GROUP BY minute_utc ORDER BY minute_utc ASC;
                """, (since,))
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
