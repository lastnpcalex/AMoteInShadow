from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


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
                self.local_files.append(value.split("#", 1)[0])

    @staticmethod
    def assert_translation(attrs: dict[str, str | None]) -> None:
        if not attrs.get("data-source") or not attrs.get("data-translation"):
            raise AssertionError("Translation unit is missing its source or translation text")


class ReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (REPO / "index.html").read_text(encoding="utf-8")
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

    def test_reader_shell_and_purchase_paths(self) -> None:
        self.assertIn('class="transmission-shell"', self.page)
        self.assertIn('aria-label="Novel reading progress"', self.page)
        self.assertIn("A burnt-out exobiologist", self.page)
        self.assertIn("https://a.co/d/d4eV40z", self.page)
        self.assertIn("https://lastnpcalex.gumroad.com/l/AMoteInShadow", self.page)
        self.assertIn("https://lastnpcalex.agency/ams", self.page)

    def test_infinite_scroll_has_no_pagers_or_link_arrows(self) -> None:
        self.assertNotIn("section-pager", self.page)
        self.assertNotIn("pager-link", self.page)
        for arrow in ("→", "↗", "←"):
            self.assertNotIn(arrow, self.page)


if __name__ == "__main__":
    unittest.main()
