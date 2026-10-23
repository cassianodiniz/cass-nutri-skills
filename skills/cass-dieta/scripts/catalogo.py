# -*- coding: utf-8 -*-
"""
Catálogo de alimentos: resolver o nome ditado, conferir a unidade e cadastrar
alimento novo.

O ponto de maior risco clínico da skill. A regra que governa tudo aqui:
na dúvida, PERGUNTA. Nunca troca um alimento por outro em silêncio.
"""
import difflib
import json
import os
import re
import unicodedata

__all__ = [
    "normalizar", "significativas", "resolver", "candidatos", "pares_acima_de",
    "conferir_unidade", "inferir_origem_proteina", "converter_para_unidade",
    "validar_valores", "campos_vazios", "montar_catalogo",
    "carregar_da_planilha", "carregar_do_usuario", "ultima_linha_com_nome",
    "colunas_da_tabela", "salvar_alimento", "remover_alimento",
    "listar_alimentos", "resumo_do_cadastro", "Alimento", "Resultado",
]

# ---------------------------------------------------------------- vocabulário

PREPOSICOES = {"de", "do", "da", "dos", "das", "com", "sem", "e", "ou",
               "a", "o", "as", "os", "em", "no", "na", "ao", "à"}

# palavras que mudam o alimento — nunca escolher sozinha (R5.3)
PALAVRAS_PERIGOSAS = {
    "integral", "desnatado", "semidesnatado", "light", "zero", "diet",
    "magra", "magro", "gordo", "gorda",
    "cru", "crua", "cozido", "cozida", "assado", "assada", "frito", "frita",
    "grelhado", "grelhada", "refogado", "refogada", "conserva",
    "pele", "casca", "gema", "clara",
    "acucar", "adocado", "salgado", "defumado", "lactose", "gluten",
    "po",            # "Leite em pó" × "Leite"
}

# origem da proteína inferida pelo nome (informação do Cassiano, 26/07)
INDICA_ANIMAL = {
    "leite", "queijo", "iogurte", "requeijao", "coalhada", "ricota", "cottage",
    "manteiga", "nata", "creme", "laticinio",
    "ovo", "ovos", "clara", "gema", "albumina",
    "carne", "boi", "bovina", "frango", "galinha", "peito", "file", "peixe",
    "tilapia", "salmao", "atum", "sardinha", "camarao", "porco", "suina",
    "presunto", "peru", "linguica", "bacon", "patinho", "alcatra", "coxao",
    "whey", "caseina", "caseinato", "colageno", "beef", "gelatina",
}
INDICA_VEGETAL = {
    "arroz", "feijao", "lentilha", "grao", "soja", "ervilha", "milho", "aveia",
    "trigo", "farinha", "pao", "macarrao", "batata", "mandioca", "abobora",
    "castanha", "amendoim", "amendoa", "noz", "nozes", "chia", "linhaca",
    "quinoa", "tapioca", "fruta", "banana", "maca", "laranja", "mamao", "uva",
    "verdura", "legume", "salada", "alface", "tomate", "cenoura", "brocolis",
    "vegetal", "vegana", "vegano",
}

_PLURAL = re.compile(r"(oes|aes|ais|eis|is|ns|es|s)$")


def normalizar(texto):
    if texto is None:
        return ""
    t = unicodedata.normalize("NFD", str(texto).strip().lower().rstrip(".,;:!?"))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return " ".join(t.split())


def _sem_plural(palavra):
    if len(palavra) <= 3:
        return palavra
    return _PLURAL.sub("", palavra) or palavra


def significativas(texto):
    """Palavras que identificam o alimento: sem preposição, sem número, sem plural."""
    out = set()
    for p in normalizar(texto).split():
        if p in PREPOSICOES or p.isdigit():
            continue
        out.add(_sem_plural(p))
    return out


def digitos(texto):
    return re.findall(r"\d+", normalizar(texto))


# ---------------------------------------------------------------- alimento

