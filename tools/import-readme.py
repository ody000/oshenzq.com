#!/usr/bin/env python3
"""
Split the README 21 text files into bilingual chapter pages under content/writing/.

    python3 tools/import-readme.py

Sources live in private/source/ and are never published. Each selected chapter
becomes two pages:

    content/writing/<slug>/index.md   English
    content/writing/<slug>/zh.md      中文

Re-running overwrites both files, so once a chapter is imported, edit the Markdown
rather than the source text. To publish another chapter, add a row to CHAPTERS.
"""

import re, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC  = ROOT / "private" / "source"
OUT  = ROOT / "content" / "writing"

# slug, EN heading, ZH heading, EN title, ZH title, date, dateline, summary
CHAPTERS = [
    ("drawing", "II. Drawing", "二 画", "Drawing", "画",
     "2023-12", "Winter 2023",
     "Hundreds of A3 sheets, a studio in Shanghai, and seven years of charcoal — how learning to draw trained my eye rather than my hand."),
    ("piano", "III. Piano", "三 钢琴", "Piano", "钢琴",
     "2023-12", "Winter 2023",
     "I did not begin the piano because I liked it. On practising something before you are old enough to want it."),
    ("badminton-i", "IV. Badminton I", "四 羽毛球（一）", "Badminton I", "羽毛球（一）",
     "2023-12", "Winter 2023",
     "Starting late, in Shanghai — with my high-school TED talk, “Being good at badminton is to be a good person”, as a prelude."),
    ("second-existential-crisis", "V. The Second Existential Crisis", "五 第二次存在主义危机",
     "The Second Existential Crisis", "第二次存在主义危机",
     "2024-07", "Summer 2024",
     "A Singapore Symphony concert, a violinist my own age, and the question of what a life gets measured against."),
    ("badminton-ii", "VIII. Badminton II", "八 羽毛球（二）", "Badminton II", "羽毛球（二）",
     "2024-07", "Summer 2024",
     "Training abroad under coaches from Malaysia, Indonesia, India and Nepal, and what constant switching does to a game."),
    ("injury", "IX. Injury", "九 伤病", "Injury", "伤病",
     "2024-12", "Winter 2024",
     "15 July 2023, the Bay State Games. A dull pain behind the right armpit, and the long argument with a body that will not cooperate."),
    ("choosing-a-major", "XI. How Did I Choose My Major", "十一 我如何选择专业",
     "How Did I Choose My Major", "我如何选择专业",
     "2025-07", "Summer 2025",
     "Confirming Cognitive Neuroscience and Computer Science in the first week of sophomore spring, and the reasoning that got me there."),
    ("learning-rules", "XVI. Learning Rules", "十六 学习方法", "Learning Rules", "学习方法",
     "2026-04", "Spring 2026",
     "In FTL, humans have no special ability except that they learn 10% faster. On academic learning, skill acquisition, and becoming my own mentor."),
]

EN_HEAD = re.compile(r"^\s*(?:X{0,3})(?:IX|IV|V?I{0,3})\.\s+\S")
ZH_HEAD = re.compile(r"^\s*[一二三四五六七八九十]+[ 　]\S")
RULE    = re.compile(r"^\s*(\*\s*\*\s*\*|⸻|—{3,})\s*$")


def load(*names):
    lines = []
    for n in names:
        f = SRC / n
        if not f.exists():
            sys.exit(f"Missing source file: {f}")
        lines += f.read_text(encoding="utf-8").splitlines()
    return lines


def norm(s):
    """Collapse whitespace — some headings in the source use double spaces."""
    return re.sub(r"\s+", " ", s).strip()


def chapter(lines, heading, is_head):
    """Return the lines between `heading` and the next chapter heading."""
    target = norm(heading)
    try:
        start = next(i for i, l in enumerate(lines) if norm(l) == target)
    except StopIteration:
        sys.exit(f"Heading not found: {heading!r}")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if is_head.match(lines[i]) and norm(lines[i]) != target:
            end = i
            break
    return lines[start + 1:end]


def to_markdown(raw):
    out = []
    for l in raw:
        s = l.strip()
        if not s:
            continue
        out.append("---" if RULE.match(s) else s)
    # collapse repeated rules and trim them from the ends
    md = []
    for s in out:
        if s == "---" and (not md or md[-1] == "---"):
            continue
        md.append(s)
    while md and md[-1] == "---":
        md.pop()
    return "\n\n".join(md)


def write(path, meta, title, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = "\n".join(f"{k}: {v}" for k, v in meta.items())
    path.write_text(f"---\n{fm}\n---\n\n# {title}\n\n{{{{lang}}}}\n\n{body}\n",
                    encoding="utf-8")


def main():
    en = load("readme21-en-1.txt", "readme21-en-2.txt")
    zh = load("readme21-zh-1.txt", "readme21-zh-2.txt")

    for slug, h_en, h_zh, t_en, t_zh, date, dateline, summary in CHAPTERS:
        body_en = to_markdown(chapter(en, h_en, EN_HEAD))
        body_zh = to_markdown(chapter(zh, h_zh, ZH_HEAD))

        write(OUT / slug / "index.md", {
            "title": t_en, "kind": "chapter", "lang": "en",
            "date": date, "dateline": dateline, "summary": summary,
            "alt_url": f"/writing/{slug}/zh/", "alt_label": "中文",
            "description": summary,
        }, t_en, body_en)

        write(OUT / slug / "zh.md", {
            "title": t_zh, "kind": "chapter-zh", "lang": "zh",
            "date": date, "dateline": dateline,
            "alt_url": f"/writing/{slug}/", "alt_label": "English",
            "description": summary,
        }, t_zh, body_zh)

        print(f"  {slug:28s} en {len(body_en.split()):5d} words   zh {len(body_zh):5d} chars")


if __name__ == "__main__":
    main()
