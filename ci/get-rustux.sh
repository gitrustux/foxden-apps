#!/bin/bash
# The rustux tree the apps are built with, at the commit ci/rustux-commit
# names, into ./rustux (its toolkit, C library and build script:
# scripts/build-outside-app.sh)
set -euo pipefail
cd "$(dirname "$0")/.."
c=$(tr -d ' \n' < ci/rustux-commit)
if [ ! -d rustux/.git ]; then
    git clone -q --filter=blob:none https://github.com/gitrustux/rustux rustux
fi
git -C rustux fetch -q origin "$c" 2>/dev/null || true
git -C rustux checkout -q "$c"
echo "rustux at $(git -C rustux rev-parse --short HEAD)"
