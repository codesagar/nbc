#!/usr/bin/env python3
"""Build the portable reading edition from the sole story shelf. Never edits sources."""
from pathlib import Path
import argparse, hashlib, html, json, math, re, shutil, tempfile, zipfile
from urllib.parse import unquote, urlsplit
from html.parser import HTMLParser
import mistune
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DESIGN = ROOT / 'Studio/reader'
OUT = ROOT / 'Reader'
CUT = re.compile(r'^## (?:Refinement record|Provenance and editorial notes)\s*$', re.M)
ALT = '\n## Meaningful alternative\n'
IMAGE_SETTINGS = 'webp-1600-q90-thumb560-q82-v1'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def clean_story(text):
    """Cut only named archival sections; narrative epilogues are story text."""
    hit = CUT.search(text)
    if not hit:
        raise ValueError('Missing archival boundary; inspect story before export')
    narrative = text[:hit.start()].strip()
    parts = narrative.split(ALT, 1)
    primary = re.sub(r'\n(?:---\s*)+$', '', parts[0]).strip()
    alternative = None
    if len(parts) == 2 and '<details>' in parts[1]:
        match = re.search(r'<details>\s*<summary>.*?</summary>\s*(.*?)\s*</details>', parts[1], re.S)
        if not match:
            raise ValueError('Incomplete alternative disclosure')
        alternative = match.group(1).strip()
    return primary, alternative

class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, data): self.parts.append(data)

def plain(s):
    parser = Text(); parser.feed(s); return ' '.join(' '.join(parser.parts).split())

def shelf_entries():
    entries = []; group = None
    for line in (ROOT / 'Stories/README.md').read_text().splitlines():
        if line.startswith('## '): group = line[3:]
        match = re.match(r'\| (S\d{3}) \| \[[^\]]+\]\(([^)]+)\) \| (.*?) \|$', line)
        if match:
            sid, path, summary = match.groups()
            entries.append({'id':sid, 'source':ROOT/'Stories'/path, 'group':group, 'summary':summary})
    if not entries or len({e['id'] for e in entries}) != len(entries):
        raise ValueError('Shelf IDs missing or repeated')
    if {e['source'] for e in entries} != set((ROOT/'Stories').glob('S[0-9][0-9][0-9]-*.md')):
        raise ValueError('Story shelf and source files differ')
    return entries

class Artwork:
    def __init__(self, dest):
        self.dest = dest; self.sources = {}; self.by_hash = {}; self.cached = {}; self.old_files = {}
        proof = ROOT/'Studio/reader-build.json'; marker = OUT/'.generated-reader.json'
        if proof.is_file() and marker.is_file():
            old = json.loads(proof.read_text())
            if old.get('image_settings') == IMAGE_SETTINGS:
                self.cached = {v['source_sha256']:v for v in old['image_derivatives'].values()}
                self.old_files = json.loads(marker.read_text())['files']
    def add(self, path):
        path = path.resolve()
        if not path.is_relative_to(ROOT) or not path.is_file(): raise ValueError(f'Invalid image {path}')
        digest = sha(path)
        cached = self.cached.get(digest)
        if digest not in self.by_hash and cached and all(
                (OUT/cached[k]).is_file() and sha(OUT/cached[k]) == self.old_files.get(cached[k])
                for k in ('file','thumbnail')):
            for k in ('file','thumbnail'): shutil.copyfile(OUT/cached[k], self.dest/cached[k])
            self.by_hash[digest] = {k:cached[k] for k in ('file','thumbnail','width','height','sha256')}
        if digest not in self.by_hash:
            with Image.open(path) as source:
                picture = ImageOps.exif_transpose(source).convert('RGB')
                # Preserve framing and aspect ratio. Original production bytes stay untouched.
                picture.thumbnail((1600,1600), Image.Resampling.LANCZOS)
                width, height = picture.size
                filename = f'images/{digest[:20]}.webp'
                picture.save(self.dest/filename, 'WEBP', quality=90, method=6)
                picture.thumbnail((560,560), Image.Resampling.LANCZOS)
                thumb = f'images/{digest[:20]}-thumb.webp'
                picture.save(self.dest/thumb, 'WEBP', quality=82, method=6)
            self.by_hash[digest] = {'file':filename,'thumbnail':thumb,'width':width,'height':height,'sha256':sha(self.dest/filename)}
        self.sources[str(path.relative_to(ROOT))] = {'source_sha256':digest, **self.by_hash[digest]}
        return self.by_hash[digest]

