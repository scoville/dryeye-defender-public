"""Contains the a manual test for experimenting with graphs"""
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Any, Tuple, Sequence

import pyqtgraph as pg
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QVBoxLayout, QWidget
from pyqtgraph import DateAxisItem

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

LOGGER = logging.getLogger(__name__)


class GraphTest(QWidget):
    """Class for the graph displaying the ear values over time"""

    def __init__(self) -> None:
        """Create the graph
        """
        super().__init__()

        # # `update graph` is called each time thread emits the `update ear values` signal
        # thread.update_ear_values.connect(self.update_graph)

        # Create the graph widget
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground("#31313a")  # Set the background color of the graph

        axis = DateAxisItem()
        self.graphWidget.setAxisItems({'bottom': axis})

        # Set the axis labels
        self.graphWidget.setLabel("left", "Blink values")
        self.graphWidget.setLabel("bottom", "x")

        # Set the axis font size
        axis_font = pg.QtGui.QFont()
        axis_font.setPointSize(10)
        self.graphWidget.getAxis("left").tickFont = axis_font
        self.graphWidget.getAxis("bottom").tickFont = axis_font

        layout = QVBoxLayout()
        #
        # self.x_axis = deque(range(100), maxlen=100)
        # self.y_axis = deque([0.0 for _ in range(100)], maxlen=100)

        # self.graphWidget.setXRange(0, 100)

        layout.addWidget(self.graphWidget)
        self.setLayout(layout)
        self.plot_graph()

    @Slot()
    def plot_graph(self) -> None:
        """Update the graph with new ear values

        """
        LOGGER.info("plotting")
        data = [('2023-01-01 12:59', 2), ('2023-01-01 13:00', 3), ('2023-01-01 13:01', 5), ]
        x_axis = [datetime.strptime(i[0], "%Y-%m-%d %H:%M").timestamp() for i in data]
        y_axis = [i[1] for i in data]

        # self.data_line_left.setData(x_axis, y_axis)  # Update the data.
        pen = pg.mkPen(color="#e60049")
        print(x_axis, y_axis)
        self.data_line_left = self.graphWidget.plot(x_axis, y_axis, pen=pen, symbol='o')


class Application(QApplication):
    """The entire application encapsulated in this class"""

    def __init__(self, argv: Sequence[str]) -> None:
        """Initialise the application
        :param argv: sys.argv
        """
        super().__init__(argv)
        # Connect the SIGINT signal to a slot
        signal.signal(signal.SIGINT, self.handle_sigint)  # type: ignore
        # Create and show the main window
        self.main_window = GraphTest()
        self.main_window.show()

    def handle_sigint(self, *_: Tuple[Any, ...]) -> None:
        """Perform any cleanup or save operations here
        before exiting the application due to a SIGINT/keyboard interrupt
        """
        LOGGER.info("SIGINT received. Shutting down gracefully.")
        self.quit()


if __name__ == "__main__":
    app = Application(sys.argv)
    # Start the application event loop
    sys.exit(app.exec())
