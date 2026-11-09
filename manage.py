#!/usr/bin/env python3
"""Install/remove user-owned integration; never change keybindings."""
import argparse
import json
from datetime import datetime
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
DEST = HOME / '.local/share/omarchy-floating-controls'
CONFIG = HOME / '.config/hypr/hyprland.lua'
MODULE = HOME / '.config/hypr/floating-controls.lua'
TITLEBARS = Path('/usr/lib/omarchy-hyprland-titlebars/titlebars.so')
LINE = 'require("hypr.floating-controls")'
LEGACY = 'require("hypr.titlebar-style")'
ANCHOR = 'require("default.hypr.toggles")'
MODES = ('both', 'workspace', 'halves', 'none')


def read_mode():
    path = DEST / 'settings.json'
    if not path.exists():
        return 'both'
    mode = json.loads(path.read_text()).get('mode')
    if mode not in MODES:
        raise ValueError('Invalid Floating Controls mode.')
    return mode


def edit(text, uninstall=False, migrate=False):
    lines = text.splitlines(keepends=True)
    lines = [line for line in lines if line.strip() != LINE]
    if uninstall:
        return ''.join(lines)
    if migrate:
        lines = [line for line in lines if line.strip() != LEGACY]
    elif any(line.strip() == LEGACY for line in lines):
        raise ValueError('Existing personal titlebar customization: use --migrate-personal after review.')
    indices = [i for i,line in enumerate(lines) if line.strip() == ANCHOR]
    if len(indices) != 1:
        raise ValueError('Expected one Omarchy toggles import; refusing to guess insertion point.')
    lines.insert(indices[0], LINE + '\n')
    return ''.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['install','uninstall','status'])
    parser.add_argument('--migrate-personal', action='store_true')
    parser.add_argument('--mode', choices=MODES)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    old = CONFIG.read_text()
    if args.action == 'status':
        active = any(line.strip() == LINE for line in old.splitlines())
        linked = MODULE.is_symlink() and MODULE.resolve() == DEST / 'hypr/floating-controls.lua'
        installed = active and linked and MODULE.is_file()
        print(json.dumps({'installed': installed, 'mode': read_mode()}) if args.json
              else 'installed' if installed else 'not-installed')
        return
    mode = args.mode or read_mode()
    settings = DEST / 'settings.json'
    previous_settings = settings.read_bytes() if settings.exists() else None
    new = edit(old, args.action == 'uninstall', args.migrate_personal)
    if args.action == 'install':
        if not TITLEBARS.exists():
            raise SystemExit('Omarchy native titlebars are required.')
        if MODULE.exists() and not MODULE.is_symlink():
            raise SystemExit('Refusing to replace an existing floating-controls.lua file.')
        if MODULE.is_symlink() and MODULE.resolve() != DEST / 'hypr/floating-controls.lua':
            raise SystemExit('Refusing to replace another plugin’s symlink.')
        if ROOT != DEST:
            DEST.mkdir(parents=True, exist_ok=True)
            for name in ('bin','hypr'):
                shutil.copytree(ROOT/name, DEST/name, dirs_exist_ok=True)
        if not MODULE.is_symlink():
            MODULE.symlink_to(DEST/'hypr/floating-controls.lua')
        settings.write_text(json.dumps({'mode': mode}) + '\n')
    backup = CONFIG.with_name('hyprland.lua.backup-floating-controls-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    shutil.copy2(CONFIG, backup)
    CONFIG.write_text(new)
    try:
        subprocess.run(['hyprctl','reload'],check=True)
        errors = subprocess.check_output(['hyprctl','configerrors'],text=True).strip()
        if errors:
            raise RuntimeError(errors)
    except (OSError, subprocess.CalledProcessError, RuntimeError) as error:
        CONFIG.write_text(old)
        if args.action == 'install':
            if previous_settings is None:
                settings.unlink(missing_ok=True)
            else:
                settings.write_bytes(previous_settings)
        try:
            subprocess.run(['hyprctl','reload'],check=True)
        except (OSError, subprocess.CalledProcessError):
            raise SystemExit('Configuration restored from memory; reload failed. Backup: ' + str(backup)) from error
        raise SystemExit('Configuration rolled back: ' + str(error)) from error
    if args.action == 'uninstall' and MODULE.is_symlink() and MODULE.resolve() == DEST/'hypr/floating-controls.lua':
        MODULE.unlink()
    print(f'{args.action}: complete. Config backup: {backup}')

if __name__ == '__main__':
    main()
