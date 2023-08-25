"""Globals"""
import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def set_environment_vars() -> None:
    """Set an environment variable for all tests to notify the get_saved_data_path()
    function to return /tmp/saved_blink.db instead of the real database path.
    """
    os.environ["CI_TESTS"] = "True"
