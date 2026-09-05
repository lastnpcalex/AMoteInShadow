# A Mote in Shadow — online reader

This repository hosts the complete, free web edition of **A Mote in Shadow** by A.N. Alex.

The reader is generated from the final DOCX manuscript rather than maintained as a second hand-edited copy. It provides:

- a semantic, single-page edition with all 24 chapters and the reference appendices;
- a table of contents generated from the book's real section headings;
- 169 accessible translation notes with phrase-by-phrase decode animation;
- an **Auto Translate** mode that reveals every annotated translation in place;
- the actual Acidburn Agency header structure and navigation menu, paired with its exact chrome palette and Source Serif 4/Inter reading typography;
- fingerprinted CSS and JavaScript URLs so GitHub Pages updates cannot mix stale behavior with new markup;
- corrected, web-oriented diagrams and click-to-enlarge figures;
- a bottom-docked reading indicator that measures the novel and deliberately excludes the One Pagers;
- the publisher blurb, current cover, and direct Amazon, preferred Gumroad, and all-editions purchase paths;
- responsive reading controls, resume position, and old-URL redirects.

The site is plain static HTML, CSS, and JavaScript and can be deployed directly with GitHub Pages.

## Rebuild from the manuscript

The committed `index.html` and figure assets are generated output, so the deployed site does not require Python. To rebuild them locally:

```powershell
python -m pip install -r requirements-dev.txt
python scripts/build_reader.py
```

By default, the script expects this workspace layout:

```text
Book Cover Renders/
├── Free Online/
│   ├── A Mote in Shadow - A.N. Alex - Paperback - Final Draft.docx
│   └── AMoteInShadow/
└── KDP/AMS/
    ├── web_1200x1920_72dpi.jpg
    └── social_og_1200x630_72dpi.jpg
```

Alternate source paths can be supplied with `--manuscript`, `--cover`, and `--social-cover`.

## Translation behavior

Translation notes are read directly from `word/footnotes.xml`. The build associates each note with the annotated phrase that precedes it. In the browser, hover or focus a phrase marker to preview its translation, click to hold it open, or enable **Auto Translate** to decode all annotated phrases. Motion is minimized automatically when the operating system requests reduced motion.

## Validation

```powershell
python -m unittest discover -s tests -v
node --check js/main.js
```

## License

**A Mote in Shadow** © 2024 A.N. Alex is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
