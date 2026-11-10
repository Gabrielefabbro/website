#!/usr/bin/env python3
"""Build the personal website from content.toml.

Usage:  python3 build.py            -> writes _site/index.html (+ assets)
No third-party dependencies: needs Python >= 3.11 (for tomllib).
"""
from __future__ import annotations

import datetime as dt
import html
import re
import shutil
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"


# ── helpers ──────────────────────────────────────────────────────────────────
def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def inline(s: str) -> str:
    """Escape, then apply a tiny subset of Markdown: `code`, **b**, *i*, [t](u)."""
    s = esc(s.strip())
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda m: f'<a href="{m.group(2)}"{ext(m.group(2))}>{m.group(1)}</a>',
        s,
    )
    return s


def ext(url: str) -> str:
    return ' target="_blank" rel="noopener"' if url.startswith("http") else ""


def paras(s: str) -> str:
    blocks = [b for b in re.split(r"\n\s*\n", (s or "").strip()) if b.strip()]
    return "\n".join(f"<p>{inline(' '.join(b.split()))}</p>" for b in blocks)


def initials(name: str) -> str:
    return "".join(w[0] for w in name.split()[:2]).upper()


ICONS = {
    # open systems: molecule exchanging electrons with a surface
    "open": '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M6 38h36" /><path d="M6 43h36" stroke-dasharray="2 4"/>'
            '<circle cx="24" cy="18" r="6"/><circle cx="12" cy="10" r="3"/><circle cx="36" cy="10" r="3"/>'
            '<path d="M19 15l-5-3M29 15l5-3"/><path d="M24 26v8" stroke-dasharray="2 3"/><path d="M21 31l3 3 3-3"/></svg>',
    # relativity: orbit with fast electron & light-cone-ish trail
    "relativity": '<svg viewBox="0 0 48 48" aria-hidden="true"><ellipse cx="24" cy="24" rx="19" ry="8" transform="rotate(-25 24 24)"/>'
                  '<circle cx="24" cy="24" r="4.5"/><circle cx="39.5" cy="15.5" r="2.5" class="fill"/>'
                  '<path d="M33 12.5c-4-.8-8 0-12 2" stroke-dasharray="1.5 3"/></svg>',
    # nucleus: prolate quadrupolar nucleus in a field gradient
    "nucleus": '<svg viewBox="0 0 48 48" aria-hidden="true"><ellipse cx="24" cy="24" rx="7" ry="11"/>'
               '<path d="M24 4v6M24 38v6M4 24h6M38 24h6"/><path d="M21 7l3-3 3 3M21 41l3 3 3-3"/>'
               '<path d="M7 21l-3 3 3 3M41 21l3 3-3 3"/></svg>',
    "code": '<svg viewBox="0 0 48 48" aria-hidden="true"><path d="M17 14L7 24l10 10M31 14l10 10-10 10M27 10l-6 28"/></svg>',
}

LINK_ICONS = {
    "email": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>',
    "orcid": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9 10v7M9 7.2v.1M12.5 10h1.5a3.5 3.5 0 010 7h-1.5z"/></svg>',
    "scholar": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 9l10-6 10 6-10 6z"/><path d="M6 11.5V16c0 1.5 2.7 3 6 3s6-1.5 6-3v-4.5"/></svg>',
    "github": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 19c-4 1.5-4-2-6-2.5m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 00-1.3-3.2 4.2 4.2 0 00-.1-3.2s-1-.3-3.4 1.3a11.6 11.6 0 00-6 0C6.8 2.3 5.7 2.6 5.7 2.6a4.2 4.2 0 00-.1 3.2A4.6 4.6 0 004.3 9c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2v3.5"/></svg>',
    "cv": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 3H6a2 2 0 00-2 2v14a2 2 0 002 2h12a2 2 0 002-2V9z"/><path d="M14 3v6h6M12 12v6M9 15l3 3 3-3"/></svg>',
}

LINK_LABELS = {"email": "Email", "orcid": "ORCID", "scholar": "Scholar", "github": "GitHub", "cv": "CV (PDF)"}


# ── sections ─────────────────────────────────────────────────────────────────
def links_html(links: dict) -> str:
    out = []
    for key in ("email", "cv", "orcid", "scholar", "github"):
        val = links.get(key)
        if not val:
            continue
        href = f"mailto:{val}" if key == "email" else val
        out.append(
            f'<a class="pill" href="{esc(href)}"{ext(href)}>{LINK_ICONS[key]}<span>{LINK_LABELS[key]}</span></a>'
        )
    return "\n".join(out)


def section(sid: str, num: int, label: str, body: str, cls: str = "") -> str:
    return f"""
<section id="{sid}" class="section {cls}">
  <div class="wrap">
    <header class="section-head reveal"><span class="kicker">{num:02d}</span><h2>{esc(label)}</h2></header>
    {body}
  </div>
</section>"""


