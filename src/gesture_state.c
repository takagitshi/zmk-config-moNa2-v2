/*
 * Copyright (c) 2026 Takashi Imai
 *
 * SPDX-License-Identifier: MIT
 */

#include <limits.h>
#include <mona2/gesture_state.h>

static int32_t saturating_add(int32_t lhs, int32_t rhs) {
    if (rhs > 0 && lhs > INT32_MAX - rhs) {
        return INT32_MAX;
    }
    if (rhs < 0 && lhs < INT32_MIN - rhs) {
        return INT32_MIN;
    }
    return lhs + rhs;
}

static uint32_t magnitude(int32_t value) {
    return value < 0 ? (uint32_t)(-(int64_t)value) : (uint32_t)value;
}

void mona2_gesture_state_reset(struct mona2_gesture_state *state) {
    state->x = 0;
    state->y = 0;
    state->cooldown_until_ms = 0;
    state->cooling_down = false;
}

enum mona2_gesture_direction
mona2_gesture_state_update(struct mona2_gesture_state *state, enum mona2_gesture_axis axis,
                           int32_t value, bool sync, int64_t now_ms, uint32_t threshold,
                           uint32_t cooldown_ms) {
    if (state->cooling_down) {
        state->x = 0;
        state->y = 0;
        if (sync && now_ms >= state->cooldown_until_ms) {
            state->cooling_down = false;
        }
        return MONA2_GESTURE_NONE;
    }

    if (axis == MONA2_GESTURE_AXIS_X) {
        state->x = saturating_add(state->x, value);
    } else {
        state->y = saturating_add(state->y, value);
    }

    if (!sync) {
        return MONA2_GESTURE_NONE;
    }

    const uint32_t abs_x = magnitude(state->x);
    const uint32_t abs_y = magnitude(state->y);
    if ((uint64_t)abs_x + abs_y < threshold) {
        return MONA2_GESTURE_NONE;
    }

    enum mona2_gesture_direction direction;
    if (abs_x >= abs_y) {
        direction = state->x < 0 ? MONA2_GESTURE_LEFT : MONA2_GESTURE_RIGHT;
    } else {
        direction = state->y < 0 ? MONA2_GESTURE_UP : MONA2_GESTURE_DOWN;
    }

    state->x = 0;
    state->y = 0;
    state->cooling_down = true;
    state->cooldown_until_ms = now_ms + cooldown_ms;
    return direction;
}
