// fixture of test_integration.py: every way an in-game test can fail
options gen2
require ecs
require DagorSystem
require danetlibs/test_harness/ecs_test

[ecs_test]
def fails_an_assertion(t : T?) {
  t |> equal(1, 2, "one is not two")
}

[ecs_test]
def panics(t : T?) {
  panic("deliberate panic")
}

[ecs_test]
def logs_an_unexpected_error(t : T?) {
  logerr("unexpected in-game error")
}

[ecs_test]
def fatal_stops_the_test(t : T?) {
  t->fatal("stop here")
  t |> equal(1, 2, "never reached")
}

[ecs_test]
def is_skipped(t : T?) {
  t |> skip("not today")
}

[ecs_test]
def sub_test_fails(t : T?) {
  t |> run("bad") <| @(t : T?) {
    t |> success(false, "sub failure")
  }
}

[ecs_test]
def passes_after_failures(t : T?) {
  t |> equal(3, 3)
}
