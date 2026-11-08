# Omarchy Floating Controls

Mouse-friendly window controls for Omarchy’s **floating workspace mode**.
Adds previous/next workspace and left/right half-screen buttons to Omarchy’s
native titlebars. Existing minimize, maximize and close controls remain.
No keyboard shortcuts are installed or changed.

- Filled ◀ / ▶ symbols, with colors inherited from the current theme.
- Move the clicked window without following it, including to empty workspaces.
- Apps that enforce a minimum width may occupy more than half the screen. The
  requested outer edge is preserved after resizing; an app wider than the entire
  usable screen cannot be made to fit by this extension.
- Half-screen placement respects the top bar, titlebar, borders, rotation and scaling.
- Actions are restricted to windows tagged by Omarchy’s floating workspace mode.

## Requirements and limits

Initial release targets Omarchy’s Lua configuration and native
`omarchy-hyprland-titlebars` package. Python 3 and `hyprctl` are required.
Workspace navigation currently supports Omarchy’s standard ten-slot monitor banks;
it reads the current monitor mapping, including `XDG_STATE_HOME`. Custom workspace
numbering is not yet supported. At the first/last slot the arrow does nothing.
Only four visible workspace slots in a bar does not limit navigation to four.
Compact-workspaces may renumber a workspace after a move; this extension does not
change that plugin’s settings. Special workspaces and guest workspaces outside the
monitor’s bank are excluded. Other titlebar extensions may conflict.

This is a Lua/configuration extension, not a Quickshell bar widget. Direct
`omarchy plugin add` integration is not provided in this initial release.
The integration wraps native button registration and therefore depends on
Omarchy’s titlebar API and loading order. Updates require compatibility checks.

## Install

```sh
git clone https://github.com/Rockl0bster/omarchy-floating-controls.git
cd omarchy-floating-controls
python3 manage.py install
```

No sudo. Installation copies runtime files to `~/.local/share/omarchy-floating-controls`,
links a Lua module under `~/.config/hypr`, backs up `hyprland.lua`, and inserts one
require before the Omarchy toggles import. Installation can be repeated.
The author's previous personal setup can be migrated with `--migrate-personal`;
its original files remain available but its require is removed to avoid duplicate buttons.

## Update / remove

```sh
git pull --ff-only
python3 manage.py install
# Remove integration and restore native controls:
python3 manage.py uninstall
```

Removal preserves runtime files and backups for recovery, removes only our import
and symlink, and does not reactivate the old personal customization.

## Development

```sh
python3 -m unittest discover -s tests -v
```

Testing on multiple physical screens, theme changes and real pointer interactions
is part of the release checklist. Mock tests do not replace this visual validation.

MIT license. Uses Omarchy’s installed titlebar plugin; does not bundle its native code.
