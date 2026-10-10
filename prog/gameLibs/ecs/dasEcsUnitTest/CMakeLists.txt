# das_ecs_test: daECS + daScript; entity systems in tests/*.das react to EventStart/EventEnd broadcasts and record
# checks. The scripts are interpreted (the AOT build of this test belongs to the daScript AOT work of the game trees).
dagor_use(engine/memory:default.off engine/memory:default.dbg)
if(DAGOR_SANITIZE STREQUAL "none")
  set(memory "$<IF:$<CONFIG:Rel>,engine.memory.default.off,engine.memory.default.dbg>")
else()
  set(memory engine.memory.default.off)
endif()

dagor_add_executable(das_ecs_test CONSOLE STRICT QUIRREL
  SOURCES defaultFileAccess.cpp unitModule.cpp unit_test.cpp dasModules/stub/aotstub.cpp
  PRIVATE_INCLUDES
    .
    ${DAGOR_PROG_DIR}/engine/dagorInclude
    ${DAGOR_PROG_DIR}/gameLibs/publicInclude
    ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
  PRIVATE_DEFINES "DAS_ECS_TEST_ENGINE_ROOT=\"${DAGOR_ENGINE_ROOT}\""
  DEPS
    ${memory}
    engine/osApiWrappers
    engine/kernel
    engine/perfMon
    engine/math
    engine/baseUtil
    engine/ioSys
    engine/startup
    engine/workCycle
    engine/daECS/core
    engine/daECS/io/datablock
    engine/daECS/utility
    gameLibs/ecs/scripts/das
    gameLibs/dasModules/common
    engine/daECS/gameResStub
  PROPERTIES DAGOR_NO_GPU ON
)
dagor_add_exec_test(gameLibs.ecs.dasEcsUnitTest COMMAND $<TARGET_FILE:das_ecs_test> tests TAGS gameLibs ecs)
