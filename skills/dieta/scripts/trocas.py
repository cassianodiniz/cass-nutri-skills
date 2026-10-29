# -*- coding: utf-8 -*-
"""
Trocas proporcionais (F2): "Arroz ou Mandioca ou Macarrão - 100g ou Batata Doce
- 150g ou Batata Inglesa - 220g".

A proporção é do nutricionista; a skill só multiplica. A planilha calcula só pelo
alimento-base — a linha completa existe no documento. Cada nutricionista tem o
seu arquivo de trocas (ambiente.arquivo_trocas), como o cadastro de alimentos.
"""
import json
import os
import re

import catalogo

FRASE_SUBSTITUICOES = ("Se quiser oferecer substituições ao paciente (por exemplo, arroz "
                       "100 g ou batata doce 150 g), é só me pedir.")
PASSO = 5   # gramas: só a quantidade que a skill calcula é arredondada

_PEDACO = re.compile(
    r"\s*(?P<nome>[^\d]+?)\s*[-–]?\s*(?P<qtd>\d+(?:[.,]\d+)?)\s*"
    r"(?P<unidade>gramas|gr|g|ml|unidades?|un\.?)?\s*(?:\bou\b|$)", re.I)


class ErroTroca(Exception):
    pass


KIT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kit", "trocas.json")


def carregar_kit():
    """As trocas de exemplo do Cassiano, que viram a lista do aluno no primeiro uso."""
    return _ler(KIT)


def ler_troca_ditada(texto, catalogo_alimentos):
    """
    Lê "X - 100g ou Y - 150g ou Z - 220g". O primeiro pedaço é o alimento-base.
    Cada nome vai INTEIRO para catalogo.resolver: nome que não sai exato vira
    pendência — com as opções da tabela — para o nutricionista escolher.
    """
    pedacos, pos = [], 0
    while pos < len(texto) and texto[pos:].strip():
        m = _PEDACO.match(texto, pos)
        if not m or not m.group("nome").strip():
            raise ErroTroca('Não entendi o trecho "%s" da troca; confirme o alimento, a quantidade e a medida.'
                            % texto[pos:].strip())
        pedacos.append(m)
        pos = m.end()
    if pedacos and re.search(r"\bou\s*$", texto, re.I):
        raise ErroTroca("A troca terminou em 'ou'; falta informar a alternativa.")
    if len(pedacos) < 2:
        raise ErroTroca('Não entendi "%s" como troca: preciso de pelo menos dois alimentos, '
                        "cada um com a sua quantidade." % texto)
    itens, pendencias = [], []
    for m in pedacos:
        ditado = m.group("nome").strip(" -–")
        quantidade = float(m.group("qtd").replace(",", "."))
        quantidade = int(quantidade) if quantidade == int(quantidade) else quantidade
        r = catalogo.resolver(ditado, catalogo_alimentos)
        if r.modo == "exato":
            itens.append({"nome": r.alimento.nome_planilha.strip(), "quantidade": quantidade})
            unidade = m.group("unidade")
            modo, aviso = catalogo.conferir_unidade(r.alimento, unidade)
            # A proporção persistida e seu arredondamento são em gramas.
            # Não reutilizar esse contrato para volumes ou contagens.
            if modo != "ok" or catalogo._familia(r.alimento.medida) != "g":
                pendencias.append({"ditado": ditado, "modo": "unidade",
                                   "aviso": aviso or "Esta troca proporcional usa gramas; confirme as quantidades em gramas.",
                                   "opcoes": [], "unidade": unidade})
        else:
            itens.append({"nome": None, "quantidade": quantidade})
            pendencias.append({"ditado": ditado, "modo": r.modo, "aviso": r.aviso,
                               "opcoes": [a.nome for a in r.opcoes]})
    return {"base": itens[0], "equivalentes": itens[1:], "pendencias": pendencias}


def _ler(caminho):
    try:
        return catalogo._ler_json(caminho)
    except ValueError as erro:
        raise ErroTroca("Não consegui ler as trocas cadastradas; o arquivo foi preservado. Verifique a cópia anterior ou o acesso ao arquivo.") from erro


def _gravar(caminho, lista):
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=1)
    os.replace(tmp, caminho)


