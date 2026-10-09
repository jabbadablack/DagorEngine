// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include "dasModules/testMode.h"

namespace bind_dascript
{
// Test mode of the game, see main/testMode.h; used by the [ecs_test] machinery of prog/daNetGameLibs/test_harness
class DngTestModeModule final : public das::Module
{
public:
  DngTestModeModule() : das::Module("DngTestMode")
  {
    das::ModuleLibrary lib(this);

    das::addExtern<DAS_BIND_FUN(test_mode::is_active)>(*this, lib, "is_test_mode", das::SideEffects::accessExternal,
      "test_mode::is_active");
    das::addExtern<DAS_BIND_FUN(test_mode::is_running_test)>(*this, lib, "is_running_test", das::SideEffects::accessExternal,
      "test_mode::is_running_test");
    das::addExtern<DAS_BIND_FUN(test_mode::fixed_dt)>(*this, lib, "test_mode_fixed_dt", das::SideEffects::accessExternal,
      "test_mode::fixed_dt");
    das::addExtern<DAS_BIND_FUN(test_mode::advance_frames)>(*this, lib, "advance_frames", das::SideEffects::modifyExternal,
      "test_mode::advance_frames");

    das::addExtern<DAS_BIND_FUN(bind_dascript::test_mode_register)>(*this, lib, "test_mode_register", das::SideEffects::modifyExternal,
      "bind_dascript::test_mode_register");
    das::addExtern<DAS_BIND_FUN(bind_dascript::test_mode_begin_case)>(*this, lib, "test_mode_begin_case",
      das::SideEffects::modifyExternal, "bind_dascript::test_mode_begin_case");
    das::addExtern<DAS_BIND_FUN(test_mode::end_case)>(*this, lib, "test_mode_end_case", das::SideEffects::modifyExternal,
      "test_mode::end_case");
    das::addExtern<DAS_BIND_FUN(test_mode::fail_case)>(*this, lib, "test_mode_fail", das::SideEffects::modifyExternal,
      "test_mode::fail_case");
    das::addExtern<DAS_BIND_FUN(test_mode::skip_case)>(*this, lib, "test_mode_skip", das::SideEffects::modifyExternal,
      "test_mode::skip_case");
    das::addExtern<DAS_BIND_FUN(bind_dascript::test_mode_log)>(*this, lib, "test_mode_log", das::SideEffects::modifyExternal,
      "bind_dascript::test_mode_log");

    das::addExtern<DAS_BIND_FUN(bind_dascript::test_mode_push_logerr_expectation)>(*this, lib, "test_mode_push_logerr_expectation",
      das::SideEffects::modifyExternal, "bind_dascript::test_mode_push_logerr_expectation");
    das::addExtern<DAS_BIND_FUN(test_mode::pop_logerr_expectation)>(*this, lib, "test_mode_pop_logerr_expectation",
      das::SideEffects::modifyExternal, "test_mode::pop_logerr_expectation");

    verifyAotReady();
  }
  das::ModuleAotType aotRequire(das::TextWriter &tw) const override
  {
    tw << "#include \"dasModules/testMode.h\"\n";
    return das::ModuleAotType::cpp;
  }
};
} // namespace bind_dascript
REGISTER_MODULE_IN_NAMESPACE(DngTestModeModule, bind_dascript);
