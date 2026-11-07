"""Explicit file:// offline browser and PDF structural verification, no server."""
import argparse,json,re,sys,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
from pypdf import PdfReader
from playwright.sync_api import sync_playwright
from work_instructions import read,digest,callout_groups,callout_labels,location_range
p=argparse.ArgumentParser();p.add_argument('package',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args();root=a.package.resolve();c=read(root/'process.json');m=read(root/'manifest.json')
for path,sha in m['outputs_sha256'].items():assert digest((root/path).read_bytes())==sha,path
requests=[];errors=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch();context=browser.new_context(offline=True,viewport={'width':1200,'height':900})
 context.route('http://**/*',lambda route: (requests.append(route.request.url),route.abort()));context.route('https://**/*',lambda route:(requests.append(route.request.url),route.abort()))
 page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.goto((root/'index.html').as_uri());page.wait_for_load_state('load')
 assert page.locator('section[id]').count()==len(c['operations'])+1
 assert page.locator('img').evaluate_all('(xs)=>xs.every(x=>x.complete && x.naturalWidth>0)')
 for o in c['operations']:assert page.locator('[id="'+o['id']+'"]').count()==1
 assert page.locator('a[href^="#bom-"]').count()==sum(len(callout_groups(c,o)) for o in c['operations'])
 if c.get('callout_style')=='grouped_by_part':
  for o in c['operations']:
   section=page.locator('[id="'+o['id']+'"]')
   for group in callout_groups(c,o):
    row=section.locator('tr[data-callout-group="'+str(group['number'])+'"]')
    assert row.get_attribute('data-part')==group['part']
    assert int(row.get_attribute('data-quantity'))==group['quantity']
 for anchor in page.locator('a[href^="#"]').evaluate_all('(xs)=>xs.map(x=>x.getAttribute("href").slice(1))'):assert page.locator('[id="'+anchor+'"]').count()==1,anchor
 page.locator('[id="s1.P020"] img').screenshot(path=str(a.report.parent/'pod-hardware.png'))
 page.locator('[id="F020"] img').screenshot(path=str(a.report.parent/'frame-joints.png'))
 # Enlarge from local link, then back; no external requests allowed.
 page.locator('[id="s1.P020"] a[href$=".svg"]').click();assert page.url.startswith('file:');page.go_back();assert not requests and not errors
 browser.close()
r=PdfReader(root/'work-instructions.pdf');text=subprocess.check_output(['pdftotext',str(root/'work-instructions.pdf'),'-'],text=True)
for o in c['operations']:assert o['id'] in text
for n in range(len(c['operations'])+1):assert 'Figure '+str(n) in text
assert all(float(p.mediabox.width)==612 and float(p.mediabox.height)==792 for p in r.pages)
grouped_checked=False
if c.get('callout_style')=='grouped_by_part':
 registry=read(root/'callouts.json')
 def bubble_labels(path):
  svg=ET.parse(path).getroot()
  return [e.text for e in svg.iter('{http://www.w3.org/2000/svg}text') if e.get('font-size')=='11' and re.fullmatch(r'[0-9]+[a-z]*',e.text or '')]
 for n,o in enumerate(c['operations'],1):
  labels=callout_labels(c,o);groups=callout_groups(c,o)
  assert registry['operations'][o['id']]['groups']==groups
  if o['id']!='F020':assert bubble_labels(root/'figures'/f'{n:02}-{o["id"]}.svg')==[labels[i] for i in o['uses']]
  for letter,detail in zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',o.get('details',[])):
   if 'section' not in detail['view']:
    assert bubble_labels(root/'figures'/f'{n:02}-{letter}.svg')==[labels[i] for i in detail['uses']]
  normalized=' '.join(text.split())
  for group in groups:assert 'locations '+location_range(group) in normalized
 grouped_checked=True
report={'result':'PASS','offline_file_url':True,'network_requests':requests,'browser_errors':errors,'operations':len(c['operations']),'pdf_pages':len(r.pages),'pdf_page_size_pt':[612,792],'manifest_output_hashes_verified':len(m['outputs_sha256']),'note':'PDF text checks supplement manual raster inspection; no physical validation.'}
report['grouped_callouts_verified']=grouped_checked
a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