def salvar_troca(caminho, troca, substituir=False):
    """
    Guarda a troca do alimento-base. Pendência aberta não é gravada. Já existe
    outra troca para o mesmo alimento: recusa mostrando a atual — só substitui
    com `substituir=True`, depois de ele escolher.
    """
    if troca.get("pendencias") or not troca["base"].get("nome") or \
            not all(e.get("nome") for e in troca["equivalentes"]):
        raise ErroTroca("Ainda há alimento a confirmar nesta troca; não gravei.")
    limpa = {"base": troca["base"], "equivalentes": troca["equivalentes"]}
    alvo = catalogo.normalizar(limpa["base"]["nome"])
    atual = troca_para(limpa["base"]["nome"], _ler(caminho))
    if atual and atual != limpa and not substituir:
        raise ErroTroca("Você já tem uma troca para %s: %s. Fico com a nova no lugar dela?"
                        % (atual["base"]["nome"], texto_da_troca(atual)))
    lista = [t for t in _ler(caminho) if catalogo.normalizar(t["base"]["nome"]) != alvo]
    _gravar(caminho, lista + [limpa])
    return limpa


def texto_da_troca(troca):
    """'Arroz ou mandioca ou macarrão - 100 g ou Batata doce - 150 g ou ...'"""
    partes = [troca["base"]] + troca["equivalentes"]
    return " ou ".join("%s - %s g" % (p["nome"], _n(p["quantidade"])) for p in partes)


def listar_trocas(caminho):
    return _ler(caminho)


def remover_troca(caminho, nome_base):
    alvo = catalogo.normalizar(nome_base)
    lista = [t for t in _ler(caminho) if catalogo.normalizar(t["base"]["nome"]) != alvo]
    _gravar(caminho, lista)
    return lista


def troca_para(nome_alimento, trocas):
    alvo = catalogo.normalizar(nome_alimento)
    return next((t for t in trocas if catalogo.normalizar(t["base"]["nome"]) == alvo), None)


def _arredondar(valor):
    return int(PASSO * round(valor / PASSO))


def linha_da_troca(troca, quantidade):
    """
    [(base, quantidade prescrita), (equivalente, quantidade proporcional), ...].
    Prescrita igual à da troca: as quantidades dele, sem conta. Outra quantidade:
    multiplica pela proporção dele e arredonda de 5 em 5 g só o que calculou.
    """
    base = troca["base"]
    saida = [(base["nome"], quantidade)]
    for e in troca["equivalentes"]:
        if float(quantidade) == float(base["quantidade"]):
            q = e["quantidade"]
        else:
            q = _arredondar(e["quantidade"] * float(quantidade) / float(base["quantidade"]))
        saida.append((e["nome"], q))
    return saida


def equivalente_por_carboidrato(pacote, catalogo_alimentos, base, quantidade, alvo):
    """
    SÓ quando o nutricionista pede: quanto de `alvo` tem o mesmo carboidrato que
    `quantidade` de `base`. Devolve a sugestão arredondada e a conta por extenso;
    vale só com o sim dele.
    """
    colunas = catalogo.colunas_da_tabela(pacote)

    def carbo(nome):
        a = next((x for x in catalogo_alimentos
                  if catalogo.normalizar(x.nome) == catalogo.normalizar(nome)), None)
        if a is None:
            raise ErroTroca('Não achei "%s" na tabela.' % nome)
        if a.origem == "usuario":
            v = (a.valores or {}).get("Carbs")
        else:
            v = pacote.numero("Tabela Nutricional", "%s%d" % (colunas["Carbs"], a.linha))
        if (a.medida or "g").strip().lower() not in ("g", ""):
            raise ErroTroca('"%s" está cadastrado em %s, não em gramas; essa conta não vale.'
                            % (a.nome, a.medida))
        return a.nome, v

    nome_base, c_base = carbo(base)
    nome_alvo, c_alvo = carbo(alvo)
    if not c_alvo:
        raise ErroTroca('"%s" não tem carboidrato na tabela; não dá para igualar por ele.' % nome_alvo)
    total = float(quantidade) * c_base
    exata = total / c_alvo
    sugerida = _arredondar(exata)
    conta = ("%s g de %s têm %s g de carboidrato. %s tem %s g por grama, então o mesmo "
             "carboidrato está em %s g — arredondando de 5 em 5, %d g."
             % (_n(quantidade), nome_base, _n(total, 1), nome_alvo, _n(c_alvo, 3),
                _n(exata, 1), sugerida))
    return {"quantidade": sugerida, "exata": exata, "conta": conta}


def _n(v, casas=0):
    return ("%%.%df" % casas % float(v)).replace(".", ",")