def pub_html(p: dict, surname: str) -> str:
    authors = ", ".join(
        f"<strong>{esc(a.strip())}</strong>" if surname and surname in a else esc(a.strip())
        for a in p.get("authors", "").split(",")
    )
    # ACS style: J. Phys. Chem. A 2025, 129, 6942–6958  /  arXiv:2610.38873 (2026)
    journal = p.get("journal", "")
    if journal.lower() == "arxiv" and p.get("arxiv"):
        venue = f"<em>arXiv</em>:{esc(p['arxiv'])} ({esc(p.get('year', ''))})"
    else:
        venue = f"<em>{esc(journal)}</em> {esc(p.get('year', ''))}"
        if p.get("volume"):
            venue += f", <strong class=\"vol\">{esc(p['volume'])}</strong>"
        if p.get("pages"):
            venue += f", {esc(p['pages'])}"
    actions = []
    if p.get("doi"):
        actions.append(f'<a class="tag link" href="https://doi.org/{esc(p["doi"])}" target="_blank" rel="noopener">DOI</a>')
    if p.get("arxiv"):
        actions.append(f'<a class="tag link" href="https://arxiv.org/abs/{esc(p["arxiv"])}" target="_blank" rel="noopener">arXiv</a>')
    if p.get("pdf"):
        actions.append(f'<a class="tag link" href="{esc(p["pdf"])}"{ext(p["pdf"])}>PDF</a>')
    if p.get("note"):
        actions.append(f'<span class="tag note">{esc(p["note"])}</span>')
    url = f"https://doi.org/{p['doi']}" if p.get("doi") else (f"https://arxiv.org/abs/{p['arxiv']}" if p.get("arxiv") else "")
    title = esc(p.get("title", ""))
    title = f'<a href="{esc(url)}" target="_blank" rel="noopener">{title}</a>' if url else title
    toc = ""
    if p.get("toc"):
        if not (ROOT / p["toc"]).exists():
            print(f"⚠ missing TOC image: {p['toc']}", file=sys.stderr)
        toc = (f'<button class="pub-toc" type="button" data-zoom="{esc(p["toc"])}" aria-label="Enlarge TOC graphic">'
               f'<img src="{esc(p["toc"])}" alt="Table-of-contents graphic: {esc(p.get("title", ""))}" loading="lazy"></button>')
    return f"""<li class="pub reveal{' has-toc' if toc else ''}">
  <div class="pub-text">
    <h3 class="pub-title">{title}</h3>
    <p class="pub-authors">{authors}</p>
    <p class="pub-venue">{venue}</p>
    <div class="pub-actions">{''.join(actions)}</div>
  </div>
  {toc}
</li>"""


def file_size(rel: str) -> str:
    f = ROOT / rel
    if not f.exists():
        print(f"⚠ missing file: {rel}", file=sys.stderr)
        return ""
    n = f.stat().st_size
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{n / 1e3:.0f} KB"


def slides_btn(t: dict) -> str:
    f = t.get("slides")
    if not f:
        return ""
    size = file_size(f)
    return (f'<a class="tag link slides" href="{esc(f)}" target="_blank" rel="noopener" '
            f'title="Open slides (PDF{", " + size if size else ""})">{LINK_ICONS["cv"]}Slides</a>')


def docs_html(docs: list) -> str:
    if not docs:
        return ""
    cards = []
    for d in docs:
        f = d.get("file", "")
        size = file_size(f) if f else ""
        cover = (f'<img src="{esc(d["cover"])}" alt="First page of {esc(d.get("title", ""))}" loading="lazy">'
                 if d.get("cover") else "")
        shape = "landscape" if "slide" in d.get("kind", "").lower() else "portrait"
        meta = " · ".join(x for x in (d.get("meta", ""), f"PDF, {size}" if size else "") if x)
        hal = (f'<a class="button ghost small" href="{esc(d["hal"])}" target="_blank" rel="noopener">HAL</a>'
               if d.get("hal") else "")
        cards.append(f"""<article class="doc reveal">
  <a class="doc-cover {shape}" href="{esc(f)}" target="_blank" rel="noopener" aria-label="Read {esc(d.get('title', ''))} online">{cover}</a>
  <div class="doc-body">
    <span class="doc-kind">{esc(d.get('kind', ''))}</span>
    <h4>{esc(d.get('title', ''))}</h4>
    <p class="doc-meta">{esc(meta)}</p>
    <div class="doc-actions">
      <a class="button small" href="{esc(f)}" target="_blank" rel="noopener">Read online</a>
      <a class="button ghost small" href="{esc(f)}" download>{LINK_ICONS['cv']}Download</a>
      {hal}
    </div>
  </div>
</article>""")
    return f'<div class="docs">{"".join(cards)}</div>'


