# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright"]
# ///
"""Local WASM render smoke test for the marimo "unlearning" bundle.

Boots the exported bundle in a headless browser, waits for Pyodide + the
notebook to render, and asserts the charts appear with no console errors. This
is the render gate, and it runs LOCALLY: a source-only session cannot *see* the
output, but a headless browser verifies it programmatically.

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

        page = browser.new_page()
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

    print("RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
