"""Contains the a manual test for experimenting with graphs"""
import logging
import time
import os
import signal
import sys
from datetime import datetime
from typing import Any, Tuple, Sequence

import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QVBoxLayout, QWidget
from pyqtgraph import DateAxisItem

from dryeye_defender.utils.utils import get_saved_data_path
from dryeye_defender.utils.database import BlinkHistory

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

LOGGER = logging.getLogger(__name__)

class MinuteOnlyDateAxisItem(pg.DateAxisItem):
    def tickStrings(self, values, scale, spacing):
        print(values)
        return [datetime.fromtimestamp(value).strftime("%H:%M") for value in values]

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
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground("#31313a")  # Set the background color of the graph

        axis = DateAxisItem()
        self.graphWidget.setAxisItems({'bottom': axis})

        # Set the axis labels
        self.graphWidget.setLabel("left", "Blink values")
        self.graphWidget.setLabel("bottom", "x")

        # Set the axis font size
        axis_font = pg.QtGui.QFont()
        axis_font.setPointSize(10)
        self.graphWidget.getAxis("left").tickFont = axis_font
        self.graphWidget.getAxis("bottom").tickFont = axis_font

        x_axis_handle = MinuteOnlyDateAxisItem()
        x_axis_handle.setLabel(text="Time", units="s")
        self.graphWidget.setAxisItems({'bottom': x_axis_handle})

        layout = QVBoxLayout()

        layout.addWidget(self.graphWidget)
        self.setLayout(layout)

    @Slot()
    def plot_graph_by_minute(self) -> None:
        """Update the graph of blinks grouped by minute

        """
        data = self.blink_history.query_blink_history_groupby_minute_since(time.time() - 600)
        LOGGER.info("Retrieved data for plot: %s", data)
        x_axis = [datetime.strptime(i[0], "%Y-%m-%d %H:%M").timestamp() for i in data]
        y_axis = [i[1] for i in data]
        bargraph = pg.BarGraphItem(x=x_axis, height=y_axis, width=60 - 2, brush='g')
        self.graphWidget.addItem(bargraph)
