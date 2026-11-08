import unittest
import manage

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
