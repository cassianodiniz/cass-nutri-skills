from pathlib import Path
import hashlib
import importlib.util
import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('book_corpus',ROOT/'skills/cass-book-biodisp-nutrients/scripts/corpus_local.py')
book=importlib.util.module_from_spec(spec);spec.loader.exec_module(book)

class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()
        p=patch.dict(os.environ,{'CASS_BIODISP_HOME':str(self.root/'private')});p.start();self.addCleanup(p.stop)
        self.source=self.root/'source';self.source.mkdir()
        for folder in ['references/pages','references/chapters','chapters','facts','metadata','references/search','scripts']:(self.source/folder).mkdir(parents=True,exist_ok=True)
        (self.source/'SKILL.md').write_text('---\nname: fixture\n---\nConteúdo sintético para teste.\n')
        (self.source/'metadata/extraction.json').write_text(json.dumps({'skill_name':book.NAME,'release_allowed':True,'physical_pages':1,'chapters':1}))
        for name,text in [('references/PROVENANCE.md','Contrato sintético'),('references/INDEX.md','Índice sintético'),('references/pages/page-0001.md','Página sintética'),('references/chapters/ch01-source.md','Fonte sintética'),('references/chapters/front-matter-source.md','Introdução sintética'),('references/search/topic-aliases.json','{}'),('scripts/search_book.py','# fixture'),('scripts/check_answer_provenance.py','# fixture')]:
            (self.source/name).write_text(text)
        db=self.source/'references/search/book-search.sqlite3'
        with sqlite3.connect(db) as cx:cx.execute('CREATE TABLE fixture (value TEXT)')
        self.manifest()
    def manifest(self):
        rows=[hashlib.sha256(p.read_bytes()).hexdigest()+'  ./'+p.relative_to(self.source).as_posix() for p in sorted(self.source.rglob('*')) if p.is_file() and p.name!='INTEGRITY-SHA256.txt']
        (self.source/'INTEGRITY-SHA256.txt').write_text('\n'.join(rows)+'\n')
    def archive(self,extra=None):
        p=self.root/'fixture.skill'
        with zipfile.ZipFile(p,'w') as z:
            for file in self.source.rglob('*'):z.write(file,'cass-book-biodisp-nutrients/'+file.relative_to(self.source).as_posix())
            if extra:z.writestr(extra,b'invalido')
        return p
    def test_absent_is_not_claimed_installed(self):
        with self.assertRaises(ValueError):book.conferir(book.casa()/'corpus')
        self.assertFalse(book.casa().exists())
    def test_install_and_verify_external_without_modifying_source(self):
        result=book.instalar(self.archive())
        self.assertEqual(result['sqlite'],'ok');self.assertTrue(result['release_allowed'])
        self.assertEqual(Path(result['corpus']),self.root/'private/corpus')
    def test_existing_is_preserved(self):
        book.instalar(self.archive());target=book.casa()/'corpus/SKILL.md';before=target.read_bytes()
        with self.assertRaises(ValueError):book.instalar(self.archive())
        self.assertEqual(target.read_bytes(),before)
    def test_missing_engine_is_rejected_even_with_valid_manifest(self):
        (self.source/'scripts/search_book.py').unlink();self.manifest()
        with self.assertRaises(ValueError):book.instalar(self.archive())
        self.assertFalse((book.casa()/'corpus').exists())
    def test_missing_instructions_is_rejected_even_with_valid_manifest(self):
        (self.source/'SKILL.md').unlink();self.manifest()
        with self.assertRaises(ValueError):book.instalar(self.archive())
        self.assertFalse((book.casa()/'corpus').exists())
    def test_tampering_is_rejected_before_install(self):
        (self.source/'SKILL.md').write_text('alteração não declarada')
        with self.assertRaises(ValueError):book.instalar(self.archive())
        self.assertFalse((book.casa()/'corpus').exists())
    def test_traversal_is_rejected(self):
        with self.assertRaises(ValueError):book.instalar(self.archive('cass-book-biodisp-nutrients/../../escape'))
        self.assertFalse((self.root/'escape').exists());self.assertFalse((book.casa()/'corpus').exists())
    def test_unreleased_extraction_is_rejected(self):
        (self.source/'metadata/extraction.json').write_text('{"release_allowed":false}');self.manifest()
        with self.assertRaises(ValueError):book.instalar(self.archive())
        self.assertFalse((book.casa()/'corpus').exists())
    def test_plugin_and_alias_destinations_are_rejected(self):
        link=self.root/'alias';link.symlink_to(ROOT,target_is_directory=True)
        for location in [ROOT/'corpus',link/'corpus']:
            with self.subTest(location=location), self.assertRaises(ValueError):book.externo(str(location))
    def test_new_plugin_copy_resolves_same_private_corpus(self):
        book.instalar(self.archive());before=(book.casa()/'corpus/INTEGRITY-SHA256.txt').read_bytes()
        with patch.object(book,'PLUGIN',self.root/'plugin-v2'):
            result=book.conferir(book.casa()/'corpus')
        self.assertEqual(result['sqlite'],'ok');self.assertEqual((book.casa()/'corpus/INTEGRITY-SHA256.txt').read_bytes(),before)

if __name__=='__main__':unittest.main()
