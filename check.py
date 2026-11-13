"""Check source contracts, generated consistency, page structure and local links."""
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
import json
from build import ROOT, load_guides, outputs

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set(); self.links = []; self.h1 = 0; self.lang = None; self.labels = set(); self.checks = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            if a['id'] in self.ids: raise ValueError(f'Duplicate id: {a["id"]}')
            self.ids.add(a['id'])
        if tag == 'html': self.lang = a.get('lang')
        if tag == 'h1': self.h1 += 1
        if tag == 'label' and 'for' in a: self.labels.add(a['for'])
        if tag == 'input' and a.get('type') == 'checkbox': self.checks.add(a['id'])
        for key in ('href', 'src'):
            if key in a: self.links.append(a[key])

def check():
    guides = load_guides(); expected = outputs(); pages = {}
    actual_paths = {str(p.relative_to(ROOT)).replace('\\', '/') for p in (ROOT / 'guides').glob('*.html')}
    assert actual_paths == {p for p in expected if p.startswith('guides/')}, 'Unexpected/missing generated guide'
    for name, rendered in expected.items():
        path = ROOT / name
        assert path.read_text(encoding='utf-8') == rendered, f'Stale output: {name}'
        p = Page(); p.feed(rendered); pages[path.resolve()] = p
        assert p.h1 == 1 and p.lang == 'zh-Hant', name
        assert 'main' in p.ids and '#main' in p.links, f'Missing skip target: {name}'
        assert p.checks <= p.labels, f'Unlabelled checklist: {name}'
        if name.startswith('guides/'):
            assert {'purpose','steps','checklist','pitfalls','verify'} <= p.ids, name
    count = 0
    for path, page in pages.items():
        for link in page.links:
            u = urlparse(link)
            if u.scheme:
                assert u.scheme == 'https', f'Unexpected scheme: {link}'
                continue
            assert not u.netloc and not u.path.startswith('/'), f'Absolute site link: {link}'
            target = (path.parent / unquote(u.path)).resolve() if u.path else path
            assert target.is_relative_to(ROOT), f'Link escapes project: {link}'
            assert target.is_file(), f'Broken link {path.name}: {link}'
            if u.fragment:
                assert target in pages and unquote(u.fragment) in pages[target].ids, f'Broken anchor: {link}'
            count += 1
    print(json.dumps({'status': 'passed', 'guides': len(guides), 'html_pages': len(pages), 'local_links_and_assets_checked': count, 'generated_outputs_current': True, 'checklist_labels_valid': True}, ensure_ascii=False))

if __name__ == '__main__': check()
