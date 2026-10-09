// Copyright (C) Gaijin Games KFT.  All rights reserved.

// Deliberately failing cases that verify how the harness reports failures (exit codes, events.jsonl).
// They are hidden ([.]) and only run when selected by name, e.g. by the test runner's self-tests:
//   unitTest-tests-dev "harness: unexpected logerr fails the case"

#include <unittest/dag_unitTest.h>
#include <debug/dag_assert.h>
#include <debug/dag_debug.h>
#include <osApiWrappers/dag_miscApi.h>
#include <osApiWrappers/dag_threads.h>

TEST_CASE("harness: unexpected logerr fails the case", "[.][harness]") { logerr("unexpected harness error"); }

TEST_CASE("harness: logerr on another thread fails the case", "[.][harness]")
{
  struct Worker final : public DaThread
  {
    Worker() : DaThread("harnessWorker") {}
    void execute() override { logerr("unexpected harness error from a worker thread"); }
  };
  Worker *worker = new Worker;
  worker->start();
  worker->terminate(true);
  worker->destroy();
}

TEST_CASE("harness: expected logerr count mismatch fails", "[.][harness]")
{
  unittest::ExpectLogerr expect("counted", 2);
  logerr("counted once");
}

TEST_CASE("harness: dagor assertion fails the case", "[.][harness]") { G_ASSERT(1 + 1 == 3); }

TEST_CASE("harness: hung case hits the watchdog", "[.][harness]")
{
  for (;;)
    sleep_msec(10);
}

TEST_CASE("harness: skipped case", "[.][harness]") { SKIP("skipped on purpose"); }
