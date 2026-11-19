#!/usr/bin/env python3
"""Compare conservative visible product facts with Product/Offer JSON-LD.

``check_page`` returns ``schema_validation`` (the existing validator result),
``visible_facts`` (each fact has a status and optional value), ``comparisons``
(each field has status, visible/schema values, and evidence), and parser
``diagnostics``. The CLI reads a local HTML file or stdin and never fetches.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

from parse_html import parse_html
from schema_ecommerce_validate import validate


_HIDDEN_CLASSES = {"sr-only", "screen-reader-text", "screen-reader-only", "visually-hidden", "visuallyhidden"}
_AVAILABILITY = {
    "InStock": ("in stock", "available now", "available to order", "ships now"),
    "OutOfStock": ("out of stock", "sold out", "unavailable"),
    "PreOrder": ("preorder", "pre-order", "pre order"),
    "BackOrder": ("backorder", "back-order", "back order"),
}


def _visible(element) -> bool:
    for parent in [element, *element.parents]:
        if getattr(parent, "name", None) in {"script", "style", "template", "noscript"}:
            return False
        if not getattr(parent, "attrs", None):
            continue
        if parent.has_attr("hidden") or str(parent.get("aria-hidden", "")).lower() == "true":
            return False
        classes = set(parent.get("class", []) or [])
        if classes & _HIDDEN_CLASSES:
            return False
        style = re.sub(r"\s+", "", str(parent.get("style", "")).lower())
        if "display:none" in style or "visibility:hidden" in style:
            return False
    return True


def _fact(value=None, status="unavailable") -> dict:
    return {"status": status, "value": value}


def _one(values: list[str]) -> dict:
    values = list(dict.fromkeys(v.strip() for v in values if v and v.strip()))
    if len(values) == 1:
        return _fact(values[0], "available")
    if len(values) > 1:
        return _fact(None, "ambiguous")
    return _fact()


def _visible_facts(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    headings = [h.get_text(" ", strip=True) for h in soup.find_all("h1") if _visible(h)]
    identity = _one(headings)

    prices: list[str] = []
    currencies: list[str] = []
    availability_text: list[str] = []
    skus: list[str] = []
    for element in soup.find_all(attrs={"itemprop": True}):
        if not _visible(element):
            continue
        props = element.get("itemprop", [])
        props = {p.lower() for p in (props if isinstance(props, list) else str(props).split())}
        content = str(element.get("content", "")).strip()
        text = element.get_text(" ", strip=True)
        if "price" in props:
            candidate = content or text
            numeric = re.findall(r"(?<!\d)\d+(?:[.,]\d{1,2})?(?!\d)", candidate)
            if len(numeric) == 1:
                prices.append(numeric[0].replace(",", ""))
        if "pricecurrency" in props:
            currencies.append(content or text)
        if "sku" in props or "productid" in props:
            skus.append(content or text)
        if "availability" in props:
            availability_text.append(content or text)

    for option in soup.select("select option[selected]"):
        if _visible(option):
            selected = str(option.get("value", "")).strip()
            if selected:
                skus.append(selected)
    selected_variant = _one(skus)

    availability_value = None
    if availability_text:
        for text in availability_text:
            token = text.rsplit("/", 1)[-1].strip().lower()
            for canonical, phrases in _AVAILABILITY.items():
                if token == canonical.lower() or any(phrase in token for phrase in phrases):
                    if availability_value and availability_value != canonical:
                        availability_value = "ambiguous"
                        break
                    availability_value = canonical
    else:
        availability_text = [str(text).strip() for text in soup.find_all(string=True)
                             if text.strip() and _visible(text.parent)]
        visible_text = " ".join(availability_text).lower()
        availability_hits = [key for key, phrases in _AVAILABILITY.items() if any(p in visible_text for p in phrases)]
        availability_value = availability_hits[0] if len(availability_hits) == 1 else (
            "ambiguous" if availability_hits else None
        )
    availability = _fact(availability_value, "available") if availability_value not in (None, "ambiguous") else (
        _fact(None, "ambiguous") if availability_value == "ambiguous" else _fact()
    )
    return {
        "identity": identity,
        "amount": _one(prices),
        "currency": _one(currencies),
        "availability": availability,
        "selected_variant": selected_variant,
    }


def _types(entity) -> set[str]:
    kinds = entity.get("@type", []) if isinstance(entity, dict) else []
    kinds = kinds if isinstance(kinds, list) else [kinds]
    return {str(k).rsplit("/", 1)[-1] for k in kinds if isinstance(k, str)}


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _field_values(offer: dict) -> dict:
    availability = offer.get("availability")
    if isinstance(availability, str):
        availability = availability.rsplit("/", 1)[-1].lower()
        availability = {"instock": "InStock", "outofstock": "OutOfStock", "soldout": "OutOfStock",
                        "preorder": "PreOrder", "backorder": "BackOrder"}.get(availability)
    price = offer.get("price")
    amount = str(price).strip() if isinstance(price, (int, float, str)) and not isinstance(price, bool) else None
    currency = offer.get("priceCurrency")
    return {"amount": amount, "currency": currency if isinstance(currency, str) else None,
            "availability": availability}


def _comparison(visible: dict, schema_value, evidence: str) -> dict:
    if visible["status"] != "available":
        status = visible["status"]
    elif schema_value is None:
        status = "unavailable"
    else:
        status = "match" if str(visible["value"]).casefold() == str(schema_value).casefold() else "conflict"
    return {"status": status, "visible": visible["value"], "schema": schema_value, "evidence": evidence}


def check_page(html: str, page_url: str = "") -> dict:
    """Parse local HTML and compare visible facts to their associated schema entity."""
    parsed = parse_html(html, page_url or None)
    entities = parsed["schema"]
    products = [node for node in _walk(entities) if "Product" in _types(node)]
    visible = _visible_facts(html)

    selected = visible["selected_variant"]["value"] if visible["selected_variant"]["status"] == "available" else None
    identity = visible["identity"]["value"] if visible["identity"]["status"] == "available" else None
    candidates = products
    if selected:
        matched = [p for p in products if selected in {str(p.get("sku", "")), str(p.get("productID", ""))}]
        if matched:
            candidates = matched
        else:
            candidates = []
    elif identity:
        matched = [p for p in products if str(p.get("name", "")).strip().casefold() == identity.strip().casefold()]
        candidates = matched
    offers = []
    if len(candidates) == 1:
        value = candidates[0].get("offers")
        offers = [o for o in (value if isinstance(value, list) else [value]) if isinstance(o, dict) and "Offer" in _types(o)]
    schema_offer = offers[0] if len(candidates) == 1 and len(offers) == 1 else None
    schema_values = _field_values(schema_offer) if schema_offer else {"amount": None, "currency": None, "availability": None}
    schema_identity = None
    schema_variant = None
    if len(candidates) == 1:
        schema_identity = candidates[0].get("name") if isinstance(candidates[0].get("name"), str) else None
        if selected:
            # A visible variant belongs to its ProductGroup; the page heading
            # commonly names the group rather than the selected child Product.
            for group in (node for node in _walk(entities) if "ProductGroup" in _types(node)):
                if any(child is candidates[0] for child in _walk(group.get("hasVariant", []))):
                    if isinstance(group.get("name"), str):
                        schema_identity = group["name"]
                    break
        for key in ("sku", "productID"):
            raw_variant = candidates[0].get(key)
            if isinstance(raw_variant, str) and raw_variant.strip():
                schema_variant = raw_variant.strip()
                break

    comparisons = {}
    schema_for = {"identity": schema_identity, "selected_variant": schema_variant, **schema_values}
    for field in ("identity", "selected_variant", "amount", "currency", "availability"):
        if len(candidates) > 1 or (len(candidates) == 1 and len(offers) > 1):
            comparisons[field] = {"status": "ambiguous", "visible": visible[field]["value"], "schema": None,
                                  "evidence": "Multiple Product or Offer candidates have no unambiguous visible identity."}
        elif not candidates and products:
            comparisons[field] = {"status": "ambiguous", "visible": visible[field]["value"], "schema": None,
                                  "evidence": "Visible identity does not identify a Product in the structured data."}
        else:
            evidence = ("Visible product identity compared with the associated Product or ProductGroup."
                        if field == "identity" else
                        "Visible selected variant compared with the associated Product identifier."
                        if field == "selected_variant" else
                        f"Visible {field} compared with the associated Product Offer.")
            comparisons[field] = _comparison(visible[field], schema_for[field], evidence)
    if not products:
        comparisons = {field: _comparison(visible[field], None, "No Product entity was parsed.")
                       for field in ("identity", "selected_variant", "amount", "currency", "availability")}
    if schema_offer is None and len(candidates) == 1 and not offers:
        for field in ("amount", "currency", "availability"):
            comparisons[field] = {"status": "unavailable", "visible": visible[field]["value"], "schema": None,
                                  "evidence": "The selected Product has no single typed Offer."}

    return {
        "url": page_url,
        "visible_facts": visible,
        "schema_validation": validate(entities),
        "comparisons": comparisons,
        "diagnostics": {"schema_invalid": parsed["schema_invalid"], "hidden_text": parsed["hidden_text"]},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare visible ecommerce facts with Product JSON-LD.")
    parser.add_argument("source", nargs="?", default="-", help="Local HTML path, or - for stdin.")
    args = parser.parse_args(argv)
    try:
        html = sys.stdin.read() if args.source == "-" else Path(args.source).read_text(encoding="utf-8-sig")
        result = check_page(html)
    except OSError as exc:
        print(json.dumps({"error": f"cannot read local HTML: {exc}"}, indent=2))
        return 1
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
