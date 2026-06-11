#!/usr/bin/env python3
"""Canonicalize messy Pokemon slab listing titles."""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any


SET_ALIASES = (
    ("ex dragon frontiers", "EX Dragon Frontiers"),
    ("dragon frontiers", "EX Dragon Frontiers"),
    ("crown zenith", "Crown Zenith"),
    ("shining fates", "Shining Fates"),
    ("celebrations classic collection", "Celebrations Classic Collection"),
    ("classic collection", "Celebrations Classic Collection"),
    ("celebrations", "Celebrations"),
    ("evolving skies", "Evolving Skies"),
    ("hidden fates", "Hidden Fates"),
    ("pokemon 151", "Pokemon 151"),
    ("paldea evolved", "Paldea Evolved"),
    ("obsidian flames", "Obsidian Flames"),
    ("twilight masquerade", "Twilight Masquerade"),
    ("surging sparks", "Surging Sparks"),
    ("prismatic evolutions", "Prismatic Evolutions"),
    ("base set", "Base Set"),
)

LANGUAGES = {
    "english": "English",
    "eng": "English",
    "japanese": "Japanese",
    "jpn": "Japanese",
    "jp": "Japanese",
    "korean": "Korean",
    "chinese": "Chinese",
}

NOISE_PATTERNS = (
    r"\bnew slab\b",
    r"\bnew cert\b",
    r"\bfresh slab\b",
    r"\bpop\s*\d+\b",
    r"\blow pop\b",
    r"\bhot\b",
    r"\brare\b",
    r"\binvest\b",
    r"\bmint\b",
    r"\bgem\s*mt\b",
    r"\bholo(?:graphic)?\b",
    r"\bfoil\b",
    r"\bpokemon\s+tcg\b",
    r"\bpokemon\b",
    r"\bcard\b",
    r"\bgraded\b",
    r"\bsecret\b",
    r"\bsecret rare\b",
    r"\billustration rare\b",
    r"\bspecial illustration rare\b",
)


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def title_case_name(value: str) -> str:
    keep_upper = {"v", "vmax", "vstar", "ex", "gx", "lv.x"}
    words = []
    for word in value.split():
        lower = word.lower()
        if lower in keep_upper:
            words.append(lower.upper())
        elif re.fullmatch(r"[A-Z0-9#/-]+", word) and any(char.isdigit() for char in word):
            words.append(word.upper())
        else:
            words.append(word[:1].upper() + word[1:].lower())
    return clean_text(" ".join(words))


def normalize_card_title(value: str) -> str:
    value = title_case_name(value)
    match = re.fullmatch(r"Gold Star (.+)", value, flags=re.I)
    if match:
        return clean_text(f"{match.group(1)} Gold Star")
    return value


def strip_market_suffix(title: str) -> str:
    title = re.sub(r"\s*\|\s*eBay\s*$", "", title, flags=re.I)
    title = re.sub(r"\s*-\s*eBay\s*$", "", title, flags=re.I)
    return title


def extract_grading(title: str) -> tuple[str, float | None]:
    match = re.search(r"\b(PSA|CGC|BGS|SGC)\s*(?:GEM\s*MT|MINT|NM-MT|MT)?\s*(\d+(?:\.\d)?)\b", title, re.I)
    if not match:
        return "", None
    grade = float(match.group(2))
    return match.group(1).upper(), int(grade) if grade.is_integer() else grade


def extract_year(title: str) -> int | None:
    match = re.search(r"\b(19[5-9]\d|20[0-3]\d)\b", title)
    return int(match.group(1)) if match else None


