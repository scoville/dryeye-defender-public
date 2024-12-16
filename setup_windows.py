"""Build instructions"""
import os
import sys
from cx_Freeze import setup, Executable

BASE = "Win32GUI" if sys.platform == "win32" else None

directory_table = [
    ("ProgramMenuFolder", "TARGETDIR", "."),
    ("MyProgramMenu", "ProgramMenuFolder", "MYPROG~1|My Program"),
]

msi_data = {
    "Directory": directory_table,
    "ProgId": [
        ("Prog.Id", None, None, "Software for improving eye health and preventing dry eye disease",
         "Ic:onId", None),
    ],
    "Icon": [
        ("IconId", "assets/icon.ico"),
    ],
}

# At time of writing it seems CX_Freeze 7.2 does not support using pyproject.toml for windows
# builds, hence why this is not DRY with much overlap with pyproject.toml.
# Note that build_exe_options is not omittted, I found assets were not included in windows.
build_exe_options = {
    "packages": ["playsound"],
    "includes": ["playsound"],
    "excludes": ["tkinter", "pytest", "cx-Freeze", "coverage", "mypy", "mypy-extensions", "pycodestyle", "pydocstyle", "pylint", "pylint-quotes", "pytest-timeout", "pytest-timeout", "pytest-xdist", "openvino-dev", "stubs"],
    "optimize": 0,
    "zip_include_packages": ["encodings", "PySide6"],
    "include_files": [
        ['submodules/blink-detection/assets/mediapipe/face_landmarker_v2_with_blendshapes.task', 'assets/mediapipe/face_landmarker_v2_with_blendshapes.task'],
        ['assets/blink.png', 'assets/blink.png'],
        ['assets/blink_animated.gif', 'assets/blink_animated.gif'],
        ['assets/blink_animated_anime.gif', 'assets/blink_animated_anime.gif'],
        ['assets/Logo.png', 'assets/Logo.png'],
        ['assets/audiocheck.net_sin_800Hz_-3dBFS_0.19s.wav', 'assets/audiocheck.net_sin_800Hz_-3dBFS_0.19s.wav'],
        ['assets/AvenirNextLTPro-Regular.otf', 'assets/AvenirNextLTPro-Regular.otf'],
        ['assets/AvenirNextLTPro-Bold.otf', 'assets/AvenirNextLTPro-Bold.otf'],
        ['assets/AvenirNextLTPro-It.otf', 'assets/AvenirNextLTPro-It.otf'],
        ['LICENSE', 'LICENSE'],
        ['NOTICE', 'NOTICE']
    ],
    "silent_level": 1
}

bdist_msi_options = {
    "add_to_path": False,
    "data": msi_data,
    "target_name": "dryeye_defender"
}

executables = [
    Executable("dryeye_defender/__main__.py",
               base=BASE,
               icon="assets/icon.ico",
               target_name="dryeye_defender",
               shortcut_name="DryEye Defender",
               shortcut_dir="ProgramMenuFolder",
               )
]

setup(version=os.environ["RELEASE_VERSION"],
      executables=executables,
      options={
          "bdist_msi": bdist_msi_options,
          "build_exe": build_exe_options
      },
      )
