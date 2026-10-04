#!/usr/bin/env python3
"""Regression tests for Keymap Editor-owned binding values."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import re
import shutil
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / "scripts" / "verify-mona2-config.py"


def load_verifier():
    spec = spec_from_file_location("verify_mona2_config", VERIFIER)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load verifier")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def remove_safe_access(text: str, target: int) -> str:
    patterns = (
        rf"&lt\s+{target}\s+[^\s>]+",
        rf"&mouse_lt\s+{target}\s+[^\s>]+",
        rf"&mo\s+{target}\b",
    )
    replacements = 0
    for pattern in patterns:
        text, count = re.subn(pattern, "&kp F15", text)
        replacements += count
    if replacements == 0:
        raise AssertionError(f"test fixture has no safe access to layer {target}")
    return text


def main() -> None:
    verifier = load_verifier()
    verifier.main()

    with tempfile.TemporaryDirectory(prefix="mona2-keymap-editor-") as temp_dir:
        test_root = Path(temp_dir) / "repo"
        shutil.copytree(ROOT, test_root, ignore=shutil.ignore_patterns(".git", "gesture_state_test"))
        keymap_path = test_root / "config" / "mona2.keymap"
        keymap = keymap_path.read_text(encoding="utf-8")

        # Change every existing layer-tap action without assuming any current
        # key value or physical position. This remains valid after later Editor
        # commits while directly covering the bfe37ae regression class.
        keymap = re.sub(r"(&lt\s+\d+\s+)[^\s>]+", r"\g<1>F13", keymap)
        keymap_path.write_text(keymap, encoding="utf-8")
        verifier.ROOT = test_root
        verifier.main()

        # Removing the only route to a customized layer is a real structural
        # regression and must still fail.
        keymap = remove_safe_access(keymap, 5)
        keymap_path.write_text(keymap, encoding="utf-8")
        try:
            verifier.main()
        except AssertionError as exc:
            if "must remain reachable" not in str(exc):
                raise
        else:
            raise AssertionError("unreachable customized layer was not rejected")

        # A fixed TO/TG-style transition is not a safe substitute for the
        # momentary/hold route: Setting has no guaranteed normal exit.
        keymap = keymap.replace("&kp F15", "&to 5", 1)
        keymap_path.write_text(keymap, encoding="utf-8")
        try:
            verifier.main()
        except AssertionError as exc:
            if "must remain reachable" not in str(exc):
                raise
        else:
            raise AssertionError("fixed layer transition was accepted as safe reachability")

    print("keymap-editor-contract-test: PASS")


if __name__ == "__main__":
    main()
