"""Fetch five real documents and verify short excerpts before Wiki authoring.
Full source caches stay outside the published folder; only short excerpts are exported.
"""
from pathlib import Path
from datetime import datetime, timezone
from html.parser import HTMLParser
import argparse
import hashlib
import io
import json
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def compact(s):
    return re.sub(r'\s+', '', s)

class BodyText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip=0; self.parts=[]
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','noscript'): self.skip+=1
        if tag in ('p','li','h1','h2','h3','div','br'): self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style','noscript'): self.skip=max(0,self.skip-1)
    def handle_data(self, data):
        if not self.skip: self.parts.append(data)

def stamp():
    return datetime.now(timezone.utc).isoformat()

def run(cache):
    cache.mkdir(parents=True,exist_ok=True)
    (ROOT/'data').mkdir(exist_ok=True); (ROOT/'raw').mkdir(exist_ok=True)
    sources=json.loads((ROOT/'sources.json').read_text(encoding='utf-8'))
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    events=[]; records=[]
    def log(node, status, source=None, **detail):
        events.append({'time_utc':stamp(),'node':node,'status':status,'source':source,**detail})
    for s in sources:
        sid=s['id'];log('fetch','started',sid,url=s['url'])
        try:
            req=urllib.request.Request(s['url'],headers={'User-Agent':'Mozilla/5.0 (educational source verification)','Accept':'text/html,application/pdf'})
            with urllib.request.urlopen(req,timeout=30) as response:
                body=response.read(); ctype=response.headers.get('Content-Type',''); final_url=response.url; code=response.status
            sha=hashlib.sha256(body).hexdigest()
            (cache/(sid+('.pdf' if s['kind']=='pdf' else '.html'))).write_bytes(body)
            log('fetch','passed',sid,http_status=code,bytes=len(body),sha256=sha)
            if s['kind']=='pdf':
                from pypdf import PdfReader
                reader=PdfReader(io.BytesIO(body))
                page=s['page_index']; content=reader.pages[page].extract_text()
                cover=reader.pages[0].extract_text()
                if compact(s['title']) not in compact(cover): raise ValueError('Confirmed title missing from PDF cover')
                if s.get('discovery_title') and s['discovery_title']!=s['title']:
                    log('source_metadata','issue_found',sid,problem='工具顯示題名與PDF封面不一致',candidate_title=s['discovery_title'],verified_title=s['title'])
                    log('source_metadata','resolved',sid,resolution='檢查PDF封面題名，保留實際文件日期和實體頁碼；僅使用第4題定義')
            else:
                html=body.decode('utf-8-sig',errors='replace')
                parser=BodyText();parser.feed(html);content=''.join(parser.parts)
            text=compact(content)
            if len(text)<150: raise ValueError('Too little article text; do not ingest a navigation/error page')
            for e in s['evidence']:
                if compact(e['quote']) not in text: raise ValueError('Excerpt not found in actual document: '+e['id'])
            log('excerpt_check','passed',sid,verified_ids=[e['id'] for e in s['evidence']],extracted_characters=len(text))
            record={**s,'status':'ingested','retrieved_utc':stamp(),'http_status':code,'final_url':final_url,'content_type':ctype,'sha256':sha,'bytes':len(body),'extracted_characters':len(text),'excerpt_check':'passed'}
            records.append(record)
            short=f'# {sid}｜{s["title"]}\n\n發布單位：{s["publisher"]}\n\n來源：{s["url"]}\n\n原始日期：{s["published"]}\n\n實際擷取：{record["retrieved_utc"]}\n\n適用範圍：{s["scope"]}\n\nSHA-256：`{sha}`\n\n本檔只保留教學需要的短摘錄，非原文全文。\n\n'
            if 'page_label' in s: short+='定位：'+s['page_label']+'\n\n'
            for e in s['evidence']:short+=f'## {e["id"]}\n\n> {e["quote"]}\n\n'
            (ROOT/'raw'/f'{sid}.md').write_text(short,encoding='utf-8')
        except Exception as exc:
            log('ingest','failed',sid,error=type(exc).__name__+': '+str(exc))
    ready=len(records)>=5 and len(records)==len(sources)
    result={'run_id':run_id,'created_utc':stamp(),'ingested_count':len(records),'ready':ready,'records':records,'events':events,'scope':'Actual HTTP fetch and excerpt verification; semantic notes are authored by AI after source review.'}
    (ROOT/'data/ingest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'docs'/f'ingest-{run_id}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'run_id':run_id,'ready':ready,'ingested':len(records),'events':[x for x in events if x['status'] in ('failed','issue_found','resolved')]},ensure_ascii=False,indent=2))
    return 0 if ready else 1

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--cache-dir',type=Path,required=True);args=ap.parse_args()
    raise SystemExit(run(args.cache_dir))
