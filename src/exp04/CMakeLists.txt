cmake_minimum_required(VERSION 3.10)
project(myapp LANGUAGES CXX)

find_package(PkgConfig REQUIRED)
pkg_check_modules(OPUS REQUIRED opus)
pkg_check_modules(LIBOGG REQUIRED ogg)

add_executable(opus-encode
        include/dr_wav.h
        src/encode.cpp)

target_include_directories(opus-encode PRIVATE
        include
        ${LIBOGG_INCLUDE_DIRS}
        ${LIBOPUS_INCLUDE_DIRS}
)

target_link_libraries(opus-encode PRIVATE
        opus
        ${LIBOGG_LIBRARIES}
        ${LIBOPUS_LIBRARIES}
)


add_executable(opus-decode
        include/dr_wav.h
        src/decode.cpp)

target_include_directories(opus-decode PRIVATE
        include
        ${LIBOGG_INCLUDE_DIRS}
        ${LIBOPUS_INCLUDE_DIRS}
)

target_link_libraries(opus-decode PRIVATE
        opus
        ${LIBOGG_LIBRARIES}
        ${LIBOPUS_LIBRARIES}
)


add_executable(drop-ulaw-frames
        include/dr_wav.h
        src/drop-frames.cpp)

target_include_directories(drop-ulaw-frames PRIVATE
        include
)

#target_link_libraries(opus-drop-ulaw-frames PRIVATE
#        opus
#        ${LIBOGG_LIBRARIES}
#        ${LIBOPUS_LIBRARIES}
#)
