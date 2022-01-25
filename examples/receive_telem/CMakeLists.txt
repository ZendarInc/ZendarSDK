## locals ######################################################################

set(_exe receive_telem)
set(_src ${CMAKE_CURRENT_SOURCE_DIR}/main.cc)
set(_inc ${CMAKE_CURRENT_SOURCE_DIR})
set(_dep zendar_api2 zendar_common shared_protobuf)


## targets #####################################################################

add_executable(${_exe} ${_src})
target_include_directories(${_exe} PUBLIC ${_inc} ${COMMON_INC})
target_link_libraries(${_exe} PUBLIC ${_dep} ${COMMON_DEP})
