# oshenzq.com

Personal website of Ziqi Shen. Plain static HTML, built from Markdown by one Python
script. No Ruby, no npm, no Jekyll, no theme. Everything the site does lives in
three files:

| File | What it is |
|---|---|
| `build.py` | The whole build system. ~250 lines. Read it. |
| `theme/base.html` | The one page template. |
| `theme/style.css` | The one stylesheet. |

---

## One-time setup

```bash
pip3 install -r requirements.txt
```

## Editing the site

**Every word on the site lives in `content/`.** One `.md` file per page:

```
content/about.md       ->  /            (front page)
content/research.md    ->  /research/
content/badminton.md   ->  /badminton/
content/misc.md        ->  /misc/
content/writing/index.md          ->  /writing/
content/writing/<slug>/index.md   ->  /writing/<slug>/       (English)
content/writing/<slug>/zh.md      ->  /writing/<slug>/zh/    (中文)
```

To change text, open the file and type. To preview:

```bash
python3 build.py --serve
```

Then open <http://localhost:8000>. Stop it with Ctrl-C. Re-run it after each change.

To publish, commit and push to `main`. GitHub Actions rebuilds and deploys in about
40 seconds. You can also edit a `.md` file directly in GitHub's web editor — from
your phone, if you want — and it will deploy the same way.

---

## How to do specific things

### Add a paragraph
Type it. Blank line between paragraphs. That's Markdown:

```markdown
This is a paragraph. *This is italic*, **this is bold**,
and [this is a link](https://example.com).

## This is a section heading
```

### Add a new page
Create `content/teaching.md`:

```markdown
---
title: Teaching
nav: Teaching       # remove this line to keep the page out of the nav
nav_order: 5        # position in the nav, lower comes first
description: One sentence, used by Google and link previews.
---

# Teaching

Your words here.
```

It appears at `/teaching/` on the next build.

### Add a dated row (jobs, awards, projects, publications)
Those rows with a year on the left are written like this:

```markdown
::: entries
2026 :: Title of the thing :: Where it happened · who you worked with
An optional description. It can run to several lines and can use
*italics*, **bold** and [links](https://example.com).

2025 :: Another thing :: Somewhere else
:::
```

The first line of each block is `when :: title :: where`. Everything after it is the
description. Blank line between entries. `where` and the description are optional.
Make the title a link by writing it as `[Title](https://url)`.

### Add a PDF
Drop the file in `assets/pdf/`, then link to it:

```markdown
[My new paper](/assets/pdf/my-new-paper.pdf)
```

To replace your CV, overwrite `assets/pdf/ziqi-shen-cv.pdf` with the new one — the
filename is linked from the About page, the Misc page and the footer, so keeping the
name means nothing else needs changing.

### Add photos to a gallery
Drop images into `assets/img/art/` or `assets/img/badminton/` — any format, straight
off your phone is fine, including HEIC. Then:

```bash
./tools/prep-images.sh art
```

That resizes each one to 1800px for the click-through view and makes a 700px
thumbnail for the grid. Rebuild and the new images appear automatically. You never
edit the page to add a photo.

### Caption a photo (optional)
Galleries have no captions by default. To add them, create
`assets/img/art/captions.txt`:

```
art-03.jpg | Elderly man — graphite, 2021
```

One line per image, `filename | caption`. Only the images you list get a caption;
lines starting with `#` are ignored. Without this file the gallery is captionless,
which is the current state.

### Add a new gallery
Make `assets/img/travel/`, add photos, run `./tools/prep-images.sh travel`, then put
`{{gallery: travel}}` on any page.

### Publish another README chapter
Chapters live in `private/source/` (four text files, never published) and are split
into pages by one script. To add one, append a row to `CHAPTERS` in
`tools/import-readme.py` — slug, the English heading, the Chinese heading, both
titles, a sortable date, a displayed dateline, and a one-line summary — then:

```bash
python3 tools/import-readme.py
```

It writes `content/writing/<slug>/index.md` (English) and
`content/writing/<slug>/zh.md` (中文), and the chapter appears on `/writing/`
automatically. **Re-running overwrites both files**, so once a chapter is imported,
edit the Markdown and not the source text.

To unpublish a chapter, delete its folder from `content/writing/`.

### Publish any other piece of writing
Create `content/writing/<slug>/index.md`:

```markdown
---
title: The title
kind: chapter          # this is what puts it in the /writing/ index
lang: en
date: 2026-09-01       # sorts the index, newest first
dateline: Autumn 2026  # what the reader sees
summary: One line shown in the index.
---

# The title

Your writing.
```

Add `alt_url` and `alt_label` to pair it with a translation. To keep a page out of
Google and out of the index, add `robots: noindex` and drop the `kind` line.

---

## Design rules

The site is deliberately **achromatic** — black, white and grey only. Every colour is
a CSS variable at the top of `theme/style.css`; there are no hues anywhere in the
interface. The exception is deliberate: **artwork and photographs keep their real
colour.** The frame is neutral so the work can be seen, exactly like a gallery wall.

There is **no motion** — no transitions, no scroll animations, no fades. There is
**no dark mode**, no analytics, no third-party scripts, and no external requests at
all. The fonts are self-hosted. The site loads what it needs and nothing else.

---

## Deployment

Hosted on GitHub Pages from the `main` branch via `.github/workflows/deploy.yml`.
The custom domain is set by the `CNAME` file.

DNS records required at the registrar for `oshenzq.com`:

```
A      @      185.199.108.153
A      @      185.199.109.153
A      @      185.199.110.153
A      @      185.199.111.153
CNAME  www    ody000.github.io
```

Then in the repository: **Settings → Pages → Source: GitHub Actions**, and set the
custom domain to `oshenzq.com` with "Enforce HTTPS" enabled.

---

## Not published

`private/` holds the full README autobiography — the PDFs and the four source text
files. It is listed in `.gitignore`, so it is never committed and never deployed.
Only the eight chapters listed in `tools/import-readme.py` reach the site.

## Originals

`originals/` holds the untouched camera files for the galleries. It is gitignored —
it is 34 MB the site never serves, and the web-ready versions in `assets/img/` are
generated from it. Keep your own backup of these; a fresh clone will not have them.
