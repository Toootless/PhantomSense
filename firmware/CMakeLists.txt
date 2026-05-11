cmake_minimum_required(VERSION 3.16)

project(phantomsense_firmware)

# Set the IDF target
set(SUPPORTED_TARGETS esp32s3)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)

project_start(phantomsense_firmware)
