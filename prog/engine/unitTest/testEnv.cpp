// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include <unittest/dag_testEnv.h>
#include <osApiWrappers/dag_atomic.h>
#include <osApiWrappers/dag_critSec.h>
#include <osApiWrappers/dag_direct.h>
#include <osApiWrappers/dag_directUtils.h>
#include <osApiWrappers/dag_files.h>
#include <osApiWrappers/dag_miscApi.h>
#include <osApiWrappers/dag_threads.h>
#include <perfMon/dag_cpuFreq.h>
#include <EASTL/vector.h>
#include <stdio.h>
#include <stdlib.h>
#if _TARGET_PC_WIN
#include <direct.h>
#include <process.h>
#else
#include <unistd.h>
#endif

namespace unittest
{
// constructed on first use: a String takes strmem when it is constructed, and on macOS (Mach-O has no init_priority)
// static constructors of this lib may run before the memory manager sets strmem
static Options &options_storage()
{
  static Options opt;
  return opt;
}
static String &current_case_storage()
{
  static String name;
  return name;
}
static WinCritSec g_events_cs;
static file_ptr_t g_events_file = nullptr;

Options &options() { return options_storage(); }

static String make_absolute(const String &path)
{
  if (path.empty() || path[0] == '/' || path[0] == '\\' || (path.length() > 1 && path[1] == ':'))
    return path;
  char cwd[DAGOR_MAX_PATH];
#if _TARGET_PC_WIN
  if (!_getcwd(cwd, sizeof(cwd)))
#else
  if (!getcwd(cwd, sizeof(cwd)))
#endif
    return path;
  String abs(0, "%s/%s", cwd, path.c_str());
  dd_simplify_fname_c(abs.data());
  abs.updateSz();
  return abs;
}

void set_options(const Options &opt)
{
  options_storage() = opt;
  options_storage().dataDir = make_absolute(opt.dataDir);
  options_storage().artifactDir = make_absolute(opt.artifactDir);
}

static String join_path(const String &dir, const char *rel)
{
  if (dir.empty())
    return String(rel);
  String path(0, "%s/%s", dir.c_str(), rel);
  dd_simplify_fname_c(path.data());
  path.updateSz();
  return path;
}

// Case names may contain any character; keep the directory name portable.
static String case_dir_name(const char *case_name)
{
  String dir(case_name && *case_name ? case_name : "_global");
  for (char &c : dir)
    if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '-' || c == '_' || c == '.'))
      c = '_';
  return dir;
}

String data_path(const char *rel) { return join_path(options_storage().dataDir, rel); }

String artifact_path(const char *rel)
{
  if (options_storage().artifactDir.empty())
    return String();
  String path = join_path(options_storage().artifactDir, String(0, "%s/%s", case_dir_name(current_case_storage()).c_str(), rel).c_str());
  dd_mkpath(path);
  return path;
}

static String temp_root()
{
#if _TARGET_PC_WIN
  const char *tmp = getenv("TEMP");
  if (!tmp || !*tmp)
    tmp = getenv("TMP");
#else
  const char *tmp = getenv("TMPDIR");
#endif
#if _TARGET_PC_WIN
  String root(0, "%s/dagor_unittest_%d", tmp && *tmp ? tmp : ".", _getpid());
#else
  String root(0, "%s/dagor_unittest_%d", tmp && *tmp ? tmp : "/tmp", getpid());
#endif
  dd_simplify_fname_c(root.data());
  root.updateSz();
  return root;
}

String scratch_dir()
{
  const String base = options_storage().artifactDir.empty() ? temp_root() : options_storage().artifactDir;
  String dir(0, "%s/%s/scratch", base.c_str(), case_dir_name(current_case_storage()).c_str());
  dag::remove_dirtree(dir);
  dd_mkdir(dir);
  return dir;
}

bool http_service(String &out_base_url, String &out_root_dir)
{
  const char *url = getenv("DAGOR_TEST_HTTP_URL");
  const char *root = getenv("DAGOR_TEST_HTTP_ROOT");
  if (!url || !*url || !root || !*root)
    return false;
  out_base_url = url;
  if (out_base_url[out_base_url.length() - 1] != '/')
    out_base_url += "/";
  out_root_dir = root;
  return true;
}

void set_current_case(const char *case_name)
{
  WinAutoLock lock(g_events_cs); // the watchdog reads the name from its own thread
  current_case_storage() = case_name ? case_name : "";
}
const char *current_case() { return current_case_storage().c_str(); }

