// Copyright (C) Gaijin Games KFT.  All rights reserved.
#pragma once

#include <daScript/daScript.h>
#include "main/testMode.h"

namespace bind_dascript
{
inline void test_mode_register(const char *name, const char *wrapper, const char *file, int line, das::Context *context)
{
  test_mode::register_test(context, name ? name : "", wrapper ? wrapper : "", file ? file : "", line);
}
inline void test_mode_begin_case(const char *name) { test_mode::begin_case(name ? name : ""); }
inline void test_mode_log(const char *msg, const char *file, int line) { test_mode::log_case(msg ? msg : "", file ? file : "", line); }
inline int test_mode_push_logerr_expectation(const char *substr) { return test_mode::push_logerr_expectation(substr ? substr : ""); }
} // namespace bind_dascript
