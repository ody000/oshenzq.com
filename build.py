#!/usr/bin/env python3
"""
build.py — turns content/*.md into a static site in _site/

    python3 build.py            build once
    python3 build.py --serve    build, then serve at http://localhost:8000

Everything the site does lives in this file, theme/base.html and theme/style.css.
There is nothing else. If something looks wrong, it is in one of those three.
"""

import functools, http.server, re, shutil, socketserver, sys
from pathlib import Path

try:
    import markdown
except ImportError:
    sys.exit("Missing dependency. Run:  pip3 install markdown")

ROOT      = Path(__file__).parent
CONTENT   = ROOT / "content"
THEME     = ROOT / "theme"
ASSETS    = ROOT / "assets"
OUT       = ROOT / "_site"
SITE_URL  = "https://oshenzq.com"
SITE_NAME = "Ziqi Shen"

MD = markdown.Markdown(
    extensions=["extra", "smarty", "sane_lists", "toc"],
    extension_configs={"smarty": {"smart_dashes": True, "smart_quotes": True}},
)


# ---------------------------------------------------------------- front matter
def split_front_matter(text):
    """Return (meta dict, body). Front matter is `key: value` lines between --- fences."""
    meta = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            text = text[end + 4:]
    return meta, text.lstrip("\n")


# ------------------------------------------------------------------ shortcodes
def gallery(name, kind):
    """{{gallery: art}} -> a grid of every image in assets/img/<name>/thumb/.

    Add a photo by dropping it in assets/img/<name>/ and running tools/prep-images.sh.
    Captions are optional: assets/img/<name>/captions.txt, one `filename | caption` per line.
    """
    folder = ASSETS / "img" / name
    if not folder.is_dir():
        return f"<!-- gallery: assets/img/{name}/ not found -->"

    captions = {}
    cap_file = folder / "captions.txt"
    if cap_file.exists():
        for line in cap_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "|" not in line:
                continue
            f, c = line.split("|", 1)
            captions[f.strip()] = c.strip()

    thumbs = sorted((folder / "thumb").glob("*.jpg"))
    tiles = []
    for t in thumbs:
        cap = captions.get(t.name, "")
        alt = cap or (f"Artwork by {SITE_NAME}" if kind == "art"
                      else f"{name.replace('_', ' ').title()} photograph")
        tiles.append(
            f'<figure><a href="/assets/img/{name}/{t.name}">'
            f'<img src="/assets/img/{name}/thumb/{t.name}" alt="{esc(alt)}" loading="lazy">'
            f"</a>"
            + (f"<figcaption>{esc(cap)}</figcaption>" if cap else "")
            + "</figure>"
        )
    return f'<div class="gallery {kind}">' + "".join(tiles) + "</div>"


def writing_index(pages):
    """{{writing_index}} -> entry rows for everything in content/writing/, newest first."""
    posts = [p for p in pages if p["url"].startswith("/writing/")]
    if not posts:
        return '<p class="muted"><em>Nothing published here yet.</em></p>'
    posts.sort(key=lambda p: p["meta"].get("date", ""), reverse=True)
    rows = []
    for p in posts:
        m = p["meta"]
        rows.append(
            f'<div class="entry"><div class="when">{esc(m.get("date", ""))}</div>'
            f'<div class="what"><div class="title"><a href="{p["url"]}">{esc(m.get("title", ""))}</a></div>'
            + (f'<p>{esc(m["summary"])}</p>' if m.get("summary") else "")
            + "</div></div>"
        )
    return '<div class="entries">' + "".join(rows) + "</div>"


def entries_block(raw):
    """::: entries ... ::: -> styled entry rows.

    Each entry is one paragraph. Its first line is
        when :: title :: where
    (`where` is optional) and any following lines are the description, in Markdown.
    """
    out = []
    for chunk in re.split(r"\n\s*\n", raw.strip()):
        lines = chunk.strip().splitlines()
        if not lines:
            continue
        head, rest = lines[0], "\n".join(lines[1:]).strip()
        parts = [c.strip() for c in head.split("::")]
        when  = parts[0] if len(parts) > 0 else ""
        title = parts[1] if len(parts) > 1 else ""
        where = parts[2] if len(parts) > 2 else ""

        MD.reset(); title_html = MD.convert(title)
        title_html = re.sub(r"^<p>|</p>$", "", title_html.strip())
        MD.reset(); where_html = MD.convert(where)
        where_html = re.sub(r"^<p>|</p>$", "", where_html.strip())
        MD.reset(); desc_html = MD.convert(rest) if rest else ""

        out.append(
            f'<div class="entry"><div class="when">{when}</div><div class="what">'
            + (f'<div class="title">{title_html}</div>' if title else "")
            + (f'<div class="where">{where_html}</div>' if where else "")
            + desc_html + "</div></div>"
        )
    return '<div class="entries">' + "".join(out) + "</div>"


