"""Editable LED palette contract, shared by source and generated checks."""
import re

def verify_led_palette(config):
    for layer in range(10):
        values = re.findall(rf"^CONFIG_RGBLED_WIDGET_LAYER_{layer}_COLOR=(\d+)$", config, re.M)
        if len(values) != 1:
            raise AssertionError(f"Layer {layer} needs exactly one LED palette setting")
        color = int(values[0])
        if not 0 <= color <= 7 or (color == 1 and layer != 8):
            raise AssertionError(f"Invalid LED color {color} for layer {layer}; red belongs to setting layer 8")
