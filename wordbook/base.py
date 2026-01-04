# SPDX-FileCopyrightText: 2016-2025 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Base module for Wordbook, containing UI-independent logic.
"""

import difflib
import os
import subprocess
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Any

import wn

from wordbook import utils
from wordbook.constants import (
    POS_MAP,
    SEARCH_TERM_CLEANUP_CHARS,
    SEARCH_TERM_REPLACE_CHARS,
    WN_DB_VERSION,
    WN_FILE_VERSION,
)

POOL = ThreadPoolExecutor()

# WordNet database access lock
WN_DATABASE_LOCK = threading.Lock()

WN_DIR: str = os.path.join(utils.DATA_DIR, f"wn-{WN_FILE_VERSION}")

wn.config.data_directory = WN_DIR
wn.config.allow_multithreading = True


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
    os.makedirs(utils.CONFIG_DIR, exist_ok=True)
    os.makedirs(utils.DATA_DIR, exist_ok=True)
    os.makedirs(WN_DIR, exist_ok=True)


def fetch_definition(term: str, wn_instance: wn.Wordnet, accent: str = "us") -> dict[str, Any]:
    """
    Obtains the definition and pronunciation data for a term from WordNet.

    Args:
        term: The term to define.
        wn_instance: The initialized Wordnet instance.
        accent: The espeak-ng accent code.

    Returns:
        A dictionary containing the definition data with pronunciation information.
    """
    with WN_DATABASE_LOCK:
        definition_data = get_definition(term, wn_instance)

    pronunciation_term = definition_data.get("term") or term
    pron = get_pronunciation(pronunciation_term, accent)
    final_pron = pron if pron and not pron.isspace() else "Pronunciation unavailable (is espeak-ng installed?)"

    final_data: dict[str, Any] = {
        "term": definition_data.get("term", term),
        "pronunciation": final_pron,
        "result": definition_data.get("result"),
    }

    return final_data


def _normalize_lemma(lemma: str) -> str:
    """Normalize a lemma by replacing underscores with spaces and stripping whitespace."""
    return lemma.replace("_", " ").strip()


def _find_best_lemma_match(term: str, lemmas: list[str]) -> str:
    """Finds the best matching lemma for the search term, prioritizing exact matches."""
    normalized_term = term.lower().strip()

    for lemma in lemmas:
        if _normalize_lemma(lemma).lower() == normalized_term:
            return _normalize_lemma(lemma)

    diff_match = difflib.get_close_matches(term, lemmas, n=1, cutoff=0.8)
    if diff_match:
        return _normalize_lemma(diff_match[0])

    return _normalize_lemma(lemmas[0]) if lemmas else ""


def _get_lemmas_from_related(matched_lemma: str, synset: wn.Synset, relation: str) -> list[str]:
    """Get normalized lemmas from a relation group."""
    target_list: list[str] = []
    for related_synset in synset.get_related(relation):
        for lemma in related_synset.lemmas():
            normalized_lemma = _normalize_lemma(lemma)
            if normalized_lemma.lower() != matched_lemma.lower() and normalized_lemma not in target_list:
                target_list.append(normalized_lemma)
    return target_list


def _extract_related_lemmas(synset: wn.Synset, matched_lemma: str) -> dict[str, list[str]]:
    """Extracts synonyms, antonyms, similar terms, and 'also sees'."""
    related: dict[str, list[str]] = {"syn": [], "ant": [], "sim": [], "also_sees": []}

    related["syn"] = [
        _normalize_lemma(lemma) for lemma in synset.lemmas() if _normalize_lemma(lemma).lower() != matched_lemma.lower()
    ]

    for sense in synset.senses():
        for ant_sense in sense.get_related("antonym"):
            ant_name = _normalize_lemma(ant_sense.word().lemma())
            if ant_name not in related["ant"]:
                related["ant"].append(ant_name)

    related["sim"] = _get_lemmas_from_related(matched_lemma, synset, "similar")
    related["also_sees"] = _get_lemmas_from_related(matched_lemma, synset, "also")

    return related


def get_definition(term: str, wn_instance: wn.Wordnet) -> dict[str, Any]:
    """
    Gets the definition from WordNet, processes it, and prepares data structure.

    Args:
        term: The term to define.
        wn_instance: The initialized Wordnet instance.

    Returns:
        A dictionary with the processed definition data ('term', 'result').
    """
    first_match: str | None = None
    result_dict: dict[str, Any] = {pos: [] for pos in POS_MAP.values()}

    synsets = wn_instance.synsets(term.lower())

    if not synsets:
        clean_def = {"term": term, "result": None}
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

        matched_lemma = _find_best_lemma_match(term, lemmas)
        if first_match is None:
            first_match = matched_lemma

        related_lemmas = _extract_related_lemmas(synset, matched_lemma)

        synset_data: dict[str, Any] = {
            "name": matched_lemma,
            "definition": synset.definition() or "No definition available.",
            "examples": synset.examples() or [],
            **related_lemmas,
        }

        result_dict[pos_name].append(synset_data)

    clean_def = {
        "term": first_match or term,
        "result": result_dict,
    }
    return clean_def


@lru_cache(maxsize=128)
def get_pronunciation(term: str, accent: str = "us") -> str | None:
    """
    Gets the pronunciation of a term using the 'espeak-ng' command-line tool.

    Args:
        term: The word or phrase to pronounce.
        accent: The espeak-ng accent code (e.g., "us", "gb").

    Returns:
        The pronunciation in IPA format (e.g., "/tˈɛst/"), or None if espeak-ng fails.
    """
    try:
        process = subprocess.Popen(
            [
                "espeak-ng",
                "-v",
                f"en-{accent}",
                "--ipa=3",
                "-q",
                term,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = process.communicate(timeout=5)

        if process.returncode == 0 and stdout:
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
def get_wn_instance(reloader: Callable[[], None]) -> wn.Wordnet:
    """
    Initializes the WordNet instance in a thread.

    Handles potential WordNet database errors and triggers the reloader function.

    Args:
        reloader: A function to call if WordNet initialization fails (e.g., to trigger download).

    Returns:
        The initialized WordNet instance.
    """
    utils.log_info("Initializing WordNet...")
    try:
        wn_instance: wn.Wordnet = wn.Wordnet(lexicon=WN_DB_VERSION)
        utils.log_info(f"WordNet instance ({WN_DB_VERSION}) created and ready.")
        return wn_instance
    except (wn.Error, wn.DatabaseError) as e:
        utils.log_error(f"WordNet initialization failed: {e}. Triggering reloader.")
        reloader()
        raise e
    except Exception as e:
        utils.log_error(f"Unexpected error during WordNet initialization: {e}. Retrying.")
        reloader()
        raise e


@_threadpool
def get_wn_wordlist(wn_instance: wn.Wordnet) -> list[str]:
    """
    Fetches the word list from an initialized WordNet instance.
    Uses _threadpool decorator to run in a separate thread.
    Uses WN_DATABASE_LOCK for each individual lemma access to allow search operations to interrupt.

    Args:
        wn_instance: The initialized WordNet instance.

    Returns:
        A list of lemmas from the WordNet database.
    """
    utils.log_info("Fetching WordNet wordlist...")
    try:
        # Get all words first
        with WN_DATABASE_LOCK:
            wn_lemmas = wn_instance.lemmas()

        utils.log_info(f"WordNet wordlist fetched ({len(wn_lemmas)} lemmas).")
        return wn_lemmas
    except Exception as e:
        utils.log_error(f"Error fetching WordNet wordlist: {e}")
        return []


def format_output(text: str, wn_instance: wn.Wordnet, accent: str = "us") -> dict[str, Any] | None:
    """
    Determines colors, handles special commands (fortune, exit), and fetches definitions.
    Uses WN_DATABASE_LOCK to prevent concurrent access with wordlist loading.

    Args:
        text: The input text (search term or command).
        wn_instance: The initialized Wordnet instance.
        accent: The espeak-ng accent code.

    Returns:
        A dictionary containing definition data, or None if input is invalid/empty.
        Exits the program for specific commands.
    """
    if text and not text.isspace():
        cleaned_text = clean_search_terms(text)
        if cleaned_text:
            definition_data = fetch_definition(cleaned_text, wn_instance, accent=accent)
            return definition_data
        else:
            utils.log_info(f"Input '{text}' became empty after cleaning.")
            return None
    else:
        utils.log_info(f"Input text is empty or whitespace: '{text}'")
        return None


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
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
            text=True,
        )
    except FileNotFoundError:
        utils.log_error("'espeak-ng' command not found. Cannot read term aloud.")
    except subprocess.TimeoutExpired:
        utils.log_error(f"espeak-ng timed out while trying to read term: '{text}'")
    except OSError as ex:
        utils.log_error(f"OS error executing espeak-ng to read term '{text}': {ex}")
