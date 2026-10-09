#!/usr/bin/env bash
# daViewer (assetViewer) for the assets in assets/ (linux)
cd "$(dirname "$0")" || exit 1
. ../_engine.sh || { echo "Run \"python3 project.py setup\" in the project dir first."; exit 1; }
"$DAGOR_CDK_DIR/assetViewer2-dev" ../application.blk "$@" &
