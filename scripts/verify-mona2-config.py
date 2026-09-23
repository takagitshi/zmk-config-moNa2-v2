#!/usr/bin/env python3
"""Fast source-level contracts for the customized moNa2 configuration."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> int:
    keymap = read("config/mona2.keymap")
    dtsi = read("boards/shields/mona2/mona2.dtsi")
    right = read("boards/shields/mona2/mona2_r.overlay")
    right_conf = read("config/mona2_r.conf")
    west = read("config/west.yml")
    builds = read("build.yaml")
    reset_build = read("build-reset.yaml")
    workflow = read(".github/workflows/build.yml")

    names = re.findall(r'display-name\s*=\s*"([^"]+)";', keymap)
    require(
        names == ["Mouse Layer-Tap", "Base", "Mouse", "Scroll", "Gesture", "symbol",
                  "number", "move", "setting", "User 8"],
        f"unexpected behavior/layer display names: {names}",
    )
    require('bindings = <&mo>, <&mkp>;' in keymap, "Mouse Layer-Tap contract missing")
    require('&mouse_lt 2 MB3' in keymap, "Mouse Layer-Tap is not assigned")
    require('excluded-positions = <17 18 19 21 33 34 41>;' in keymap,
            "AML exclusions changed without contract update")
    require('&zip_temp_layer 1 10000' in keymap and '&zip_temp_layer 1 10000' in right,
            "AML timeout path missing")

    for fragment in (
        'layer = <3>;', 'binding-layer = <3>;', 'up-position = <7>;',
        'left-position = <17>;', 'right-position = <19>;', 'down-position = <30>;',
        'threshold = <200>;', 'cooldown-ms = <150>;', 'reset-on-layer = <2>;',
    ):
        require(fragment in dtsi, f"gesture contract missing: {fragment}")

    for fragment in (
        'cpi = <1200>;', 'pointer-acceleration;',
        'invert-x;', 'invert-y;',
        'pointer-acceleration-reference-interval-ms = <15>;',
        'pointer-acceleration-scroll-layer = <2>;',
        'pointer-acceleration-gesture-layer = <3>;',
        'layers = <2>;', '<&zip_scroll_scaler 1 10>;', 'process-next;',
    ):
        require(fragment in right, f"pointer contract missing: {fragment}")

    sensor_block = re.search(
        r"trackball_central:\s*trackball_central@0\s*\{(?P<body>.*?)\n\s*\};",
        right,
        re.DOTALL,
    )
    require(sensor_block is not None, "trackball sensor node missing")
    sensor_body = sensor_block.group("body")
    require(re.search(r"^\s*invert-x;", sensor_body, re.MULTILINE) is not None,
            "COROPIT X inversion is not active on the sensor")
    require(re.search(r"^\s*invert-y;", sensor_body, re.MULTILINE) is not None,
            "COROPIT Y inversion is not active on the sensor")
    require(sensor_body.count("invert-x;") == 1 and sensor_body.count("invert-y;") == 1,
            "sensor inversion contract is ambiguous")

    require('CONFIG_PMW3610_REPORT_INTERVAL_MIN=15' in right_conf,
            "15 ms driver aggregation is not enabled")
    require('CONFIG_PMW3610_POINTER_ACCELERATION=y' in right_conf,
            "pointer acceleration Kconfig is not enabled")
    require('CONFIG_RGBLED_WIDGET_SHOW_LAYER_COLORS=y' in right_conf,
            "stock layer LED behavior was removed")
    require('CONFIG_ZMK_STUDIO=y' in right_conf, "standard ZMK Studio was removed")
    require('settings_reset' not in builds, "pairing reset leaked into normal firmware package")
    require('artifact-name: mona2-right-central-coropit' in builds,
            "right-central artifact is not clearly named")
    require('artifact-name: mona2-left-peripheral' in builds,
            "left-peripheral artifact is not clearly named")
    require('shield: settings_reset' in reset_build,
            "separate pairing reset build is missing")
    require('python3 scripts/verify-built-firmware.py' in workflow,
            "generated firmware contract is not enforced in CI")
    require('archive_name: pairing-reset-use-only-when-needed' in workflow,
            "pairing reset is not published as a separate CI artifact")
    require(re.search(r"build-pairing-reset:.*?\n\s+needs: build", workflow, re.DOTALL),
            "pairing reset must run after the normal artifact merge")

    revisions = re.findall(r"revision:\s*([0-9a-f]{40})", west)
    require(len(revisions) == 4, f"expected four pinned dependencies, found {len(revisions)}")
    for forbidden in ("cormoran", "custom-settings", "runtime-input-processor"):
        require(forbidden not in west, f"DYA-only dependency present: {forbidden}")

    print("verify-mona2-config: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"verify-mona2-config: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
