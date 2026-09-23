# zmk-config-moNa2

<img src="keymap-drawer/mona2_01.svg">

## Takashi custom firmware

This branch starts from the original `bbcf723` main configuration and keeps the
moNa2 split matrix, left encoder, battery reporting, standard ZMK Studio build,
and `zmk-rgbled-widget` layer/battery LED behavior.

The only editable layout source is the Keymap Editor-compatible
`config/mona2.keymap`. The shield's bundled keymap is only a fallback and is
not compared with the editable file, so a normal Keymap Editor commit cannot
be rejected merely because the fallback did not change. The nine layers are
Base, Mouse/AML, Scroll, Gesture, symbol, number, move, setting, and User 8.
Keys without a safe physical equivalent remain transparent so they can be
adjusted later in Keymap Editor.

While this hardware candidate remains a Draft PR, select branch
`codex/zen-lism-customization` in Keymap Editor to see these nine layers. The
repository default `main` intentionally stays at the rollback-safe seven-layer
original until the physical pointer, reconnect, sleep/resume, Scroll, and
Gesture checks pass. After acceptance, merging this branch makes the same
nine-layer file the normal Keymap Editor default.

Mouse/pointing behavior:

- Auto Mouse Layer selects Layer 1 after pointer motion, waits for 300 ms of
  keyboard idle, and times out after 10 seconds. Mouse clicks refresh the timer.
- `Mouse Layer-Tap` uses `&mouse_lt <layer> <MB1..MB5>` so both parameters remain
  editable in Keymap Editor.
- Layer 2 converts the trackball to scroll while preserving the original moNa2
  axes and physical scroll scale (`1200 CPI / 10`, equal to the original
  `600 CPI / 5`).
- Layer 3 recognizes four gestures through the editable I/J/L/comma bindings.
- Pointer acceleration is implemented at the PMW3610 15 ms X/Y aggregation
  boundary. Scroll and Gesture receive raw deltas. `force-awake` remains off.
- This physical unit must not enable the PMW3610 sensor `invert-x` or
  `invert-y` properties. Enabling both in the rejected `d5615af` candidate
  reversed both axes on hardware. The original listener-level direction
  transform is retained and the absence of both sensor flags is verified from
  the generated devicetree.
- ZEN's smooth-scrolling mode, 300-second idle timeout, and 4096-byte input
  thread stack are retained. ZEN-only hardware settings such as `force-awake`,
  non-LiPo battery thresholds, and GPIO status LEDs are intentionally not
  copied to moNa2.

The PMW3610 dependency is an owned, commit-pinned fork that retains final motion
samples and retries unsent non-blocking reports. ZMK, the RGB widget, and the
keybind input processor are also pinned to the revisions used for validation.

The stock DYA branches are not used. Standard ZMK Studio remains enabled because
it is independent of DYA Studio and was already present on the original main.

`scripts/verify-mona2-config.py` checks the editable source contracts without
pinning `Mouse Layer-Tap` to one physical key. It also compares AML exclusions
with the actual non-transparent Mouse-layer positions. After an internal right
and left build, `scripts/verify-built-firmware.py` checks the generated
devicetree and Kconfig for the accepted physical-unit axes, exactly nine
layers, unchanged Bluetooth identity, and the intended split roles.

Each normal Actions run publishes one `firmware` artifact containing exactly
one file: `mona2-right-central.uf2`. The left peripheral is still built
inside CI as a compatibility check, but is not published because ordinary
keymap, pointer, and central behavior updates only require the central half.
Pairing reset is available only through an explicit manual-dispatch option and
can no longer appear during a normal push. Automatic keymap-drawer commits are
also disabled. The stock Bluetooth configuration and device name (`mona2`) are
otherwise unchanged.

For the difference between an ordinary two-file update and a full bond reset,
see [`docs/PAIRING_RECOVERY.md`](docs/PAIRING_RECOVERY.md).