def extract_card_number(title: str) -> str:
    patterns = (
        r"(?:#|No\.?\s*)\s*([A-Z]{0,4}\d+[A-Z]?/[A-Z]{0,4}\d+[A-Z]?)\b",
        r"\b([A-Z]{1,4}\d+[A-Z]?/[A-Z]{0,4}\d+[A-Z]?)\b",
        r"(?:#|No\.?\s*)\s*([A-Z]{0,4}\d+[A-Z]?)\b",
        r"\b([A-Z]{1,4}\d+[A-Z]?)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, title, re.I)
        if match:
            return match.group(1).upper()
    return ""


def comp_card_number(card_number: str) -> str:
    if "/" not in card_number:
        return card_number
    return card_number.split("/", 1)[0]


def extract_language(title: str) -> str:
    lowered = title.lower()
    for token, label in LANGUAGES.items():
        if re.search(rf"\b{re.escape(token)}\b", lowered):
            return label
    return ""


def extract_set(title: str) -> str:
    lowered = title.lower()
    for token, label in SET_ALIASES:
        if token in lowered:
            return label
    return ""


def remove_known_parts(title: str, grading_company: str, grade: float | None, year: int | None, card_number: str) -> str:
    text = strip_market_suffix(title)
    if grading_company and grade is not None:
        text = re.sub(
            rf"\b{re.escape(grading_company)}\s*(?:GEM\s*MT|MINT|NM-MT|MT)?\s*{re.escape(str(grade).removesuffix('.0'))}(?:\.0)?\b",
            " ",
            text,
            flags=re.I,
        )
    if year:
        text = re.sub(rf"\b{year}\b", " ", text)
    if card_number:
        text = re.sub(rf"(?:#|No\.?\s*)?\s*{re.escape(card_number)}\b", " ", text, flags=re.I)
    for token, _label in SET_ALIASES:
        text = re.sub(re.escape(token), " ", text, flags=re.I)
    for token in LANGUAGES:
        text = re.sub(rf"\b{re.escape(token)}\b", " ", text, flags=re.I)
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.I)
    text = re.sub(r"\bSWSH\b", " ", text, flags=re.I)
    text = re.sub(r"\bSword\s*&\s*Shield\b", " ", text, flags=re.I)
    text = re.sub(r"[\[\]()/,:;]+", " ", text)
    text = re.sub(r"\s*[-–—]\s*", " ", text)
    return clean_text(text)


def canonicalize_title(title: str, grading_company: str = "", grade: float | None = None) -> dict[str, Any]:
    raw_title = clean_text(title)
    inferred_company, inferred_grade = extract_grading(raw_title)
    grading_company = grading_company or inferred_company
    grade = grade if grade is not None else inferred_grade
    year = extract_year(raw_title)
    card_number_full = extract_card_number(raw_title)
    card_number = comp_card_number(card_number_full)
    language = extract_language(raw_title)
    set_name = extract_set(raw_title)
    name = normalize_card_title(remove_known_parts(raw_title, grading_company, grade, year, card_number_full))

    parts = [name]
    if card_number:
        parts.append(f"#{card_number}")
    if set_name:
        parts.append(set_name)
    if language:
        parts.append(language)
    if grading_company and grade is not None:
        grade_text = str(grade).removesuffix(".0")
        parts.append(f"{grading_company} {grade_text}")

    canonical = clean_text(" ".join(part for part in parts if part))
    return {
        "canonical_card_name": canonical,
        "card_title": name,
        "card_number": card_number,
        "card_number_full": card_number_full,
        "set": set_name,
        "year": year,
        "language": language,
        "grading_company": grading_company,
        "grade": grade,
        "raw_title": raw_title,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Canonicalize a Pokemon slab listing title.")
    parser.add_argument("title", nargs="?", default="")
    parser.add_argument("--grading-company", default="")
    parser.add_argument("--grade", type=float)
    parser.add_argument("--json", action="store_true", help="Read JSON from stdin and enrich it.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.json:
        listing = json.load(sys.stdin)
        title = str(listing.get("raw_title") or listing.get("card_name") or listing.get("listing_notes") or "")
        fields = canonicalize_title(title, str(listing.get("grading_company") or ""), listing.get("grade"))
        listing.update({key: value for key, value in fields.items() if value not in ("", None)})
        print(json.dumps(listing, indent=2))
        return 0

    print(json.dumps(canonicalize_title(args.title, args.grading_company, args.grade), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
