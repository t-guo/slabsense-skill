#!/usr/bin/env python3
"""Deterministic SlabSense analyzer.

No network calls. No API keys. Input is a listing JSON plus optional comps CSV.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MAJOR_CARD_TERMS = (
    "charizard",
    "pikachu",
    "lugia",
    "mew",
    "mewtwo",
    "giratina",
    "gengar",
    "umbreon",
    "rayquaza",
    "gold star",
    "tag team",
    "alt art",
    "moonbreon",
)

CHASE_CARD_TERMS = (
    "gold star",
    "crystal",
    "shining",
    "alt art",
    "alternate art",
    "special illustration",
    "moonbreon",
)

CONDITION_RISK_TERMS = (
    "crease",
    "surface",
    "scratch",
    "whitening",
    "dent",
    "print line",
    "off center",
    "oc",
    "dark",
    "angled",
    "glare",
    "missing",
)

SELLER_RISK_TERMS = (
    "no return",
    "no returns",
    "cert mismatch",
    "stock photo",
    "poor feedback",
    "damaged slab",
)


@dataclass
class Comp:
    card_name: str
    grade: float | None
    sold_price: float
    sold_date: str
    source: str
    confidence: str
    notes: str


def load_listing(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except ValueError:
        return None


def load_comps(path: Path | None) -> list[Comp]:
    if not path:
        return []

    comps: list[Comp] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            price = parse_float(row.get("sold_price"))
            if price is None:
                continue
            comps.append(
                Comp(
                    card_name=row.get("card_name", ""),
                    grade=parse_float(row.get("grade")),
                    sold_price=price,
                    sold_date=row.get("sold_date", ""),
                    source=row.get("source", ""),
                    confidence=row.get("confidence", ""),
                    notes=row.get("notes", ""),
                )
            )
    return comps


def relevant_comps(listing: dict[str, Any], comps: list[Comp]) -> tuple[list[Comp], list[Comp]]:
    target_name = str(listing.get("card_name", "")).lower().strip()
    target_grade = parse_float(listing.get("grade"))
    same_grade: list[Comp] = []
    nearby_grade: list[Comp] = []

    for comp in comps:
        name_match = target_name and target_name in comp.card_name.lower()
        if not name_match or comp.grade is None or target_grade is None:
            continue
        if comp.grade == target_grade:
            same_grade.append(comp)
        elif abs(comp.grade - target_grade) <= 1:
            nearby_grade.append(comp)

    return same_grade, nearby_grade


def base_value_range(comps: list[Comp]) -> tuple[int, int] | tuple[None, None]:
    if not comps:
        return None, None
    prices = sorted(comp.sold_price for comp in comps)
    if len(prices) == 1:
        price = prices[0]
        return round(price * 0.9), round(price * 1.1)
    if len(prices) == 2:
        return round(min(prices) * 0.95), round(max(prices) * 1.05)

    midpoint = statistics.median(prices)
    spread = max(statistics.pstdev(prices), midpoint * 0.08)
    return round(max(min(prices), midpoint - spread)), round(min(max(prices), midpoint + spread))


def text_blob(listing: dict[str, Any]) -> str:
    fields = (
        "card_name",
        "card_title",
        "card_number",
        "set",
        "listing_notes",
        "front_image_notes",
        "back_image_notes",
        "photo_quality",
        "buyer_intent",
    )
    return " ".join(str(listing.get(field, "")) for field in fields).lower()


def psa_population(listing: dict[str, Any]) -> tuple[int | None, int | None, str]:
    grade_pop = parse_float(
        listing.get("psa_population_grade")
        or listing.get("psa_grade_population")
        or listing.get("psa_10_population")
    )
    total_pop = parse_float(listing.get("psa_population_total") or listing.get("psa_total_population"))
    source = str(listing.get("psa_population_source", "")).strip()
    return (
        int(grade_pop) if grade_pop is not None else None,
        int(total_pop) if total_pop is not None else None,
        source,
    )


def scarcity_premium_rates(listing: dict[str, Any], comp_count: int) -> tuple[float, float]:
    grade_pop, total_pop, pop_source = psa_population(listing)
    if grade_pop is None or not pop_source:
        return 0.0, 0.0

    blob = text_blob(listing)
    is_major = any(term in blob for term in MAJOR_CARD_TERMS)
    is_chase = any(term in blob for term in CHASE_CARD_TERMS)
    if not (is_major or is_chase):
        return 0.0, 0.0

    low_premium = 0.0
    high_premium = 0.0
    if grade_pop <= 100:
        low_premium += 0.10
        high_premium += 0.26
    elif grade_pop <= 500:
        low_premium += 0.06
        high_premium += 0.20
    elif grade_pop <= 2000:
        low_premium += 0.02
        high_premium += 0.10
    else:
        return 0.0, 0.0

    if total_pop is not None and total_pop > 0 and grade_pop / total_pop <= 0.2:
        low_premium += 0.01
        high_premium += 0.04

    year = parse_float(listing.get("year"))
    if year and year <= 2010 and is_chase:
        high_premium += 0.03

    if comp_count < 3:
        high_premium += 0.05

    return min(low_premium, 0.12), min(high_premium, 0.30)


def value_range(listing: dict[str, Any], comps: list[Comp]) -> tuple[int, int] | tuple[None, None]:
    low, high = base_value_range(comps)
    if low is None or high is None or len(comps) < 3:
        return low, high

    prices = sorted(comp.sold_price for comp in comps)
    midpoint = statistics.median(prices)
    low_premium, high_premium = scarcity_premium_rates(listing, len(comps))
    if low_premium == 0 and high_premium == 0:
        return low, high

    premium_low = round(midpoint * (1 + low_premium))
    premium_high = round(midpoint * (1 + high_premium))
    return max(low, premium_low), max(high, premium_high)


def missing_info(listing: dict[str, Any], comps: list[Comp]) -> list[str]:
    missing: list[str] = []
    for field, label in (
        ("cert_number", "PSA cert number"),
        ("front_image_notes", "front image observations"),
        ("back_image_notes", "back image observations"),
    ):
        if not str(listing.get(field, "")).strip():
            missing.append(label)
    if not comps:
        missing.append("relevant sold comps")
    if parse_float(listing.get("seller_feedback_count")) is None:
        missing.append("seller feedback data")
    if not str(listing.get("return_policy", "")).strip():
        missing.append("return policy")
    grade_pop, total_pop, pop_source = psa_population(listing)
    if grade_pop is None and total_pop is None:
        missing.append("PSA population data")
    elif not pop_source:
        missing.append("PSA population source")
    return missing


def investability(
    listing: dict[str, Any],
    same_grade: list[Comp],
    low: int | None,
    high: int | None,
    asking: float,
    liquidity: int,
) -> dict[str, Any]:
    blob = text_blob(listing)
    grade_pop, total_pop, pop_source = psa_population(listing)
    demand = 35
    scarcity = 35
    risks: list[str] = []
    thesis: list[str] = []

    if any(term in blob for term in MAJOR_CARD_TERMS):
        demand += 25
        thesis.append("popular Pokemon or established chase character")
    if any(term in blob for term in CHASE_CARD_TERMS):
        demand += 15
        thesis.append("recognized chase-card category")
    if len(same_grade) >= 5:
        demand += 10
        thesis.append("recent same-grade sales support liquidity")
    elif len(same_grade) <= 1:
        demand -= 5
        risks.append("thin recent same-grade sales history")

    year = parse_float(listing.get("year"))
    if year and year <= 2010:
        scarcity += 15
        thesis.append("older card with naturally lower surviving supply")
    if grade_pop is not None:
        if grade_pop <= 100:
            scarcity += 30
            thesis.append(f"low sourced grade population ({grade_pop})")
        elif grade_pop <= 500:
            scarcity += 18
            thesis.append(f"moderate sourced grade population ({grade_pop})")
        elif grade_pop <= 2000:
            scarcity += 8
        else:
            scarcity -= 12
            risks.append(f"high sourced grade population ({grade_pop})")
    else:
        scarcity -= 8
        risks.append("PSA grade population not sourced")

    if total_pop is not None and grade_pop is not None and total_pop > 0:
        grade_rate = grade_pop / total_pop
        if grade_rate <= 0.2:
            scarcity += 10
            thesis.append("low top-grade share versus total PSA population")
        elif grade_rate >= 0.55 and grade_pop > 1000:
            scarcity -= 8
            risks.append("large top-grade share reduces scarcity")

    premium = 0.0
    if low is not None and high is not None and asking:
        midpoint = (low + high) / 2
        premium = (asking - midpoint) / midpoint if midpoint else 0.0
        if premium > 0.25:
            risks.append("entry price is far above same-grade comp midpoint")
        elif premium > 0.1:
            risks.append("entry price is above same-grade comp midpoint")
        elif premium < -0.05:
            thesis.append("entry price is below same-grade comp midpoint")

    demand = max(0, min(100, demand))
    scarcity = max(0, min(100, scarcity))
    score_value = round(demand * 0.4 + scarcity * 0.35 + liquidity * 0.25)
    if premium > 0.25 and scarcity < 70:
        score_value -= 12
    score_value = max(0, min(100, score_value))
    hold_quality = "high" if score_value >= 75 else "medium" if score_value >= 50 else "low"

    if not thesis:
        thesis.append("investment case is not strongly supported by sourced demand or scarcity signals")

    return {
        "investability_score": score_value,
        "demand_score": demand,
        "scarcity_score": scarcity,
        "hold_quality": hold_quality,
        "psa_population_grade": grade_pop,
        "psa_population_total": total_pop,
        "psa_population_source": pop_source,
        "investment_thesis": thesis,
        "investment_risks": sorted(set(risks)),
    }


def score(listing: dict[str, Any], comps: list[Comp]) -> dict[str, Any]:
    asking = parse_float(listing.get("asking_price")) or 0
    same_grade, nearby_grade = relevant_comps(listing, comps)
    low, high = value_range(listing, same_grade)
    blob = text_blob(listing)
    miss = missing_info(listing, same_grade)

    liquidity = 45
    if any(term in blob for term in MAJOR_CARD_TERMS):
        liquidity += 20
    if len(same_grade) >= 3:
        liquidity += 15
    elif len(same_grade) == 0:
        liquidity -= 15
    grade = parse_float(listing.get("grade"))
    if grade == 10:
        liquidity += 10
    elif grade == 9 and "modern" in blob:
        liquidity -= 10
    elif grade is not None and grade <= 4 and "vintage" not in blob and "gold star" not in blob:
        liquidity -= 5
    liquidity = max(0, min(100, liquidity))
    investment = investability(listing, same_grade, low, high, asking, liquidity)

    regret = 35
    red_flags: list[str] = []
    if low is not None and high is not None and asking:
        midpoint = (low + high) / 2
        if asking > high * 1.1:
            regret += 25
            red_flags.append("asking price is materially above same-grade comps")
        elif asking > midpoint:
            regret += 10
        elif asking < low:
            regret -= 10

    if any(term in blob for term in CONDITION_RISK_TERMS):
        regret += 15
        red_flags.append("condition or photo-quality concern is present")
    if any(term in blob for term in SELLER_RISK_TERMS):
        regret += 15
        red_flags.append("seller/listing risk concern is present")
    seller_feedback = parse_float(listing.get("seller_feedback_count"))
    seller_positive = parse_float(listing.get("seller_positive_percent"))
    if seller_feedback is not None and seller_feedback < 50 and asking >= 1000:
        regret += 8
        red_flags.append("seller feedback count is low for a high-value slab")
    if seller_positive is not None and seller_positive < 98:
        regret += 10
        red_flags.append("seller positive feedback is below 98%")
    if len(miss) >= 3:
        regret += 10
    if listing.get("buyer_intent") == "personal_collection":
        regret -= 5
    if listing.get("buyer_intent") == "investment" and liquidity < 60:
        regret += 10
    regret = max(0, min(100, regret))

    confidence = 45 + min(len(same_grade), 4) * 8
    if str(listing.get("photo_quality", "")).lower() == "clear":
        confidence += 10
    elif str(listing.get("photo_quality", "")).lower() in {"poor", "mixed"}:
        confidence -= 8
    confidence -= min(len(miss), 4) * 4
    confidence = max(0, min(100, confidence))

    if low is None or high is None:
        verdict = "watch"
        suggested = 0
        downside = "medium"
    else:
        midpoint = (low + high) / 2
        if asking <= high and regret < 60 and confidence >= 55:
            verdict = "buy"
            suggested = round(midpoint * 0.93)
            downside = "low" if asking <= midpoint else "medium"
        elif asking > high * 1.15 or regret >= 75:
            verdict = "pass"
            suggested = round(midpoint * 0.8)
            downside = "high"
        else:
            verdict = "watch"
            suggested = round(midpoint * 0.85)
            downside = "medium"

    comp_summary = [
        {
            "sold_price": comp.sold_price,
            "sold_date": comp.sold_date,
            "source": comp.source,
            "confidence": comp.confidence or "high",
            "notes": comp.notes,
        }
        for comp in same_grade[:8]
    ]
    comp_sources_checked = [
        {
            "source": source,
            "status": "checked",
            "notes": "Provided comps CSV",
        }
        for source in sorted({comp.source for comp in comps if comp.source})
    ]
    nearby_context = [
        {
            "price": comp.sold_price,
            "sold_date": comp.sold_date,
            "source": comp.source,
            "type": "nearby grade sold comp",
            "grade": comp.grade,
            "confidence": comp.confidence or "low",
            "notes": comp.notes,
        }
        for comp in nearby_grade[:8]
    ]
    if nearby_grade and not same_grade:
        red_flags.append("only nearby-grade comps were found; value confidence is limited")

    return {
        "verdict": verdict,
        "deal_verdict": verdict,
        "hold_verdict": investment["hold_quality"],
        "fair_value_low": low or 0,
        "fair_value_high": high or 0,
        "suggested_offer": suggested,
        "expected_downside": downside,
        "liquidity_score": liquidity,
        **investment,
        "regret_risk_score": regret,
        "confidence": confidence / 100,
        "condition_notes": [
            note
            for note in (
                listing.get("front_image_notes", ""),
                listing.get("back_image_notes", ""),
            )
            if note
        ],
        "comp_sources_checked": comp_sources_checked,
        "comp_summary": comp_summary,
        "nearby_grade_or_active_ask_context": nearby_context,
        "red_flags": sorted(set(red_flags)),
        "missing_info": miss,
        "collector_summary": build_summary(listing, verdict, investment["hold_quality"], low, high, suggested, regret),
    }


def build_summary(
    listing: dict[str, Any],
    verdict: str,
    hold_quality: str,
    low: int | None,
    high: int | None,
    suggested: int,
    regret: int,
) -> str:
    card = listing.get("card_name", "This slab")
    asking = parse_float(listing.get("asking_price")) or 0
    if low is None or high is None:
        value_text = "No grounded fair-value range is available from same-grade comps."
    else:
        value_text = f"Estimated fair value is ${low:,}-${high:,}; suggested offer is ${suggested:,}."
    return (
        f"{card}: {verdict.upper()} at ${asking:,.0f}. "
        f"{value_text} Hold quality is {hold_quality}. Regret risk is {regret}/100."
    )


def render_text(result: dict[str, Any]) -> str:
    low = result.get("fair_value_low") or 0
    high = result.get("fair_value_high") or 0
    suggested = result.get("suggested_offer") or 0
    value_text = f"${low:,}-${high:,}" if low and high else "not available"
    offer_text = f"${suggested:,}" if suggested else "not available"
    lines = [
        result["collector_summary"],
        "",
        f"Deal verdict: {str(result['deal_verdict']).upper()}",
        f"Hold quality: {str(result['hold_verdict']).upper()}",
        f"Fair value: {value_text}",
        f"Suggested offer: {offer_text}",
        f"Liquidity / Investability / Regret: {result['liquidity_score']}/100 / {result['investability_score']}/100 / {result['regret_risk_score']}/100",
    ]
    if result.get("investment_thesis"):
        lines.extend(["", "Investment thesis:"])
        lines.extend(f"- {item}" for item in result["investment_thesis"])
    if result.get("red_flags"):
        lines.extend(["", "Red flags:"])
        lines.extend(f"- {item}" for item in result["red_flags"])
    if result.get("missing_info"):
        lines.extend(["", "Missing info:"])
        lines.extend(f"- {item}" for item in result["missing_info"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a PSA Pokemon slab deal locally.")
    parser.add_argument("listing", type=Path)
    parser.add_argument("--comps", type=Path)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--format", choices=("json", "text", "both"), default="json")
    args = parser.parse_args()

    listing = load_listing(args.listing)
    result = score(listing, load_comps(args.comps))
    output_format = "both" if args.pretty else args.format
    if output_format == "text":
        print(render_text(result))
    elif output_format == "both":
        print(render_text(result))
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
