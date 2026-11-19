"""Visible Product and Offer facts must be compared conservatively."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ecommerce_page_check import check_page  # noqa: E402


def page(body, schema):
    return (
        "<html><body>" + body
        + '<script type="application/ld+json">' + json.dumps(schema)
        + "</script></body></html>"
    )


def product(name="Trail Shoe", **offer):
    explicit_offers = offer.pop("offers", None)
    entity = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "image": "shoe.jpg",
        "offers": {"@type": "Offer", **offer},
    }
    if explicit_offers is not None:
        entity["offers"] = explicit_offers
    return entity


def test_matches_visible_offer_facts():
    html = page(
        '<h1>Trail Shoe</h1><div itemprop="offers" itemscope>'
        '<span itemprop="price" content="89.99">$89.99</span>'
        '<span itemprop="priceCurrency">USD</span>'
        '<p>In stock</p></div>',
        product(price="89.99", priceCurrency="USD", availability="https://schema.org/InStock"),
    )

    result = check_page(html)

    assert result["visible_facts"]["identity"] == {"status": "available", "value": "Trail Shoe"}
    assert result["visible_facts"]["amount"] == {"status": "available", "value": "89.99"}
    assert result["visible_facts"]["currency"] == {"status": "available", "value": "USD"}
    assert result["visible_facts"]["availability"] == {"status": "available", "value": "InStock"}
    assert all(result["comparisons"][key]["status"] == "match"
               for key in ("identity", "amount", "currency", "availability"))
    assert result["comparisons"]["selected_variant"]["status"] == "unavailable"
    assert result["schema_validation"]["findings"]


def test_reports_conflicting_price_currency_and_availability():
    html = page(
        '<h1>Trail Shoe</h1><div itemprop="offers"><span itemprop="price" content="99.00">$99.00</span>'
        '<span itemprop="priceCurrency">CAD</span><p>Out of stock</p></div>',
        product(price="89.00", priceCurrency="USD", availability="https://schema.org/InStock"),
    )

    result = check_page(html)

    assert result["comparisons"]["amount"]["status"] == "conflict"
    assert result["comparisons"]["currency"]["status"] == "conflict"
    assert result["comparisons"]["availability"]["status"] == "conflict"
    assert result["comparisons"]["amount"]["visible"] == "99.00"
    assert result["comparisons"]["amount"]["schema"] == "89.00"


def test_matches_variant_by_explicit_identity():
    blue = {
        "@type": "Product", "name": "Trail Shoe Blue 8", "sku": "BLUE-8",
        "offers": {"@type": "Offer", "price": "89.99", "priceCurrency": "USD"},
    }
    black = {
        "@type": "Product", "name": "Trail Shoe Black 8", "sku": "BLACK-8",
        "offers": {"@type": "Offer", "price": "99.99", "priceCurrency": "USD"},
    }
    schema = {"@context": "https://schema.org", "@type": "ProductGroup", "name": "Trail Shoe",
              "hasVariant": [blue, black]}
    html = page(
        '<h1>Trail Shoe</h1><label>Variant <select><option>Blue / 8</option>'
        '<option selected value="BLACK-8">Black / 8</option></select></label>'
        '<meta itemprop="sku" content="BLACK-8">'
        '<span itemprop="price" content="99.99">$99.99</span>'
        '<span itemprop="priceCurrency">USD</span>', schema,
    )

    result = check_page(html)

    assert result["visible_facts"]["selected_variant"] == {"status": "available", "value": "BLACK-8"}
    assert result["comparisons"]["identity"]["status"] == "match"
    assert result["comparisons"]["selected_variant"]["status"] == "match"
    assert result["comparisons"]["amount"]["schema"] == "99.99"
    assert result["comparisons"]["amount"]["status"] == "match"


def test_reads_root_list_and_graph_jsonld():
    entity = product(price="89.99", priceCurrency="USD")
    html = page('<h1>Trail Shoe</h1><span itemprop="price" content="89.99">89.99</span>'
                '<span itemprop="priceCurrency">USD</span>', [entity])
    listed = check_page(html)
    graphed = check_page(
        '<h1>Trail Shoe</h1><span itemprop="price" content="89.99">89.99</span>'
        '<span itemprop="priceCurrency">USD</span><script type="application/ld+json">'
        + json.dumps({"@context": "https://schema.org", "@graph": [entity]}) + "</script>"
    )

    assert listed["comparisons"]["amount"]["status"] == "match"
    assert graphed["comparisons"]["amount"]["status"] == "match"
    assert listed["schema_validation"]["findings"] == graphed["schema_validation"]["findings"]


def test_hidden_only_facts_are_not_visible_evidence():
    html = page(
        '<h1>Trail Shoe</h1><div hidden><span itemprop="price" content="89.99">89.99</span>'
        '<meta itemprop="priceCurrency" content="USD">In stock</div>',
        product(price="99.99", priceCurrency="CAD", availability="https://schema.org/SoldOut"),
    )

    result = check_page(html)

    assert result["visible_facts"]["amount"]["status"] == "unavailable"
    assert result["visible_facts"]["currency"]["status"] == "unavailable"
    assert result["visible_facts"]["availability"]["status"] == "unavailable"
    assert all(result["comparisons"][key]["status"] == "unavailable"
               for key in ("amount", "currency", "availability"))


def test_multiple_products_or_offers_are_ambiguous_without_identity():
    first = product("Trail Shoe", price="89.99", priceCurrency="USD")
    second = product("Road Shoe", price="79.99", priceCurrency="USD")
    html = page('<span itemprop="price" content="89.99">89.99</span>',
                [first, second])

    result = check_page(html)

    assert result["comparisons"]["amount"]["status"] == "ambiguous"
    assert result["comparisons"]["amount"]["schema"] is None
    assert result["comparisons"]["amount"]["evidence"]

    one_product_two_offers = product(
        "Trail Shoe",
        offers=[
            {"@type": "Offer", "price": "89.99", "priceCurrency": "USD"},
            {"@type": "Offer", "price": "99.99", "priceCurrency": "USD"},
        ],
    )
    two_offers = check_page(
        page('<span itemprop="price" content="89.99">89.99</span>', one_product_two_offers)
    )
    assert two_offers["comparisons"]["amount"]["status"] == "ambiguous"


def test_rendered_price_and_currency_control_visible_evidence():
    html = page(
        '<h1>Trail Shoe</h1><section itemprop="offers">'
        '<span itemprop="price" content="109.99">89.99</span>'
        '<meta itemprop="priceCurrency" content="USD"></section>',
        product(price="89.99", priceCurrency="USD"),
    )

    result = check_page(html)

    assert result["visible_facts"]["amount"] == {"status": "available", "value": "89.99"}
    assert result["visible_facts"]["currency"] == {"status": "unavailable", "value": None}
    assert result["comparisons"]["amount"]["status"] == "match"
    assert result["comparisons"]["currency"]["status"] == "unavailable"


def test_negated_availability_is_not_reported_as_in_stock():
    html = page(
        '<h1>Trail Shoe</h1><section itemprop="offers"><p>Not in stock</p></section>',
        product(price="89.99", priceCurrency="USD", availability="https://schema.org/InStock"),
    )

    result = check_page(html)

    assert result["visible_facts"]["availability"]["status"] in {"ambiguous", "unavailable"}
    assert result["comparisons"]["availability"]["status"] in {"ambiguous", "unavailable"}


def test_availability_from_another_product_scope_is_ignored():
    html = page(
        '<h1>Trail Shoe</h1>'
        '<article itemtype="https://schema.org/Product"><span itemprop="name">Trail Shoe</span>'
        '<section itemprop="offers"><p>In stock</p></section></article>'
        '<article itemtype="https://schema.org/Product"><span itemprop="name">Road Shoe</span>'
        '<section itemprop="offers"><p>Out of stock</p></section></article>',
        product(price="89.99", priceCurrency="USD", availability="https://schema.org/InStock"),
    )

    result = check_page(html)

    assert result["visible_facts"]["availability"] == {"status": "available", "value": "InStock"}
    assert result["comparisons"]["availability"]["status"] == "match"
