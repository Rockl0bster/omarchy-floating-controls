import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import manage


class ModeTests(unittest.TestCase):
    def test_switch_preserve_and_rollback_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            config = home / 'hyprland.lua'
            config.write_text(manage.ANCHOR + '\n')
            titlebars = home / 'titlebars.so'
            titlebars.touch()
            with patch.multiple(manage, CONFIG=config, MODULE=home/'floating-controls.lua',
                                DEST=home/'runtime', TITLEBARS=titlebars), \
                 patch.object(manage.subprocess, 'run'), \
                 patch.object(manage.subprocess, 'check_output', return_value='') as errors:
                def call(*args):
                    with patch.object(sys, 'argv', ['manage.py', *args]), contextlib.redirect_stdout(io.StringIO()) as out:
                        manage.main()
                    return out.getvalue()
                for mode in manage.MODES:
                    call('install', '--mode', mode)
                    state = json.loads(call('status', '--json'))
                    self.assertEqual(state, {'installed': True, 'mode': mode})
                call('install', '--mode', 'halves')
                call('install')
                self.assertEqual(manage.read_mode(), 'halves')
                previous = config.read_text()
                errors.return_value = 'invalid config'
                with self.assertRaisesRegex(SystemExit, 'rolled back'):
                    call('install', '--mode', 'workspace')
                self.assertEqual(manage.read_mode(), 'halves')
                self.assertEqual(config.read_text(), previous)

    @unittest.skipUnless(shutil.which('lua'), 'Lua interpreter required')
    def test_lua_registers_only_selected_buttons(self):
        script = r'''
local test_home, module_path = arg[1], arg[2]
local getenv = os.getenv
os.getenv = function(key) if key == "HOME" then return test_home end return getenv(key) end
local buttons = {}
hl = { plugin = {} }
hl.plugin.load = function(path)
  hl.plugin.hyprbars = { add_button = function(button) table.insert(buttons, button.icon) end }
end
dofile(module_path)
hl.plugin.load("/usr/lib/omarchy-hyprland-titlebars/titlebars.so")
for _, icon in ipairs({"□", "−", "×"}) do hl.plugin.hyprbars.add_button({icon = icon}) end
for _, icon in ipairs(buttons) do print(icon) end
'''
        with tempfile.TemporaryDirectory() as temp:
            settings = Path(temp)/'.local/share/omarchy-floating-controls/settings.json'
            settings.parent.mkdir(parents=True)
            cases = [(None, ['◧','□','◨','−','▶','◀','×']),
                     ('both', ['◧','□','◨','−','▶','◀','×']),
                     ('workspace', ['□','−','▶','◀','×']),
                     ('halves', ['◧','□','◨','−','×']),
                     ('none', ['□','−','×'])]
            for mode, expected in cases:
                with self.subTest(mode=mode):
                    if mode:
                        settings.write_text(json.dumps({'mode': mode}))
                    actual = subprocess.check_output(
                        ['lua','-',temp,str(manage.ROOT/'hypr/floating-controls.lua')],
                        input=script, text=True).splitlines()
                    self.assertEqual(actual, expected)