class Renderer(mistune.HTMLRenderer):
    def __init__(self, source, artwork):
        super().__init__(escape=False); self.source = source; self.artwork = artwork; self.headings = []; self.images = []
    def image(self, text, url, title=None):
        u = urlsplit(url)
        if u.scheme: raise ValueError('Reading images must be local')
        record = self.artwork.add(self.source.parent/unquote(u.path)); self.images.append(record['file'])
        return f'<figure><img src="../{record["file"]}" alt="{html.escape(plain(text),quote=True)}" width="{record["width"]}" height="{record["height"]}" loading="lazy" decoding="async"></figure>\n'
    def paragraph(self, text):
        if text.strip().startswith('<figure>') and text.strip().endswith('</figure>'): return text
        return super().paragraph(text)
    def heading(self, text, level, **attrs):
        anchor = f'part-{len(self.headings)+1}'; self.headings.append((anchor,plain(text)))
        return f'<h{level} id="{anchor}">{text}</h{level}>\n'

def shell(title, body, prefix='', attrs=''):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · Neet &amp; Buddy</title><meta name="description" content="The illustrated adventures of Neet, Buddy, and the humans who love them.">
<link rel="stylesheet" href="{prefix}reader.css"><script src="{prefix}reader.js" defer></script></head>
<body {attrs}><a class="skip" href="#main">Skip to content</a>
<header class="topbar"><a class="brand" href="{prefix}index.html">Neet <span>&amp;</span> Buddy</a><nav class="topnav" aria-label="Main"><a href="{prefix}index.html#library">The stories</a><a href="{prefix}index.html#about">About</a></nav></header>
{body}<footer class="site-footer"><span>Neet &amp; Buddy Chronicles</span><span>A little chaos. A lot of love.</span></footer></body></html>'''

class Targets(HTMLParser):
    def __init__(self): super().__init__(); self.targets = []
    def handle_starttag(self, tag, attrs):
        for k,v in attrs:
            if k in ('src','href'): self.targets.append(v)

def verify_site(folder):
    failures = []; pages = list(folder.rglob('*.html'))
    for p in pages:
        parser = Targets(); parser.feed(p.read_text())
        for target in parser.targets:
            u = urlsplit(target)
            if u.scheme or u.netloc or u.path.startswith('/'):
                failures.append(f'{p.name}: nonportable target {target}'); continue
            if u.path and not (p.parent/unquote(u.path)).is_file(): failures.append(f'{p.name}: missing {target}')
        if re.search(r'/Users/|Refinement record|Provenance and editorial notes|\.\.\/Productions/',p.read_text()):
            failures.append(f'{p.name}: archival content leaked')
    if failures: raise ValueError('\n'.join(failures))
    return len(pages)

def build():
    entries = shelf_entries(); groups = list(dict.fromkeys(e['group'] for e in entries))
    labels = ['India & homecoming','Life at home','More adventures']
    with tempfile.TemporaryDirectory(prefix='nbc-reader-') as tmp:
        dest = Path(tmp)/'Reader'; (dest/'images').mkdir(parents=True); (dest/'stories').mkdir()
        artwork = Artwork(dest); pages = []; cards = []; story_proofs = []
        for index,e in enumerate(entries):
            source = e['source']; text = source.read_text(); primary, alternate = clean_story(text)
            title = primary.splitlines()[0].lstrip('# ').strip(); e['title']=title; e['page']=f'stories/{source.stem}.html'
            e['primary']=primary; e['alternate']=alternate
        for index,e in enumerate(entries):
            title=e['title']; source=e['source']; rendered={}
            for variant,content in [('primary',e['primary']),('alternative',e['alternate'])]:
                if content is None: continue
                prose = content.split('\n',1)[1].strip() if variant=='primary' else content
                renderer=Renderer(source,artwork); markdown=mistune.create_markdown(renderer=renderer,plugins=['table']); body=markdown(prose)
                page=e['page'] if variant=='primary' else e['page'].replace('.html','-alternative.html')
                sid=e['id'] if variant=='primary' else e['id']+'-alternative'
                minutes=max(1,math.ceil(len(plain(body).split())/200))
                contents=''
                if len(renderer.headings)>3:
                    items=''.join(f'<li><a href="#{a}">{html.escape(t)}</a></li>' for a,t in renderer.headings)
                    contents=f'<details class="contents"><summary>In this story</summary><ol>{items}</ol></details>'
                variantlink=''
                if e['alternate']:
                    target=Path(e['page']).name if variant=='alternative' else Path(e['page']).name.replace('.html','-alternative.html')
                    label='Return to the main telling' if variant=='alternative' else 'Read another telling of this story'
                    variantlink=f'<a href="{target}">{label}</a>'
                prevnext=[]
                for pos, label in [(index-1,'Previous story'),(index+1,'Next story')]:
                    if 0<=pos<len(entries):
                        other=entries[pos];prevnext.append(f'<a href="{Path(other["page"]).name}"><span>{label}</span><strong>{html.escape(other["title"])}</strong></a>')
                    else: prevnext.append('<a href="../index.html#library"><span>The collection</span><strong>Back to the stories</strong></a>')
                eyebrow=f'Story {index+1:02} / {len(entries)}' + (' · Another telling' if variant=='alternative' else '')
                article=f'''<div class="reading-progress" aria-hidden="true"></div><main id="main">
