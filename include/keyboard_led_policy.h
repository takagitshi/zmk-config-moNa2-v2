/* LED-only policy. No charging or power-management controls. */
#pragma once
#include <stdbool.h>
#include <stdint.h>
#define KEYBOARD_LED_POLICY_VERSION 2
#define KL_BATTERY_CRITICAL 10
#define KL_BATTERY_HIGH 30
#define KL_USB_BLINK_THRESHOLD 80
#define KL_BOOT_MS 2000 /* existing moNa2 battery indication duration */
#define KL_BT_MS 1500
#define KL_DIAG_MS 2000
#define KL_USB_HALF_PERIOD_MS 500
#define KL_SETTING_LAYER 8
/* palette: off, red, green, yellow, blue, magenta, cyan, white */
struct keyboard_led_state {
    bool usb, battery_valid, active, sleeping, layer_active;
    uint8_t battery, bt_color, layer_color, diag_color;
    int64_t bt_until, boot_until, diag_until;
};
static inline uint8_t keyboard_led_battery_color(bool valid, uint8_t level) {
    return !valid ? 6 : level < KL_BATTERY_CRITICAL ? 1 : level < KL_BATTERY_HIGH ? 3 : 2;
}
static inline bool keyboard_led_color_allowed(uint8_t layer, uint8_t color) {
    return layer < 32 && color < 8 && (color != 1 || layer == KL_SETTING_LAYER);
}
/* Notifications temporarily cover a layer; their expiry always returns to the
 * current highest layer. Base OFF leaves the USB/battery baseline visible. */
static inline uint8_t keyboard_led_color(const struct keyboard_led_state *s, int64_t now) {
    if (s->sleeping) return 0;
    if (now < s->diag_until) return s->diag_color;
    /* IDLE may briefly report a connection event without waking activity. */
    if (now < s->bt_until) return s->bt_color;
    if (!s->active && !s->usb) return 0;
    if (s->active && now < s->boot_until) return keyboard_led_battery_color(s->battery_valid, s->battery);
    if (s->active && s->layer_active) return s->layer_color;
    if (!s->usb) return 0;
    if (s->battery_valid && s->battery >= KL_USB_BLINK_THRESHOLD &&
        (now / KL_USB_HALF_PERIOD_MS) % 2) return 0;
    return keyboard_led_battery_color(s->battery_valid, s->battery);
}
/* Schedule only the visible notification/blink. Persistent layers need no
 * polling; layer/activity/USB events synchronously update their output. */
static inline int64_t keyboard_led_next(const struct keyboard_led_state *s, int64_t now) {
    if (s->sleeping) return 0;
    if (s->diag_until > now) return s->diag_until - now;
    if (s->bt_until > now) return s->bt_until - now;
    if (s->active && s->boot_until > now) return s->boot_until - now;
    if (s->active && s->layer_active) return 0;
    if (s->usb && s->battery_valid && s->battery >= KL_USB_BLINK_THRESHOLD)
        return KL_USB_HALF_PERIOD_MS - now % KL_USB_HALF_PERIOD_MS;
    return 0;
}
