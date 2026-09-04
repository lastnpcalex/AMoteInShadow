"""Optional browser-level smoke test for a locally served reader."""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


REPO = Path(__file__).resolve().parents[1]
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8765")
    parser.add_argument("--screenshots", action="store_true")
    args = parser.parse_args()
    page_errors: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=str(EDGE), headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.goto(args.url, wait_until="domcontentloaded")
        page.evaluate("localStorage.setItem('ams-theme', 'dark'); localStorage.setItem('ams-auto-translate', 'false')")
        page.reload(wait_until="domcontentloaded")

        assert page.locator(".chapter-section").count() == 24
        assert page.locator(".translation-unit").count() == 169
        assert page.locator("#generated-contents .toc-link").count() >= 30

        first_note = page.locator(".translation-unit").first
        first_note.scroll_into_view_if_needed()
        first_note.hover()
        assert first_note.locator(".translation-popover").evaluate(
            "element => getComputedStyle(element).visibility"
        ) == "visible"
        if args.screenshots:
            page.wait_for_timeout(900)
            page.screenshot(path=str(REPO / "tmp-translation-dark.png"), full_page=False)

        page.locator("#translate-toggle").click()
        assert page.locator("body").evaluate("element => element.classList.contains('auto-translate')")
        assert first_note.locator(".target-layer").evaluate(
            "element => Number(getComputedStyle(element).opacity)"
        ) > 0.9

        initial_theme = page.locator("html").get_attribute("data-theme")
        page.locator("#theme-toggle").click()
        assert page.locator("html").get_attribute("data-theme") != initial_theme

        if args.screenshots:
            page.evaluate("localStorage.setItem('ams-theme', 'light'); localStorage.setItem('ams-auto-translate', 'false')")
            page.goto(f"{args.url}?preview=light#top", wait_until="domcontentloaded")
            assert page.locator("html").get_attribute("data-theme") == "light"
            page.screenshot(path=str(REPO / "tmp-light.png"), full_page=False)
            page.set_viewport_size({"width": 390, "height": 844})
            page.evaluate("localStorage.setItem('ams-theme', 'dark')")
            page.goto(args.url, wait_until="domcontentloaded")
            page.locator("#menu-toggle").click()
            assert page.locator("#contents-panel").evaluate("element => element.classList.contains('open')")
            page.screenshot(path=str(REPO / "tmp-mobile-menu.png"), full_page=False)

        browser.close()

    if page_errors:
        raise AssertionError(f"Browser page errors: {page_errors}")
    print("Browser smoke test passed: TOC, translations, auto translate, theme, and mobile menu.")


if __name__ == "__main__":
    main()
