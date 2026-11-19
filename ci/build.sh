#!/bin/bash
# Build apps from their source into app packages:
#
#   ci/build.sh OUTDIR ID...
#
# Each with rustux's scripts/build-outside-app.sh (ci/get-rustux.sh fetches
# the tree), which also checks the package against the folder. Prints the
# files.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=${1:?usage: ci/build.sh OUTDIR ID...}; shift
mkdir -p "$OUT"
[ $# -gt 0 ] || { echo "ci/build.sh: nothing to build"; exit 0; }
[ -d rustux/.git ] || ci/get-rustux.sh
for id in "$@"; do
    rustux/scripts/build-outside-app.sh "apps/$id" "$OUT"
done
