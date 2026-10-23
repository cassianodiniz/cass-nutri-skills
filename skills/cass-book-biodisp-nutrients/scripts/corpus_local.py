"""Instala e confere o corpus privado, sem o copiar para o plugin."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import stat
import tempfile
import zipfile

NAME='cass-book-biodisp-nutrients'
PLUGIN=Path(__file__).resolve().parents[3]

def externo(value):
    p=Path(value).expanduser()
    if not p.is_absolute():raise ValueError('Use uma pasta absoluta para o corpus privado.')
    p=p.resolve()
    for base in [PLUGIN,Path.home()/'.codex/plugins',Path.home()/'.codex/.tmp',Path.home()/'.agents/skills']:
        base=base.resolve()
        if p==base or base in p.parents:raise ValueError('O corpus precisa ficar fora do plugin e do cache de skills.')
    return p

def casa():
    return externo(os.environ.get('CASS_BIODISP_HOME',str(Path.home()/'.cass-book-biodisp-nutrients')))

def relativo(value):
    p=PurePosixPath(value.removeprefix('./'))
    if p.is_absolute() or '..' in p.parts or '\\' in value or not p.parts:raise ValueError('Caminho inválido no pacote.')
    return p

def conferir(root):
    root=externo(str(root))
    if not root.is_dir():raise ValueError('Corpus local ainda não preparado. Informe o pacote .skill de sua cópia autorizada.')
    manifest=root/'INTEGRITY-SHA256.txt'
    expected=set()
    for line in manifest.read_text(encoding='utf-8').splitlines():
        digest,name=line.split(None,1);p=relativo(name.lstrip('*'));file=root.joinpath(*p.parts)
        if file.is_symlink() or not file.is_file() or root not in file.resolve().parents:raise ValueError('Arquivo ausente ou redirecionado no corpus: '+str(p))
        if hashlib.sha256(file.read_bytes()).hexdigest()!=digest:raise ValueError('A integridade do corpus divergiu em '+str(p))
        expected.add(p.as_posix())
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    if actual!=expected|{'INTEGRITY-SHA256.txt'}:raise ValueError('O corpus contém arquivos ausentes ou não declarados no manifesto.')
    for folder in ['references/pages','references/chapters','chapters','facts']:
        if not (root/folder).is_dir():raise ValueError('Estrutura incompleta: '+folder)
    required=['SKILL.md','references/PROVENANCE.md','references/INDEX.md','references/search/topic-aliases.json','scripts/search_book.py','scripts/check_answer_provenance.py']
    for name in required:
        if not (root/name).is_file():raise ValueError('Arquivo obrigatório ausente no corpus: '+name)
    meta=json.loads((root/'metadata/extraction.json').read_text(encoding='utf-8'))
    if meta.get('skill_name')!=NAME:raise ValueError('O pacote não corresponde ao corpus de Biodisponibilidade de Nutrientes.')
    pages=list((root/'references/pages').glob('page-*.md'))
    chapters=list((root/'references/chapters').glob('ch[0-9][0-9]*-source.md'))
    if type(meta.get('physical_pages')) is not int or meta['physical_pages']<1 or len(pages)!=meta['physical_pages']:
        raise ValueError('A quantidade de páginas não corresponde à extração.')
    if type(meta.get('chapters')) is not int or meta['chapters']<1 or len(chapters)!=meta['chapters']:
        raise ValueError('A quantidade de capítulos não corresponde à extração.')
    if meta.get('release_allowed') is not True:raise ValueError('A revisão desta extração ainda não foi liberada.')
    db=root/'references/search/book-search.sqlite3'
    with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as cx:
        if cx.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('O índice local não passou na conferência.')
    return {'corpus':str(root),'instrucoes':str(root/'SKILL.md'),'paginas':meta.get('physical_pages'),'capitulos':meta.get('chapters'),'arquivos':len(actual),'release_allowed':True,'sqlite':'ok'}

def instalar(archive):
    base=casa();target=base/'corpus'
    if target.exists():
        # Não substituir corpus anterior nem índices locais.
        raise ValueError('Já existe um corpus neste destino. Ele foi preservado; use verificar ou escolha outra CASS_BIODISP_HOME.')
    base.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.preparar-',dir=base) as tmp:
        extracted=Path(tmp)/NAME;extracted.mkdir()
        with zipfile.ZipFile(archive) as z:
            if sum(i.file_size for i in z.infolist())>256*1024*1024:raise ValueError('Pacote maior que o limite de conferência.')
            seen=set()
            for item in z.infolist():
                p=relativo(item.filename)
                if p.parts[0]!=NAME or item.filename in seen or stat.S_ISLNK(item.external_attr>>16):raise ValueError('Raiz, arquivo duplicado ou link inválido no pacote.')
                seen.add(item.filename)
                if len(p.parts)==1:
                    if not item.is_dir():raise ValueError('Raiz do pacote inválida.')
                    continue
                file=extracted.joinpath(*p.parts[1:])
                if item.is_dir():file.mkdir(parents=True,exist_ok=True);continue
                file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(z.read(item))
        conferir(extracted)
        if target.exists():raise ValueError('Outro corpus apareceu no destino; nada foi substituído.')
        extracted.rename(target)
    return conferir(target)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='acao',required=True)
    setup=sub.add_parser('instalar');setup.add_argument('--pacote',required=True)
    sub.add_parser('verificar');sub.add_parser('localizar')
    a=p.parse_args()
    try:
        result=instalar(Path(a.pacote).expanduser()) if a.acao=='instalar' else conferir(casa()/'corpus')
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,OSError,zipfile.BadZipFile,sqlite3.Error) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':main()
