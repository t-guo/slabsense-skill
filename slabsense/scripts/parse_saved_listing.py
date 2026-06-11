#!/usr/bin/env python3
"""Parse saved marketplace HTML into SlabSense listing JSON.

This script is for offline debugging of HTML captured by a browser or curl. It
does not fetch marketplace URLs and is not the normal SlabSense import path.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from canonicalize import canonicalize_title


class ListingMetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.title_parts: list[str] = []
        self.json_ld_blocks: list[str] = []
        self._in_title = False
        self._script_type = ""
        self._script_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key.lower(): value or "" for key, value in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = attr.get("property") or attr.get("name")
            content = attr.get("content")
            if key and content:
                self.meta[key.lower()] = content.strip()
        elif tag == "script":
            self._script_type = attr.get("type", "").lower()
            self._script_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        if self._script_type == "application/ld+json":
            self._script_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            if self._script_type == "application/ld+json" and self._script_parts:
                self.json_ld_blocks.append("".join(self._script_parts).strip())
            self._script_type = ""
            self._script_parts = []

    @property
    def title(self) -> str:
        return clean_text(" ".join(self.title_parts))


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def money_to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    match = re.search(r"\d+(?:,\d{3})*(?:\.\d+)?", str(value))
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def iter_json_objects(raw: str) -> list[Any]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if isinstance(parsed, list):
        return parsed
    return [parsed]


def find_product_json(parser: ListingMetadataParser) -> dict[str, Any]:
    for block in parser.json_ld_blocks:
        for obj in iter_json_objects(block):
            candidates = obj.get("@graph", []) if isinstance(obj, dict) else []
            if isinstance(obj, dict):
                candidates = [obj, *candidates]
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                kind = candidate.get("@type")
                if kind == "Product" or (isinstance(kind, list) and "Product" in kind):
                    return candidate
    return {}


def first_string(value: Any) -> str:
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, list):
        for item in value:
            text = first_string(item)
            if text:
                return text
    if isinstance(value, dict):
        for key in ("url", "contentUrl"):
            text = first_string(value.get(key))
            if text:
                return text
    return ""


def extract_price(product: dict[str, Any], meta: dict[str, str]) -> float | None:
    for key in ("product:price:amount", "og:price:amount"):
        price = money_to_float(meta.get(key))
        if price is not None:
            return price

    offers = product.get("offers") if product else None
    if isinstance(offers, list):
        offers = offers[0] if offers else None
    if isinstance(offers, dict):
        for key in ("price", "lowPrice", "highPrice"):
            price = money_to_float(offers.get(key))
            if price is not None:
                return price
    return None


def infer_grade(title: str) -> tuple[str, float | None]:
    match = re.search(r"\b(PSA|CGC|BGS|SGC)\s*(?:GEM\s*MT|MINT|NM-MT|MT)?\s*(\d+(?:\.\d)?)\b", title, re.I)
    if not match:
        return "", None
    return match.group(1).upper(), float(match.group(2))


def normalize_card_name(title: str) -> str:
    title = re.sub(r"\s*\|\s*eBay\s*$", "", title, flags=re.I)
    title = re.sub(r"\bPSA\s*(?:GEM\s*MT|MINT|NM-MT|MT)?\s*\d+(?:\.\d)?\b", "", title, flags=re.I)
    title = re.sub(r"\b(CG[C]?|BGS|SGC)\s*\d+(?:\.\d)?\b", "", title, flags=re.I)
    title = re.sub(r"\bPokemon\s+TCG\b", "Pokemon", title, flags=re.I)
    return clean_text(title)


def blocked_reason(html: str, parser: ListingMetadataParser) -> str:
    lowered = html.lower()
    if "something went wrong on our end" in lowered and "error page | ebay" in lowered:
        return "eBay returned a generic marketplace error page."
    if "robot check" in lowered or "captcha" in lowered:
        return "Marketplace bot protection blocked the request."
    if parser.title.lower().startswith("error page"):
        return f"Marketplace returned an error page: {parser.title}."
    return ""


def parse_listing(html: str, url: str) -> tuple[dict[str, Any], list[str]]:
    parser = ListingMetadataParser()
    parser.feed(html)

    reason = blocked_reason(html, parser)
    if reason:
        return (
            {
                "listing_url": url,
                "extraction_status": "blocked",
                "listing_notes": reason,
                "photo_quality": "unknown",
                "buyer_intent": "unknown",
            },
            [reason],
        )

    product = find_product_json(parser)
    title = clean_text(
        product.get("name")
        or parser.meta.get("og:title")
        or parser.meta.get("twitter:title")
        or parser.title
    )
    price = extract_price(product, parser.meta)
    grading_company, grade = infer_grade(title)
    canonical = canonicalize_title(title, grading_company, grade)

    image = first_string(product.get("image")) or parser.meta.get("og:image", "")
    notes = [f"Listing title: {title}" if title else "Listing title was not exposed."]
    if image:
        notes.append("At least one listing image URL was exposed in page metadata; inspect front/back photos manually.")

    warnings: list[str] = []
    if not title:
        warnings.append("listing title was not found")
    if price is None:
        warnings.append("asking price was not found")
    if grade is None:
        warnings.append("grade was not found in the listing title")

    listing: dict[str, Any] = {
        "card_name": (canonical.get("canonical_card_name") or normalize_card_name(title)) if title else "",
        "card_title": canonical.get("card_title", ""),
        "card_number": canonical.get("card_number", ""),
        "card_number_full": canonical.get("card_number_full", ""),
        "set": canonical.get("set", ""),
        "year": canonical.get("year"),
        "language": canonical.get("language", ""),
        "grading_company": grading_company,
        "grade": grade,
        "asking_price": price,
        "listing_url": url,
        "listing_notes": " ".join(notes),
        "buyer_intent": "unknown",
        "front_image_notes": "",
        "back_image_notes": "",
        "photo_quality": "unknown",
        "extraction_status": "ok" if not warnings else "partial",
        "extraction_warnings": warnings,
    }
    if image:
        listing["image_url"] = image
    return listing, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse saved marketplace HTML into SlabSense listing JSON.")
    parser.add_argument("html_file", type=Path)
    parser.add_argument("--url", default="", help="Original listing URL to include in output.")
    parser.add_argument("--output", "-o", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    html = args.html_file.read_text(encoding="utf-8")

    listing, warnings = parse_listing(html, args.url)
    if listing.get("extraction_status") == "blocked":
        print(listing["listing_notes"], file=sys.stderr)
        return 3

    payload = json.dumps(listing, indent=2 if args.pretty else None)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)

    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
