#!/usr/bin/env python3
"""Install/remove user-owned integration; never change keybindings."""
import argparse
from datetime import datetime
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
DEST = HOME / '.local/share/omarchy-floating-controls'
CONFIG = HOME / '.config/hypr/hyprland.lua'
MODULE = HOME / '.config/hypr/floating-controls.lua'
LINE = 'require("hypr.floating-controls")'
LEGACY = 'require("hypr.titlebar-style")'
ANCHOR = 'require("default.hypr.toggles")'


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
    parser.add_argument('action', choices=['install','uninstall'])
    parser.add_argument('--migrate-personal', action='store_true')
    args = parser.parse_args()
    old = CONFIG.read_text()
    new = edit(old, args.action == 'uninstall', args.migrate_personal)
    if args.action == 'install':
        if not Path('/usr/lib/omarchy-hyprland-titlebars/titlebars.so').exists():
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
    backup = CONFIG.with_name('hyprland.lua.backup-floating-controls-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    shutil.copy2(CONFIG, backup)
    CONFIG.write_text(new)
    subprocess.run(['hyprctl','reload'],check=True)
    errors = subprocess.check_output(['hyprctl','configerrors'],text=True).strip()
    if errors:
        CONFIG.write_text(old)
        subprocess.run(['hyprctl','reload'],check=True)
        raise SystemExit('Configuration rolled back: ' + errors)
    if args.action == 'uninstall' and MODULE.is_symlink() and MODULE.resolve() == DEST/'hypr/floating-controls.lua':
        MODULE.unlink()
    print(f'{args.action}: complete. Config backup: {backup}')

if __name__ == '__main__':
    main()
