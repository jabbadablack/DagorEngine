// fixture of test_integration.py: a test that never returns
options gen2
require danetlibs/test_harness/ecs_test

[ecs_test]
def hangs(t : T?) {
  var i = 0
  while (true) {
    i++
  }
}
