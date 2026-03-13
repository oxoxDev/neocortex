cmake_minimum_required(VERSION 3.14)
project(alphahuman-sdk-cpp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ---------- Dependencies ----------

include(FetchContent)

FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG        v3.11.3
)
FetchContent_MakeAvailable(nlohmann_json)

find_package(CURL REQUIRED)

# ---------- Library ----------

add_library(alphahuman
    src/memory_client.cpp
)

target_include_directories(alphahuman PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

target_link_libraries(alphahuman
    PUBLIC  nlohmann_json::nlohmann_json
    PRIVATE CURL::libcurl
)

# ---------- Example ----------

add_executable(example_usage example/example_usage.cpp)
target_link_libraries(example_usage PRIVATE alphahuman CURL::libcurl)

# ---------- Tests ----------

option(BUILD_TESTS "Build tests" ON)
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(test)
endif()
