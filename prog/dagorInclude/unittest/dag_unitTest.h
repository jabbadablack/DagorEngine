//
// Dagor Engine 6.5
// Copyright (C) Gaijin Games KFT.  All rights reserved.
//
#pragma once

// Catch2 helpers for Dagor unit tests. Test executables are built with prog/_jBuild/unitTest.jam and use
// <unittest/mainCatch2.inc.cpp> as their main.

#include <unittest/dag_testEnv.h>
#include <catch2/catch_test_macros.hpp>
#include <exception>

namespace unittest
{
// Expects error messages containing substr while in scope; they don't fail the test.
// On scope exit checks that exactly `count` of them were logged (any number when count < 0).
class ExpectLogerr
{
public:
  explicit ExpectLogerr(const char *substr, int count = 1) : substr(substr), expected(count), handle(push_logerr_expectation(substr))
  {}
  ~ExpectLogerr()
  {
    const int logged = pop_logerr_expectation(handle);
    if (expected < 0 || std::uncaught_exceptions() > 0) // don't pile up a second failure while a REQUIRE unwinds
      return;
    INFO("expected logerr containing \"" << substr << "\"");
    CHECK(logged == expected);
  }
  ExpectLogerr(const ExpectLogerr &) = delete;
  ExpectLogerr &operator=(const ExpectLogerr &) = delete;

private:
  const char *substr;
  int expected;
  int handle;
};

// Collects every error message logged while in scope into `out` (one per line) instead of failing the test.
class CaptureLogerr
{
public:
  explicit CaptureLogerr(String &out) : handle(push_logerr_expectation("", &out)) {}
  ~CaptureLogerr() { pop_logerr_expectation(handle); }
  CaptureLogerr(const CaptureLogerr &) = delete;
  CaptureLogerr &operator=(const CaptureLogerr &) = delete;

private:
  int handle;
};
} // namespace unittest

// Compares a TexImage32 with references/<name>.png in the test data dir (see unittest::check_image).
#define CHECK_IMAGE(image, name, params)                                                       \
  do                                                                                           \
  {                                                                                            \
    const unittest::ImageCheckResult imageCheck_ = unittest::check_image(image, name, params); \
    INFO(imageCheck_.message.c_str());                                                         \
    CHECK(imageCheck_.passed);                                                                 \
  } while (0)

#define REQUIRE_IMAGE(image, name, params)                                                     \
  do                                                                                           \
  {                                                                                            \
    const unittest::ImageCheckResult imageCheck_ = unittest::check_image(image, name, params); \
    INFO(imageCheck_.message.c_str());                                                         \
    REQUIRE(imageCheck_.passed);                                                               \
  } while (0)
