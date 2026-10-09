// Dagor Engine 6.5
// Copyright (C) Gaijin Games KFT.  All rights reserved.

#pragma once

// Copyright (C) Gaijin Games KFT.  All rights reserved.

// ===============================================================================
//
// main() for Catch2 unit test executables (build them with prog/_jBuild/unitTest.jam).
//
// Optional configuration, defined before including this file:
//   UNITTEST_ENV               - engine subsystems to bring up around the test run, a combination of
//                                UNITTEST_ENV_SETTINGS (settings.blk), UNITTEST_ENV_CPUJOBS (cpujobs) and
//                                UNITTEST_ENV_GPU (3d driver and video, implies the previous two)
//   UNITTEST_SETTINGS_BLK      - settings file relative to the data dir, "settings.blk" by default
//   UNITTEST_APP_NAME          - window class/title for UNITTEST_ENV_GPU
//   CUSTOM_UNITTEST_CODE       - code run before the test session (argc, argv are available)
//   CUSTOM_UNITTEST_SHUTDOWN_CODE - code run after the test session
//
// Command line options added to the Catch2 ones:
//   --data-dir <dir>           test data dir (default: the test's source dir)
//   --artifact-dir <dir>       where images and events.jsonl are written (default: none)
//   --case-timeout <sec>       kill the process when a single test case runs longer (default: off)
//   --image-variant <name>     reference image variant, e.g. a driver name (default: the 3d driver name with UNITTEST_ENV_GPU)
//   --gpu-driver <name>        overrides video/driver from settings with UNITTEST_ENV_GPU, e.g. stub
//   --update-references        replace mismatching or missing reference images with the actual ones
//
// Any error logged inside a test case fails it unless expected with unittest::ExpectLogerr/CaptureLogerr.
// Exit codes follow unittest::ExitCode.
//
// ===============================================================================

#define UNITTEST_ENV_SETTINGS 1
#define UNITTEST_ENV_CPUJOBS  2
#define UNITTEST_ENV_GPU      4

#ifndef UNITTEST_ENV
#define UNITTEST_ENV 0
#endif
#ifndef UNITTEST_SETTINGS_BLK
#define UNITTEST_SETTINGS_BLK "settings.blk"
#endif
#ifndef UNITTEST_APP_NAME
#define UNITTEST_APP_NAME "unitTest"
#endif
#ifndef UNITTEST_DEFAULT_DATA_DIR
#define UNITTEST_DEFAULT_DATA_DIR "."
#endif

#if _TARGET_PC_WIN
#include <windows.h>
#include <crtdbg.h>
#include <stdlib.h>
#endif

#include <unittest/catch2_reporter_detailed.h>
#include <unittest/dag_unitTest.h>

#include <debug/dag_fatal.h>
#include <debug/dag_logSys.h>
#include <osApiWrappers/dag_atomic.h>
#include <osApiWrappers/dag_miscApi.h>
#include <osApiWrappers/dag_symHlp.h>
#include <startup/dag_globalSettings.h>
#include <util/dag_globDef.h>
#include <util/dag_string.h>

#if UNITTEST_ENV != 0
#include <ioSys/dag_dataBlock.h>
#include <osApiWrappers/dag_dbgStr.h>
#include <startup/dag_loadSettings.h>
#endif
#if UNITTEST_ENV & (UNITTEST_ENV_CPUJOBS | UNITTEST_ENV_GPU)
#include <osApiWrappers/dag_cpuJobs.h>
#endif
#if UNITTEST_ENV & UNITTEST_ENV_GPU
#include <drv/3d/dag_driver.h>
#include <drv/3d/dag_info.h>
#include <startup/dag_addBasePathDef.h>
#include <startup/dag_restart.h>
#include <workCycle/dag_startupModules.h>
#endif

#ifdef USE_EASTL
#include <EASTL/internal/config.h>
#endif

#include <catch2/catch_session.hpp>
#include <catch2/catch_test_case_info.hpp>
#include <catch2/internal/catch_compiler_capabilities.hpp>
#include <catch2/internal/catch_config_wchar.hpp>
#include <catch2/internal/catch_enforce.hpp>
#include <catch2/internal/catch_leak_detector.hpp>
#include <catch2/internal/catch_platform.hpp>
#include <catch2/internal/catch_reporter_spec_parser.hpp>
#include <catch2/reporters/catch_reporter_event_listener.hpp>
#include <catch2/reporters/catch_reporter_registrars.hpp>

