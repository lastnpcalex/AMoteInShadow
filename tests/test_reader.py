from __future__ import annotations

import html
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]


class ReaderParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.local_files: list[str] = []
        self.chapter_count = 0
        self.translation_count = 0
        self.figures = 0

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs_list)
        classes = set((attrs.get("class") or "").split())
        if attrs.get("id"):
            self.ids.append(attrs["id"] or "")
        if "chapter-section" in classes:
            self.chapter_count += 1
        if "translation-unit" in classes:
            self.translation_count += 1
            self.assert_translation(attrs)
        if "manuscript-figure" in classes:
            self.figures += 1
        for attribute in ("src", "href"):
            value = attrs.get(attribute)
            if value and not value.startswith(("#", "http://", "https://", "mailto:")):
                self.local_files.append(value.split("#", 1)[0].split("?", 1)[0])

    @staticmethod
    def assert_translation(attrs: dict[str, str | None]) -> None:
        if not attrs.get("data-source") or not attrs.get("data-translation"):
            raise AssertionError("Translation unit is missing its source or translation text")


class ReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (REPO / "index.html").read_text(encoding="utf-8")
        cls.styles = (REPO / "css" / "style.css").read_text(encoding="utf-8")
        cls.parser = ReaderParser()
        cls.parser.feed(cls.page)

    def test_complete_manuscript_shape(self) -> None:
        self.assertEqual(self.parser.chapter_count, 24)
        self.assertEqual(self.parser.translation_count, 169)
        self.assertEqual(self.parser.figures, 5)
        self.assertIn("Chapter Twenty-four", self.page)

    def test_generated_ids_are_unique(self) -> None:
        self.assertEqual(len(self.parser.ids), len(set(self.parser.ids)))

    def test_local_assets_exist(self) -> None:
        missing = sorted({path for path in self.parser.local_files if not (REPO / path).is_file()})
        self.assertEqual(missing, [])

    def test_old_conversion_artifacts_are_gone(self) -> None:
        self.assertNotIn("<html><head></head><body>", self.page)
        self.assertNotRegex(self.page, r"\d+F\d+F")
        self.assertNotIn("â€™", self.page)
        self.assertNotIn("�", self.page)
        self.assertNotIn("{{BOOK_CONTENT}}", self.page)

    def test_redirects_cover_every_chapter(self) -> None:
        redirects = list((REPO / "chapters").glob("chapter-*.html"))
        self.assertEqual(len(redirects), 24)
        for redirect in redirects:
            content = redirect.read_text(encoding="utf-8")
            self.assertIn("../index.html#chapter-", content)

    def test_translation_numbers_are_contiguous(self) -> None:
        numbers = [int(value) for value in re.findall(r'id="translation-(\d+)"', self.page)]
        self.assertEqual(numbers, list(range(1, 170)))

    def test_every_translation_contains_its_attached_italic_phrase(self) -> None:
        source_markup = re.findall(
            r'<span class="source-layer">(.*?)</span>', self.page, re.DOTALL
        )
        self.assertEqual(len(source_markup), 169)
        self.assertTrue(all("<em>" in source for source in source_markup))
        self.assertTrue(
            all(not source.startswith((" ", "\t", " ")) for source in source_markup)
        )

        sources = [
            html.unescape(source)
            for source in re.findall(
                r'class="translation-unit"[^>]*data-source="([^"]*)"', self.page
            )
        ]
        for expected in (
            "Ahdioseu, Charles.",
            "Hao fa, Gray Top",
            "Hao fa, Ya Ke Juliet Sierra zero-one-four.",
            "Anchuan shiyong, Frederik.",
            "Chu’eh son, Dr. No.",
        ):
            self.assertTrue(
                any(expected in source for source in sources),
                f"Missing complete attached Di Lingua phrase: {expected}",
            )

    def test_reported_translation_boundaries(self) -> None:
        def source_for(number: int) -> str:
            match = re.search(
                rf'<span class="translation-unit"[^>]*data-source="([^"]*)"[^\n]*'
                rf'id="translation-{number}"',
                self.page,
            )
            self.assertIsNotNone(match, f"Missing translation {number}")
            return html.unescape(match.group(1))

        expected_sources = {
            90: "“Erm, prastitey?”",
            91: "“Neva palava.”",
            93: "“Nawa oh!”",
            94: "“Na yu gah gahdah lul tsow!”",
            99: "“Oke, binu ohlowyeh.",
            100: "“Ye, A gah am sabi.",
            110: "“Yu’ll tsow.”",
            132: "“Neva palava.”",
            135: "“Nawa oh! Anchuan shiyong!”",
            157: "“Juan juye.",
            162: "Hao fa,",
        }
        for number, expected in expected_sources.items():
            self.assertEqual(source_for(number), expected)
        self.assertRegex(
            self.page,
            r'id="translation-162"[^<]*</button></span>',
        )
        self.assertIn('<span class="translation-context"><em> Dr. No?”</em></span>', self.page)

    def test_complex_script_flags_do_not_italicize_latin_prose(self) -> None:
        for opening in (
            "Once we land, it’ll be just like that Old Towne operation",
            "The thump of boots vibrating through the floor of the hab",
            "If that’s the only way, then fine.",
        ):
            paragraph = re.search(
                rf"<p[^>]*>[^\n]*?(?P<body>{re.escape(opening)}[^\n]*)</p>", self.page
            )
            self.assertIsNotNone(paragraph, f"Missing reported prose: {opening}")
            self.assertNotIn("<em>", paragraph.group("body"))

    def test_scene_breaks_are_centered(self) -> None:
        self.assertNotRegex(self.page, r"<p>(?:<em>)?\*\*\*")
        self.assertGreater(self.page.count('class="scene-break"'), 5)
        rule = re.search(r"\.scene-break\s*\{(?P<body>.*?)\}", self.styles, re.DOTALL)
        self.assertIsNotNone(rule)
        self.assertIn("text-align: center", rule.group("body"))

    def test_character_bio_bullets_follow_docx_numbering(self) -> None:
        section = re.search(
            r'<section class="appendix-section transmission-section" id="persons-of-interest"'
            r'(?P<body>.*?)</section>',
            self.page,
            re.DOTALL,
        )
        self.assertIsNotNone(section)
        body = section.group("body")
        self.assertEqual(body.count("list-paragraph"), 215)
        self.assertEqual(body.count("list-level-1"), 10)
        self.assertRegex(
            body,
            r'<p class="list-paragraph list-level-0">2342: EVA qualified\.',
        )
        self.assertRegex(
            self.styles,
            r'\.appendix-section \.list-paragraph::before\s*\{[^}]*content:\s*"•"',
        )
        self.assertIn(".appendix-section .list-level-2", self.styles)

    def test_translations_decode_inline_without_popovers(self) -> None:
        self.assertNotIn("translation-popover", self.page)
        self.assertNotIn("translation-result", self.page)
        self.assertNotIn("positionPopover", (REPO / "js" / "main.js").read_text(encoding="utf-8"))
        self.assertIn("word-spacing: normal", self.styles)
        self.assertRegex(self.styles, r"\.decode-word\s*\{[^}]*text-indent:\s*0")
        self.assertIn("(hover: none) and (pointer: coarse)", (REPO / "js" / "main.js").read_text(encoding="utf-8"))
        script = (REPO / "js" / "main.js").read_text(encoding="utf-8")
        self.assertIn("unit.style.inlineSize", script)
        self.assertIn("removeProperty('inline-size')", script)

    def test_assets_are_versioned_and_agency_menu_is_present(self) -> None:
        self.assertRegex(self.page, r'href="css/style\.css\?v=[0-9a-f]{12}"')
        self.assertRegex(self.page, r'src="js/main\.js\?v=[0-9a-f]{12}"')
        self.assertIn('class="header-bar"', self.page)
        self.assertIn('id="nav-menu"', self.page)
        self.assertIn('id="nav-dropdown"', self.page)
        self.assertIn('class="header-brand" href="https://lastnpcalex.agency/"', self.page)
        self.assertNotIn("nav-link-arrow", self.page)

    def test_reader_shell_and_purchase_paths(self) -> None:
        self.assertIn('class="transmission-shell"', self.page)
        self.assertIn('aria-label="Novel reading progress"', self.page)
        self.assertIn("A burnt-out exobiologist", self.page)
        self.assertIn("https://a.co/d/d4eV40z", self.page)
        self.assertIn("https://lastnpcalex.gumroad.com/l/AMoteInShadow", self.page)
        self.assertIn("https://lastnpcalex.agency/ams", self.page)

    def test_front_matter_dividers(self) -> None:
        front_matter = re.search(
            r'<section class="front-matter transmission-section"(?P<body>.*?)</section>',
            self.page,
            re.DOTALL,
        )
        self.assertIsNotNone(front_matter)
        body = front_matter.group("body")
        self.assertEqual(body.count('<hr class="front-matter-divider">'), 2)
        copyright_rule = body.index("No additional restrictions")
        poem_title = body.index("Safe Handling")
        first_rule = body.index('<hr class="front-matter-divider">')
        final_line = body.index("abyssal current")
        second_rule = body.rindex('<hr class="front-matter-divider">')
        self.assertLess(copyright_rule, first_rule)
        self.assertLess(first_rule, poem_title)
        self.assertLess(final_line, second_rule)

    def test_contents_panel_omits_cover(self) -> None:
        script = (REPO / "js" / "main.js").read_text(encoding="utf-8")
        self.assertIn("TABLE OF CONTENTS", self.page)
        self.assertNotIn("SIGNAL INDEX", self.page)
        self.assertNotIn("cover-mini", self.page)
        self.assertIn("contentsSections = navigableSections.filter", script)
        self.assertIn("contentsSections.forEach", script)

    def test_book_and_social_covers_use_web_export_dimensions(self) -> None:
        with Image.open(REPO / "assets" / "cover.jpg") as cover:
            self.assertEqual(cover.size, (1200, 1920))
        with Image.open(REPO / "assets" / "social-cover.jpg") as social_cover:
            self.assertEqual(social_cover.size, (1200, 630))

    def test_infinite_scroll_has_no_pagers_or_link_arrows(self) -> None:
        self.assertNotIn("section-pager", self.page)
        self.assertNotIn("pager-link", self.page)
        for arrow in ("→", "↗", "←"):
            self.assertNotIn(arrow, self.page)

    def test_acidburn_tokens_and_no_left_highlights(self) -> None:
        for token in ("--cyan: #00ffff", "--purple: #bf00ff", "--green: #00ff88"):
            self.assertIn(token, self.styles)
        self.assertIn('--mono: "Share Tech Mono"', self.styles)
        self.assertIn('--serif: "Source Serif 4"', self.styles)
        self.assertNotIn(".toc-link.active::before", self.styles)
        blurb_rule = re.search(r"\.amazon-blurb\s*\{(?P<body>.*?)\}", self.styles, re.DOTALL)
        self.assertIsNotNone(blurb_rule)
        self.assertIn("border: 0", blurb_rule.group("body"))


if __name__ == "__main__":
    unittest.main()
