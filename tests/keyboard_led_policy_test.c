/* Compile: cc -std=c99 -Wall -Wextra -Werror -Iinclude tests/keyboard_led_policy_test.c */
#include <assert.h>
#include "keyboard_led_policy.h"
int main(void) {
    struct keyboard_led_state s = {.active=true, .usb=true, .battery_valid=true};
    for (int n=0; n<=100; n++) {
        s.battery=n;
        assert(keyboard_led_color(&s, 0) == (n<10 ? 1 : n<30 ? 3 : 2));
        assert(keyboard_led_color(&s, 500) == (n>=80 ? 0 : n<10 ? 1 : n<30 ? 3 : 2));
        assert(keyboard_led_color(&s, 1000) == (n<10 ? 1 : n<30 ? 3 : 2));
    }
    s.battery_valid=false;
    assert(keyboard_led_color(&s, 0)==6 && keyboard_led_color(&s, 500)==6);
    assert(keyboard_led_next(&s, 500)==0);
    s.battery_valid=true; s.battery=50;
    s.bt_color=4; s.bt_until=1500; s.layer_color=7; s.layer_until=2500;
    assert(keyboard_led_color(&s, 1499)==4);
    assert(keyboard_led_next(&s, 1499)==1);
    assert(keyboard_led_color(&s, 1500)==7);
    assert(keyboard_led_color(&s, 2500)==2);
    s.usb=false;
    assert(keyboard_led_color(&s, 2500)==0);
    assert(keyboard_led_next(&s, 2500)==0);
    s.boot_until=2000;
    s.bt_until=s.layer_until=0;
    assert(keyboard_led_color(&s, 1999)==2 && keyboard_led_color(&s, 2000)==0);
    s.battery_valid=false;
    assert(keyboard_led_color(&s, 1999)==6);
    s.active=false; s.bt_until=1500; s.bt_color=4; s.layer_until=9999;
    assert(keyboard_led_color(&s, 0)==4 && keyboard_led_next(&s, 0)==1500);
    assert(keyboard_led_color(&s, 1499)==4 && keyboard_led_next(&s, 1499)==1);
    assert(keyboard_led_color(&s, 1500)==0 && keyboard_led_next(&s, 1500)==0);
    s.usb=true; s.battery_valid=true; s.battery=80;
    assert(keyboard_led_color(&s, 500)==4); /* transient also wins at USB IDLE */
    assert(keyboard_led_color(&s, 1500)==0 && keyboard_led_color(&s, 2000)==2);
    s.bt_until=0;
    assert(keyboard_led_color(&s, 0)==2 && keyboard_led_color(&s, 500)==0);
    s.sleeping=true;
    assert(keyboard_led_color(&s, 0)==0 && keyboard_led_next(&s, 0)==0);
    s.sleeping=false; s.active=true; s.bt_until=s.layer_until=s.boot_until=0;
    assert(keyboard_led_color(&s, 0)==2);
    for (int layer=0; layer<32; layer++) for (int color=0; color<8; color++)
        assert(keyboard_led_color_allowed(layer,color) == (color!=1 || layer==8));
    assert(!keyboard_led_color_allowed(32,0) && !keyboard_led_color_allowed(8,8));
    return 0;
}