def build(c: dict) -> str:
    site, person, links = c.get("site", {}), c.get("person", {}), c.get("links", {})
    name = person.get("name", "")
    surname = name.split()[-1] if name else ""
    updated = site.get("updated") or dt.date.today().strftime("%B %Y")

    # hero portrait
    if person.get("photo"):
        portrait = f'<img src="{esc(person["photo"])}" alt="Portrait of {esc(name)}">'
    else:
        portrait = f'<span class="initials">{esc(initials(name))}</span>'

    nav_items = [("about", "About"), ("now", "Now"), ("research", "Research"), ("phd", "PhD"),
                 ("publications", "Publications"), ("talks", "Talks"), ("cv", "CV")]

    sections, n = [], 0

    def add(sid, label, body, cls=""):
        nonlocal n
        n += 1
        sections.append(section(sid, n, label, body, cls))

    # About
    if c.get("about"):
        add("about", "About", f'<div class="prose lead reveal">{paras(c["about"]["text"])}</div>')

    # Now
    if c.get("now"):
        now = c["now"]
        add("now", "What I do now", f"""
<article class="now-card reveal">
  <div class="now-meta"><span class="live-dot" aria-hidden="true"></span><span>Current project</span></div>
  <h3>{esc(now.get('heading', ''))}</h3>
  <p class="muted small">{esc(now.get('place', ''))}</p>
  <div class="prose">{paras(now.get('text', ''))}</div>
</article>""")

    # Research lines
    if c.get("research"):
        cards = "\n".join(
            f"""<article class="card reveal">
  <div class="icon">{ICONS.get(r.get('icon', ''), ICONS['code'])}</div>
  <h3>{esc(r.get('title', ''))}</h3>
  <p>{inline(' '.join(r.get('text', '').split()))}</p>
</article>""" for r in c["research"])
        add("research", "Research lines", f'<div class="grid-3">{cards}</div>')

    # PhD
    if c.get("phd"):
        p = c["phd"]
        hl = "".join(f"<li>{inline(h)}</li>" for h in p.get("highlights", []))
        facts = "".join(
            f"<div><dt>{k}</dt><dd>{esc(v)}</dd></div>"
            for k, v in (("Period", p.get("period")), ("Defended", p.get("defended")), ("Advisor", p.get("advisor")),
                         ("Project", p.get("project")), ("Institution", p.get("place"))) if v)
        add("phd", "PhD", f"""
<div class="phd reveal">
  <div class="phd-main">
    <h3 class="phd-title">{esc(p.get('title', ''))}</h3>
    <div class="prose">{paras(p.get('text', ''))}</div>
  </div>
  <aside class="phd-side">
    <dl class="facts">{facts}</dl>
    {'<h4>Highlights</h4><ul class="checks">' + hl + '</ul>' if hl else ''}
  </aside>
</div>{docs_html(p.get('documents', []))}""")

    # Publications grouped by year
    if c.get("publications"):
        by_year: dict = {}
        for pub in c["publications"]:
            by_year.setdefault(pub.get("year", ""), []).append(pub)
        groups = "\n".join(
            f"""<div class="pub-year"><div class="year reveal">{esc(y)}</div>
<ol class="pubs">{''.join(pub_html(pb, surname) for pb in pubs)}</ol></div>"""
            for y, pubs in sorted(by_year.items(), key=lambda kv: str(kv[0]), reverse=True))
        sw = ""
        if c.get("software"):
            items = "".join(
                f"""<li><span class="sw-name">{f'<a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["name"])}</a>' if s.get('url') else esc(s.get('name', ''))}</span>
<span class="sw-text">{inline(s.get('text', ''))}</span></li>""" for s in c["software"])
            sw = f'<div class="software reveal"><h3>Code contributions</h3><ul>{items}</ul></div>'
        add("publications", "Publications", groups + sw)

    # Talks
    if c.get("talks"):
        rows = "".join(
            f"""<li class="talk reveal">
  <span class="talk-date">{esc(t.get('date', ''))}</span>
  <div><p class="talk-title">{esc(t.get('title', ''))}</p>
  <p class="talk-event">{esc(t.get('event', ''))} · {esc(t.get('place', ''))}</p></div>
  <div class="talk-side"><span class="tag kind">{esc(t.get('kind', ''))}</span>{slides_btn(t)}</div>
</li>""" for t in c["talks"])
        add("talks", "Talks", f'<ul class="talks">{rows}</ul>')

    # CV: education + service
    if c.get("education") or c.get("service"):
        edu = "".join(
            f"""<li class="reveal"><span class="tl-period">{esc(e.get('period', ''))}</span>
<p class="tl-title">{esc(e.get('degree', ''))}</p><p class="tl-place">{esc(e.get('place', ''))}</p>
{f'<p class="tl-note">{esc(e["note"])}</p>' if e.get('note') else ''}</li>""" for e in c.get("education", []))
        srv = "".join(
            f'<li class="reveal"><span class="tl-period">{esc(s.get("date", ""))}</span><p class="tl-title">{inline(s.get("text", ""))}</p></li>'
            for s in c.get("service", []))
        cv_btn = (f'<a class="button" href="{esc(links["cv"])}">{LINK_ICONS["cv"]}Download full CV</a>'
                  if links.get("cv") else "")
        add("cv", "Education & service", f"""
<div class="cv-grid">
  <div><h3 class="col-head">Education</h3><ol class="timeline">{edu}</ol></div>
  <div><h3 class="col-head">Service</h3><ol class="timeline">{srv}</ol>
  <div class="cv-cta reveal">{cv_btn}</div></div>
</div>""")

    nav = "".join(f'<a href="#{sid}">{lbl}</a>' for sid, lbl in nav_items if any(f'id="{sid}"' in s for s in sections))
    css = (ROOT / "theme" / "style.css").read_text()
    js = (ROOT / "theme" / "site.js").read_text()
    og_url = f'<meta property="og:url" content="{esc(site["url"])}">' if site.get("url") else ""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(site.get('title', name))}</title>