#include <stdio.h>

// ===============================================================================

CATCH_REGISTER_REPORTER("detailed", Catch::gaijin_reporters::DetailedConsoleReporter)

// ===============================================================================

namespace Catch
{
CATCH_INTERNAL_START_WARNINGS_SUPPRESSION
CATCH_INTERNAL_SUPPRESS_GLOBALS_WARNINGS
static LeakDetector leakDetector;
CATCH_INTERNAL_STOP_WARNINGS_SUPPRESSION
} // namespace Catch

// ===============================================================================

static volatile int unittest_in_case = 0;
static int unittest_late_failures = 0;
static int unittest_infra_errors = 0;
static bool unittest_env_starting = false;

static void unittest_report_outside_case(const char *kind, const char *msg)
{
  fprintf(stderr, "unittest: %s: %s\n", kind, msg);
  fflush(stderr);
  unittest::write_event(String(0, "\"event\":\"infraError\",\"case\":\"%s\",\"message\":\"%s\"",
    unittest::json_escape(unittest::current_case()).c_str(), unittest::json_escape(msg).c_str()));
}

static bool fatal_handler(const char *msg, const char *call_stack, const char *origin_file, int origin_line)
{
  String text(0, "%s(%d): Fatal handler error: %s; callstack: %s", origin_file, origin_line, msg,
    call_stack ? call_stack : "<no_callstack>");
  if (unittest_env_starting)
  {
    unittest_report_outside_case("test environment is unavailable", text);
    _exit(unittest::EXIT_SKIPPED);
  }
  if (!is_main_thread() || !interlocked_acquire_load(unittest_in_case))
  {
    unittest_report_outside_case("fatal error", text);
    _exit(unittest::EXIT_FAILED);
  }
  FAIL(text.c_str());
  return false;
}

static bool assertion_handler(bool /*verify*/, const char *file, int line, const char *func, const char *cond, const char *fmt,
  const DagorSafeArg *args, int anum)
{
  String text(0, "%s(%d): Dagor assertion \"%s\" failed", file, line, cond);
  if (fmt)
  {
    text.append(" with message:\n");
    text.avprintf(0, fmt, args, anum);
  }
  text.aprintf(0, "; function: %s", func ? func : "<no_func>");
  if (!is_main_thread() || !interlocked_acquire_load(unittest_in_case))
    unittest::queue_unexpected_logerr(text);
  else
    FAIL(text.c_str());
  return false;
}

#if defined(USE_EASTL) && EASTL_ASSERT_ENABLED
static void eastl_assertion_failure_function(const char *expr, void * /*ctx*/)
{
  if (!is_main_thread() || !interlocked_acquire_load(unittest_in_case))
    unittest::queue_unexpected_logerr(String(0, "EASTL Assertion: %s", expr));
  else
    FAIL("EASTL Assertion: " << expr);
}
#endif

// Errors fail the current test case unless expected. Errors from other threads cannot be reported to Catch2 directly
// (its assertions aren't thread-safe), so they are queued and reported when the case ends.
static debug_log_callback_t unittest_prev_log_callback = nullptr;
static int unittest_log_callback(int lev_tag, const char *fmt, const void *arg, int anum, const char *ctx_file, int ctx_line)
{
  static const int D3DE_TAG = _MAKE4C('D3DE');
  if (unittest_prev_log_callback)
    unittest_prev_log_callback(lev_tag, fmt, arg, anum, ctx_file, ctx_line);
  if (lev_tag > LOGLEVEL_ERR && lev_tag != D3DE_TAG)
    return 1;

  String msg;
  if (ctx_file)
    msg.printf(0, "[E] %s,%d: ", ctx_file, ctx_line);
  else
    msg.printf(0, "[E] ");
  msg.avprintf(0, fmt, (const DagorSafeArg *)arg, anum);

  if (unittest::consume_expected_logerr(msg))
    return 1;
  if (is_main_thread() && interlocked_acquire_load(unittest_in_case))
    FAIL_CHECK(msg.c_str());
  else
    unittest::queue_unexpected_logerr(msg);
  return 1;
}

