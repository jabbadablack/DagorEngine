# tests of the project tools (engine.blk, project glue, dng.py new)
dagor_add_exec_test(tools.dagorProject COMMAND ${Python3_EXECUTABLE} -m unittest -v test_dagorProject TAGS tools)
