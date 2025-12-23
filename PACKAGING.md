# Packaging Wordbook

Starting with version 0.7.0, Wordbook bundles the WordNet database, making Wordbook fully offline. This means that anyone packaging Wordbook must also take this into account.

## Database Requirement

Wordbook now requires a pre-built, compressed WordNet database file to be packaged along with the application. The application **does not** download this file at runtime anymore; it must be provided by the package as the [Flatpak](build-aux/flatpak/dev.mufeed.Wordbook.Devel.json) does, for example.

### File Details

The filename is suffixed with the version of the `wn` library used to generate it, as the database schema may change between versions. Each release of Wordbook will include a database file generated with the `wn` version that the release was built and tested against as a release asset.

File name format: `wn-oewn-<oewn-version>-<wn-version>.db.zst`
Example: `wn-oewn-2024-0.14.0.db.zst`

### Installation Path

The compressed database file must be installed to the application's data directory. **Usually** `/usr/share/wordbook/` in the case of system-level packages. Refer to the [GLib documentation](https://docs.gtk.org/glib/func.get_system_data_dirs.html) if necessary.

### Runtime Behavior

On the first run, Wordbook will:

1. Look for `wn-oewn-2024-0.14.0.db.zst` in the system data directories (e.g., `/usr/share/wordbook`).
2. Extract it to the user's data directory (e.g., `~/.local/share/wordbook/wn-oewn-2024-0.14.0/wn.db`).
3. Clean up any older directories from previous versions if present.

If the compressed file is not found in the system paths, the application will show a "Database not found" error screen and will not function.

## Python Dependencies

The following Python packages are required:

- `wn` (Refer to version compatibility section below)
- `pydantic`
- `rapidfuzz`
- `backports.zstd` (Required for Python < 3.14; Python 3.14+ has built-in zstd support)

## `wn` Version Compatibility

The `wn` library version is tightly coupled with the database schema. The provided database file (`wn-oewn-2024-0.14.0.db.zst`) is generated using `wn==0.14.0`.

Packagers **must** ensure that the system version of `python-wn` is compatible with this database file. If the distribution ships a newer version of `wn` that introduces schema changes, the database file provided in the release assets will be incompatible.

### Database Regeneration

If the system `wn` version differs significantly or introduces schema changes, you must regenerate the database file using the included script.

1. Ensure build dependencies are installed (`wn`, `rich`, `backports.zstd`).
2. Run the generation script:
   ```bash
   python3 scripts/generate-wn-db.py --output .
   ```
3. This will download the Open English WordNet data, import it into a fresh SQLite database using the current `wn` version, and compress it.
4. Use the resulting `wn-<oewn-version>-<wn-version>.db.zst` in place of the upstream asset.
5. Verify that everything actually works and check for API differences in `wn`.
