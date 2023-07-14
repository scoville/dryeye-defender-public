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
        ("IconId", "images/icon.ico"),
    ],
}

bdist_msi_options = {
    "add_to_path": False,
    "data": msi_data,
    "target_name": "dryeye_defender"
}

executables = [
    Executable("dryeye_defender/__main__.py",
               base=BASE,
               icon="images/icon.ico",
               target_name="dryeye_defender",
               shortcut_name="DryEye Defender",
               shortcut_dir="ProgramMenuFolder",
               )
]

setup(version=os.environ["RELEASE_VERSION"],
      executables=executables,
      options={
          "bdist_msi": bdist_msi_options,
      },
      )
