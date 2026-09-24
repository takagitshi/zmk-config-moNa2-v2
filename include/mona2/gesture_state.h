/*
 * Copyright (c) 2026 Takashi Imai
 *
 * SPDX-License-Identifier: MIT
 */

#pragma once

#include <stdbool.h>
#include <stdint.h>

enum mona2_gesture_direction {
    MONA2_GESTURE_NONE,
    MONA2_GESTURE_LEFT,
    MONA2_GESTURE_RIGHT,
    MONA2_GESTURE_UP,
    MONA2_GESTURE_DOWN,
};

enum mona2_gesture_axis {
    MONA2_GESTURE_AXIS_X,
    MONA2_GESTURE_AXIS_Y,
};

struct mona2_gesture_state {
    int32_t x;
    int32_t y;
    int64_t cooldown_until_ms;
    bool cooling_down;
};

void mona2_gesture_state_reset(struct mona2_gesture_state *state);

enum mona2_gesture_direction
mona2_gesture_state_update(struct mona2_gesture_state *state, enum mona2_gesture_axis axis,
                           int32_t value, bool sync, int64_t now_ms, uint32_t threshold,
                           uint32_t cooldown_ms);
