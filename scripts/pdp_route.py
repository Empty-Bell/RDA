"""Out-of-stock PDP route loss: classify failed attempts and build the terminal evidence record.

A listed SKU whose requested PDP URL repeatedly lands on a different Samsung US page
(another model's PDP or a non-PDP page such as the family hub) while its PLP stockFlag is
N is not a route a consumer can take: the PLP card offers a stock alert instead of a PDP
link. DECISIONS.md (2026-10-26) settles such a SKU by where the redirect lands: a PDP that is
itself in the audited population is audited on its own route (this SKU passes with the
redirect noted), a non-PDP page leaves nothing to audit (pass with a note), and a PDP that
is not exposed on the PLP is a LOW finding. In-stock or stock-unknown SKUs are never
confirmed here.
"""
import json
import re
from urllib.parse import urlsplit

CONFIRMED = "PDP_REDIRECT_CONFIRMED"
OUT_OF_STOCK_PDP_INSPECTION = "PDP_NOT_REACHABLE_FROM_PLP_WHILE_STOCK_FLAG_N"
UNLISTED_REDIRECT_ISSUE = "PDP_REDIRECT_TO_UNLISTED_PDP"
ROUTE_BASIS = "PLP_STOCK_FLAG_N_REQUESTED_PDP_URL_DID_NOT_REACH_THE_REQUESTED_SKU"
_NOTES = {
    "POPULATION_MEMBER": "The requested PDP redirected to {sku}, which is audited on its own route; "
                         "this SKU's PDP controls are not repeated.",
    "NON_PDP_PAGE": "The requested PDP redirected to a page that is not a product page; no PDP is left to audit.",
    "UNLISTED_PDP": "The requested PDP redirected to a PDP that is not exposed on the PLP.",
}
_ERROR_PAGE = re.compile(r"(^|[/-])(error|404|not-found|unavailable)([/-]|$)")


def stock_flag(product):
    """The PLP stockFlag preserved from the PF listing, or None when it is not recorded."""
    listing = product.get("source_claim_listing_raw") if isinstance(product, dict) else None
    return listing.get("stockFlag") if isinstance(listing, dict) else None


def route_loss(row, sku):
    """Return ((kind, final_url), None) when a failed attempt loaded a Samsung US page that is
    not the requested SKU's PDP, else (None, reason). kind is OTHER_MODEL_PDP or NON_PDP_PAGE."""
    if row.get("status") != "FAILED":
        return None, f"STATUS:{row.get('status')}"
    if row.get("http_status") != 200:
        return None, f"HTTP_STATUS:{row.get('http_status')}"
    final = urlsplit(str(row.get("final_url") or ""))
    if final.scheme != "https" or final.hostname != "www.samsung.com" or not final.path.startswith("/us/"):
        return None, "FINAL_URL_NOT_SAMSUNG_US_HTTPS"
    path = final.path.lower().rstrip("/")
    if path.endswith("-sku-" + str(sku).lower().replace("/", "-")):
        return None, "FINAL_URL_IS_THE_REQUESTED_SKU_PDP"
    if final.path.rstrip("/") == urlsplit(str(row.get("requested_url") or "")).path.rstrip("/"):
        return None, "FINAL_URL_IS_THE_REQUESTED_URL"
    if _ERROR_PAGE.search(path):
        return None, "FINAL_URL_IS_AN_ERROR_PAGE"
    kind = "OTHER_MODEL_PDP" if re.search(r"-sku-[a-z0-9/-]+$", path) else "NON_PDP_PAGE"
    return (kind, row["final_url"]), None


def confirm_route_loss(attempts, product):
    """Terminal PDP_REDIRECT_CONFIRMED record, or None.

    Every attempt (the initial capture and both fresh retries) must have lost the route to the
    same page, and the PLP stockFlag must be exactly N.
    """
    sku = product["exact_sku"]
    if len(attempts) < 3 or stock_flag(product) != "N":
        return None
    checks = [route_loss(row, sku)[0] for row in attempts]
    if None in checks or len(set(checks)) != 1:
        return None
    first = attempts[0]
    return {**first, "status": CONFIRMED, "root_cause": "UNDETERMINED",
            "observation_scope": "Repeated route loss observed; option unavailability not established",
            "route_loss_kind": checks[0][0],
            "source_claim_listing_raw": product["source_claim_listing_raw"],
            "redirect_observations": [{"requested_url": row.get("requested_url"), "final_url": row.get("final_url"),
                                       "http_status": row.get("http_status"), "error": row.get("error")}
                                      for row in attempts]}


