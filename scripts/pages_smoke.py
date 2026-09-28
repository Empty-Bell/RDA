"""Check the published project path, current run, controls and browser errors."""

import argparse
import json
import time
from urllib.request import Request, urlopen

def fetch(url):
    with urlopen(Request(url, headers={"Cache-Control": "no-cache"}), timeout=20) as response:
        if response.status != 200:
            raise ValueError(f"HTTP {response.status}: {url}")
        return response.read()


def check(base, run_id, browser_check=True):
    base = base.rstrip("/") + "/"
    for _ in range(18):
        try:
            manifest = json.loads(fetch(base + "publication-manifest.json?run=" + run_id))
            if manifest.get("run_id") == run_id:
                break
        except Exception:
            pass
        time.sleep(10)
    else:
        raise ValueError("Published Pages run has not reached the requested source run")
    for name in ("index.html", "styles.css", "app.js", "model-data.json",
                 "history.json", "report-data.csv", "report-all-fields.csv", "report-data.xlsx"):
        fetch(base + name + "?run=" + run_id)
    model = json.loads(fetch(base + "model-data.json?run=" + run_id))
    if model["run_number"] != manifest["dashboard_run_number"] or len(model["records"]) != manifest["model_count"]:
        raise ValueError("Published model data differs from the bundle manifest")
    fetch(base + model["records"][0]["evidence_url"].removeprefix("./") + "?run=" + run_id)
    if not browser_check:
        print(json.dumps({"status": "PASS", "run_id": run_id, "model_count": len(model["records"])}))
        return
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for mode, options in (("desktop", {"viewport": {"width": 1440, "height": 900}}),
                              ("mobile", {"viewport": {"width": 390, "height": 844}, "is_mobile": True,
                                          "device_scale_factor": 2, "has_touch": True})):
            context = browser.new_context(**options)
            page = context.new_page()
            failures = []
            page.on("pageerror", lambda error: failures.append(str(error)))
            page.goto(base + "?run=" + run_id + "#queue", wait_until="networkidle", timeout=60000)
            page.locator("#run-number").wait_for(timeout=20000)
            if str(model["run_number"]) not in page.locator("#run-number").inner_text():
                raise ValueError(f"{mode}: displayed run number differs")
            if page.locator("#queue-list .queue-item").count() == 0:
                raise ValueError(f"{mode}: action queue did not render")
            page.locator("#queue-severity").select_option("HIGH")
            if page.locator("#queue-list .queue-item").count() == 0:
                raise ValueError(f"{mode}: severity filter did not render")
            page.locator("#queue-list .queue-item").first.locator("summary").click()
            page.locator("#queue-list .queue-item").first.locator(".evidence-mount").locator("*", has_text="PDP").first.wait_for(timeout=20000)
            page.locator("#report-grade").select_option("PASS")
            if page.locator("#report-rows .report-row").count() == 0:
                raise ValueError(f"{mode}: report filter did not render")
            if failures:
                raise ValueError(f"{mode}: browser errors: {failures}")
            context.close()
        browser.close()
    print(json.dumps({"status": "PASS", "run_id": run_id, "model_count": len(model["records"])}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    check(args.base, args.run_id, not args.no_browser)