String json_escape(const char *s)
{
  String out;
  for (; s && *s; s++)
  {
    const unsigned char c = (unsigned char)*s;
    if (c == '"' || c == '\\')
      out.aprintf(0, "\\%c", c);
    else if (c == '\n')
      out += "\\n";
    else if (c == '\r')
      out += "\\r";
    else if (c == '\t')
      out += "\\t";
    else if (c < 0x20)
      out.aprintf(0, "\\u%04x", c);
    else
      out += char(c);
  }
  return out;
}

void write_event(const char *fields_json)
{
  if (options_storage().artifactDir.empty())
    return;
  WinAutoLock lock(g_events_cs);
  if (!g_events_file)
  {
    String fn = join_path(options_storage().artifactDir, "events.jsonl");
    dd_mkpath(fn);
    g_events_file = df_open(fn, DF_WRITE | DF_APPEND);
    if (!g_events_file)
    {
      fprintf(stderr, "unittest: cannot open %s for writing\n", fn.c_str());
      return;
    }
  }
  df_cprintf(g_events_file, "{%s}\n", fields_json);
  df_flush(g_events_file);
}


// ---- watchdog ----

static volatile int g_case_start_msec = 0;
static volatile int g_case_running = 0;

class WatchdogThread final : public DaThread
{
public:
  WatchdogThread() : DaThread("unittestWatchdog") {}

  void execute() override
  {
    const int timeoutMsec = int(options_storage().caseTimeoutSec * 1000);
    while (!isThreadTerminating())
    {
      sleep_msec(50);
      if (!interlocked_acquire_load(g_case_running))
        continue;
      if (get_time_msec() - interlocked_acquire_load(g_case_start_msec) < timeoutMsec)
        continue;
      String caseName;
      {
        WinAutoLock lock(g_events_cs); // the main thread may be updating the name; take a stable copy
        caseName = current_case_storage();
      }
      fprintf(stderr, "\nunittest: TIMEOUT: test case \"%s\" exceeded %.1f s\n", caseName.c_str(), options_storage().caseTimeoutSec);
      fflush(stderr);
      fflush(stdout);
      write_event(
        String(0, "\"event\":\"timeout\",\"case\":\"%s\",\"timeoutSec\":%g", json_escape(caseName).c_str(), options_storage().caseTimeoutSec));
      _exit(EXIT_TIMEOUT);
    }
  }
};

static WatchdogThread *g_watchdog = nullptr;

void start_watchdog()
{
  if (g_watchdog || options_storage().caseTimeoutSec <= 0)
    return;
  g_watchdog = new WatchdogThread;
  g_watchdog->start();
}

void stop_watchdog()
{
  if (!g_watchdog)
    return;
  g_watchdog->terminate(true);
  g_watchdog->destroy();
  g_watchdog = nullptr;
}

void watchdog_case_started()
{
  interlocked_release_store(g_case_start_msec, get_time_msec());
  interlocked_release_store(g_case_running, 1);
}

void watchdog_case_ended() { interlocked_release_store(g_case_running, 0); }


// ---- logerr expectations ----

struct LogerrExpectation
{
  int handle;
  String substr;
  String *capture;
  int consumed;
};

static WinCritSec g_logerr_cs;
static eastl::vector<LogerrExpectation> g_expectations;
static eastl::vector<String> g_unexpected;
static int g_next_handle = 1;

int push_logerr_expectation(const char *substr, String *capture)
{
  WinAutoLock lock(g_logerr_cs);
  g_expectations.push_back(LogerrExpectation{g_next_handle, String(substr), capture, 0});
  return g_next_handle++;
}

int pop_logerr_expectation(int handle)
{
  WinAutoLock lock(g_logerr_cs);
  for (auto it = g_expectations.begin(); it != g_expectations.end(); ++it)
    if (it->handle == handle)
    {
      const int consumed = it->consumed;
      g_expectations.erase(it);
      return consumed;
    }
  return 0;
}

bool consume_expected_logerr(const char *msg)
{
  WinAutoLock lock(g_logerr_cs);
  for (auto it = g_expectations.rbegin(); it != g_expectations.rend(); ++it) // innermost expectation first
    if (strstr(msg, it->substr.c_str()))
    {
      it->consumed++;
      if (it->capture)
        it->capture->aprintf(0, "%s\n", msg);
      return true;
    }
  return false;
}

void queue_unexpected_logerr(const char *msg)
{
  WinAutoLock lock(g_logerr_cs);
  g_unexpected.push_back(String(msg));
}

bool pop_unexpected_logerr(String &out_msg)
{
  WinAutoLock lock(g_logerr_cs);
  if (g_unexpected.empty())
    return false;
  out_msg = eastl::move(g_unexpected.front());
  g_unexpected.erase(g_unexpected.begin());
  return true;
}
} // namespace unittest
