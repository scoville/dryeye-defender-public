"""Contains class blink graph"""
import logging
import time
from typing import List, Tuple

from PySide6.QtCharts import QBarSeries, QBarSet, QChart, QChartView
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGridLayout, QWidget

LOGGER = logging.getLogger(__name__)


class BlinkGraph(QWidget):
    """Widget for the blink frequency graph"""

    def __init__(self) -> None:
        """Initialize the graph variables"""
        super().__init__()

        self.series = QBarSeries()
        self.blink_bar = QBarSet("blink")
        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle("How many blink per minute")
        self.chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        self.chart.createDefaultAxes()

        axis_y = self.chart.axes(Qt.Orientation.Vertical)[0]
        # axis_x = self.chart.axes(Qt.Horizontal)[0]
        axis_y.setTitleText("Number of blink")
        # axis_x.setTitleText("Minutes")

        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.main_layout = QGridLayout()
        self.main_layout.addWidget(self.chart_view, 0, 0, 5, 6)
        self.setLayout(self.main_layout)

    @Slot(list)
    def update_graph(self, blink_history: List[Tuple[float, int]]) -> None:
        """Update the graph with next value

        :param blink_history: List of blink value(1 if detected blink, else -1) associated with time
        """
        LOGGER.info("updating graph")
        current_time = time.time()
        if blink_history:
            start_of_detection = blink_history[0][0]
            n_minutes = ((int(current_time) - int(start_of_detection))//60)
            blink_per_minutes = [0]+[0]*n_minutes
            for time_code, blink_value in reversed(blink_history):
                current_minute = (int(current_time) - int(time_code))//60
                if blink_value == 1:
                    blink_per_minutes[current_minute] += 1
            blink_per_minutes.reverse()
            LOGGER.info("blink_per_minutes=%s", blink_per_minutes)
            self.blink_bar.append(blink_per_minutes)
            self.series.append(self.blink_bar)

        self.chart.createDefaultAxes()

        axis_y = self.chart.axes(Qt.Orientation.Vertical)[0]
        axis_y.setTitleText("Number of blink")
        if not blink_per_minutes:
            blink_per_minutes = [5]  # defaut for axis y
        axis_y.setRange(0, max(blink_per_minutes))
