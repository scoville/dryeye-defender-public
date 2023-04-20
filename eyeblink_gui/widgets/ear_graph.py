from PySide6.QtCharts import QChart, QSplineSeries, QValueAxis
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QPen

from eyeblink_gui.widgets.eyeblink_model_thread import EyeblinkModelThread
import time


class EarGraph(QChart):
    def __init__(self, thread=EyeblinkModelThread, parent=None):
        super().__init__(QChart.ChartTypeCartesian,  parent, Qt.WindowFlags())

        thread.update_ear_values.connect(self.update_graph)
        self._series = QSplineSeries(self)
        self._titles = []
        self._axisX = QValueAxis()
        self._axisY = QValueAxis()
        self._step = 0
        init_time = time.time()
        self._x = init_time
        self._y = 0

        green = QPen(Qt.red)
        green.setWidth(3)
        self._series.setPen(green)
        self._series.append(self._x, self._y)

        self.addSeries(self._series)
        self.addAxis(self._axisX, Qt.AlignBottom)
        self.addAxis(self._axisY, Qt.AlignLeft)

        self._series.attachAxis(self._axisX)
        self._series.attachAxis(self._axisY)
        self._axisX.setTickCount(10)
        self._axisX.setRange(init_time-10, init_time)
        self._axisY.setRange(0, 1)

    @Slot()
    def update_graph(self, left_ear, rigth_ear, time):
        self._x = time
        self._y = left_ear
        self._series.append(self._x, self._y)
        self.scroll(time - self._axisX.max(), 0)
