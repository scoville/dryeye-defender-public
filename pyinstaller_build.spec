#!/usr/bin/env python
# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['dryeye_defender/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ['submodules/blink-detection/assets/mediapipe/face_landmarker_v2_with_blendshapes.task', 'assets/mediapipe'],
        ['assets/blink.png', 'assets/'],
        ['assets/blink_animated.gif', 'assets/'],
        ['assets/blink_animated_anime.gif', 'assets/'],
        ['assets/Logo.png', 'assets/'],
        ['assets/audiocheck.net_sin_800Hz_-3dBFS_0.19s.wav', 'assets/'],
        ['assets/AvenirNextLTPro-Regular.otf', 'assets/'],
        ['assets/AvenirNextLTPro-Bold.otf', 'assets/'],
        ['assets/AvenirNextLTPro-It.otf', 'assets/']
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='__main__',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='6.0.0.rc18'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='dryeye_defender',
)
app = BUNDLE(
    coll,
    name='DryEye Defender.app',
    icon='assets/icon.icns',
    bundle_identifier=None,
    info_plist={
                'NSCameraUsageDescription':
                    'This app requires access to the camera for the blink detection feature.'
                    ' Please enable this in your system settings.',
                'CFBundleShortVersionString': '6.0.0.rc18',
             }
)
