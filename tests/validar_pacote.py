from pathlib import Path
import ast, hashlib, json, re
r=Path(__file__).resolve().parents[1]
a=json.loads((r/'plugin.json').read_text());b=json.loads((r/'.codex-plugin/plugin.json').read_text())
assert a['name']==b['name']=='cass-nutri-skills' and a['version']==b['version']
assert a['extensions']['com.openai']['interface']==b['interface']
assert len(b['interface']['shortDescription'])<=30
skills=list((r/'skills').iterdir());assert {p.name for p in skills}=={'dieta','biodisp-nutrients','nutricao-canetas','exames-laboratoriais'}
for p in skills:assert (p/'SKILL.md').read_text().startswith('---\nname: '+p.name+'\n')
s=r/'skills/dieta'
for p in s.rglob('*'):
 if not p.is_file() or '__pycache__' in p.parts:continue
 assert not p.is_symlink()
 if p.suffix=='.py':ast.parse(p.read_text())
 if p.suffix=='.md':
  for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if ':' not in link and not link.startswith('#'):assert (p.parent/link.split('#')[0]).exists(),(p,link)
assert hashlib.sha256((s/'planilha/Planilha de Dieta.xlsm').read_bytes()).hexdigest()==(s/'planilha/HASH.txt').read_text().strip()

book=r/'skills/biodisp-nutrients'
assert len(list((book/'references/pages').glob('page-*.md')))==910
canetas=r/'skills/nutricao-canetas'
assert len(list((canetas/'references/pages').glob('page-*.md')))==51
assert len(list((canetas/'references/source').glob('*original.pdf')))==3
exames=r/'skills/exames-laboratoriais'
assert len(list((exames/'references/pages').glob('page-*.txt')))==273
assert (exames/'references/source/original.pdf').is_file()
assert len(list((exames/'assets/page-images').glob('*.png')))==11
for name in ['biodisp-nutrients','nutricao-canetas','exames-laboratoriais']:
 for p in (r/'skills'/name).rglob('*.py'):ast.parse(p.read_text())
for line in (book/'INTEGRITY-SHA256.txt').read_text().splitlines():
 digest,name=line.split(None,1)
 assert hashlib.sha256((book/name.strip().removeprefix('./')).read_bytes()).hexdigest()==digest
print('Pacote completo: quatro skills, 1.234 páginas, PDFs disponíveis e integridade conferidos.')
