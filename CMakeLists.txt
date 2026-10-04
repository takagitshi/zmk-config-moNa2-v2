if(CONFIG_SHIELD_MONA2_L OR CONFIG_SHIELD_MONA2_R)
  if(NOT "${KEYMAP_FILE}" STREQUAL "${mona2_aml_keymap}")
    message(FATAL_ERROR "AML exclusions were not derived from the selected KEYMAP_FILE")
  endif()
  zephyr_library()
  zephyr_include_directories(${CMAKE_CURRENT_LIST_DIR}/include)
  zephyr_library_sources_ifdef(CONFIG_ZMK_INPUT_PROCESSOR_GESTURE
    src/gesture_state.c
    src/input_processor_gesture.c)
endif()
