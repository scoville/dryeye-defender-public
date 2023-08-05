"""Contains the a manual test for experimenting with graphs"""
import logging
import time
import os
from datetime import datetime, timezone
from typing import Any, List
from dateutil import tz
import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget
from dryeye_defender.utils.utils import get_saved_data_path
from dryeye_defender.utils.database import BlinkHistory

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
local_timezone = tz.tzlocal()

LOGGER = logging.getLogger(__name__)


class MinuteOnlyDateAxisItem(pg.DateAxisItem):
    """Replace the timestamps to string datetimes with only the hour/minutes shown"""

    def tickStrings(self, values: List[float], scale: Any, spacing: Any) -> List[str]:
        """Replace the tick strings with only the hour/minutes shown

        :param values: timestamps to be converted to datetime strings
        :param scale: scale of the axis
        :param spacing: spacing of the axis
        """
        print("here", values)
        return [datetime.fromtimestamp(value, tz=timezone.utc).astimezone(
            local_timezone).strftime("%H:%M") for value in
                values]


class BlinkGraph(QWidget):
    """Class for the graph displaying the ear values over time"""

    def __init__(self) -> None:
        """Create the graph
        """
        super().__init__()
        self.blink_history = BlinkHistory(get_saved_data_path())

        # # `update graph` is called each time thread emits the `update ear values` signal
        # thread.update_ear_values.connect(self.update_graph)

        # Create the graph widget
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground("#31313a")  # Set the background color of the graph

        # Set the axis labels
        self.graph_widget.setLabel("left", "Blinks per minute")
        self.graph_widget.setLabel("bottom", "x")

        # Set the axis font size
        axis_font = pg.QtGui.QFont()  # pylint: disable=no-member
        axis_font.setPointSize(10)
        self.graph_widget.getAxis("left").tickFont = axis_font
        self.graph_widget.getAxis("bottom").tickFont = axis_font

        x_axis_handle = MinuteOnlyDateAxisItem()
        x_axis_handle.setLabel(text="Time", units="s")
        self.graph_widget.setAxisItems({"bottom": x_axis_handle})

        layout = QVBoxLayout()

        layout.addWidget(self.graph_widget)
        self.setLayout(layout)

    @Slot()
    def plot_graph_by_minute(self) -> None:
        """Retrieve blink data from DB over last 60 minutes and plot the number of points per
        minute.
        """
        LOGGER.info("plot_graph_by_minute called")
        self.graph_widget.clear()
        data = self.blink_history.query_blink_history_groupby_minute_since(time.time() - 60 * 60)
        if not data:
            LOGGER.info("no data found in last 60 minutes")
            self.graph_widget.setTitle("No blink data available over the last 10 minutes")
            return
        LOGGER.info("Retrieved data for plot: %s", data)
        self.graph_widget.setTitle("Blinks over last 60 minutes")
        bargraph = pg.BarGraphItem(x=data["timestamps"], height=data["values"],
                                   width=60 - 2, brush="g")
        self.graph_widget.addItem(bargraph)

    @Slot()
    def plot_graph_by_hour(self) -> None:
        """Retrieve blink data from DB over last 24 hours and plot per hour bin,the mean blinks per
        minute.
        """
        self.graph_widget.clear()
        data = self.blink_history.query_blink_history_groupby_hour_since(time.time() - 60 * 60 * 24)
        if not data:
            LOGGER.info("no data found in last 24 hours")
            self.graph_widget.setTitle("No blink data available over the last 24 hours")
            return
        LOGGER.info("Retrieved data for plot: %s", data)
        self.graph_widget.setTitle("Blinks over last 24 hours")
        bargraph = pg.BarGraphItem(x=data["timestamps"], height=data["values"],
                                   width=60 * 60 - 2, brush="g")
        self.graph_widget.addItem(bargraph)