class Alimento:
    """
    `nome` é o nome limpo — para exibir e comparar.
    `nome_planilha` é o valor EXATO da célula — é ele que vai para a planilha.

    Os dois existem porque a tabela do Cassiano tem alimentos com espaço
    sobrando no nome ("Lentilha ", "Requeijão ", "Muçarela de búfala "). Gravar
    o nome limpo fazia a busca não encontrar, e esses alimentos davam erro na
    dieta inteira — descoberto no teste de carga em 27/07/2026.
    """

    def __init__(self, nome, medida, origem="planilha", linha=None, valores=None,
                 nome_planilha=None):
        self.nome_planilha = nome_planilha if nome_planilha is not None else nome
        self.nome = (nome or "").strip()
        self.medida = (medida or "").strip()
        self.origem = origem            # "planilha" | "usuario"
        self.linha = linha
        self.valores = valores or {}

    @property
    def opcoes(self):
        """Quantas escolhas este item libera ao paciente (nomes com 'ou')."""
        partes = re.split(r"\s+ou\s+", self.nome, flags=re.I)
        return [p.strip() for p in partes] if len(partes) > 1 else []

    def __repr__(self):
        return "<%s [%s] %s>" % (self.nome, self.medida, self.origem)


class Resultado:
    def __init__(self, modo, alimento=None, opcoes=None, digitado=None, aviso=None):
        self.modo = modo                # exato | automatico | perguntar | nao_encontrado
        self.alimento = alimento
        self.opcoes = opcoes or []
        self.digitado = digitado
        self.aviso = aviso

    def __repr__(self):
        return "<%s %s>" % (self.modo, self.alimento)


# ---------------------------------------------------------------- carregar

def carregar_da_planilha(pacote, aba="Tabela Nutricional", max_linha=200):
    """
    Lê os alimentos da planilha. Ignora linhas sem nome.

    Guarda o nome EXATO da célula (`nome_planilha`) além do limpo: a busca da
    planilha é literal, e há alimentos cadastrados com espaço sobrando.
    """
    alimentos = []
    for linha in range(2, max_linha):
        bruto = pacote.texto(aba, "A%d" % linha)
        if not bruto or not bruto.strip():
            continue
        alimentos.append(Alimento(
            bruto.strip(),
            pacote.texto(aba, "B%d" % linha),
            origem="planilha",
            linha=linha,
            nome_planilha=bruto,
        ))
    return alimentos


def carregar_do_usuario(caminho):
    if not caminho or not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)
    return [Alimento(d["nome"], d.get("medida", "g"), origem="usuario",
                     valores=d.get("valores", {})) for d in dados]


def montar_catalogo(pacote, caminho_usuario=None):
    """
    Alimentos do usuário PRIMEIRO: o cadastro dele vence o da planilha (R6.11).
    A revisão sempre mostra a origem, para a escolha nunca ser silenciosa.
    """
    return carregar_do_usuario(caminho_usuario) + carregar_da_planilha(pacote)


def ultima_linha_com_nome(pacote, aba="Tabela Nutricional", max_linha=400):
    """R6.8 — onde inserir alimento novo. Há buracos no meio; vale a ÚLTIMA."""
    ultima = 1
    for linha in range(2, max_linha):
        nome = pacote.texto(aba, "A%d" % linha)
        if nome and nome.strip():
            ultima = linha
    return ultima


# ---------------------------------------------------------------- resolver

def _perigosa(digitado, candidato):
    divergencia = significativas(digitado) ^ significativas(candidato)
    return bool(divergencia & PALAVRAS_PERIGOSAS)


def candidatos(digitado, catalogo):
    """Só entra quem compartilha uma palavra significativa (R5.4)."""
    palavras = significativas(digitado)
    if not palavras:
        return []
    achados = []
    for a in catalogo:
        if palavras & significativas(a.nome):
            r = difflib.SequenceMatcher(None, normalizar(digitado),
                                        normalizar(a.nome)).ratio()
            achados.append((r, a))
    achados.sort(key=lambda t: -t[0])
    return achados


