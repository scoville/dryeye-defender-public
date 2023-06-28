"""Class for debug window"""
import logging

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from eyeblink_gui.widgets.debug_window.ear_graph import EarGraph
from eyeblink_gui.widgets.eyeblink_model_thread import EyeblinkModelThread

LOGGER = logging.getLogger(__name__)
MAX_CAMERA_VIEW_WIDTH = 600
MAX_CAMERA_VIEW_HEIGHT = 800


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
        LOGGER.info("init debug window")
        self.setGeometry(0, 0, 800, 1000)

        thread.update_debug_img.connect(self.update_img)
        # Create a label for the display camera
        self.label = QLabel()
        self.label.setScaledContents(True)
        self.label.setFixedSize(MAX_CAMERA_VIEW_HEIGHT, MAX_CAMERA_VIEW_WIDTH)
        self.label.setScaledContents(True)
        self.chart_view = EarGraph(thread=thread)

        debug_layout.addWidget(self.chart_view)
        debug_layout.addWidget(self.label)
        self.setLayout(debug_layout)

    @Slot(QPixmap)
    def update_img(self, image: QPixmap) -> None:
        """Slot for updating the image on the window, called by the thread when finished

        :param image: QPixMap of the current debug output
        """
        ar_image = image.width() / image.height()
        ar_label = MAX_CAMERA_VIEW_WIDTH / MAX_CAMERA_VIEW_HEIGHT

        # If image aspect ratio is wider than label aspect ratio
        # then scale by width, else by height
        if ar_image > ar_label:
            image = image.scaledToWidth(
                MAX_CAMERA_VIEW_WIDTH, Qt.TransformationMode.SmoothTransformation
            )
        else:
            image = image.scaledToHeight(
                MAX_CAMERA_VIEW_HEIGHT, Qt.TransformationMode.SmoothTransformation
            )
        self.label.setPixmap(image)
