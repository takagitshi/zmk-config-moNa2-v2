CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -O2

.PHONY: test clean

test: tests/gesture_state_test
	./tests/gesture_state_test

tests/gesture_state_test: tests/gesture_state_test.c src/gesture_state.c include/mona2/gesture_state.h
	$(CC) $(CFLAGS) -Iinclude tests/gesture_state_test.c src/gesture_state.c -o $@

clean:
	$(RM) tests/gesture_state_test
