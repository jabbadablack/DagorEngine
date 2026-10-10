# the fork contacts no Gaijin hosts: see host_guard.py
dagor_add_exec_test(tools.hostGuard COMMAND ${Python3_EXECUTABLE} -m unittest -v test_host_guard TAGS tools)
