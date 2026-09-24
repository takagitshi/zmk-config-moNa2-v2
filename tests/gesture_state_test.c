/* SPDX-License-Identifier: MIT */

#include <assert.h>
#include <limits.h>
#include <stdio.h>

#include <mona2/gesture_state.h>

#define THRESHOLD 100
#define COOLDOWN_MS 150

static enum mona2_gesture_direction update(struct mona2_gesture_state *state,
                                            enum mona2_gesture_axis axis, int32_t value,
                                            bool sync, int64_t now_ms) {
    return mona2_gesture_state_update(state, axis, value, sync, now_ms, THRESHOLD,
                                      COOLDOWN_MS);
}

int main(void) {
    struct mona2_gesture_state state;

    mona2_gesture_state_reset(&state);
    assert(update(&state, MONA2_GESTURE_AXIS_X, 80, false, 1000) == MONA2_GESTURE_NONE);
    assert(update(&state, MONA2_GESTURE_AXIS_Y, 60, true, 1000) == MONA2_GESTURE_RIGHT);

    mona2_gesture_state_reset(&state);
    assert(update(&state, MONA2_GESTURE_AXIS_X, -100, true, 1000) == MONA2_GESTURE_LEFT);

    mona2_gesture_state_reset(&state);
    assert(update(&state, MONA2_GESTURE_AXIS_Y, -100, true, 1000) == MONA2_GESTURE_UP);

    mona2_gesture_state_reset(&state);
    assert(update(&state, MONA2_GESTURE_AXIS_Y, 100, true, 1000) == MONA2_GESTURE_DOWN);
    assert(update(&state, MONA2_GESTURE_AXIS_X, 200, true, 1100) == MONA2_GESTURE_NONE);
    assert(update(&state, MONA2_GESTURE_AXIS_X, 100, true, 1165) == MONA2_GESTURE_NONE);
    assert(update(&state, MONA2_GESTURE_AXIS_X, 100, true, 1180) == MONA2_GESTURE_RIGHT);

    mona2_gesture_state_reset(&state);
    assert(update(&state, MONA2_GESTURE_AXIS_X, INT32_MAX, false, 1000) == MONA2_GESTURE_NONE);
    assert(update(&state, MONA2_GESTURE_AXIS_X, 1, false, 1000) == MONA2_GESTURE_NONE);
    assert(state.x == INT32_MAX);

    puts("gesture_state_test: PASS");
    return 0;
}
