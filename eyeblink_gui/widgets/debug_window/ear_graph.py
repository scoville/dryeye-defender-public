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
        """Create the graph with the two series for left and rigth eye

        :param thread: thread for connecting to signal
        """
        super().__init__()

        # `update graph` is called each time thread emit update ear values signal
        thread.update_ear_values.connect(self.update_graph)

        # serie for left eye
        self.series_left = QSplineSeries(self)
        # serie for rigth eye
        self.series_rigth = QSplineSeries(self)
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
        self.series_rigth.setPen(blue)
        self.series_rigth.append(self.current_x, 0)
        self.series_rigth.setName("Right Eye EAR")

        self.addSeries(self.series_left)
        self.addSeries(self.series_rigth)
        self.addAxis(self.axis_x, Qt.AlignmentFlag.AlignBottom)
        self.addAxis(self.axis_y, Qt.AlignmentFlag.AlignLeft)

        self.series_left.attachAxis(self.axis_x)
        self.series_left.attachAxis(self.axis_y)
        self.series_rigth.attachAxis(self.axis_x)
        self.series_rigth.attachAxis(self.axis_y)
        self.axis_x.setTickCount(10)
        # we put a range not center to get the last values on the rigth
        self.axis_x.setRange(0, 10)
        # ear values are mainly between 0 and 1
        self.axis_y.setRange(0, 1)

    @Slot()
    def update_graph(self, left_ear: float, rigth_ear: float) -> None:
        """Update the graph with new ear values

        :param left_ear: left ear value
        :param rigth_ear: rigth ear value
        """
        x_scroll = (self.plotArea().width() / self.axis_x.tickCount())/20
        new_x_diff = ((self.axis_x.max() - self.axis_x.min()) / self.axis_x.tickCount())/20
        self.current_x += new_x_diff
        self.series_left.append(self.current_x, left_ear)
        self.series_rigth.append(self.current_x, rigth_ear)

        self.scroll(x_scroll, 0)
