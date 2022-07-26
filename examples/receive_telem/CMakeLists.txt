## locals ######################################################################
set(exe receive_telem)


## targets #####################################################################
add_executable(${exe} "main.cc")
target_include_directories(${exe} PUBLIC ${COMMON_INC})
target_link_libraries(${exe} PUBLIC ${COMMON_DEP})
