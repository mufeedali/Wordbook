# SPDX-FileCopyrightText: 2016-2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Base module for Wordbook, containing UI-independent logic.
"""

import difflib
import html
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from shutil import rmtree
from typing import Any
from collections.abc import Callable

import wn

from wordbook import utils

POOL = ThreadPoolExecutor()
WN_DB_VERSION: str = "oewn:2024"

# Configure wn library
wn.config.data_directory = os.path.join(utils.WN_DIR)
wn.config.allow_multithreading = True

# Parts of Speech Mapping (from wn tagset to human-readable)
POS_MAP: dict[str, str] = {
    "s": "adjective",
    "n": "noun",
    "v": "verb",
    "r": "adverb",
    "a": "adjective",  # Note: 'a' and 's' both map to adjective
    "t": "phrase",
    "c": "conjunction",
    "p": "adposition",
    "x": "other",
    "u": "unknown",
}

# Color Constants for Output Formatting
DARK_MODE_SENTENCE_COLOR = "cyan"
DARK_MODE_WORD_COLOR = "lightgreen"
LIGHT_MODE_SENTENCE_COLOR = "blue"
LIGHT_MODE_WORD_COLOR = "green"

# Characters to remove during search term cleaning
SEARCH_TERM_CLEANUP_CHARS = '<>"-?`![](){}/:;,'
SEARCH_TERM_REPLACE_CHARS = ["(", ")", "<", ">", "[", "]", "&", "\\", "\n"]


def _threadpool(func: Callable) -> Callable:
    """
    Wraps around a function allowing it to run in a separate thread and
    return a future object.
    """

    def wrap(*args: Any, **kwargs: Any) -> Any:
        return (POOL).submit(func, *args, **kwargs)

    return wrap


def clean_search_terms(search_term: str) -> str:
    """
    Cleans up search terms by removing leading/trailing whitespace,
    specific punctuation, and unwanted characters.
    """
    text = search_term.strip().strip(SEARCH_TERM_CLEANUP_CHARS)
    for char in SEARCH_TERM_REPLACE_CHARS:
        text = text.replace(char, "")
    return text


def create_required_dirs() -> None:
    """Make required directories if they don't already exist."""
    os.makedirs(utils.CONFIG_DIR, exist_ok=True)  # create Wordbook folder
    os.makedirs(utils.CDEF_DIR, exist_ok=True)  # create Custom Definitions folder.


def fetch_definition(
    text: str,
    wn_instance: wn.Wordnet,
    use_custom_def: bool = True,
    accent: str = "us",
) -> dict[str, Any]:
    """
    Fetches the definition for a term, checking for a custom definition first if requested.

    Args:
        text: The term to define.
        wn_instance: The initialized Wordnet instance.
        use_custom_def: Whether to check for a custom definition first.
        accent: The espeak-ng accent code (e.g., "us", "gb").

    Returns:
        A dictionary with the definition data.
    """
    custom_def_path = os.path.join(utils.CDEF_DIR, text.lower())
    if use_custom_def and os.path.isfile(custom_def_path):
        return get_custom_def(text, wn_instance, accent)
    return get_data(text, wn_instance, accent)


def get_cowfortune() -> str:
    """
    Presents a cowsay version of a fortune easter egg.

    Requires 'cowsay' and 'fortune'/'fortune-mod' to be installed.

    Returns:
        An HTML formatted string with the cowsay output, or an error message.
    """
    try:
        # Ensure get_fortune runs first and potentially raises its own error if fortune isn't found
        fortune_text = get_fortune(mono=False)
        if "Easter egg fail!" in fortune_text:  # Check if get_fortune failed
            return f"<tt>{fortune_text}</tt>"  # Return fortune's error message

        process = subprocess.Popen(
            ["cowsay", fortune_text],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # Capture stderr separately
            text=True,  # Decode output automatically
        )
        stdout, stderr = process.communicate()

        if process.returncode == 0 and stdout:
            return f"<tt>{html.escape(stdout)}</tt>"
        else:
            error_msg = f"Cowsay command failed. Return code: {process.returncode}. Stderr: {stderr.strip()}"
            utils.log_error(error_msg)
            return "<tt>Cowsay fail… Too bad…</tt>"
    except FileNotFoundError:
        error_msg = "Easter Egg Fail! 'cowsay' command not found. Please install it."
        utils.log_error(error_msg)
        return f"<tt>{error_msg}</tt>"
    except OSError as ex:
        error_msg = f"Easter Egg Fail! OS error during cowsay execution: {ex}"
        utils.log_error(error_msg)
        return f"<tt>{error_msg}</tt>"


