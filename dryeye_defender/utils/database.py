"""Database class to interact with SQLite3 database

A similar class exists in the submodule for limited use without GUI,
but this is the only class that should be used for the dryeye defender software.
"""
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Any

from blinkdetector.utils.database import EventTypes, BlinkHistory

LOGGER = logging.getLogger(__name__)


class BlinkHistoryDryEyeDefender(BlinkHistory):
    """Database class to interact with SQLite3 database"""

    def __init__(self,
                 db_path: Optional[Path] = None,
                 db_con: Optional[sqlite3.Connection] = None) -> None:
        """Create the SQLite3 Database and table if not exist

        :param db_path: if db_con not provided, provide a path to where to store the database
        :param db_con: Optionally, a direct connection object to a database can be provided
        instead of the path to the database itself, useful for testing.
        """
        super().__init__(db_path, db_con)

    def _display_all_rows(self) -> Any:
        """A debugging function to display all rows of DB up to max of 100"""
        with self.db_con:
            result = self.db_con.execute("SELECT * FROM blink_history LIMIT 100").fetchall()
        return result

    def query_raw_blink_history_no_grouping(self, since: float) \
            -> dict[str, List[float | int]]:
        """Fetch the last blink history (blink_marker) from since provided timestamp,
        with returning the value 1 to represent a blink occurs

        :param since: Only consider timestamps after this, a unix timestamp
        :return: list of tuples, each is an utc datetime string e.g.
         [('2023-01-01 12:59:00', 1), ('2023-01-01 13:00:14', 1),] where 1 is always the value
         for each blink that occurred at that timestamp.
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
        :return: list of tuples, each is an utc datetime string e.g.
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
        :return: list of tuples, each is an utc datetime string e.g.
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
        :return: list of tuples, each is an utc datetime string e.g.
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

    def store_event(self,
                    timestamp: float,
                    event_type: EventTypes,
                    event_numerical_metadata: Optional[float] = None,
                    event_textual_metadata: Optional[float] = None) -> None:
        """Store an event into the events table of the database

        :param timestamp: unix timestamp of the event
        :param event_type: The event name ENUM
        :param event_numerical_metadata: Optional numerical metadata to store with the event
        :param event_textual_metadata: Optional textual metadata to store with the event
        """
        with self.db_con:
            self.db_con.execute(
                """INSERT INTO events(timestamp, event_type_id,
                 event_numerical_metadata, event_textual_metadata) VALUES(?,?,?,?)""", (
                    timestamp,
                    event_type.value,
                    event_numerical_metadata,
                    event_textual_metadata
                ))
        LOGGER.info("Wrote to database event_type: %s at %s with numerical metadata: %s and "
                    "textual metadata: %s", event_type,
                    timestamp, event_numerical_metadata, event_textual_metadata)

    def query_events(self, since: float, event_type_list: list[EventTypes]) \
            -> dict[str, List[float | int]]:
        """Fetch the events since the `since` timestamp, and return a list of tuples
        with the first item being the timestamp and the second being the integer 1 representing
        an event occurring
        :param since: Only consider timestamps after this, a unix timestamp
        :param event_type_list: List of events type string's you'd like to retrieve
        :return: list of tuples, each is a utc datetime string e.g.
         [('2023-01-01 12:59:00', 1), ('2023-01-01 13:00:14', 1),] where 1 is a notification
         event
        """
        with self.db_con:
            query = f"""
                SELECT timestamp, 1
                FROM events
                WHERE event_type_id IN ({','.join('?' for _ in event_type_list)}) AND timestamp >= ?
                ORDER BY timestamp ASC;
            """
            params = [i.value for i in event_type_list] + [since]
            cursor = self.db_con.execute(query, params)
            rows = cursor.fetchall()
        x_axis = [i[0] for i in rows]
        y_axis = [i[1] for i in rows]
        return {"timestamps": x_axis, "values": y_axis}

    # _create_db() from BlinkHistory()
    # store_blink() from BlinkHistory()
    # write_blink_history() from BlinkHistory()
    # get_blink_history_count() from BlinkHistory()
    # reset_create_db() from BlinkHistory()
    # fetch_last_n_blink() from BlinkHistory()
    # fetch_last_n_blink() from BlinkHistory()
    # _create_connection() from BlinkHistory()
