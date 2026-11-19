#!/usr/bin/env python3
# The checks every pull request (and main) must pass (README.md, "What the
# checks look at"). Run from the repository's top folder:
#
#   python3 ci/check.py [--base REF] [--author LOGIN] [--rpg RPG]
#
# --base REF: check only what changed since REF (a pull request's base),
# and the rules about who may change what and versions going up;
# without it, everything. --author: the pull request's GitHub login.
# --rpg: rpg for this computer (rpg dev verify checks each signature).
# Prints what it checked; exits 1 on any problem, listing them all.
import argparse, os, re, subprocess, sys

ALLOWED_LICENSES = {
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Zlib", "MPL-2.0",
    "GPL-2.0-only", "GPL-2.0-or-later", "GPL-3.0-only", "GPL-3.0-or-later",
    "LGPL-2.1-only", "LGPL-2.1-or-later", "LGPL-3.0-only", "LGPL-3.0-or-later",
    "AGPL-3.0-only", "AGPL-3.0-or-later", "Unlicense", "CC0-1.0",
}
# The project's own namespaces: its apps are in the rustux repository
RESERVED = ("org.rustica", "org.rustux", "com.rustux")
PERMISSIONS = {"network", "files:documents", "files:pictures", "files:music", "files:videos",
               "files:downloads", "files:home", "removable", "audio", "camera", "location"}
PICTURE = re.compile(r"^[a-z0-9][a-z0-9._-]*\.(png|jpg|jpeg)$")
SOURCE = re.compile(r"^src/([a-z0-9_]+/)*[a-z0-9_]+\.rs$")
ID = re.compile(r"^[a-z0-9][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)+$")
# What may not be in an app's source: reading files or the environment
# while it is built, other source files, unstable features
FORBIDDEN = [
    (re.compile(r"\binclude(_str|_bytes)?\s*!"), "include!, include_str! and include_bytes! (read files while it is built)"),
    (re.compile(r"\b(option_)?env\s*!"), "env! and option_env! (read the build's environment)"),
    (re.compile(r"#\s*\[\s*path\b"), "#[path] (another file as a module)"),
    (re.compile(r"#\s*!\s*\[\s*feature\b"), "#![feature] (unstable features)"),
    (re.compile(r"\bextern\s+crate\b"), "extern crate"),
]
MAX_PICTURE = 2 * 1024 * 1024
MAX_SOURCE = 1024 * 1024

problems = []
checked = []

def problem(where, what):
    problems.append(f"{where}: {what}")