def get_custom_def(text: str, wn_instance: wn.Wordnet, accent: str = "us") -> dict[str, str]:
    """
    Loads and presents a custom definition from a local file.

    Args:
        text: The term whose custom definition file should be read.
        wn_instance: The initialized Wordnet instance.
        accent: The espeak-ng accent code.

    Returns:
        A dictionary with the custom definition and related data.
    """
    custom_def_path = os.path.join(utils.CDEF_DIR, text.lower())
    try:
        with open(custom_def_path, encoding="utf-8") as def_file:
            custom_def_dict: dict[str, str] = json.load(def_file)
    except FileNotFoundError:
        # This is not an error, just means no custom definition exists. Fallback silently.
        return get_data(text, wn_instance, accent)
    except json.JSONDecodeError as e:
        utils.log_error(f"Error decoding custom definition file '{custom_def_path}': {e}")
        # Fallback to standard definition if custom file is corrupt
        return get_data(text, wn_instance, accent)
    except OSError as e:
        utils.log_error(f"OS error reading custom definition file '{custom_def_path}': {e}")
        # Fallback on other OS errors during file read
        return get_data(text, wn_instance, accent)

    # Handle 'linkto' redirection
    linked_term = custom_def_dict.get("linkto")
    if linked_term:
        return get_data(linked_term, wn_instance, accent)

    # Get definition string, falling back to WordNet if not provided
    definition = custom_def_dict.get("out_string", "")

    formatted_definition = definition or ""

    term = custom_def_dict.get("term", text)
    # Get pronunciation, falling back to espeak-ng
    pronunciation = custom_def_dict.get("pronunciation")
    if not pronunciation:
        pronunciation = get_pronunciation(term, accent)
        pronunciation = (
            pronunciation
            if pronunciation and not pronunciation.isspace()
            else "Pronunciation unavailable (is espeak-ng installed?)"
        )

    final_data: dict[str, str] = {
        "term": term,
        "pronunciation": pronunciation,
        "out_string": formatted_definition,
    }
    return final_data


def get_data(term: str, wn_instance: wn.Wordnet, accent: str = "us") -> dict[str, Any]:
    """
    Obtains the definition and pronunciation data for a term from WordNet.

    Args:
        term: The term to define.
        wn_instance: The initialized Wordnet instance.
        accent: The espeak-ng accent code.

    Returns:
        A dictionary containing the definition data with pronunciation information.
    """
    # Obtain definition from WordNet
    definition_data = get_definition(term, wn_instance)

    # Determine the term to use for pronunciation (found lemma or original)
    pronunciation_term = definition_data.get("term") or term

    # Get pronunciation
    pron = get_pronunciation(pronunciation_term, accent)
    final_pron = pron if pron and not pron.isspace() else "Pronunciation unavailable (is espeak-ng installed?)"
    # Create the dictionary to be returned.
    final_data: dict[str, Any] = {
        "term": definition_data.get("term", term),  # Use original term if lookup failed
        "pronunciation": final_pron,
        "result": definition_data.get("result"),  # This holds the structured data
        "out_string": definition_data.get("out_string"),
    }

    return final_data


def _find_best_lemma_match(term: str, lemmas: list[str]) -> str:
    """Finds the best matching lemma for the search term."""
    diff_match = difflib.get_close_matches(term, lemmas, n=1, cutoff=0.8)
    return diff_match[0].strip() if diff_match else lemmas[0].strip()


