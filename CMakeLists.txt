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

# The LED arbiter replaces legacy display owners only. All pinned modules and
# non-LED firmware sources remain in place. Defer until target_sources is final.
if(CONFIG_KEYBOARD_LED_POLICY)
  target_sources(app PRIVATE ${CMAKE_CURRENT_LIST_DIR}/src/keyboard_led.c)
  function(keyboard_led_single_owner)
    get_target_property(_sources app SOURCES)
    list(FILTER _sources EXCLUDE REGEX "/zmk-rgbled-widget/src/widget\\.c$")
    list(FILTER _sources EXCLUDE REGEX "/zmk-feature-charge-indicator/src/charge_indicator\\.c$")
    set_property(TARGET app PROPERTY SOURCES "${_sources}")
  endfunction()
  cmake_language(DEFER DIRECTORY "${APPLICATION_SOURCE_DIR}" CALL keyboard_led_single_owner)
endif()
