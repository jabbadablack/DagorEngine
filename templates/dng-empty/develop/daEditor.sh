#!/usr/bin/env bash
# daEditor for this project (linux): its workspace is made from ../application.blk on the first start
cd "$(dirname "$0")" || exit 1
. ../_engine.sh || { echo "Run \"python3 project.py setup\" in the project dir first."; exit 1; }
"$DAGOR_CDK_DIR/daEditor3x-dev" ../application.blk "$@" &
