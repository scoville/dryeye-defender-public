# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['eyeblink_gui/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ['submodules/eyeblink-detection/assets/mediapipe/face_landmarker_v2_with_blendshapes.task', 'assets/mediapipe'],
        ['images/blink.png', 'assets/images'],
        ['images/blink_animated.gif', 'assets/images'],
        ['images/blink_animated_anime.gif', 'assets/images']
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
    version='3.0.0'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='eyehealth',
)
app = BUNDLE(
    coll,
    name='EyeblinkHealth.app',
    icon='images/icon.icns',
    bundle_identifier=None,
    info_plist={
                'NSCameraUsageDescription': 'This app requires access to the camera for eye blink detection.',
                'CFBundleShortVersionString': '3.0.0',
             }
)
