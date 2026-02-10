cmake_minimum_required(VERSION 3.13)

# Initialize pico-sdk from parent cmake file
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(test_project C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the SDK
pico_sdk_init()

add_executable(blink
  blink.c
)

# Pull in our pico_stdlib which pulls in commonly used features
target_link_libraries(blink pico_stdlib)

# Create map/bin/hex file etc.
pico_add_extra_outputs(blink)
