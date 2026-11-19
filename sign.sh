#!/bin/bash
# Sign your app's folder with your developer key (FoxDen, README.md):
#
#   ./sign.sh apps/YOUR.APP.ID ~/foxden/YOUR.DEVELOPER.ID.key
#
# Writes apps/YOUR.APP.ID/SIGNATURE: your key's signature over the list of
# the folder's files and their SHA-256 (what `rpg dev digest` prints; the
# checks recompute it, so sign again after every change). Needs openssl 3
# and python3; rpg is not needed.
set -euo pipefail
dir=${1:?usage: ./sign.sh apps/ID KEYFILE}
key=${2:?usage: ./sign.sh apps/ID KEYFILE}
[ -f "$dir/manifest" ] || { echo "sign.sh: $dir: no manifest"; exit 1; }
d=$(mktemp)
trap 'rm -f "$d"' EXIT
python3 "$(dirname "$0")/ci/digest.py" "$dir" > "$d"
openssl pkeyutl -sign -inkey "$key" -rawin -in "$d" -out "$dir/SIGNATURE"
echo "sign.sh: signed $dir ($(grep -c '^file ' "$d") files)"