def resolver(digitado, catalogo):
    """A escada de 4 degraus. Na dúvida, pergunta."""
    if not digitado or not digitado.strip():
        return Resultado("nao_encontrado", digitado=digitado)

    alvo = normalizar(digitado)

    # Degrau 1 — diferença que não muda nada (caixa, acento, espaço, pontuação)
    for a in catalogo:
        if normalizar(a.nome) == alvo:
            aviso = None
            if a.nome != digitado.strip():
                aviso = "usei %r" % a.nome
            if a.origem == "usuario":
                aviso = ((aviso + "; ") if aviso else "") + "do seu cadastro"
            return Resultado("exato", alimento=a, digitado=digitado, aviso=aviso)

    if re.search(r"\s+ou\s+", digitado, flags=re.I):
        return _resolver_com_ou(digitado, catalogo)

    achados = candidatos(digitado, catalogo)
    if not achados:
        return Resultado("nao_encontrado", digitado=digitado,
                         opcoes=[a for _, a in _busca_ampla(digitado, catalogo)])

    melhor_r, melhor_a = achados[0]

    # Degrau 2 e 3 — só decide sozinha em condição estreita
    bloqueado = (_perigosa(digitado, melhor_a.nome)
                 or digitos(digitado) != digitos(melhor_a.nome))   # R5.10
    empatado = len(achados) > 1 and abs(achados[1][0] - melhor_r) < 1e-9

    if melhor_r >= 0.90 and not bloqueado and not empatado:
        return Resultado("automatico", alimento=melhor_a, digitado=digitado)

    # Havendo candidato, SEMPRE pergunta — nunca diz "não encontrei".
    # A semelhança de letras serve para ordenar e para liberar o automático,
    # não para descartar: "macarrão" x "Arroz ou mandioca ou macarrão" pontua
    # baixo porque os nomes têm tamanhos muito diferentes, e "ovos" x "Ovo
    # inteiro" idem. Dizer "não achei" nesses casos empurra o nutricionista a
    # cadastrar um alimento duplicado — o problema que a skill existe para evitar.
    return Resultado("perguntar", opcoes=[a for _, a in achados[:3]],
                     digitado=digitado)


def _partes(texto):
    return [normalizar(p) for p in re.split(r"\s+ou\s+", texto, flags=re.I) if p.strip()]


def _resolver_com_ou(digitado, catalogo):
    """
    E1 — a linha com "ou" é resolvida INTEIRA aqui, nunca separada antes.

    Mesma lista de um item agrupado, em qualquer ordem: é ele. Parte da lista:
    pergunta, nomeando o que o item agrupado liberaria a mais — liberar um
    alimento que não foi dito é decisão clínica do nutricionista. "ou" que não
    existe como item: pergunta se são alimentos separados.
    """
    ditas = _partes(digitado)
    conjunto = set(ditas)
    contem = []
    for a in catalogo:
        membros = set(_partes(a.nome)) if a.opcoes else set()
        if membros and membros == conjunto:
            return Resultado("exato", alimento=a, digitado=digitado,
                             aviso="usei %r (mesma lista, em outra ordem)" % a.nome)
        if membros and conjunto < membros:
            contem.append(a)
    avulsos = []
    for parte in ditas:
        r = resolver(parte, catalogo)
        if r.alimento:
            avulsos.append(r.alimento)
        else:
            avulsos.extend(r.opcoes[:1])
    if contem:
        a = contem[0]
        extras = [p for p in a.opcoes if normalizar(p) not in conjunto]
        return Resultado(
            "perguntar", opcoes=contem + avulsos, digitado=digitado,
            aviso='o item da tabela "%s" também libera %s, que não foi dito. Usar o item '
                  "agrupado mesmo assim, ou prescrever os alimentos separados?"
                  % (a.nome, " e ".join(extras)))
    return Resultado(
        "perguntar", opcoes=avulsos, digitado=digitado,
        aviso="não existe na tabela um item com %s juntos. São alimentos separados, "
              "cada um com sua quantidade?" % " e ".join(ditas))


