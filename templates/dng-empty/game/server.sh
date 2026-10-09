#!/usr/bin/env bash
# Runs the dedicated server (clients connect with client.sh -connect:localhost); scripts are read from ../prog
cd "$(dirname "$0")" || exit 1
case "$(uname -s)" in
  Darwin) exec ./macOS-$(uname -m)/dng_empty-ded-dev -config:debug/useAddonVromSrc:b=yes "$@" ;;
  *)      exec ./linux-$(uname -m)/dng_empty-ded-dev -config:debug/useAddonVromSrc:b=yes "$@" ;;
esac
