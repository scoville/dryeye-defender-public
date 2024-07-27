"""Contains the a manual test for experimenting with graphs"""
import logging
import time
from datetime import datetime, timezone
from typing import Any, List

import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget
from dateutil import tz

from blinkdetector.utils.database import EventTypes
from dryeye_defender.utils.database import BlinkHistory

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
        return [datetime.fromtimestamp(value, tz=timezone.utc).astimezone(
            local_timezone).strftime("%H:%M") for value in
                values]

    def generateSvg(self, *args: Any, **kwargs: Any) -> None:  # pylint: disable=invalid-name
        """This method is implemented to satisfy the abstract method in the parent class"""


class BlinkGraph(QWidget):
    """
    Class for just the graph COMPONENT of the window displaying the blink-per-minute statistics
    over time
    """

    def __init__(self, blink_history: BlinkHistory) -> None:
        """Create the graph
        """
        super().__init__()
        self.blink_history = blink_history
        # Create the graph widget
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setLimits(yMin=0)
        self.graph_widget.setBackground("#31313a")  # Set the background color of the graph

        # Set the axis labels
        self.graph_widget.setLabel("left", "Blinks per minute")
        self.graph_widget.setLabel("bottom", "x")

        # Set the axis font size
        axis_font = pg.QtGui.QFont()  # pylint: disable=no-member
        axis_font.setPointSize(10)
        self.graph_widget.getAxis("left").tickFont = axis_font
        self.graph_widget.getAxis("bottom").tickFont = axis_font

        layout = QVBoxLayout()

        layout.addWidget(self.graph_widget)
        self.setLayout(layout)

    def set_minute_xaxis_tick_format(self) -> None:
        """Set the xaxis to show only show %H:$M hours and minutes for each tick"""
        x_axis_handle = MinuteOnlyDateAxisItem()
        x_axis_handle.setLabel(text="Time", units="s")
        self.graph_widget.setAxisItems({"bottom": x_axis_handle})

    def set_default_xaxis_tick_format(self) -> None:
        """Set the xaxis to show default tick labelling, which auto-adjusts labels based on the
        zoom scale of the user
        """
        self.graph_widget.setAxisItems({"bottom": pg.DateAxisItem()})

    @Slot()
    def plot_graph_last_5_minutes(self) -> None:
        """Retrieve blink data from DB over last 5 minutes and plot a point with value 1 at the
        timestamp of the blink
        """
        LOGGER.info("plot_graph_by_minute called")
        self.graph_widget.clear()
        graph_end_time = time.time()
        graph_start_time = graph_end_time - 60 * 5
        self.graph_widget.setXRange(graph_start_time, graph_end_time)
        self.graph_widget.setLabel("left", "Event Detected")
        self.set_default_xaxis_tick_format()
        data = self.blink_history.query_raw_blink_history_no_grouping(graph_start_time)
        if not data:
            LOGGER.info("no data found in last 5 minutes")
            self.graph_widget.setTitle("No blink data available over the last 10 minutes")
            return
        LOGGER.info("Retrieved data for plot: %s", data)

        self.graph_widget.setTitle("Blinks over last 5 minutes")
        bargraph = pg.BarGraphItem(x=data["timestamps"], height=data["values"],
                                   width=1, brush="g")
        self.graph_widget.addItem(bargraph)

        events = self.blink_history.query_events(graph_start_time,
                                                 [EventTypes["SYSTEM_TRAY_NOTIFICATION"],
                                                  EventTypes["POPUP_NOTIFICATION"], ])
        LOGGER.info("Retrieved data for plot: %s", data)
        if not events:
            LOGGER.info("no events found")
            legend = pg.LegendItem()
            legend.addItem(bargraph, "Blink Detection")
            legend.setParentItem(self.graph_widget.graphicsItem())
            legend.anchor(itemPos=(1, 0), parentPos=(1, 0))
        else:
            LOGGER.info("Events found: %s", events)
            event_bargraph = pg.BarGraphItem(x=events["timestamps"], height=events["values"],
                                             width=1, brush="r")
            self.graph_widget.addItem(event_bargraph)
            legend = pg.LegendItem()
            legend.addItem(bargraph, "Blink Detection")
            legend.addItem(event_bargraph, "Blink Reminder Event")
            legend.setParentItem(self.graph_widget.graphicsItem())
            legend.anchor(itemPos=(1, 0), parentPos=(1, 0))
        self.graph_widget.show()

    @Slot()
    def plot_graph_by_minute(self) -> None:
        """Retrieve blink data from DB over last 60 minutes and plot the number of points per
        minute.
        """
        LOGGER.info("plot_graph_by_minute called")
        self.graph_widget.clear()
        graph_end_time = time.time()
        graph_start_time = graph_end_time - 60 * 60
        self.graph_widget.setXRange(graph_start_time, graph_end_time)
        self.set_minute_xaxis_tick_format()
        data = self.blink_history.query_blink_history_groupby_minute_since(graph_start_time)
        if not data:
            LOGGER.info("no data found in last 60 minutes")
            self.graph_widget.setTitle("No blink data available over the last 10 minutes")
            return
        LOGGER.info("Retrieved data for plot: %s", data)
        self.graph_widget.setTitle("Blinks over last 60 minutes")
        bargraph = pg.BarGraphItem(x=data["timestamps"], height=data["values"],
                                   width=60 - 2, brush="g")
        self.graph_widget.addItem(bargraph)
        self.graph_widget.setLabel("left", "Blinks per minute")

    @Slot()
    def plot_graph_by_hour(self) -> None:
        """Retrieve blink data from DB over last 24 hours and plot per hour bin,the mean blinks per
        minute.
        """
        self.graph_widget.clear()
        graph_end_time = time.time()
        graph_start_time = graph_end_time - 60 * 60 * 24
        self.graph_widget.setXRange(graph_start_time, graph_end_time)
        self.set_minute_xaxis_tick_format()
        data = self.blink_history.query_blink_history_groupby_hour_since(graph_start_time)
        if not data:
            LOGGER.info("no data found in last 24 hours")
            self.graph_widget.setTitle("No blink data available over the last 24 hours")
            return
        LOGGER.info("Retrieved data for plot: %s", data)
        self.graph_widget.setTitle("Blinks over last 24 hours")
        bargraph = pg.BarGraphItem(x=data["timestamps"], height=data["values"],
                                   width=60 * 60 - 2, brush="g")
        self.graph_widget.addItem(bargraph)
        self.graph_widget.setLabel("left", "Blinks per minute")

    @Slot()
    def plot_graph_by_day(self) -> None:
        """Retrieve blink data from DB over last 30 days and plot per day bin, the mean
        blinks per minute.
        """
        self.graph_widget.clear()
        graph_end_time = time.time()
        graph_start_time = graph_end_time - 60 * 60 * 24 * 30
        self.graph_widget.setXRange(graph_start_time, graph_end_time)
        self.set_default_xaxis_tick_format()
        data = self.blink_history.query_blink_history_groupby_day_since(graph_start_time)
        if not data:
            LOGGER.info("no data found in last 30 days")
            self.graph_widget.setTitle("No blink data available over the last 30 days")
            return
        LOGGER.info("Retrieved data for plot: %s", data)
        self.graph_widget.setTitle("Blinks over last 30 days")
        bargraph = pg.BarGraphItem(x=data["timestamps"], height=data["values"],
                                   width=24 * 60 * 60 - 2, brush="g")
        self.graph_widget.addItem(bargraph)
        self.graph_widget.setLabel("left", "Blinks per minute")

    @Slot()
    def plot_graph_by_year(self) -> None:
        """Retrieve blink data from DB over last 360 days and plot per day bin, the mean
        blinks per minute.
        """
        self.graph_widget.clear()
        graph_end_time = time.time()
        graph_start_time = graph_end_time - 60 * 60 * 24 * 30 * 12
        self.graph_widget.setXRange(graph_start_time, graph_end_time)
        self.set_default_xaxis_tick_format()
        data = self.blink_history.query_blink_history_groupby_day_since(graph_start_time)
        if not data:
            LOGGER.info("no data found in last 360 days")
            self.graph_widget.setTitle("No blink data available over the last 360 days")
            return
        LOGGER.info("Retrieved data for plot: %s", data)
        self.graph_widget.setTitle("Blinks over last 360 days")
        bargraph = pg.BarGraphItem(x=data["timestamps"], height=data["values"],
                                   width=24 * 60 * 60 - 2, brush="g")
        self.graph_widget.addItem(bargraph)
        self.graph_widget.setLabel("left", "Blinks per minute")