def protect_blocks(body):
    """Pull ::: entries ::: blocks out before Markdown runs; return (body, stash)."""
    stash = []
    def take(m):
        stash.append(entries_block(m.group(1)))
        return f"\n\nENTRIESPLACEHOLDER{len(stash) - 1}\n\n"
    body = re.sub(r"^:::\s*entries\s*$(.*?)^:::\s*$", take, body,
                  flags=re.MULTILINE | re.DOTALL)
    return body, stash


def restore_blocks(html, stash):
    for i, block in enumerate(stash):
        html = re.sub(rf"<p>ENTRIESPLACEHOLDER{i}</p>", lambda _m, b=block: b, html)
    return html


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def expand(html, pages):
    """Replace shortcodes. Markdown wraps a lone shortcode in <p>...</p>; since these
    expand to block-level <div>s, the surrounding <p> is matched and dropped."""
    html = re.sub(r"(?:<p>)?\{\{\s*gallery:\s*([\w/-]+)\s*\}\}(?:</p>)?",
                  lambda m: gallery(m.group(1), "art" if "art" in m.group(1) else "photo"), html)
    html = re.sub(r"(?:<p>)?\{\{writing_index\}\}(?:</p>)?",
                  lambda _m: writing_index(pages), html)
    return html


# ----------------------------------------------------------------------- build
def collect():
    pages = []
    for md_file in sorted(CONTENT.rglob("*.md")):
        meta, body = split_front_matter(md_file.read_text(encoding="utf-8"))
        rel = md_file.relative_to(CONTENT).with_suffix("")
        url = "/" if rel.name == "about" and rel.parent == Path(".") else f"/{rel.as_posix()}/"
        pages.append({"meta": meta, "body": body, "url": url, "src": md_file})
    return pages


def nav_html(pages, current_url):
    items = [p for p in pages if p["meta"].get("nav")]
    items.sort(key=lambda p: int(p["meta"].get("nav_order", 99)))
    out = []
    for p in items:
        here = ' aria-current="page"' if p["url"] == current_url else ""
        out.append(f'<a href="{p["url"]}"{here}>{esc(p["meta"]["nav"])}</a>')
    return "".join(out)


def build():
    OUT.mkdir(exist_ok=True)
    for item in OUT.iterdir():          # empty it, but keep the directory itself
        shutil.rmtree(item) if item.is_dir() else item.unlink()

    template = (THEME / "base.html").read_text(encoding="utf-8")
    pages = collect()

    for p in pages:
        meta = p["meta"]
        body, stash = protect_blocks(p["body"])
        MD.reset()
        content = restore_blocks(MD.convert(body), stash)
        content = expand(content, pages)

        title = meta.get("title", "")
        title_tag = SITE_NAME if p["url"] == "/" else f"{title} · {SITE_NAME}"
        robots = '<meta name="robots" content="noindex,nofollow">' if meta.get("robots") == "noindex" else ""

        html = (template
                .replace("{{title_tag}}", esc(title_tag))
                .replace("{{description}}", esc(meta.get("description", "")))
                .replace("{{canonical}}", SITE_URL + p["url"])
                .replace("{{site_url}}", SITE_URL)
                .replace("{{robots}}", robots)
                .replace("{{nav}}", nav_html(pages, p["url"]))
                .replace("{{content}}", content))

        dest = OUT / (p["url"].strip("/") + "/index.html" if p["url"] != "/" else "index.html")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
        print(f"  {p['url']:24s} <- content/{p['src'].relative_to(CONTENT)}")

    # static files
    shutil.copytree(ASSETS / "img",   OUT / "assets/img")
    shutil.copytree(ASSETS / "pdf",   OUT / "assets/pdf")
    shutil.copytree(ASSETS / "fonts", OUT / "assets/fonts")
    shutil.copy(THEME / "style.css",  OUT / "assets/style.css")
    for extra in ("CNAME", "robots.txt", "404.html"):
        if (ROOT / extra).exists():
            shutil.copy(ROOT / extra, OUT / extra)

    # sitemap (referenced by robots.txt)
    urls = "".join(f"<url><loc>{SITE_URL}{p['url']}</loc></url>"
                   for p in pages if p["meta"].get("robots") != "noindex")
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + "</urlset>",
        encoding="utf-8")

    print(f"\nBuilt {len(pages)} pages -> _site/")


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        print("Serving http://localhost:8000  (Ctrl-C to stop)")
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", 8000), handler) as httpd:
            httpd.serve_forever()