static void unittest_flush_unexpected_logerrs()
{
  String msg;
  while (unittest::pop_unexpected_logerr(msg))
  {
    const char *caseName = unittest::current_case();
    if (*caseName)
    {
      fprintf(stderr, "unittest: FAILED (error outside the test thread) in \"%s\": %s\n", caseName, msg.c_str());
      unittest::write_event(String(0, "\"event\":\"failure\",\"case\":\"%s\",\"message\":\"%s\"",
        unittest::json_escape(caseName).c_str(), unittest::json_escape(msg).c_str()));
      unittest_late_failures++;
    }
    else
    {
      unittest_report_outside_case("error outside of test cases", msg);
      unittest_infra_errors++;
    }
  }
  fflush(stderr);
}

class DagorTestListener final : public Catch::EventListenerBase
{
public:
  using EventListenerBase::EventListenerBase;

  void testCaseStarting(const Catch::TestCaseInfo &info) override
  {
    unittest_flush_unexpected_logerrs(); // anything queued between cases belongs to no case
    unittest::set_current_case(info.name.c_str());
    unittest::write_event(String(0, "\"event\":\"caseStarted\",\"case\":\"%s\"", unittest::json_escape(info.name.c_str()).c_str()));
    unittest::watchdog_case_started();
    interlocked_release_store(unittest_in_case, 1);
  }

  void testCaseEnded(const Catch::TestCaseStats &stats) override
  {
    interlocked_release_store(unittest_in_case, 0);
    unittest::watchdog_case_ended();
    const int lateBefore = unittest_late_failures;
    unittest_flush_unexpected_logerrs();
    const bool passed = stats.totals.assertions.allOk() && lateBefore == unittest_late_failures;
    unittest::write_event(String(0, "\"event\":\"caseEnded\",\"case\":\"%s\",\"passed\":%s",
      unittest::json_escape(stats.testInfo->name.c_str()).c_str(), passed ? "true" : "false"));
    unittest::set_current_case(nullptr);
  }
};

CATCH_REGISTER_LISTENER(DagorTestListener)

// ===============================================================================

static void set_default_reporter(Catch::ConfigData &config_data, const std::string &default_reporter_spec)
{
  // Exactly the same logic as in `Config::Config( ConfigData const& data )` (catch_config.cpp)
  if (config_data.reporterSpecifications.empty())
  {
    auto parsed = Catch::parseReporterSpec(default_reporter_spec);
    CATCH_ENFORCE(parsed, "Cannot parse the provided default reporter spec: '" << default_reporter_spec << '\'');
    config_data.reporterSpecifications.push_back(eastl::move(*parsed));
  }
}

static int unittest_exit_code(int catch_code)
{
  switch (catch_code)
  {
    case 0: return unittest::EXIT_PASSED;
    case 4: return unittest::EXIT_SKIPPED; // Catch2 AllTestsSkippedExitCode
    case 42: return unittest::EXIT_FAILED; // Catch2 TestFailureExitCode
    default: return unittest::EXIT_INFRA_ERROR;
  }
}

static void unittest_disable_crash_dialogs()
{
#if _TARGET_PC_WIN
  if (IsDebuggerPresent())
    return;
  // report crashes and CRT asserts to stderr instead of blocking unattended runs with modal dialogs
  SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX);
  _set_abort_behavior(0, _WRITE_ABORT_MSG | _CALL_REPORTFAULT);
  for (int type : {_CRT_WARN, _CRT_ERROR, _CRT_ASSERT})
  {
    G_UNUSED(type); // the _Crt* macros compile to nothing with the release CRT
    _CrtSetReportMode(type, _CRTDBG_MODE_FILE);
    _CrtSetReportFile(type, _CRTDBG_FILE_STDERR);
  }
#endif
}

#if UNITTEST_ENV != 0
static void unittest_env_startup(int argc, char *argv[], const char *gpu_driver)
{
  unittest_env_starting = true;
#if UNITTEST_ENV & (UNITTEST_ENV_SETTINGS | UNITTEST_ENV_GPU)
  dgs_init_argv(argc, argv);
  // intentionally never freed: engine globals may still reference settings at exit
  static DagorSettingsBlkHolder *settingsHolder = new DagorSettingsBlkHolder;
  G_UNUSED(settingsHolder);
  dgs_load_settings_blk(false, unittest::data_path(UNITTEST_SETTINGS_BLK));
#endif
#if UNITTEST_ENV & (UNITTEST_ENV_CPUJOBS | UNITTEST_ENV_GPU)
  cpujobs::init();
#endif
#if UNITTEST_ENV & UNITTEST_ENV_GPU
#if _TARGET_PC_WIN
  set_debug_console_handle((intptr_t)::GetStdHandle(STD_OUTPUT_HANDLE));
#else
  set_debug_console_handle((intptr_t)stdout);
#endif
  dagor_init_base_path();
  if (*gpu_driver)
    const_cast<DataBlock *>(::dgs_get_settings())->addBlock("video")->setStr("driver", gpu_driver);
  if (!d3d::init_driver())
  {
    unittest_report_outside_case("test environment is unavailable", "d3d::init_driver() failed");
    _exit(unittest::EXIT_SKIPPED);
  }
  ::dagor_init_video(UNITTEST_APP_NAME, 0, nullptr, "");
  ::startup_game(RESTART_ALL);
  if (unittest::options().imageVariant.empty())
    unittest::options().imageVariant = d3d::get_driver_name();
#else
  G_UNUSED(gpu_driver);
#endif
  G_UNUSED(argc);
  G_UNUSED(argv);
  unittest_env_starting = false;
}