def fonte_dos_valores(pacote, alimento, catalogo, aba="Tabela Nutricional"):
    """
    De qual alimento são os valores de um item agrupado com "ou".

    Na tabela, cada agrupado copia os valores de UM dos seus membros — e nem
    sempre do primeiro ("Abacaxi ou Mamão ou…" usa o Mamão). Devolve o nome do
    membro avulso com valores idênticos, ou None se nenhum bate.
    """
    if not alimento.opcoes or not alimento.linha:
        return None
    colunas = colunas_da_tabela(pacote)
    numericas = [c for t, c in colunas.items() if t not in ("Nome", "Medida")]

    def valores(linha):
        return [pacote.numero(aba, "%s%d" % (c, linha)) for c in numericas]

    do_agrupado = valores(alimento.linha)
    membros = {normalizar(p) for p in alimento.opcoes}
    for a in catalogo:
        if a.linha and a is not alimento and normalizar(a.nome) in membros:
            if valores(a.linha) == do_agrupado:
                return a.nome
    return None


def _busca_ampla(digitado, catalogo, limite=3):
    """Antes de oferecer cadastro, procura por palavra contida (R5.8)."""
    alvo = normalizar(digitado)
    achados = []
    for a in catalogo:
        n = normalizar(a.nome)
        if alvo and (alvo in n or n in alvo):
            achados.append((1.0, a))
    return achados[:limite]


def pares_acima_de(catalogo, limiar=0.90):
    """
    R6.9 — pares que a skill trocaria sozinha. Roda após cada cadastro.
    Baseline na tabela do Cassiano em 26/07/2026: nenhum.
    """
    perigosos = []
    for i in range(len(catalogo)):
        for j in range(i + 1, len(catalogo)):
            a, b = catalogo[i], catalogo[j]
            if not (significativas(a.nome) & significativas(b.nome)):
                continue
            if _perigosa(a.nome, b.nome) or digitos(a.nome) != digitos(b.nome):
                continue
            r = difflib.SequenceMatcher(None, normalizar(a.nome),
                                        normalizar(b.nome)).ratio()
            if r >= limiar:
                perigosos.append((round(r, 3), a.nome, b.nome))
    return perigosos


# ---------------------------------------------------------------- unidades

EQUIVALENTES = {
    "g": {"g", "grama", "gramas", "gr"},
    "ml": {"ml", "mililitro", "mililitros"},
    "un.": {"un", "un.", "unidade", "unidades", "uni"},
}
CASEIRAS = {"colher", "colheres", "xicara", "xicaras", "concha", "conchas",
            "fatia", "fatias", "copo", "copos", "punhado", "pitada",
            "meio", "meia", "vontade", "gosto", "pouco", "pouca"}


LIVRES = {"a vontade", "a gosto", "1x"}      # medidas sem quantidade fixa


def _familia(unidade):
    """
    Reduz a medida à sua família. O sufixo entre parênteses é anotação do
    nutricionista, não unidade: "g (ou mais)" é grama. Sem isto, "Verduras e
    legumes" era recusado da dieta e o item sumia do documento.
    """
    u = normalizar(unidade)
    u = re.sub(r"\(.*?\)", "", u).strip()      # "g (ou mais)" -> "g"
    if u in LIVRES:
        return "livre"
    for chave, formas in EQUIVALENTES.items():
        if u in formas:
            return chave
    return u or None


def conferir_unidade(alimento, unidade_dita):
    """
    R4.2 — a quantidade é um multiplicador cego: se o alimento está cadastrado
    por unidade e o nutricionista fala em gramas, a planilha calcula 100 ovos
    sem reclamar. Aqui a gente para e pergunta. NUNCA converte.
    """
    cadastrada = _familia(alimento.medida)
    dita = _familia(unidade_dita)

    # 1. alimento sem medida fixa ("à vontade", "a gosto"): nada a conferir
    if cadastrada == "livre":
        return ("ok", None)

    # 2. a unidade dita É a cadastrada -> segue, mesmo sendo caseira.
    #    Esta comparação vem ANTES da checagem de medida caseira: "Presunto"
    #    está cadastrado em "fatia", então dizer "fatia" está correto e não há
    #    o que perguntar.
    if dita is not None and cadastrada is not None and dita == cadastrada:
        return ("ok", None)

    # 3. medida caseira que NÃO é a cadastrada: pergunta os gramas, nunca converte
    if dita and normalizar(_sem_parenteses(unidade_dita)) in CASEIRAS:
        return ("caseira",
                'Você disse "%s", mas "%s" está cadastrado em "%s". Quantos '
                "gramas você considera para isso?"
                % (unidade_dita, alimento.nome, alimento.medida))

    # 4. nutricionista não disse a unidade
    if dita is None:
        if cadastrada in ("g", None):
            return ("ok", None)
        return ("perguntar",
                '"%s" está cadastrado em "%s". A quantidade que você disse é '
                "nessa medida?" % (alimento.nome, alimento.medida))

    # 5. unidades diferentes
    if cadastrada and dita != cadastrada:
        return ("perguntar",
                '"%s" está cadastrado por "%s", e você falou em "%s". '
                "Não vou converter por conta própria — me diga a quantidade na "
                "medida cadastrada." % (alimento.nome, alimento.medida, unidade_dita))

    return ("ok", None)


