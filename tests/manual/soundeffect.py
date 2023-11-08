"""Demo of how to play sound effects"""
import sys
import time
from PySide6.QtCore import QUrl, QCoreApplication
from PySide6.QtMultimedia import QSoundEffect, QMediaDevices, QAudioDevice


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
    print(f"Audio device id {audioDevice.id()}")
    assert audioDevice.isDefault(), f"isDefaultAudio device: {audioDevice.isDefault()}"
    return audioDevice


effect = None


def main() -> None:
    """Demo of sound effect usage"""
    app = QCoreApplication(sys.argv)

    filename = "assets/audiocheck.net_sin_800Hz_-3dBFS_0.19s.wav"

    # filename = "assets/file_example_WAV_1MG.wav"
    global effect
    effect = QSoundEffect(get_default_sound_device())
    # effect.setParent(app)
    effect.loadedChanged.connect(
        lambda: print("loadedChanged Changed", effect.status().name)
    )
    effect.sourceChanged.connect(lambda: print("sourceChanged Changed"))
    effect.statusChanged.connect(lambda: print("mutedChanged Changed"))
    effect.volumeChanged.connect(lambda: print("volumeChanged Changed"))
    effect.loopsRemainingChanged.connect(lambda: print("loopsRemainingChanged Changed"))
    effect.playingChanged.connect(lambda: print("playingChanged Changed"))
    effect.audioDeviceChanged.connect(lambda: print("audioDeviceChanged Changed"))
    effect.setSource(QUrl.fromLocalFile(filename))
    effect.setLoopCount(1)  # play once

    # while effect.status().name == "Loading":
    #     time.sleep(0.2)
    #     print(effect.status().name)

    print(effect.status().name)
    time.sleep(2)
    effect.play()
    print(effect.status().name)
    print("here")
    time.sleep(2)
    effect.play()
    print("here2")
    print(effect.status().name)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
