# Welcome to XRPLib!

## Getting Starting with your XRP Robot

### Step 1: Plug XRP Robot Controller Board into Computer

### Step 2: Navigate to [xrpcode.wpi.edu](https://xrpcode.wpi.edu)

- Follow instructions there to install MicroPython and the libraries onto the board
- Please note that this version of the library requires a version of MicroPython specifically for the XRP Control Board. An official download for the firmware is coming soon, but for now, the UF2 file is attached to the most recent release on Github.

### Step 3: Navigate to the tutorial linked there to learn how to use the bot!

$~$

### That's it! Happy Learning!

$~$

## For Maintainers: Releasing to XRP_Firmware

Publishing a GitHub release here automatically proposes the same XRPLib as a new
versioned bundle in [Open-STEM/XRP_Firmware](https://github.com/Open-STEM/XRP_Firmware),
via the `Publish XRPLib to Firmware` workflow
([.github/workflows/publish-to-firmware.yml](.github/workflows/publish-to-firmware.yml)).

**What it does.** On a published (non-pre-) release it checks out this repo at the
release tag, assembles `boards/XRPLib/<version>/` in XRP_Firmware, and opens a pull
request there for a maintainer to review and merge. The bundle contains:

- `XRPLib/` and `XRPExamples/` copied from this release,
- `ble/` and `phew/` carried forward unchanged from the previous version (they are not
  stored in this repo),
- a generated `files.json`, and
- a new entry in `boards/XRPLib/index.json`.

The version is taken from the release tag with any leading `v` stripped
(`v2.2.4` → `2.2.4`), and becomes the directory name and the `xrplib-<version>` id.

The library version number has been changed to YY.MM.N - ex. 26.07.1 is the first version released in July 2026.

**One-time setup.** Add a repository secret named `FIRMWARE_TOKEN` — a fine-grained
PAT or GitHub App token with **Contents: write** and **Pull requests: write** on
Open-STEM/XRP_Firmware. Contents: write is needed to push the PR's branch (not to
merge or write to `main`); the default `GITHUB_TOKEN` cannot reach another repository.
Protect `main` on XRP_Firmware so nothing merges without review.

**Manual runs and backfills.** Trigger the workflow by hand from the Actions tab
(`Run workflow`) and optionally supply a `version` to (re)publish a specific one. Re-runs
are safe: if that version already exists in `index.json` on XRP_Firmware the workflow
makes no changes, and an open PR for the same version is updated rather than duplicated.

**Note.** The `files.json` generator in
[.github/scripts/build_xrplib_version.py](.github/scripts/build_xrplib_version.py)
reproduces the convention documented in XRP_Firmware's `boards/spec.md`; if that spec
changes, update the script to match.