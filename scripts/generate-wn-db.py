#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Generate compressed WordNet database for Wordbook."""

import argparse
import sys
import tempfile
import urllib.request
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "subprojects" / "wn"))

import wn  # noqa: E402
import wn.util  # noqa: E402

if sys.version_info >= (3, 14):
    from compression import zstd
else:
    try:
        import backports.zstd as zstd
    except ImportError:
        sys.exit("Error: 'backports.zstd' is required for Python < 3.14\nInstall with: pip install backports.zstd")

CHUNK_SIZE = 1024 * 1024

WORDNET_URLS = [
    "https://github.com/globalwordnet/english-wordnet/releases/download/2025-edition/english-wordnet-2025-plus.xml.gz",
    "https://en-word.net/static/english-wordnet-2025-plus.xml.gz",
]


class ProgressHandler(wn.util.ProgressHandler):
    """Simple progress handler for wn operations."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._last_percent = -1

    def update(self, n: int = 1, force: bool = False):
        super().update(n, force)
        total = self.kwargs.get("total", 0)
        if total:
            count = self.kwargs.get("count", 0)
            percent = int((int(count) / int(total)) * 100)
            if percent // 10 > self._last_percent // 10:
                self._last_percent = percent
                message = self.kwargs.get("message", "Processing")
                print(f"  {message}: {percent}%")

    def flash(self, message: str):
        if message:
            print(f"  {message}")


def download_wordnet_xml(output_path: Path) -> bool:
    """Download WordNet XML file using the configured fallback URLs."""

    for url in WORDNET_URLS:
        try:
            print(f"Downloading from {url}...")
            request = urllib.request.Request(url, headers={"User-Agent": "Wordbook"})

            with urllib.request.urlopen(request) as response, output_path.open("wb") as file_handle:
                total = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                last_percent = -1

                while chunk := response.read(CHUNK_SIZE):
                    file_handle.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        percent = int((downloaded / total) * 100)
                        if percent // 10 > last_percent // 10:
                            last_percent = percent
                            print(f"  Download: {percent}%")

            print(f"✓ Downloaded to {output_path}")
            return True
        except Exception as e:
            print(f"✗ Download failed: {e}")

    return False


def add_from_file(source_file: Path, data_dir: Path) -> bool:
    """Add WordNet from local file."""
    try:
        wn.config.data_directory = str(data_dir)
        print(f"Adding {source_file}...")
        wn.add(source_file, progress_handler=ProgressHandler)
        print(f"✓ Added {source_file}")
        return True
    except Exception as e:
        print(f"✗ Failed to add source file: {e}")
        return False


def compress_database(db_path: Path, output_path: Path, level: int = 15) -> bool:
    """Compress database with zstd."""
    try:
        original_mb = db_path.stat().st_size / CHUNK_SIZE
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Compressing {original_mb:.1f} MB (level {level})...")
        with open(db_path, "rb") as src, zstd.open(output_path, "wb", level=level) as dst:
            while chunk := src.read(CHUNK_SIZE):
                dst.write(chunk)

        compressed_mb = output_path.stat().st_size / CHUNK_SIZE
        ratio = (1 - compressed_mb / original_mb) * 100
        print(f"✓ Compressed to {compressed_mb:.1f} MB ({ratio:.0f}% saved)")
        return True

    except Exception as e:
        print(f"✗ Compression failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate compressed WordNet database")
    parser.add_argument(
        "--compression-level",
        type=int,
        default=15,
        choices=range(1, 23),
        metavar="LEVEL",
        help="Zstd level 1-22 (default: 15)",
    )
    parser.add_argument(
        "--source-file", type=Path, help="Path to local lexicon file (XML/GZ). If not provided, downloads from GitHub."
    )
    parser.add_argument("--output", type=Path, help="Output path for the compressed database")

    args = parser.parse_args()
    output_path = args.output or project_root / "data" / "wn.db.zst"
    source_label = args.source_file or f"{WORDNET_URLS[0]} (+ {len(WORDNET_URLS) - 1} fallback)"

    print("─" * 20 + " Wordbook Database Generator " + "─" * 20)
    print(f"Source:      {source_label}")
    print(f"Output:      {output_path}")
    print(f"Compression: Level {args.compression_level}")
    print()

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        source_file = args.source_file or temp_dir / "english-wordnet.xml.gz"

        if not args.source_file and not download_wordnet_xml(source_file):
            print("✗ All download URLs failed")
            return 1

        if not add_from_file(source_file, temp_dir):
            return 1

        db_path = next(temp_dir.rglob("wn.db"), None)
        if not db_path:
            print(f"✗ wn.db not found in {temp_dir}")
            return 1

        if not compress_database(db_path, output_path, args.compression_level):
            return 1

        print()
        print("─" * 25 + " Success " + "─" * 25)
        print(f"Generated: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
