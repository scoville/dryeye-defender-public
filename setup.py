import sys
import os
from cx_Freeze import setup, Executable

version="3.0.0",

base = 'Win32GUI' if sys.platform == 'win32' else None

directory_table = [
    ("ProgramMenuFolder", "TARGETDIR", "."),
    ("MyProgramMenu", "ProgramMenuFolder", "MYPROG~1|My Program"),
]

msi_data = {
    "Directory": directory_table,
    "ProgId": [
        ("Prog.Id", None, None, "Eyehealth software description", "Ic:onId", None),
    ],
    "Icon": [
        ("IconId", "images/icon.ico"),
    ],
}

bdist_msi_options = {
    "add_to_path": False,
    "data": msi_data,
}


bdist_mac_options = {
    "bundle_name": "EyeblinkHealth",
    "iconfile": "images/icon.icns",  # replace with your icon file    
    # "codesign_identity": "common name of the certificate",  # replace with your Developer ID
    # you can also specify other codesign options
    # "codesign_entitlements": "myapp.entitlements",  # replace with your entitlements file if any
    # "codesign_deep": True,
    # "codesign_resource_rules": "resource_rules.plist"  # replace with your resource rules file if any

    # "custom_info_plist": "Info.plist",  # replace with your plist file if any
    # Add other options as needed
}

bdist_dmg_options = {
    "volume_label": "Eyeblink_GUI",
    "applications_shortcut": True,
    # Add other options as needed
}

executables = [
    Executable('eyeblink_gui/__main__.py',
               base=base,
               icon='images/icon.ico',
               target_name='eyehealth',
               shortcut_name="EyeHealth",
               shortcut_dir="ProgramMenuFolder",
               )
]

setup(version="3.0.0",
      executables=executables,
      options={
          "bdist_msi": bdist_msi_options,
          "bdist_mac": bdist_mac_options,
          "bdist_dmg": bdist_dmg_options,
      },
      )

