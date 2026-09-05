#!/usr/bin/env python3
"""Build the static A Mote in Shadow reader from the canonical DOCX manuscript."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageOps


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": W, "r": R, "a": A, "rel": REL}


FIGURES = {
    "image2.png": (
        "inhabited-space.png",
        "Map of inhabited space and travel times from Sol",
        "Inhabited space",
        True,
    ),
    "image3.png": (
        "moons-of-jin.png",
        "Reference chart showing the major moons of Jin",
        "Moons of Jin",
        True,
    ),
    "image4.png": (
        "el-cajon-spacecraft.png",
        "IKSA CT-185 El Cajon spacecraft schematic",
        "IKSA CT-185 “El Cajon”",
        True,
    ),
    "image5.png": (
        "one-pagers-glyph.png",
        "One Pagers access glyph",
        "Personal-use dossier access glyph",
        False,
    ),
    "image6.jpeg": (
        "author.jpg",
        "Portrait of A.N. Alex",
        "A.N. Alex",
        False,
    ),
}


@dataclass
class InlineChunk:
    markup: str
    text: str
    italic: bool = False


@dataclass
class Section:
    section_id: str
    title: str
    kind: str


def q(namespace: str, name: str) -> str:
    return f"{{{namespace}}}{name}"


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = value.lower().replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "section"


def text_of(node: ET.Element) -> str:
    return "".join(part.text or "" for part in node.findall(".//w:t", NS))


def style_of(paragraph: ET.Element) -> str:
    style = paragraph.find("w:pPr/w:pStyle", NS)
    return style.get(q(W, "val"), "") if style is not None else ""


def note_parts(note: str) -> tuple[str, str]:
    match = re.match(r"\s*\[([^]]+)]\s*:\s*(.*?)\s*$", note)
    if match:
        return match.group(1), match.group(2)
    return "Translation", note.strip()


def animated_words(value: str) -> str:
    pieces: list[str] = []
    word_index = 0
    for token in re.findall(r"\s+|\S+", value):
        if token.isspace():
            pieces.append(token)
        else:
            pieces.append(
                f'<span class="decode-word" style="--word-index:{word_index}">'
                f"{html.escape(token)}</span>"
            )
            word_index += 1
    return "".join(pieces)


def translation_unit(
    source_markup: str,
    source_text: str,
    note: str,
    display_number: int,
) -> str:
    language, translation = note_parts(note)
    unit_id = f"translation-{display_number}"
    return (
        f'<span class="translation-unit" data-language="{html.escape(language, quote=True)}" '
        f'data-source="{html.escape(source_text.strip(), quote=True)}" '
        f'data-translation="{html.escape(translation, quote=True)}">'
        '<span class="translation-phrase">'
        f'<span class="source-layer">{source_markup}</span>'
        f'<span class="target-layer" aria-hidden="true">{animated_words(translation)}</span>'
        "</span>"
        f'<button class="translation-trigger" id="{unit_id}" type="button" '
        f'aria-label="Translation note {display_number}: {html.escape(translation, quote=True)}">'
        f"{display_number}</button>"
        "</span>"
    )


def attached_italic_start(chunks: list[InlineChunk]) -> int:
    """Find the full mixed-format Di Lingua phrase attached to a footnote."""
    end = len(chunks)
    nearest_italic: int | None = None
    scanned_characters = 0

    # Word frequently splits a single phrase into italic words followed by a
    # non-italic name, punctuation, or closing quote. Anchor the unit to the
    # nearest italic run instead of assuming the run beside the note is italic.
    for distance, cursor in enumerate(range(end - 1, -1, -1), start=1):
        scanned_characters += len(chunks[cursor].text)
        if distance > 16 or scanned_characters > 240:
            break
        if chunks[cursor].italic:
            nearest_italic = cursor
            break

    if nearest_italic is None:
        return max(0, end - 1)

    start = nearest_italic
    cursor = nearest_italic - 1
    opening_punctuation = "“‘([{'\""
    connecting_punctuation = ",;:—–-/'’"

    # Continue through the rest of the contiguous italic expression. Spaces
    # and light punctuation are often separate non-italic Word runs.
    while cursor >= 0:
        chunk = chunks[cursor]
        stripped = chunk.text.strip()
        if chunk.italic:
            start = cursor
        elif stripped:
            if any(character.isalnum() for character in stripped):
                break
            if all(character in opening_punctuation for character in stripped):
                start = cursor
                break
            if not all(character in connecting_punctuation for character in stripped):
                break
        # Whitespace and connecting punctuation are included only if the scan
        # reaches another italic run, proving they sit inside the expression.
        cursor -= 1

    return start


def run_chunks(paragraph: ET.Element, footnotes: dict[str, str]) -> str:
    runs = paragraph.findall(".//w:r", NS)
    chunks: list[InlineChunk] = []

    for index, run in enumerate(runs):
        reference = run.find(".//w:footnoteReference", NS)
        if reference is not None:
            footnote_id = reference.get(q(W, "id"), "")
            display_number = max(1, int(footnote_id) - 1)
            note = footnotes.get(footnote_id, "Translation unavailable")

            start = attached_italic_start(chunks)

            phrase = chunks[start:]
            del chunks[start:]
            source_markup = "".join(chunk.markup for chunk in phrase)
            source_text = "".join(chunk.text for chunk in phrase)
            leading_spacing = source_markup[: len(source_markup) - len(source_markup.lstrip(" \t "))]
            source_markup = source_markup[len(leading_spacing) :]
            if leading_spacing:
                chunks.append(InlineChunk(leading_spacing, ""))
            chunks.append(
                InlineChunk(
                    translation_unit(source_markup, source_text, note, display_number),
                    source_text,
                )
            )
            continue

        raw_text = "".join(item.text or "" for item in run.findall(".//w:t", NS))
        if re.fullmatch(r"\d+F", raw_text):
            nearby = runs[index + 1 : index + 3]
            if any(item.find(".//w:footnoteReference", NS) is not None for item in nearby):
                continue

        if not raw_text and run.find(".//w:br", NS) is None and run.find(".//w:tab", NS) is None:
            continue

        properties = run.find("w:rPr", NS)
        italic = properties is not None and (
            properties.find("w:i", NS) is not None or properties.find("w:iCs", NS) is not None
        )
        bold = properties is not None and properties.find("w:b", NS) is not None
        markup = html.escape(raw_text)
        if run.find(".//w:tab", NS) is not None:
            markup = " " + markup
        if run.find(".//w:br", NS) is not None:
            markup += "<br>"
        if bold:
            markup = f"<strong>{markup}</strong>"
        if italic:
            markup = f"<em>{markup}</em>"
        chunks.append(InlineChunk(markup, raw_text, italic))

    rendered = "".join(chunk.markup for chunk in chunks)
    rendered = re.sub(
        r"(https://creativecommons\.org/licenses/by/4\.0/[^\s<]*)",
        r'<a href="\1" rel="license">\1</a>',
        rendered,
    )
    return rendered


def image_relationships(archive: zipfile.ZipFile) -> dict[str, str]:
    root = ET.fromstring(archive.read("word/_rels/document.xml.rels"))
    return {
        relation.get("Id", ""): Path(relation.get("Target", "")).name
        for relation in root.findall(q(REL, "Relationship"))
        if relation.get("Type", "").endswith("/image")
    }


def render_figures(paragraph: ET.Element, relationships: dict[str, str]) -> str:
    rendered: list[str] = []
    seen: set[str] = set()
    for blip in paragraph.findall(".//a:blip", NS):
        source_name = relationships.get(blip.get(q(R, "embed"), ""), "")
        if source_name in seen or source_name not in FIGURES:
            continue
        seen.add(source_name)
        output_name, alt_text, caption, _ = FIGURES[source_name]
        rendered.append(
            '<figure class="manuscript-figure">'
            f'<button class="figure-open" type="button" data-image="assets/figures/{output_name}" '
            f'aria-label="Enlarge {html.escape(caption, quote=True)}">'
            f'<img src="assets/figures/{output_name}" alt="{html.escape(alt_text, quote=True)}" loading="lazy">'
            "</button>"
            f"<figcaption>// FIGURE · {html.escape(caption)}</figcaption>"
            "</figure>"
        )
    return "".join(rendered)


def extract_figures(archive: zipfile.ZipFile, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for source_name, (output_name, _, _, rotate) in FIGURES.items():
        source_path = f"word/media/{source_name}"
        with archive.open(source_path) as source:
            image = Image.open(source)
            image.load()
        image = ImageOps.exif_transpose(image)
        if rotate:
            image = image.transpose(Image.Transpose.ROTATE_90)
        destination = output_dir / output_name
        if destination.suffix.lower() in {".jpg", ".jpeg"}:
            image.convert("RGB").save(destination, quality=90, optimize=True, progressive=True)
        else:
            image.save(destination, optimize=True)


def read_footnotes(archive: zipfile.ZipFile) -> dict[str, str]:
    root = ET.fromstring(archive.read("word/footnotes.xml"))
    notes: dict[str, str] = {}
    for note in root.findall("w:footnote", NS):
        note_id = note.get(q(W, "id"), "")
        note_text = text_of(note).strip()
        if note_id and int(note_id) > 0 and note_text:
            notes[note_id] = note_text
    return notes


def unique_id(title: str, used: set[str]) -> str:
    base = slugify(re.sub(r"^\[\d+]\s*", "", title))
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = f"{base}-{suffix}"
        suffix += 1
    used.add(candidate)
    return candidate


def render_manuscript(
    document_root: ET.Element,
    footnotes: dict[str, str],
    relationships: dict[str, str],
) -> tuple[str, list[Section]]:
    paragraphs = document_root.findall(".//w:body/w:p", NS)
    output: list[str] = [
        '<section class="front-matter transmission-section" id="front-matter" data-nav-title="Front matter">',
        '<div class="section-signal">// PREFACE SIGNAL</div>',
    ]
    sections = [Section("front-matter", "Front matter", "front")]
    section_open = True
    used_ids = {"front-matter", "top"}
    current_kind = "front"
    chapter_content_count = 0
    previous_blank = False

    for paragraph_index, paragraph in enumerate(paragraphs):
        text = text_of(paragraph).strip()
        style = style_of(paragraph)

        if paragraph_index in {0, 2}:
            continue
        if paragraph_index in {41, 42}:
            continue
        if text == "Chapter Twenty-four":
            style = "Heading2"

        if style == "Title" and not text:
            continue

        if style == "Heading1" and text:
            if section_open:
                output.append("</section>")
                section_open = False
            section_id = unique_id(text, used_ids)
            if text.lower() == "about the author":
                current_kind = "about"
                output.append(
                    f'<section class="about-section transmission-section" id="{section_id}" '
                    f'data-nav-title="{html.escape(text, quote=True)}"><div class="section-signal">// PERSONNEL FILE</div>'
                    f'<h2>{html.escape(text)}</h2>'
                )
                sections.append(Section(section_id, text, current_kind))
                section_open = True
            else:
                output.append(
                    f'<section class="part-divider" id="{section_id}" data-nav-title="{html.escape(text, quote=True)}">'
                    '<div class="part-grid" aria-hidden="true"></div>'
                    '<span class="section-signal">// CHANNEL DIVISION</span>'
                    f'<h2>{html.escape(text)}</h2></section>'
                )
                sections.append(Section(section_id, text, "part"))
                current_kind = "part"
            continue

        if style == "Heading2" and text:
            if section_open:
                output.append("</section>")
            section_id = unique_id(text, used_ids)
            current_kind = "chapter" if text.lower().startswith("chapter ") else "appendix"
            signal = "// STORY TRANSMISSION" if current_kind == "chapter" else "// REFERENCE PACKET"
            output.append(
                f'<section class="{current_kind}-section transmission-section" id="{section_id}" '
                f'data-nav-title="{html.escape(text, quote=True)}">'
                f'<div class="section-signal">{signal}</div>'
                f'<h2>{html.escape(text)}</h2>'
            )
            sections.append(Section(section_id, text, current_kind))
            section_open = True
            chapter_content_count = 0
            figures = render_figures(paragraph, relationships)
            if figures:
                output.append(figures)
            previous_blank = False
            continue

        if style == "Heading3" and text:
            heading_id = unique_id(text, used_ids)
            output.append(f'<h3 id="{heading_id}">{html.escape(text)}</h3>')
            previous_blank = False
            continue

        figures = render_figures(paragraph, relationships) if paragraph_index >= 4097 else ""
        if not section_open and (text or figures):
            output.append('<section class="interstitial-section transmission-section">')
            section_open = True
        if figures:
            output.append(figures)

        if not text:
            previous_blank = True
            continue

        paragraph_markup = run_chunks(paragraph, footnotes)
        classes: list[str] = []
        if style == "ListParagraph":
            classes.append("list-paragraph")
        if current_kind == "chapter":
            chapter_content_count += 1
            if chapter_content_count == 1 and re.match(r"^\[\d+]", text):
                classes.append("scene-date")
            elif chapter_content_count == 2 and len(text) < 100:
                classes.append("scene-place")
            elif previous_blank and len(text) < 90 and not re.search(r"[.!?]$", text):
                classes.append("scene-stamp")
        class_attribute = f' class="{" ".join(classes)}"' if classes else ""
        output.append(f"<p{class_attribute}>{paragraph_markup}</p>")
        previous_blank = False

    if section_open:
        output.append("</section>")
    return "\n".join(output), sections


def redirect_document(target: str, title: str) -> str:
    escaped_target = html.escape(target, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url={escaped_target}">
  <link rel="canonical" href="{escaped_target}">
  <title>{html.escape(title)} · A Mote in Shadow</title>
</head>
<body>
  <p>This page moved to <a href="{escaped_target}">{html.escape(title)}</a>.</p>
  <script>location.replace({json.dumps(target)});</script>
</body>
</html>
"""


