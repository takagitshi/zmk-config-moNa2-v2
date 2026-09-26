# zmk-config-moNa2

<img src="keymap-drawer/mona2_01.svg">

## Takashi custom firmware

This branch starts from the original `bbcf723` main configuration and keeps the
moNa2 split matrix, left encoder, battery reporting, standard ZMK Studio build,
and `zmk-rgbled-widget` layer/battery LED behavior.

The only editable layout source is the Keymap Editor-compatible
`config/mona2.keymap`. The shield's bundled keymap is only a fallback and is
not compared with the editable file, so a normal Keymap Editor commit cannot
be rejected merely because the fallback did not change. The ten layers are
Base, Mouse/AML, Scroll, Gesture 1, Gesture 2, symbol, number, move, setting,
and User 9.
Keys without a safe physical equivalent remain transparent so they can be
adjusted later in Keymap Editor.

The repository default `main` and Keymap Editor both use this ten-layer layout.
It was merged before the physical checks so Keymap Editor could edit all ten
layers. The four-direction, reconnect, sleep/resume, Scroll, Gesture, LED, and
AML checks therefore remain required on the physical keyboard.

Mouse/pointing behavior:

- Auto Mouse Layer selects Layer 1 after pointer motion, waits for 300 ms of
  keyboard idle, and times out after 10 seconds. Mouse clicks refresh the timer.
- AML exclusions are derived from every non-transparent/non-none Mouse-layer
  binding. The current seven positions are 17/18/19/20/21/34/35, including the
  right Command key at the same physical position as Base `-`.
- `Mouse Layer-Tap` uses `&mouse_lt <layer> <MB1..MB5>` so both parameters remain
  editable in Keymap Editor.
- Layer 2 converts the trackball to scroll. Both vertical and horizontal
  outputs are reversed from the physically accepted `17b4108` candidate, while
  using cascaded `1/10` and `1/6` scalers for an effective `1/60` scale. Each
  scaler stays within ZMK's recommended parameter limit and retains remainders
  for low-speed motion.
- Layer 3 (Gesture 1) recognizes four gestures through the editable
  I/J/L/comma bindings. Layer 4 (Gesture 2) uses the same physical slots and
  reads their normal keymap bindings, so Keymap Editor can change each action.
  Its initial actions are Command+T (up), Control+Shift+Tab (left), Control+Tab
  (right), and Command+Shift+N (down). Base comma taps comma and holds Gesture 2;
  the Mouse-layer left Command key is a normal Command key.
- Pointer acceleration is implemented at the PMW3610 15 ms X/Y aggregation
  boundary. It uses ZEN's 1200 CPI curve: 0.5x base gain, acceleration from
  normalized speed 32 through 160, and a 3.0x maximum gain. Scroll and Gesture
  1 / Gesture 2 receive unaccelerated deltas through separate layer bypasses.
  `force-awake` is enabled and the RUN-to-REST1 downshift is 3264 ms.
- This physical unit keeps the PMW3610 sensor `invert-x` and `invert-y`
  properties disabled. The listener applies one X-axis transform, matching the
  effective orientation used before the customization while leaving the
  layer-specific Scroll chain independent. The generated devicetree contract
  verifies the pointer transform, two-axis Scroll reversal, and absence of
  sensor inversion flags.
- Both halves enter idle after 5 minutes and deep sleep after 30 minutes,
  matching LisM. PM soft-off remains disabled. ZEN's smooth-scrolling mode and
  4096-byte input thread stack are retained. ZEN-only non-LiPo battery
  thresholds and GPIO status LEDs are intentionally not copied to moNa2.
- The shared left/right key matrix is a deep-sleep wake source, so pressing any
  matrix key wakes its own half. The first press may be consumed by boot and BLE
  reconnection instead of being sent as a character.

The PMW3610 dependency is an owned, commit-pinned fork that retains final motion
samples and retries unsent non-blocking reports. ZMK, the RGB widget, and the
keybind input processor are also pinned to the revisions used for validation.

The stock DYA branches are not used. Standard ZMK Studio remains enabled because
it is independent of DYA Studio and was already present on the original main.

`scripts/verify-mona2-config.py` checks the editable source contracts without
pinning `Mouse Layer-Tap` to one physical key. It also compares AML exclusions
with the actual non-transparent Mouse-layer positions. After an internal right
and left build, `scripts/verify-built-firmware.py` checks the generated
devicetree and Kconfig for the accepted physical-unit axes, exactly ten
layers, unchanged Bluetooth identity, and the intended split roles.

Each Actions run publishes one downloadable `firmware` artifact containing
exactly three files: `mona2-left-peripheral.uf2`,
`mona2-right-central.uf2`, and
`mona2-pairing-reset-use-only-when-needed.uf2`. Flash the left image only to
the left peripheral and the right image only to the right central; never use
one image on both halves. The reset image is included for recovery but must not
be used during an ordinary update because it erases saved bonds. Automatic
keymap-drawer commits are disabled. The stock Bluetooth configuration and
device name (`mona2`) are otherwise unchanged.

The right-central layer indicator uses only the pinned widget palette:
0=off, 1=white, 2=green, 3=yellow, 4=magenta, 5=blue, 6=green,
7=cyan, 8=red, and 9=yellow. Trackball activity temporarily activates Mouse layer 1,
so the LED stays white for the 10-second AML timeout. This is a layer
indicator, not an error condition.

For the difference between an ordinary side-specific update and a full bond reset,
see [`docs/PAIRING_RECOVERY.md`](docs/PAIRING_RECOVERY.md).
