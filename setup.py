from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
build_options = {'packages': [], 'excludes': [], 'include_files':[
    'submodules/eyeblink-detection/assets/face-detection-adas-0001/FP16-INT8/face-detection-adas-0001.bin',
    'submodules/eyeblink-detection/assets/face-detection-adas-0001/FP16-INT8/face-detection-adas-0001.xml',
    'submodules/eyeblink-detection/assets/vino_preprocess/lmks.bin',
    'submodules/eyeblink-detection/assets/vino_preprocess/lmks.xml',
    'images/blink.png'
    ]}

import sys
base = 'Win32GUI' if sys.platform=='win32' else None

executables = [
    Executable('eyeblink_gui/__main__.py', base=base, target_name = 'eyeblinkgui')
]

setup(name='eyeblink_gui',
      version = '1.0',
      description = 'Prototype for eye health',
      options = {'build_exe': build_options},
      executables = executables)