def diagnostics(attempts, product):
    """Readable per-attempt reasons for a route loss that was not confirmed (hosted logs)."""
    sku = product["exact_sku"]
    flag = stock_flag(product)
    return [{"attempt": index, "stock_flag": flag, "final_url": row.get("final_url"),
             "not_confirmed_because": (route_loss(row, sku)[1]
                                       or ("STOCK_FLAG_NOT_N" if flag != "N" else "DESTINATIONS_DIFFER_ACROSS_ATTEMPTS"))}
            for index, row in enumerate(attempts)]


def redirect_claim(row, sku, population_skus):
    """Claim record for a SKU whose PDP route loss was confirmed at collection.

    It carries only PLP-side facts plus the route-loss evidence; nothing from the page the
    requested URL landed on is borrowed. Anything but a consistent stockFlag-N confirmation
    is an error, never a quiet pass.
    """
    listing = row.get("source_claim_listing_raw")
    observations = row.get("redirect_observations")
    if (row.get("status") != CONFIRMED or not isinstance(listing, dict) or listing.get("stockFlag") != "N"
            or not row.get("requested_url") or not row.get("final_url")
            or not isinstance(observations, list) or len(observations) != 3
            or any(item.get("final_url") != row.get("final_url") for item in observations)):
        raise ValueError("PDP route-loss result is not a consistent out-of-stock confirmation")
    return {"exact_sku": sku, "plp_energy_star_flag_raw": listing.get("energyStarFlg"),
            "pdp_route_loss_raw": {"requested_url": row["requested_url"], "final_url": row["final_url"],
                                   "plp_stock_flag_raw": listing.get("stockFlag"),
                                   "route_loss_kind": row.get("route_loss_kind"),
                                   "destination": classify_destination(row["final_url"], population_skus),
                                   "redirect_observations": observations}}


def print_unconfirmed(results):
    """One log line naming each failed SKU's per-attempt route-loss reasons (evidence only)."""
    unconfirmed = [{"exact_sku": row["exact_sku"], "error": row.get("error"),
                    "attempts": row["route_loss_diagnostics"]}
                   for row in results if row.get("route_loss_diagnostics")]
    if unconfirmed:
        print(json.dumps({"pdp_route_loss_unconfirmed": unconfirmed}, ensure_ascii=False, sort_keys=True), flush=True)


def destination_slug(url):
    """The SKU slug a Samsung PDP path ends with (`...-sku-<slug>`), else None."""
    path = urlsplit(str(url or "")).path.lower().rstrip("/")
    return path.rsplit("-sku-", 1)[1] if "-sku-" in path else None


def classify_destination(final_url, population_skus):
    """Where a lost route landed: a PDP in the audited population, another PDP, or a non-PDP page."""
    slug = destination_slug(final_url)
    if slug is None:
        return {"kind": "NON_PDP_PAGE", "final_url": final_url}
    members = {str(sku).lower().replace("/", "-"): sku for sku in population_skus}
    if slug in members:
        return {"kind": "POPULATION_MEMBER", "sku": members[slug], "final_url": final_url}
    return {"kind": "UNLISTED_PDP", "sku_slug": slug, "final_url": final_url}


def route_loss_outcome(loss):
    """(display outcome, findings, observation) for a confirmed out-of-stock route loss."""
    destination = (loss or {}).get("destination") or {}
    kind = destination.get("kind")
    if kind not in _NOTES:
        raise ValueError("PDP route-loss destination is not classified")
    if kind == "UNLISTED_PDP":
        outcome = "LOW"
        findings = [{"control": "PDP_ROUTE", "severity": "LOW", "issue_code": UNLISTED_REDIRECT_ISSUE}]
    else:
        outcome, findings = "PASS", []
    observation = {"basis": ROUTE_BASIS, "destination": destination,
                   "finding": UNLISTED_REDIRECT_ISSUE if findings else "NONE",
                   "note": _NOTES[kind].format(sku=destination.get("sku"))}
    return outcome, findings, observation


def route_loss_points(claim):
    """Publication points for a route-loss SKU: the PLP flag as observed, PDP points not applicable."""
    raw = claim.get("plp_energy_star_flag_raw")
    state = ("PRESENT" if str(raw).strip().lower() in ("y", "yes", "true", "1")
             else "ABSENT" if str(raw).strip().lower() in ("n", "no", "false", "0") else "UNKNOWN")
    unreachable = {"state": "NOT_APPLICABLE", "inspection": OUT_OF_STOCK_PDP_INSPECTION}
    return {"plp_logo": {"state": state, "raw_value": raw, "inspection": "OBSERVED_NOT_ASSESSED_PDP_ROUTE_LOSS"},
            "pdp_logo": dict(unreachable), "spec_certification": dict(unreachable)}
