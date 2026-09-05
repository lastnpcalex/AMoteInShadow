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
        assert page.locator(".section-pager").count() == 0
        assert page.locator('a[href="https://a.co/d/d4eV40z"]').count() == 1
        assert page.locator('a[href="https://lastnpcalex.gumroad.com/l/AMoteInShadow"]').count() == 1
        assert page.locator('a[href="https://lastnpcalex.agency/ams"]').count() == 1

        header_box = page.locator(".signal-header").bounding_box()
        layout_box = page.locator(".reader-layout").bounding_box()
        assert header_box is not None and layout_box is not None
        assert abs(header_box["x"] - layout_box["x"]) < 1
        assert abs(header_box["width"] - layout_box["width"]) < 1
        assert header_box["y"] == 0 and header_box["height"] == 50
        assert page.locator("html").evaluate(
            "element => getComputedStyle(element).getPropertyValue('--cyan').trim()"
        ) == "#00ffff"
        assert "Orbitron" in page.locator(".signal-brand").evaluate("element => getComputedStyle(element).fontFamily")
        assert "Share Tech Mono" in page.locator("#translate-toggle").evaluate(
            "element => getComputedStyle(element).fontFamily"
        )
        prose = page.locator(".chapter-section p:not(.scene-date):not(.scene-place):not(.scene-stamp)").first
        assert "Source Serif 4" in prose.evaluate(
            "element => getComputedStyle(element).fontFamily"
        )
        assert page.locator(".amazon-blurb").evaluate("element => getComputedStyle(element).borderLeftWidth") == "0px"
        active_toc = page.locator(".toc-link.active").first
        assert active_toc.evaluate("element => getComputedStyle(element, '::before').content") == "none"

        shell_box = page.locator(".transmission-shell").bounding_box()
        assert shell_box is not None
        assert shell_box["y"] + shell_box["height"] <= page.viewport_size["height"] - 8
        assert page.locator("#book").evaluate("element => element.scrollHeight > element.clientHeight")
        assert page.locator("#book").evaluate("element => element.scrollWidth <= element.clientWidth + 1")
        assert page.evaluate("scrollY") == 0

        page.locator("#chapter-twelve").scroll_into_view_if_needed()
        page.wait_for_timeout(100)
        middle_progress = int(page.locator(".reading-progress").get_attribute("aria-valuenow") or "0")
        assert 20 < middle_progress < 90, f"unexpected Chapter Twelve progress: {middle_progress}%"
        page.locator("#one-pagers-personal-use-eyes-only").scroll_into_view_if_needed()
        page.wait_for_timeout(100)
        assert page.locator(".reading-progress").get_attribute("aria-valuenow") == "100"

        first_note = page.locator(".translation-unit").first
        first_note.scroll_into_view_if_needed()
        first_note.hover()
        assert first_note.evaluate("element => element.scrollWidth <= element.clientWidth + 1")
        assert page.locator(".translation-popover").count() == 0
        assert first_note.locator(".source-layer").evaluate(
            "element => getComputedStyle(element).display"
        ) == "none"
        assert first_note.locator(".target-layer").evaluate(
            "element => getComputedStyle(element).display"
        ) == "inline"
        long_note = page.locator("#translation-3").locator("xpath=..")
        long_note.scroll_into_view_if_needed()
        long_note.hover()
        word_boxes = long_note.locator(".target-layer .decode-word").evaluate_all(
            "elements => elements.map(element => element.getBoundingClientRect()).map(rect => ({left: rect.left, right: rect.right, top: rect.top}))"
        )
        same_line_gaps = [
            word_boxes[index + 1]["left"] - box["right"]
            for index, box in enumerate(word_boxes[:-1])
            if abs(word_boxes[index + 1]["top"] - box["top"]) < 1
        ]
        assert same_line_gaps and max(same_line_gaps) < 8, f"unexpected translated word gap: {max(same_line_gaps)}px"
        if args.screenshots:
            page.wait_for_timeout(900)
            page.screenshot(path=str(REPO / "tmp-translation-dark.png"), full_page=False)

        page.locator("#translate-toggle").click()
        assert page.locator("body").evaluate("element => element.classList.contains('auto-translate')")
        assert first_note.locator(".target-layer").evaluate(
            "element => getComputedStyle(element).display"
        ) == "inline"

        initial_theme = page.locator("html").get_attribute("data-theme")
        page.locator("#theme-toggle").click()
        assert page.locator("html").get_attribute("data-theme") != initial_theme
        assert prose.evaluate("element => getComputedStyle(element).color") == "rgb(46, 42, 38)"
        assert page.locator(".hero-copy h1").evaluate("element => getComputedStyle(element).color") == "rgb(74, 24, 104)"
        assert page.locator(".signal-header").evaluate(
            "element => getComputedStyle(element, '::after').backgroundColor"
        ) == "rgb(253, 250, 245)"

        if args.screenshots:
            page.evaluate("localStorage.setItem('ams-theme', 'light'); localStorage.setItem('ams-auto-translate', 'false')")
            page.goto(f"{args.url}?preview=light#top", wait_until="domcontentloaded")
            assert page.locator("html").get_attribute("data-theme") == "light"
            page.screenshot(path=str(REPO / "tmp-light.png"), full_page=False)
            page.set_viewport_size({"width": 2048, "height": 1182})
            page.goto(f"{args.url}?preview=wide-light#top", wait_until="domcontentloaded")
            wide_header = page.locator(".signal-header").bounding_box()
            wide_layout = page.locator(".reader-layout").bounding_box()
            assert wide_header is not None and wide_layout is not None
            assert abs(wide_header["x"] - wide_layout["x"]) < 1
            assert abs(wide_header["width"] - wide_layout["width"]) < 1
            page.screenshot(path=str(REPO / "tmp-wide-light.png"), full_page=False)
            page.set_viewport_size({"width": 390, "height": 844})
            page.evaluate("localStorage.setItem('ams-theme', 'dark')")
            page.goto(args.url, wait_until="domcontentloaded")
            page.locator("#menu-toggle").click()
            assert page.locator("#contents-panel").evaluate("element => element.classList.contains('open')")
            page.wait_for_timeout(300)
            page.screenshot(path=str(REPO / "tmp-mobile-menu.png"), full_page=False)
            page.set_viewport_size({"width": 1620, "height": 482})
            page.evaluate("localStorage.setItem('ams-theme', 'dark'); localStorage.setItem('ams-auto-translate', 'false')")
            page.goto(f"{args.url}#chapter-two", wait_until="domcontentloaded")
            fourth_note = page.locator("#translation-4").locator("xpath=..")
            fourth_note.scroll_into_view_if_needed()
            page.wait_for_timeout(100)
            short_shell = page.locator(".transmission-shell").bounding_box()
            assert short_shell is not None
            assert short_shell["y"] + short_shell["height"] <= 474
            assert page.locator("#book").evaluate("element => element.scrollWidth <= element.clientWidth + 1")
            page.screenshot(path=str(REPO / "tmp-short-frame.png"), full_page=False)

        browser.close()

    if page_errors:
        raise AssertionError(f"Browser page errors: {page_errors}")
    print("Browser smoke test passed: TOC, translations, auto translate, theme, and mobile menu.")


if __name__ == "__main__":
    main()
