from PySide6.QtCore import Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from eyeblink_gui.widgets.eyeblink_thread import EyeblinkModelThread


class DebugWindow(QWidget):
    def __init__(self, thread: EyeblinkModelThread):
        super().__init__()
        # Title and dimensions
        # self.setWindowTitle("Debug window")
        debug_layout = QVBoxLayout(self)
        print("init debug w")
        self.setGeometry(0, 0, 800, 500)
        thread.update_debug_img.connect(self.update_img)
        # Create a label for the display camera
        self.label = QLabel()
        self.label.setFixedSize(640, 480)
        debug_layout.addWidget(self.label)
        self.setLayout(debug_layout)

    @Slot(QPixmap)
    def update_img(self, image):
        self.label.setPixmap(image)
