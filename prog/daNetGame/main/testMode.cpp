// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include "main/testMode.h"
#include "main/gameLoad.h"
#include "main/level.h"
#include "main/main.h"
#include <daScript/daScript.h>
#include <debug/dag_logSys.h>
#include <ecs/scripts/dasEs.h>
#include <generic/dag_tab.h>
#include <ioSys/dag_findFiles.h>
#include <osApiWrappers/dag_basePath.h>
#include <osApiWrappers/dag_direct.h>
#include <osApiWrappers/dag_files.h>
#include <osApiWrappers/dag_miscApi.h>
#include <perfMon/dag_cpuFreq.h>
#include <startup/dag_globalSettings.h>
#include <unittest/dag_testEnv.h>
#include <util/dag_simpleString.h>
#include <util/dag_string.h>
#include <EASTL/algorithm.h>
#include <EASTL/vector.h>
#include <stdlib.h>

extern bool do_fatal_on_logerr_on_exit;

namespace test_mode
{
static constexpr int READY_FRAMES = 3; // let entities created by the scene finish their async creation
static constexpr const char *STARTUP_CASE = "<game startup>";

struct RegisteredTest
{
  das::Context *ctx;
  String name, wrapper, file;
  int line;
};

struct CaseResult
{
  String name;
  bool failed = false, failedNow = false, skipped = false;
  int64_t startTicks = 0;
  int usec = 0;
  Tab<String> messages;
  String location;
};

static bool active = false;
static bool running = false;
static bool done = false;
static int readyFrames = 0;
static float fixedDt = 0.f;
static Tab<String> testPaths;
static Tab<String> filters;
static String outDir;
static eastl::vector<RegisteredTest> tests;
static eastl::vector<CaseResult> results;
static eastl::vector<int> caseStack; // indices into results: top level case, then nested sub tests
static eastl::vector<int> openExpectations;
static debug_log_callback_t prevLogCallback = nullptr;

bool is_active() { return active; }
float fixed_dt() { return fixedDt; }
bool is_running_test() { return running; }

static CaseResult *current_case() { return caseStack.empty() ? nullptr : &results[caseStack.back()]; }

static int on_log(int lev_tag, const char *fmt, const void *arg, int anum, const char *ctx_file, int ctx_line)
{
  if (prevLogCallback)
    prevLogCallback(lev_tag, fmt, arg, anum, ctx_file, ctx_line);
  if (lev_tag > LOGLEVEL_ERR)
    return 1;
  String msg;
  if (ctx_file)
    msg.printf(0, "[E] %s,%d: ", ctx_file, ctx_line);
  else
    msg.printf(0, "[E] ");
  msg.avprintf(0, fmt, (const DagorSafeArg *)arg, anum);
  if (unittest::consume_expected_logerr(msg))
    return 1;
  // results are only touched on the main thread; errors of other threads are attributed when the case ends
  if (is_main_thread())
  {
    if (CaseResult *c = current_case())
    {
      c->failed = true;
      c->messages.push_back(msg);
      return 1;
    }
  }
  unittest::queue_unexpected_logerr(msg);
  return 1;
}

static void flush_queued_errors(CaseResult &c)
{
  String msg;
  while (unittest::pop_unexpected_logerr(msg))
  {
    c.failed = true;
    c.messages.push_back(String(0, "%s (outside the test thread)", msg.c_str()));
  }
}

static int push_case(const char *name)
{
  CaseResult c;
  c.name = name;
  c.startTicks = ref_time_ticks();
  results.push_back(eastl::move(c));
  caseStack.push_back(int(results.size() - 1));
  unittest::set_current_case(name);
  unittest::write_event(String(0, "\"event\":\"caseStarted\",\"case\":\"%s\"", unittest::json_escape(name).c_str()));
  unittest::watchdog_case_started();
  return caseStack.back();
}

static void pop_case()
{
  G_ASSERT_RETURN(!caseStack.empty(), );
  CaseResult &c = results[caseStack.back()];
  flush_queued_errors(c);
  c.usec = get_time_usec(c.startTicks);
  unittest::write_event(String(0, "\"event\":\"caseEnded\",\"case\":\"%s\",\"passed\":%s", unittest::json_escape(c.name).c_str(),
    c.failed ? "false" : "true"));
  caseStack.pop_back();
  unittest::set_current_case(caseStack.empty() ? nullptr : results[caseStack.back()].name.c_str());
  if (caseStack.empty())
  {
    unittest::watchdog_case_ended();
    for (int handle : openExpectations) // left open by a panic: must not swallow errors of the next tests
      unittest::pop_logerr_expectation(handle);
    openExpectations.clear();
  }
}

int push_logerr_expectation(const char *substr)
{
  const int handle = unittest::push_logerr_expectation(substr);
  openExpectations.push_back(handle);
  return handle;
}

int pop_logerr_expectation(int handle)
{
  openExpectations.erase(eastl::remove(openExpectations.begin(), openExpectations.end(), handle), openExpectations.end());
  return unittest::pop_logerr_expectation(handle);
}

void init()
{
  for (int it = 1; const char *p = dgs_get_argv("das_test", it);)
    testPaths.push_back(String(p));
  for (int it = 1; const char *f = dgs_get_argv("test_filter", it);)
    filters.push_back(String(f));
  if (testPaths.empty())
    return;
  active = true;
  outDir = dgs_get_argv("test_out") ? dgs_get_argv("test_out") : ".";
  const char *dt = dgs_get_argv("test_dt");
  fixedDt = dt ? (float)atof(dt) : 1.f / 60.f;
  if (fixedDt <= 0.f)
    fixedDt = 1.f / 60.f;

  ::dgs_execute_quiet = true;         // no message boxes in unattended runs
  do_fatal_on_logerr_on_exit = false; // errors are reported as test failures instead

  unittest::Options opt;
  opt.artifactDir = outDir;
  const char *timeout = dgs_get_argv("test_timeout");
  opt.caseTimeoutSec = timeout ? (float)atof(timeout) : 300.f;
  unittest::set_options(opt); // the watchdog starts with the tests: loading is bounded by the runner's own timeout

  prevLogCallback = debug_set_log_callback(&on_log);
  push_case(STARTUP_CASE); // errors until the tests start fail this pseudo case
  debug("test mode: %d test path(s), results in %s, fixed dt %g", testPaths.size(), outDir.c_str(), fixedDt);
}

static bool passes_filter(const char *name)
{
  if (filters.empty())
    return true;
  for (const String &f : filters)
    if (strncmp(name, f.c_str(), f.length()) == 0)
      return true;
  return false;
}

static void collect_test_files(Tab<String> &files)
{
  for (const String &p : testPaths)
  {
    String path;
    if (!dd_resolve_named_mount(path, p.c_str()))
      path = p;
    if (dd_dir_exists(path))
    {
      Tab<SimpleString> found;
      find_files_in_folder(found, path, ".das", /*vromfs*/ true, /*realfs*/ true, /*subdirs*/ true);
      eastl::sort(found.begin(), found.end(), [](const SimpleString &a, const SimpleString &b) { return strcmp(a, b) < 0; });
      for (const SimpleString &f : found)
        files.push_back(String(f.str()));
    }
    else
      files.push_back(path);
  }
}

void register_test(das::Context *ctx, const char *name, const char *wrapper, const char *file, int line)
{
  if (!running)
  {
    logerr("test registration outside of test loading: %s", name);
    return;
  }
  tests.push_back(RegisteredTest{ctx, String(name), String(wrapper), String(file), line});
}

void begin_case(const char *name)
{
  G_ASSERT_RETURN(running && is_main_thread(), );
  push_case(name);
}

void end_case() { pop_case(); }

void fail_case(bool now)
{
  if (CaseResult *c = current_case())
  {
    c->failed = true;
    c->failedNow = c->failedNow || now;
  }
}

void skip_case()
{
  if (CaseResult *c = current_case())
    c->skipped = true;
}

void log_case(const char *msg, const char *file, int line)
{
  if (CaseResult *c = current_case())
  {
    c->messages.push_back(String(0, "%s:%d: %s", file, line, msg));
    if (c->location.empty())
      c->location.printf(0, "%s:%d", file, line);
  }
}

void advance_frames(int count)
{
  G_ASSERT_RETURN(running && is_main_thread(), );
  // frame code sets up its own shared script stack and expects none to be active (see game_scene::update),
  // so the test's stack is hidden while frames run; it lives on the heap, untouched by their framemem resets
  das::StackAllocator *testStack = *das::SharedStackGuard::lastContextStack;
  *das::SharedStackGuard::lastContextStack = nullptr;
  for (int i = 0; i < count; ++i)
    run_main_loop_frame();
  *das::SharedStackGuard::lastContextStack = testStack;
}

// Test code runs whole frames (advance_frames), and every frame resets framemem, where script calls normally put their
// stack. So tests get a heap stack, which the script calls of those frames then share.
struct TestStackScope
{
  static constexpr uint32_t SIZE = 256 << 10;
  das::StackAllocator stack{SIZE};
  das::StackAllocator *saved = *das::SharedStackGuard::lastContextStack;
  TestStackScope() { *das::SharedStackGuard::lastContextStack = nullptr; }
  ~TestStackScope() { *das::SharedStackGuard::lastContextStack = saved; }
};

static void run_registered(const RegisteredTest &t)
{
  const int idx = push_case(t.name);
  das::SimFunction *fn = t.ctx->findFunction(t.wrapper.c_str());
  if (!fn)
  {
    results[idx].failed = true;
    results[idx].messages.push_back(String(0, "test wrapper %s is missing (was the file compiled by [ecs_test]?)", t.wrapper.c_str()));
  }
  else
  {
    {
      TestStackScope stackScope;
      das::SharedStackGuard guard(*t.ctx, stackScope.stack);
      t.ctx->evalWithCatch(fn, nullptr);
    }
    if (const char *ex = t.ctx->getException())
    {
      CaseResult &c = results[idx];
      if (!c.failed && !c.skipped) // reported already: failNow and skipNow panic on purpose, other panics are recovered in das
      {
        c.failed = true;
        c.messages.push_back(String(0, "%s:%d: %s",
          t.ctx->exceptionAt.fileInfo ? t.ctx->exceptionAt.fileInfo->name.c_str() : t.file.c_str(), t.ctx->exceptionAt.line, ex));
      }
      t.ctx->clearException();
    }
  }
  while (caseStack.size() > 1 || (caseStack.size() == 1 && caseStack.back() != idx)) // a sub test panicked out of its scope
    pop_case();
  pop_case();
}

static bool write_report(const char *path, int &out_failed, int &out_skipped, int total_usec)
{
  int passed = 0;
  out_failed = out_skipped = 0;
  String tests;
  for (const CaseResult &c : results)
  {
    if (c.failed)
      out_failed++;
    else if (c.skipped)
      out_skipped++;
    else
      passed++;
    String msgs;
    for (const String &m : c.messages)
      msgs.aprintf(0, "%s\"%s\"", msgs.empty() ? "" : ",", unittest::json_escape(m).c_str());
    tests.aprintf(0, "%s{\"name\":\"%s\",\"passed\":%s,\"skipped\":%s,\"time\":%d,\"messages\":[%s],\"location\":\"%s\"}",
      tests.empty() ? "" : ",", unittest::json_escape(c.name).c_str(), c.failed ? "false" : "true", c.skipped ? "true" : "false",
      c.usec, msgs.c_str(), unittest::json_escape(c.location).c_str());
  }
  // the same shape as dastest's JsonTestReport (prog/1stPartyLibs/daScript/dastest/dastest.das)
  String json(0,
    "{\"file\":\"\",\"total\":%d,\"passed\":%d,\"failed\":%d,\"errors\":0,\"skipped\":%d,\"success\":%s,\"time_usec\":%d,\"tests\":[%"
    "s]}",
    (int)results.size(), passed, out_failed, out_skipped, out_failed ? "false" : "true", total_usec, tests.c_str());
  dd_mkpath(path);
  file_ptr_t f = df_open(path, DF_WRITE | DF_CREATE);
  if (!f)
  {
    logerr("test mode: cannot write %s", path);
    return false;
  }
  df_write(f, json.data(), json.length());
  df_close(f);
  return true;
}

static int run_all()
{
  const int64_t startTicks = ref_time_ticks();
  unittest::start_watchdog();
  pop_case(); // <game startup>
  if (!results.back().failed)
    results.pop_back(); // a clean startup isn't worth a case

  Tab<String> files;
  collect_test_files(files);
  const bind_dascript::AotMode aotMode = bind_dascript::get_das_aot();
  bind_dascript::set_das_aot(bind_dascript::AotMode::NO_AOT); // tests are never AOT compiled
  for (const String &file : files)
  {
    // loading runs the [init] registration generated by [ecs_test]; compile errors are logged and fail this case
    const int idx = push_case(String(0, "<load %s>", file.c_str()));
    if (!bind_dascript::load_das_script(file))
      results[idx].failed = true;
    pop_case();
    if (!results[idx].failed)
      results.erase(results.begin() + idx);
  }
  bind_dascript::set_das_aot(aotMode);

  int selected = 0;
  for (const RegisteredTest &t : tests)
    if (passes_filter(t.name))
    {
      selected++;
      run_registered(t);
    }

  int failed = 0, skipped = 0;
  const String reportPath(0, "%s/dastest.json", unittest::options().artifactDir.c_str());
  if (!write_report(reportPath, failed, skipped, get_time_usec(startTicks)))
    return unittest::EXIT_INFRA_ERROR;
  debug("test mode: %d tests registered, %d run, %d failed, %d skipped; report %s", (int)tests.size(), selected, failed, skipped,
    reportPath.c_str());
  if (failed)
    return unittest::EXIT_FAILED;
  if (selected == 0 || skipped == selected)
    return unittest::EXIT_SKIPPED;
  return unittest::EXIT_PASSED;
}

void update()
{
  if (!active || running || done)
    return;
  if (!is_initial_loading_complete() || is_level_loading() || sceneload::is_scene_switch_in_progress())
    return;
  if (++readyFrames < READY_FRAMES)
    return;
  running = true;
  const int code = run_all();
  running = false;
  done = true;
  unittest::stop_watchdog();
  debug_set_log_callback(prevLogCallback);
  exit_game("tests finished", code);
}
} // namespace test_mode