def _extract_related_lemmas(synset: wn.Synset) -> dict[str, list[str]]:
    """Extracts synonyms, antonyms, similar terms, and 'also sees'."""
    related: dict[str, list[str]] = {"syn": [], "ant": [], "sim": [], "also_sees": []}
    base_lemma = synset.lemmas()[0]  # Use first lemma as reference if needed

    # Synonyms (other lemmas in the same synset)
    related["syn"] = [lemma.replace("_", " ").strip() for lemma in synset.lemmas() if lemma != base_lemma]

    # Antonyms
    for sense in synset.senses():
        for ant_sense in sense.get_related("antonym"):
            ant_name = ant_sense.word().lemma().replace("_", " ").strip()
            if ant_name not in related["ant"]:  # Avoid duplicates
                related["ant"].append(ant_name)

    # Similar To
    for sim_synset in synset.get_related("similar"):
        related["sim"].extend(lemma.replace("_", " ").strip() for lemma in sim_synset.lemmas())

    # Also See
    for also_synset in synset.get_related("also"):
        related["also_sees"].extend(lemma.replace("_", " ").strip() for lemma in also_synset.lemmas())

    return related


def get_definition(term: str, wn_instance: wn.Wordnet) -> dict[str, Any]:
    """
    Gets the definition from WordNet, processes it, and prepares data structure.

    Args:
        term: The term to define.
        wn_instance: The initialized Wordnet instance.

    Returns:
        A dictionary with the processed definition data ('term', 'result', 'out_string').
    """
    first_match: str | None = None
    # Initialize result_dict with all possible POS keys from POS_MAP
    result_dict: dict[str, Any] = {pos: [] for pos in POS_MAP.values()}

    synsets = wn_instance.synsets(term)

    if not synsets:
        # Term not found in WordNet
        clean_def = {"term": term, "result": None, "out_string": None}
        return clean_def

    for synset in synsets:
        pos_tag = synset.pos
        pos_name = POS_MAP.get(pos_tag)
        if not pos_name:
            utils.log_warning(f"Unknown POS tag encountered: {pos_tag} for term '{term}'")
            pos_name = POS_MAP["u"]  # Default to 'unknown'

        lemmas = synset.lemmas()
        if not lemmas:
            continue  # Skip synsets with no lemmas

        # Find the best lemma match and store the first good one found
        matched_lemma = _find_best_lemma_match(term, lemmas)
        if first_match is None:
            first_match = matched_lemma

        # Extract related lemmas (synonyms, antonyms, etc.)
        related_lemmas = _extract_related_lemmas(synset)

        synset_data: dict[str, Any] = {
            "name": matched_lemma,
            "definition": synset.definition() or "No definition available.",
            "examples": synset.examples() or [],
            **related_lemmas,  # Merge related lemmas dict
        }

        result_dict[pos_name].append(synset_data)

    # Prepare the final output structure
    # Note: 'out_string' is usually generated later by the UI/formatter based on 'result'
    clean_def = {
        "term": first_match or term,  # Fallback to original term if no match found
        "result": result_dict,
        "out_string": None,  # Formatted string is generated elsewhere
    }
    return clean_def


