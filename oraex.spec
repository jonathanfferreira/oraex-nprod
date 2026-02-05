# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec para ORAEX Automation
=======================================
Gera executáveis standalone para Windows/Linux

Uso:
    pyinstaller oraex.spec

Resultado:
    dist/oraex-runner      - Executável do runner
    dist/oraex-webhook     - Executável do webhook receiver
"""

import os
from PyInstaller.utils.hooks import collect_submodules

# Coletar todos os submódulos
hiddenimports = collect_submodules('automacao')
hiddenimports += ['flask', 'requests', 'cx_Oracle', 'paramiko']

# === RUNNER EXECUTABLE ===
runner_a = Analysis(
    ['automacao/runbooks/runner.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('automacao/utils/*.py', 'automacao/utils'),
        ('automacao/runbooks/*.py', 'automacao/runbooks'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy'],
    noarchive=False,
)

runner_pyz = PYZ(runner_a.pure)

runner_exe = EXE(
    runner_pyz,
    runner_a.scripts,
    runner_a.binaries,
    runner_a.datas,
    [],
    name='oraex-runner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='presentation_site/assets/oraex_logo.ico' if os.path.exists('presentation_site/assets/oraex_logo.ico') else None,
)

# === WEBHOOK RECEIVER EXECUTABLE ===
webhook_a = Analysis(
    ['webhook_receiver.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('automacao/runbooks/*.py', 'automacao/runbooks'),
        ('automacao/utils/*.py', 'automacao/utils'),
    ],
    hiddenimports=hiddenimports + ['werkzeug', 'jinja2', 'markupsafe'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy'],
    noarchive=False,
)

webhook_pyz = PYZ(webhook_a.pure)

webhook_exe = EXE(
    webhook_pyz,
    webhook_a.scripts,
    webhook_a.binaries,
    webhook_a.datas,
    [],
    name='oraex-webhook',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='presentation_site/assets/oraex_logo.ico' if os.path.exists('presentation_site/assets/oraex_logo.ico') else None,
)

# === COLLECT ALL ===
coll = COLLECT(
    runner_exe,
    webhook_exe,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='oraex-automation',
)