def fields(path):
    """A control-format file's fields (continuation lines joined)"""
    out, last = {}, None
    try:
        text = open(path, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as e:
        problem(path, f"cannot read it ({e})")
        return {}
    for line in text.splitlines():
        if line.startswith((" ", "\t")) and last:
            out[last] += "\n" + line.strip()
        elif ":" in line:
            k, v = line.split(":", 1)
            last = k.strip()
            if last in out:
                problem(path, f"{last} twice")
            out[last] = v.strip()
        elif line.strip():
            problem(path, f"not a field: {line!r}")
    return out

def version_key(v):
    return [int(p) if p.isdigit() else p for p in re.split(r"[.+~-]", v)]

def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout

def check_developer(dev):
    d = f"developers/{dev}"
    names = sorted(os.listdir(d))
    for n in names:
        if n not in ("developer", "key.pub"):
            problem(d, f"{n}: a developer's folder has developer and key.pub only")
    f = fields(f"{d}/developer")
    if f.get("Id") != dev:
        problem(f"{d}/developer", f"Id {f.get('Id')!r}: the folder's name, {dev}")
    if not ID.match(dev):
        problem(d, "a developer's ID is reverse DNS in lower case (io.github.LOGIN)")
    login = f.get("GitHub", "")
    if not re.match(r"^[A-Za-z0-9-]{1,39}$", login):
        problem(f"{d}/developer", "GitHub: your GitHub login")
    elif dev != f"io.github.{login.lower()}":
        problem(d, f"the developer ID of GitHub's {login} is io.github.{login.lower()} (other names: ask in an issue)")
    if not f.get("Name"):
        problem(f"{d}/developer", "Name: how FoxDen names you")
    try:
        k = open(f"{d}/key.pub").read()
        if "BEGIN PUBLIC KEY" not in k:
            raise ValueError
    except (OSError, ValueError):
        problem(f"{d}/key.pub", "your Ed25519 public key (openssl pkey -in KEY -pubout)")
    return f

def check_app(app, developers, rpg):
    d = f"apps/{app}"
    if not ID.match(app):
        problem(d, "an app's ID is reverse DNS in lower case")
    if app.startswith(tuple(r + "." for r in RESERVED)):
        problem(d, "org.rustica and the like are the project's own")
    source_size = 0
    for root, dirs, files in os.walk(d):
        for n in dirs + files:
            p = os.path.join(root, n)
            rel = os.path.relpath(p, d)
            if os.path.islink(p):
                problem(p, "a link (not allowed)")
                continue
            if os.path.isdir(p):
                if rel not in ("RPG", "src") and not rel.startswith("src/"):
                    problem(p, "only RPG/ and src/ (and src/'s folders)")
                continue
            size = os.path.getsize(p)
            if rel in ("manifest", "RPG/control", "SIGNATURE"):
                continue
            if PICTURE.match(rel):
                if size > MAX_PICTURE:
                    problem(p, "a picture of more than 2 MiB")
            elif SOURCE.match(rel):
                source_size += size
                try:
                    text = open(p, encoding="utf-8").read()
                except UnicodeDecodeError:
                    problem(p, "not UTF-8")
                    continue
                for rx, why in FORBIDDEN:
                    for m in rx.finditer(text):
                        line = text.count("\n", 0, m.start()) + 1
                        problem(f"{p}:{line}", f"{why}: not allowed")
            else:
                problem(p, "not allowed (manifest, RPG/control, SIGNATURE, pictures .png/.jpg at the top, src/**/*.rs)")
    if source_size > MAX_SOURCE:
        problem(d, "more than 1 MiB of source")
    if not os.path.isfile(f"{d}/src/main.rs"):
        problem(d, "no src/main.rs")
    m = fields(f"{d}/manifest")
    c = fields(f"{d}/RPG/control")
    if m.get("Id") != app:
        problem(f"{d}/manifest", f"Id: the folder's name, {app}")
    dev = m.get("Developer", "")
    if dev not in developers:
        problem(f"{d}/manifest", f"Developer {dev!r}: a folder in developers/")
    elif not app.startswith(dev + "."):
        problem(d, f"the app's ID is under its developer's ({dev}.NAME)")
    elif m.get("Developer-Name") != developers[dev].get("Name"):
        problem(f"{d}/manifest", f"Developer-Name: {developers[dev].get('Name')!r}, as in developers/{dev}/developer")
    if m.get("Exec") != "bin/app":
        problem(f"{d}/manifest", "Exec: bin/app (the program built from src/)")
    want = f"https://github.com/gitrustux/foxden-apps/tree/main/apps/{app}"
    if m.get("Source") != want:
        problem(f"{d}/manifest", f"Source: {want}")
    if m.get("Platform") != "1":
        problem(f"{d}/manifest", "Platform: 1")
    for k in ("Name", "Summary"):
        if not m.get(k):
            problem(f"{d}/manifest", f"no {k}")
    for p in m.get("Permissions", "").split():
        if p not in PERMISSIONS:
            problem(f"{d}/manifest", f"Permissions: {p}?" + (" (system is the project's only)" if p == "system" else ""))
    for k in ("Icon",):
        if m.get(k) and not PICTURE.match(m[k]):
            problem(f"{d}/manifest", f"{k}: a picture at the folder's top")
    for s in m.get("Screenshots", "").split():
        if not PICTURE.match(s) or not os.path.isfile(f"{d}/{s}"):
            problem(f"{d}/manifest", f"Screenshots: {s} is not a picture at the folder's top")
    if c.get("Package") != app:
        problem(f"{d}/RPG/control", f"Package: {app}")
    if c.get("Kind") != "app":
        problem(f"{d}/RPG/control", "Kind: app")
    if c.get("Architecture") != "x86_64":
        problem(f"{d}/RPG/control", "Architecture: x86_64")
    if c.get("License") not in ALLOWED_LICENSES:
        problem(f"{d}/RPG/control", f"License: one of {', '.join(sorted(ALLOWED_LICENSES))} (SPDX)")
    if not re.match(r"^[0-9][0-9A-Za-z.+~-]*$", c.get("Version", "")):
        problem(f"{d}/RPG/control", "Version: 1.0.0 and the like")
    for k in ("Depends", "Pre-Depends", "Conflicts", "Breaks", "Provides", "Replaces"):
        if k in c:
            problem(f"{d}/RPG/control", f"{k}: an app is self-contained")
    if not os.path.isfile(f"{d}/SIGNATURE"):
        problem(d, "no SIGNATURE (./sign.sh)")
    elif dev in developers and rpg:
        r = subprocess.run([rpg, "dev", "verify", d, f"developers/{dev}/key.pub"], capture_output=True, text=True)
        if r.returncode != 0:
            why = (r.stderr or r.stdout).strip().removeprefix("rpg: ").removeprefix(f"{d}: ")
            problem(d, why + " (./sign.sh again)")
    return m, c

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    ap.add_argument("--author")
    ap.add_argument("--rpg")
    a = ap.parse_args()
    maintainers = set()
    if os.path.isfile("MAINTAINERS"):
        maintainers = {l.split("#")[0].strip().lower() for l in open("MAINTAINERS") if l.split("#")[0].strip()}
    devs = sorted(os.listdir("developers")) if os.path.isdir("developers") else []
    apps = sorted(os.listdir("apps")) if os.path.isdir("apps") else []
    changed = None
    if a.base:
        changed = [l for l in git("diff", "--name-only", f"{a.base}...HEAD").splitlines() if l]
    def touched(prefix):
        return changed is None or any(p == prefix or p.startswith(prefix + "/") for p in changed)
    developers = {}
    for dev in devs:
        developers[dev] = check_developer(dev) if touched(f"developers/{dev}") else fields(f"developers/{dev}/developer")
        if touched(f"developers/{dev}"):
            checked.append(f"developer {dev}")
    for app in apps:
        if not touched(f"apps/{app}"):
            continue
        m, c = check_app(app, developers, a.rpg)
        checked.append(f"app {app} {c.get('Version', '?')}")
        if a.base:
            old = git("show", f"{a.base}:apps/{app}/RPG/control")
            ov = re.search(r"^Version:\s*(\S+)", old, re.M)
            if ov and c.get("Version") and version_key(c["Version"]) <= version_key(ov.group(1)):
                problem(f"apps/{app}/RPG/control", f"Version {c['Version']}: changed apps need a higher version than {ov.group(1)}")
            oldm = git("show", f"{a.base}:apps/{app}/manifest")
            od = re.search(r"^Developer:\s*(\S+)", oldm, re.M)
            if od and od.group(1) != m.get("Developer"):
                problem(f"apps/{app}/manifest", "Developer changed: an app does not pass to another developer")
    if changed is not None:
        for p in changed:
            if not (p.startswith("developers/") or p.startswith("apps/")) and (a.author or "").lower() not in maintainers:
                problem(p, "only the maintainers change the repository's own files (MAINTAINERS)")
            if p.startswith("apps/") and not os.path.exists(p) and (a.author or "").lower() not in maintainers:
                parts = p.split("/")
                if not os.path.isdir(f"apps/{parts[1]}"):
                    problem(p, "an app is taken down by the maintainers (open an issue)")
    # Who may change what: a developer their own folder and apps
    if a.author and changed is not None and a.author.lower() not in maintainers:
        owners = set()
        for p in changed:
            parts = p.split("/")
            if parts[0] == "developers" and len(parts) > 1:
                owners.add(parts[1])
            elif parts[0] == "apps" and len(parts) > 1:
                owner = next((dv for dv in developers if parts[1].startswith(dv + ".")), None)
                owners.add(owner or "?")
        for o in sorted(owners):
            login = developers.get(o, {}).get("GitHub", "")
            if o == "?" or login.lower() != a.author.lower():
                problem(f"developers/{o}" if o != "?" else "apps/", f"{a.author} may change only their own developer folder and apps (io.github.{a.author.lower()})")
        for p in changed:
            if p.startswith("developers/") and p.endswith("/key.pub") and git("show", f"{a.base}:{p}"):
                print(f"check: note: {p} changed: a maintainer should confirm it is the developer's new key")
    for c in checked:
        print(f"check: {c}")
    if problems:
        print(f"check: {len(problems)} problems:")
        for p in problems:
            print(f"  {p}")
        sys.exit(1)
    print(f"check: all well ({len(checked)} checked)")

if __name__ == "__main__":
    main()
