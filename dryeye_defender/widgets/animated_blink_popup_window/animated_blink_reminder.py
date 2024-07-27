"""Class for the animated blink reminder widget"""
import os
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QMovie, QScreen
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QApplication

if os.name == "nt":  # Windows
    import win32gui  # pylint: disable=import-error
    import win32con  # pylint: disable=import-error
    import win32process  # pylint: disable=import-error
    import win32api  # pylint: disable=import-error


class AnimatedBlinkReminder(QWidget):
    """Widget that pops up to remind user to blink"""

    def __init__(
            self,
            movie_path: str,
            dismiss_callback: Callable[[], None],
            duration_lack: int,
            alert_seconds_cooldown: int,
            width: int = 320,
    ) -> None:
        # pylint: disable=too-many-arguments
        """Initialize all variable and create the layout of the window
        :param movie_path: path to the gif
        :param dismiss_callback: callback to call when the user clicks the dismiss button
        :param duration_lack: duration in seconds without blinks before the popup appears
        :param alert_seconds_cooldown: duration in seconds before the popup can appear again
        if the user dismisses it
        :param width: width of the window, default is set to the width of the gif (320px)
        """
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.gif_label = QLabel("Blinking Gif")
        self.gif_label.setFixedWidth(width)

        self.setup_movie(movie_path)

        layout.addWidget(self.gif_label)

        # Set up the text
        self.text_label = QLabel("Text")
        self.text_label.setText(
            f"You didn't blink in the last {duration_lack} seconds"
        )
        self.text_label.setFixedWidth(width)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.text_label)

        self.informative_text_label = QLabel("Informative Text")
        self.informative_text_label.setText(
            "Blink now to close the window or click 'Dismiss' to "
            f"dismiss for {alert_seconds_cooldown} seconds"
        )
        self.informative_text_label.setFixedWidth(width)
        self.informative_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.informative_text_label.setWordWrap(True)
        layout.addWidget(self.informative_text_label)

        # Set up the button
        self.button = QPushButton("Dismiss")
        self.button.setFixedWidth(width)

        def on_button_click() -> None:
            """On button click dismiss and close window"""
            dismiss_callback()
            self.close()

        self.button.clicked.connect(on_button_click)
        layout.addWidget(self.button)

        # Prepare force focus on Windows
        if os.name == "nt":  # Windows
            win32gui.SystemParametersInfo(
                win32con.SPI_SETFOREGROUNDLOCKTIMEOUT,
                0,
                win32con.SPIF_SENDWININICHANGE | win32con.SPIF_UPDATEINIFILE
            )

    def update_duration_lack(self, duration_lack: int) -> None:
        """Update the text label with the new duration lack

        :param duration_lack: duration in seconds without blinks before the popup appears
        """
        self.text_label.setText(
            f"You didn't blink in the last {duration_lack} seconds"
        )

    def show_reminder(self) -> None:
        """Show the reminder and start the gif. Don't show if already visible"""
        if not self.isVisible():
            self.movie.jumpToFrame(0)
            self.movie.start()
            self.show()
            self._center_window()
            self._force_focus()

    def _center_window(self) -> None:
        """Center the window on the screen"""
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo = self.frameGeometry()
        geo.moveCenter(center)
        self.move(geo.topLeft())

    def setup_movie(self, path: str) -> None:
        """Set up the movie with the given path

        :param path: path to the gif
        """
        assert os.path.exists(path), f"Could not find {path} at {Path(path).resolve()}"
        self.movie = QMovie(path)
        assert self.movie.isValid(), f"{path} file invalid"
        self.gif_label.setMovie(self.movie)

    def _force_focus(self) -> None:
        """Force focus on the window, so that it appears on top of all other windows"""
        self.raise_()  # Raises widget to top of parent widget's stack
        if os.name == "nt":  # Windows
            fg_window = win32gui.GetForegroundWindow()
            fg_thread_id = win32process.GetWindowThreadProcessId(fg_window)[0]
            current_thread_id = win32api.GetCurrentThreadId()
            if current_thread_id != fg_thread_id:
                win32process.AttachThreadInput(fg_thread_id, current_thread_id, True)
                win32gui.SetForegroundWindow(self.winId())
                win32process.AttachThreadInput(fg_thread_id, win32api.GetCurrentThreadId(), False)
        self.activateWindow()  # Sets the top widget in the stack to be the active window
