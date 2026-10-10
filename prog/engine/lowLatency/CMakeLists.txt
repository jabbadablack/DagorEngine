# Low latency mode (NVIDIA Reflex / AMD Anti-Lag) with its debug renderer, for the programs that set the
# DAGOR_LOW_LATENCY target property; a stub in the others (see dagor_add_link_choice())
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)
dagor_add_library(engine.lowLatency.framework
  SOURCES lowLatency.cpp latencyDebugRenderer.cpp PRIVATE_INCLUDES ${includes} DEPS engine/profilerTracker)
dagor_add_library(engine.lowLatency.stub SOURCES lowLatencyStub.cpp PRIVATE_INCLUDES ${includes} DEPS engine/profilerTracker)
dagor_add_link_choice(engine.lowLatency PROPERTY DAGOR_LOW_LATENCY
  ON engine.lowLatency.framework OFF engine.lowLatency.stub)
