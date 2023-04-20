"""Contains the QChart object to display the ear values over time"""
import logging
import time

from PySide6.QtCharts import QChart, QSplineSeries, QValueAxis
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPen

from eyeblink_gui.widgets.eyeblink_model_thread import EyeblinkModelThread

LOGGER = logging.getLogger(__name__)


class EarGraph(QChart):
    def __init__(self, thread: EyeblinkModelThread, parent=None):
        """Create the graph with the two series for left and rigth eye

        :param thread: thread for connecting to signal
        """
        super().__init__(QChart.ChartTypeCartesian, parent, Qt.WindowFlags())

        # `update graph` is called each time thread emit update ear values signal
        thread.update_ear_values.connect(self.update_graph)

        # serie for left eye
        self.series_left = QSplineSeries(self)
        # serie for rigth eye
        self.series_rigth = QSplineSeries(self)
        self.axisX = QValueAxis()
        self.axisY = QValueAxis()
        self.current_x = 9.5

        # colors of the graph lines
        green = QPen(Qt.green)
        green.setWidth(3)
        blue = QPen(Qt.blue)
        blue.setWidth(3)
        self.series_left.setPen(green)
        self.series_left.append(self.current_x, 0)
        self.series_left.setName("Left ear")
        self.series_rigth.setPen(blue)
        self.series_rigth.append(self.current_x, 0)
        self.series_rigth.setName("Rigth ear")

        self.addSeries(self.series_left)
        self.addSeries(self.series_rigth)
        self.addAxis(self.axisX, Qt.AlignBottom)
        self.addAxis(self.axisY, Qt.AlignLeft)

        self.series_left.attachAxis(self.axisX)
        self.series_left.attachAxis(self.axisY)
        self.series_rigth.attachAxis(self.axisX)
        self.series_rigth.attachAxis(self.axisY)
        self.axisX.setTickCount(10)
        # we put a range not center to get the last values on the rigth
        self.axisX.setRange(0, 10)
        # ear values are mainly between 0 and 1
        self.axisY.setRange(0, 1)

    @Slot()
    def update_graph(self, left_ear, rigth_ear):
        """Update the graph with new ear values

        :param left_ear: left ear value
        :param rigth_ear: rigth ear value
        """
        x_scroll = (self.plotArea().width() / self.axisX.tickCount())/20
        new_x_diff = ((self.axisX.max() - self.axisX.min()) / self.axisX.tickCount())/20
        self.current_x += new_x_diff
        self.series_left.append(self.current_x, left_ear)
        self.series_rigth.append(self.current_x, rigth_ear)

        self.scroll(x_scroll, 0)
