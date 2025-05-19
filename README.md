# A Mote in Shadow

## Overview

"A Mote in Shadow" is a space opera set in a future where humanity has spread beyond the Solar System. The story follows multiple protagonists as they navigate interstellar politics, encounter alien mysteries, and confront a universe far more dangerous than they imagined.

## Story

In 66036 Sol Universal Time, the United Planets of the Local Bubble, the Spanning Worlds Independence, and the Homeworlds Federation maintain an uneasy peace after a devastating interstellar war. The story follows several protagonists:

- **Chaeyoung**: An exobiologist who accepts a mission to explore Mu Herculis and discovers alien ruins.
- **Frederik**: Captain of the cargo ship Ergo Infinitum, who accepts a suspicious contract with unexpected consequences.
- **Isabell**: An operative with the enigmatic Grayson Services Group.
- **Ai aka "Betty Blue"**: An undercover operative with a hidden agenda, working within the complex web of interstellar politics.

As their paths converge, they uncover a conspiracy involving ancient alien technology that could change humanity's future forever.

## Features

- Immersive world-building spanning multiple star systems
- Conlang integration with Di Lingua (hover tooltips for translations)
- Hard science fiction elements with ERR-AL drive technology and realistic space combat
- Multiple narrative perspectives that converge in an epic conclusion

## Reading Online

The complete novel is available to read for free on this website. Navigate through chapters using the menu or the next/previous buttons at the bottom of each chapter.

## Di Lingua Tooltips

This website uses footnote-style tooltips to provide translations for Di Lingua, the constructed language used throughout the novel. When you encounter Di Lingua phrases marked with superscript numbers, hover over them to see the English translation.

## Implementation Details

### Tooltip Implementation

The tooltips for Di Lingua translations are implemented using HTML and CSS. Here's how they work:

```html
<em>"Hao fa!"</em><em><sup class="footnote">[1]<span class="footnote-tooltip">[Di Lingua]:  Hello! ↑</span></sup></em>
```

The CSS implementation from the actual website:

```css
/* Footnotes - Superscript style */
.footnote {
  position: relative;
  cursor: pointer;
  color: var(--accent-color);
  vertical-align: super;
  font-size: 0.75em;
  font-weight: bold;
  padding: 0 2px;
}

.footnote-tooltip {
  position: absolute;
  bottom: 125%;
  left: 50%;
  transform: translateX(-50%) scale(0.95);
  width: 300px;
  max-width: 90vw;
  background-color: rgba(245, 245, 245, 0.97);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
  padding: 12px 15px;
  border-radius: 6px;
  font-size: 1.1rem;
  line-height: 1.5;
  text-align: left;
  opacity: 0;
  visibility: hidden;
  transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  z-index: 1000;
  pointer-events: none;
  font-weight: normal;
  color: var(--text-color);
}

.footnote:hover .footnote-tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateX(-50%) scale(1);
}

/* Arrow at the bottom of tooltip */
.footnote-tooltip::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  margin-left: -8px;
  border-width: 8px;
  border-style: solid;
  border-color: rgba(245, 245, 245, 0.97) transparent transparent transparent;
}

[data-theme="dark"] .footnote-tooltip {
  background-color: rgba(45, 45, 45, 0.97);
}

[data-theme="dark"] .footnote-tooltip::after {
  border-color: rgba(45, 45, 45, 0.97) transparent transparent transparent;
}
```

### Implementation Steps

1. Add the CSS to your stylesheet
2. Wrap Di Lingua phrases in `<em>` elements for italics
3. Add a superscript tag with the footnote class: `<sup class="footnote">[number]<span class="footnote-tooltip">[Di Lingua]: Translation ↑</span></sup>`
4. The tooltip appears when users hover over the footnote

### Dark Mode Support

The tooltips support dark mode through CSS variables and the `[data-theme="dark"]` selector. The tooltip background and arrow colors change accordingly.

### Responsive Design

For mobile devices, the tooltips are adjusted for better visibility:

```css
@media (max-width: 768px) {
  .footnote-tooltip {
    width: calc(100vw - 40px);
    left: 20px;
    transform: translateX(0) scale(0.95);
  }
  
  .footnote:hover .footnote-tooltip {
    transform: translateX(0) scale(1);
  }
}
```

## License

A Mote in Shadow © 2024 by A.N. Alex is licensed under CC BY 4.0.  
To view a copy of this license, visit https://creativecommons.org/licenses/by/4.0/
 
You are free to:
1. **Share** — copy and redistribute the material in any medium or format for any purpose, even commercially.
2. **Adapt** — remix, transform, and build upon the material for any purpose, even commercially.

The licensor cannot revoke these freedoms as long as you follow the license terms.
 
Under the following terms:
1. **Attribution** — You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
 
2. **No additional restrictions** — You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.


