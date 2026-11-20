"""Build the SRD-style B:OW rules reference (web page + print HTML for PDF).

Source: manual/srd/*.md (rewritten from the forum threads in manual/raw).
Outputs:
  build/srd_web.html   - artifact body (no <html>/<head>; sidebar navigation)
  build/srd_print.html - full document for Playwright -> PDF
"""
import re, html, pathlib, markdown, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRD = ROOT / 'srd'
OUT = ROOT / 'build'
FORUM = 'https://rpforumbleach.proboards.com/thread/'

THREADS = {
    '4170': 'Introduction', '4286': 'Trial Apps', '4629': 'How to Start Strong and Start Easy',
    '4627': 'Section 1: Character Creation', '5580': 'Section 2: Races, Releases, and Leveling',
    '2772': 'Section 3: Stats & Skills', '2041': 'Section 4: Types',
    '1389': 'Section 5: Rank Requirements & Organizations', '4172': 'Section 6: Types of Threads',
    '4626': 'Section 7: Battle Mechanics', '7302': 'Section 8: Custom Item Guidelines',
    '8196': 'Section 9: Nobility and Families', '8470': 'Section 10: NPCs and You',
    '2037': 'Rules of Conduct', '13462': 'Out-of-Character Rules for Players',
    '1395': 'Rules for Posting', '13552': 'Quick Reference',
}

PARTS = [
    ('I', 'Getting Started', ['00_basics', '01_creation', '02_points']),
    ('II', 'Your Character', ['03_races', '04_stats', '05_skills', '06_types', '07_ranks']),
    ('III', 'Playing the Game', ['08_threads', '09_battle', '10_items', '11_nobility', '12_npcs']),
    ('IV', 'Community', ['13_conduct']),
    ('Appendix', 'Reference', ['14_reference']),
]


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def load(name):
    text = (SRD / f'{name}.md').read_text()
    m = re.match(r'---\n(.*?)\n---\n', text, re.S)
    meta = dict(l.split(':', 1) for l in m.group(1).splitlines())
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    body = text[m.end():]
    fixed = []
    for line in body.split('\n'):
        lead = len(line) - len(line.lstrip(' '))
        if lead and line.lstrip().startswith('|'):
            line = line.lstrip()            # tables can't live inside list items
        elif lead:
            line = ' ' * (lead * 2) + line.lstrip(' ')   # 2-space nesting -> 4-space
        fixed.append(line)
    return meta, '\n'.join(fixed)


def render(md, chap_id):
    h = markdown.markdown(md, extensions=['tables', 'sane_lists', 'attr_list'])
    # wrap tables for horizontal scroll
    h = re.sub(r'<table>', '<div class="tbl"><table>', h)
    h = h.replace('</table>', '</table></div>')
    # advice vs note callouts
    def bq(m):
        inner = m.group(1)
        if re.match(r'\s*<p><strong>Advice\.</strong>', inner):
            inner = re.sub(r'<strong>Advice\.</strong>\s*', '', inner, count=1)
            return f'<aside class="advice"><div class="advice-label">Advice</div>{inner}</aside>'
        return f'<div class="note">{inner}</div>'
    h = re.sub(r'<blockquote>(.*?)</blockquote>', bq, h, flags=re.S)
    # heading ids, prefixed with chapter id
    heads = []
    def hid(m):
        lvl, txt = m.group(1), m.group(2)
        plain = re.sub('<[^>]+>', '', txt)
        i = f'{chap_id}-{slug(plain)}'
        if lvl == '2':
            heads.append((i, plain))
        return f'<h{lvl} id="{i}">{txt}</h{lvl}>'
    h = re.sub(r'<h([234])>(.*?)</h\1>', hid, h)
    # mark first paragraph after a chapter's first h2 "Overview" as lede
    return h, heads


def build(pages=None):
    pages = pages or {}
    nav, body, toc_print = [], [], []
    n = 0
    for part_no, part_title, files in PARTS:
        pid = 'part-' + slug(part_no)
        is_app = part_no == 'Appendix'
        label_part = 'Appendix' if is_app else f'Part {part_no}'
        body.append(f'<section class="part" id="{pid}"><div class="part-no">{label_part}</div>'
                    f'<h1 class="part-title">{part_title}</h1></section>')
        nav.append(f'<li class="nav-part">{label_part} · {part_title}</li>')
        toc_print.append(f'<li class="toc-part"><span>{label_part} · {part_title}</span><em>{pages.get(pid, "")}</em></li>')
        for f in files:
            meta, md = load(f)
            if not is_app:
                n += 1
            num = 'A' if is_app else str(n)
            cid = slug(meta['title'])
            h, heads = render(md, cid)
            srcs = [s.strip() for s in meta['sources'].split(',')]
            src_html = ' · '.join(f'<a href="{FORUM}{s}">{html.escape(THREADS[s])}</a>' for s in srcs)
            body.append(
                f'<section class="chapter" id="{cid}">'
                f'<header class="ch-head"><div class="ch-no">{"Appendix" if is_app else "Chapter"} {num}</div>'
                f'<h1 class="ch-title">{html.escape(meta["title"])}</h1>'
                f'<p class="ch-src">Based on {src_html}</p></header>{h}</section>')
            sub = ''.join(f'<li><a href="#{i}">{html.escape(t)}</a></li>' for i, t in heads)
            nav.append(f'<li class="nav-ch"><a href="#{cid}"><span class="nav-num">{num}</span>{html.escape(meta["title"])}</a>'
                       f'<ul class="nav-sub">{sub}</ul></li>')
            toc_print.append(f'<li><a href="#{cid}"><span>{num}</span>{html.escape(meta["title"])}</a><em>{pages.get(cid, "")}</em></li>')
    tpl = (OUT / 'srd_template.html').read_text()
    page = (tpl.replace('{{NAV}}', '\n'.join(nav))
               .replace('{{BODY}}', '\n'.join(body))
               .replace('{{TOC}}', '\n'.join(toc_print)))
    (OUT / 'srd_web.html').write_text(page)
    (OUT / 'srd_print.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8">'
                                       '<meta name="viewport" content="width=device-width, initial-scale=1">'
                                       '</head><body class="print">' + page + '</body></html>')
    print('chapters', n, 'bytes', len(page))


def page_numbers(pdf):
    import subprocess
    txt = subprocess.run(['pdftotext', pdf, '-'], capture_output=True, text=True).stdout.split('\f')
    res = {}
    for part_no, part_title, files in PARTS:
        label_part = 'Appendix' if part_no == 'Appendix' else f'Part {part_no}'
        for f in files:
            meta, _ = load(f)
            cid = slug(meta['title'])
            for i, pg in enumerate(txt):
                if i > 2 and re.search(re.escape(meta['title']) + r'\s+Based on', pg):
                    res[cid] = i + 1
                    break
        first = slug(load(files[0])[0]['title'])
        if first in res:
            res['part-' + slug(part_no)] = res[first] - 1
    return res


if __name__ == '__main__':
    build(page_numbers(sys.argv[1]) if len(sys.argv) > 1 else None)
