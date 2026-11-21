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
from decimal import Decimal, InvalidOperation
from pathlib import Path

from bs4 import BeautifulSoup
from parse_html import parse_html
from schema_ecommerce_validate import validate

_HIDDEN_CLASSES = {"sr-only", "screen-reader-text", "screen-reader-only", "visually-hidden", "visuallyhidden",
                   "hidden", "d-none", "opacity-0"}
_ISO_CURRENCY = re.compile(r"\b[A-Z]{3}\b")
_PRICE_TEXT = re.compile(r"(?<![\w.,])(?:[$€£¥]\s*)?(\d+(?:\.\d{1,2})?)(?:\s+([A-Z]{3}))?(?![\w.,])", re.I)
_CSS_NUMBER = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$", re.I)
_AVAILABILITY = {
    "InStock": ("in stock", "available now", "available to order", "ships now"),
    "OutOfStock": ("out of stock", "sold out", "unavailable"),
    "PreOrder": ("preorder", "pre-order", "pre order"),
    "BackOrder": ("backorder", "back-order", "back order"),
}
_NEGATED_AVAILABILITY = re.compile(
    r"\b(?:no\s+longer\s+|not\s+(?:(?:currently|yet)\s+)?)"
    r"(?:in stock|available(?: now| to order)?|out of stock|sold out|unavailable)\b"
)
_PLACEHOLDER_VARIANT = re.compile(r"^(?:choose|select|please select)(?:\s+(?:a|an|your))?\b", re.I)


