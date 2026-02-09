cmake_minimum_required(VERSION 3.13)

# Include pico-sdk
include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(test_project C CXX ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

# Initialize the SDK
pico_sdk_init()

# Create executable
add_executable(test_project
    main.c
)

# Link libraries
target_link_libraries(test_project
    pico_stdlib
)

# Create map/bin/hex/uf2 files
pico_add_extra_outputs(test_project)

# Enable USB output, disable UART output
pico_enable_stdio_usb(test_project 1)
pico_enable_stdio_uart(test_project 0)
