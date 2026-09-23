# zmk-config-moNa2

<img src="keymap-drawer/mona2_01.svg">

## Takashi custom firmware

This branch starts from the original `bbcf723` main configuration and keeps the
moNa2 split matrix, left encoder, battery reporting, standard ZMK Studio build,
and `zmk-rgbled-widget` layer/battery LED behavior.

The active layout is the Keymap Editor-compatible `config/mona2.keymap`.
`boards/shields/mona2/mona2.keymap` is kept in sync as a fallback. The nine
layers are Base, Mouse/AML, Scroll, Gesture, symbol, number, move, setting, and
User 8. Keys without a safe physical equivalent remain transparent so they can
be adjusted later in Keymap Editor.

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

The PMW3610 dependency is an owned, commit-pinned fork that retains final motion
samples and retries unsent non-blocking reports. ZMK, the RGB widget, and the
keybind input processor are also pinned to the revisions used for validation.

The stock DYA branches are not used. Standard ZMK Studio remains enabled because
it is independent of DYA Studio and was already present on the original main.

# COROPITを使用するへ

COROPITを使用する方は以下のようにコードを編集してください。

mona2_r.overlay

修正前
```
  trackball_central: trackball_central@0 {
        status = "okay";
        compatible = "pixart,pmw3610";  //トラボセンサ用のドライバとバインド
        reg = <0>;
        spi-max-frequency = <2000000>;
        irq-gpios = <&gpio0 2 (GPIO_ACTIVE_LOW | GPIO_PULL_UP)>; //P0.02を指定(MOTION)
        cpi = <600>;
        //swap-xy;
        //invert-x; //COROPIT版ではコメントアウトを外す
        //invert-y; //COROPIT版ではコメントアウトを外す
        evt-type = <INPUT_EV_REL>;
        x-input-code = <INPUT_REL_X>;
        y-input-code = <INPUT_REL_Y>;
    };
};

```
**修正後**
```
  trackball_central: trackball_central@0 {
        status = "okay";
        compatible = "pixart,pmw3610";  //トラボセンサ用のドライバとバインド
        reg = <0>;
        spi-max-frequency = <2000000>;
        irq-gpios = <&gpio0 2 (GPIO_ACTIVE_LOW | GPIO_PULL_UP)>; //P0.02を指定(MOTION)
        cpi = <600>;
        //swap-xy;
        invert-x; //COROPIT版ではコメントアウトを外す
        invert-y; //COROPIT版ではコメントアウトを外す
        evt-type = <INPUT_EV_REL>;
        x-input-code = <INPUT_REL_X>;
        y-input-code = <INPUT_REL_Y>;
    };
};

```
