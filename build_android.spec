# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 配置文件 - Android 性能监控工具
使用方法: pyinstaller build_android.spec
"""

block_cipher = None

import os

# 动态添加数据文件，避免空目录导致打包失败
datas = [
    ('templates', 'templates'),
    ('android', 'android'),
    ('ios', 'ios'),  # 包含 ios 目录以支持内存泄漏检测模块
]

# 只在 static 目录存在且不为空时添加
if os.path.exists('static') and os.listdir('static'):
    datas.append(('static', 'static'))

a = Analysis(
    ['start_android_monitor.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flask',
        'flask_socketio',
        'psutil',
        'engineio',
        'socketio',
        'engineio.async_drivers.threading',
        'simple_websocket',
        'wsproto',
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
    name='Android性能监控',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台窗口以显示日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico'  # 取消注释并添加图标文件
)
