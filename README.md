# FoxDen apps

Apps from outside developers for **FoxDen**, Rustica's app store. You
submit your app's source here as a pull request. GitHub checks it and
builds it, a maintainer reviews it, and once it is merged it is released
and published at `https://rustux.com/download/apps`. Every Rustica
computer can then install it from FoxDen or with `rpg install`.

Rustica's own apps (the Calculator, the Text Editor, ...) are in the
[rustux](https://github.com/gitrustux/rustux) repository, under
`userspace/apps`. This repository is for everyone else's.

## How an app gets to FoxDen

1. **You** register as a developer once, sign your app's folder with your
   key, and open a pull request.
2. **The checks** (`.github/workflows/check.yml`) look at the folder,
   verify your signature, and build the app from its source for Rustux.
   The package is attached to the run.
3. **A maintainer** reviews the source and the checks, then merges.
4. **The publish workflow** (`publish.yml`) builds each new version from
   `main`. It releases the package as `ID-VERSION` with a build provenance
   attestation.
5. **rustux.com** fetches the release and checks it again: your
   signature, that the package is your folder built, and its provenance.
   It then signs the package into the apps repository with the store's
   key, which never touches GitHub.

Apps run in Rustica's sandbox. An app reaches only its own folders, a
window, and what its permissions give, so a mistake in an app stays in
that app.

## 1. Register as a developer

Your developer ID comes from your GitHub login: `io.github.LOGIN` in lower
case (`io.github.alice` for `Alice`). Your apps' IDs are under it, for
example `io.github.alice.notes`.

Make a key with OpenSSL 3. Keep the private key to yourself; it is never
committed:

```sh
mkdir -p ~/foxden && cd ~/foxden
openssl genpkey -algorithm ed25519 -out io.github.alice.key
chmod 600 io.github.alice.key
openssl pkey -in io.github.alice.key -pubout -out key.pub
```

Add `developers/io.github.alice/` with two files:

- `key.pub`: the public key you just made.
- `developer`:

  ```
  Id: io.github.alice
  Name: Alice Example
  GitHub: alice
  ```

FoxDen shows your `Name` on your apps' pages. Only your GitHub account can
change your folder and your apps, and the checks enforce this. A key
change is confirmed by a maintainer.

## 2. Your app's folder

`apps/io.github.alice.notes/`:

```
manifest          what Rustica needs to know (below)
RPG/control       the package: version, license, description
icon.png          optional, 64x64 or larger
screenshot.png    optional, any number (listed in the manifest)
src/main.rs       your program, Rust; more modules in src/
SIGNATURE         made by ./sign.sh
```

`manifest`:

```
Id: io.github.alice.notes
Name: Notes
Summary: write down what you think of
Exec: bin/app
Icon: icon.png
Categories: Office Utility
Screenshots: screenshot.png
Permissions: files:documents
Platform: 1
Developer: io.github.alice
Developer-Name: Alice Example
Source: https://github.com/gitrustux/foxden-apps/tree/main/apps/io.github.alice.notes
```

`Exec` is always `bin/app`, the program built from `src/`. `Permissions`
lists what the app needs beyond its own folders and a window. The options
are `network`, `audio` (playing sound), `files:documents`,
`files:pictures`, `files:music`, `files:videos`, `files:downloads`,
`files:home` and `removable`. Ask for as
little as you can: without a `files:` permission, your app can still open
and save the files the user picks, through the file chooser
(`<rustux/portal.h>`).

`RPG/control`:

```
Package: io.github.alice.notes
Version: 1.0.0
Architecture: x86_64
Kind: app
License: MIT
Maintainer: Alice Example <alice@example.org>
Homepage: https://example.org/notes
Description: Notes
 A longer description, each line starting with a space.
```

`License` is an SPDX identifier from the list in `ci/check.py`, and your
source is published under it. Raise `Version` with every change.

### The source

Your app is Rust, built against Rustica's toolkit,
[rustica-ui](https://github.com/gitrustux/rustux/tree/main/userspace/rust/rustica-ui).
You don't write a `Cargo.toml`: the build makes the crate itself, with
`rustica-ui` as its only dependency. Nothing of yours runs while the app
is built. Your source may not use:

- `include!`, `include_str!`, `include_bytes!`
- `env!`, `option_env!`
- `#[path]`
- `#![feature]`
- `extern crate`

`apps/io.github.gitrustux.dice` is a small complete example.

## 3. Sign and submit

```sh
./sign.sh apps/io.github.alice.notes ~/foxden/io.github.alice.key
```

`sign.sh` signs the list of your folder's files and their SHA-256. Sign
again after every change, then commit and open a pull request. To run the
checks yourself (`rpg` from a rustux checkout is optional):

```sh
python3 ci/check.py
```

To build like the checks do (needs Rust 1.91 with `rust-src`, gcc and
binutils on Linux x86-64):

```sh
ci/get-rustux.sh
ci/build.sh out io.github.alice.notes
```

## Trying your app before submitting it

On Rustica you can run your app from its folder without installing it,
in the same sandbox it gets when installed (developer mode). Put the
program at `bin/app` beside the manifest, then run the command below.
The folder `ci/build.sh` packs on Linux,
`rustux/userspace/build/outside/ID.pkg`, is one, so you can copy it
over.

```sh
appctl run --dir ~/src/notes/build
```

No password is needed, because nothing is installed. You can also hand a
package file to others (`rpg build DIR`). They can install it with `rpg
install ./FILE.rpg` or by opening it in Files. Rustica shows such an app
as **not from FoxDen**, because nobody has checked it. By default,
installing a package file needs an administrator; one can let everyone do
it in Settings > Apps. An app installed from FoxDen is never replaced by
a package file.

## What the checks look at

- The folder's layout: only the files above, no links, pictures up to
  2 MiB, up to 1 MiB of source.
- The manifest and control file: the ID matches the folder and sits under
  your developer ID. `Exec`, `Source`, `Platform`, the permissions and the
  license are checked too.
- The source rules above.
- Your signature, by the key in your developer folder.
- In a pull request:
  - Only your own developer folder and apps are changed (`MAINTAINERS`
    may change anything).
  - A changed app's version goes up.
  - Its developer stays the same: an app never passes to another
    developer. Rustica refuses such an update too.
- The app builds, and the package is exactly your folder plus the
  program.

## Taking an app down, other questions

Open an issue. Maintainers are listed in `MAINTAINERS`.

## License

This repository's own files (`ci/`, `.github/`, `sign.sh`, this README)
are under the MIT license (`LICENSE`). Each app is under the license its
`RPG/control` names.
