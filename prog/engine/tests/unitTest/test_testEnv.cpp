// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include <unittest/dag_unitTest.h>
#include <debug/dag_debug.h>
#include <debug/dag_assert.h>
#include <osApiWrappers/dag_direct.h>
#include <osApiWrappers/dag_files.h>

TEST_CASE("expected errors do not fail the test", "[testEnv][logerr]")
{
  unittest::ExpectLogerr expect("expected failure", 2);
  logerr("an expected failure #%d", 1);
  logerr("another expected failure #%d", 2);
}

TEST_CASE("nested expectations consume the innermost match first", "[testEnv][logerr]")
{
  unittest::ExpectLogerr outer("failure", 1);
  {
    unittest::ExpectLogerr inner("inner failure", 1);
    logerr("inner failure");
  }
  logerr("outer failure");
}

TEST_CASE("captured errors are collected", "[testEnv][logerr]")
{
  String captured;
  {
    unittest::CaptureLogerr capture(captured);
    logerr("first %d", 1);
    logerr("second");
  }
  CHECK(strstr(captured, "first 1"));
  CHECK(strstr(captured, "second"));
}

TEST_CASE("expectation bookkeeping", "[testEnv][logerr]")
{
  const int handle = unittest::push_logerr_expectation("needle");
  CHECK_FALSE(unittest::consume_expected_logerr("haystack"));
  CHECK(unittest::consume_expected_logerr("[E] a needle here"));
  CHECK(unittest::pop_logerr_expectation(handle) == 1);
  CHECK_FALSE(unittest::consume_expected_logerr("[E] a needle here"));
}

TEST_CASE("data paths resolve against the data dir", "[testEnv]")
{
  CHECK(dd_file_exists(unittest::data_path("references/gradient.png")));
  CHECK(strstr(unittest::data_path("a/b.txt"), "a/b.txt"));
}

TEST_CASE("json escaping", "[testEnv]") { CHECK(unittest::json_escape("a\"b\\c\nd\x01") == String("a\\\"b\\\\c\\nd\\u0001")); }

TEST_CASE("current case tracks the running test case", "[testEnv]")
{
  CHECK(String(unittest::current_case()) == "current case tracks the running test case");
}

TEST_CASE("expected dagor assertions do not fail the test", "[testEnv][logerr]")
{
  unittest::ExpectLogerr expect("expected assertion");
  G_ASSERTF(1 + 1 == 3, "expected assertion");
}

TEST_CASE("scratch dir is fresh and writable", "[testEnv]")
{
  const String dir = unittest::scratch_dir();
  const String fn(0, "%s/file.txt", dir.c_str());
  file_ptr_t f = df_open(fn, DF_WRITE | DF_CREATE);
  REQUIRE(f);
  df_close(f);
  CHECK(dd_file_exists(fn));
  CHECK(unittest::scratch_dir() == dir);
  CHECK_FALSE(dd_file_exists(fn));
}
