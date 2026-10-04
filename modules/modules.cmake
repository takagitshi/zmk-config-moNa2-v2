# Zephyr 3.5 loads module extension roots before boards/shields and Devicetree.
string(REPLACE " " ";" mona2_aml_shields "${SHIELD}")
if("mona2_l" IN_LIST mona2_aml_shields OR "mona2_r" IN_LIST mona2_aml_shields)
  if(KEYMAP_FILE)
    set(mona2_aml_keymap "${KEYMAP_FILE}")
  elseif(EXISTS "${ZMK_CONFIG}/mona2.keymap")
    # This hook can precede ZMK's own keymap-selection hook on pristine builds.
    set(mona2_aml_keymap "${ZMK_CONFIG}/mona2.keymap")
  else()
    message(FATAL_ERROR "moNa2 AML generation requires config/mona2.keymap or KEYMAP_FILE")
  endif()
  set(mona2_aml_generator "${CMAKE_CURRENT_LIST_DIR}/../scripts/generate-aml-exclusions.py")
  set(mona2_aml_header "${CMAKE_BINARY_DIR}/aml-exclusions.h")
  set(mona2_aml_depfile "${CMAKE_BINARY_DIR}/aml-keymap-inputs.txt")
  execute_process(
    COMMAND "${PYTHON_EXECUTABLE}" "${mona2_aml_generator}" "${mona2_aml_keymap}" "${mona2_aml_header}" --mouse-layer 1 --key-count 42 --depfile "${mona2_aml_depfile}"
    RESULT_VARIABLE mona2_aml_result
    ERROR_VARIABLE mona2_aml_error
  )
  if(NOT mona2_aml_result EQUAL 0)
    message(FATAL_ERROR "moNa2 AML generation failed: ${mona2_aml_error}")
  endif()
  # Zephyr 3.5 can miss inputs packed together on one GCC dependency line.
  file(STRINGS "${mona2_aml_depfile}" mona2_aml_inputs)
  set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    ${mona2_aml_inputs} "${mona2_aml_generator}"
    "${CMAKE_CURRENT_LIST_DIR}/../scripts/aml_keymap.py")
  list(APPEND DTS_EXTRA_CPPFLAGS "-I${CMAKE_BINARY_DIR}")
endif()
