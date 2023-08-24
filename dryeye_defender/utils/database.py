"""Database class to interact with SQLite3 database"""
import logging
import sqlite3
from pathlib import Path
from typing import Optional, List, Any
from datetime import datetime, timezone

LOGGER = logging.getLogger(__name__)


class BlinkHistory:
    """Database class to interact with SQLite3 database"""

    def __init__(self,
                 db_path: Optional[Path] = None,
                 db_con: Optional[sqlite3.Connection] = None) -> None:
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
            if not db_path:
                raise RuntimeError("db_path must be provided if db_con is not")
            self.db_con = self._create_connection(db_path)

    @staticmethod
    def _create_connection(db_path: Path) -> sqlite3.Connection:
        """Create the SQLite3 connection

        :param db_path: Path to sqlite3 database on disk
        :return: connection to the database
        """
        if get_sqlite3_thread_safety() == 3:
            check_same_thread = False
        else:
            check_same_thread = True
        return sqlite3.connect(db_path, check_same_thread=check_same_thread)

    def _display_all_rows(self) -> List[Any]:
        """A debugging function to display all rows of DB up to max of 100"""
        with self.db_con:
            result = self.db_con.execute("SELECT * FROM blink_history LIMIT 100").fetchall()
        return result

    def query_raw_blink_history_no_grouping(self, since: float) \
            -> dict[str, List[float | int]]:
        """Fetch the last blink history (blink_marker) from since provided timestamp,
        with returning the value 1 to represent a blink occurs

        :param since: Only consider timestamps after this, a unix timestamp
        :return: list of tuples, each is a utc datetime string e.g.
         [('2023-01-01 12:59:00', 1), ('2023-01-01 13:00:14', 1),] where 1 is always the value
         for each blink that occured at that timestamp.
        """
        with self.db_con:
            cursor = self.db_con.execute(
                """
                SELECT blink_time, 1
                FROM blink_history
                WHERE blink_marker = 1 AND blink_time >= ?
                ORDER BY blink_time ASC;
                """, (since,))
            rows = cursor.fetchall()
        x_axis = [i[0] for i in rows]
        y_axis = [i[1] for i in rows]
        return {"timestamps": x_axis, "values": y_axis}

    def query_blink_history_groupby_minute_since(self, since: float) \
            -> dict[str, List[float | int]]:
        """Fetch the last blink history (blink_marker) from since provided timestamp,
        groupby minutes

        :param since: Only consider timestamps after this, a unix timestamp
        :return: list of tuples, each is a utc datetime string e.g.
         [('2023-01-01 12:59', 2), ('2023-01-01 13:00', 3), ('2023-01-01 13:01', 5), ] followed by
         the number of blinks that minute bin.
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
        x_axis = [datetime.strptime(i[0], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp()
                  for i in rows]
        y_axis = [i[1] for i in rows]
        return {"timestamps": x_axis, "values": y_axis}

    def query_blink_history_groupby_hour_since(self, since: float) -> dict[str, List[float | int]]:
        """Fetch the last blink history (blink_marker) from since provided timestamp,
        groupby minutes as a subquery, then aggregate that as a mean over hourly bins.

        :param since: Only consider timestamps after this, a unix timestamp
        :return: list of tuples, each is a utc datetime string e.g.
         [('2023-01-01 12:00', 2.1), ('2023-01-01 13:00', 3.5), ('2023-01-01 14:00', 5.2),]
          followed by the mean number of blinks that hourly bin, averaged over minute bins.
        """
        with self.db_con:
            cursor = self.db_con.execute(
                """SELECT strftime('%Y-%m-%d %H:00', minute_utc) AS hour_utc,
               AVG(events_per_minute) AS mean_events_per_hour
        FROM (
            SELECT strftime('%Y-%m-%d %H:%M', blink_time, 'unixepoch') AS minute_utc,
                   COUNT(*) AS events_per_minute
            FROM blink_history
            WHERE blink_marker = 1 AND blink_time >= ?
            GROUP BY minute_utc
        ) AS subquery
        GROUP BY hour_utc
        ORDER BY hour_utc ASC;""", (since,))
            rows = cursor.fetchall()
        x_axis = [datetime.strptime(i[0], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp()
                  for i in rows]
        y_axis = [i[1] for i in rows]
        return {"timestamps": x_axis, "values": y_axis}

    def query_blink_history_groupby_day_since(self, since: float) -> dict[str, List[float | int]]:
        """Fetch the last blink history (blink_marker) from since provided timestamp,
        groupby minutes as a subquery, then aggregate that as a mean over daily bins.

        :param since: Only consider timestamps after this, a unix timestamp
        :return: list of tuples, each is a utc datetime string e.g.
         [('2023-01-01 00:00', 2.1), ('2023-01-02 00:00', 3.5), ('2023-01-03 00:00', 5.2),]
          followed by the mean number of blinks that daily bin, averaged over minute bins.
        """
        with self.db_con:
            cursor = self.db_con.execute(
                """SELECT strftime('%Y-%m-%d 00:00', minute_utc) AS day_utc,
               AVG(events_per_minute) AS mean_events_per_hour
        FROM (
            SELECT strftime('%Y-%m-%d %H:%M', blink_time, 'unixepoch') AS minute_utc,
                   COUNT(*) AS events_per_minute
            FROM blink_history
            WHERE blink_marker = 1 AND blink_time >= ?
            GROUP BY minute_utc
        ) AS subquery
        GROUP BY day_utc
        ORDER BY day_utc ASC;""", (since,))
            rows = cursor.fetchall()
        x_axis = [datetime.strptime(i[0], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp()
                  for i in rows]
        y_axis = [i[1] for i in rows]
        return {"timestamps": x_axis, "values": y_axis}


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
