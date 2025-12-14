#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

"""Generate compressed WordNet database for Wordbook."""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

import wn
import wn.util
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

if sys.version_info >= (3, 14):
    from compression import zstd
else:
    import backports.zstd as zstd


# Add project root to sys.path to allow importing wordbook
sys.path.append(str(Path(__file__).resolve().parent.parent))

from wordbook.constants import WN_DB_VERSION, WN_FILE_VERSION

console = Console()
_progress_context = None


class RichProgressHandler(wn.util.ProgressHandler):
    """Rich progress handler for wn downloads."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.task_id = None
        if _progress_context is not None:
            total = kwargs.get("total", 0)
            message = kwargs.get("message", "Processing")
            self.task_id = _progress_context.add_task(f"[cyan]{message}", total=total or None)

    def update(self, n: int = 1, force: bool = False):
        """Update progress by n bytes."""
        super().update(n, force)
        if _progress_context is not None and self.task_id is not None:
            _progress_context.advance(self.task_id, n)

    def set(self, **kwargs):
        """Update handler parameters."""
        super().set(**kwargs)
        # Update the Rich task if message or total changes
        if _progress_context is not None and self.task_id is not None:
            if "total" in kwargs:
                total = kwargs["total"]
                _progress_context.update(self.task_id, total=total or None)
            if "message" in kwargs:
                _progress_context.update(self.task_id, description=f"[cyan]{kwargs['message']}")

    def flash(self, message: str):
        """Display a flash message."""
        if message:
            console.print(f"[dim]{message}[/dim]")

    def close(self):
        """Close the progress handler."""
        pass


def download_wordnet(lexicon: str, data_dir: Path) -> bool:
    """Download WordNet lexicon."""
    global _progress_context

    try:
        wn.config.data_directory = str(data_dir)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            _progress_context = progress
            wn.download(lexicon, progress_handler=RichProgressHandler)
            _progress_context = None

        console.print(f"[green]✓[/green] Downloaded {lexicon}")
        return True
    except Exception as e:
        _progress_context = None
        console.print(f"[red]✗ Download failed: {e}[/red]")
        return False


def find_db_file(data_dir: Path) -> Path | None:
    """Find wn.db in data directory."""
    db_path = data_dir / "wn.db"
    if db_path.exists():
        return db_path

    for db_file in data_dir.rglob("wn.db"):
        return db_file

    console.print(f"[red]✗ wn.db not found in {data_dir}[/red]")
    return None


def compress_database(db_path: Path, output_path: Path, level: int = 15) -> bool:
    """Compress database with zstd."""
    try:
        original_size = db_path.stat().st_size
        original_mb = original_size / (1024 * 1024)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"[cyan]Compressing {original_mb:.1f} MB (level {level})", total=original_size)

            with open(db_path, "rb") as src, zstd.open(output_path, "wb", level=level) as dst:
                while chunk := src.read(1024 * 1024):
                    dst.write(chunk)
                    progress.advance(task, len(chunk))

        compressed_mb = output_path.stat().st_size / (1024 * 1024)
        ratio = (1 - compressed_mb / original_mb) * 100

        console.print(
            f"[green]✓[/green] Compressed to [bold]{compressed_mb:.1f} MB[/bold] ([dim]{ratio:.0f}% saved[/dim])"
        )
        return True

    except Exception as e:
        console.print(f"[red]✗ Compression failed: {e}[/red]")
        return False


def main():
    parser = argparse.ArgumentParser(description="Generate compressed WordNet database")
    parser.add_argument("--version", default=WN_FILE_VERSION, help=f"Version string (default: {WN_FILE_VERSION})")
    parser.add_argument("--lexicon", default=WN_DB_VERSION, help=f"Lexicon to download (default: {WN_DB_VERSION})")
    parser.add_argument("--output", type=Path, default=Path.cwd(), help="Output directory")
    parser.add_argument(
        "--compression-level",
        type=int,
        default=15,
        choices=range(1, 23),
        metavar="LEVEL",
        help="Zstd level 1-22 (default: 15)",
    )
    parser.add_argument("--keep-temp", action="store_true", help="Keep temp directory")

    args = parser.parse_args()
    output_path = args.output / f"wn-{args.version}.db.zst"

    console.rule("[bold cyan]Wordbook Database Generator[/bold cyan]")
    console.print(f"[dim]Lexicon:[/dim]     [yellow]{args.lexicon}[/yellow]")
    console.print(f"[dim]Output:[/dim]      [blue]{output_path}[/blue]")
    console.print(f"[dim]Compression:[/dim] Level {args.compression_level}")
    console.print()

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        if not download_wordnet(args.lexicon, temp_dir):
            return 1

        db_path = find_db_file(temp_dir)
        if not db_path:
            return 1

        if not compress_database(db_path, output_path, args.compression_level):
            return 1

        console.print()
        console.rule("[bold green]Success[/bold green]")
        console.print(f"Generated: [bold blue]{output_path}[/bold blue]")

        if args.keep_temp:
            kept_dir = Path(f"wordnet_temp_{args.version}")
            shutil.copytree(temp_dir, kept_dir)
            console.print()
            console.print(f"[dim]Temp files: {kept_dir}[/dim]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
