# SPDX-FileCopyrightText: 2016-2026 Mufeed Ali <me@mufeed.dev>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Base module for Wordbook, containing UI-independent logic.
"""

import difflib
import os
import subprocess
import threading
from collections.abc import Callable
from dataclasses import dataclass
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

WN_DATABASE_LOCK = threading.Lock()

WN_DIR: str = os.path.join(utils.DATA_DIR, f"wn-{WN_FILE_VERSION}")

wn.config.data_directory = WN_DIR
wn.config.allow_multithreading = True


def clean_search_terms(search_term: str) -> str:
    """
    Cleans up search terms by removing leading/trailing whitespace,
    specific punctuation, and unwanted characters.
    """
    text = search_term.strip().strip(SEARCH_TERM_CLEANUP_CHARS)
    for char in SEARCH_TERM_REPLACE_CHARS:
        text = text.replace(char, "")
    return text


@dataclass
class PronunciationInfo:
    ipa: str
    is_fallback: bool = False


@dataclass
class PronunciationGroup:
    pronunciation: PronunciationInfo | None
    synsets: list[dict[str, Any]]


@dataclass
class LemmaGroup:
    lemma: str
    pronunciation_groups: list[PronunciationGroup]


def _normalize_pronunciation_variety(variety: str | None) -> str:
    if not variety:
        return ""
    return variety.strip().casefold()


def _pronunciation_group_key(pronunciation: PronunciationInfo | None) -> tuple[str, bool]:
    if pronunciation is None:
        return ("", False)
    return (pronunciation.ipa, pronunciation.is_fallback)


def group_synsets_by_lemma(synsets: list[dict[str, Any]]) -> list[LemmaGroup]:
    lemma_groups: dict[str, dict[tuple[str, bool], list[dict[str, Any]]]] = {}

    for synset in synsets:
        lemma = synset["name"]
        pronunciation = synset.get("pronunciation")
        pronunciation_groups = lemma_groups.setdefault(lemma, {})
        pronunciation_groups.setdefault(_pronunciation_group_key(pronunciation), []).append(synset)

    return [
        LemmaGroup(
            lemma=lemma,
            pronunciation_groups=[
                PronunciationGroup(
                    pronunciation=group_synsets[0].get("pronunciation"),
                    synsets=group_synsets,
                )
                for group_synsets in pronunciation_groups.values()
            ],
        )
        for lemma, pronunciation_groups in lemma_groups.items()
    ]


def ipa_to_espeak(ipa_string: str) -> str:
    s = ipa_string.strip().strip("/[]")

    mapping = {
        "ˈ": "'",
        "ˌ": ",",
        "ː": ":",
        ".": "",
        "‿": "",
        "|": "",
        "‖": "",
        "tʃ": "tS",
        "dʒ": "dZ",
        "eɪ": "eI",
        "aɪ": "aI",
        "ɔɪ": "OI",
        "aʊ": "aU",
        "oʊ": "oU",
        "əʊ": "@U",
        "ɪə": "I@",
        "eə": "e@",
        "ɛə": "e@",
        "ʊə": "U@",
        "iː": "i:",
        "ɑː": "A:",
        "ɔː": "O:",
        "uː": "u:",
        "ɜː": "3:",
        "ɚ": "@r",
        "ɝ": "3r",
        "ɪ": "I",
        "ɛ": "E",
        "e": "e",
        "æ": "a",
        "ɑ": "A",
        "ɒ": "0",
        "ɔ": "O",
        "ʊ": "U",
        "ʌ": "V",
        "ɜ": "3",
        "ə": "@",
        "ɐ": "@",
        "a": "a",
        "θ": "T",
        "ð": "D",
        "ʃ": "S",
        "ʒ": "Z",
        "ŋ": "N",
        "ɹ": "r",
        "ɾ": "4",
        "ɫ": "l",
        "ʔ": "?",
        "ʍ": "W",
        "x": "x",
        "ç": "C",
    }

    for ipa_sym, esp_sym in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
        s = s.replace(ipa_sym, esp_sym)

    s = "".join(c for c in s if ord(c) < 128)
    return f"[[{s}]]"


def _pick_pronunciation(prons: list[wn.Pronunciation], accent: str) -> PronunciationInfo | None:
    if not prons:
        return None

    requested_variety = _normalize_pronunciation_variety(accent)

    for p in prons:
        pronunciation_variety = _normalize_pronunciation_variety(p.variety)
        if pronunciation_variety and pronunciation_variety == requested_variety:
            return PronunciationInfo(ipa=p.value)

    p = prons[0]
    return PronunciationInfo(ipa=p.value)


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
        A dictionary containing the definition data without a top-level pronunciation.
    """
    with WN_DATABASE_LOCK:
        definition_data = get_definition(term, wn_instance, accent=accent)

    result = definition_data.get("result")
    resolved_term = definition_data.get("term", term)

    if not result or not resolved_term:
        return definition_data

    normalized_resolved_term = resolved_term.casefold()
    needs_fallback = any(
        synset_data.get("pronunciation") is None and synset_data["name"].casefold() == normalized_resolved_term
        for pos_synsets in result.values()
        for synset_data in pos_synsets
    )

    if not needs_fallback:
        return definition_data

    fallback_ipa = get_pronunciation(resolved_term, accent)
    if not fallback_ipa:
        return definition_data

    fallback_pronunciation = PronunciationInfo(ipa=fallback_ipa, is_fallback=True)
    for pos_synsets in result.values():
        for synset_data in pos_synsets:
            if synset_data.get("pronunciation") is None and synset_data["name"].casefold() == normalized_resolved_term:
                synset_data["pronunciation"] = fallback_pronunciation

    return definition_data


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


