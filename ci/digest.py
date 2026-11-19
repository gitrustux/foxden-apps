#!/usr/bin/env python3
# What a developer signs (as `rpg dev digest DIR` prints it; the checks
# compare the two): "rpg-source 1", then "file PATH SHA256" for every file
# under DIR but SIGNATURE, sorted by path. Links, and names with spaces or
# control characters, are refused.
import hashlib, os, sys

def digest(top):
    files = []
    for root, dirs, names in os.walk(top, followlinks=False):
        for n in dirs + names:
            p = os.path.join(root, n)
            rel = os.path.relpath(p, top)
            if any(c.isspace() or ord(c) < 32 for c in rel):
                sys.exit(f"digest: {rel}: a name with a space or a control character")
            if os.path.islink(p):
                sys.exit(f"digest: {rel}: not a file or a folder (no links)")
            if n in names:
                if not os.path.isfile(p):
                    sys.exit(f"digest: {rel}: not a file or a folder")
                if rel != "SIGNATURE":
                    with open(p, "rb") as f:
                        files.append((rel, hashlib.sha256(f.read()).hexdigest()))
    files.sort(key=lambda x: x[0].encode())
    return "rpg-source 1\n" + "".join(f"file {r} {h}\n" for r, h in files)

if __name__ == "__main__":
    sys.stdout.write(digest(sys.argv[1]))
