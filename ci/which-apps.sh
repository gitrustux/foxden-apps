#!/bin/bash
# Which apps to build:
#
#   ci/which-apps.sh changed BASE   the apps a pull request changes (that
#                                   still exist)
#   ci/which-apps.sh unreleased     the apps whose version has no release
#                                   yet (tag ID-VERSION; needs GH_TOKEN)
set -euo pipefail
cd "$(dirname "$0")/.."
case ${1:-} in
    changed)
        git diff --name-only "${2:?BASE}...HEAD" -- apps | cut -d/ -f2 | sort -u | while read -r id; do
            [ -f "apps/$id/RPG/control" ] && echo "$id"
        done ;;
    unreleased)
        for d in apps/*/RPG/control; do
            [ -f "$d" ] || continue
            id=$(basename "$(dirname "$(dirname "$d")")")
            v=$(sed -n 's/^Version: *//p' "$d" | tr -d '\r')
            gh release view "$id-$v" --repo "${GITHUB_REPOSITORY:-gitrustux/foxden-apps}" > /dev/null 2>&1 || echo "$id"
        done ;;
    *) echo "usage: ci/which-apps.sh changed BASE | unreleased"; exit 2 ;;
esac
