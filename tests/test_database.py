"""Test logic for databse setup."""
import time
from freezegun import freeze_time
import pytest
import sqlite3
import datetime
from unittest import mock
from dryeye_defender.utils.database import BlinkHistory

MOCK_DATE = "2023-01-01"
MOCK_TIME = f"{MOCK_DATE} 13:00:00"
MOCK_TIMESTAMP = datetime.datetime.strptime(MOCK_TIME, "%Y-%m-%d %H:%M:%S").timestamp()


@pytest.fixture
def connection():
    """Create a temporary database in memory"""
    connection = sqlite3.connect(':memory:')
    yield connection
    connection.close()


@pytest.fixture
@freeze_time(MOCK_TIME)
def setup_db(connection):
    """Setup the temporary database in memory"""
    with connection:
        connection.execute(
            """
            CREATE TABLE blink_history
            (frame_number INTEGER,
            blink_time FLOAT,
            blink_value INT,
            left_ear FLOAT,
            right_ear FLOAT,
            blink_marker INT)
        """)
        connection.execute(
            """
            CREATE INDEX idx_blink_timestamp ON blink_history (blink_marker, blink_time);
            """
        )

        connection.create_function("CURRENT_TIME", 0, MOCK_TIME)
        connection.create_function("CURRENT_DATE", 0, MOCK_DATE)
        connection.create_function("CURRENT_TIMESTAMP", 0, MOCK_TIME)

    with connection:
        connection.execute(
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
        connection.execute(
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
        connection.execute(
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
def blinkhistory(connection):  # 1
    return BlinkHistory(db_con=connection)


@freeze_time(MOCK_TIME)
@pytest.mark.usefixtures("setup_db")
def test_database(blinkhistory):
    # result = blinkhistory._display_all_rows()
    result = blinkhistory.query_blink_history_groupby_minute_since(MOCK_TIMESTAMP - 60)
    assert result == {"timestamps": [1672577940.0], "values": [2]}
