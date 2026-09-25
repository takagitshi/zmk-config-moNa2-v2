#!/usr/bin/env python3
"""Verify contracts that only exist after ZMK has generated build files."""

from pathlib import Path
import re
import sys


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def node_body(dts: str, label: str) -> str:
    match = re.search(rf"\b{re.escape(label)}:\s*[^{{]+\{{(?P<body>.*?)\n\s*\}};", dts,
                      re.DOTALL)
    require(match is not None, f"generated node missing: {label}")
    return match.group("body")


def enabled(config: str, symbol: str) -> bool:
    return re.search(rf"^{re.escape(symbol)}=y$", config, re.MULTILINE) is not None


def main() -> int:
    if len(sys.argv) != 5:
        print("usage: verify-built-firmware.py RIGHT_DTS RIGHT_CONFIG LEFT_DTS LEFT_CONFIG",
              file=sys.stderr)
        return 2

    right_dts, right_config, left_dts, left_config = map(read, sys.argv[1:])
    sensor = node_body(right_dts, "trackball_central")
    listener = node_body(right_dts, "trackball_central_listener")
    normalized_listener = re.sub(r"\s+", "", listener)

    for name, dts in (("right-central", right_dts), ("left-peripheral", left_dts)):
        matrix = node_body(dts, "kscan0")
        require("wakeup-source;" in matrix,
                f"{name} matrix cannot wake from deep sleep")

    for prop in (
        "pointer-acceleration;",
        "force-awake;",
        "cpi = < 0x4b0 >;",
        "pointer-acceleration-base-gain-milli = < 0x1f4 >;",
        "pointer-acceleration-takeoff-speed = < 0x20 >;",
        "pointer-acceleration-full-speed = < 0xa0 >;",
        "pointer-acceleration-max-gain-milli = < 0xbb8 >;",
        "pointer-acceleration-reference-interval-ms = < 0xf >;",
        "pointer-acceleration-idle-reset-ms = < 0x3c >;",
        "pointer-acceleration-scroll-layer = < 0x2 >;",
        "pointer-acceleration-gesture-layer = < 0x3 >;",
    ):
        require(prop in sensor, f"generated pointer contract missing: {prop}")
    require("pointer-acceleration-precision-mode;" not in sensor,
            "generated sensor unexpectedly retains precision mode")
    for prop in ("invert-x;", "invert-y;"):
        require(prop not in sensor,
                f"generated physical-unit contract forbids sensor inversion: {prop}")
    require(
        "input-processors=<&zip_xy_transform0x2>,<&gesture_processor>,"
        "<&zip_temp_layer0x10x2710>;" in normalized_listener,
        "generated Pointer/Gesture/AML processor order changed",
    )
    require(
        "input-processors=<&zip_xy_transform0x2>,<&zip_xy_to_scroll_mapper>,"
        "<&zip_scroll_transform0x4>,<&zip_scroll_scaler0x10xa>,"
        "<&zip_scroll_scaler0x10x6>;" in normalized_listener,
        "generated Scroll processor order changed",
    )
    require("process-next;" in normalized_listener,
            "generated Scroll chain no longer continues to HID")

    layers = sorted({int(value) for value in re.findall(r"\blayer_(\d+)\s*\{", right_dts)})
    require(layers == list(range(9)), f"generated keymap is not exactly nine layers: {layers}")

    for symbol in (
        "CONFIG_ZMK_BLE",
        "CONFIG_ZMK_SPLIT",
        "CONFIG_ZMK_SPLIT_ROLE_CENTRAL",
        "CONFIG_ZMK_STUDIO",
        "CONFIG_ZMK_STUDIO_TRANSPORT_BLE",
        "CONFIG_PMW3610_POINTER_ACCELERATION",
        "CONFIG_ZMK_POINTING_SMOOTH_SCROLLING",
    ):
        require(enabled(right_config, symbol), f"right-central build missing {symbol}")
    require('CONFIG_BT_DEVICE_NAME="mona2"' in right_config,
            "right-central Bluetooth name changed")
    require('CONFIG_INPUT_THREAD_STACK_SIZE=4096' in right_config,
            "right-central input thread stack changed")
    require('CONFIG_PMW3610_REPORT_INTERVAL_MIN=15' in right_config,
            "right-central PMW3610 aggregation interval changed")
    require('CONFIG_PMW3610_RUN_DOWNSHIFT_TIME_MS=3264' in right_config,
            "right-central PMW3610 run-to-rest downshift changed")
    require('CONFIG_RGBLED_WIDGET_LAYER_1_COLOR=7' in right_config,
            "right-central Mouse / AML layer is not white")
    require('CONFIG_RGBLED_WIDGET_LAYER_7_COLOR=1' in right_config,
            "right-central setting layer is not red")
    require(not enabled(right_config, "CONFIG_ZMK_SETTINGS_RESET_ON_START"),
            "right-central normal firmware would erase settings on boot")

    for name, config in (("right-central", right_config),
                         ("left-peripheral", left_config)):
        require(enabled(config, "CONFIG_ZMK_SLEEP"), f"{name} deep sleep is disabled")
        require('CONFIG_ZMK_IDLE_TIMEOUT=300000' in config,
                f"{name} idle timeout is not 5 minutes")
        require('CONFIG_ZMK_IDLE_SLEEP_TIMEOUT=1800000' in config,
                f"{name} deep-sleep timeout is not 30 minutes")
        require(not enabled(config, "CONFIG_ZMK_PM_SOFT_OFF"),
                f"{name} unexpectedly enables PM soft-off")

    for symbol in ("CONFIG_ZMK_BLE", "CONFIG_ZMK_SPLIT"):
        require(enabled(left_config, symbol), f"left-peripheral build missing {symbol}")
    require(not enabled(left_config, "CONFIG_ZMK_SPLIT_ROLE_CENTRAL"),
            "left build unexpectedly became the split central")
    require(not enabled(left_config, "CONFIG_ZMK_SETTINGS_RESET_ON_START"),
            "left-peripheral normal firmware would erase settings on boot")
    require("trackball_central@0" not in left_dts,
            "left-peripheral build unexpectedly contains the right trackball sensor")
    left_listener = node_body(left_dts, "trackball_central_listener")
    require('status = "disabled";' in left_listener,
            "left-peripheral trackball listener is unexpectedly enabled")

    print("verify-built-firmware: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"verify-built-firmware: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
