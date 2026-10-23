import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/cass-dieta/scripts'))
import restricoes
from catalogo import Alimento


def registro(nome='Alimento teste', criterio='fodmap', quantidade=30,
             resultado='compativel', unidade='g'):
    return dict(alimento=nome, criterio=criterio, quantidade=quantidade,
                unidade=unidade, resultado=resultado,
                fonte=dict(referencia='https://example.org/ensaio-ficticio',
                           consultado_em='2026-10-23', trecho='Dado sintético de teste.'))


class Filtros(unittest.TestCase):
    def avaliar(self, registros, quantidade=30, criterios=('fodmap',), nome='Alimento teste', unidade='g'):
        return restricoes.avaliar(nome, quantidade, unidade, criterios, registros)

    def test_compativel_exato_com_fonte(self):
        r = self.avaliar([registro()])
        self.assertEqual(r['status'], 'compativel')
        self.assertEqual(len(r['evidencias']), 1)

    def test_incompativel_nao_some(self):
        self.assertEqual(self.avaliar([registro(resultado='incompativel')])['status'], 'incompativel')

    def test_ausencia_nao_libera(self):
        self.assertEqual(self.avaliar([])['status'], 'verificar')

    def test_nao_extrapola_porcao_nem_unidade(self):
        for q, u in [(60, 'g'), (15, 'g'), (30, 'ml')]:
            self.assertEqual(self.avaliar([registro()], quantidade=q, unidade=u)['status'], 'verificar')

    def test_nao_transfere_para_variante(self):
        self.assertEqual(self.avaliar([registro()], nome='Alimento teste sem lactose')['status'], 'verificar')

    def test_fonte_incompleta_nao_libera(self):
        for campo in ['referencia', 'consultado_em', 'trecho']:
            r = registro(); del r['fonte'][campo]
            self.assertEqual(self.avaliar([r])['status'], 'verificar')

    def test_criterios_sao_intersecao(self):
        self.assertEqual(self.avaliar([registro()], criterios=('fodmap', 'lactose'))['status'], 'verificar')
        self.assertEqual(self.avaliar([registro(), registro(criterio='lactose')], criterios=('fodmap', 'lactose'))['status'], 'compativel')
        self.assertEqual(self.avaliar([registro(), registro(criterio='lactose', resultado='incompativel')], criterios=('fodmap', 'lactose'))['status'], 'incompativel')

    def test_fontes_divergentes_nao_escolhe_sozinha(self):
        self.assertEqual(self.avaliar([registro(), registro(resultado='incompativel')])['status'], 'verificar')

    def test_ou_exige_todos_membros(self):
        self.assertEqual(self.avaliar([registro()], nome='Alimento teste ou Outro teste')['status'], 'verificar')
        self.assertEqual(self.avaliar([registro(), registro(nome='Outro teste')], nome='Alimento teste ou Outro teste')['status'], 'compativel')

    def test_entrada_invalida(self):
        for q in [0, -1, float('nan'), float('inf'), True, '30']:
            with self.assertRaises(ValueError): self.avaliar([registro()], quantidade=q)
        with self.assertRaises(ValueError): self.avaliar([registro()], criterios=())

    def test_filtra_sem_mutar_catalogo(self):
        a = Alimento('Alimento teste', 'g'); b = Alimento('Outro teste', 'g')
        r = restricoes.filtrar([a, b], 30, 'g', ['fodmap'], [registro()])
        self.assertEqual([x['alimento'] for x in r['compativeis']], [a.nome])
        self.assertEqual([x['alimento'] for x in r['verificar']], [b.nome])
        self.assertEqual(a.nome, 'Alimento teste')


if __name__ == '__main__': unittest.main()