<meta name="description" content="{esc(site.get('description', ''))}">
<meta property="og:title" content="{esc(site.get('title', name))}">
<meta property="og:description" content="{esc(site.get('description', ''))}">
<meta property="og:type" content="profile">
{og_url}
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='14' fill='%2314383f'/><text x='50%25' y='56%25' dominant-baseline='middle' text-anchor='middle' font-family='Georgia,serif' font-size='30' fill='%23f3efe6'>{esc(initials(name))}</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
{css}
</style>
</head>
<body>
<a class="skip" href="#about">Skip to content</a>
<nav class="topnav" aria-label="Sections">
  <div class="wrap nav-inner">
    <a class="brand" href="#top">{esc(name)}</a>
    <div class="nav-links">{nav}</div>
    <button class="theme-toggle" type="button" aria-label="Toggle dark mode">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path class="sun" d="M12 4V2M12 22v-2M4 12H2M22 12h-2M5.6 5.6L4.2 4.2M19.8 19.8l-1.4-1.4M5.6 18.4l-1.4 1.4M19.8 4.2l-1.4 1.4"/><circle cx="12" cy="12" r="4.5"/></svg>
    </button>
  </div>
</nav>

<header id="top" class="hero">
  <div class="hero-bg" aria-hidden="true">
    <svg viewBox="0 0 600 600" preserveAspectRatio="xMidYMid slice">
      <g class="orbits">
        <ellipse cx="300" cy="300" rx="260" ry="92"/>
        <ellipse cx="300" cy="300" rx="260" ry="92" transform="rotate(60 300 300)"/>
        <ellipse cx="300" cy="300" rx="260" ry="92" transform="rotate(120 300 300)"/>
        <ellipse cx="300" cy="300" rx="190" ry="190" class="faint"/>
      </g>
    </svg>
  </div>
  <div class="wrap hero-inner">
    <div class="hero-text">
      <p class="eyebrow">{esc(person.get('role', ''))}</p>
      <h1>{esc(name)}</h1>
      <p class="tagline">{inline(person.get('tagline', ''))}</p>
      <p class="affil">{esc(person.get('affiliation', ''))}<span class="sep">·</span>{esc(person.get('location', ''))}</p>
      <div class="pills">{links_html(links)}</div>
    </div>
    <div class="portrait">{portrait}</div>
  </div>
</header>

<main>
{''.join(sections)}
</main>

<dialog class="lightbox" aria-label="Enlarged image"><img alt=""><button type="button" class="lb-close" aria-label="Close">×</button></dialog>

<footer class="footer">
  <div class="wrap footer-inner">
    <p>© {dt.date.today().year} {esc(name)}{f' · <a href="mailto:{esc(links["email"])}">{esc(links["email"])}</a>' if links.get('email') else ''}</p>
    <p class="muted">Last updated {esc(updated)}</p>
  </div>
</footer>
<script>
{js}
</script>
</body>
</html>
"""


def main() -> int:
    src = ROOT / "content.toml"
    try:
        content = tomllib.loads(src.read_text())
    except tomllib.TOMLDecodeError as e:
        print(f"✗ content.toml has a syntax error: {e}", file=sys.stderr)
        return 1
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    if (ROOT / "assets").exists():
        shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / "index.html").write_text(build(content))
    (OUT / ".nojekyll").write_text("")
    print(f"✓ built {OUT / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
