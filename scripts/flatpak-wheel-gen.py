#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

PACKAGES = ["pydantic", "rapidfuzz", "backports.zstd"]
PYTHON_VERSION = "3.13"
ABI = "cp313"
ARCHES = {
    "x86_64": "manylinux_2_17_x86_64",
    "aarch64": "manylinux_2_17_aarch64",
}


def get_sha256(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def find_pypi_url(filename):
    guess_name = filename.split("-")[0]
    candidates = {guess_name, guess_name.replace("_", "-"), guess_name.replace(".", "-")}

    for name in candidates:
        try:
            url = f"https://pypi.org/pypi/{name}/json"
            with urllib.request.urlopen(url) as r:
                data = json.load(r)

            for version in data.get("releases", {}).values():
                for file_info in version:
                    if file_info["filename"] == filename:
                        return file_info["url"]
        except Exception:
            continue

    return None


def download_wheels(temp_dir, arch, platform_tag):
    print(f"--> Resolving and downloading for {arch} ({platform_tag})...", file=sys.stderr)
    dest = Path(temp_dir) / arch
    dest.mkdir()

    cmd = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "--dest",
        str(dest),
        "--only-binary=:all:",
        "--python-version",
        PYTHON_VERSION,
        "--implementation",
        "cp",
        "--abi",
        ABI,
        "--platform",
        platform_tag,
    ] + PACKAGES

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error downloading for {arch}:", file=sys.stderr)
        print(e.stderr.decode(), file=sys.stderr)
        sys.exit(1)

    return {f.name: f for f in dest.glob("*.whl")}


def generate_sources():
    with tempfile.TemporaryDirectory() as temp_dir:
        results = {}
        for arch, tag in ARCHES.items():
            results[arch] = download_wheels(temp_dir, arch, tag)

        all_filenames = set()
        for arch in ARCHES:
            all_filenames.update(results[arch].keys())

        sources = []
        for filename in sorted(all_filenames):
            arches_with_file = [arch for arch in ARCHES if filename in results[arch]]
            if not arches_with_file:
                continue

            first_arch = arches_with_file[0]
            filepath = results[first_arch][filename]
            sha256 = get_sha256(filepath)
            url = find_pypi_url(filename)
            if url is None:
                print(f"Warning: Could not find PyPI URL for {filename}", file=sys.stderr)
                url = f"FIXME_COULD_NOT_FIND_URL_FOR_{filename}"

            source = {
                "type": "file",
                "url": url,
                "sha256": sha256,
            }

            if len(arches_with_file) < len(ARCHES):
                source["only-arches"] = arches_with_file

            sources.append(source)

        print(json.dumps(sources, indent=4))


if __name__ == "__main__":
    generate_sources()
