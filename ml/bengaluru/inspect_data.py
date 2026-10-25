from pathlib import Path
from pypdf import PdfReader
import json
P=Path('data/bengaluru')
O=P/'processed'
O.mkdir(exist_ok=True)
for name in ['hces_2023_24_full.pdf','official_economic_survey_2025_26.pdf']:
    out=O/(name.replace('.pdf','_extracted.txt'))
    if out.exists():continue
    r=PdfReader(P/'raw'/name)
    print(name,len(r.pages),flush=True)
    parts=[]
    for i,pg in enumerate(r.pages):
        txt=pg.extract_text()
        parts.append(f'\nPDF_PAGE {i+1}\n'+txt)
        if name.startswith('hces') and ('3.11U' in txt[:300] or ('Karnataka' in txt and ('household size' in txt.lower() or 'sugar' in txt.lower()))):
            print('MATCH',i+1,txt[:250],flush=True)
        if name.startswith('official') and '5.10.2' in txt:print('BLUE',i+1,txt[txt.index('5.10.2'):][:1500],flush=True)
    out.write_text('\n'.join(parts),encoding='utf-8')
