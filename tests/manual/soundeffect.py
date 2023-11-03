import sys
import time
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtMultimedia import QSoundEffect


def main():
    app = QGuiApplication(sys.argv)
    filename = "assets/audiocheck.net_sin_800Hz_-3dBFS_0.19s.wav"
    effect = QSoundEffect()
    effect.setSource(QUrl.fromLocalFile(filename))
    effect.setLoopCount(1)  # play once
    effect.play()
    time.sleep(2)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