def get_definition(term: str, wn_instance: wn.Wordnet, accent: str = "us") -> dict[str, Any]:
    """
    Gets the definition from WordNet, processes it, and prepares data structure.

    Args:
        term: The term to define.
        wn_instance: The initialized Wordnet instance.
        accent: The espeak-ng accent code.

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

        wn_pron = None
        for word in synset.words():
            if _normalize_lemma(word.lemma(data=False)).lower() == matched_lemma.lower():
                form = word.lemma(data=True)
                wn_pron = _pick_pronunciation(form.pronunciations(), accent)
                break

        related_lemmas = _extract_related_lemmas(synset, matched_lemma)

        synset_data: dict[str, Any] = {
            "name": matched_lemma,
            "definition": synset.definition() or "No definition available.",
            "examples": synset.examples() or [],
            "pronunciation": wn_pron,
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
        The pronunciation in IPA format without wrapper slashes, or None if espeak-ng fails.
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
            return ipa_pronunciation.strip("/")

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
    print("Copyright 2016-2026 Mufeed Ali")
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


def get_wn_instance() -> wn.Wordnet | None:
    utils.log_info("Initializing WordNet...")
    try:
        wn_instance = wn.Wordnet(lexicon=WN_DB_VERSION)
        utils.log_info(f"WordNet instance ({WN_DB_VERSION}) created and ready.")
        return wn_instance
    except (wn.Error, wn.DatabaseError) as e:
        utils.log_error(f"WordNet initialization failed: {e}")
        return None
    except Exception as e:
        utils.log_error(f"Unexpected error during WordNet initialization: {e}")
        return None


def get_wn_wordlist(wn_instance: wn.Wordnet, on_complete: Callable[[list[str]], None]):
    def fetch():
        try:
            with WN_DATABASE_LOCK:
                lemmas = wn_instance.lemmas()
            utils.log_info(f"WordNet wordlist fetched ({len(lemmas)} lemmas).")
            on_complete(lemmas)
        except Exception as e:
            utils.log_error(f"Error fetching WordNet wordlist: {e}")
            on_complete([])

    utils.log_info("Fetching WordNet wordlist...")
    threading.Thread(target=fetch, daemon=True).start()


def format_output(text: str, wn_instance: wn.Wordnet, accent: str = "us") -> dict[str, Any] | None:
    """
    Determines colors, handles special commands (fortune, exit), and fetches definitions.

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


def read_term(text: str, speed: int = 120, accent: str = "us", ipa: str | None = None) -> None:
    """
    Uses espeak-ng to speak the given text aloud.

    Args:
        text: The text to speak.
        speed: Speaking speed (words per minute).
        accent: The espeak-ng accent code.
        ipa: The IPA string to use for pronunciation (if available).
    """
    if ipa:
        phoneme_input = ipa_to_espeak(ipa)
    else:
        phoneme_input = text

    try:
        subprocess.run(
            ["espeak-ng", "-s", str(speed), "-v", f"en-{accent}", phoneme_input],
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