<section class="story-head"><div class="eyebrow">{eyebrow}</div><h1>{html.escape(title)}</h1><div class="story-meta">{minutes} minute read · {len(renderer.images)} illustrations</div>
<div class="reading-tools only-js" aria-label="Reading preferences"><button data-font="-2" aria-label="Smaller text">A−</button><button data-font="2" aria-label="Larger text">A+</button><button data-theme aria-pressed="false">Night</button></div></section>
{contents}<article class="prose">{body}</article>
<section class="ending" aria-label="Continue reading"><div class="end-mark" aria-hidden="true">· · ·</div><button class="button only-js" data-mark-read aria-pressed="false">Mark as read</button><div class="ending-links"><a href="../index.html#library">All stories</a>{variantlink}</div><nav class="next-prev" aria-label="Story navigation">{''.join(prevnext)}</nav></section></main>'''
                attrs=f'data-story="{sid}" data-title="{html.escape(title,quote=True)}" data-page="{page}"'
                (dest/page).write_text(shell(title,article,'../',attrs)); pages.append(page)
                rendered[variant]={'page':page,'images':len(renderer.images),'rendered_text_sha256':hashlib.sha256(plain(body).encode()).hexdigest(),'reading_minutes':minutes}
                if variant=='primary':
                    first_img=re.search(r'!\[[^\]]*\]\(([^)]+)\)',e['primary'])
                    if not first_img: raise ValueError(f'{source}: no contextual artwork')
                    e['cover']=artwork.add(source.parent/first_img.group(1)); e['minutes']=minutes
                    # First narrative paragraph gives a teaser without importing archival browse notes.
                    match=re.search(r'<p>(.*?)</p>',body,re.S); teaser=plain(match.group(1)) if match else ''
                    if len(teaser)>150:teaser=teaser[:150].rsplit(' ',1)[0]+'…'
                    e['teaser']=teaser
            story_proofs.append({'id':e['id'],'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'exports':rendered})
            group=groups.index(e['group']); search=html.escape((title+' '+e['summary']).lower(),quote=True)
            cards.append(f'''<article class="card" data-id="{e['id']}" data-group="{group}" data-search="{search}"><a href="{e['page']}"><img class="card-image" src="{e['cover']['thumbnail']}" alt="" width="560" height="373" loading="lazy"><div class="card-meta"><span>Story {index+1:02} · {e['minutes']} min</span><span class="read-badge" hidden>Read ✓</span></div><h3>{html.escape(title)}</h3><p>{html.escape(e['teaser'])}</p></a></article>''')
        filters='<button data-filter="all" aria-pressed="true">All stories</button>'+''.join(f'<button data-filter="{i}" aria-pressed="false">{html.escape(labels[i] if i<len(labels) else g)}</button>' for i,g in enumerate(groups))
        hero=entries[0]['cover']
        home=f'''<main id="main"><section class="hero" id="about"><div><div class="eyebrow">The illustrated collection</div><h1>Neet &amp; Buddy<br>Chronicles</h1><p>The everyday adventures of two extraordinary dogs and the humans who love them.</p><div class="actions"><a class="button" href="{entries[0]['page']}">Begin the adventures →</a><a class="quiet-link" href="#library">Browse the collection</a></div><p><a id="resume" class="quiet-link" hidden></a></p><div class="stats">{len(entries)} STORIES &nbsp;·&nbsp; {len(artwork.by_hash)} ILLUSTRATIONS</div></div><img class="hero-image" src="{hero['file']}" width="{hero['width']}" height="{hero['height']}" alt="Buddy guards a slipper under the breakfast table while Neet heads toward the kitchen." fetchpriority="high"></section>
