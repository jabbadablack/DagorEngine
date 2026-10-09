#!/usr/bin/env bash
# Runs the game. The scripts and data are read from ../prog (no vromfs rebuild needed); pass more arguments as usual.
cd "$(dirname "$0")" || exit 1
if [ "$(uname -s)" = Darwin ]; then
  app=DngEmpty; [ "$(uname -m)" = arm64 ] && app=DngEmptyArm64
  exec "./$app.app/Contents/MacOS/dng_empty-dev" -config:debug/useAddonVromSrc:b=yes "$@"
fi
exec "./linux-$(uname -m)/dng_empty-dev" -config:debug/useAddonVromSrc:b=yes "$@"
