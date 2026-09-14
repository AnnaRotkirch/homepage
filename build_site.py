"""Build the static site for annarotkirch.com.

Reads (all paths resolved from this script's own location):
  content/*.md            - page text in Markdown, one file per page
  ../media_2023_2026.csv  - international media (the media page is generated, not hand-written)
  ../media_fi_2022_2026.csv - Finnish and Finland-Swedish media
  ../talks_2024_2026.csv  - talks, used only for recording links on the media page

  files/                  - PDFs and other documents, copied to docs/files/ (links in content/ use files/<name>)

Writes:
  docs/                   - the whole site, ready for GitHub Pages ("Deploy from branch", /docs)
                            *.html, style.css, robots.txt, llms.txt, sitemap.xml, CNAME

Usage:  python3 build_site.py [--domain annarotkirch.com]
Requires: markdown (pip install markdown).
"""

import csv, os, re, shutil, sys, datetime
import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(HERE, "content")
DOCS = os.path.join(HERE, "docs")
DATA = os.path.dirname(HERE)          # the Homepage folder, where the CSVs live
IMAGES = os.path.join(HERE, "images") # photo sources, copied to docs/img/ at build time

SITE_TITLE = "Anna Rotkirch"
TAGLINE = "Research on families, fertility and population change"
NAV = [("index.html", "About"), ("publications.html", "Publications"),
       ("media.html", "Media"), ("talks.html", "Talks"),
       ("research.html", "Research projects"),
       ("books.html", "Books and reports"), ("cv.html", "CV")]
# pages built and listed in the sitemap but not in the navigation (linked from other pages)
EXTRA_PAGES = [("archive.html", "Other and older publications")]
MONTHS = ["January","February","March","April","May","June","July","August",
          "September","October","November","December"]
# One photo per page: slug -> (file in images/, credit line, shape).
# Shape "wide" spans the full column under the heading (group photos); "left" floats left. An empty credit prints no caption.
# Credits: only where Anna has named the photographer. Never infer one.
PHOTOS = {
    "index.html":    ("rotkirch-portrait-tall.jpg", "",                            "left"),
    "publications.html": (None,                     "",                            ""),
    "media.html":    ("rotkirch-ft-bibby.jpg",      "© Charlie Bibby for the FT",  "left large"),
    "talks.html":    ("rotkirch-talks.jpg",         "",                            "left large"),
    "research.html": ("rotkirch-netresilience.jpg", "NetResilience project members", "wide"),
    "books.html":    (None,                         "",                            ""),
    "cv.html":       ("rotkirch-research.jpg",      "",                            "left"),
}
OG_IMAGE = "rotkirch-portrait.jpg"      # link-preview image used on every page
# Profiles listed as schema.org sameAs in every page head (read by search engines and crawlers).
# Only addresses Anna has confirmed or that were verified to be hers.
SAME_AS = [
    "https://orcid.org/0000-0002-9429-1499",
    "https://www.wikidata.org/wiki/Q11851609",
    "https://fi.wikipedia.org/wiki/Anna_Rotkirch",
    "https://sv.wikipedia.org/wiki/Anna_Rotkirch",
    "https://scholar.google.com/citations?user=H9_DJN8AAAAJ",
    "https://www.linkedin.com/in/anna-rotkirch-b6808550/",
    "https://www.researchgate.net/profile/Anna-Rotkirch",
    "https://www.vaestoliitto.fi/henkilosto/anna-rotkirch/",
]

def person_jsonld():
    import json
    d = {"@context": "https://schema.org", "@type": "Person",
         "name": "Anna Rotkirch", "givenName": "Anna", "familyName": "Rotkirch",
         "url": f"https://{domain()}/", "image": f"https://{domain()}/img/{OG_IMAGE}",
         "jobTitle": "Research Professor and Research Director",
         "worksFor": {"@type": "Organization", "name": "Population Research Institute, Väestöliitto",
                      "url": "https://www.vaestoliitto.fi/en/research/"},
         "email": "mailto:anna.rotkirch@vaestoliitto.fi",
         "sameAs": SAME_AS}
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + "</script>"

MEDIA_ORDER = ["Interviews and profiles", "Podcasts and broadcast", "Essays and columns",
               "Press mentions", "German, French and other European", "Czech", "Finnish"]

def domain():
    return sys.argv[sys.argv.index("--domain")+1] if "--domain" in sys.argv else "annarotkirch.com"

def read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

