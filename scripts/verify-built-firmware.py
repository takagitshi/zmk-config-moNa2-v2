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

    for prop in ("pointer-acceleration;", "cpi = < 0x4b0 >;"):
        require(prop in sensor, f"generated pointer contract missing: {prop}")
    for prop in ("invert-x;", "invert-y;"):
        require(prop not in sensor,
                f"generated physical-unit contract forbids sensor inversion: {prop}")
    require("<&zip_xy_transform0x4>" in normalized_listener,
            "generated base Y transform changed")
    require("<&zip_temp_layer0x10x2710>" in normalized_listener,
            "generated AML layer/timeout changed")

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
    require('CONFIG_ZMK_IDLE_TIMEOUT=300000' in right_config,
            "right-central idle timeout changed")
    require(not enabled(right_config, "CONFIG_ZMK_SETTINGS_RESET_ON_START"),
            "right-central normal firmware would erase settings on boot")

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