def _sem_parenteses(texto):
    return re.sub(r"\(.*?\)", "", str(texto or "")).strip()


# ---------------------------------------------------------------- cadastro

def inferir_origem_proteina(nome):
    """
    Laticínio, ovo, carne, peixe e suplementos proteicos são animais
    (whey, albumina, caseína, beef protein, colágeno). Informação do Cassiano.
    Devolve ("animal"|"vegetal"|None, motivo).
    """
    palavras = significativas(nome)
    animal = palavras & INDICA_ANIMAL
    vegetal = palavras & INDICA_VEGETAL
    if animal and not vegetal:
        return "animal", "por causa de '%s'" % sorted(animal)[0]
    if vegetal and not animal:
        return "vegetal", "por causa de '%s'" % sorted(vegetal)[0]
    return None, None


# macronutrientes: em 1 grama de alimento não cabe mais de 1 grama de nada.
# Os nomes são os REAIS das colunas da planilha ("Ptn (A)", "Carbs", "Fat"),
# normalizados — com nomes genéricos a validação nunca disparava.
CHAVES_MACRO = {
    "ptn a", "ptn v", "ptn", "proteina", "carbs", "carboidrato",
    "fat", "gordura", "sat", "poli", "mono", "fibra",
}
LIMITE_POR_GRAMA = 1.0


def _chave_macro(nome):
    limpo = normalizar(re.sub(r"[()]", " ", str(nome)))
    return limpo in CHAVES_MACRO


def converter_para_unidade(valores, base):
    """R6.3 — divide os valores do rótulo pela base declarada."""
    if not base or base <= 0:
        raise ValueError("base inválida")
    return {k: (v / base if isinstance(v, (int, float)) else v)
            for k, v in valores.items()}


def validar_valores(valores, medida="g"):
    """R6.13 — recusa o implausível antes de virar dieta."""
    problemas = []
    por_grama = normalizar(_sem_parenteses(medida)) in ("g", "")
    soma_macro = 0.0
    for chave, valor in valores.items():
        if not isinstance(valor, (int, float)):
            continue
        if valor < 0:
            problemas.append("%s está negativo (%s)" % (chave, valor))
            continue
        if por_grama and _chave_macro(chave):
            soma_macro += valor
            if valor > LIMITE_POR_GRAMA:
                problemas.append(
                    "%s deu %.2f g por grama de alimento — impossível. "
                    "Confira a base do rótulo." % (chave, valor))
    if por_grama and soma_macro > 1.05:      # folga para arredondamento
        problemas.append(
            "os nutrientes somam %.2f g por grama de alimento — mais do que o "
            "próprio alimento pesa. A base do rótulo provavelmente está errada."
            % soma_macro)
    return problemas


def campos_vazios(valores, esperados):
    """R6.6 — o que ficará valendo ZERO nas dietas."""
    return [c for c in esperados
            if valores.get(c) in (None, "") or valores.get(c) == 0]


def colunas_da_tabela(pacote, aba="Tabela Nutricional", max_col=32):
    """Cabeçalho da Tabela Nutricional: nome da coluna -> letra."""
    import string
    colunas = {}
    for i in range(1, max_col + 1):
        letra = _letra(i)
        titulo = pacote.texto(aba, "%s1" % letra)
        if titulo and titulo.strip():
            colunas[titulo.strip()] = letra
    return colunas