def fmt_date(d):
    if not d: return ""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", d)
    if m: return f"{int(m.group(3))} {MONTHS[int(m.group(2))-1]} {m.group(1)}"
    m = re.match(r"^(\d{4})-(\d{2})$", d)
    if m: return f"{MONTHS[int(m.group(2))-1]} {m.group(1)}"
    return d

def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

def figure(slug):
    """The <figure> for a page, or empty string when the page has no photo."""
    if slug not in PHOTOS:
        return ""
    f, credit, shape = PHOTOS[slug]
    if not f:
        return ""
    if not os.path.exists(os.path.join(IMAGES, f)):
        print(f"  (warning: {f} listed in PHOTOS but not found in images/)")
        return ""
    cls = "portrait" + (f" {shape}" if shape else "")
    cap = f'<figcaption>{esc(credit)}</figcaption>' if credit else ""
    return (f'\n<figure class="{cls}">'
            f'<img src="img/{f}" alt="{esc(credit) if shape == "wide" and credit else "Anna Rotkirch"}" loading="lazy" decoding="async">'
            f'{cap}</figure>\n')


def page(slug, title, body, description, long_page=False):
    def nav_item(h, t):
        cls = ' class="here"' if h == slug else ''
        return f'      <a href="{h}"{cls}>{esc(t)}</a>'
    nav = "\n".join(nav_item(h, t) for h, t in NAV)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — {SITE_TITLE}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<link rel="canonical" href="https://{domain()}/{'' if slug == 'index.html' else slug}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Sans:wght@400;500&display=swap">
<meta property="og:type" content="profile">
<meta property="og:title" content="{esc(title)} — {SITE_TITLE}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="https://{domain()}/{'' if slug == 'index.html' else slug}">
<meta property="og:image" content="https://{domain()}/img/{OG_IMAGE}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="img/{OG_IMAGE}">
<link rel="stylesheet" href="style.css">
{person_jsonld()}
</head>
<body>
<header id="top">
  <div class="wrap">
    <p class="sitename"><a href="index.html">{esc(SITE_TITLE)}</a></p>
    <p class="tagline">{esc(TAGLINE)}</p>
    <nav>
{nav}
    </nav>
  </div>
</header>
<main class="wrap">
{body}
</main>
<footer class="wrap">
  <p>Anna Rotkirch, Population Research Institute, Väestöliitto, Helsinki.
     <a href="mailto:anna.rotkirch@vaestoliitto.fi">anna.rotkirch@vaestoliitto.fi</a> ·
     <a href="https://orcid.org/0000-0002-9429-1499">ORCID 0000-0002-9429-1499</a></p>
  <p class="built">Page generated {datetime.date.today().isoformat()}.</p>
