# cspiceConfig.cmake

add_library(cspice::cspice STATIC IMPORTED)

# 头文件路径
set_target_properties(cspice::cspice PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${CMAKE_CURRENT_LIST_DIR}/../../../include"
    IMPORTED_LOCATION "${CMAKE_CURRENT_LIST_DIR}/../../../lib/cspice.lib"
)

# 注意：Basilisk 实际上还会用到 csupport.lib
# 你可以直接把它链到同一个 target 上：
set_property(TARGET cspice::cspice APPEND PROPERTY
    INTERFACE_LINK_LIBRARIES "${CMAKE_CURRENT_LIST_DIR}/../../../lib/csupport.lib"
)
