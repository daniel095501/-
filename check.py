from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
from datetime import datetime, timezone
import json,re
from build import ROOT,load,dump

class Page(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.ids=set();self.links=[];self.h1=0;self.lang='';self.quiz_names=set()
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:
            assert a['id'] not in self.ids,'Duplicate HTML id: '+a['id']
            self.ids.add(a['id'])
        if tag=='html':self.lang=a.get('lang')
        if tag=='h1':self.h1+=1
        for k in ('href','src'):
            if k in a:self.links.append(a[k])

def run():
    ingest=load('data/ingest.json');topics=load('data/topics.json');claims={c['id']:c for c in load('data/claims.json')};lesson=load('data/lesson.json')
    assert ingest['ready'] and len(ingest['records'])>=5
    assert len({s['url'] for s in ingest['records']})==len(ingest['records'])
    for s in ingest['records']:
        assert s['status']=='ingested' and s['excerpt_check']=='passed' and len(s['sha256'])==64
        assert (ROOT/'raw'/f'{s["id"]}.md').is_file()
    for t in topics:
        md=(ROOT/'wiki'/f'{t["slug"]}.md').read_text(encoding='utf-8')
        for cid in t['claim_ids']:assert f'<!-- claim:{cid} -->\n{claims[cid]["text"]}\n<!-- /claim -->' in md
        for slug in t['related']:assert (ROOT/'wiki'/f'{slug}.md').is_file()
    total_knowledge=0
    for s in lesson['slides']:
        assert s['claims']==[k['claim_id'] for k in s['knowledge']]
        for k in s['knowledge']:
            assert k['text_from_wiki']==claims[k['claim_id']]['text'];total_knowledge+=1
    files=[ROOT/'index.html',ROOT/'sources.html',ROOT/'slides.html',ROOT/'workflow.html']+sorted((ROOT/'wiki').glob('*.html'))
    assert len(files)==10
    parsed={}
    for p in files:
        t=p.read_text(encoding='utf-8');parser=Page();parser.feed(t);parsed[p.resolve()]=parser
        assert parser.h1==1 and parser.lang=='zh-Hant' and 'main' in parser.ids,p.name
        assert '{{' not in t,'Unresolved template placeholder'
    refs=0
    for p,parser in parsed.items():
        for link in parser.links:
            u=urlparse(link)
            if u.scheme:
                assert u.scheme=='https',f'Unexpected link scheme: {link}'
                continue
            assert not u.path.startswith('/') and not u.netloc,link
            target=(p.parent/unquote(u.path)).resolve() if u.path else p
            assert target.is_relative_to(ROOT) and target.is_file(),f'Broken local link: {p.name} {link}'
            if u.fragment:
                assert target in parsed and unquote(u.fragment) in parsed[target].ids,f'Broken anchor: {link}'
            refs+=1
    for p in (ROOT/'wiki').glob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            u=urlparse(link)
            if u.scheme:continue
            target=(p.parent/unquote(u.path)).resolve()
            assert target.is_relative_to(ROOT) and target.is_file(),f'Broken Wiki crosslink: {p.name} {link}'
    report={'status':'passed','checked_utc':datetime.now(timezone.utc).isoformat(),'ingested_sources':len(ingest['records']),'wiki_pages':len(topics),'teaching_slides':len(lesson['slides']),'wiki_claim_mappings':total_knowledge,'html_pages':len(files),'local_link_and_asset_references':refs,'scope':'結構與對應檢查；語意真偽另經來源閱讀複核'}
    dump('data/static-check.json',report);print(json.dumps(report,ensure_ascii=False))
    return report

if __name__=='__main__':run()
