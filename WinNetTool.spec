# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('app_icon.ico', '.')],
    hiddenimports=[
        'psutil', 'nmap', 'requests', 'locale', 'datetime',
        'network', 'network.base', 'network.ports', 'network.dhcp',
        'network.hosts', 'network.services', 'network.wifi', 'network.version',
        'gui', 'gui.main_window', 'gui.styles', 'gui.workers', 'gui.dialogs',
        'gui.panels', 'gui.panels.welcome', 'gui.panels.port_panel',
        'gui.panels.dhcp_panel', 'gui.panels.host_panel',
        'gui.panels.service_panel', 'gui.panels.wifi_panel',
        'gui.panels.update_panel', 'utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WinNetTool',
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
    uac_admin=True,
    icon=['app_icon.ico'],
)
