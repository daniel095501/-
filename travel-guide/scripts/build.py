"""Validate plain-text guide sources and generate deterministic static HTML."""
from pathlib import Path
from html import escape
import json
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ('行李', '交通', '行前', '住宿')
FIELDS = {'slug', 'order', 'title', 'category', 'summary', 'intro', 'steps', 'checklist', 'pitfalls', 'verification', 'resources'}

def text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Expected nonempty plain text')
    if '<' in value or '>' in value:
        raise ValueError('HTML is not allowed in content')
    return value

def exact(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f'Unexpected fields; expected {keys}')

def slug(value):
    text(value)
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
        raise ValueError('Invalid kebab-case identifier')

def validate(g):
    exact(g, FIELDS)
    slug(g['slug'])
    if type(g['order']) is not int or g['order'] < 1:
        raise ValueError('order must be a positive integer')
    for key in ('title', 'category', 'summary', 'intro', 'verification'):
        text(g[key])
    if g['category'] not in CATEGORIES:
        raise ValueError('Unknown category')
    for key, minimum in (('steps', 3), ('checklist', 4), ('pitfalls', 2), ('resources', 0)):
        if not isinstance(g[key], list) or len(g[key]) < minimum:
            raise ValueError(f'Invalid {key}')
    for item in g['steps']:
        exact(item, ('title', 'body'))
        text(item['title']); text(item['body'])
    checklist_ids = []
    for item in g['checklist']:
        exact(item, ('id', 'text')); slug(item['id']); text(item['text'])
        checklist_ids.append(item['id'])
    if len(set(checklist_ids)) != len(checklist_ids):
        raise ValueError('Duplicate checklist id')
    for item in g['pitfalls']: text(item)
    for item in g['resources']:
        exact(item, ('label', 'url')); text(item['label']); text(item['url'])
        u = urlparse(item['url'])
        if u.scheme != 'https' or not u.netloc or u.username or u.password:
            raise ValueError('Resource URL must be HTTPS without credentials')

def load_guides():
    guides = []
    for path in sorted((ROOT / 'content/guides').glob('*.json')):
        g = json.loads(path.read_text(encoding='utf-8'))
        validate(g)
        if path.stem != g['slug']: raise ValueError('Filename/slug mismatch')
        guides.append(g)
    if not guides: raise ValueError('No guides')
    for key in ('slug', 'order'):
        if len({g[key] for g in guides}) != len(guides): raise ValueError(f'Duplicate {key}')
    return sorted(guides, key=lambda g: g['order'])

def template(name, values):
    source = (ROOT / 'templates' / name).read_text(encoding='utf-8')
    result = re.sub(r'\{\{([a-z_]+)\}\}', lambda m: str(values[m[1]]), source)
    if '{{' in result: raise ValueError('Unresolved template token')
    return result

def card(g, prefix='guides/'):
    e = escape
    search = ' '.join([g['title'], g['category'], g['summary'], g['intro']] + [x['title'] for x in g['steps']] + [x['text'] for x in g['checklist']])
    return f'''<a class="guide-card" href="{prefix}{g['slug']}.html" data-category="{e(g['category'])}" data-search="{e(search)}"><div class="card-top"><span class="category">{e(g['category'])}</span><span class="card-number">FIELD NOTE / {g['order']:02d}</span></div><h3>{e(g['title'])}</h3><p>{e(g['summary'])}</p><div class="card-bottom"><span>{len(g['steps'])} 個步驟 · {len(g['checklist'])} 項檢查</span><span class="card-arrow" aria-hidden="true">↗</span></div></a>'''

def page(body, title, description, prefix):
    return template('layout.html', {'body': body, 'title': escape(title), 'description': escape(description), 'prefix': prefix})

def outputs():
    guides = load_guides()
    filters = ''.join(f'<button type="button" data-category-filter="{c}" aria-pressed="{str(c == "全部").lower()}">{c}</button>' for c in ('全部',) + tuple(c for c in CATEGORIES if any(g['category'] == c for g in guides)))
    home = template('index.html', {'guide_count': len(guides), 'filters': filters, 'cards': '\n'.join(card(g) for g in guides)})
    result = {'index.html': page(home, '旅行準備指南', '行李、交通與行前確認。從一份小清單開始，照自己的步調準備旅行。', '')}
    for i, g in enumerate(guides):
        steps = ''.join(f'<li><h3>{escape(s["title"])}</h3><p>{escape(s["body"])}</p></li>' for s in g['steps'])
        checks = ''.join(f'<label class="check-item" for="check-{s["id"]}"><input id="check-{s["id"]}" data-check-id="{s["id"]}" type="checkbox"><span>{escape(s["text"])}</span></label>' for s in g['checklist'])
        nav = ''.join(f'<a href="{x["slug"]}.html"' + (' aria-current="page"' if x['slug'] == g['slug'] else '') + f'>{x["order"]:02d}　{escape(x["title"])}</a>' for x in guides)
        others = [guides[(i + shift) % len(guides)] for shift in range(1, min(3, len(guides)))]
        resources = '<p class="resource-links">' + ''.join(f'<a href="{escape(r["url"])}" target="_blank" rel="noopener noreferrer">{escape(r["label"])} ↗</a>' for r in g['resources']) + '</p>' if g['resources'] else ''
        body = template('guide.html', {'category': escape(g['category']), 'number': f'{g["order"]:02d}', 'heading': escape(g['title']), 'summary': escape(g['summary']), 'step_count': len(g['steps']), 'check_count': len(g['checklist']), 'slug': g['slug'], 'intro': escape(g['intro']), 'steps': steps, 'checklist': checks, 'pitfalls': ''.join(f'<li>{escape(p)}</li>' for p in g['pitfalls']), 'verification': escape(g['verification']), 'resources': resources, 'guide_nav': nav, 'related': ''.join(card(x, '') for x in others)})
        result[f'guides/{g["slug"]}.html'] = page(body, g['title'], g['summary'], '../')
    return result

def main():
    result = outputs()
    expected = {ROOT / p for p in result if p.startswith('guides/')}
    existing = set((ROOT / 'guides').glob('*.html'))
    if existing - expected:
        raise ValueError('Stale generated guides; inspect before deleting or renaming content')
    for name, content in result.items():
        path = ROOT / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8', newline='\n')
    print(f'Built {len(result)} HTML pages from {len(result)-1} validated guides.')

if __name__ == '__main__': main()