# Nome como aparece na tabela "Outros dados" (o que planilha.extrair() devolve em
# dados["micros"]) -> nome real da coluna na Tabela Nutricional. Divergem pra quase
# toda vitamina. SEM este mapa, planilha.cobertura_micronutrientes() procura a
# coluna errada, não acha em nenhum alimento e conclui "ninguém tem esse valor"
# mesmo quando têm — bug real, achado 04/08/2026 num atendimento de verdade (o
# documento da paciente saiu com "—" em vitaminas com total calculado > 0).
MAPA_MICRO_COLUNA = {
    "Fibra Alimentar": "Fibra",
    "Vitamina A": "Vit A (RAE)",
    "Vitamina B1": "Vit B1",
    "Vitamina B2": "Vit B2",
    "Vitamina B3": "Vit B3",
    "Vitamina B6": "Vit B6",
    "Vitamina C": "Vit C",
    "Vitamina D": "Vit D",
    "Vitamina E": "Vit E",
    "Vitamina B9 (folato)": "Folato (B9)",
}


def valores_por_alimento(pacote_mestre, nomes_alimentos, nomes_micro,
                         aba="Tabela Nutricional"):
    """
    R9.15 — monta o `catalogo_por_nome` que planilha.cobertura_micronutrientes()
    espera: para cada alimento da dieta, os valores brutos de cada micronutriente,
    lidos da Tabela Nutricional pelo nome REAL da coluna (traduzido via
    MAPA_MICRO_COLUNA quando o nome de exibição diverge — ver comentário acima).

    Sem esta função, cada chamador tinha que reinventar essa tradução — e nenhum
    lugar do código acertava (nem os testes, nem o script de referência de
    atendimento completo).
    """
    colunas = colunas_da_tabela(pacote_mestre, aba)
    col_nome = colunas.get("Nome", "A")
    alvo = set(nomes_alimentos)
    saida = {}
    for linha in range(2, ultima_linha_com_nome(pacote_mestre, aba) + 1):
        nome = pacote_mestre.texto(aba, "%s%d" % (col_nome, linha))
        if not nome or nome.strip() not in alvo:
            continue
        nome = nome.strip()
        valores = {}
        for micro in nomes_micro:
            col = colunas.get(MAPA_MICRO_COLUNA.get(micro, micro))
            if col:
                valores[micro] = pacote_mestre.numero(aba, "%s%d" % (col, linha))
        saida[nome] = valores
    return saida


def _letra(indice):
    letra = ""
    while indice > 0:
        indice, resto = divmod(indice - 1, 26)
        letra = chr(65 + resto) + letra
    return letra


# ---------------------------------------------------------------- persistência

def salvar_alimento(caminho, alimento):
    """
    R6.7 — grava no arquivo do PRÓPRIO nutricionista, nunca na planilha mestre.
    Assim a planilha segue intacta e uma versão nova dela não apaga o que ele
    cadastrou. `alimento` = {nome, medida, valores:{coluna: numero}}.
    """
    if not str(alimento.get("nome", "")).strip():
        raise ValueError("alimento sem nome")
    lista = _ler_json(caminho)
    alvo = normalizar(alimento["nome"])
    for i, a in enumerate(lista):
        if normalizar(a.get("nome")) == alvo:
            lista[i] = alimento
            break
    else:
        lista.append(alimento)
    _escrever_json(caminho, lista)
    return alimento


def remover_alimento(caminho, nome):
    """R6.10 — poder apagar o que foi cadastrado errado."""
    alvo = normalizar(nome)
    lista = [a for a in _ler_json(caminho) if normalizar(a.get("nome")) != alvo]
    _escrever_json(caminho, lista)
    return lista


def listar_alimentos(caminho):
    return _ler_json(caminho)


# ---------------------------------------------------------------- refeições modelo

