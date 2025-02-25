"""Class for debug window"""
import logging
from typing import Optional

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget, QLabel, QComboBox, QPushButton
from PySide6.QtGui import QFont

from dryeye_defender.utils.database import BlinkHistoryDryEyeDefender
from dryeye_defender.widgets.stats_window.blink_graph import BlinkGraph

from dryeye_defender.utils.utils import update_font

LOGGER = logging.getLogger(__name__)


class BlinkStatsWindow(QWidget):
    """Class to create the Blink Stats window with graphs of historical trends in blinks"""

    def __init__(self, db_api: BlinkHistoryDryEyeDefender) -> None:
        """Init
        """
        super().__init__()
        self.setWindowTitle("Stats window")
        qbbox_layout = QVBoxLayout(self)
        LOGGER.info("init stats window")

        self.blink_graph = BlinkGraph(db_api)

        self.select_stats_label = QLabel("Choose which stats to calculate")
        self.select_stats_dropdown = QComboBox()
        update_font(self.select_stats_dropdown)
        self.select_stats_dropdown.addItems(["Last 5 Minutes",  "Last Hour",  "Last Day",
                                             "Last Month",
                                             "Last Year"])
        self.default_plot_index = 1
        self.select_stats_dropdown.setCurrentIndex(self.default_plot_index)
        self.select_stats_dropdown.currentIndexChanged.connect(self.draw_selected_plot)
        qbbox_layout.addWidget(self.select_stats_dropdown, stretch=3)
        qbbox_layout.addWidget(self.blink_graph, stretch=3)
        self.setLayout(qbbox_layout)

        self.open_blink_stats_button = QPushButton(("Update"))
        self.open_blink_stats_button.setFont(QFont("Avenir Next LT Pro", 10))
        self.open_blink_stats_button.clicked.connect(self.draw_selected_plot)
        update_font(self.open_blink_stats_button)
        qbbox_layout.addWidget(self.open_blink_stats_button)

    def show_default_plot(self) -> None:
        """Display the default plot"""
        self.draw_selected_plot(self.default_plot_index)

    @Slot()
    def draw_selected_plot(self, stats_index: Optional[int] = None) -> None:
        """Slot for drawing the selected plot

        :param stats_index: index of the selected type of plot to draw if called via
        currentIndexChanged() signal. If called via button.clicked signal (from update() button)
        then instead introspect the index
        """
        if stats_index is False:
            # Occurs if called via a clicked.connect signal from the update button
            LOGGER.info("Refreshing graph")
            stats_index = self.select_stats_dropdown.currentIndex()
        if stats_index == -1:
            raise RuntimeError("This should not occur as there is no unselected option")
        if stats_index == 0:
            self.blink_graph.plot_graph_last_5_minutes()
        elif stats_index == 1:
            self.blink_graph.plot_graph_by_minute()
        elif stats_index == 2:
            self.blink_graph.plot_graph_by_hour()
        elif stats_index == 3:
            self.blink_graph.plot_graph_by_day()
        elif stats_index == 4:
            self.blink_graph.plot_graph_by_year()
        else:
            raise RuntimeError(f"This should not occur as"
                               f" this option does not exist: {stats_index}")
