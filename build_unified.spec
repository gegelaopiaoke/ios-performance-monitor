# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件 - 跨平台统一性能监控工具
使用方法: pyinstaller build_unified.spec
"""

block_cipher = None

a = Analysis(
    ['start_unified_monitor.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('android', 'android'),
        ('ios', 'ios'),
    ],
    hiddenimports=[
        'flask',
        'flask_socketio',
        'psutil',
        'engineio',
        'socketio',
        'engineio.async_drivers.threading',
        'simple_websocket',
        'wsproto',
        # iOS 相关 (Windows 上可选)
        'py_ios_device',
        'pymobiledevice3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='跨平台性能监控',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico'  # 取消注释并添加图标文件
)
