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

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

LOGGER = logging.getLogger(__name__)


class MinuteOnlyDateAxisItem(pg.DateAxisItem):
    def tickStrings(self, values, scale, spacing):
        print(values)
        return [datetime.fromtimestamp(value).strftime("%H:%M") for value in values]


class GraphTest(QWidget):
    """Class for the graph displaying the ear values over time"""

    def __init__(self) -> None:
        """Create the graph
        """
        super().__init__()

        # # `update graph` is called each time thread emits the `update ear values` signal
        # thread.update_ear_values.connect(self.update_graph)

        # Create the graph widget
        self.graphWidget = pg.plot()

        # self.graphWidget = pg.PlotWidget()
        self.graphWidget.setBackground("#31313a")  # Set the background color of the graph

        # x_axis_handle = MinuteOnlyDateAxisItem()
        # x_axis_handle.setTickSpacing(major=timedelta(minutes=1), minor=timedelta(minutes=1))
        # x_axis_handle.setLabel(text="Time", units="s")
        # self.graphWidget.setAxisItems({'bottom': x_axis_handle})

        # Set the axis labels
        self.graphWidget.setLabel("left", "Blink values")
        self.graphWidget.setLabel("bottom", "x")

        # Set the axis font size
        axis_font = pg.QtGui.QFont()
        axis_font.setPointSize(10)
        self.graphWidget.getAxis("left").tickFont = axis_font
        self.graphWidget.getAxis("bottom").tickFont = axis_font

        layout = QVBoxLayout()
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
        print(x_axis, y_axis)
        bargraph = pg.BarGraphItem(x=x_axis, height=y_axis, width=60 - 2, brush='g')
        self.graphWidget.addItem(bargraph)
        x_axis_handle = MinuteOnlyDateAxisItem()
        # x_axis_handle.setTickSpacing(major=timedelta(minutes=1), minor=timedelta(minutes=1))
        x_axis_handle.setLabel(text="Time", units="s")
        # x_axis_handle.setTicks([("12:59", "12:59"), ("12:59", "12:59"), ("12:59", "12:59")])
        self.graphWidget.setAxisItems({'bottom': x_axis_handle})
        # self.data_line_left = self.graphWidget.plot(x_axis, y_axis, pen=pen, symbol ='o')


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
