(function () {
  'use strict';

  const root = document.documentElement;
  const body = document.body;
  const contentsPanel = document.getElementById('contents-panel');
  const contentsScrim = document.getElementById('contents-scrim');
  const menuToggle = document.getElementById('menu-toggle');
  const contentsClose = document.getElementById('contents-close');
  const generatedContents = document.getElementById('generated-contents');
  const locationLabel = document.getElementById('signal-location');
  const progressBar = document.getElementById('reading-progress-bar');
  const prefersReducedMotion = matchMedia('(prefers-reduced-motion: reduce)');

  function setTheme(theme) {
    root.dataset.theme = theme;
    localStorage.setItem('ams-theme', theme);
    const toggle = document.getElementById('theme-toggle');
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    toggle.setAttribute('aria-label', `Switch to ${nextTheme} theme`);
    toggle.querySelector('.theme-icon').textContent = theme === 'dark' ? '☼' : '◐';
  }

  document.getElementById('theme-toggle').addEventListener('click', function () {
    setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark');
  });
  setTheme(root.dataset.theme || 'dark');

  function setContents(open) {
    contentsPanel.classList.toggle('open', open);
    contentsScrim.hidden = !open;
    menuToggle.setAttribute('aria-expanded', String(open));
    body.style.overflow = open && innerWidth <= 1120 ? 'hidden' : '';
    if (open) document.getElementById('contents-filter').focus();
  }

  menuToggle.addEventListener('click', () => setContents(!contentsPanel.classList.contains('open')));
  contentsClose.addEventListener('click', () => setContents(false));
  contentsScrim.addEventListener('click', () => setContents(false));

  const navigableSections = Array.from(document.querySelectorAll('#book > section[data-nav-title]'));

  function sectionKind(section) {
    if (section.classList.contains('part-divider')) return 'part';
    if (section.classList.contains('chapter-section')) return 'chapter';
    if (section.classList.contains('appendix-section')) return 'appendix';
    if (section.classList.contains('about-section')) return 'about';
    return section.id === 'top' ? 'cover' : 'front';
  }

  function buildContents() {
    const fragment = document.createDocumentFragment();
    navigableSections.forEach((section, index) => {
      const link = document.createElement('a');
      const code = document.createElement('span');
      const title = document.createElement('span');
      const kind = sectionKind(section);
      link.className = 'toc-link';
      link.dataset.kind = kind;
      link.dataset.search = section.dataset.navTitle.toLowerCase();
      link.href = `#${section.id}`;
      code.className = 'toc-code';
      code.textContent = String(index).padStart(2, '0');
      title.textContent = section.dataset.navTitle;
      link.append(code, title);
      link.addEventListener('click', () => setContents(false));
      fragment.append(link);
    });
    generatedContents.replaceChildren(fragment);
  }

  function buildSectionPagers() {
    const readingSections = navigableSections.filter((section) => {
      const kind = sectionKind(section);
      return kind === 'chapter' || kind === 'appendix' || kind === 'about';
    });
    readingSections.forEach((section, index) => {
      const pager = document.createElement('nav');
      pager.className = 'section-pager';
      pager.setAttribute('aria-label', 'Previous and next sections');
      const previous = readingSections[index - 1];
      const next = readingSections[index + 1];
      pager.append(
        previous ? pagerLink(previous, '← PREVIOUS') : document.createElement('span'),
        next ? pagerLink(next, 'NEXT →') : document.createElement('span')
      );
      section.append(pager);
    });
  }

  function pagerLink(section, direction) {
    const link = document.createElement('a');
    const label = document.createElement('span');
    const title = document.createElement('strong');
    link.className = 'pager-link';
    link.href = `#${section.id}`;
    label.textContent = direction;
    title.textContent = section.dataset.navTitle;
    link.append(label, title);
    return link;
  }

  buildContents();
  buildSectionPagers();

  document.getElementById('contents-filter').addEventListener('input', function () {
    const query = this.value.trim().toLowerCase();
    const links = Array.from(generatedContents.querySelectorAll('.toc-link'));
    let visible = 0;
    links.forEach((link) => {
      const matches = !query || link.dataset.search.includes(query);
      link.hidden = !matches;
      visible += Number(matches);
    });
    const oldEmpty = generatedContents.querySelector('.toc-empty');
    if (oldEmpty) oldEmpty.remove();
    if (!visible) {
      const empty = document.createElement('p');
      empty.className = 'toc-empty';
      empty.textContent = 'NO MATCHING SIGNALS';
      generatedContents.append(empty);
    }
  });

  function markActive(section) {
    if (!section) return;
    generatedContents.querySelectorAll('.toc-link').forEach((link) => {
      const active = link.hash === `#${section.id}`;
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
    locationLabel.textContent = section.dataset.navTitle.toUpperCase();
    if (section.id !== 'top') localStorage.setItem('ams-last-section', section.id);
  }

  const sectionObserver = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
    if (visible[0]) markActive(visible[0].target);
  }, { rootMargin: '-14% 0px -66% 0px', threshold: [0, 0.01, 0.15] });
  navigableSections.forEach((section) => sectionObserver.observe(section));

  const savedSection = localStorage.getItem('ams-last-section');
  const savedTarget = savedSection && document.getElementById(savedSection);
  if (savedTarget && !location.hash) {
    const begin = document.getElementById('begin-reading');
    begin.href = `#${savedSection}`;
    begin.firstChild.textContent = `RESUME · ${savedTarget.dataset.navTitle.toUpperCase()} `;
  }

  let progressQueued = false;
  function updateProgress() {
    const documentHeight = document.documentElement.scrollHeight - innerHeight;
    const progress = documentHeight > 0 ? Math.min(1, Math.max(0, scrollY / documentHeight)) : 0;
    progressBar.style.width = `${progress * 100}%`;
    progressQueued = false;
  }
  addEventListener('scroll', () => {
    if (!progressQueued) {
      progressQueued = true;
      requestAnimationFrame(updateProgress);
    }
  }, { passive: true });
  updateProgress();

  const translateToggle = document.getElementById('translate-toggle');
  function setAutoTranslate(enabled) {
    body.classList.toggle('auto-translate', enabled);
    translateToggle.setAttribute('aria-pressed', String(enabled));
    translateToggle.title = enabled ? 'Show original annotated phrases' : 'Translate every annotated phrase';
    localStorage.setItem('ams-auto-translate', String(enabled));
  }
  translateToggle.addEventListener('click', () => {
    setAutoTranslate(translateToggle.getAttribute('aria-pressed') !== 'true');
  });
  setAutoTranslate(localStorage.getItem('ams-auto-translate') === 'true');

  const translationUnits = Array.from(document.querySelectorAll('.translation-unit'));

  function positionPopover(unit) {
    const trigger = unit.querySelector('.translation-trigger');
    const popover = unit.querySelector('.translation-popover');
    const rect = trigger.getBoundingClientRect();
    const halfWidth = Math.min(200, (innerWidth - 24) / 2);
    const left = Math.max(halfWidth + 12, Math.min(innerWidth - halfWidth - 12, rect.left + rect.width / 2));
    const below = rect.top < popover.offsetHeight + 80;
    unit.classList.toggle('popover-below', below);
    unit.style.setProperty('--tooltip-left', `${left}px`);
    unit.style.setProperty('--tooltip-top', `${below ? rect.bottom : rect.top}px`);
  }

  function decode(unit) {
    if (body.classList.contains('auto-translate')) return;
    positionPopover(unit);
    unit.classList.remove('is-decoding');
    void unit.offsetWidth;
    unit.classList.add('is-decoding');
  }

  function closeUnpinned(unit) {
    if (!unit.classList.contains('is-pinned')) unit.classList.remove('is-decoding');
  }

  translationUnits.forEach((unit) => {
    const trigger = unit.querySelector('.translation-trigger');
    unit.addEventListener('pointerenter', () => decode(unit));
    unit.addEventListener('pointerleave', () => closeUnpinned(unit));
    trigger.addEventListener('focus', () => decode(unit));
    trigger.addEventListener('blur', () => closeUnpinned(unit));
    trigger.addEventListener('click', (event) => {
      event.stopPropagation();
      const pinned = !unit.classList.contains('is-pinned');
      translationUnits.forEach((other) => other.classList.remove('is-pinned', 'is-decoding'));
      unit.classList.toggle('is-pinned', pinned);
      if (pinned) decode(unit);
    });
  });

  document.addEventListener('click', () => {
    translationUnits.forEach((unit) => unit.classList.remove('is-pinned', 'is-decoding'));
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      translationUnits.forEach((unit) => unit.classList.remove('is-pinned', 'is-decoding'));
      setContents(false);
    }
  });

  const fontOutput = document.getElementById('font-size-output');
  let fontScale = Number(localStorage.getItem('ams-font-scale') || 1);
  function setFontScale(next) {
    fontScale = Math.min(1.25, Math.max(0.85, Math.round(next * 20) / 20));
    root.style.setProperty('--reader-scale', fontScale);
    fontOutput.value = `${Math.round(fontScale * 100)}%`;
    fontOutput.textContent = fontOutput.value;
    localStorage.setItem('ams-font-scale', String(fontScale));
  }
  document.getElementById('font-smaller').addEventListener('click', () => setFontScale(fontScale - 0.05));
  document.getElementById('font-larger').addEventListener('click', () => setFontScale(fontScale + 0.05));
  setFontScale(fontScale);

  const guideToggle = document.getElementById('guide-toggle');
  const guide = document.getElementById('reader-guide');
  guideToggle.addEventListener('click', () => {
    const expanded = guideToggle.getAttribute('aria-expanded') !== 'true';
    guideToggle.setAttribute('aria-expanded', String(expanded));
    guide.hidden = !expanded;
  });

  const dialog = document.getElementById('image-dialog');
  const dialogImage = document.getElementById('dialog-image');
  document.querySelectorAll('.figure-open').forEach((button) => {
    button.addEventListener('click', () => {
      const source = button.dataset.image;
      const inlineImage = button.querySelector('img');
      dialogImage.src = source;
      dialogImage.alt = inlineImage ? inlineImage.alt : '';
      dialog.showModal();
    });
  });
  dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  });

  addEventListener('resize', () => {
    if (innerWidth > 1120) setContents(false);
    document.querySelectorAll('.translation-unit.is-decoding, .translation-unit.is-pinned').forEach(positionPopover);
  });

  if (prefersReducedMotion.matches) body.classList.add('reduced-motion');
}());
