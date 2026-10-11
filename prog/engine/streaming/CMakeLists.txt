# Ported from prog/engine/streaming/jamfile (jam2cmake/skeleton.py)
set(sources streamingCtrl.cpp streamingCtrlDebug.cpp streamingMgr.cpp baseStreamingScene.cpp)

dagor_add_library(STRICT SOURCES ${sources})
