/* LED-only policy. No charging or power-management controls. */
#pragma once
#include <stdbool.h>
#include <stdint.h>
#define KEYBOARD_LED_POLICY_VERSION 1
#define KL_BATTERY_CRITICAL 10
#define KL_BATTERY_HIGH 30
#define KL_USB_BLINK_THRESHOLD 80
#define KL_BOOT_MS 2000 /* existing moNa2 battery indication duration */
#define KL_BT_MS 1500
#define KL_TRANSIENT_MS 1200
#define KL_MOUSE_BATTERY_MS 350
#define KL_MOUSE_USB_MS 800
#define KL_USB_HALF_PERIOD_MS 500
#define KL_SETTING_LAYER 8
/* palette: off, red, green, yellow, blue, magenta, cyan, white */
struct keyboard_led_state {
    bool usb, battery_valid, active, sleeping;
    uint8_t battery, bt_color, layer_color;
    int64_t bt_until, layer_until, boot_until;
};
static inline uint8_t keyboard_led_battery_color(bool valid, uint8_t level) {
    return !valid ? 6 : level < KL_BATTERY_CRITICAL ? 1 : level < KL_BATTERY_HIGH ? 3 : 2;
}
static inline bool keyboard_led_color_allowed(uint8_t layer, uint8_t color) {
    return layer < 32 && color < 8 && (color != 1 || layer == KL_SETTING_LAYER);
}
static inline uint8_t keyboard_led_color(const struct keyboard_led_state *s, int64_t now) {
    if (s->sleeping) return 0;
    /* IDLE may briefly report a connection event without waking activity. */
    if (now < s->bt_until) return s->bt_color;
    if (!s->active && !s->usb) return 0;
    if (s->active && now < s->layer_until) return s->layer_color;
    if (s->active && now < s->boot_until) return keyboard_led_battery_color(s->battery_valid, s->battery);
    if (!s->usb) return 0;
    if (s->battery_valid && s->battery >= KL_USB_BLINK_THRESHOLD &&
        (now / KL_USB_HALF_PERIOD_MS) % 2) return 0;
    return keyboard_led_battery_color(s->battery_valid, s->battery);
}
/* No timer on battery after a transient, nor during sleep. */
static inline int64_t keyboard_led_next(const struct keyboard_led_state *s, int64_t now) {
    if (s->sleeping) return 0;
    int64_t next = s->bt_until > now ? s->bt_until : 0;
    if (s->active) {
        const int64_t times[] = {s->layer_until, s->boot_until};
        for (unsigned i=0; i<2; i++)
            if (times[i] > now && (!next || times[i] < next)) next = times[i];
    }
    if (s->usb && s->battery_valid && s->battery >= KL_USB_BLINK_THRESHOLD) {
        int64_t tick = (now / KL_USB_HALF_PERIOD_MS + 1) * KL_USB_HALF_PERIOD_MS;
        if (!next || tick < next) next = tick;
    }
    return next ? next - now : 0;
}