</footer>
{TOTOP if long_page else ""}</body>
</html>
"""

TOTOP = """<a class="totop" href="#top" aria-label="Back to top">&uarr; Top</a>
<script>
(function () {
  var b = document.querySelector("a.totop");
  function f() { b.classList.toggle("show", window.scrollY > 700); }
  window.addEventListener("scroll", f, { passive: true }); f();
})();
</script>
"""

STYLE = """:root {
  --ink: #16181a; --muted: #5a6068; --bg: #fcfcfb; --rule: #e2e5e7;
  --link: #17506b; --accent: #17506b;
}
@media (prefers-color-scheme: dark) {
  :root { --ink: #e7eaec; --muted: #99a2a9; --bg: #14171a; --rule: #2b3137;
          --link: #86b8d1; --accent: #86b8d1; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 17px/1.62 "Source Serif 4", Charter, Georgia, "Iowan Old Style", serif; }
.wrap { max-width: 46rem; margin: 0 auto; padding: 0 1.25rem; }
header { border-bottom: 1px solid var(--rule); padding: 2.2rem 0 0.9rem; margin-bottom: 2.2rem; }
.sitename { font-size: 2.1rem; font-weight: 600; margin: 0; letter-spacing: -0.015em; line-height: 1.15; }
.sitename a { color: var(--ink); text-decoration: none; }
.tagline { margin: 0.35rem 0 1.35rem; color: var(--muted); font-size: 1.08rem; }
header nav { display: flex; flex-wrap: wrap; gap: 0.3rem 1.35rem;
  font-family: "IBM Plex Sans", system-ui, -apple-system, sans-serif; font-size: 1rem;
  font-weight: 500; }
header nav a { color: var(--ink); text-decoration: none; padding-bottom: 0.4rem;
  border-bottom: 2px solid transparent; }
header nav a:hover { color: var(--accent); }
header nav a.here { color: var(--accent); border-bottom-color: var(--accent); }
main { padding-bottom: 3rem; }
h1 { font-size: 1.9rem; line-height: 1.2; margin: 0 0 1.1rem; letter-spacing: -0.015em; }
h2 { font-size: 1.22rem; margin: 2.3rem 0 0.7rem; letter-spacing: -0.005em; scroll-margin-top: 1rem; }
h3 { font-size: 1.02rem; margin: 1.7rem 0 0.5rem; color: var(--muted);
  font-family: "IBM Plex Sans", system-ui, -apple-system, sans-serif; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.05em; }
p, li { margin: 0 0 0.9rem; text-wrap: pretty; hyphens: none; }
a { color: var(--link); text-decoration-thickness: 1px; text-underline-offset: 2px; }
a:focus-visible, nav a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
ul { padding-left: 1.15rem; }
.lead { font-size: 1.1rem; margin-bottom: 1.2rem; }
.refs p { margin-bottom: 0.9rem; }
.meta { color: var(--muted); font-size: 0.93rem; }
hr { border: 0; border-top: 1px solid var(--rule); margin: 2.4rem 0; }
footer { border-top: 1px solid var(--rule); padding: 1.2rem 1.25rem 3rem;
  color: var(--muted); font-size: 0.88rem; }
footer p { margin: 0 0 0.3rem; }
.built { font-size: 0.8rem; }
figure.portrait { float: right; width: 232px; margin: 0.35rem 0 1.2rem 1.7rem; }
figure.portrait img { display: block; width: 100%; height: auto; border-radius: 2px; }
figure.portrait.round img { border-radius: 50%; }
figure.portrait.left { float: left; margin: 0.35rem 1.7rem 1.2rem 0; }
figure.portrait.wide { float: none; width: 100%; margin: 0.2rem 0 1.5rem; }
figure.portrait.large { width: 320px; }
figure.portrait figcaption { margin-top: 0.4rem; color: var(--muted);
  font-family: "IBM Plex Sans", system-ui, -apple-system, sans-serif; font-size: 0.72rem;
  letter-spacing: 0.01em; }
footer { clear: both; }
/* the first block after a floated photo starts level with the photo's top edge */
figure.portrait + * { margin-top: 0; }
/* jump links to the sections of a long page */
nav.jump { display: flex; flex-wrap: wrap; gap: 0.2rem 0.9rem; margin: 0.4rem 0 1.6rem;
  padding: 0.6rem 0; border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule);
  font-family: "IBM Plex Sans", system-ui, -apple-system, sans-serif; font-size: 0.88rem; }
nav.jump a { color: var(--muted); text-decoration: none; }
nav.jump a:hover { color: var(--accent); text-decoration: underline; }
a.totop { position: fixed; right: 1.1rem; bottom: 1.1rem; padding: 0.4rem 0.7rem;
  font-family: "IBM Plex Sans", system-ui, -apple-system, sans-serif; font-size: 0.8rem;
  color: var(--muted); background: var(--bg); border: 1px solid var(--rule); border-radius: 3px;
  text-decoration: none; opacity: 0; pointer-events: none; transition: opacity 0.2s; }
a.totop.show { opacity: 1; pointer-events: auto; }
a.totop:hover { color: var(--accent); }
@media (max-width: 560px) {
  figure.portrait, figure.portrait.large { float: none; width: min(100%, 320px); margin: 0 0 1.3rem; }
}
@media (max-width: 480px) { body { font-size: 16px; } h1 { font-size: 1.6rem; } }
"""

JUMP_MIN = 6   # pages with at least this many h2 sections get a jump bar

def slugify(t):
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return t or "section"

def add_ids_and_jump(body):
    """Give every h2 an id; on long pages insert a jump bar before the first h2."""
    heads = []
    def fix(m):
        text = m.group(1); i = slugify(text)
        n = 2
        while i in [h[0] for h in heads]:
            i = f"{slugify(text)}-{n}"; n += 1
        heads.append((i, text))
        return f'<h2 id="{i}">{text}</h2>'
    body = re.sub(r"<h2>(.*?)</h2>", fix, body)
    long_page = len(heads) >= JUMP_MIN
    if long_page:
        links = " ".join(f'<a href="#{i}">{t}</a>' for i, t in heads)
        body = body.replace("<h2 ", f'<nav class="jump" aria-label="Sections">{links}</nav>\n<h2 ', 1)
    return body, long_page

def media_html():
    rows = read(os.path.join(DATA, "media_2023_2026.csv"))
    fi = read(os.path.join(DATA, "media_fi_2022_2026.csv"))
    talks = read(os.path.join(DATA, "talks_2024_2026.csv"))
    out = ["<h1>Media</h1>",
           '<p class="lead">Interviews, podcasts, recorded talks and press coverage.</p>']

    rec = [t for t in talks if t.get("Recording link")]
    if rec:
        out.append("<h2>Recorded talks</h2>")
        out.append('<div class="refs">')
        for t in sorted(rec, key=lambda r: r["Date"], reverse=True):
            venue = esc(t["Event / Venue"].split(",")[0])
            title = esc(t["Title / Topic"])
            out.append(f'<p>{venue}, {fmt_date(t["Date"])}. '
                       f'<a href="{t["Recording link"]}">{title}</a>. {esc(t["Type"])}.</p>')
        out.append("</div>")

    for cat in MEDIA_ORDER:
        sel = [r for r in rows if r["category"] == cat and r["title"]]
        if not sel: continue
        out.append(f"<h2>{esc(cat)}</h2>")
        out.append('<div class="refs">')
        for r in sorted(sel, key=lambda r: r["date"], reverse=True):
            head = esc(r["outlet"]) + (f", {fmt_date(r['date'])}" if r["date"] else "")
            title = esc(r["title"])
            title = title if title.endswith(("?", ".", "!")) else title + "."
            link = f'<a href="{r["url"]}">{title}</a>' if r["url"] else title
            tail = f" {esc(r['kind'])}." if r["kind"] else ""
            lang = f" In {esc(r['language'])}." if r["language"] and r["language"] != "English" else ""
            out.append(f"<p>{head}. {link}{tail}{lang}</p>")
        out.append("</div>")

    if fi:
        out.append("<h2>Finnish and Finland-Swedish media</h2>")
        out.append('<div class="refs">')
        for r in sorted(fi, key=lambda r: r.get("date", ""), reverse=True):
            t = esc(r.get("title", ""))
            if not t: continue
            t = t if t.endswith(("?", ".", "!")) else t + "."
            link = f'<a href="{r["url"]}">{t}</a>' if r.get("url") else t
            head = esc(r.get("outlet", ""))
            if r.get("date"): head += f", {fmt_date(r['date'])}"
            kind = f" {esc(r.get('kind',''))}." if r.get("kind") else ""
            out.append(f"<p>{head}. {link}{kind}</p>")
        out.append("</div>")
    return "\n".join(out)

def main():
    os.makedirs(DOCS, exist_ok=True)
    md = markdown.Markdown(extensions=["extra", "sane_lists", "attr_list"])
    written = []
    for slug, _ in NAV + EXTRA_PAGES:
        if slug == "media.html":
            body, title = media_html(), "Media"
            desc = "Interviews, podcasts, recorded talks and press coverage of Anna Rotkirch."
        else:
            src = os.path.join(CONTENT, slug.replace(".html", ".md"))
            if not os.path.exists(src):
                print(f"  (skipped {slug}: no {os.path.basename(src)})"); continue
            text = open(src, encoding="utf-8").read()
            first = text.strip().splitlines()[0]
            title = first.lstrip("# ").strip()
            desc_m = re.search(r"^description:\s*(.+)$", text, re.M)
            desc = desc_m.group(1).strip() if desc_m else f"{title} — Anna Rotkirch"
            text = re.sub(r"^description:.*$", "", text, flags=re.M)
            md.reset(); body = md.convert(text)
        body, long_page = add_ids_and_jump(body)
        fig = figure(slug)
        if fig:
            # plain string replace: the figure HTML must not be read as a regex template
            body = (body.replace("</h1>", "</h1>" + fig, 1)
                    if "</h1>" in body else fig + body)
        open(os.path.join(DOCS, slug), "w", encoding="utf-8").write(
            page(slug, title, body, desc, long_page))
        written.append(slug)

    # photos: copy images/ into docs/img/ so docs/ is fully reproducible
    if os.path.isdir(IMAGES):
        dest = os.path.join(DOCS, "img")
        os.makedirs(dest, exist_ok=True)
        keep = set()
        for f in sorted(os.listdir(IMAGES)):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".svg")):
                shutil.copyfile(os.path.join(IMAGES, f), os.path.join(dest, f))
                keep.add(f)
        for f in os.listdir(dest):            # drop images removed from images/
            if f not in keep:
                os.remove(os.path.join(dest, f))

    # documents (PDFs etc. formerly hosted on blogs.helsinki.fi): files/ -> docs/files/
    FILES = os.path.join(HERE, "files")
    if os.path.isdir(FILES):
        dest = os.path.join(DOCS, "files")
        os.makedirs(dest, exist_ok=True)
        for f in sorted(os.listdir(FILES)):
            if not f.startswith("."):
                shutil.copyfile(os.path.join(FILES, f), os.path.join(dest, f))

    open(os.path.join(DOCS, "style.css"), "w", encoding="utf-8").write(STYLE)
    # no trailing newline: GitHub Pages rewrites this file itself when the custom domain
    # is saved, and it writes it without one. Matching avoids a needless remote commit.
    open(os.path.join(DOCS, "CNAME"), "w", encoding="utf-8").write(domain())
    open(os.path.join(DOCS, ".nojekyll"), "w", encoding="utf-8").write("")
    open(os.path.join(DOCS, "robots.txt"), "w", encoding="utf-8").write(
        "# Every crawler, including AI crawlers, is welcome on this site.\n"
        "User-agent: *\nAllow: /\n\n"
        f"Sitemap: https://{domain()}/sitemap.xml\n")
    today = datetime.date.today().isoformat()
    urls = "".join(
        f"  <url><loc>https://{domain()}/{'' if s == 'index.html' else s}</loc>"
        f"<lastmod>{today}</lastmod></url>\n" for s in written)
    open(os.path.join(DOCS, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")
    open(os.path.join(DOCS, "llms.txt"), "w", encoding="utf-8").write(
        f"""# Anna Rotkirch

> Research Professor and Director of the Population Research Institute at Väestöliitto,
> the Family Federation of Finland. Demographer and sociologist working on fertility
> decline, family and kin relations, and evolutionary approaches to human behaviour.
> Demographic rapporteur to the Finnish Government in 2020-21 and 2024.

This site is open to all crawlers, including AI crawlers. Content may be quoted with
attribution to Anna Rotkirch and a link to the page it came from.

## Pages
""" + "".join(f"- [{t}](https://{domain()}/{'' if s == 'index.html' else s})\n"
              for s, t in NAV + EXTRA_PAGES if s in written) +
        f"""
## Identifiers
- ORCID: https://orcid.org/0000-0002-9429-1499
- Affiliation: Population Research Institute, Väestöliitto, Helsinki, Finland
- Contact: anna.rotkirch@vaestoliitto.fi
""")
    print(f"Wrote {len(written)} pages to {DOCS}: " + ", ".join(written))

if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
# Preview: one self-contained page holding every section, for review only.
# Written to preview/preview.html when --preview is passed. Not part of the site.
def preview():
    md = markdown.Markdown(extensions=["extra", "sane_lists", "attr_list"])
    parts = []
    for slug, label in NAV:
        if slug == "media.html":
            body = media_html()
        else:
            src = os.path.join(CONTENT, slug.replace(".html", ".md"))
            if not os.path.exists(src):
                continue
            text = re.sub(r"^description:.*$", "", open(src, encoding="utf-8").read(), flags=re.M)
            md.reset(); body = md.convert(text)
        anchor = slug.replace(".html", "")
        body = body.replace("<h1>", f'<h1 id="{anchor}">', 1)
        parts.append(body)
    nav = " ".join(f'<a href="#{s.replace(".html","")}">{esc(t)}</a>' for s, t in NAV)
    out = os.path.join(HERE, "preview")
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "preview.html"), "w", encoding="utf-8").write(
        f'<title>{SITE_TITLE} — site preview</title>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        'family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&'
        'family=IBM+Plex+Sans:wght@400;500&display=swap">\n'
        f"<style>\n{STYLE}\n"
        "header{position:sticky;top:0;background:var(--bg);z-index:5}\n"
        "main section{border-top:1px solid var(--rule);padding-top:2rem;margin-top:2.5rem}\n"
        "main section:first-child{border-top:0;margin-top:0;padding-top:0}\n</style>\n"
        f'<header><div class="wrap"><p class="sitename">{esc(SITE_TITLE)}</p>'
        f'<p class="tagline">{esc(TAGLINE)}</p><nav>{nav}</nav></div></header>\n'
        '<main class="wrap">\n' +
        "\n".join(f"<section>\n{p}\n</section>" for p in parts) +
        '\n</main>\n<footer class="wrap"><p>Preview of the site as it would be published. '
        'Each section is a separate page on the real site.</p></footer>\n')
    print(os.path.join(out, "preview.html"))

if "--preview" in sys.argv:
    preview()
