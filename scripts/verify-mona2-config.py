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
    left_conf = read("config/mona2_l.conf")
    right_conf = read("config/mona2_r.conf")
    west = read("config/west.yml")
    builds = read("build.yaml")
    workflow = read(".github/workflows/build.yml")

    names = re.findall(r'display-name\s*=\s*"([^"]+)";', keymap)
    require(
        names == ["Mouse Layer-Tap", "Base", "Mouse", "Scroll", "Gesture 1",
                  "Gesture 2", "symbol", "number", "move", "setting", "User 9"],
        f"unexpected behavior/layer display names: {names}",
    )
    require('bindings = <&mo>, <&mkp>;' in keymap, "Mouse Layer-Tap contract missing")
    require('&zip_temp_layer 1 10000' in keymap and '&zip_temp_layer 1 10000' in right,
            "AML timeout path missing")

    layer_ids = sorted(int(value) for value in re.findall(r"\blayer_(\d+)\s*\{", keymap))
    require(layer_ids == list(range(10)), f"keymap is not exactly ten layers: {layer_ids}")

    layers = {}
    for layer_id in range(10):
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
    gesture_2_access = layers[0] + layers[1]
    require(
        re.search(r"&(?:lt|mo)\s+4\b", gesture_2_access) is not None,
        "Gesture 2 must remain reachable from the Base or Mouse layer",
    )

    gesture_2_bindings = re.search(r"bindings\s*=\s*<(?P<body>.*?)>;", layers[4], re.DOTALL)
    require(gesture_2_bindings is not None, "Gesture 2 bindings are missing")
    gesture_2_behaviors = re.findall(r"&([A-Za-z0-9_]+)\b", gesture_2_bindings.group("body"))
    require(len(gesture_2_behaviors) == 42,
            f"Gesture 2 must retain all 42 editable key slots: {len(gesture_2_behaviors)}")
    for position in (7, 17, 19, 30):
        require(gesture_2_behaviors[position] not in {"trans", "none"},
                f"Gesture 2 editable action slot {position} is empty")

    require('&lt 5 LANGUAGE_1' in layers[0] and '&lt 6 SPACE' in layers[0]
            and '&lt 7 ENTER' in layers[0],
            "existing Symbol/Number/Move layer-taps were not shifted with their roles")
    require('&mo 8' in layers[5],
            "Symbol-to-setting momentary binding was not shifted with setting")

    for label, layer_id in (("gesture_processor", 3), ("gesture_2_processor", 4)):
        processor = re.search(
            rf"{label}:\s*{label}\s*\{{(?P<body>.*?)\n\s*\}};",
            dtsi,
            re.DOTALL,
        )
        require(processor is not None, f"{label} node missing")
        body = processor.group("body")
        for fragment in (
            f'layer = <{layer_id}>;', f'binding-layer = <{layer_id}>;',
            'up-position = <7>;', 'left-position = <17>;',
            'right-position = <19>;', 'down-position = <30>;',
            'threshold = <200>;', 'cooldown-ms = <150>;', 'reset-on-layer = <2>;',
        ):
            require(fragment in body, f"{label} contract missing: {fragment}")

    matrix = re.search(
        r"kscan0:\s*kscan\s*\{(?P<body>.*?)\n\s*\};",
        dtsi,
        re.DOTALL,
    )
    require(matrix is not None, "shared keyboard matrix node missing")
    require('wakeup-source;' in matrix.group("body"),
            "shared left/right matrix cannot wake from deep sleep")

    for fragment in (
        'cpi = <1200>;', 'pointer-acceleration;',
        'pointer-acceleration-base-gain-milli = <500>;',
        'pointer-acceleration-takeoff-speed = <32>;',
        'pointer-acceleration-full-speed = <160>;',
        'pointer-acceleration-max-gain-milli = <3000>;',
        'pointer-acceleration-reference-interval-ms = <15>;',
        'pointer-acceleration-idle-reset-ms = <60>;',
        'pointer-acceleration-scroll-layer = <2>;',
        'pointer-acceleration-gesture-layer = <3>;',
        'pointer-acceleration-gesture-layer-2 = <4>;',
        'force-awake;',
        'layers = <2>;', '<&zip_scroll_scaler 1 10>,',
        '<&zip_scroll_scaler 1 6>;', 'process-next;',
    ):
        require(fragment in right, f"pointer contract missing: {fragment}")

    sensor_block = re.search(
        r"trackball_central:\s*trackball_central@0\s*\{(?P<body>.*?)\n\s*\};",
        right,
        re.DOTALL,
    )
    require(sensor_block is not None, "trackball sensor node missing")
    sensor_body = sensor_block.group("body")
    require('pointer-acceleration-precision-mode;' not in sensor_body,
            "ZEN pointer contract forbids moNa2-only precision mode")
    require(re.search(r"^\s*invert-x;", sensor_body, re.MULTILINE) is None,
            "physical-unit contract forbids active sensor X inversion")
    require(re.search(r"^\s*invert-y;", sensor_body, re.MULTILINE) is None,
            "physical-unit contract forbids active sensor Y inversion")
    base_listener = re.search(
        r"&trackball_central_listener\s*\{(?P<body>.*?)\n\s*scroller\s*\{",
        right,
        re.DOTALL,
    )
    require(base_listener is not None, "right trackball base listener missing")
    normalized_base_listener = re.sub(r"\s+", "", base_listener.group("body"))
    require(
        "input-processors=<&zip_xy_transformINPUT_TRANSFORM_X_INVERT>,"
        "<&gesture_2_processor>,<&gesture_processor>,"
        "<&zip_temp_layer110000>;" in normalized_base_listener,
        "base Pointer/Gesture/AML processor order or direction changed",
    )

    scroller = re.search(
        r"scroller\s*\{(?P<body>.*?)\n\s*\};",
        right,
        re.DOTALL,
    )
    require(scroller is not None, "right trackball Scroll listener missing")
    scroller_without_comments = re.sub(r"//[^\n]*", "", scroller.group("body"))
    normalized_scroller = re.sub(r"\s+", "", scroller_without_comments)
    require(
        "layers=<2>;input-processors="
        "<&zip_xy_transformINPUT_TRANSFORM_X_INVERT>,"
        "<&zip_xy_to_scroll_mapper>,"
        "<&zip_scroll_transformINPUT_TRANSFORM_Y_INVERT>,"
        "<&zip_scroll_scaler110>,"
        "<&zip_scroll_scaler16>;process-next;" in normalized_scroller,
        "Scroll processor order or requested two-axis reversal changed",
    )

    require('CONFIG_PMW3610_REPORT_INTERVAL_MIN=15' in right_conf,
            "15 ms driver aggregation is not enabled")
    require('CONFIG_PMW3610_RUN_DOWNSHIFT_TIME_MS=3264' in right_conf,
            "ZEN run-to-rest downshift time is not enabled")
    require('CONFIG_PMW3610_POINTER_ACCELERATION=y' in right_conf,
            "pointer acceleration Kconfig is not enabled")
    require('CONFIG_ZMK_POINTING_SMOOTH_SCROLLING=y' in right_conf,
            "ZEN smooth scrolling behavior is not enabled")
    require('CONFIG_INPUT_THREAD_STACK_SIZE=4096' in right_conf,
            "input thread stack is too small for the custom pointer pipeline")
    for name, conf in (("left", left_conf), ("right", right_conf)):
        require('CONFIG_ZMK_SLEEP=y' in conf, f"{name} deep sleep is not enabled")
        require('CONFIG_ZMK_IDLE_TIMEOUT=300000' in conf,
                f"{name} idle timeout is not 5 minutes")
        require('CONFIG_ZMK_IDLE_SLEEP_TIMEOUT=1800000' in conf,
                f"{name} deep-sleep timeout is not 30 minutes")
        require('CONFIG_ZMK_PM_SOFT_OFF=y' not in conf,
                f"{name} unexpectedly enables PM soft-off")
    require('CONFIG_RGBLED_WIDGET_SHOW_LAYER_COLORS=y' in right_conf,
            "stock layer LED behavior was removed")
    expected_layer_colors = [0, 7, 2, 3, 5, 4, 2, 6, 1, 3]
    for layer_id, color in enumerate(expected_layer_colors):
        require(f'CONFIG_RGBLED_WIDGET_LAYER_{layer_id}_COLOR={color}' in right_conf,
                f"layer {layer_id} LED color is not palette value {color}")
    require('CONFIG_ZMK_STUDIO=y' in right_conf, "standard ZMK Studio was removed")
    matrix_entries = []
    for block in re.findall(r"(?ms)^  - board:.*?(?=^  - board:|\Z)", builds):
        matrix_entries.append(dict(re.findall(r"^\s+(?:-\s+)?(board|shield|snippet|artifact-name):\s*(.+?)\s*$",
                                              block, re.MULTILINE)))
    require(
        matrix_entries == [
            {
                "board": "seeeduino_xiao_ble",
                "shield": "mona2_l rgbled_adapter",
                "artifact-name": "mona2-left-peripheral",
            },
            {
                "board": "seeeduino_xiao_ble",
                "shield": "mona2_r rgbled_adapter",
                "snippet": "studio-rpc-usb-uart",
                "artifact-name": "mona2-right-central",
            },
            {
                "board": "seeeduino_xiao_ble",
                "shield": "settings_reset",
                "artifact-name": "mona2-pairing-reset-use-only-when-needed",
            },
        ],
        f"build matrix must contain exactly left, right, and reset images: {matrix_entries}",
    )
    require('python3 scripts/verify-built-firmware.py' in workflow,
            "generated firmware contract is not enforced in CI")
    require('build-pairing-reset:' not in workflow,
            "obsolete duplicate pairing-reset job is still present")
    require('branches: [main]' in workflow,
            "feature branch pushes would duplicate pull-request builds")

    draw_workflow = read(".github/workflows/draw.yml")
    require(re.search(r"^\s+push:", draw_workflow, re.MULTILINE) is None,
            "keymap drawing must not auto-commit files on push")

    revisions = re.findall(r"revision:\s*([0-9a-f]{40})", west)
    require(len(revisions) == 4, f"expected four pinned dependencies, found {len(revisions)}")
    require('revision: 1c6499b3622f849fd556e585870dfed4696d2edd' in west,
            "dual-Gesture PMW3610 driver commit is not pinned")
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
