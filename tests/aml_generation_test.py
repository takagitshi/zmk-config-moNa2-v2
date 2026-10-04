#!/usr/bin/env python3
"""Exercise Editor changes through the actual build-time AML generator."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from aml_keymap import aml_header, bindings, layer_body, mouse_positions


class AMLGenerationTest(unittest.TestCase):
    def setUp(self):
        self.keymap = (ROOT / "config/mona2.keymap").read_text(encoding="utf-8")

    def replace_mouse(self, items):
        body = layer_body(self.keymap, "layer_1")
        updated = re.sub(r"(?<!sensor-)\bbindings\s*=\s*<.*?>;",
                         "bindings = <\n" + "\n".join(items) + "\n>;", body, flags=re.DOTALL)
        self.keymap = self.keymap.replace(body, updated, 1)

    def test_binding_add_remove_and_none(self):
        original = mouse_positions(self.keymap)
        items = bindings(layer_body(self.keymap, "layer_1"))
        new = next(i for i, item in enumerate(items) if item == "&trans")
        items[new] = "&kp F13"
        self.replace_mouse(items)
        self.assertEqual(mouse_positions(self.keymap), sorted([*original, new]))
        items[original[0]] = "&none"
        self.replace_mouse(items)
        self.assertEqual(mouse_positions(self.keymap), sorted([*original[1:], new]))

    def test_all_transparent_keeps_cancellation_enabled(self):
        self.replace_mouse(["&trans"] * 42)
        self.assertEqual(mouse_positions(self.keymap), [])
        self.assertIn("#define AML_EXCLUDED_POSITIONS 65535\n", aml_header(self.keymap))

    def test_comments_and_sensor_bindings_are_not_key_positions(self):
        expected = mouse_positions(self.keymap)
        self.keymap = self.keymap.replace("layer_1 {", "layer_1 { /* &kp F13 */\n // &kp F14")
        self.assertEqual(mouse_positions(self.keymap), expected)

    def test_invalid_slot_count_rejected(self):
        self.replace_mouse(["&trans"] * 41)
        with self.assertRaisesRegex(AssertionError, "42 editable slots"):
            aml_header(self.keymap)

    def test_real_generator_selected_wrapper_idempotence_and_updates(self):
        with tempfile.TemporaryDirectory(prefix="mona2-aml-") as temporary:
            directory = Path(temporary)
            source = directory / "selected.keymap"
            source.write_text(self.keymap, encoding="utf-8")
            wrapper = directory / "shield.keymap"
            wrapper.write_text('#include "selected.keymap"\n', encoding="utf-8")
            output = directory / "aml-exclusions.h"
            deps = directory / "inputs.txt"
            command = [sys.executable, str(ROOT / "scripts/generate-aml-exclusions.py"),
                       str(wrapper), str(output), "--key-count", "42", "--depfile", str(deps)]
            subprocess.run(command, check=True)
            self.assertEqual(output.read_text(), aml_header(self.keymap))
            self.assertEqual(deps.read_text().splitlines(), [str(wrapper.resolve()), str(source.resolve())])
            modified = output.stat().st_mtime_ns
            subprocess.run(command, check=True)
            self.assertEqual(output.stat().st_mtime_ns, modified)
            self.replace_mouse(["&none"] * 42)
            source.write_text(self.keymap, encoding="utf-8")
            subprocess.run(command, check=True)
            self.assertEqual(output.read_text(), aml_header(self.keymap))
            self.assertIn("65535", output.read_text())


if __name__ == "__main__":
    unittest.main()
