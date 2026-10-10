# GPU objects: the GPU placement of small objects on surfaces (rendinst decorations), with the volume placer ES
dagor_add_library(STRICT
  SOURCES gpuObjects.cpp
  ES_SOURCES volumePlacerES.cpp.inl
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR}
)
