"""Class for debug window"""
import logging

from typing import Optional
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget, QLabel, QComboBox, QPushButton

from dryeye_defender.widgets.blink_window.blink_graph import BlinkGraph


LOGGER = logging.getLogger(__name__)


class BlinkStatsWindow(QWidget):
    """Class to create the Blink Stats window with graphs of historical trends in blinks"""

    def __init__(self) -> None:
        """Init
        """
        super().__init__()
        self.setWindowTitle("Stats window")
        qbbox_layout = QVBoxLayout(self)
        LOGGER.info("init stats window")

        self.blink_graph = BlinkGraph()

        self.select_stats_label = QLabel("Choose which stats to calculate")
        self.select_stats_dropdown = QComboBox()
        self.select_stats_dropdown.addItems(["Last Hour",
                                             "Last Day"])
        self.select_stats_dropdown.currentIndexChanged.connect(self.draw_selected_plot)
        qbbox_layout.addWidget(self.select_stats_dropdown, stretch=3)
        qbbox_layout.addWidget(self.blink_graph, stretch=3)
        self.setLayout(qbbox_layout)

        self.open_blink_stats_button = QPushButton(("Update"))
        self.open_blink_stats_button.clicked.connect(self.draw_selected_plot)
        qbbox_layout.addWidget(self.open_blink_stats_button)

    @Slot()
    def draw_selected_plot(self, stats_index: Optional[int] = None) -> None:
        """Slot for drawing the selected plot

        :param stats_index: index of the selected type of plot to draw if called via
        currentIndexChanged() signal. If called via button.clicked signal (from update() button)
        then instead introspect the index
        """
        if not stats_index:
            stats_index = self.select_stats_dropdown.currentIndex()
            LOGGER.info("Refreshing graph")
        if stats_index == -1:
            raise RuntimeError("This should not occur as there is no unselected option")
        if stats_index == 0:
            self.blink_graph.plot_graph_by_minute()
        elif stats_index == 1:
            self.blink_graph.plot_graph_by_hour()
        else:
            raise RuntimeError("This should not occur as this option does not exist.")
