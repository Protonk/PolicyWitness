from pathlib import Path
import base64, hashlib, json, re, subprocess
from html.parser import HTMLParser
from collections import Counter
from weasyprint import HTML, CSS
from pypdf import PdfReader

ROOT = Path('/Users/raccoon/Desktop/Security/PolicyWitness')
OUT = ROOT / 'records/doc-lookback-2026-11-04/final-readers'
ART = OUT / 'artifacts'
WORK = OUT / 'rendering'

CSS_TEXT = '''
@page { size: 1684pt 1191pt; margin: 48pt 54pt 52pt;
  @bottom-center { content: counter(page); font-family: sans-serif; font-size: 10pt; color: #666; }
}
@page tall { size: 1800pt 2700pt; margin: 48pt; }
@page worker-map { size: 1500pt 3800pt; margin: 48pt; }
body { font-family: "Helvetica", "Arial", sans-serif; font-size: 13pt; line-height: 1.4; color: #171717; }
h1,h2,h3,h4 { break-after: avoid; line-height: 1.2; }
h1 { font-size: 30pt; } h2 { font-size: 23pt; margin-top: 28pt; }
h3 { font-size: 18pt; margin-top: 22pt; } h4 { font-size: 15pt; }
p,ul,ol,blockquote,pre,h1,h2,h3,h4 { max-width: 940pt; }
a { color: #1d4f88; text-decoration: none; overflow-wrap: anywhere; }
code { font-family: "Menlo", monospace; font-size: .90em; overflow-wrap: anywhere; }
pre { font-family: "Menlo", monospace; font-size: 11pt; line-height: 1.3; white-space: pre-wrap; }
pre code { font-size: inherit; overflow-wrap: normal; }
table { width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 10pt; line-height: 1.3; margin: 16pt 0 24pt; }
thead { display: table-header-group; }
th,td { border: .5pt solid #bbc2c9; padding: 6pt; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
th { background: #edf0f3; font-weight: bold; }
tr { break-inside: avoid; } td p,th p { margin: 0; }
.summary { font-weight: bold; margin-top: 16pt; }
figure { margin: 20pt 0; } figure img { max-width: 100%; max-height: 990pt; }
.tall { page: tall; break-before: page; break-after: page; }
.tall img { width: 1700pt; max-height: none; }
.worker-map { page: worker-map; break-before: page; break-after: page; }
.worker-map img { width: 1390pt; max-height: none; }
figcaption { font-size: 12pt; }
'''

# Faithful rendering of the one Mermaid diagram: same nine labeled nodes,
# four nested groups, eight directed relations and all edge labels. No new facts.
DOT = r'''digraph G {
graph [rankdir=TB, compound=true, fontname="Helvetica", nodesep=.45, ranksep=.6];
node [shape=box, style="rounded,filled", fillcolor="#f3f5f7", fontname="Helvetica", fontsize=13];
edge [fontname="Helvetica", fontsize=11];
subgraph cluster_worker { label="Worker";
 subgraph cluster_before { label="Before policy application";
 context [label="Credentials, restrictions\nand runtime state"];
 token [label="Optional token channel\nprepared separately"]; }
 policy [label="Compile policy,\nthen apply restriction"];
 subgraph cluster_after { label="Under the applied policy";
 acquire [label="Attempt acquisitions:\nfile targets, Mach rights,\nexec setup and children"];
 extension [label="Requested extension\nconsume or release"]; }
 context -> policy [label="starting context"];
 policy -> acquire [lhead=cluster_after,label="after host release"];
 token -> extension [label="bearer bytes for consume"];
}
storage [label="Reporting storage prepared before apply\nWorker and host retain separate views"];
subgraph cluster_outside { label="Outside the worker";
 validator [label="Validator queries\nthe live worker"];
 host [label="Host collects publications\nand assembles comparisons"];
 controller [label="Controller associates\nexternal log candidates"]; }
acquire -> storage [label="publish observations"];
extension -> storage [label="publish native results"];
storage -> host [label="host observes retained view"];
validator -> host [label="predictions"];
host -> controller [label="run evidence"];
}'''

def clean_markdown(text):
    parts = re.split(r'(```.*?```)', text, flags=re.S)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r'<!--.*?-->', '', parts[i], flags=re.S)
        parts[i] = re.sub(r'</?details[^>]*>', '', parts[i])
        parts[i] = re.sub(r'<summary>(.*?)</summary>', r'\1', parts[i])
    return ''.join(parts)

class Visible(HTMLParser):
    def __init__(self): super().__init__(); self.data=[]
    def handle_data(self, data): self.data.append(data)

