## project setup ###############################################################

cmake_minimum_required(VERSION 3.10)
project(zendar-sdk)

set(LOCAL_API  FALSE CACHE BOOL "Path to ZenApi package installation")
set(SYSTEM_API TRUE CACHE BOOL "Path to ZenApi package installation")

list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/cmake/modules)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 14)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Werror")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Werror")


## common dependencies #########################################################

if (LOCAL_API)
  list(APPEND CMAKE_PREFIX_PATH "$ENV{ZEN_CODE}/build/install/share/zendar/cmake")
  find_package(ZenClient REQUIRED)
  list(APPEND COMMON_DEP zen::zendar_client)
elseif(SYSTEM_API)
  list(APPEND CMAKE_PREFIX_PATH "/usr/share/zendar/cmake")
  find_package(ZenClient REQUIRED)
  list(APPEND COMMON_DEP zen::zendar_client)
endif()


## subprojects #################################################################

add_subdirectory("examples")
