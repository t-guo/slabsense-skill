#!/usr/bin/env python3
"""Fetch or parse PriceCharting pages for SlabSense comps and population data."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


USER_AGENT = "Mozilla/5.0 SlabSense/0.2"


def slugify(value: str) -> str:
    value = html.unescape(value).lower()
    value = re.sub(r"\[[^\]]+\]", " ", value)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def guess_price_url(set_name: str, card_title: str, card_number: str = "") -> str:
    card = " ".join(part for part in (card_title, card_number) if part)
    return f"https://www.pricecharting.com/game/pokemon-{slugify(set_name)}/{slugify(card)}"


def guess_pop_url(set_name: str, card_title: str, card_number: str = "") -> str:
    return guess_price_url(set_name, card_title, card_number).replace("/game/", "/pop/item/")


def fetch(url: str, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def text_lines(raw_html: str) -> list[str]:
    text = re.sub(r"<script\b.*?</script>", " ", raw_html, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", "\n", text)
    return [re.sub(r"\s+", " ", html.unescape(line)).strip() for line in text.splitlines() if line.strip()]


def money(value: str) -> float | None:
    match = re.search(r"\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)", value)
    return float(match.group(1).replace(",", "")) if match else None


def parse_population(raw_html: str) -> dict[str, Any]:
    rows: dict[str, dict[str, Any]] = {}
    total_psa = None
    total_all = None
    for line in text_lines(raw_html):
        match = re.fullmatch(r"(\d{1,2})\s+([\d,]+|-)\s+([\d,]+|-)\s+([\d,]+)(?:\s+\$[\d,.]+)?", line)
        if match:
            grade, psa, cgc, total = match.groups()
            rows[grade] = {
                "psa": None if psa == "-" else int(psa.replace(",", "")),
                "cgc": None if cgc == "-" else int(cgc.replace(",", "")),
                "total": int(total.replace(",", "")),
            }
            continue
        total = re.fullmatch(r"Total\s+([\d,]+|-)\s+([\d,]+|-)\s+([\d,]+)", line)
        if total:
            psa, _cgc, all_total = total.groups()
            total_psa = None if psa == "-" else int(psa.replace(",", ""))
            total_all = int(all_total.replace(",", ""))
    return {
        "population_by_grade": rows,
        "psa_population_total": total_psa,
        "population_total": total_all,
        "psa_population_source": "PriceCharting population report; data from PSA and CGC",
    }


def parse_price_guide(raw_html: str) -> dict[str, float]:
    prices: dict[str, float] = {}
    for line in text_lines(raw_html):
        match = re.fullmatch(r"(Ungraded|Grade \d+(?:\.5)?|PSA 10|CGC 10|BGS 10(?: Black)?)\s+\$([\d,]+(?:\.\d+)?)", line)
        if match:
            prices[match.group(1)] = float(match.group(2).replace(",", ""))
    return prices


def parse_sales(raw_html: str, grade: float | None = None, limit: int = 12) -> list[dict[str, Any]]:
    lines = text_lines(raw_html)
    sales: list[dict[str, Any]] = []
    grade_pattern = None
    if grade is not None:
        grade_text = str(grade).removesuffix(".0")
        grade_pattern = re.compile(rf"\b(PSA|CGC|BGS|SGC)\s*{re.escape(grade_text)}\b", re.I)
    for index, line in enumerate(lines):
        if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", line):
            continue
        window = " ".join(lines[index + 1 : index + 8])
        price_match = re.search(r"\[eBay\]|\[Goldin\]", window)
        price = money(window[price_match.end() :] if price_match else window)
        if price is None:
            continue
        title = re.sub(r"\s+", " ", window.split("[eBay]")[0].split("[Goldin]")[0]).strip()
        if grade_pattern and not grade_pattern.search(title):
            continue
        sales.append(
            {
                "sold_date": line,
                "title": title,
                "sold_price": price,
                "source": "PriceCharting",
                "confidence": "medium",
            }
        )
        if len(sales) >= limit:
            break
    return sales


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse PriceCharting price/population pages.")
    parser.add_argument("--url")
    parser.add_argument("--html-file", type=Path)
    parser.add_argument("--set")
    parser.add_argument("--card-title")
    parser.add_argument("--card-number", default="")
    parser.add_argument("--grade", type=float)
    parser.add_argument("--kind", choices=("price", "pop"), default="price")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.html_file:
        raw = args.html_file.read_text(encoding="utf-8")
        url = args.url or ""
    else:
        if args.url:
            url = args.url
        elif args.set and args.card_title:
            url = guess_pop_url(args.set, args.card_title, args.card_number) if args.kind == "pop" else guess_price_url(args.set, args.card_title, args.card_number)
        else:
            raise SystemExit("--url or --set/--card-title is required")
        raw = fetch(url)

    payload = {"url": url}
    if args.kind == "pop":
        payload.update(parse_population(raw))
    else:
        payload["price_guide"] = parse_price_guide(raw)
        payload["sales"] = parse_sales(raw, args.grade)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
