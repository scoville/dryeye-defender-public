"""Class for debug window"""
import logging


from PySide6.QtCore import Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget, QLabel, QComboBox

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
        self.select_stats_dropdown.addItems(["Blinks by Minute",
                                             "Blinks by Hour"])
        self.select_stats_dropdown.currentIndexChanged.connect(self.draw_selected_plot)
        qbbox_layout.addWidget(self.select_stats_dropdown, stretch=3)
        qbbox_layout.addWidget(self.blink_graph, stretch=3)
        self.setLayout(qbbox_layout)

    @Slot()
    def draw_selected_plot(self, stats_index: int) -> None:
        """Slot for drawing the selected plot

        :param stats_index: index of the selected type of plot to draw
        """
        if stats_index == -1:
            raise RuntimeError("This should not occur as there is no unselected option")
        if stats_index == 0:
            self.blink_graph.plot_graph_by_minute()
        elif stats_index == 1:
            self.blink_graph.plot_graph_by_hour()
        else:
            raise RuntimeError("This should not occur as this option does not exist.")
