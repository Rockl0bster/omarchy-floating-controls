import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "bin/floating-controls-workspace"


class WorkspaceTests(unittest.TestCase):
    def test_uses_current_mapping_and_falls_back_to_legacy(self):
        address = "0x123"
        clients = [{
            "address": address,
            "floating": True,
            "tags": ["omarchy-floating-workspace"],
            "workspace": {"id": 11},
            "monitor": 4,
        }]
        monitors = [{"id": 4, "name": "DP-3"}]
        for has_current in (True, False):
            with self.subTest(has_current=has_current), tempfile.TemporaryDirectory() as temp:
                state = Path(temp) / "omarchy"
                current = state / "monitors/workspaces"
                current.parent.mkdir(parents=True)
                legacy = state / "monitor-workspaces"
                if has_current:
                    current.write_text("1\tDP-3\tExternal monitor\n")
                    legacy.write_text("0\tDP-3\n")
                else:
                    legacy.write_text("1\tDP-3\n")

                with (
                    patch.dict(os.environ, {"XDG_STATE_HOME": temp}),
                    patch.object(sys, "argv", [str(SCRIPT), address, "next"]),
                    patch("subprocess.check_output", side_effect=[json.dumps(clients), json.dumps(monitors)]),
                    patch("subprocess.run") as dispatch,
                ):
                    with self.assertRaises(SystemExit) as exit_status:
                        runpy.run_path(str(SCRIPT), run_name="__main__")

                self.assertEqual(exit_status.exception.code, 0)
                dispatch.assert_called_once_with(
                    ["hyprctl", "dispatch",
                     'hl.dsp.window.move({ window = "address:0x123", workspace = 12, follow = false })'],
                    check=True, stdout=subprocess.DEVNULL,
                )
