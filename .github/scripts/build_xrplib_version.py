#!/usr/bin/env python3
"""
Assemble a new XRPLib version directory inside a checked-out XRP_Firmware repo.

Called by .github/workflows/publish-to-firmware.yml on a XRP_MicroPython release.
It copies this release's XRPLib/ and XRPExamples/ into boards/XRPLib/<version>/,
carries ble/ and phew/ forward from the previous version (they do not live in this
repo), regenerates files.json, and registers the version in index.json.

The files.json format and device-path convention are defined in the firmware repo's
boards/spec.md; this reproduces the generator that normally lives in XRPWeb.
"""

import json
import os
import shutil
import sys

# Directories whose files land under /lib on the robot; everything else keeps its path.
LIB_DIRS = ("XRPLib", "AgXRPLib", "ble", "phew")
# Never bundled: version.py is synthesized on-device from the registry version.
EXCLUDE_NAMES = ("version.py",)
EXCLUDE_DIRS = ("__pycache__",)


def die(msg):
    print("ERROR: {}".format(msg), file=sys.stderr)
    sys.exit(1)


def copy_tree(src, dst):
    if not os.path.isdir(src):
        die("expected source directory does not exist: {}".format(src))
    shutil.copytree(
        src, dst,
        ignore=shutil.ignore_patterns(*EXCLUDE_DIRS, "*.pyc", *EXCLUDE_NAMES),
    )


def device_path(rel_path):
    # rel_path is POSIX-style, relative to the version dir, e.g. "XRPLib/board.py".
    top = rel_path.split("/", 1)[0]
    return "/lib/" + rel_path if top in LIB_DIRS else "/" + rel_path


def generate_files_json(version_dir):
    pairs = []
    for root, dirs, files in os.walk(version_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for name in files:
            if name in EXCLUDE_NAMES or name.endswith(".pyc") or name == "files.json":
                continue
            abs_path = os.path.join(root, name)
            rel = os.path.relpath(abs_path, version_dir).replace(os.sep, "/")
            pairs.append([device_path(rel), rel])
    # files.json is a plain ascending sort by source path (see spec.md / existing releases).
    pairs.sort(key=lambda pair: pair[1])
    with open(os.path.join(version_dir, "files.json"), "w", newline="\n") as f:
        json.dump(pairs, f, indent=4)
        f.write("\n")


def main():
    version = os.environ["XRPLIB_VERSION"].strip()
    src_repo = os.environ.get("SRC_REPO", ".")
    firmware = os.environ["FIRMWARE_REPO"]

    store = os.path.join(firmware, "boards", "XRPLib")
    index_path = os.path.join(store, "index.json")
    version_dir = os.path.join(store, version)

    with open(index_path) as f:
        index = json.load(f)

    version_id = "xrplib-{}".format(version)
    if any(v.get("id") == version_id or v.get("dir") == version for v in index["versions"]):
        print("Version {} already registered in index.json; nothing to do.".format(version))
        return

    if os.path.exists(version_dir):
        die("{} already exists but is not in index.json; refusing to overwrite".format(version_dir))

    if not index["versions"]:
        die("no existing versions to source ble/ and phew/ from; seed one manually first")
    previous_dir = os.path.join(store, index["versions"][0]["dir"])

    # This release supplies XRPLib and XRPExamples; ble/phew are carried forward unchanged.
    os.makedirs(version_dir)
    copy_tree(os.path.join(src_repo, "XRPLib"), os.path.join(version_dir, "XRPLib"))
    copy_tree(os.path.join(src_repo, "XRPExamples"), os.path.join(version_dir, "XRPExamples"))
    for carried in ("ble", "phew"):
        copy_tree(os.path.join(previous_dir, carried), os.path.join(version_dir, carried))

    generate_files_json(version_dir)

    index["versions"].insert(0, {
        "id": version_id,
        "name": "XRPLib {}".format(version),
        "dir": version,
        "version": version,
    })
    with open(index_path, "w", newline="\n") as f:
        json.dump(index, f, indent=4)
        f.write("\n")

    print("Created {} and registered {}".format(version_dir, version_id))


if __name__ == "__main__":
    main()
