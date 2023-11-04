"""Demo of how to play sound effects"""
import sys
import time
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtMultimedia import QSoundEffect


def main() -> None:
    """Demo of sound effect usage"""
    app = QGuiApplication(sys.argv)
    filename = "assets/audiocheck.net_sin_800Hz_-3dBFS_0.19s.wav"

    filename = "assets/file_example_WAV_1MG.wav"
    effect = QSoundEffect()
    effect.setSource(QUrl.fromLocalFile(filename))
    effect.setLoopCount(1)  # play once
    time.sleep(2)  # wait for it to load
    effect.play()
    print(f"effect status: {effect.status()}")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
