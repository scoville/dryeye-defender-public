import sys
from cx_Freeze import setup, Executable


base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('eyeblink_gui/__main__.py', base=base, target_name='eyehealth')
]

setup(version="2.0.2",
      executables=executables)
