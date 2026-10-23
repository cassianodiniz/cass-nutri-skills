from pathlib import Path
import ast, hashlib, json, re
r=Path(__file__).resolve().parents[1]
a=json.loads((r/'plugin.json').read_text());b=json.loads((r/'.codex-plugin/plugin.json').read_text())
assert a['name']==b['name']=='cass-nutri-skills' and a['version']==b['version']
assert a['extensions']['com.openai']['interface']==b['interface']
assert len(b['interface']['shortDescription'])<=30
skills=list((r/'skills').iterdir());assert len(skills)==1 and skills[0].name=='cass-dieta'
s=skills[0];assert (s/'SKILL.md').read_text().startswith('---\nname: cass-dieta\n')
for p in s.rglob('*'):
 if not p.is_file() or '__pycache__' in p.parts:continue
 assert not p.is_symlink()
 if p.suffix=='.py':ast.parse(p.read_text())
 if p.suffix=='.md':
  for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if ':' not in link and not link.startswith('#'):assert (p.parent/link.split('#')[0]).exists(),(p,link)
assert hashlib.sha256((s/'planilha/Planilha de Dieta.xlsm').read_bytes()).hexdigest()==(s/'planilha/HASH.txt').read_text().strip()
print('Pacote Nutri válido: uma skill, manifestos, links, Python e planilha conferidos.')
