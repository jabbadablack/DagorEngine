#!/usr/bin/env bash
# dabuild: exports assets/ into the game packs (../game/content), as python3 ../prog/build.py assets does
cd "$(dirname "$0")" || exit 1
. ../_engine.sh || { echo "Run \"python3 project.py setup\" in the project dir first."; exit 1; }
exec "$DAGOR_CDK_DIR/daBuild-dev" ../application.blk -q -jobs:$(getconf _NPROCESSORS_ONLN) "$@"
