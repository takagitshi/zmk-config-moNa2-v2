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
- Current moNa2 kits include COROPIT, and the official configuration requires
  its X/Y sensor inversion. The inversion is applied in the PMW3610 node,
  before pointer, Scroll, and Gesture processing, and is verified from the
  generated devicetree during builds. Final direction remains a physical gate.

The PMW3610 dependency is an owned, commit-pinned fork that retains final motion
samples and retries unsent non-blocking reports. ZMK, the RGB widget, and the
keybind input processor are also pinned to the revisions used for validation.

The stock DYA branches are not used. Standard ZMK Studio remains enabled because
it is independent of DYA Studio and was already present on the original main.

`scripts/verify-mona2-config.py` checks the editable source contracts. After a
right and left build, `scripts/verify-built-firmware.py` checks the generated
devicetree and Kconfig for the COROPIT axes, exactly nine layers, unchanged
Bluetooth identity, and the intended right-central/left-peripheral split roles.

The normal `firmware` package contains only the clearly named right-central and
left-peripheral images. The same CI run publishes pairing-reset firmware as a
separate `pairing-reset-use-only-when-needed` artifact so it cannot be mistaken
for a normal half update. The stock Bluetooth configuration and device name
(`mona2`) are otherwise unchanged.

For the difference between an ordinary two-file update and a full bond reset,
see [`docs/PAIRING_RECOVERY.md`](docs/PAIRING_RECOVERY.md).
