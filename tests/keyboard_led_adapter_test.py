"""Exercise the actual renderer/listeners with deterministic hardware stubs."""
from pathlib import Path
import re, subprocess, tempfile
ROOT=Path(__file__).resolve().parents[1]
STUB=r'''
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <assert.h>
#include <errno.h>
#define IS_ENABLED(x) (x)
#define CONFIG_ZMK_BATTERY_REPORTING_FETCH_MODE_STATE_OF_CHARGE 0
#define CONFIG_ZMK_BATTERY_REPORTING_FETCH_MODE_LITHIUM_VOLTAGE 1
#define CONFIG_RGBLED_WIDGET_RESET_DIAG 1
#define ARRAY_SIZE(a) (sizeof(a)/sizeof((a)[0]))
#define DT_NODELABEL(x) x
#define led0 0
#define led1 1
#define led2 2
struct gpio_dt_spec { int pin; };
#define GPIO_DT_SPEC_GET(node, prop) {node}
#define GPIO_OUTPUT_INACTIVE 0
static unsigned physical;
static bool gpio_is_ready_dt(const struct gpio_dt_spec *s) { return true; }
static int gpio_pin_configure_dt(const struct gpio_dt_spec *s, int flags) { return 0; }
static int gpio_pin_set_dt(const struct gpio_dt_spec *s, int value) {
 if(value) physical |= 1U<<s->pin; else physical &= ~(1U<<s->pin); return 0;
}
struct k_work { int dummy; };
struct k_work_delayable { int64_t delay; };
struct k_mutex { int dummy; };
#define K_MUTEX_DEFINE(n) static struct k_mutex n
#define K_WORK_DELAYABLE_DEFINE(n, cb) static struct k_work_delayable n
#define K_FOREVER 0
#define K_NO_WAIT 0
#define K_MSEC(n) (n)
static int64_t now;
static int64_t k_uptime_get(void) {return now;}
static void k_mutex_lock(struct k_mutex *m, int n) {}
static void k_mutex_unlock(struct k_mutex *m) {}
static int k_work_reschedule(struct k_work_delayable *w, int64_t n) { w->delay=n; return 0; }
static int k_work_cancel_delayable(struct k_work_delayable *w) {w->delay=-1;return 0;}
static void *zmk_workqueue_lowprio_work_q(void) {return NULL;}
static int k_work_reschedule_for_queue(void *q, struct k_work_delayable *w, int64_t n) {return k_work_reschedule(w,n);}
#define NRF_POWER 0
static bool usb;
static bool nrf_power_usbregstatus_vbusdet_get(int r) {return usb;}
struct device {int dummy;};
static struct device battery_device;
#define DT_CHOSEN(x) 0
#define DEVICE_DT_GET(n) (&battery_device)
static bool sensor_ok=true;
static int sensor_reads, voltage_mv=4100;
struct sensor_value {int val1, val2;};
#define SENSOR_CHAN_VOLTAGE 1
#define SENSOR_CHAN_GAUGE_STATE_OF_CHARGE 2
static bool device_is_ready(const struct device *d) {return true;}
static int sensor_sample_fetch_chan(const struct device *d, int chan) {sensor_reads++;return sensor_ok ? 0 : -EIO;}
static int sensor_channel_get(const struct device *d, int chan, struct sensor_value *v) {
 v->val1=voltage_mv/1000;v->val2=voltage_mv%1000*1000;return 0;
}
#define ZMK_ACTIVITY_ACTIVE 0
#define ZMK_ACTIVITY_IDLE 1
#define ZMK_ACTIVITY_SLEEP 2
static int activity;
static int zmk_activity_get_state(void) {return activity;}
static uint8_t soc;
static uint8_t zmk_battery_state_of_charge(void) {return soc;}
static bool connected, open_profile;
static bool zmk_ble_active_profile_is_connected(void) {return connected;}
static bool zmk_ble_active_profile_is_open(void) {return open_profile;}
static bool zmk_split_bt_peripheral_is_connected(void) {return connected;}
static uint8_t layer;
static uint8_t zmk_keymap_highest_layer_active(void) {return layer;}
typedef struct {int type;} zmk_event_t;
struct zmk_battery_state_changed {int type;uint8_t state_of_charge;};
#define as_zmk_activity_state_changed(e) ((e)->type==1)
#define as_zmk_battery_state_changed(e) ((e)->type==2 ? (const struct zmk_battery_state_changed*)(e):NULL)
#define as_zmk_usb_conn_state_changed(e) ((e)->type==3)
#define as_zmk_ble_active_profile_changed(e) ((e)->type==4)
#define as_zmk_layer_state_changed(e) ((e)->type==5)
#define as_zmk_split_peripheral_status_changed(e) ((e)->type==6)
#define ZMK_EV_EVENT_BUBBLE 0
#define ZMK_LISTENER(n, cb)
#define ZMK_SUBSCRIPTION(n, event)
struct bt_conn {int role;};
struct bt_conn_info {int role;};
#define BT_CONN_ROLE_CENTRAL 1
static int bt_conn_get_info(struct bt_conn *c, struct bt_conn_info *i) {i->role=c->role;return 0;}
struct bt_callbacks {void (*connected)(struct bt_conn*,uint8_t);void (*disconnected)(struct bt_conn*,uint8_t);};
#define BT_CONN_CB_DEFINE(n) static struct bt_callbacks n
#define SYS_INIT(fn, level, prio)
static int diag_captured;
uint8_t reset_diag_boot_color(void) {diag_captured++; return 0;}
'''
TEST=r'''
static void event(int type) { zmk_event_t e={.type=type}; listener(&e); }
int main(void) {
 assert(keyboard_led_init()==0 && diag_captured==1);
 assert(physical==6); /* unknown cyan: green led2 + blue led1 */
 struct zmk_battery_state_changed battery={.type=2,.state_of_charge=10};
 listener((const zmk_event_t*)&battery);
 assert(physical==5); /* yellow: red led0 + green led2 */
 now=2000;render(NULL);assert(physical==0 && keyboard_led_work.delay==-1);
 usb=true;event(3);render(NULL);assert(physical==5);
 battery.state_of_charge=30;listener((const zmk_event_t*)&battery);assert(physical==4);
 battery.state_of_charge=80;listener((const zmk_event_t*)&battery);assert(physical==4);
 now=2500;render(NULL);assert(physical==0);
 now=3000;render(NULL);assert(physical==4);
 connected=true;indicate_connectivity();assert(physical==2); /* blue physical led1 */
#if CONFIG_ZMK_SPLIT_ROLE_CENTRAL
 layer=1;event(5);assert(physical==2); /* BT wins */
 now=4500;render(NULL);assert(physical==0); /* both deadlines end, blink off */
 now=5000;layer=31;zmk_rgbled_widget_set_layer_color(31,5);event(5);assert(physical==3);
 zmk_rgbled_widget_set_layer_color(31,1);assert(zmk_rgbled_widget_get_layer_color(31)==5);
#endif
 activity=ZMK_ACTIVITY_IDLE;event(1);assert(keyboard_led_sample_work.delay==0);
 sample_idle_battery(NULL);assert(sensor_reads==1 && state.battery_valid);
 assert(state.battery==87 && keyboard_led_sample_work.delay==60000);
 voltage_mv=3600;now+=60000;sample_idle_battery(NULL);assert(state.battery==21 && physical==5);
 sensor_ok=false;now+=60000;sample_idle_battery(NULL);assert(!state.battery_valid && physical==6);
 usb=false;event(3);render(NULL);assert(physical==0 && keyboard_led_sample_work.delay==-1);
 int reads=sensor_reads;sample_idle_battery(NULL);assert(sensor_reads==reads);
 /* Connection events are visible in IDLE; they do not wake activity or poll
  * the battery, and expire back to off/USB without requiring key input. */
 connected=false;indicate_connectivity();assert(physical==1);
 assert(activity==ZMK_ACTIVITY_IDLE && !state.active);
 assert(keyboard_led_work.delay==1500 && keyboard_led_sample_work.delay==-1);
 now+=1499;render(NULL);assert(physical==1 && keyboard_led_work.delay==1);
 now++;render(NULL);assert(physical==0 && keyboard_led_work.delay==-1);
 connected=true;indicate_connectivity();assert(physical==2);
 now+=1500;render(NULL);assert(physical==0 && sensor_reads==reads);
 usb=true;event(3);render(NULL);assert(physical==6);
 connected=false;indicate_connectivity();assert(physical==1);
 now+=1500;render(NULL);assert(physical==6 && activity==ZMK_ACTIVITY_IDLE);
 activity=ZMK_ACTIVITY_SLEEP;event(1);usb=true;event(3);render(NULL);
 assert(physical==0 && keyboard_led_work.delay==-1 && keyboard_led_sample_work.delay==-1);
 indicate_connectivity();indicate_layer();indicate_battery();render(NULL);assert(physical==0);
 sample_idle_battery(NULL);assert(sensor_reads==reads);
 activity=ZMK_ACTIVITY_ACTIVE;event(1);assert(physical==6);
 assert(keyboard_led_sample_work.delay==-1);return 0;
}
'''
def main():
    source=(ROOT/'src/keyboard_led.c').read_text()
    source=re.sub(r'^#include .*\n','',source,flags=re.M)
    policy=(ROOT/'include/keyboard_led_policy.h').read_text().replace('#pragma once','')
    palette=[0,7,2,3,5,4,2,6,1,3]+[0]*22
    defines=''.join(f'#define CONFIG_RGBLED_WIDGET_LAYER_{i}_COLOR {c}\n' for i,c in enumerate(palette))
    with tempfile.TemporaryDirectory(prefix='keyboard-led-adapter-') as tmp:
        tmp=Path(tmp)
        policy_binary=tmp/'policy-test'
        subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=undefined','-I'+str(ROOT/'include'),str(ROOT/'tests/keyboard_led_policy_test.c'),'-o',str(policy_binary)],check=True)
        subprocess.run([str(policy_binary)],check=True)
        for central in (0,1):
            unit=tmp/f'led-{central}.c'; binary=tmp/f'led-{central}'
            unit.write_text(STUB+f'\n#define CONFIG_ZMK_SPLIT_ROLE_CENTRAL {central}\n'+defines+policy+source+TEST)
            subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-Wno-unused-function','-Wno-unused-variable','-fsanitize=undefined',str(unit),'-o',str(binary)],check=True)
            subprocess.run([str(binary)],check=True)
    print(f'{ROOT.name}: actual RGB renderer central/peripheral adapter PASS')
if __name__=='__main__':main()
