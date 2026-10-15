# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright"]
# ///
"""Local WASM render smoke test for the marimo "unlearning" bundle.

Boots the exported bundle in a headless browser, waits for Pyodide + the
notebook to render, and asserts the charts appear with no console errors and no
marimo "Bad Data" widget alerts. This is the render gate, and it runs LOCALLY:
a source-only session cannot *see* the output, but a headless browser verifies
it programmatically. Set SMOKE_SHOT=path.png to also save a screenshot of the
hero section.

By default it drives the system Edge (channel "msedge"), so there is no browser
download. Set CHANNEL=chromium (after `playwright install chromium`) to use
Playwright's bundled browser instead.

Run (serve the bundle first, in another shell or backgrounded):
    python -m http.server 8137 --directory dist/unlearning
    SMOKE_URL=http://127.0.0.1:8137/ uv run --script deploy/tests/wasm_smoke.py

Exit 0 = bundle renders; 1 = a render check failed; 2 = could not launch a browser.
"""
import os
import sys

from playwright.sync_api import sync_playwright

URL = os.environ.get("SMOKE_URL", "http://127.0.0.1:8137/")
CHANNEL = os.environ.get("CHANNEL", "msedge")  # system Edge => no browser download
SHOT = os.environ.get("SMOKE_SHOT")  # optional screenshot path for the hero section


def main() -> None:
    console_errors = []
    wasm_ct = None

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel=CHANNEL or None, headless=True)
        except Exception as e:  # noqa: BLE001
            print(f"could not launch channel={CHANNEL!r}: {e}")
            print("retry with bundled chromium:")
            print("  uv run --with playwright python -m playwright install chromium")
            print("  CHANNEL=chromium SMOKE_URL=... uv run --script deploy/tests/wasm_smoke.py")
            sys.exit(2)

        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append(str(e)))

        def _on_response(r):
            nonlocal wasm_ct
            if r.url.endswith(".wasm"):
                wasm_ct = (r.headers.get("content-type") or "").lower()

        page.on("response", _on_response)

        print(f"loading {URL} via channel={CHANNEL!r} ...")
        page.goto(URL, wait_until="domcontentloaded", timeout=60_000)

        # (2)+(3) marimo reaches ready state and Altair renders: a chart surface
        # appears only after Pyodide boots and the notebook executes. Slow first
        # load (Pyodide + micropip), so allow generous time.
        page.wait_for_selector(
            "canvas, svg.marks, .vega-embed canvas, .vega-embed svg",
            timeout=150_000,
        )
        # (5) hero interactive present
        page.wait_for_selector("text=/Fine-tuning step/i", timeout=150_000)
        # Let the cells below the hero finish rendering before scanning the page.
        page.wait_for_timeout(5_000)

        # (6) marimo validates each widget's args in the browser and, on failure,
        # renders a "Bad Data" alert in place of the widget. That logs no console
        # error, so check 4 cannot see it (how the v0.1.0 autoplay bug shipped).
        bad_data = page.get_by_text("Bad Data", exact=True).count()
        # (7) the hero autoplay control rendered as a real control. Its interval
        # <select> exists only on a valid render; a "Bad Data" alert also holds
        # a button ("View Data:"), so a bare button count cannot tell them apart.
        autoplay = page.locator('[data-testid="marimo-plugin-refresh-select"]').count()
        # (8) the build-time loading splash cleared itself once the page painted
        splash_left = page.locator("#jb-splash").count()
        if SHOT:
            # The hero chart is the page's first canvas; centering it also brings
            # the scrub + autoplay row above it into frame. (marimo-refresh itself
            # is display:contents, so it has no box to scroll to.)
            page.locator("canvas").first.evaluate(
                "e => e.scrollIntoView({block: 'center'})"
            )
            page.wait_for_timeout(800)
            page.screenshot(path=SHOT)
        browser.close()

    ok = True
    print("[check 2/3] marimo ready + Altair chart rendered: PASS")
    print("[check 5]   hero 'Fine-tuning step' slider present: PASS")
    print(f"[check 1]   .wasm Content-Type (local http.server): {wasm_ct or 'no .wasm fetched'}")
    if console_errors:
        ok = False
        print(f"[check 4]   console errors: FAIL ({len(console_errors)})")
        for e in console_errors[:10]:
            print("   -", e)
    else:
        print("[check 4]   no console errors during boot: PASS")
    if bad_data:
        ok = False
        print(f"[check 6]   marimo 'Bad Data' widget alerts: FAIL ({bad_data})")
    else:
        print("[check 6]   no marimo 'Bad Data' widget alerts: PASS")
    if autoplay:
        print("[check 7]   hero autoplay control rendered: PASS")
    else:
        ok = False
        print("[check 7]   hero autoplay control rendered: FAIL (no refresh interval select)")
    if splash_left:
        ok = False
        print("[check 8]   loading splash cleared after paint: FAIL (still in the DOM)")
    else:
        print("[check 8]   loading splash cleared after paint: PASS")
    if SHOT:
        print(f"screenshot: {SHOT}")

    print("RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
