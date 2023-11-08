import sys
from typing import Any

from PySide6 import QtMultimedia, QtWidgets
from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QAudioDevice, QMediaDevices, QMediaPlayer, QAudioOutput


def get_default_sound_device() -> QAudioDevice:
    devices = QMediaDevices.audioOutputs()
    device_list = {}
    number = 1
    for device in devices:
        default = " "
        device_list[str(number)] = QAudioDevice(device)
        if device.isDefault():
            default = "#"
            default_device_id = number
        print(f"{default} {number} - {device.description()}")
        number += 1
    audioDevice = device_list[str(default_device_id)]
    return audioDevice


class MyWidget(QtWidgets.QWidget):
    def __init__(self, parent: Any = None) -> None:
        filename = "assets/audiocheck.net_sin_800Hz_-3dBFS_0.19s.wav"
        filename = "assets/file_example_WAV_1MG.wav"
        super().__init__(parent)
        mainLayout = QtWidgets.QVBoxLayout(self)
        self.sound_button = QtWidgets.QPushButton(text="Play")
        mainLayout.addWidget(self.sound_button)
        try:
            self.player = QMediaPlayer()
            # self.player.setAudioOutput(audio_output)
            self.player.setSource(QUrl.fromLocalFile(filename))
            self.sound_button.clicked.connect(self.player.play)
        except Exception:
            print(self.player.error(), self.player.errorString())
            raise


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = MyWidget()
    widget.resize(200, 100)
    widget.show()
    sys.exit(app.exec())
