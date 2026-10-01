"""Bind an audit population to exact model codes on rendered PLP cards."""
import json
from pathlib import Path


def rendered_card_skus(recon_root, pf_population):
    path = Path(recon_root) / "population-observation.json"
    if not path.is_file():
        raise ValueError("Source artifact has no rendered PLP population observation")
    observation = json.loads(path.read_bytes())
    tiles = observation.get("rendered_tiles")
    groups = observation.get("rendered_tile_groups")
    expected = pf_population["total_groups"]
    if (observation.get("groups") != expected or not isinstance(tiles, list)
            or len(tiles) != expected or not isinstance(groups, list)
            or len(groups) != expected or len(set(groups)) != expected):
        raise ValueError("Rendered PLP cards do not reconcile to the complete PF groups")
    provenance = {}
    for row in pf_population["records"]:
        sku = row["exact_sku"]
        provenance.setdefault(sku, set()).add(str(row["family_id"]))
    cards = {}
    for tile, group in zip(tiles, groups):
        if not isinstance(tile, dict):
            raise ValueError("Rendered PLP card is malformed")
        sku = str(tile.get("sku") or "").strip()
        if not sku or sku in cards or provenance.get(sku) != {str(group)}:
            raise ValueError("Rendered PLP SKU is missing, duplicated, or mismatched with PF provenance")
        cards[sku] = tile
    claim_path = Path(recon_root) / "plp-claim-observation.json"
    if not claim_path.is_file():
        raise ValueError("Source artifact has no rendered PLP card claim observation")
    claims = json.loads(claim_path.read_bytes()).get("cards")
    if (not isinstance(claims, list) or len(claims) != len(cards)
            or {item.get("sku") for item in claims if isinstance(item, dict)} != set(cards)):
        raise ValueError("Rendered PLP card identity differs from claim observation")
    return cards


def select_rendered_products(products, cards):
    selected = [product for product in products if product["exact_sku"] in cards]
    if len(selected) != len(cards) or {product["exact_sku"] for product in selected} != set(cards):
        raise ValueError("Collector products do not cover each rendered PLP card exactly once")
    return selected


def select_listed_products(products, cards, expected_count):
    """Keep every PLP group option while proving every visible card has a source SKU."""
    by_sku = {product["exact_sku"]: product for product in products}
    if (len(by_sku) != len(products) or len(products) != expected_count
            or not cards or not set(cards) <= set(by_sku)):
        raise ValueError("PLP group options or rendered cards have incomplete exact-SKU coverage")
    return products
