"""Run the reproducible graph. Refresh pauses for a new scope review if hashes change."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,subprocess,sys

ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--refresh',action='store_true');ap.add_argument('--cache-dir',type=Path,default=ROOT/'.cache')
args=ap.parse_args();steps=[]
if args.refresh:steps.append(('取得與摘錄檢查',[sys.executable,str(ROOT/'scripts/ingest.py'),'--cache-dir',str(args.cache_dir)]))
steps.extend([('Wiki與教學建置',[sys.executable,str(ROOT/'scripts/build.py')]),('結構與連結檢查',[sys.executable,str(ROOT/'scripts/check.py')])])
events=[]
for node,command in steps:
    result=subprocess.run(command,cwd=ROOT,text=True,encoding='utf-8',capture_output=True)
    event={'time_utc':datetime.now(timezone.utc).isoformat(),'node':node,'exit_code':result.returncode,'stdout':result.stdout.strip(),'stderr':result.stderr.strip()}
    events.append(event)
    print(result.stdout,end='')
    if result.returncode:
        print(result.stderr,file=sys.stderr)
        break
passed=all(x['exit_code']==0 for x in events)
report={'status':'passed' if passed else 'stopped_for_revision','refresh_sources':args.refresh,'steps':events,'rerun_rule':'依failed建置紀錄的return_to修改內容後再執行；不自動捏造修訂或模型回覆。'}
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
(ROOT/'docs'/f'workflow-run-{stamp}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':report['status'],'executed_steps':len(events)},ensure_ascii=False))
raise SystemExit(0 if passed else 1)
