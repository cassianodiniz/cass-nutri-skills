from pathlib import Path
import ast, hashlib, json, re
r=Path(__file__).resolve().parents[1]
a=json.loads((r/'plugin.json').read_text());b=json.loads((r/'.codex-plugin/plugin.json').read_text())
assert a['name']==b['name']=='cass-nutri-skills' and a['version']==b['version']
assert a['extensions']['com.openai']['interface']==b['interface']
assert len(b['interface']['shortDescription'])<=30
skills=list((r/'skills').iterdir());assert {p.name for p in skills}=={'cass-dieta','cass-book-biodisp-nutrients'}
for p in skills:assert (p/'SKILL.md').read_text().startswith('---\nname: '+p.name+'\n')
s=r/'skills/cass-dieta'
for p in s.rglob('*'):
 if not p.is_file() or '__pycache__' in p.parts:continue
 assert not p.is_symlink()
 if p.suffix=='.py':ast.parse(p.read_text())
 if p.suffix=='.md':
  for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if ':' not in link and not link.startswith('#'):assert (p.parent/link.split('#')[0]).exists(),(p,link)
assert hashlib.sha256((s/'planilha/Planilha de Dieta.xlsm').read_bytes()).hexdigest()==(s/'planilha/HASH.txt').read_text().strip()
book=r/'skills/cass-book-biodisp-nutrients'
assert not (book/'references/pages').exists() and not list(book.rglob('*.sqlite3'))
for p in book.rglob('*.py'):ast.parse(p.read_text())
print('Pacote Nutri válido: duas skills, manifestos, Python, planilha e ausência de corpus privado no plugin conferidos.')