def _has_zero_opacity(style: str) -> bool:
    for declaration in style.split(";"):
        property_name, separator, raw_value = declaration.partition(":")
        if not separator or property_name.strip().lower() != "opacity":
            continue
        value = re.sub(r"\s*!important\s*$", "", raw_value.strip(), flags=re.I)
        if _CSS_NUMBER.fullmatch(value):
            try:
                if Decimal(value) == 0:
                    return True
            except InvalidOperation:
                continue
    return False


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
        if ("display:none" in style or "visibility:hidden" in style
                or _has_zero_opacity(str(parent.get("style", "")))):
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
    ambiguous_currency_symbol = False
    for element in soup.find_all(attrs={"itemprop": True}):
        if not _visible(element):
            continue
        props = element.get("itemprop", [])
        props = {p.lower() for p in (props if isinstance(props, list) else str(props).split())}
        text = element.get_text(" ", strip=True)
        # Attributes on meta/data elements describe markup, not rendered text.
        if not text:
            continue
        if "price" in props:
            # Commas are locale-dependent (decimal or grouping separator), so
            # leave them unresolved rather than manufacturing another amount.
            numeric = re.findall(r"(?<![\d,.])\d+(?:\.\d{1,2})?(?![\d,.])", text)
            if len(numeric) == 1:
                prices.append(numeric[0].replace(",", ""))
        if "pricecurrency" in props:
            codes = _ISO_CURRENCY.findall(text.upper())
            currencies.extend(codes)
            if not codes:
                ambiguous_currency_symbol = True

    # Some storefronts expose product facts through explicit UI test hooks
    # instead of microdata. Only the rendered text of these narrowly named,
    # visible markers is evidence; data attributes and structured data are not.
    for element in soup.find_all(attrs={"data-test": True}):
        if not _visible(element):
            continue
        marker = str(element.get("data-test", "")).strip().casefold()
        text = " ".join(str(node).strip() for node in element.find_all(string=True)
                        if str(node).strip() and _visible(node.parent))
        if not text:
            continue
        if marker == "product-price-display-price":
            matches = list(_PRICE_TEXT.finditer(text))
            if matches:
                prices.extend(match.group(1) for match in matches)
                for match in matches:
                    if match.group(2):
                        currencies.append(match.group(2).upper())
                    elif re.search(r"[$€£¥]", match.group(0)):
                        ambiguous_currency_symbol = True
        elif marker == "product-overview-availability":
            availability_text.append(text)
    selected_values: list[str] = []
    selected_labels: list[str] = []
    for option in soup.select("select option[selected]"):
        if _visible(option):
            selected_label = option.get_text(" ", strip=True)
            if selected_label and not _PLACEHOLDER_VARIANT.match(selected_label):
                selected_labels.append(selected_label)
                value = str(option.get("value", "")).strip()
                if value:
                    selected_values.append(value)
    selected_variant = _one(selected_labels)

    # Without microdata, inspect only one explicit visible Offer scope. This
    # bounded text fallback avoids borrowing prices from recommendations or
    # unrelated page content.
    if not prices:
        offer_scopes = [el for el in soup.find_all(True) if _visible(el) and
                        ("offers" in {str(x).lower() for x in ((el.get("itemprop", []) or [])
                                                                  if isinstance(el.get("itemprop", []), list)
                                                                  else str(el.get("itemprop", "")).split())}
                         or "offer" in str(el.get("itemtype", "")).lower())]
        if len(offer_scopes) == 1:
            text = " ".join(str(node).strip() for node in offer_scopes[0].find_all(string=True)
                            if str(node).strip() and _visible(node.parent))
            matches = list(_PRICE_TEXT.finditer(text))
            if len(matches) == 1:
                match = matches[0]
                price_label = re.search(r"\bprice\b", text[max(0, match.start() - 32):match.start()], re.I)
                explicit_currency = bool(match.group(2) or re.search(r"[$€£¥]", match.group(0)))
                if price_label or explicit_currency:
                    prices.append(match.group(1))
                if match.group(2):
                    currencies.append(match.group(2).upper())
                elif re.search(r"[$€£¥]", match.group(0)):
                    ambiguous_currency_symbol = True

    availability_value = None
    if not availability_text:
        def tokens(element) -> set[str]:
            raw = element.get("itemprop", [])
            return {str(item).lower() for item in (raw if isinstance(raw, list) else str(raw).split())}

        product_scopes = [el for el in soup.find_all(True) if _visible(el) and
                          ("product" in tokens(el) or "product" in str(el.get("itemtype", "")).lower())]
        offer_scopes = [el for el in soup.find_all(True) if _visible(el) and
                        ("offers" in tokens(el) or "offer" in str(el.get("itemtype", "")).lower())]
        selected_product_scopes = []
        if identity["status"] == "available":
            for scope in product_scopes:
                names = [node.get_text(" ", strip=True) for node in scope.find_all(attrs={"itemprop": True})
                         if "name" in tokens(node) and _visible(node)]
                headings_in_scope = [node.get_text(" ", strip=True) for node in scope.find_all("h1") if _visible(node)]
                if any(name.casefold() == identity["value"].casefold() for name in names + headings_in_scope):
                    selected_product_scopes.append(scope)

        if len(selected_product_scopes) == 1:
            product_scope = selected_product_scopes[0]
            associated_offers = [scope for scope in offer_scopes if scope is product_scope or product_scope in scope.parents]
            scopes = associated_offers or [product_scope]
        elif product_scopes:
            # A structured Product scope exists, but visible identity did not
            # select one. Do not borrow availability from a sibling product.
            scopes = []
            availability_value = "ambiguous" if len(selected_product_scopes) > 1 else None
        elif len(offer_scopes) == 1:
            scopes = offer_scopes
        elif len(offer_scopes) > 1:
            scopes = []
            availability_value = "ambiguous"
        else:
            scopes = []

        scoped_text = [str(text).strip() for scope in scopes for text in scope.find_all(string=True)
                       if text.strip() and _visible(text.parent)]
        availability_text.extend(scoped_text)

    if availability_value != "ambiguous" and availability_text:
        visible_text = " ".join(availability_text).lower()
        if _NEGATED_AVAILABILITY.search(visible_text):
            availability_value = "ambiguous"
        else:
            availability_hits = [key for key, phrases in _AVAILABILITY.items()
                                 if any(phrase in visible_text for phrase in phrases)]
            availability_value = availability_hits[0] if len(availability_hits) == 1 else (
                "ambiguous" if availability_hits else None
            )
    availability = _fact(availability_value, "available") if availability_value not in (None, "ambiguous") else (
        _fact(None, "ambiguous") if availability_value == "ambiguous" else _fact()
    )
    return {
        "identity": identity,
        "amount": _one(prices),
        "currency": (_one(currencies) if currencies else
                      _fact(None, "ambiguous") if ambiguous_currency_symbol else _fact()),
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
        left, right = str(visible["value"]), str(schema_value)
        if evidence.startswith("Visible amount"):
            try:
                status = "match" if Decimal(left) == Decimal(right) else "conflict"
            except InvalidOperation:
                status = "conflict"
        else:
            status = "match" if left.casefold() == right.casefold() else "conflict"
    return {"status": status, "visible": visible["value"], "schema": schema_value, "evidence": evidence}


def check_page(html: str, page_url: str = "") -> dict:
    """Parse local HTML and compare visible facts to their associated schema entity."""
    parsed = parse_html(html, page_url or None)
    entities = parsed["schema"]
    products = [node for node in _walk(entities) if "Product" in _types(node)]
    visible = _visible_facts(html)

    selected = visible["selected_variant"]["value"] if visible["selected_variant"]["status"] == "available" else None
    soup = BeautifulSoup(html, "html.parser")
    selected_values = [str(option.get("value", "")).strip() for option in soup.select("select option[selected]")
                       if _visible(option) and str(option.get("value", "")).strip()
                       and not _PLACEHOLDER_VARIANT.match(option.get_text(" ", strip=True))]
    association_key = selected_values[0] if len(set(selected_values)) == 1 else None
    identity = visible["identity"]["value"] if visible["identity"]["status"] == "available" else None
    candidates = products
    variant_association_ambiguous = len(set(selected_values)) > 1
    if association_key:
        matched = [p for p in products if association_key.casefold() in {
            str(p.get("sku", "")).strip().casefold(), str(p.get("productID", "")).strip().casefold(),
        }]
        if matched:
            candidates = matched
            label_points_elsewhere = any(
                p is not matched[0] and isinstance(p.get("name"), str)
                and p["name"].strip().casefold() == str(selected or "").strip().casefold()
                for p in products
            ) if len(matched) == 1 else False
            variant_association_ambiguous = variant_association_ambiguous or label_points_elsewhere
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
        if isinstance(candidates[0].get("name"), str) and candidates[0]["name"].strip():
            schema_variant = candidates[0]["name"].strip()

    comparisons = {}
    schema_for = {"identity": schema_identity, "selected_variant": schema_variant, **schema_values}
    for field in ("identity", "selected_variant", "amount", "currency", "availability"):
        if variant_association_ambiguous or len(candidates) > 1 or (len(candidates) == 1 and len(offers) > 1):
            comparisons[field] = {"status": "ambiguous", "visible": visible[field]["value"], "schema": None,
                                  "evidence": "Multiple Product or Offer candidates have no unambiguous visible identity."}
        elif not candidates and products:
            comparisons[field] = {"status": "ambiguous", "visible": visible[field]["value"], "schema": None,
                                  "evidence": "Visible identity does not identify a Product in the structured data."}
        else:
            evidence = ("Visible product identity compared with the associated Product or ProductGroup."
                        if field == "identity" else
                        "Visible selected option label compared with the associated variant display name."
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