def salvar_refeicao(caminho, modelo):
    """
    Uma combinação de alimentos que o nutricionista repete muito.

    `modelo` = {nome, alimentos: [{nome, nome_planilha, quantidade?}, ...]}.

    Guarda `nome_planilha` — o valor EXATO da célula — e não o nome digitado.
    Três alimentos da tabela estão cadastrados com espaço no fim ("Lentilha ",
    "Requeijão ", "Muçarela de búfala ") e a busca da planilha é literal: um
    modelo com o nome limpo faria a refeição inteira dar erro no dia em que
    fosse usado (bug nº 15, 27/07).

    Quantidade é OPCIONAL e é sugestão dele, nunca prescrição: o modelo existe
    para poupar digitação, não para decidir dose (P5).
    """
    if not str(modelo.get("nome", "")).strip():
        raise ValueError("refeição modelo sem nome")
    if not modelo.get("alimentos"):
        raise ValueError("refeição modelo sem alimentos")
    lista = _ler_json(caminho)
    alvo = normalizar(modelo["nome"])
    for i, m in enumerate(lista):
        if normalizar(m.get("nome")) == alvo:
            lista[i] = modelo
            break
    else:
        lista.append(modelo)
    _escrever_json(caminho, lista)
    return modelo


def remover_refeicao(caminho, nome):
    alvo = normalizar(nome)
    lista = [m for m in _ler_json(caminho) if normalizar(m.get("nome")) != alvo]
    _escrever_json(caminho, lista)
    return lista


def listar_refeicoes(caminho):
    return _ler_json(caminho)


def refeicao_do_prato(nome, refeicoes, itens):
    """
    Monta um modelo a partir de uma refeição que ele acabou de montar.

    É o caminho natural — ninguém senta para cadastrar modelo do zero; ele monta
    a dieta, gosta do café da manhã e quer repetir. `itens` é a lista de
    (alimento, quantidade) já resolvida contra o catálogo, então o nome exato da
    planilha vem de graça.
    """
    return {
        "nome": str(nome).strip(),
        "alimentos": [{
            "nome": getattr(a, "nome", None) or str(a),
            "nome_planilha": getattr(a, "nome_planilha", None) or str(a),
            "quantidade": q,
        } for a, q in itens],
    }


def conferir_refeicao(modelo, catalogo):
    """
    Os alimentos deste modelo ainda existem? Devolve os que sumiram.

    O nutricionista pode ter apagado ou renomeado um alimento do cadastro dele
    depois de criar o modelo. Usar sem conferir faria a refeição inteira dar
    erro no cálculo; conferir antes permite dizer QUAL item saiu e seguir com o
    resto.
    """
    presentes = {normalizar(a.nome_planilha if hasattr(a, "nome_planilha") else a)
                 for a in catalogo}
    presentes |= {normalizar(getattr(a, "nome", "")) for a in catalogo}
    return [item.get("nome_planilha") or item.get("nome")
            for item in modelo.get("alimentos", [])
            if normalizar(item.get("nome_planilha") or item.get("nome"))
            not in presentes]


def _ler_json(caminho):
    if not caminho:
        return []
    try:
        with open(caminho, encoding="utf-8") as f:
            dados = json.load(f)
    except FileNotFoundError:
        return []
    except (ValueError, OSError) as erro:
        raise ValueError("Não consegui ler o cadastro; o arquivo foi preservado. Verifique a cópia anterior ou o acesso ao arquivo.") from erro
    if not isinstance(dados, list) or not all(isinstance(item, dict) for item in dados):
        raise ValueError("O cadastro tem um formato inválido; o arquivo foi preservado. Verifique a cópia anterior.")
    return dados


def _escrever_json(caminho, lista):
    pasta = os.path.dirname(caminho)
    if pasta and not os.path.isdir(pasta):
        os.makedirs(pasta, exist_ok=True)
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=1)
    os.replace(tmp, caminho)


def resumo_do_cadastro(alimento):
    """R6.10 — o que mostrar ao nutricionista logo depois de gravar."""
    medida = alimento.get("medida") or "g"
    linhas = ["1 %s de %s:" % (medida, alimento["nome"])]
    for chave, valor in sorted(alimento.get("valores", {}).items()):
        if isinstance(valor, (int, float)) and valor:
            linhas.append("  %s: %s" % (chave, ("%.6f" % valor).rstrip("0").rstrip(".")))
    return "\n".join(linhas)
