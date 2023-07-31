"""Class for debug window"""
import logging

from PySide6.QtWidgets import QVBoxLayout, QWidget

from dryeye_defender.widgets.blink_window.blink_graph import BlinkGraph
from PySide6.QtWidgets import QPushButton
from PySide6 import QtCore

LOGGER = logging.getLogger(__name__)


class BlinkStatsWindow(QWidget):
    """Class to create the Blink Stats window with graphs of historical trends in blinks"""

    def __init__(self):
        """Init
        """
        super().__init__()
        self.setWindowTitle("Stats window")
        qbbox_layout = QVBoxLayout(self)
        LOGGER.info("init stats window")

        self.blink_graph = BlinkGraph()

        self.open_blink_stats_button = QPushButton(("Blinks by Minute"))
        self.open_blink_stats_button.clicked.connect(self.blink_graph.plot_graph_by_minute)
        qbbox_layout.addWidget(self.open_blink_stats_button, stretch=3)
        qbbox_layout.addWidget(self.blink_graph, stretch=3)

        self.setLayout(qbbox_layout)
