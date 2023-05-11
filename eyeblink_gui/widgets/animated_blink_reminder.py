"""Class for the animated blink reminder widget"""
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QMovie, QScreen
from PySide6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QApplication


class AnimatedBlinkReminder(QWidget):
    """Widget that pops up to remind user to blink"""

    def __init__(
            self,
            dismiss_callback: callable,
            duration_lack: int,
            alert_seconds_cooldown: int,
            width: int = 320,
    ) -> None:
        """Initialize all variable and create the layout of the window
        :param dismiss_callback: callback to call when the user clicks the dismiss button
        :param duration_lack: duration in seconds without blinks before the popup appears
        :param alert_seconds_cooldown: duration in seconds before the popup can appear again
        if the user dismisses it
        :param width: width of the window, default is set to the width of the gif (320px)
        """
        super().__init__()

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Set up the movie
        path = "images/blink_animated.gif"
        assert os.path.exists(path)
        self.movie = QMovie(path)
        assert self.movie.isValid(), f"{path} file invalid "

        self.gif_label = QLabel("Blinking Gif")
        self.gif_label.setMovie(self.movie)
        self.gif_label.setFixedWidth(width)

        layout.addWidget(self.gif_label)

        # Set up the text
        self.text_label = QLabel("Text")
        self.text_label.setText(
            f"You didn't blink in the last {duration_lack} seconds"
        )
        self.text_label.setFixedWidth(width)
        self.text_label.setAlignment(Qt.AlignCenter)  # type: ignore[attr-defined]
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.text_label)

        self.informative_text_label = QLabel("Informative Text")
        self.informative_text_label.setText(
            "Blink now to close the window or click 'Dismiss' to "
            f"dismiss for {alert_seconds_cooldown} seconds"
        )
        self.informative_text_label.setFixedWidth(width)
        self.informative_text_label.setAlignment(Qt.AlignCenter)  # type: ignore[attr-defined]
        self.informative_text_label.setWordWrap(True)
        layout.addWidget(self.informative_text_label)

        # Set up the button
        self.button = QPushButton("Dismiss")
        self.button.setFixedWidth(width)
        self.button.clicked.connect(
            lambda: (
                dismiss_callback(),
                self.close()
            )
        )
        layout.addWidget(self.button)

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
            self.center_window()

            # Make sure the window is on top of other applications
            self.raise_()  # for MacOS
            self.activateWindow()  # for Windows

    def center_window(self) -> None:
        """Center the window on the screen"""
        center = QScreen.availableGeometry(QApplication.primaryScreen()).center()
        geo = self.frameGeometry()
        geo.moveCenter(center)
        self.move(geo.topLeft())
