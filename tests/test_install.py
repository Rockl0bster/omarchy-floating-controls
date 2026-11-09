import unittest
import manage
import contextlib
import io
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

class InstallTests(unittest.TestCase):
    def test_repeat_and_remove_preserve_user_configuration(self):
        original = '-- personal\nrequire("hypr.bindings")\n' + manage.ANCHOR + '\n'
        installed = manage.edit(original)
        self.assertEqual(manage.edit(installed), installed)
        self.assertEqual(manage.edit(installed, uninstall=True), original)
        self.assertLess(installed.index(manage.LINE), installed.index(manage.ANCHOR))

    def test_legacy_requires_explicit_migration(self):
        original = manage.LEGACY + '\n' + manage.ANCHOR + '\n'
        with self.assertRaises(ValueError): manage.edit(original)
        self.assertNotIn(manage.LEGACY, manage.edit(original, migrate=True))

    def test_unknown_config_rejected(self):
        with self.assertRaises(ValueError): manage.edit('-- custom config\n')

    def test_status_and_install_uninstall(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            config = home / 'hyprland.lua'
            config.write_text('-- personal\n' + manage.ANCHOR + '\n')
            original = config.read_text()
            module = home / 'floating-controls.lua'
            dest = home / 'runtime'
            titlebars = home / 'titlebars.so'
            titlebars.touch()
            with patch.multiple(manage, CONFIG=config, MODULE=module, DEST=dest, TITLEBARS=titlebars), \
                 patch.object(manage.subprocess, 'run') as reload, \
                 patch.object(manage.subprocess, 'check_output', return_value=''):
                def call(action):
                    with patch.object(sys, 'argv', ['manage.py', action]), contextlib.redirect_stdout(io.StringIO()) as out:
                        manage.main()
                    return out.getvalue()
                self.assertEqual(call('status').strip(), 'not-installed')
                call('install')
                self.assertEqual(call('status').strip(), 'installed')
                self.assertTrue(module.is_symlink())
                call('uninstall')
                self.assertEqual(config.read_text(), original)
                self.assertFalse(module.exists())
                self.assertEqual(call('status').strip(), 'not-installed')
                self.assertEqual(reload.call_count, 2)

    def test_failed_reload_restores_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            config = home / 'hyprland.lua'
            original = '-- personal\n' + manage.ANCHOR + '\n'
            config.write_text(original)
            titlebars = home / 'titlebars.so'
            titlebars.touch()
            failure = subprocess.CalledProcessError(1, 'hyprctl')
            with patch.multiple(manage, CONFIG=config, MODULE=home/'floating-controls.lua', DEST=home/'runtime', TITLEBARS=titlebars), \
                 patch.object(manage.subprocess, 'run', side_effect=[failure, None]), \
                 patch.object(sys, 'argv', ['manage.py', 'install']):
                with self.assertRaisesRegex(SystemExit, 'rolled back'):
                    manage.main()
            self.assertEqual(config.read_text(), original)
