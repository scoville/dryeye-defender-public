"""Contains the QChart object to display the ear values over time"""
import logging
import time

from PySide6.QtCharts import QChart, QSplineSeries, QValueAxis
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPen

from eyeblink_gui.widgets.eyeblink_model_thread import EyeblinkModelThread

LOGGER = logging.getLogger(__name__)


class EarGraph(QChart):
    def __init__(self, thread=EyeblinkModelThread, parent=None):
        super().__init__(QChart.ChartTypeCartesian,  parent, Qt.WindowFlags())

        # `update graph` is called each time thread emit update ear values signal
        thread.update_ear_values.connect(self.update_graph)

        self._series_left = QSplineSeries(self)
        self._series_rigth = QSplineSeries(self)
        self._axisX = QValueAxis()
        self._axisY = QValueAxis()
        init_time = time.time()
        self._x = init_time
        self._y = 0

        green = QPen(Qt.green)
        green.setWidth(3)
        blue = QPen(Qt.blue)
        blue.setWidth(3)
        self._series_left.setPen(green)
        self._series_left.append(self._x, self._y)
        self._series_rigth.setPen(blue)
        self._series_rigth.append(self._x, self._y)

        self.addSeries(self._series_left)
        self.addSeries(self._series_rigth)
        self.addAxis(self._axisX, Qt.AlignBottom)
        self.addAxis(self._axisY, Qt.AlignLeft)

        self._series_left.attachAxis(self._axisX)
        self._series_left.attachAxis(self._axisY)
        self._series_rigth.attachAxis(self._axisX)
        self._series_rigth.attachAxis(self._axisY)
        self._axisX.setTickCount(10)
        self._axisX.setRange(init_time-8, init_time+1)
        self._axisY.setRange(0, 1)

    @Slot()
    def update_graph(self, left_ear, rigth_ear, time):
        x = (self.plotArea().width() / self._axisX.tickCount())/20
        y = ((self._axisX.max() - self._axisX.min()) / self._axisX.tickCount())/20
        self._x += y
        self._y = left_ear
        self._series_left.append(self._x, self._y)
        self._series_rigth.append(self._x, rigth_ear)
        # diff_time = time - self._old_x
        # LOGGER.info("diff_time=%s", diff_time)
        self.scroll(x, 0)
