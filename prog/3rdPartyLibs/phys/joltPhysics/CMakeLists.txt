# Jolt Physics (https://github.com/jrouwe/JoltPhysics.git, rev 7b9fbc356e83e3faaef36311f2d7fd6cc9720916)
if(NOT DAGOR_PLATFORM MATCHES "^(windows|linux|android|macOS|iOS|tvOS)$")
  message(FATAL_ERROR "Jolt: ${DAGOR_PLATFORM} is not supported")
endif()
set(dirs
  Jolt/AABBTree
  Jolt/Compute
  Jolt/Compute/CPU
  Jolt/Compute/DX12
  Jolt/Compute/VK
  Jolt/Core
  Jolt/Geometry
  Jolt/Math
  Jolt/ObjectStream
  Jolt/Physics
  Jolt/Physics/Body
  Jolt/Physics/Character
  Jolt/Physics/Collision
  Jolt/Physics/Collision/BroadPhase
  Jolt/Physics/Collision/Shape
  Jolt/Physics/Constraints
  Jolt/Physics/Hair
  Jolt/Physics/Ragdoll
  Jolt/Physics/SoftBody
  Jolt/Physics/Vehicle
  Jolt/Shaders
  Jolt/Skeleton
  Jolt/TriangleSplitter
)
set(sources Jolt/RegisterTypes.cpp)
dagor_glob_sources(sources DIRS ${dirs} GLOB *.cpp)
# the debug renderer where the settings enable it
dagor_glob_sources(renderer DIRS Jolt/Renderer GLOB *.cpp)
foreach(file IN LISTS renderer)
  list(APPEND sources "$<${DAGOR_JOLT_DEBUG}:${file}>")
endforeach()

set(defines)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND defines _CRT_SECURE_NO_WARNINGS _CRT_SECURE_NO_DEPRECATE _SCL_SECURE_NO_WARNINGS)
endif()
set(options)
if(DAGOR_CC STREQUAL "gcc")
  list(APPEND options -Wno-uninitialized) # on `index` in UnorderedMap.h
endif()
dagor_deterministic_fp(options)
set(source_options)
if(DAGOR_CC STREQUAL "msvc")
  list(APPEND source_options Jolt/Physics/Vehicle/MotorcycleController.cpp -wd4756) # overflow in constant arithmetic
  if(DAGOR_ARCH STREQUAL "arm64")
    list(APPEND source_options Jolt/Math/Vec3.cpp /Od) # for a correct Vec3::sUnitSphere
  endif()
endif()

dagor_add_library(SOURCES ${sources}
  PRIVATE_INCLUDES ${CMAKE_CURRENT_SOURCE_DIR}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  SOURCE_OPTIONS ${source_options}
  DEPS Dagor::JoltSettings
)
