/* One owner for XIAO RGB output. Only observes existing battery, USB and BLE
 * state; never changes charging, USB transport, bonds, activity or sleep. */
#include <zephyr/kernel.h>
#include <zephyr/init.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/sensor.h>
#include <zmk/workqueue.h>
#include <zephyr/bluetooth/conn.h>
#include <hal/nrf_power.h>
#include <zmk/activity.h>
#include <zmk/battery.h>
#include <zmk/ble.h>
#include <zmk/event_manager.h>
#include <zmk/events/activity_state_changed.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/events/usb_conn_state_changed.h>
#include <zmk/events/ble_active_profile_changed.h>
#include <zmk/events/split_peripheral_status_changed.h>
#include <zmk/events/layer_state_changed.h>
#include <zmk/keymap.h>
#include <zmk/split/bluetooth/peripheral.h>
#include "keyboard_led_policy.h"

static const struct gpio_dt_spec rgb[] = {
    GPIO_DT_SPEC_GET(DT_NODELABEL(led0), gpios),
    GPIO_DT_SPEC_GET(DT_NODELABEL(led2), gpios), /* green, P0.6 */
    GPIO_DT_SPEC_GET(DT_NODELABEL(led1), gpios), /* blue, P0.30 */
};
static uint8_t colors[] = {
    CONFIG_RGBLED_WIDGET_LAYER_0_COLOR, CONFIG_RGBLED_WIDGET_LAYER_1_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_2_COLOR, CONFIG_RGBLED_WIDGET_LAYER_3_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_4_COLOR, CONFIG_RGBLED_WIDGET_LAYER_5_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_6_COLOR, CONFIG_RGBLED_WIDGET_LAYER_7_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_8_COLOR, CONFIG_RGBLED_WIDGET_LAYER_9_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_10_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_11_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_12_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_13_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_14_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_15_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_16_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_17_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_18_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_19_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_20_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_21_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_22_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_23_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_24_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_25_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_26_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_27_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_28_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_29_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_30_COLOR,
    CONFIG_RGBLED_WIDGET_LAYER_31_COLOR,
};
static struct keyboard_led_state state;
static bool ready;
static uint8_t current_layer;
K_MUTEX_DEFINE(keyboard_led_lock);
static void render(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(keyboard_led_work, render);
static void sample_idle_battery(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(keyboard_led_sample_work, sample_idle_battery);
static int64_t idle_sample_at;


static bool usb_powered(void) {
    /* VBUS hardware state works on both halves, including power-only chargers.
     * Do not use the charging STAT pin or the selected HID endpoint. */
    return nrf_power_usbregstatus_vbusdet_get(NRF_POWER);
}
static void output(uint8_t color) {
    for (unsigned i=0; i<3; i++) gpio_pin_set_dt(&rgb[i], !!(color & (1U << i)));
}
static void render_locked(void) {
    if (!ready) return;
    const int64_t now = k_uptime_get();
    state.usb = usb_powered();
#if IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    /* Read the authoritative keymap on every event/render, including init and
     * IDLE wake. A repeated activation cannot start or expire a layer timer. */
    current_layer = zmk_keymap_highest_layer_active();
    state.layer_color = current_layer < ARRAY_SIZE(colors) ? colors[current_layer] : 0;
    state.layer_active = current_layer != 0 || state.layer_color != 0;
#endif
    /* The upstream sampler stops at IDLE. Keep USB-only indication fresh on
     * its existing low-priority queue, with no extra battery/sleep polling. */
    if (state.usb && !state.active && !state.sleeping) {
        int64_t wait = idle_sample_at > now ? idle_sample_at - now : 0;
        k_work_reschedule_for_queue(zmk_workqueue_lowprio_work_q(),
                                   &keyboard_led_sample_work, K_MSEC(wait));
    } else {
        idle_sample_at = 0;
        k_work_cancel_delayable(&keyboard_led_sample_work);
    }
    output(keyboard_led_color(&state, now));
    const int64_t delay = keyboard_led_next(&state, now);
    if (delay) k_work_reschedule(&keyboard_led_work, K_MSEC(delay));
    else k_work_cancel_delayable(&keyboard_led_work);
}
static void render(struct k_work *work) {
    k_mutex_lock(&keyboard_led_lock, K_FOREVER);
    render_locked();
    k_mutex_unlock(&keyboard_led_lock);
}

static void sample_idle_battery(struct k_work *work) {
    k_mutex_lock(&keyboard_led_lock, K_FOREVER);
    bool allowed = ready && usb_powered() && !state.active && !state.sleeping;
    k_mutex_unlock(&keyboard_led_lock);
    if (!allowed) return;
    /* Same chosen device, fetch mode and conversion as pinned ZMK battery.c.
     * Same lowprio work queue serializes samples with upstream on wake. */
    const struct device *battery = DEVICE_DT_GET(DT_CHOSEN(zmk_battery));
    struct sensor_value reading;
    int level = -1;
    if (device_is_ready(battery)) {
#if IS_ENABLED(CONFIG_ZMK_BATTERY_REPORTING_FETCH_MODE_STATE_OF_CHARGE)
        if (!sensor_sample_fetch_chan(battery, SENSOR_CHAN_GAUGE_STATE_OF_CHARGE) &&
            !sensor_channel_get(battery, SENSOR_CHAN_GAUGE_STATE_OF_CHARGE, &reading))
            level = reading.val1;
#elif IS_ENABLED(CONFIG_ZMK_BATTERY_REPORTING_FETCH_MODE_LITHIUM_VOLTAGE)
        if (!sensor_sample_fetch_chan(battery, SENSOR_CHAN_VOLTAGE) &&
            !sensor_channel_get(battery, SENSOR_CHAN_VOLTAGE, &reading)) {
            int mv = reading.val1 * 1000 + reading.val2 / 1000;
            level = mv >= 4200 ? 100 : mv <= 3450 ? 0 : mv * 2 / 15 - 459;
        }
#endif
    }
    k_mutex_lock(&keyboard_led_lock, K_FOREVER);
    if (usb_powered() && !state.active && !state.sleeping) {
        state.battery_valid = level >= 0 && level <= 100;
        if (state.battery_valid) state.battery = level;
        idle_sample_at = k_uptime_get() + 60000;
        render_locked();
    }
    k_mutex_unlock(&keyboard_led_lock);
}

static void connectivity_color(uint8_t color) {
    k_mutex_lock(&keyboard_led_lock, K_FOREVER);
    if (!state.sleeping) {
        state.bt_color = color;
        state.bt_until = k_uptime_get() + KL_BT_MS;
    }
    render_locked();
    k_mutex_unlock(&keyboard_led_lock);
}
void indicate_connectivity(void) {
#if IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    connectivity_color(zmk_ble_active_profile_is_connected() ? 4 :
                       zmk_ble_active_profile_is_open() ? 3 : 1);
#else
    connectivity_color(zmk_split_bt_peripheral_is_connected() ? 4 : 1);
#endif
}
void indicate_battery(void) {
    k_mutex_lock(&keyboard_led_lock, K_FOREVER);
    if (state.active && !state.sleeping) state.boot_until = k_uptime_get() + KL_BOOT_MS;
    render_locked();
    k_mutex_unlock(&keyboard_led_lock);
}
void indicate_layer(void) {
#if IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    k_mutex_lock(&keyboard_led_lock, K_FOREVER);
    render_locked();
    k_mutex_unlock(&keyboard_led_lock);
#endif
}
/* Compatibility API for the pinned Conductor integration. Stored LED settings
 * remain untouched; Keyboard Studio's build palette is authoritative. */
uint8_t zmk_rgbled_widget_get_layer_color(uint8_t layer) {
    return layer < ARRAY_SIZE(colors) ? colors[layer] : 0;
}
void zmk_rgbled_widget_set_layer_color(uint8_t layer, uint8_t color) {
    if (!keyboard_led_color_allowed(layer, color)) return;
    k_mutex_lock(&keyboard_led_lock, K_FOREVER);
    colors[layer] = color;
    if (layer == current_layer) state.layer_color = color;
    render_locked();
    k_mutex_unlock(&keyboard_led_lock);
}
void zmk_rgbled_widget_restore(void) { k_work_reschedule(&keyboard_led_work, K_NO_WAIT); }

static int listener(const zmk_event_t *eh) {
    if (as_zmk_activity_state_changed(eh)) {
        k_mutex_lock(&keyboard_led_lock, K_FOREVER);
        const bool was_sleeping = state.sleeping;
        state.active = zmk_activity_get_state() == ZMK_ACTIVITY_ACTIVE;
        state.sleeping = zmk_activity_get_state() == ZMK_ACTIVITY_SLEEP;
        if (!state.active) state.bt_until = state.boot_until = state.diag_until = 0;
        else if (was_sleeping) state.boot_until = k_uptime_get() + KL_BOOT_MS;
        /* Serialized with worker GPIO writes: queued work cannot relight sleep. */
        render_locked();
        k_mutex_unlock(&keyboard_led_lock);
        return ZMK_EV_EVENT_BUBBLE;
    }
    const struct zmk_battery_state_changed *battery = as_zmk_battery_state_changed(eh);
    if (battery) {
        k_mutex_lock(&keyboard_led_lock, K_FOREVER);
        state.battery = battery->state_of_charge;
        state.battery_valid = state.battery <= 100;
        render_locked();
        k_mutex_unlock(&keyboard_led_lock);
        return ZMK_EV_EVENT_BUBBLE;
    }
    if (as_zmk_usb_conn_state_changed(eh)) {
        k_work_reschedule(&keyboard_led_work, K_NO_WAIT);
        return ZMK_EV_EVENT_BUBBLE;
    }
#if IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
    if (as_zmk_ble_active_profile_changed(eh)) indicate_connectivity();
    if (as_zmk_layer_state_changed(eh)) indicate_layer();
#else
    if (as_zmk_split_peripheral_status_changed(eh)) indicate_connectivity();
#endif
    return ZMK_EV_EVENT_BUBBLE;
}
ZMK_LISTENER(keyboard_led, listener);
ZMK_SUBSCRIPTION(keyboard_led, zmk_activity_state_changed);
ZMK_SUBSCRIPTION(keyboard_led, zmk_battery_state_changed);
ZMK_SUBSCRIPTION(keyboard_led, zmk_usb_conn_state_changed);
#if IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)
ZMK_SUBSCRIPTION(keyboard_led, zmk_ble_active_profile_changed);
ZMK_SUBSCRIPTION(keyboard_led, zmk_layer_state_changed);
/* Observe only the central's split link; host status uses the ZMK event above. */
static void split_connected(struct bt_conn *conn, uint8_t err) {
    struct bt_conn_info info;
    if (err) connectivity_color(1); /* Failed host/split attempt has no profile event. */
    else if (!bt_conn_get_info(conn, &info) && info.role == BT_CONN_ROLE_CENTRAL)
        connectivity_color(4);
}
static void split_disconnected(struct bt_conn *conn, uint8_t reason) {
    struct bt_conn_info info;
    if (!bt_conn_get_info(conn, &info) && info.role == BT_CONN_ROLE_CENTRAL)
        connectivity_color(1);
}
BT_CONN_CB_DEFINE(keyboard_led_split_observer) = {
    .connected = split_connected, .disconnected = split_disconnected,
};
#else
ZMK_SUBSCRIPTION(keyboard_led, zmk_split_peripheral_status_changed);
#endif
static int keyboard_led_init(void) {
    uint8_t boot_diag_color = 0;
#if IS_ENABLED(CONFIG_RGBLED_WIDGET_RESET_DIAG)
    /* Preserve Conductor forensic capture/logging and fatal recovery, and show
     * critical reset causes before battery. Normal software reset stays silent. */
    extern uint8_t reset_diag_boot_color(void);
    boot_diag_color = reset_diag_boot_color();
#endif
    for (unsigned i=0; i<ARRAY_SIZE(rgb); i++) {
        if (!gpio_is_ready_dt(&rgb[i])) return -ENODEV;
        int err = gpio_pin_configure_dt(&rgb[i], GPIO_OUTPUT_INACTIVE);
        if (err) return err;
    }
    for (uint8_t i=0; i<ARRAY_SIZE(colors); i++)
        if (!keyboard_led_color_allowed(i, colors[i])) colors[i] = 0;
    k_mutex_lock(&keyboard_led_lock, K_FOREVER);
    state.active = zmk_activity_get_state() == ZMK_ACTIVITY_ACTIVE;
    state.sleeping = zmk_activity_get_state() == ZMK_ACTIVITY_SLEEP;
    /* Zero before the first successful event is unknown, not an empty cell. */
    state.battery = zmk_battery_state_of_charge();
    state.battery_valid |= state.battery > 0 && state.battery <= 100;
    const int64_t now = k_uptime_get();
    if (boot_diag_color == 1 || boot_diag_color == 3 || boot_diag_color == 5) {
        state.diag_color = boot_diag_color;
        state.diag_until = now + KL_DIAG_MS;
    }
    state.boot_until = now + (state.diag_until > now ? KL_DIAG_MS : 0) + KL_BOOT_MS;
    ready = true;
    render_locked();
    k_mutex_unlock(&keyboard_led_lock);
    return 0;
}
SYS_INIT(keyboard_led_init, APPLICATION, 95);
