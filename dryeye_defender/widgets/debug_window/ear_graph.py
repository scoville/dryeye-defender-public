"""Contains the QChart object to display the ear values over time"""
import logging
import time
from collections import deque

import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from dryeye_defender.widgets.blink_model_thread import BlinkModelThread

LOGGER = logging.getLogger(__name__)


class EarGraph(QWidget):
    """Class for the graph displaying the ear values over time"""

    def __init__(self, thread: BlinkModelThread) -> None:
        """Create the graph with the two series for left and right eye

        :param thread: thread for connecting to signal
        """
        super().__init__()

        # `update graph` is called each time thread emits the `update ear values` signal
        thread.update_ear_values.connect(self.update_graph)

        # Create the graph widget
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground("#31313a")  # Set the background color of the graph

        # Set the axis labels
        self.graphWidget.setLabel("left", "EAR ratiovalues")
        self.graphWidget.setLabel("bottom", "x")

        # Set the axis font size
        axis_font = pg.QtGui.QFont()
        axis_font.setPointSize(10)
        self.graphWidget.getAxis("left").tickFont = axis_font
        self.graphWidget.getAxis("bottom").tickFont = axis_font

        layout = QVBoxLayout()

        self.x_axis = deque(range(100), maxlen=100)
        self.y_left = deque([0.0 for _ in range(100)], maxlen=100)
        self.y_right = deque([0.0 for _ in range(100)], maxlen=100)

        pen_left = pg.mkPen(color="#e60049")
        pen_right = pg.mkPen(color="#50e991")
        self.data_line_left = self.graphWidget.plot(self.x_axis, self.y_left, pen=pen_left)
        self.data_line_right = self.graphWidget.plot(self.x_axis, self.y_right, pen=pen_right)

        self.graphWidget.setXRange(0, 100)

        layout.addWidget(self.graphWidget)
        self.setLayout(layout)

    @Slot()
    def update_graph(self, left_ear: float, right_ear: float) -> None:
        """Update the graph with new ear values

        :param left_ear: left ear value
        :param right_ear: right ear value
        """
        b_time = time.time()
        self.y_left.append(left_ear)
        self.y_right.append(right_ear)

        self.data_line_left.setData(self.x_axis, self.y_left)  # Update the data.
        self.data_line_right.setData(self.x_axis, self.y_right)  # Update the data.

        LOGGER.debug("update graph time: %s", time.time() - b_time)