<section id="library" class="library"><div class="library-heading"><h2>A story for every mood.</h2><div class="search-wrap only-js"><label for="search">Find an adventure</label><input id="search" type="search" placeholder="Try vacuum, India, or birthday…" autocomplete="off"></div></div><div class="filters only-js" aria-label="Story collections">{filters}</div><p id="result-count" class="result-count" aria-live="polite">{len(entries)} stories</p><p id="no-results" hidden>No stories match yet. Try another word or choose All stories.</p><div class="cards">{''.join(cards)}</div></section></main>'''
        (dest/'index.html').write_text(shell('The stories',home,attrs=f'data-pages="{"|".join(pages)}"'))
        for name in ['reader.css','reader.js']:shutil.copyfile(DESIGN/name,dest/name)
        (dest/'.nojekyll').write_text('')
        count=verify_site(dest)
        outputs={str(p.relative_to(dest)):sha(p) for p in sorted(dest.rglob('*')) if p.is_file()}
        (dest/'.generated-reader.json').write_text(json.dumps({'generator':'Studio/build_reader.py','files':outputs},indent=2)+'\n')
        if OUT.exists():
            marker=OUT/'.generated-reader.json'
            if not marker.is_file():raise ValueError('Reader folder is not managed; refusing to replace it')
            previous=json.loads(marker.read_text())['files']
            actual={str(p.relative_to(OUT)):p for p in OUT.rglob('*') if p.is_file() and p.name!='.DS_Store' and p!=marker}
            if set(actual)!=set(previous) or any(sha(p)!=previous[n] for n,p in actual.items()):
                raise ValueError('Reader contains hand edits. Preserve them before rebuilding; edit Studio/reader for design changes.')
            previous_dir = Path(tmp)/'PreviousReader'
            OUT.rename(previous_dir)
            try:
                dest.rename(OUT)
            except Exception:
                previous_dir.rename(OUT)
                raise
        else:
            dest.rename(OUT)
        proof={'generator':'Studio/build_reader.py','image_settings':IMAGE_SETTINGS,'source_shelf_sha256':sha(ROOT/'Stories/README.md'),'html_pages':count,'primary_stories':len(entries),'complete_alternatives':len(pages)-len(entries),'unique_illustrations':len(artwork.by_hash),'reader_bytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),'stories':story_proofs,'image_derivatives':artwork.sources,'source_policy':'Exact narrative text and image placement retained; named archival sections hidden from reader; complete variants separate; source Markdown and production originals untouched. Shorter-version omission notes remain in source only. Narrative epilogues retained.'}
        (ROOT/'Studio/reader-build.json').write_text(json.dumps(proof,indent=2)+'\n')
        print(f'Built {len(entries)} stories + {len(pages)-len(entries)} alternate tellings; {len(artwork.by_hash)} pictures; {proof["reader_bytes"]/1e6:.1f} MB. Open Reader/index.html.')

def package(path):
    verify_site(OUT); target=Path(path).expanduser().resolve();target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():raise ValueError('Choose a new versioned ZIP path; existing packages are preserved')
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file() and not p.name.startswith('.'):
                z.write(p,Path('Neet-and-Buddy')/p.relative_to(OUT))
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for n in z.namelist():assert hashlib.sha256(z.read(n)).hexdigest()==sha(OUT/Path(n).relative_to('Neet-and-Buddy'))
    print(f'ZIP verified: {target} ({target.stat().st_size/1e6:.1f} MB)')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');parser.add_argument('--zip',metavar='PATH');args=parser.parse_args()
    if args.check:print(f'PASS: {verify_site(OUT)} portable HTML pages; local links and assets resolve.')
    else:build()
    if args.zip:package(args.zip)
