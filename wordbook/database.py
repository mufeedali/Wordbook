# SPDX-FileCopyrightText: 2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Database management for pre-built WordNet databases.
Handles extraction, versioning, and cleanup of compressed database files.
"""

import os
import shutil
import sys
from pathlib import Path

from gi.repository import GLib

from wordbook import utils
from wordbook.constants import WN_FILE_VERSION

# Import appropriate zstd module based on Python version
if sys.version_info >= (3, 14):
    from compression import zstd
else:
    import backports.zstd as zstd


class DatabaseManager:
    """Manages pre-built WordNet database extraction and versioning."""

    @staticmethod
    def find_compressed_db() -> Path | None:
        """
        Search system data directories for versioned compressed database.

        Returns:
            Path to compressed database if found, None otherwise.
        """
        filename = f"wn-{WN_FILE_VERSION}.db.zst"

        if "MESON_SOURCE_ROOT" in os.environ:
            build_root = Path(os.environ.get("MESON_BUILD_ROOT", os.environ["MESON_SOURCE_ROOT"]))
            dev_db_path = build_root / "data" / filename
            if dev_db_path.is_file():
                utils.log_info(f"Found compressed database (dev): {dev_db_path}")
                return dev_db_path

        for data_dir in GLib.get_system_data_dirs():
            db_path = Path(data_dir) / "wordbook" / filename
            if db_path.is_file():
                utils.log_info(f"Found compressed database: {db_path}")
                return db_path

        utils.log_warning(f"No compressed database found for version {WN_FILE_VERSION}")
        return None

    @staticmethod
    def get_extracted_db_path() -> Path:
        """
        Get the path where the extracted database should exist.

        Returns:
            Path to extracted database.
        """
        return Path(utils.DATA_DIR) / f"wn-{WN_FILE_VERSION}" / "wn.db"

    @staticmethod
    def needs_extraction() -> bool:
        """
        Check if database needs to be extracted.

        Returns:
            True if extraction is needed, False otherwise.
        """
        db_path = DatabaseManager.get_extracted_db_path()
        exists = db_path.exists()

        if not exists:
            utils.log_info(f"Database extraction needed for version {WN_FILE_VERSION}")

        return not exists

    @staticmethod
    def cleanup_old_versions() -> None:
        """
        Remove old database directories for versions other than current.
        """
        data_dir = Path(utils.DATA_DIR)
        current_dir_name = f"wn-{WN_FILE_VERSION}"

        if not data_dir.exists():
            return

        for item in data_dir.iterdir():
            # Check if it's a wn-* directory and not the current version
            if item.is_dir() and item.name.startswith("wn") and item.name != current_dir_name:
                utils.log_info(f"Removing old database version: {item}")
                try:
                    shutil.rmtree(item)
                except OSError as e:
                    utils.log_error(f"Failed to remove old database directory {item}: {e}")

    @staticmethod
    def extract_database(compressed_path: Path) -> bool:
        """
        Extract compressed database to user data directory.

        Args:
            compressed_path: Path to the compressed .zst file

        Returns:
            True if extraction succeeded, False otherwise.
        """
        try:
            db_path = DatabaseManager.get_extracted_db_path()
            db_path.parent.mkdir(parents=True, exist_ok=True)

            utils.log_info(f"Extracting database from {compressed_path} to {db_path}")

            # Extract using zstd (same API for both compression.zstd and backports.zstd)
            with zstd.open(compressed_path, "rb") as src:
                with open(db_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

            utils.log_info("Database extraction complete")
            return True

        except Exception as e:
            utils.log_error(f"Database extraction failed: {e}")
            return False

    @staticmethod
    def setup() -> bool:
        """
        Main entry point for database setup.
        Checks if extraction is needed, cleans up old versions, and extracts if necessary.

        Returns:
            True if database is ready for use, False otherwise.
        """
        # Check if extraction needed
        if not DatabaseManager.needs_extraction():
            utils.log_info("Database already up to date")
            return True

        # Find compressed DB in system directories
        compressed_db = DatabaseManager.find_compressed_db()
        if not compressed_db:
            utils.log_error("No compressed database found - installation may be incomplete")
            return False

        # Clean up old versions before extracting new one
        DatabaseManager.cleanup_old_versions()

        # Extract new version
        return DatabaseManager.extract_database(compressed_db)
