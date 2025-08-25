cmake_minimum_required(VERSION 3.26)
# XXX: Some versions of CMake around 3.21~3.26 crash CMake on Windows. Reason and range is still TBD.

project("basilisk")

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE
      "Debug"
      CACHE STRING "Choose the type of build, options are: Debug Release RelWithDebInfo MinSizeRel." FORCE)
endif(NOT CMAKE_BUILD_TYPE)

list(APPEND CMAKE_MODULE_PATH ${CMAKE_BINARY_DIR})
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

list(APPEND CMAKE_PREFIX_PATH ${CMAKE_BINARY_DIR})
list(APPEND CMAKE_PREFIX_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
list(APPEND CMAKE_PREFIX_PATH "${CMAKE_CURRENT_SOURCE_DIR}/dependencies/eigen3") # add eigen3 preffix
list(APPEND CMAKE_PREFIX_PATH "${CMAKE_CURRENT_SOURCE_DIR}/dependencies/cspice") # add cspice preffix

# BUILD_VIZINTERFACE "Build VizInterface Module" OFF
list(APPEND EXCLUDED_BSK_TARGETS "vizInterface")
# BUILD_OPNAV "Build OpNav Modules" OFF
list(APPEND EXCLUDED_BSK_TARGETS "limbFinding" "centerRadiusCNN" "houghCircles" "camera")
# BUILD_MUJOCO "Build MuJoCo Modules" OFF
list(APPEND EXCLUDED_BSK_LIBRARIES "mujocoDynamics")

# ! create_copies : create copies to keeping them in dist. The function takes one
# required argument and N optional arguments. \argn: a list of supporting file paths
function(create_copies destinationPath)
  # Do nothing if building in-source
  if(${CMAKE_CURRENT_BINARY_DIR} STREQUAL ${CMAKE_CURRENT_SOURCE_DIR})
    return()
  endif()

  foreach(filePath ${ARGN})
    get_filename_component(fileName ${filePath} NAME)

    # Get OS dependent path to use in `execute_process`
    file(TO_NATIVE_PATH "${destinationPath}/${fileName}" link)
    file(TO_NATIVE_PATH "${filePath}" target)

    # Delete the files from the dist directory, and instead just link them to the files in source
    file(REMOVE ${destinationPath}/${fileName})
    
    file(COPY ${target} DESTINATION ${destinationPath})
    message(STATUS "copy file: ${target}")
  endforeach(filePath)
endfunction(create_copies)

function(sub_dir_list result curdir)
  # Searches through all directories in source, and keeps those called GeneralModuleFiles
  file(
    GLOB_RECURSE children
    LIST_DIRECTORIES true
    RELATIVE ${curdir}
    ${curdir}/*/)
  set(dirlist "")
  foreach(child ${children})
    if(IS_DIRECTORY ${curdir}/${child})
      string(FIND ${curdir}/${child} "_GeneralModuleFiles" FOUND)
      string(FIND ${curdir}/${child} "__pycache__" FOUND_PY)
      string(FIND ${curdir}/${child} "_UnitTest" FOUND_UNIT)
      if(${FOUND} GREATER -1
         AND ${FOUND_PY} EQUAL -1
         AND ${FOUND_UNIT} EQUAL -1)
        list(APPEND dirlist ${child})
      endif()
    endif()
  endforeach()
  set(${result}
      ${dirlist}
      PARENT_SCOPE)
endfunction(sub_dir_list)

# add header search directories
include_directories("${CMAKE_SOURCE_DIR}")

function(generate_package_libraries INIT_DIRECTORY AllLibs)
  # Find all _GeneralModuleFiles and put them into library targets so they aren't rewrapped, built with every module.

  # Find all _GeneralModuleFiles directories
  sub_dir_list(LIB_DIRS ${INIT_DIRECTORY})
  foreach(LIB_DIR ${LIB_DIRS})

    # Determine the name of the parent directory of _GeneralModuleFiles (i.e. dynamics, environment, etc)
    get_filename_component(PARENT_DIR ${LIB_DIR} DIRECTORY) # Relative to the source directory (e.g. simulation/power)
    string(FIND ${PARENT_DIR} "/" DIR_NAME_IDX REVERSE)
    math(EXPR DIR_NAME_IDX "${DIR_NAME_IDX} + 1") # "simulation/"
    string(SUBSTRING ${PARENT_DIR} ${DIR_NAME_IDX} -1 PARENT_DIR_NAME) # Should be "power"

    if(${PARENT_DIR_NAME} IN_LIST EXCLUDED_BSK_LIBRARIES)
      message(STATUS "skipped package library: ${PARENT_DIR_NAME}")
        continue()
    endif()

    # Set the library name (ex. dynamicsLib, environmentLib, etc)
    set(LIB_NAME "${PARENT_DIR_NAME}Lib")
    # Added to build ExternalModulesLib
    file(
      GLOB LIB_DIR
      RELATIVE ${CMAKE_SOURCE_DIR}
      "${INIT_DIRECTORY}/${LIB_DIR}")
    # Grab the library source files
    file(GLOB C_FILES "${LIB_DIR}/*.cpp" "${LIB_DIR}/*.c" "${LIB_DIR}/*.h")
    # Grab the framework source files
    file(GLOB BSK_FWK_FILES "${CMAKE_SOURCE_DIR}/architecture/_GeneralModuleFiles/*.cpp" # Might not be needed
         "${CMAKE_SOURCE_DIR}/architecture/_GeneralModuleFiles/*.h"
         "${CMAKE_SOURCE_DIR}/architecture/_GeneralModuleFiles/*.c")

    # Add Target
    add_library(${LIB_NAME} SHARED ${C_FILES} ${BSK_FWK_FILES})

    # Add to list of library
    list(APPEND AllLibs ${LIB_NAME})

    # If the library directory has a Custom.cmake, include that
    if(EXISTS "${CMAKE_SOURCE_DIR}/${LIB_DIR}/Custom.cmake")
      message(STATUS "Including custom Custom.cmake for package lib: ${LIB_DIR}")
      include("${CMAKE_SOURCE_DIR}/${LIB_DIR}/Custom.cmake")
    endif()

    # Link all necessary libraries
    target_link_libraries(${LIB_NAME} PUBLIC ModuleIdGenerator)
    target_link_libraries(${LIB_NAME} PUBLIC Eigen3::Eigen3)
    if(${PARENT_DIR_NAME} STREQUAL "mujocoDynamics")
      target_link_libraries(${LIB_NAME} PUBLIC dynamicsLib)
      # dynamicsLib already has ArchitectureUtilities and cMsgCInterface
      # publicly linked, so no need to add them (again) for mujocoDynamics
    else()
      target_link_libraries(${LIB_NAME} PUBLIC ArchitectureUtilities)
      target_link_libraries(${LIB_NAME} PUBLIC cMsgCInterface)
    endif()

    # define build location, IDE generation specifications
    set_target_properties(${LIB_NAME} PROPERTIES FOLDER ${PARENT_DIR})
    set_target_properties(${LIB_NAME} PROPERTIES LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/Basilisk")
    set_target_properties(${LIB_NAME} PROPERTIES LIBRARY_OUTPUT_DIRECTORY_DEBUG "${CMAKE_BINARY_DIR}/Basilisk")
    set_target_properties(${LIB_NAME} PROPERTIES LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}/Basilisk")

    # Define the location for the executable part of the library (.dll) files (Windows Only)
    # https://cmake.org/cmake/help/v3.17/manual/cmake-buildsystem.7.html#output-artifacts for details
    set_target_properties(${LIB_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/Basilisk")
    set_target_properties(${LIB_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_BINARY_DIR}/Basilisk")
    set_target_properties(${LIB_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}/Basilisk")

    # Define the location of the import library file (.lib) needed for the .dll (Windows Only)
    set_target_properties(${LIB_NAME} PROPERTIES ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/Basilisk")
    set_target_properties(${LIB_NAME} PROPERTIES ARCHIVE_OUTPUT_DIRECTORY_DEBUG "${CMAKE_BINARY_DIR}/Basilisk")
    set_target_properties(${LIB_NAME} PROPERTIES ARCHIVE_OUTPUT_DIRECTORY_RELEASE "${CMAKE_BINARY_DIR}/Basilisk")
  endforeach()
  set(AllLibs
      ${AllLibs}
      PARENT_SCOPE)
endfunction(generate_package_libraries)

# Start of main projection configuration

include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/v1.17.0.zip
)
# For Windows: Prevent overriding the parent project's compiler/linker settings
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)
include(GoogleTest)
enable_testing()

# Function to check files
function(check_file url destination)
    get_filename_component(filename "${destination}" NAME)
    if(NOT EXISTS "${destination}")
        message(WARNING "file ${filename} not found at ${destination}, please download from ${url}")
    else()
        message(STATUS "file ${filename} exists.")
    endif()
endfunction()

# Define download URLs and target paths
set(SPICE_FILES
    "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de430.bsp::${CMAKE_SOURCE_DIR}/../supportData/EphemerisData/de430.bsp"
    "https://naif.jpl.nasa.gov/pub/naif/HST/kernels/spk/hst_edited.bsp::${CMAKE_SOURCE_DIR}/../supportData/EphemerisData/hst_edited.bsp"
    "https://naif.jpl.nasa.gov/pub/naif/pds/data/nh-j_p_ss-spice-6-v1.0/nhsp_1000/data/spk/nh_pred_od077.bsp::${CMAKE_SOURCE_DIR}/../supportData/EphemerisData/nh_pred_od077.bsp"
)
# Process each large data file
message(STATUS "checking large Basilisk data files")
foreach(spice_file IN LISTS SPICE_FILES)
    string(REPLACE "::" ";" spice_parts "${spice_file}")
    list(GET spice_parts 0 url)
    list(GET spice_parts 1 destination)
    check_file("${url}" "${destination}")
endforeach()

# Eigen 3.4 dependency
set(EIGEN3_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/dependencies/eigen3" CACHE PATH "Path to Eigen3 headers (folder that contains the 'Eigen' directory)")
if(NOT EIGEN3_INCLUDE_DIR)
  message(FATAL_ERROR "Please set EIGEN3_INCLUDE_DIR to the folder that contains the 'Eigen' headers (e.g. /.../include/eigen3)")
endif()

add_library(Eigen3::Eigen3 INTERFACE IMPORTED)
set_target_properties(Eigen3::Eigen3 PROPERTIES
  INTERFACE_INCLUDE_DIRECTORIES "${EIGEN3_INCLUDE_DIR}"
)
link_libraries(Eigen3::Eigen3)

# Add general compiler flags
set(CMAKE_MACOSX_RPATH 1)
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O2")

# Test Coverage
option(USE_COVERAGE "GCOV code coverage analysis" OFF)
if(USE_COVERAGE AND (CMAKE_COMPILER_IS_GNUC OR CMAKE_COMPILER_IS_GNUCXX))
  message(STATUS "USE_COVERAGE : ${USE_COVERAGE}")
  set(GCOV_CFLAGS "-fprofile-arcs -ftest-coverage -O0 -fno-default-inline -fno-inline")
  set(GCOV_LDFLAGS "-fprofile-arcs -ftest-coverage -O0 -fno-default-inline -fno-inline")

  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${GCOV_CFLAGS}")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${GCOV_CFLAGS}")
  set(CMAKE_LD_FLAGS "${CMAKE_LD_FLAGS} ${GCOV_LDFLAGS}")

  message(STATUS "CMAKE_C_FLAGS : ${CMAKE_C_FLAGS}")
  message(STATUS "CMAKE_CXX_FLAGS : ${CMAKE_CXX_FLAGS}")
  message(STATUS "CMAKE_LD_FLAGS : ${CMAKE_LD_FLAGS}")
endif()

# Add platform specific compiler flags
if(MSVC)
  set(CMAKE_CXX_STANDARD 17)
  add_definitions(/MP)
  add_definitions(/D _USE_MATH_DEFINES)
  add_definitions(/D _CRT_SECURE_NO_WARNINGS)
  add_definitions(/D _WINSOCK_DEPRECATED_NO_WARNINGS)
  add_definitions(/D _WIN32_WINNT=0x0501) # Targets Windows xp
  add_definitions(/W3)
  add_definitions(/wd"4913")
  add_definitions(/wd"4251")
  add_definitions(/wd"5208")
  add_definitions(/wd"4267")
  add_definitions(/wd"4244") # for closing conversion loss warning
  add_definitions(/bigobj)
  # Make sure we are using Multi-Threaded run time library
  foreach(flag CMAKE_C_FLAGS CMAKE_C_FLAGS_DEBUG CMAKE_C_FLAGS_RELEASE CMAKE_CXX_FLAGS CMAKE_CXX_FLAGS_DEBUG
               CMAKE_CXX_FLAGS_RELEASE)
    if (${CMAKE_BUILD_TYPE} STREQUAL "Debug")
      string(REPLACE "/D_DEBUG" "" "${flag}" "${${flag}}")
      string(REPLACE "/MDd" "${CONAN_LINK_RUNTIME_MULTI}" "${flag}" "${${flag}}")
      string(REPLACE "/MTd" "${CONAN_LINK_RUNTIME_MULTI}" "${flag}" "${${flag}}")
    else()
      string(REPLACE "/MD" "${CONAN_LINK_RUNTIME_MULTI}" "${flag}" "${${flag}}")
      string(REPLACE "/MT" "${CONAN_LINK_RUNTIME_MULTI}" "${flag}" "${${flag}}")
    endif()
    set("${flag}" "${${flag}} /EHsc")
  endforeach()
elseif(APPLE)
  set(CMAKE_CXX_STANDARD 17)
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -g -gdwarf-3")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g -gdwarf-3 -stdlib=libc++")
  set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g -gdwarf-3")
  set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE}  -Wall")
  set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG}  -Wall")
  if(${CMAKE_GENERATOR} MATCHES "Xcode")
    set(CMAKE_XCODE_GENERATE_SCHEME YES)
  endif()
else()
  set(CMAKE_CXX_STANDARD 17)
  set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -g -gdwarf-3")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g -gdwarf-3 -fPIC")
  set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g -gdwarf-3")
  set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE}  -Wall")
  set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG}  -Wall")
endif()

if(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-deprecated-register")
endif()

if(CMAKE_SIZEOF_VOID_P EQUAL 8)
  set(_arch_suffix 64)
else()
  set(_arch_suffix 32)
endif()

# TODO: Move the cspice library extension into a custom pyswice CMakeList.txt Manually create list of libraries
# depending on system
find_package(cspice REQUIRED CONFIG)
set(library_dependencies cspice::cspice)
if(WIN32)
  set(CMAKE_MSVCIDE_RUN_PATH "${CMAKE_BINARY_DIR}/Basilisk")
  set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS YES)
  # fix for opencv not finding conan gflags for opencv sfm lib on windows when the finding is fixed, the following line
  # should be removed https://github.com/conan-community/community/issues/210
  list(REMOVE_ITEM CONAN_LIBS opencv_sfm411d multiview)

elseif(APPLE)
  set(CMAKE_SKIP_BUILD_RPATH FALSE) # use, i.e. don't skip the full RPATH for the build tree
  set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE) # when building, don't use the install RPATH already (but later on when
                                           # installing)
  set(CMAKE_INSTALL_RPATH "${CMAKE_BINARY_DIR}/Basilisk"  # the RPATH to be used when installing
      # Also add relative paths so we can install from wheel/sdist.
      # TODO: Is there a proper way to set relative library paths without just
      # guessing how many parent ".." directories to use?
      "@loader_path"
      "@loader_path/.."
      "@loader_path/../.."
  )

  # don't add the automatically determined parts of the RPATH which point to directories outside the build tree to the
  # install RPATH
  set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
else()
  set(CMAKE_SKIP_BUILD_RPATH FALSE)
  set(CMAKE_INSTALL_RPATH "\$ORIGIN/../../")
endif()

set_property(GLOBAL PROPERTY BUILT_LIB_LIST "ArchitectureUtilities")
set_property(GLOBAL PROPERTY USE_FOLDERS ON)

# Targets that must be built first
add_subdirectory("architecture/utilities")
add_subdirectory("utilities") # has protobuffers included
add_subdirectory("architecture/messaging/cMsgCInterface")
add_subdirectory("architecture/messaging/")

# TODO: I'd call this generate_libraries(), because it really does find all of them. TODO: I'd like for all generated
# libraries to end up in a dist/Basilisk/lib folder rather than the /dist/Basilisk folder; however haven't found a way
# to use target_link_libraries() in a cross platform way to support this (needs full path and custom extensions
# --.dylib, .lib, .a, etc -- which gets messy in CMake).
set(AllLibs "")
generate_package_libraries("${CMAKE_SOURCE_DIR}" "${AllLibs}") # This finds GeneralModuleFiles and generates a library
                                                               # of the parentDirectory name

set(ARCHITECTURE_LIBS architectureLib ArchitectureUtilities ModuleIdGenerator cMsgCInterface)

# SIMULATION

if(NOT "${EXTERNAL_MODULES_PATH}" STREQUAL "")
  string(REPLACE "\\" "/" EXTERNAL_MODULES_PATH "${EXTERNAL_MODULES_PATH}")
  include_directories("${EXTERNAL_MODULES_PATH}")
  if(EXISTS "${EXTERNAL_MODULES_PATH}/ExternalModules/_GeneralModuleFiles")
    generate_package_libraries("${EXTERNAL_MODULES_PATH}" "${AllLibs}")
  endif()
endif(NOT "${EXTERNAL_MODULES_PATH}" STREQUAL "")

# MESSAGES

# add message headers
file(GLOB CMESSAGE_HEADER_FILES "${CMAKE_SOURCE_DIR}/architecture/msgPayloadDefC/*.h"
      "${EXTERNAL_MODULES_PATH}/msgPayloadDefC/*.h")
file(GLOB CPPMESSAGE_HEADER_FILES "${CMAKE_SOURCE_DIR}/architecture/msgPayloadDefCpp/*.h"
      "${EXTERNAL_MODULES_PATH}/msgPayloadDefCpp/*.h")
add_custom_target(msgPayloadDefC SOURCES ${CMESSAGE_HEADER_FILES})
add_custom_target(msgPayloadDefCpp SOURCES ${CPPMESSAGE_HEADER_FILES})
set_target_properties(msgPayloadDefC PROPERTIES FOLDER architecture)
set_target_properties(msgPayloadDefCpp PROPERTIES FOLDER architecture)

# copy into package the supportData files to keep
file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/Basilisk/supportData")
file(GLOB dataFiles "${CMAKE_SOURCE_DIR}/../supportData/*")
create_copies("${CMAKE_BINARY_DIR}/Basilisk/supportData" ${dataFiles})

# Tests targets
add_subdirectory("architecture/utilities/tests")

# INSTALL

install(TARGETS ${AllLibs} ${ARCHITECTURE_LIBS}
  RUNTIME DESTINATION bin
  LIBRARY DESTINATION bin
  ARCHIVE DESTINATION lib
)

install(DIRECTORY ${CMAKE_SOURCE_DIR}/
  DESTINATION include/Basilisk
  FILES_MATCHING
    PATTERN "*.h"

    # for long path constraint, documentations 
    # wont be copied to installations by cmake
    PATTERN "*_Documentation*" EXCLUDE

    PATTERN "cmake*" EXCLUDE
    PATTERN "dependencies*" EXCLUDE
    PATTERN "tests*" EXCLUDE
    PATTERN "topLevelModules*" EXCLUDE
    PATTERN "utilities*" EXCLUDE

    PATTERN "*_UnitTest*" EXCLUDE
    
    PATTERN "architecture/messaging/cMsgCInterface*" EXCLUDE
    PATTERN "architecture/messaging/cMsgCInterfacePy*" EXCLUDE
    PATTERN "architecture/messaging/msgAutoSource*" EXCLUDE

    PATTERN "architecture/utilitiesSelfCheck/swigEigenCheck*" EXCLUDE
)

install(DIRECTORY ${CMAKE_SOURCE_DIR}/../supportData/ DESTINATION share/Basilisk/supportData)