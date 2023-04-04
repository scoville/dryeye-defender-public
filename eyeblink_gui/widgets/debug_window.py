"""Class for debug window"""
import logging

from PySide6.QtCore import Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from eyeblink_gui.widgets.eyeblink_model_thread import EyeblinkModelThread

LOGGER = logging.getLogger(__name__)


class DebugWindow(QWidget):
    """Class to create the debug window with a juste a simple image of the output of the model"""

    def __init__(self, thread: EyeblinkModelThread):
        """Init the debug window

        :param thread: thread that compute the model
        """
        super().__init__()
        # Title and dimensions
        # self.setWindowTitle("Debug window")
        debug_layout = QVBoxLayout(self)
        logging.info("init debug window")
        self.setGeometry(0, 0, 800, 500)
        thread.update_debug_img.connect(self.update_img)
        # Create a label for the display camera
        self.label = QLabel()
        self.label.setFixedSize(640, 480)
        debug_layout.addWidget(self.label)
        self.setLayout(debug_layout)

    @Slot(QPixmap)
    def update_img(self, image: QPixmap) -> None:
        """Slot for updating the image on the window, called by the thread when finished

        :param image: QPixMap of the current debug output
        """
        self.label.setPixmap(image)