manifest = {'sources':{}, 'artifacts':{}, 'conversion':{}, 'fidelity':{}}
for name in ['ARCHITECTURE','WORKER','LIMITS']:
    source = ROOT/'docs'/f'{name}.md'
    raw = source.read_text()
    manifest['sources'][str(source.relative_to(ROOT))] = hashlib.sha256(source.read_bytes()).hexdigest()
    clean = clean_markdown(raw)
    if name == 'LIMITS':
        dest=ART/'LIMITS.md'; dest.write_text(clean)
        manifest['artifacts'][dest.name]={'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'format':'flat Markdown','bytes':dest.stat().st_size}
        manifest['fidelity'][name]={'transformation':'remove non-visible HTML comments only; no figures or details blocks in source','visible_text_preserved':True,'tables':len(re.findall(r'^\| ---',raw,re.M))}
        continue
    if name == 'WORKER':
        mermaid=re.search(r'```mermaid\n(.*?)```', clean, re.S)
        if mermaid is None: raise ValueError('expected Mermaid figure missing')
        (WORK/'worker-overview.mermaid').write_text(mermaid[1])
        (WORK/'worker-overview.dot').write_text(DOT)
        subprocess.run(['/opt/homebrew/bin/dot','-Tsvg',str(WORK/'worker-overview.dot'),'-o',str(WORK/'worker-overview.svg')],check=True)
        clean=clean[:mermaid.start()]+'![Capability map](worker-overview.svg)\n'+clean[mermaid.end():]
    body=subprocess.check_output(['/opt/homebrew/bin/pandoc','--from=gfm+raw_html','--to=html5','--wrap=none'],input=clean,text=True)
    # Embed each figure in the one PDF; oversized inventories get their own tall page.
    image_sources=[]
    def replace_image(m):
        file=m[1]; alt=m[2]
        path=(WORK/file) if file=='worker-overview.svg' else ROOT/'docs'/file
        data=path.read_bytes();image_sources.append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest()})
        cls='worker-map' if file=='worker-capabilities.svg' else ('tall' if file=='architecture-documents.svg' else '')
        encoded=base64.b64encode(data).decode()
        return f'<figure class="{cls}"><img src="data:image/svg+xml;base64,{encoded}" alt="{alt}" /></figure>'
    body=re.sub(r'<p><img src="([^"]+)" alt="([^"]*)"\s*/?></p>',replace_image,body)
    if '<img src="' not in body or not image_sources:raise ValueError('figures missing')
    html=f'<!doctype html><html><head><meta charset="UTF-8"><title>{name}</title></head><body>{body}</body></html>'
    (WORK/f'{name}.html').write_text(html)
    rendered=HTML(string=html,base_url=str(ROOT/'docs')).render(stylesheets=[CSS(string=CSS_TEXT)])
    outliers=[]
    for page_no,page in enumerate(rendered.pages,1):
        for box in page._page_box.descendants():
            if box.__class__.__name__=='TextBox' and (box.position_x < -1 or box.position_y < -1 or box.position_x+box.width > page.width+1 or box.position_y+box.height > page.height+1):
                outliers.append({'page':page_no,'text':box.text[:100],'x':box.position_x,'y':box.position_y,'w':box.width,'h':box.height})
    dest=ART/f'{name}.pdf';rendered.write_pdf(dest)
    extracted='\n'.join(p.extract_text() for p in PdfReader(dest).pages)
    (WORK/f'{name}.txt').write_text(extracted)
    parser=Visible();parser.feed(body)
    words=lambda s:Counter(re.findall(r'[A-Za-z0-9_]+',s))
    missing=words(' '.join(parser.data))-words(extracted)
    # Tables repeat headings at page boundaries, so extracted counts may exceed source counts.
    manifest['fidelity'][name]={'pages':len(rendered.pages),'out_of_page_text_boxes':outliers,'missing_visible_tokens':dict(missing),'embedded_figures':image_sources,'headings':len(re.findall(r'<h[1-6][ >]',body)),'tables':body.count('<table>')}
    manifest['artifacts'][dest.name]={'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'format':'self-contained vector PDF','bytes':dest.stat().st_size}
    manifest['conversion'][name]='Pandoc GFM to HTML, all details expanded, invisible comments removed, SVG figures embedded; WORKER Mermaid faithfully rendered through recorded Graphviz translation; WeasyPrint with wide table pages and tall inventory figure pages.'
(WORK/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
for name,v in manifest['fidelity'].items():print(name,json.dumps({k:v[k] for k in v if k!='embedded_figures'}))
