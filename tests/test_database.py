"""Test logic for databse setup."""
import datetime
import sqlite3
# pylint: disable = redefined-outer-name
import time
from typing import Generator

import pytest
from freezegun import freeze_time

from dryeye_defender.utils.database import BlinkHistory

MOCK_DATE = "2023-01-01"
MOCK_TIME = f"{MOCK_DATE} 13:00:00"
MOCK_TIMESTAMP = datetime.datetime.strptime(MOCK_TIME, "%Y-%m-%d %H:%M:%S").timestamp()


@pytest.fixture
def connection() -> Generator[sqlite3.Connection, None, None]:
    """Create a temporary database in memory"""
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture
@freeze_time(MOCK_TIME)
def setup_db(connection: sqlite3.Connection) -> None:
    """Setup the temporary database in memory"""
    # pylint: disable = expression-not-assigned
    conn = connection
    with conn:
        conn.execute(
            """
            CREATE TABLE blink_history
            (frame_number INTEGER,
            blink_time FLOAT,
            blink_value INT,
            left_ear FLOAT,
            right_ear FLOAT,
            blink_marker INT)
        """)
        conn.execute(
            """
            CREATE INDEX idx_blink_timestamp ON blink_history (blink_marker, blink_time);
            """
        )

        conn.create_function("CURRENT_TIME", 0, MOCK_TIME)  # type: ignore
        conn.create_function("CURRENT_DATE", 0, MOCK_DATE)  # type: ignore
        conn.create_function("CURRENT_TIMESTAMP", 0, MOCK_TIME)  # type: ignore

    with conn:
        conn.execute(
            """
            INSERT INTO blink_history(blink_time, blink_value, left_ear, right_ear,
            blink_marker)
            VALUES(?,?,?,?,?)
            """,
            (
                time.time() - 3,
                1,
                0.1,
                0.2,
                1
            ),
        )
        conn.execute(
            """
            INSERT INTO blink_history(blink_time, blink_value, left_ear, right_ear,
            blink_marker)
            VALUES(?,?,?,?,?)
            """,
            (
                time.time() - 2,
                -1,
                0.9,
                0.8,
                0
            ),
        ),
        conn.execute(
            """
            INSERT INTO blink_history(blink_time, blink_value, left_ear, right_ear,
            blink_marker)
            VALUES(?,?,?,?,?)
            """,
            (
                time.time() - 1,
                1,
                0.2,
                0.2,
                1
            ),
        )


@pytest.fixture
def blinkhistory(connection: sqlite3.Connection) -> BlinkHistory:
    """get blink history instance"""
    return BlinkHistory(db_con=connection)


@freeze_time(MOCK_TIME)
@pytest.mark.usefixtures("setup_db")
def test_database_query_blink_history_groupby_minute_since(blinkhistory: BlinkHistory) -> None:
    """Test query_blink_history_groupby_minute_since"""
    # result = blinkhistory._display_all_rows()
    result = blinkhistory.query_blink_history_groupby_minute_since(MOCK_TIMESTAMP - 60)
    assert result == {"timestamps": [1672577940.0], "values": [2]}
