/* ==========================================================================
   Site JS (sidebar toggle, theme toggle, image handling, include loader,
   active nav highlighting)
   ========================================================================== */

// Wait for DOM content to be loaded
document.addEventListener('DOMContentLoaded', function () {
  // Initialize sidebar toggle
  initSidebarToggle();

  // Initialize theme toggle
  initThemeToggle();

  // Initialize image handling
  initImageHandling();
});

/* ===========================
   Sidebar toggle functionality
   =========================== */
function initSidebarToggle() {
  const menuToggle = document.querySelector('.menu-toggle');
  const sidebar = document.querySelector('.sidebar');

  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', function () {
      sidebar.classList.toggle('active');
    });

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function (event) {
      if (
        window.innerWidth <= 768 &&
        !sidebar.contains(event.target) &&
        event.target !== menuToggle
      ) {
        sidebar.classList.remove('active');
      }
    });
  }
}

/* =========================
   Theme toggle functionality
   ========================= */
function initThemeToggle() {
  const themeToggle = document.querySelector('.theme-toggle');

  if (themeToggle) {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      document.body.setAttribute('data-theme', savedTheme);
    }

    // Toggle theme on button click
    themeToggle.addEventListener('click', function () {
      const currentTheme = document.body.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

      document.body.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
    });
  }
}

/* ==========================
   Image handling functionality
   ========================== */
function initImageHandling() {
  const images = document.querySelectorAll('.novel-image');
  const imageOverlay = document.querySelector('.image-overlay');

  if (images.length > 0 && imageOverlay) {
    images.forEach((image) => {
      // Add click handler to expand/rotate images
      image.addEventListener('click', function () {
        this.classList.toggle('expanded');
        imageOverlay.classList.toggle('active');
      });
    });

    // Add click handler to close expanded images
    imageOverlay.addEventListener('click', function () {
      const expandedImage = document.querySelector('.novel-image.expanded');
      if (expandedImage) {
        expandedImage.classList.remove('expanded');
        imageOverlay.classList.remove('active');
      }
    });
  }
}

/* =========================================
   Simple include loader for the new nav bar
   - Replaces elements with [data-include="..."]
   - Dispatches "include:loaded" event when done
   ========================================= */
document.addEventListener('DOMContentLoaded', async () => {
  const zones = document.querySelectorAll('[data-include]');
  if (!zones.length) return;

  for (const zone of zones) {
    const target = zone.getAttribute('data-include'); // e.g., "nav.html"
    // Resolve URL relative to the current page (your chapter file)
    const url = new URL(target, location.href).toString();
    console.log('[include] fetching:', url);

    try {
      const res = await fetch(url, { cache: 'no-cache' });
      if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
      const html = await res.text();
      // Replace the placeholder node with the fetched markup
      zone.outerHTML = html;
      console.log('[include] injected:', url);

      // Signal that this include finished
      document.dispatchEvent(new CustomEvent('include:loaded', { detail: { url } }));
    } catch (err) {
      console.error('[include] failed:', url, err);
      zone.innerHTML = `
        <div style="padding:.75rem;border:1px solid #c33;color:#c33;background:#fee">
          Failed to load <code>${url}</code> – ${err.message}.
          Check the path and that you're serving over http(s), not file://
        </div>`;
    }
  }
});

/* =========================================
   Active nav highlighter
   - Highlights the link for the current page
   - Expands matching subnavs
   - Updates on history/hash changes
   ========================================= */

/**
 * Normalize a URL to a comparable path (lowercase, no query/hash,
 * treat "/x/" and "/x/index.html" as the same, remove trailing slash except root).
 */
function normalizePath(u) {
  try {
    const url = new URL(u, location.origin);
    let p = url.pathname;

    // Treat /x/index.html and /x/ as the same
    p = p.replace(/\/index\.html$/i, '/');

    // Remove trailing slash (except root)
    if (p.length > 1 && p.endsWith('/')) p = p.slice(0, -1);

    // Lowercase & decode for consistency
    p = decodeURIComponent(p).toLowerCase();

    return p;
  } catch {
    return '';
  }
}

/**
 * Finds and sets the active state on the best-matching nav link:
 * 1) If a hash is present and a subnav link matches it, prefer that.
 * 2) Else pick exact file match.
 * 3) Else use the longest prefix match (helps when linking to a section root).
 */
function initActiveNavHighlight() {
  // Your nav is injected as <nav class="sidebar">...</nav> in nav.html
  const sidebarNav = document.querySelector('nav.sidebar');
  if (!sidebarNav) return;

  const navLinks = sidebarNav.querySelectorAll('a[href]');
  if (!navLinks.length) return;

  const herePath = normalizePath(location.pathname + location.search);
  const hereHash = (location.hash || '').trim();

  // Clear previous states
  navLinks.forEach((a) => {
    a.classList.remove('active', 'current');
    a.removeAttribute('aria-current');
    a.closest('li')?.classList.remove('active', 'current');
  });

  // Helper to mark an anchor and expand containing groups
  const markActive = (a) => {
    a.classList.add('active');
    a.setAttribute('aria-current', 'page');
    a.closest('li')?.classList.add('active');

    // Expand any parent "subnav-list" containers, if you collapse them via CSS/JS
    const subnav = a.closest('.subnav-list');
    if (subnav) {
      // If you use a collapsible marker, set it here:
      subnav.classList.add('open');
      subnav.closest('li')?.classList.add('open');
    }

    // Optionally ensure visibility in the sidebar
    a.scrollIntoView({ block: 'nearest' });
  };

  // 1) If hash exists and a subnav link matches it (same page), prefer that
  if (hereHash) {
    const hashTarget = Array.from(navLinks).find((a) => {
      // Same page (ignoring hash) and same hash
      const linkUrl = new URL(a.getAttribute('href'), location.href);
      const linkPath = normalizePath(linkUrl.pathname);
      return linkPath === herePath && linkUrl.hash === hereHash;
    });
    if (hashTarget) {
      markActive(hashTarget);
      return;
    }
  }

  // 2) Try exact match on path
  let best = null;
  let bestLen = -1;

  navLinks.forEach((a) => {
    const linkUrl = new URL(a.getAttribute('href'), location.href);
    const linkPath = normalizePath(linkUrl.pathname);

    if (!linkPath) return;

    if (linkPath === herePath) {
      best = a;
      bestLen = Infinity; // exact beats all
    } else if (herePath.startsWith(linkPath) && linkPath.length > bestLen) {
      // 3) Longest prefix match as fallback
      best = a;
      bestLen = linkPath.length;
    }
  });

  if (best) {
    markActive(best);
  }
}

// Re-run highlight after the nav include is injected
document.addEventListener('include:loaded', (e) => {
  // If you ever include more than one file, you can scope by filename:
  // e.g., if (e.detail?.url?.endsWith('/nav.html')) { ... }
  initActiveNavHighlight();
});

// Keep it in sync on navigation within the browser
window.addEventListener('popstate', initActiveNavHighlight);
window.addEventListener('hashchange', initActiveNavHighlight);

// Optional: If your site uses JS-driven internal link navigation (pushState),
// you can call initActiveNavHighlight() after you update history.
// Example:
// document.addEventListener('click', (e) => {
//   const a = e.target.closest('a[href^="./"], a[href^="../"], a[href^="/"]');
//   if (!a || a.target || a.hasAttribute('download') || a.getAttribute('rel') === 'external') return;
//   // ... do your pushState SPA handling ...
//   // After changing history, call:
//   // initActiveNavHighlight();
// });

