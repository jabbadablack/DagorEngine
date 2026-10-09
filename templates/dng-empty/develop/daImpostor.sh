#!/usr/bin/env bash
# impostorBaker: bakes impostor textures of the assets that use them
cd "$(dirname "$0")" || exit 1
. ../_engine.sh || { echo "Run \"python3 project.py setup\" in the project dir first."; exit 1; }
exec "$DAGOR_CDK_DIR/impostorBaker-dev" ../application.blk -rootdir:./ -clean:yes "$@"