def write_redirects(repo: Path, sections: list[Section]) -> None:
    chapters_dir = repo / "chapters"
    appendices_dir = repo / "appendices"
    chapters_dir.mkdir(exist_ok=True)
    appendices_dir.mkdir(exist_ok=True)
    wanted: set[Path] = set()

    for section in sections:
        if section.kind == "chapter":
            path = chapters_dir / f"{section.section_id}.html"
        elif section.kind == "appendix":
            path = appendices_dir / f"appendix-{section.section_id}.html"
        elif section.kind == "about":
            path = appendices_dir / "appendix-about-the-author.html"
        else:
            continue
        path.write_text(redirect_document(f"../index.html#{section.section_id}", section.title), encoding="utf-8")
        wanted.add(path.resolve())

    for directory in (chapters_dir, appendices_dir):
        for old_page in directory.glob("*.html"):
            if old_page.resolve() not in wanted:
                old_page.unlink()


def build(args: argparse.Namespace) -> None:
    repo = Path(__file__).resolve().parents[1]
    manuscript = Path(args.manuscript).resolve()
    template = repo / "templates" / "index.html"
    assets = repo / "assets"
    assets.mkdir(exist_ok=True)

    with zipfile.ZipFile(manuscript) as archive:
        footnotes = read_footnotes(archive)
        relationships = image_relationships(archive)
        document_root = ET.fromstring(archive.read("word/document.xml"))
        book_markup, sections = render_manuscript(document_root, footnotes, relationships)
        extract_figures(archive, assets / "figures")

    cover = Path(args.cover).resolve()
    social_cover = Path(args.social_cover).resolve()
    shutil.copy2(cover, assets / "cover.jpg")
    shutil.copy2(social_cover, assets / "social-cover.jpg")
    with Image.open(cover) as cover_image:
        favicon = ImageOps.fit(cover_image.convert("RGB"), (192, 192), method=Image.Resampling.LANCZOS)
        favicon.save(assets / "favicon.png", optimize=True)

    chapter_count = sum(section.kind == "chapter" for section in sections)
    page = template.read_text(encoding="utf-8")
    asset_digest = hashlib.sha256()
    for asset_path in (repo / "css" / "style.css", repo / "js" / "main.js"):
        asset_digest.update(asset_path.read_bytes())
    asset_version = asset_digest.hexdigest()[:12]
    replacements = {
        "{{BOOK_CONTENT}}": book_markup,
        "{{CHAPTER_COUNT}}": str(chapter_count),
        "{{NOTE_COUNT}}": str(len(footnotes)),
        "{{ASSET_VERSION}}": asset_version,
    }
    for placeholder, value in replacements.items():
        page = page.replace(placeholder, value)
    (repo / "index.html").write_text(page, encoding="utf-8", newline="\n")
    write_redirects(repo, sections)

    print(f"Built {chapter_count} chapters and {len(footnotes)} translation notes from {manuscript.name}.")


def parse_args() -> argparse.Namespace:
    repo = Path(__file__).resolve().parents[1]
    workspace = repo.parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manuscript",
        default=repo.parent / "A Mote in Shadow - A.N. Alex - Paperback - Final Draft.docx",
        help="Path to the canonical DOCX manuscript.",
    )
    parser.add_argument(
        "--cover",
        default=workspace / "KDP" / "AMS" / "web_1200x1920_72dpi.jpg",
        help="Path to the web cover image.",
    )
    parser.add_argument(
        "--social-cover",
        default=workspace / "KDP" / "AMS" / "social_og_1200x630_72dpi.jpg",
        help="Path to the social preview image.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    build(parse_args())