def get_fortune(mono: bool = True) -> str:
    """
    Presents a fortune easter egg. Requires 'fortune' or 'fortune-mod'.

    Args:
        mono: If True, wraps the output in <tt> tags for monospace display.

    Returns:
        The fortune text, HTML escaped, optionally in <tt> tags, or an error message.
    """
    try:
        process = subprocess.Popen(
            ["fortune", "-a"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate()

        if process.returncode == 0 and stdout:
            fortune_output = html.escape(stdout.strip(), False)
        else:
            error_msg = f"Fortune command failed. Return code: {process.returncode}. Stderr: {stderr.strip()}"
            utils.log_error(error_msg)
            fortune_output = "Easter egg fail! Could not get fortune."

    except FileNotFoundError:
        fortune_output = "Easter egg fail! 'fortune' command not found. Install 'fortune' or 'fortune-mod'."
        utils.log_error(fortune_output)
    except OSError as ex:
        fortune_output = f"Easter egg fail! OS error during fortune execution: {ex}"
        utils.log_error(fortune_output)

    return f"<tt>{fortune_output}</tt>" if mono else fortune_output


@lru_cache(maxsize=128)
def get_pronunciation(term: str, accent: str = "us") -> str | None:
    """
    Gets the pronunciation of a term using espeak-ng.

    Args:
        term: The word or phrase to pronounce.
        accent: The espeak-ng accent code (e.g., "us", "gb").

    Returns:
        The pronunciation in IPA format (e.g., "/tˈɛst/"), or None if espeak-ng fails.
    """
    try:
        process = subprocess.Popen(
            ["espeak-ng", "-v", f"en-{accent}", "--ipa=3", "-q", term],  # Use IPA level 3 for more detail
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(timeout=5)  # Add timeout

        if process.returncode == 0 and stdout:
            # Clean up potential extra whitespace and format
            ipa_pronunciation = stdout.strip().replace("\n", " ").replace("  ", " ")
            return f"/{ipa_pronunciation.strip('/')}/"

        utils.log_warning(f"espeak-ng failed for term '{term}'. RC: {process.returncode}. Stderr: {stderr.strip()}")
        return None
    except FileNotFoundError:
        utils.log_error("'espeak-ng' command not found. Please install espeak-ng.")
        return None
    except subprocess.TimeoutExpired:
        utils.log_error(f"espeak-ng timed out for term '{term}'.")
        return None
    except OSError as ex:
        utils.log_error(f"OS error executing espeak-ng for term '{term}': {ex}")
        return None


def get_version_info(app_version: str) -> None:
    """Prints application and dependency version info to the console."""
    print(f"Wordbook - {app_version}")
    print("Copyright 2016-2025 Mufeed Ali")
    print()
    try:
        process = subprocess.Popen(
            ["espeak-ng", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate(timeout=5)

        if process.returncode == 0 and stdout:
            print(stdout.strip())
        else:
            utils.log_error(f"Failed to get espeak-ng version. RC: {process.returncode}. Stderr: {stderr.strip()}")
            print("Could not retrieve espeak-ng version information.")

    except FileNotFoundError:
        utils.log_error("'espeak-ng' command not found during version check.")
        print("Dependency missing: espeak-ng is not installed or not in PATH.")
    except subprocess.TimeoutExpired:
        utils.log_error("espeak-ng --version command timed out.")
        print("Could not retrieve espeak-ng version information (timeout).")
    except OSError as ex:
        utils.log_error(f"OS error executing espeak-ng --version: {ex}")
        print(f"Could not retrieve espeak-ng version information (OS error: {ex})")


@_threadpool
def get_wn_file(reloader: Callable[[], None]) -> dict[str, Any]:
    """
    Initializes the WordNet instance and fetches the word list in a thread.

    Handles potential WordNet database errors and triggers the reloader function.

    Args:
        reloader: A function to call if WordNet initialization fails (e.g., to trigger download).

    Returns:
        A dictionary containing the WordNet instance ('instance') and the word list ('list'),
        or the result of the reloader function if initialization fails.
    """
    utils.log_info("Initializing WordNet...")
    try:
        wn_instance: wn.Wordnet = wn.Wordnet(lexicon=WN_DB_VERSION)
        utils.log_info(f"WordNet instance ({WN_DB_VERSION}) created.")

        utils.log_info("Fetching WordNet wordlist...")

        wn_lemmas = [w.lemma() for w in wn_instance.words()]
        utils.log_info(f"WordNet wordlist fetched ({len(wn_lemmas)} lemmas). WordNet is ready.")
        return {"instance": wn_instance, "list": wn_lemmas}

    except (wn.Error, wn.DatabaseError) as e:
        utils.log_error(f"WordNet initialization failed: {e}. Triggering reloader.")
        return reloader()
    except Exception as e:
        # Catch unexpected errors during initialization
        utils.log_error(f"Unexpected error during WordNet initialization: {e}. Retrying.")
        return reloader()


def format_output(
    text: str, wn_instance: wn.Wordnet, use_custom_def: bool, accent: str = "us"
) -> dict[str, Any] | None:
    """
    Determines colors, handles special commands (fortune, exit), and fetches definitions.

    Args:
        text: The input text (search term or command).
        wn_instance: The initialized Wordnet instance.
        use_custom_def: Whether to check for custom definitions.
        accent: The espeak-ng accent code.

    Returns:
        A dictionary containing definition data, or None if input is invalid/empty.
        Exits the program for specific commands.
    """
    # Easter Eggs and Special Commands
    if text == "fortune -a":
        return {
            "term": "<tt>Some random adage</tt>",
            "pronunciation": "<tt>Courtesy of fortune</tt>",
            "out_string": get_fortune(),
        }
    if text == "cowfortune":
        return {
            "term": "<tt>Some random adage from a cow</tt>",
            "pronunciation": "<tt>Courtesy of fortune and cowsay</tt>",
            "out_string": get_cowfortune(),
        }
    if text in ("crash now", "close now"):
        utils.log_info(f"Exiting due to command: '{text}'")
        sys.exit(0)  # Intentional exit

    # Fetch definition for valid, non-empty text
    if text and not text.isspace():
        cleaned_text = clean_search_terms(text)
        if cleaned_text:  # Ensure text isn't empty after cleaning
            definition_data = fetch_definition(cleaned_text, wn_instance, use_custom_def=use_custom_def, accent=accent)
            return definition_data
        else:
            utils.log_info(f"Input '{text}' became empty after cleaning.")
            return None  # Return None if text becomes empty after cleaning
    else:
        utils.log_info(f"Input text is empty or whitespace: '{text}'")
        return None  # Return None for empty or whitespace input


def read_term(text: str, speed: int = 120, accent: str = "us") -> None:
    """
    Uses espeak-ng to speak the given text aloud.

    Args:
        text: The text to speak.
        speed: Speaking speed (words per minute).
        accent: The espeak-ng accent code.
    """
    try:
        subprocess.run(
            ["espeak-ng", "-s", str(speed), "-v", f"en-{accent}", text],
            stdout=subprocess.DEVNULL,  # Discard standard output
            stderr=subprocess.PIPE,  # Capture standard error
            check=False,  # Don't raise exception on non-zero exit, handle manually
            timeout=10,  # Add timeout
            text=True,
        )
        # Note: We don't check result.check_returncode() here as espeak might return non-zero
        # even on successful speech in some cases. Logging stderr might be useful if debugging.
        # if result.stderr:
        #    utils.log_warning(f"espeak-ng stderr while reading term '{text}': {result.stderr.strip()}")

    except FileNotFoundError:
        utils.log_error("'espeak-ng' command not found. Cannot read term aloud.")
    except subprocess.TimeoutExpired:
        utils.log_error(f"espeak-ng timed out while trying to read term: '{text}'")
    except OSError as ex:
        utils.log_error(f"OS error executing espeak-ng to read term '{text}': {ex}")


class WordnetDownloader:
    @staticmethod
    def check_status() -> bool:
        """
        Checks if the primary WordNet database file exists.
        """
        db_path = os.path.join(utils.WN_DIR, "wn.db")
        utils.log_info(f"Checking for WordNet DB at: {db_path}")
        return os.path.isfile(db_path)

    @staticmethod
    def download(progress_handler: Callable[[int, int], None] | None = None) -> None:
        """
        Downloads the specified WordNet database version using wn.download.

        Removes the temporary 'downloads' directory first if it exists.

        Args:
            progress_handler: An optional callback function for progress updates.
        """
        download_dir = os.path.join(utils.WN_DIR, "downloads")
        if os.path.isdir(download_dir):
            utils.log_info(f"Removing existing temporary download directory: {download_dir}")
            rmtree(download_dir)

        utils.log_info(f"Starting download of WordNet version: {WN_DB_VERSION}")
        try:
            # Let wn handle the download, but pass a callback to track progress
            _ = wn.download(WN_DB_VERSION, progress_handler=progress_handler)
            utils.log_info(f"WordNet download completed for {WN_DB_VERSION}.")
        except Exception as e:
            # Catch potential errors during download (network issues, wn errors)
            utils.log_error(f"WordNet download failed for {WN_DB_VERSION}: {e}")
            raise

    @staticmethod
    def delete_db() -> None:
        """
        Deletes the primary WordNet database file.
        """
        db_path = os.path.join(utils.WN_DIR, "wn.db")
        if os.path.isfile(db_path):
            try:
                utils.log_info(f"Deleting WordNet database file: {db_path}")
                os.remove(db_path)
            except OSError as e:
                utils.log_error(f"Failed to delete WordNet database file '{db_path}': {e}")
        else:
            utils.log_warning(f"Attempted to delete WordNet database, but file not found: {db_path}")
