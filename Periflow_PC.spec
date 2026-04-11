# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('build_assets\\periflow_logo.png', 'build_assets'),
    ],
    hiddenimports=[
        'cv2',
        'numpy',
        'PIL',
        'pyaudio',
        'pynput',
        'pyvirtualcam',
        'pyvirtualcam._native_windows_obs',
        'pyvirtualcam._native_windows_unity_capture',
        'typing_extensions',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'test',
        'tests',
        'unittest',
        'numpy.f2py',
        'numpy.testing',
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Periflow_PC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='build_assets\\periflow.ico',
)
