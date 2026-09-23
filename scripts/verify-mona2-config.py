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
    require('&zip_temp_layer 1 10000' in keymap and '&zip_temp_layer 1 10000' in right,
            "AML timeout path missing")

    layers = {}
    for layer_id in range(9):
        layer = re.search(
            rf"^\s*layer_{layer_id}\s*\{{(?P<body>.*?)^\s*\}};",
            keymap,
            re.MULTILINE | re.DOTALL,
        )
        require(layer is not None, f"missing layer {layer_id}")
        layers[layer_id] = layer.group("body")

    mouse_bindings = re.search(r"bindings\s*=\s*<(?P<body>.*?)>;", layers[1], re.DOTALL)
    require(mouse_bindings is not None, "Mouse layer bindings are missing")
    mouse_binding_text = mouse_bindings.group("body")
    for mouse_button in ("MB1", "MB2", "MB3"):
        require(
            re.search(
                rf"&(?:mkp\s+{mouse_button}|mouse_lt\s+\d+\s+{mouse_button})\b",
                mouse_binding_text,
            ) is not None,
            f"Mouse layer is missing {mouse_button}",
        )
    mouse_behaviors = re.findall(r"&([A-Za-z0-9_]+)\b", mouse_binding_text)
    configured_mouse_positions = [
        position
        for position, behavior in enumerate(mouse_behaviors)
        if behavior not in {"trans", "none"}
    ]
    excluded_match = re.search(r"excluded-positions\s*=\s*<(?P<body>[^>]*)>;", keymap)
    require(excluded_match is not None, "AML excluded-positions is missing")
    excluded_positions = [int(value) for value in excluded_match.group("body").split()]
    require(
        excluded_positions == configured_mouse_positions,
        f"AML exclusions {excluded_positions} do not match Mouse layer positions "
        f"{configured_mouse_positions}",
    )

    for fragment in (
        'layer = <3>;', 'binding-layer = <3>;', 'up-position = <7>;',
        'left-position = <17>;', 'right-position = <19>;', 'down-position = <30>;',
        'threshold = <200>;', 'cooldown-ms = <150>;', 'reset-on-layer = <2>;',
    ):
        require(fragment in dtsi, f"gesture contract missing: {fragment}")

    for fragment in (
        'cpi = <1200>;', 'pointer-acceleration;',
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
    require(re.search(r"^\s*invert-x;", sensor_body, re.MULTILINE) is None,
            "physical-unit contract forbids active sensor X inversion")
    require(re.search(r"^\s*invert-y;", sensor_body, re.MULTILINE) is None,
            "physical-unit contract forbids active sensor Y inversion")
    require('<&zip_xy_transform INPUT_TRANSFORM_Y_INVERT>' in right,
            "base pointer direction transform changed")

    require('CONFIG_PMW3610_REPORT_INTERVAL_MIN=15' in right_conf,
            "15 ms driver aggregation is not enabled")
    require('CONFIG_PMW3610_POINTER_ACCELERATION=y' in right_conf,
            "pointer acceleration Kconfig is not enabled")
    require('CONFIG_ZMK_POINTING_SMOOTH_SCROLLING=y' in right_conf,
            "ZEN smooth scrolling behavior is not enabled")
    require('CONFIG_INPUT_THREAD_STACK_SIZE=4096' in right_conf,
            "input thread stack is too small for the custom pointer pipeline")
    require('CONFIG_ZMK_IDLE_TIMEOUT=300000' in right_conf,
            "ZEN idle timeout is not preserved")
    require('CONFIG_RGBLED_WIDGET_SHOW_LAYER_COLORS=y' in right_conf,
            "stock layer LED behavior was removed")
    require('CONFIG_ZMK_STUDIO=y' in right_conf, "standard ZMK Studio was removed")
    require('settings_reset' not in builds, "pairing reset leaked into normal firmware package")
    require('artifact-name: mona2-right-central' in builds,
            "right-central artifact is not clearly named")
    require(len(re.findall(r"^\s+artifact-name:", builds, re.MULTILINE)) == 1,
            "normal firmware package must contain exactly one image")
    require('shield: mona2_l' not in builds,
            "left-peripheral image leaked into the one-file normal package")
    require('shield: settings_reset' in reset_build,
            "separate pairing reset build is missing")
    require('python3 scripts/verify-built-firmware.py' in workflow,
            "generated firmware contract is not enforced in CI")
    require('archive_name: pairing-reset-use-only-when-needed' in workflow,
            "pairing reset is not published as a separate CI artifact")
    require("if: github.event_name == 'workflow_dispatch' && inputs.pairing_reset" in workflow,
            "pairing reset must be manual-only")
    require('branches: [main]' in workflow,
            "feature branch pushes would duplicate pull-request builds")

    draw_workflow = read(".github/workflows/draw.yml")
    require(re.search(r"^\s+push:", draw_workflow, re.MULTILINE) is None,
            "keymap drawing must not auto-commit files on push")

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
