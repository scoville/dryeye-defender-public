"""Contains the QChart object to display the ear values over time"""
import logging

from PySide6.QtCharts import QChart, QSplineSeries, QValueAxis
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPen

from eyeblink_gui.widgets.eyeblink_model_thread import EyeblinkModelThread

LOGGER = logging.getLogger(__name__)


class EarGraph(QChart):
    """Class for the graph displaying the ear values over time"""

    def __init__(self, thread: EyeblinkModelThread) -> None:
        """Create the graph with the two series for left and right eye

        :param thread: thread for connecting to signal
        """
        super().__init__()

        # `update graph` is called each time thread emit update ear values signal
        thread.update_ear_values.connect(self.update_graph)

        # series for left eye
        self.series_left = QSplineSeries(self)
        # series for right eye
        self.series_right = QSplineSeries(self)
        self.axis_x = QValueAxis()
        self.axis_y = QValueAxis()
        self.current_x = 9.5

        # colors of the graph lines
        green = QPen(Qt.GlobalColor.green)
        green.setWidth(3)
        blue = QPen(Qt.GlobalColor.blue)
        blue.setWidth(3)
        self.series_left.setPen(green)
        self.series_left.append(self.current_x, 0)
        self.series_left.setName("Left Eye EAR")
        self.series_right.setPen(blue)
        self.series_right.append(self.current_x, 0)
        self.series_right.setName("Right Eye EAR")

        self.addSeries(self.series_left)
        self.addSeries(self.series_right)
        self.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        self.series_left.attachAxis(self.axis_x)
        self.series_left.attachAxis(self.axis_y)
        self.series_right.attachAxis(self.axis_x)
        self.series_right.attachAxis(self.axis_y)
        self.axis_x.setTickCount(10)
        # we put a range not center to get the last values on the right
        self.axis_x.setRange(0, 10)
        # ear values are mainly between 0 and 1
        self.axis_y.setRange(0, 1)

    @Slot()
    def update_graph(self, left_ear: float, right_ear: float) -> None:
        """Update the graph with new ear values

        :param left_ear: left ear value
        :param right_ear: right ear value
        """
        x_scroll = (self.plotArea().width() / self.axis_x.tickCount())/20
        new_x_diff = ((self.axis_x.max() - self.axis_x.min()) / self.axis_x.tickCount())/20
        self.current_x += new_x_diff
        print("current_x: ", self.current_x)
        print("left ear", left_ear)
        self.series_left.append(self.current_x, left_ear)
        self.series_right.append(self.current_x, right_ear)
        print("series_left: ", self.series_left)
        self.scroll(x_scroll, 0)

        x_min = self.current_x - (self.axis_x.max() - self.axis_x.min())

        print("x_min", x_min)
        # Remove points before the x_min value from the left series
        for point in reversed(self.series_left.points()):
            if point.x() < x_min:
                print("removing", point.x())
                self.series_left.remove(point)
        # Remove points before the x_min value from the right series
        for point in reversed(self.series_right.points()):
            if point.x() < x_min:
                self.series_right.remove(point)