static void unittest_env_shutdown()
{
#if UNITTEST_ENV & UNITTEST_ENV_GPU
  d3d::release_driver();
#endif
#if UNITTEST_ENV & (UNITTEST_ENV_CPUJOBS | UNITTEST_ENV_GPU)
  cpujobs::term(true, 1000);
#endif
}
#endif

// ===============================================================================

#include <supp/dag_define_KRNLIMP.h>
extern KRNLIMP void init_main_thread_id();
#include <supp/dag_undef_KRNLIMP.h>

int main(int argc, char *argv[])
{
  ::init_main_thread_id();
  ::symhlp_init_default();
  unittest_disable_crash_dialogs();
  ::dgs_fatal_handler = fatal_handler;
  ::dgs_assertion_handler = assertion_handler;
#if defined(USE_EASTL) && EASTL_ASSERT_ENABLED
  eastl::SetAssertionFailureFunction(&eastl_assertion_failure_function, NULL);
#endif

#ifdef CUSTOM_UNITTEST_CODE
  CUSTOM_UNITTEST_CODE
#endif

  {
    // We want to force the linker not to discard the global variable
    // and its constructor, as it (optionally) registers leak detector
    (void)&Catch::leakDetector;
  }

  Catch::Session session;

  std::string dataDir = UNITTEST_DEFAULT_DATA_DIR, artifactDir, imageVariant, gpuDriver;
  double caseTimeout = 0;
  bool updateReferences = false;
  using Catch::Clara::Opt;
  session.cli(session.cli() | Opt(dataDir, "dir")["--data-dir"]("test data dir") |
              Opt(artifactDir, "dir")["--artifact-dir"]("dir for test artifacts and events.jsonl") |
              Opt(caseTimeout, "seconds")["--case-timeout"]("abort when a test case runs longer") |
              Opt(imageVariant, "name")["--image-variant"]("reference image variant") |
              Opt(gpuDriver, "name")["--gpu-driver"]("3d driver override") |
              Opt(updateReferences)["--update-references"]("replace mismatching reference images"));

  int returnCode = session.applyCommandLine(argc, argv);
  if (returnCode != 0)
    return unittest::EXIT_INFRA_ERROR;

  unittest::Options opt;
  opt.dataDir = dataDir.c_str();
  opt.artifactDir = artifactDir.c_str();
  opt.imageVariant = imageVariant.c_str();
  opt.caseTimeoutSec = float(caseTimeout);
  opt.updateReferences = updateReferences;
  unittest::set_options(opt);

  unittest_prev_log_callback = debug_set_log_callback(&unittest_log_callback);
#if UNITTEST_ENV != 0
  unittest_env_startup(argc, argv, gpuDriver.c_str());
#else
  G_UNUSED(gpuDriver);
#endif
  unittest_flush_unexpected_logerrs();

  unittest::start_watchdog();
  set_default_reporter(session.configData(), "detailed");
  returnCode = unittest_exit_code(session.run());
  unittest::stop_watchdog();

#if UNITTEST_ENV != 0
  unittest_env_shutdown();
#endif

#ifdef CUSTOM_UNITTEST_SHUTDOWN_CODE
  CUSTOM_UNITTEST_SHUTDOWN_CODE
#endif

  unittest_flush_unexpected_logerrs();
  if (returnCode == unittest::EXIT_PASSED && unittest_late_failures)
    returnCode = unittest::EXIT_FAILED;
  if (returnCode == unittest::EXIT_PASSED && unittest_infra_errors)
    returnCode = unittest::EXIT_INFRA_ERROR;
  return returnCode;
}

// ===============================================================================
