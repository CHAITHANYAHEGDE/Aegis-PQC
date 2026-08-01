cmake_minimum_required(VERSION 3.15)
project(AegisPQC)

# 1. Detect Python using modern CMake
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# 2. Try to find pybind11, install if missing
find_package(pybind11 CONFIG)

if(NOT pybind11_FOUND)
    message(STATUS "pybind11 not found. Attempting to install via pip...")
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" -m pip install pybind11
        RESULT_VARIABLE PIP_INSTALL_RESULT
    )
    if(NOT PIP_INSTALL_RESULT EQUAL 0)
        message(FATAL_ERROR "Failed to install pybind11 automatically. Please install it manually: python3 -m pip install pybind11")
    endif()
    
    # We must explicitly add the pybind11 cmake dir to CMAKE_PREFIX_PATH after installing
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" -c "import pybind11; print(pybind11.get_cmake_dir())"
        OUTPUT_VARIABLE PYBIND11_CMAKE_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
    )
    list(APPEND CMAKE_PREFIX_PATH "${PYBIND11_CMAKE_DIR}")
    
    find_package(pybind11 CONFIG REQUIRED)
endif()

# 3. Create the Python extension module
pybind11_add_module(aegis_engine aegis_engine.cpp)

# 4. Link against existing liboqs library
# Make this portable by assuming liboqs_src/build is in the project root
set(OQS_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/liboqs_src/build/include")
set(OQS_LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/liboqs_src/build/lib")

target_include_directories(aegis_engine PRIVATE "${OQS_INCLUDE_DIR}")
target_link_directories(aegis_engine PRIVATE "${OQS_LIB_DIR}")
target_link_libraries(aegis_engine PRIVATE oqs)

# Needed for macOS pybind11 modules
if(APPLE)
    set_target_properties(aegis_engine PROPERTIES LINK_FLAGS "-undefined dynamic_lookup")
endif()
