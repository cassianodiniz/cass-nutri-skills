"""Filtra evidências por alimento/porção, sem inferir composição nem prescrever.

Os registros são conferidos pelo agente nas fontes, conforme a referência da
skill. Este motor verifica correspondência e integridade, não a verdade da fonte.
Não calcula teores de lactose/FODMAPs a partir de macronutrientes.
"""
import json
import math
import re
from pathlib import Path

from catalogo import normalizar


def carregar(caminho):
    """Arquivo ausente = nenhuma evidência. JSON inválido é erro explícito."""
    p = Path(caminho)
    if not p.exists():
        return []
    dados = json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(dados, list):
        raise ValueError('O cadastro de filtros deve ser uma lista de evidências.')
    return dados


def _numero(valor):
    return (isinstance(valor, (int, float)) and not isinstance(valor, bool)
            and math.isfinite(valor) and valor > 0)


def _fonte_valida(registro):
    fonte = registro.get('fonte')
    return (isinstance(fonte, dict) and all(
        isinstance(fonte.get(c), str) and fonte[c].strip()
        for c in ('referencia', 'consultado_em', 'trecho')))


def avaliar(nome, quantidade, unidade, criterios, registros):
    """Compativel/incompativel/verificar no contexto e porção EXATOS da evidência.

    O nome deve identificar marca/preparo/variante quando relevantes. Critérios
    são as chaves da restrição definida pelo profissional (p.ex. 'fodmap',
    'lactose', 'fodmap:frutanos'). Não há equivalência implícita entre chaves.
    """
    if not isinstance(nome, str) or not nome.strip() or not _numero(quantidade):
        raise ValueError('Informe alimento e quantidade numérica positiva.')
    if not isinstance(unidade, str) or not unidade.strip():
        raise ValueError('Informe a unidade da porção, sem conversão automática.')
    if isinstance(criterios, str) or not criterios or any(
            not isinstance(c, str) or not c.strip() for c in criterios):
        raise ValueError('Informe a lista de restrições definidas pelo nutricionista.')
    partes = [p.strip() for p in re.split(r'\s+ou\s+', nome, flags=re.I) if p.strip()]
    detalhes = []
    evidencias = []
    for parte in partes:
        for criterio in dict.fromkeys(criterios):
            achados = [r for r in registros if isinstance(r, dict)
                       and normalizar(r.get('alimento')) == normalizar(parte)
                       and r.get('criterio') == criterio
                       and _numero(r.get('quantidade'))
                       and r['quantidade'] == quantidade
                       and normalizar(r.get('unidade')) == normalizar(unidade)
                       and r.get('resultado') in ('compativel', 'incompativel')
                       and _fonte_valida(r)]
            resultados = {r['resultado'] for r in achados}
            status = next(iter(resultados)) if len(resultados) == 1 else 'verificar'
            motivo = ('Fontes divergentes: conferir com o nutricionista.' if len(resultados) > 1
                      else 'Sem evidência completa para este alimento e esta porção.' if not achados
                      else 'Correspondência exata com a evidência registrada.')
            detalhes.append(dict(alimento=parte, criterio=criterio, status=status, motivo=motivo))
            evidencias.extend(achados)
    estados = {d['status'] for d in detalhes}
    status = ('incompativel' if 'incompativel' in estados else
              'verificar' if 'verificar' in estados else 'compativel')
    return dict(alimento=nome, quantidade=quantidade, unidade=unidade,
                status=status, detalhes=detalhes, evidencias=evidencias)


def filtrar(alimentos, quantidade, unidade, criterios, registros):
    """Separa catálogo na porção pedida, preservando os itens e suas unidades."""
    grupos = dict(compativeis=[], incompativeis=[], verificar=[])
    destino = dict(compativel='compativeis', incompativel='incompativeis', verificar='verificar')
    for alimento in alimentos:
        r = avaliar(alimento.nome, quantidade, unidade, criterios, registros)
        if normalizar(alimento.medida) != normalizar(unidade):
            r['status'] = 'verificar'
            r['detalhes'].append(dict(alimento=alimento.nome, criterio='unidade_catalogo',
                status='verificar', motivo='Unidade diferente da cadastrada; confirmar antes de usar.'))
        grupos[destino[r['status']]].append(r)
    return grupos
