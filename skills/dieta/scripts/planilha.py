# -*- coding: utf-8 -*-
"""
Leitura e escrita da planilha de dietas.

Só biblioteca padrão: um nutricionista leigo não deve precisar instalar nada
além do LibreOffice. Toda escrita é cirúrgica no XML dentro do pacote (P2).
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from html import unescape
from xml.sax.saxutils import escape

import catalogo

# ---------------------------------------------------------------- constantes

ABAS = {                      # nome da aba -> arquivo interno
    "TMB": "xl/worksheets/sheet1.xml",
    "Master": "xl/worksheets/sheet2.xml",
    "Template": "xl/worksheets/sheet3.xml",
    "Cálculo de Dieta": "xl/worksheets/sheet4.xml",
    "Cálculo Alternativo (1)": "xl/worksheets/sheet5.xml",
    "Cálculo Alternativo (2)": "xl/worksheets/sheet6.xml",
    "Cálculo Alternativo (3)": "xl/worksheets/sheet7.xml",
    "Cálculo Alternativo (4)": "xl/worksheets/sheet8.xml",
    "Tabela Nutricional": "xl/worksheets/sheet9.xml",
}
ABAS_CALCULO = ["Cálculo de Dieta"] + ["Cálculo Alternativo (%d)" % i for i in range(1, 5)]
ABA_CONFERENCIA = "Cálculo Alternativo (4)"     # desativada no Master — R7.3

# âncoras: só escreve se o rótulo vizinho for o esperado (R3.7)
ANCORAS_TMB = {
    "C2": ("B2", "Nome"), "C3": ("B3", "Objetivo"), "C6": ("B6", "Peso"),
    "C7": ("B7", "Altura"), "C8": ("B8", "Idade"), "C9": ("B9", "FA"),
    "C10": ("B10", "Sexo"), "C15": ("B15", "% gordura"), "C18": ("B18", "Gestante?"),
}
CAMPOS_TEXTO = {"C2", "C3", "C10", "C18"}       # R3.10 — sem t="str" viram zero

PRIMEIRA_LINHA_BLOCO = 2
LINHAS_POR_BLOCO = 16
ALIMENTOS_POR_REFEICAO = 10                     # o 11º sobrescreveria os totais
MAX_REFEICOES = 12

_CACHE = re.compile(r'(</f>|<f\b[^>]*/>)(<v[^>]*>[^<]*</v>|<v\s*/>)')
_PROIBIDO_INICIO = ("=", "+", "-", "@")


class ErroPlanilha(Exception):
    """Erro com mensagem já escrita para leigo."""


# ---------------------------------------------------------------- utilidades

def sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _linhas_bloco(indice):
    """Devolve (linha do cabeçalho, primeira linha de alimento) do bloco N (0-based)."""
    base = PRIMEIRA_LINHA_BLOCO + indice * LINHAS_POR_BLOCO
    return base, base + 2


def col_linha(ref):
    m = re.match(r"([A-Z]+)(\d+)$", ref)
    return m.group(1), int(m.group(2))


# ---------------------------------------------------------------- leitura

class Pacote:
    """Um .xlsm aberto como pacote zip, com as abas carregadas sob demanda."""

    def __init__(self, caminho):
        self.caminho = caminho
        self._zip = zipfile.ZipFile(caminho)
        self._xml = {}
        self._alterados = set()
        self._shared = None

    # -- shared strings -------------------------------------------------
    @property
    def shared(self):
        if self._shared is None:
            try:
                bruto = self._zip.read("xl/sharedStrings.xml").decode("utf-8")
            except KeyError:
                self._shared = []
            else:
                self._shared = [
                    unescape("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S)))
                    for si in re.findall(r"<si>(.*?)</si>", bruto, re.S)
                ]
        return self._shared

    # -- xml de uma aba -------------------------------------------------
    def xml(self, aba):
        if aba not in self._xml:
            self._xml[aba] = self._zip.read(ABAS[aba]).decode("utf-8")
        return self._xml[aba]

    def _set_xml(self, aba, novo):
        self._xml[aba] = novo
        self._alterados.add(aba)

    # -- leitura de célula ----------------------------------------------
    def celula_bruta(self, aba, ref):
        # [^>]*? NÃO-GULOSO é obrigatório: com [^>]* guloso, uma célula fechada em
        # "/>" fazia o padrão cair no ramo ">...</c>" e engolir a célula seguinte —
        # apagando a fórmula do vizinho ao escrever. Verificado em 26/07/2026.
        m = re.search(r'<c r="%s"(?=[\s/>])[^>]*?(?:/>|>.*?</c>)' % ref,
                      self.xml(aba), re.S)
        return m.group(0) if m else None

    def texto(self, aba, ref):
        """Valor da célula como texto, resolvendo sharedStrings (R3.7)."""
        bruta = self.celula_bruta(aba, ref)
        if not bruta:
            return None
        v = re.search(r"<v[^>]*>(.*?)</v>", bruta, re.S)
        if not v:
            t = re.search(r"<t[^>]*>(.*?)</t>", bruta, re.S)
            return unescape(t.group(1)) if t else None
        valor = unescape(v.group(1))
        if 't="s"' in bruta and valor.isdigit():
            idx = int(valor)
            return self.shared[idx] if idx < len(self.shared) else None
        return valor

    def numero(self, aba, ref):
        v = self.texto(aba, ref)
        if v in (None, ""):
            return None
        try:
            return float(v.replace(",", "."))
        except ValueError:
            return None

    # -- escrita ---------------------------------------------------------
    def escrever(self, aba, ref, valor, tipo="numero"):
        """Escreve uma célula preservando o estilo. Texto vai como t="str" (R3.10)."""
        if valor is None or valor == "":
            return
        texto = str(valor)
        if tipo == "texto" and texto.lstrip().startswith(_PROIBIDO_INICIO):
            raise ErroPlanilha(
                'O texto "%s" não pode ser usado porque começa com um símbolo que a '
                "planilha interpretaria como conta." % texto[:40]
            )
        if tipo == "bool":
            texto = "1" if valor else "0"
        if tipo == "numero":
            texto = str(valor).replace(",", ".")
            try:
                float(texto)
            except ValueError:
                raise ErroPlanilha(
                    'Não consegui entender "%s" como número.' % valor
                )

        x = self.xml(aba)
        bruta = self.celula_bruta(aba, ref)
        estilo = ""
        if bruta:
            m = re.search(r'\bs="(\d+)"', bruta)
            if m:
                estilo = ' s="%s"' % m.group(1)
        conteudo = escape(texto)
        if tipo == "texto":
            nova = '<c r="%s"%s t="str"><v>%s</v></c>' % (ref, estilo, conteudo)
        elif tipo == "bool":
            nova = '<c r="%s"%s t="b"><v>%s</v></c>' % (ref, estilo, "1" if valor else "0")
        else:
            nova = '<c r="%s"%s><v>%s</v></c>' % (ref, estilo, conteudo)

        if bruta:
            x = x.replace(bruta, nova, 1)
        else:
            x = self._inserir(x, ref, nova)
        self._set_xml(aba, x)

    def apagar(self, aba, ref):
        """Esvazia a célula preservando o estilo. Nunca toca em célula com fórmula."""
        bruta = self.celula_bruta(aba, ref)
        if not bruta or "<f" in bruta:
            return False
        m = re.search(r'\bs="(\d+)"', bruta)
        estilo = ' s="%s"' % m.group(1) if m else ""
        self._set_xml(aba, self.xml(aba).replace(
            bruta, '<c r="%s"%s/>' % (ref, estilo), 1))
        return True

    def _inserir(self, x, ref, nova):
        """Insere célula que ainda não existe, na posição correta da linha."""
        col, lin = col_linha(ref)
        mrow = re.search(r'<row[^>]*\br="%d"[^>]*>(.*?)</row>' % lin, x, re.S)
        if not mrow:
            mvazia = re.search(r'<row[^>]*\br="%d"[^>]*/>' % lin, x)
            if not mvazia:
                raise ErroPlanilha(
                    "A linha %d não existe na planilha — o formato mudou." % lin
                )
            aberta = mvazia.group(0)[:-2] + ">"
            return x.replace(mvazia.group(0), aberta + nova + "</row>", 1)

        interno = mrow.group(1)
        pos = len(interno)
        for m in re.finditer(r'<c r="([A-Z]+)%d"' % lin, interno):
            outra = m.group(1)
            if (len(outra), outra) > (len(col), col):
                pos = m.start()
                break
        novo_interno = interno[:pos] + nova + interno[pos:]
        return x.replace(mrow.group(0), mrow.group(0).replace(interno, novo_interno, 1), 1)

    # -- gravação --------------------------------------------------------
    def salvar(self, destino):
        """
        Reempacota copiando todos os membros não alterados byte a byte (P2).

        Fecha o pacote de leitura antes de substituir: no Windows não é possível
        sobrescrever um arquivo que ainda está aberto.
        """
        tmp = destino + ".tmp"
        alterados = {ABAS[a]: self._xml[a] for a in self._alterados}
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in self._zip.infolist():
                dado = alterados.get(item.filename)
                zout.writestr(item, dado.encode("utf-8") if dado is not None
                              else self._zip.read(item.filename))
        self.fechar()
        os.replace(tmp, destino)

    def fechar(self):
        if self._zip is not None:
            self._zip.close()
            self._zip = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.fechar()
        return False


# ---------------------------------------------------------------- cache

def limpar_cache(pacote, abas=None):
    """
    R3.8 — remove o valor em cache de toda fórmula.

    CRÍTICO: sem isto o LibreOffice devolve os valores antigos e a dieta sai
    inteira zerada, com todas as conferências em verde. Verificado em 26/07/2026.
    """
    total = 0
    for aba in (abas or ABAS):
        x = pacote.xml(aba)
        novo, n = _CACHE.subn(r"\1", x)
        if n:
            pacote._set_xml(aba, novo)
            total += n
    return total


# ---------------------------------------------------------------- âncoras

def conferir_ancoras_tmb(pacote):
    """R3.7 — a planilha ainda tem o formato esperado?"""
    for alvo, (ancora, esperado) in ANCORAS_TMB.items():
        achado = (pacote.texto("TMB", ancora) or "").strip()
        if achado != esperado:
            raise ErroPlanilha(
                "A planilha parece ter mudado de formato: eu esperava encontrar "
                '"%s" ao lado do campo, mas encontrei "%s". Não vou escrever nada '
                "para não estragar seu arquivo." % (esperado, achado)
            )


def conferir_ancora_bloco(pacote, aba, indice):
    """O cabeçalho do bloco de refeição está onde deveria?"""
    cab, _ = _linhas_bloco(indice)
    if (pacote.texto(aba, "C%d" % (cab + 1)) or "").strip() != "Alimento":
        raise ErroPlanilha(
            "A refeição %d da aba '%s' não está no formato esperado. "
            "Não vou escrever para não estragar a planilha." % (indice + 1, aba)
        )


def abas_ativas(pacote):
    """R7.6 — quais abas de cálculo estão ligadas no Master."""
    ativas = []
    for i, aba in enumerate(ABAS_CALCULO):
        v = (pacote.texto("Master", "D%d" % (6 + i)) or "").strip().lower()
        if v in ("true", "1", "verdadeiro"):
            ativas.append(aba)
    return ativas or [ABAS_CALCULO[0]]


def ligar_abas(pacote, abas):
    """Liga no Master exatamente estas abas de cálculo e desliga as outras."""
    for i, aba in enumerate(ABAS_CALCULO):
        pacote.escrever("Master", "D%d" % (6 + i), aba in abas, "bool")


# ---------------------------------------------------------------- escrita alto nível

SEXO = {"m": "M", "masc": "M", "masculino": "M", "homem": "M",
        "f": "F", "fem": "F", "feminino": "F", "mulher": "F"}
SIM = {"sim", "s", "x", "true", "verdadeiro", "1"}
NAO = {"não", "nao", "n", "false", "falso", "0"}
# Fora destas faixas o nutricionista confirma — o código nunca corrige sozinho.
FAIXAS = {"peso": (20, 300, "kg"), "altura": (100, 250, "cm"), "idade": (1, 120, "anos"),
          "gordura": (3, 70, "%")}


def _sim_nao(valor):
    if isinstance(valor, bool):
        return valor
    v = str(valor).strip().lower()
    return True if v in SIM else False if v in NAO else None


def _numero(valor):
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return None


def normalizar_ficha(dados):
    """
    B1 — confere a ficha ANTES de tocar na planilha e devolve a versão que ela
    entende. Quem barra formato errado é o código: a planilha testa sexo com
    `="M"` (qualquer outra coisa dá meta 0) e gestante com `<>""` (qualquer texto,
    até "não", vira gestante), e o texto do SKILL.md não segura isso.

    Campo ausente = mantém o que já está na planilha. "não" = apagar (só
    gestante e % de gordura). Recusa com ErroPlanilha listando todos os motivos.
    """
    saida, motivos = dict(dados), []
    if dados.get("sexo") not in (None, ""):
        sexo = SEXO.get(str(dados["sexo"]).strip().lower())
        if not sexo:
            motivos.append('o sexo "%s" não foi entendido — use masculino ou feminino'
                           % dados["sexo"])
        saida["sexo"] = sexo
    for chave, (minimo, maximo, unidade) in FAIXAS.items():
        valor = dados.get(chave)
        if valor in (None, "") or (chave == "gordura" and _sim_nao(valor) is False):
            continue
        n = _numero(valor)
        if n is None:
            motivos.append('não entendi "%s" como número no campo %s' % (valor, chave))
        elif chave == "altura" and 1 <= n <= 2.5:
            motivos.append("a altura %s parece estar em metros — a planilha usa centímetros "
                           "(%s m = %d cm). Confirme o valor em cm" % (valor, valor, round(n * 100)))
        elif not minimo <= n <= maximo:
            motivos.append("%s de %s %s está fora da faixa esperada (%s a %s %s) — confirme"
                           % (chave, valor, unidade, minimo, maximo, unidade))
    if dados.get("gestante") not in (None, ""):
        g = _sim_nao(dados["gestante"])
        if g is None:
            motivos.append('não entendi "%s" para gestante — responda sim ou não'
                           % dados["gestante"])
        saida["gestante"] = g
    if dados.get("gordura") not in (None, "") and _sim_nao(dados["gordura"]) is False:
        saida["gordura"] = False
    if dados.get("formula") not in (None, ""):
        f = _numero(dados["formula"])
        if f is None or f != int(f) or not 1 <= f <= 6:
            motivos.append("a fórmula %s não existe — escolha de 1 a 6" % dados["formula"])
        else:
            saida["formula"] = int(f)
    if motivos:
        raise ErroPlanilha("Não gravei a ficha: " + "; ".join(motivos) + ".")
    return saida


def escrever_paciente(pacote, dados, conferir=True):
    """dados: dict com nome, objetivo, peso, altura, idade, fa, sexo, gordura,
    gestante, formula (1-6) e gcd_manual. Passa antes por normalizar_ficha().
    `conferir=False` só ao copiar a ficha antiga: a conferência do conjunto roda
    depois que as mudanças desta consulta forem aplicadas por cima."""
    conferir_ancoras_tmb(pacote)
    dados = normalizar_ficha(dados)
    mapa = [
        ("C2", "nome"), ("C3", "objetivo"), ("C6", "peso"), ("C7", "altura"),
        ("C8", "idade"), ("C9", "fa"), ("C10", "sexo"), ("C15", "gordura"),
    ]
    for ref, chave in mapa:
        if dados.get(chave) is False:
            pacote.apagar("TMB", ref)
        elif dados.get(chave) not in (None, ""):
            tipo = "texto" if ref in CAMPOS_TEXTO else "numero"
            pacote.escrever("TMB", ref, dados[chave], tipo)
    if dados.get("gestante") is True:
        pacote.escrever("TMB", "C18", "X", "texto")
    elif dados.get("gestante") is False:
        pacote.apagar("TMB", "C18")
    if dados.get("formula"):
        pacote.escrever("TMB", "H23", dados["formula"], "numero")
    if dados.get("gcd_manual"):
        pacote.escrever("TMB", "H18", dados["gcd_manual"], "numero")
    if conferir:
        _conferir_ficha_gravada(pacote)


def _conferir_ficha_gravada(pacote):
    """O que só dá para saber olhando a ficha inteira (a herdada + a nova)."""
    formula = pacote.numero("TMB", "H23")
    motivos = []
    if formula in (4, 5) and pacote.numero("TMB", "C15") is None:
        motivos.append("a fórmula %d precisa do percentual de gordura corporal" % formula)
    if formula == 6 and not pacote.numero("TMB", "H18"):
        motivos.append("a fórmula 6 usa o valor definido por você — falta o total em kcal")
    if (pacote.texto("TMB", "C10") or "").strip() == "M" and pacote.texto("TMB", "C18"):
        motivos.append("gestante só vale para sexo feminino")
    if motivos:
        raise ErroPlanilha("Não dá para calcular ainda: " + "; ".join(motivos) + ".")


def limpar_ficha_paciente(pacote):
    """
    Zera a ficha da TMB — só para PACIENTE NOVO (R2.9).

    escrever_paciente() só grava o que foi informado, e limpar_blocos() mexe
    apenas nas refeições. Sem esta limpeza, o que não for dito nesta dieta
    permanece do que estava na planilha: a mestre distribuída vem com
    C3 = "Definição Muscular" (sobra do exemplo), que ia parar no cabeçalho do
    PDF de quem não ditou objetivo. Verificado em 28/07/2026.

    NUNCA usar na retomada de um paciente: lá o dado anterior é justamente o que
    se quer herdar — e a skill mostra o que herdou antes de calcular.

    H18 (GCD manual) entra junto por ser entrada do usuário: um valor velho
    sobrevivente viraria a meta calórica de outro paciente. H23 fica de fora
    porque a escolha de fórmula acompanha o objetivo por meses (regra do
    nutricionista) e escrever_paciente() a grava em toda dieta.
    """
    apagadas = 0
    for ref in list(ANCORAS_TMB) + ["H18"]:
        if pacote.apagar("TMB", ref):
            apagadas += 1
    return apagadas


def nome_para_planilha(alimento):
    """
    O que vai para a célula: o nome EXATO da tabela, não o limpo.

    A busca da planilha é literal. Há alimentos cadastrados com espaço sobrando
    ("Lentilha ", "Requeijão ", "Muçarela de búfala ") — gravar o nome limpo
    fazia a busca falhar e a refeição inteira dava erro. Aceita tanto o objeto
    Alimento quanto texto puro, para ninguém precisar lembrar da diferença.
    """
    return getattr(alimento, "nome_planilha", None) or str(alimento)


def limpar_blocos(pacote, aba):
    """
    A planilha distribuída vem com uma dieta de exemplo preenchida. Sem limpar,
    os alimentos do exemplo entrariam na dieta do paciente e no cálculo.
    Apaga apenas C (alimento), D (quantidade) e E do cabeçalho — nunca as fórmulas.
    """
    apagadas = 0
    for i in range(MAX_REFEICOES):
        cab, primeira = _linhas_bloco(i)
        for ref in ["E%d" % cab]:
            if pacote.celula_bruta(aba, ref):
                pacote.apagar(aba, ref); apagadas += 1
        for j in range(ALIMENTOS_POR_REFEICAO):
            for col in ("C", "D"):
                ref = "%s%d" % (col, primeira + j)
                if pacote.celula_bruta(aba, ref):
                    pacote.apagar(aba, ref); apagadas += 1
    return apagadas


def escrever_refeicoes(pacote, aba, refeicoes, limpar=True):
    """
    refeicoes: lista de dicts {nome, itens: [(alimento, quantidade), ...]}.
    Escreve só C (alimento) e D (quantidade) — E é fórmula nas linhas de alimento.
    Um None na lista deixa aquele bloco vazio, mantendo a posição dos seguintes
    (as opções de uma refeição ficam no mesmo bloco da principal — F1).
    """
    if len(refeicoes) > MAX_REFEICOES:
        raise ErroPlanilha(
            "A planilha comporta %d refeições e você montou %d."
            % (MAX_REFEICOES, len(refeicoes))
        )
    if limpar:
        limpar_blocos(pacote, aba)
    for i, ref in enumerate(refeicoes):
        if ref is None:
            continue
        conferir_ancora_bloco(pacote, aba, i)
        cab, primeira = _linhas_bloco(i)
        if ref.get("nome"):
            nome = ref["nome"]
            if ref.get("horario"):
                nome += " (horário: %s)" % ref["horario"]
            pacote.escrever(aba, "E%d" % cab, nome, "texto")
        itens = ref.get("itens", [])
        if len(itens) > ALIMENTOS_POR_REFEICAO:
            raise ErroPlanilha(
                'Na refeição "%s" cabem %d alimentos e você listou %d. '
                "Se eu escrever o %dº, apago o total da refeição."
                % (ref.get("nome", i + 1), ALIMENTOS_POR_REFEICAO,
                   len(itens), ALIMENTOS_POR_REFEICAO + 1)
            )
        for j, (alimento, quantidade) in enumerate(itens):
            pacote.escrever(aba, "C%d" % (primeira + j),
                            nome_para_planilha(alimento), "texto")
            pacote.escrever(aba, "D%d" % (primeira + j), quantidade, "numero")


# ---------------------------------------------------------------- conferência

# R7.3 — alimento de conferência criado pela SKILL, não tirado do catálogo.
#
# A versão anterior usava "Pão" 60 g = 4,77213913043478 — dado clínico da tabela.
# Isso criava uma armadilha: no dia em que o Cassiano corrigisse o Pão, a skill
# travaria na mão de TODOS os alunos, com a planilha perfeitamente válida.
# Agora os valores são escolhidos aqui e gravados na cópia, então o resultado
# esperado não depende de nenhum dado do catálogo.
#
# Um valor distinto por coluna: uma versão do LibreOffice pode recalcular uma
# coluna e falhar em outra, e um par único não pegaria isso.
CONFERENCIA_NOME = "zz Conferencia da skill"
CONFERENCIA_QTD = 100
CONFERENCIA_VALORES = {                 # por 1 unidade -> x100 dá o esperado
    "Ptn (A)": 0.5, "Ptn (V)": 0.25, "Carbs": 0.125,
    "Fat": 0.0625, "Poli": 0.03125, "Mono": 0.015625, "Fibra": 0.0078125,
}
# coluna do bloco de refeição onde cada nutriente é calculado
COLUNA_NO_BLOCO = {
    "Ptn (A)": "F", "Ptn (V)": "G", "Carbs": "H", "Fat": "I",
    "Poli": "J", "Mono": "K", "Fibra": "L",
}


def gravar_conferencia(pacote, colunas_tabela, aba=ABA_CONFERENCIA):
    """
    Cria o alimento de conferência na cópia e o prescreve numa aba desligada.

    B5 — a cópia que recebe isto NUNCA é a que vai para a pasta do paciente:
    calcular_dieta() grava o paciente a partir da cópia limpa, feita antes.
    """
    conferir_ancora_bloco(pacote, aba, 0)
    linha = injetar_alimentos(
        pacote,
        [{"nome": CONFERENCIA_NOME, "medida": "g",
          "valores": dict(CONFERENCIA_VALORES)}],
        colunas_tabela,
        ultima_linha_preenchida(pacote, colunas_tabela) + 1)[0]
    pacote.escrever(aba, "C4", CONFERENCIA_NOME, "texto")
    pacote.escrever(aba, "D4", CONFERENCIA_QTD, "numero")
    return linha


def ultima_linha_preenchida(pacote, colunas, aba="Tabela Nutricional",
                            max_linha=400):
    col = colunas.get("Nome", "A")
    ultima = 1
    for linha in range(2, max_linha):
        if (pacote.texto(aba, "%s%d" % (col, linha)) or "").strip():
            ultima = linha
    return ultima


def validar_conferencia(pacote_calculado, tolerancia=1e-6, aba=ABA_CONFERENCIA):
    """
    Confere que o recálculo aconteceu de verdade, coluna por coluna.
    Falhou -> não há PDF. É a única defesa contra o LibreOffice devolver
    valores velhos, e ela mede o RESULTADO, não o sistema operacional.
    """
    erradas = []
    for campo, por_unidade in CONFERENCIA_VALORES.items():
        ref = "%s4" % COLUNA_NO_BLOCO[campo]
        esperado = por_unidade * CONFERENCIA_QTD
        obtido = pacote_calculado.numero(aba, ref)
        if obtido is None or abs(obtido - esperado) > tolerancia:
            erradas.append("%s (esperava %s, veio %s)" % (campo, esperado, obtido))
    if erradas:
        raise ErroPlanilha(
            "Não consegui confirmar que as contas da planilha foram refeitas: %s. "
            "Não vou gerar o PDF com números em que não confio. Isso costuma ser "
            "a versão do LibreOffice instalada — tente atualizar; se continuar, "
            "avise o suporte." % "; ".join(erradas[:3]))
    return True


# ---------------------------------------------------------------- cálculo

ERROS_CELULA = re.compile(r"#(N/A|REF|VALOR|VALUE|DIV/0|NOME|NAME|NUM|NULO|NULL)")


def calcular(caminho_xlsm, soffice, pasta_trabalho, timeout=180):
    """
    Roda o LibreOffice sobre a cópia e devolve o caminho do .xlsx com os valores.

    Perfil isolado para não conflitar com o LibreOffice que o usuário tenha aberto.
    """
    saida = os.path.join(pasta_trabalho, "calculado")
    os.makedirs(saida, exist_ok=True)
    perfil = os.path.join(pasta_trabalho, "perfil_lo")
    url_perfil = "file:///" + perfil.replace("\\", "/").lstrip("/")

    esperado = os.path.join(
        saida, os.path.splitext(os.path.basename(caminho_xlsm))[0] + ".xlsx")
    # R8.9 — com recálculo a cada refeição, a mesma pasta é reutilizada: o
    # resultado da rodada anterior é APAGADO antes, senão uma falha silenciosa
    # do soffice entregaria o arquivo velho como se fosse novo.
    if os.path.exists(esperado):
        os.remove(esperado)

    cmd = [
        soffice, "--headless", "--norestore", "--nolockcheck", "--invisible",
        "-env:UserInstallation=" + url_perfil,
        "--convert-to", "xlsx", "--outdir", saida, caminho_xlsm,
    ]
    try:
        subprocess.run(cmd, timeout=timeout, capture_output=True)
    except subprocess.TimeoutExpired:
        raise ErroPlanilha(
            "A planilha demorou demais para calcular. Feche o LibreOffice se ele "
            "estiver aberto e tente de novo."
        )

    # o código de saída do soffice não é confiável — conferimos o arquivo
    if not os.path.exists(esperado) or os.path.getsize(esperado) == 0:
        raise ErroPlanilha(
            "O LibreOffice não conseguiu processar a planilha. Verifique se ele "
            "está instalado corretamente."
        )
    return esperado


# Célula inteira, com corpo não-guloso: para no primeiro </c>.
# A versão anterior usava (?:(?!</c>).)*? — lookahead por caractere — e levava
# 458 SEGUNDOS numa aba de 1,4 MB. Medido no teste de carga em 27/07/2026.
_CELULA = re.compile(r'<c r="([A-Z]+\d+)"[^>]*?(?:/>|>(.*?)</c>)', re.S)


def procurar_erros(pacote, abas):
    """R7.5 — devolve [(aba, ref, alimento_da_linha), ...] para cada erro achado."""
    achados = []
    for aba in abas:
        x = pacote.xml(aba)
        if "#" not in x:                      # atalho: nenhuma célula com erro
            continue
        for m in _CELULA.finditer(x):
            corpo = m.group(2)
            if not corpo or "#" not in corpo:
                continue
            valor = re.search(r"<v[^>]*>([^<]*)</v>", corpo)
            if valor and ERROS_CELULA.search(valor.group(1)):
                ref = m.group(1)
                _, lin = col_linha(ref)
                achados.append((aba, ref, pacote.texto(aba, "C%d" % lin)))
    return achados


# ------------------------------------------------- conclusão do cálculo

def conferir_conclusao(pacote_calculado, abas):
    """
    A conta fechou? Roda em TODO cálculo e devolve os problemas em português.

    Existe porque "sem erro de célula" não é o mesmo que "calculou". Três
    famílias de falha, e só a primeira tinha cobertura:

      1. célula com erro (#N/A e parentes) — alimento removido ou renomeado
      2. meta calórica vazia — a fórmula escolhida exige % de gordura e ele está
         em branco. Cunningham e Tinsley (MLG) devolvem célula VAZIA, não erro:
         verificado em 28/07/2026, a skill gerava o PDF com a meta em branco e
         procurar_erros() não via nada
      3. total da dieta vazio — mesma família, do lado da dieta

    Lista vazia = pode salvar e pode gerar documento. Qualquer item = para.
    A mensagem nomeia o alimento culpado quando existe um; endereço de célula
    não diz nada para quem usa isto.
    """
    problemas = []

    # Um alimento que não existe contamina a planilha inteira: o teste de 28/07
    # produziu 6 avisos para UM alimento faltando, e 5 eram consequência —
    # "Alimento" e "kcals" (rótulos de cabeçalho), "#N/A" e "0" (células já
    # contaminadas). Por isso a busca começa pela causa: as linhas de alimento
    # prescritas. Só se nenhuma delas explicar o erro é que se fala em outra coisa.
    culpados = []
    for aba in abas:
        for i in range(MAX_REFEICOES):
            _, primeira = _linhas_bloco(i)
            for j in range(ALIMENTOS_POR_REFEICAO):
                linha = primeira + j
                nome = pacote_calculado.texto(aba, "C%d" % linha)
                if not nome:
                    continue
                if any(ERROS_CELULA.search(
                        pacote_calculado.texto(aba, "%s%d" % (col, linha)) or "")
                        for col in COLUNA_NO_BLOCO.values()):
                    if nome.strip() not in culpados:
                        culpados.append(nome.strip())

    for nome in culpados:
        problemas.append(
            'o alimento "%s" não foi encontrado na tabela — ele pode ter sido '
            "removido ou renomeado no seu cadastro" % nome)

    if not culpados:
        restantes = procurar_erros(pacote_calculado, list(abas) + ["TMB"])
        if any(aba == "TMB" for aba, _, _ in restantes):
            problemas.append("a ficha do paciente tem uma conta que não fechou")
        if any(aba != "TMB" for aba, _, _ in restantes):
            problemas.append("a dieta tem uma conta que não fechou")

    meta = pacote_calculado.numero("TMB", "C12")
    formula = pacote_calculado.numero("TMB", "H23")
    if meta is None or meta <= 0:
        # A causa depende da fórmula: só a 4 e a 5 dependem do % de gordura.
        if formula in (4, 5):
            causa = "a fórmula escolhida precisa do percentual de gordura corporal"
        elif formula == 6:
            causa = "a fórmula 6 usa o valor definido por você, e ele não está preenchido"
        else:
            causa = "confira sexo, peso, altura e idade na ficha do paciente"
        problemas.append("a meta calórica saiu %s — %s"
                         % ("em branco" if meta is None else "zerada", causa))
    elif pacote_calculado.numero("TMB", "C13") is None:
        problemas.append("as calorias por quilo saíram em branco")

    # O total em branco é CONSEQUÊNCIA de um alimento que faltou; repetir isso
    # depois de já ter nomeado o culpado só afoga a mensagem que importa.
    if not culpados:
        for aba in abas:
            if pacote_calculado.numero(aba, "AM9") is None:
                problemas.append(
                    "o total de calorias da dieta saiu em branco na aba '%s'" % aba)

    vistos = set()
    return [p for p in problemas if not (p in vistos or vistos.add(p))]


# ---------------------------------------------------------------- extração

MACROS = [
    ("Proteína (Animal)", 3), ("Proteína (Vegetal)", 4), ("Carboidrato", 5),
    ("Gordura Saturada", 6), ("Gordura Polinsaturada", 7), ("Gordura Monoinsaturada", 8),
]
PRIMEIRA_LINHA_MICRO = 29
ULTIMA_LINHA_MICRO = 48


def extrair(pacote, aba):
    """Lê os resultados de UMA aba. Nunca soma abas diferentes (R9.14)."""
    if (pacote.texto(aba, "AJ2") or "").strip() != "Macronutrientes":
        raise ErroPlanilha(
            "Não encontrei a tabela de macronutrientes onde esperava — o formato "
            "da planilha mudou."
        )

    macros = []
    for nome, linha in MACROS:
        macros.append({
            "nome": nome,
            "gramas": pacote.numero(aba, "AK%d" % linha),
            "percentual": pacote.numero(aba, "AL%d" % linha),
            "kcal": pacote.numero(aba, "AM%d" % linha),
            "g_por_kg": pacote.numero(aba, "AN%d" % linha),
        })

    if (pacote.texto(aba, "AJ28") or "").strip() != "Outros dados":
        raise ErroPlanilha("Não encontrei a tabela de micronutrientes.")

    micros = []
    for linha in range(PRIMEIRA_LINHA_MICRO, ULTIMA_LINHA_MICRO + 1):
        nome = pacote.texto(aba, "AJ%d" % linha)
        if not nome:
            continue
        micros.append({
            "nome": nome.strip(),
            "total": pacote.numero(aba, "AK%d" % linha),
            "unidade": (pacote.texto(aba, "AL%d" % linha) or "").strip(),
            "idr": pacote.numero(aba, "AM%d" % linha),
            "adequacao": pacote.numero(aba, "AN%d" % linha),
        })

    return {
        "aba": aba,
        "refeicoes": _extrair_refeicoes(pacote, aba),
        "macros": macros,
        "micros": micros,
        "total_kcal": pacote.numero(aba, "AM9"),
        "kcal_por_kg": pacote.numero(aba, "AM10"),
        "diferenca_gcd": pacote.numero(aba, "AM11"),
    }


def _extrair_refeicoes(pacote, aba):
    refeicoes = []
    for i in range(MAX_REFEICOES):
        cab, primeira = _linhas_bloco(i)
        nome = pacote.texto(aba, "E%d" % cab)
        itens = []
        for j in range(ALIMENTOS_POR_REFEICAO):
            linha = primeira + j
            alimento = pacote.texto(aba, "C%d" % linha)
            if not alimento:
                continue
            itens.append({
                "alimento": alimento.strip(),
                "quantidade": pacote.numero(aba, "D%d" % linha),
                "medida": (pacote.texto(aba, "E%d" % linha) or "").strip(),
            })
        if itens:
            ref = {"nome": (nome or "").strip(), "itens": itens, "bloco": i,
                   "kcal": pacote.numero(aba, "C%d" % (primeira + ALIMENTOS_POR_REFEICAO + 1))}
            horario = re.fullmatch(r"(.*) \(horário: (.+)\)", ref["nome"])
            if horario:
                ref["nome"], ref["horario"] = horario.groups()
            refeicoes.append(ref)
    return refeicoes


def extrair_por_alimento(pacote, aba):
    """
    R8.8 — macros por alimento, em gramas, lidos das células F..L já calculadas
    pela planilha em cada bloco de refeição (mesma geometria de _extrair_refeicoes).

    Nenhuma conta nova: só leitura das colunas de COLUNA_NO_BLOCO na linha de
    cada alimento. Célula vazia vira 0.0, nunca None.
    """
    refeicoes = []
    for i in range(MAX_REFEICOES):
        cab, primeira = _linhas_bloco(i)
        nome = pacote.texto(aba, "E%d" % cab)
        itens = []
        for j in range(ALIMENTOS_POR_REFEICAO):
            linha = primeira + j
            alimento = pacote.texto(aba, "C%d" % linha)
            if not alimento:
                continue
            macros = {}
            for campo, col in COLUNA_NO_BLOCO.items():
                if campo == "Fibra":
                    continue
                valor = pacote.numero(aba, "%s%d" % (col, linha))
                macros[campo] = valor if valor is not None else 0.0
            itens.append({
                "alimento": alimento.strip(),
                "quantidade": pacote.numero(aba, "D%d" % linha),
                "medida": (pacote.texto(aba, "E%d" % linha) or "").strip(),
                "macros": macros,
            })
        if itens:
            # R8.9 — a linha de totais do bloco (a que o 11º alimento
            # sobrescreveria) é calculada pela planilha; lê-se, nunca se soma.
            # Total em branco aqui é fórmula apagada — erro claro, nunca zero.
            linha_total = primeira + ALIMENTOS_POR_REFEICAO
            totais = {}
            for campo, col in COLUNA_NO_BLOCO.items():
                if campo == "Fibra":
                    continue
                valor = pacote.numero(aba, "%s%d" % (col, linha_total))
                if valor is None:
                    raise ErroPlanilha(
                        'O total de "%s" da refeição "%s" saiu em branco na '
                        "planilha — a fórmula dessa linha pode ter sido apagada. "
                        "Não vou mostrar uma tabela com total que não veio da "
                        "planilha." % (campo, (nome or "refeição %d" % (i + 1))))
                totais[campo] = valor
            refeicoes.append({"nome": (nome or "").strip(), "itens": itens,
                              "totais": totais})
    return refeicoes


CURINGAS_PROCV = ("*", "?", "~")


def _linha_do_nome(pacote, nome, colunas, aba="Tabela Nutricional",
                   max_linha=400):
    """Primeira linha com esse nome — é a única que o PROCV enxerga."""
    alvo = str(nome).strip().lower()
    col = colunas.get("Nome", "A")
    for linha in range(2, max_linha):
        atual = pacote.texto(aba, "%s%d" % (col, linha))
        if atual and atual.strip().lower() == alvo:
            return linha
    return None


def _limpar_linha(pacote, linha, colunas, aba="Tabela Nutricional"):
    for letra in set(colunas.values()):
        pacote.apagar(aba, "%s%d" % (letra, linha))


def primeira_linha_usuario(pacote_modelo, colunas, aba="Tabela Nutricional"):
    """
    Onde começa a área dos alimentos cadastrados pelo nutricionista.

    É constante, porque a mestre é fixa e conferida por SHA-256: tudo até a
    última linha com nome pertence à tabela original; da seguinte em diante é do
    usuário. Ler do MODELO (nunca da planilha do paciente) é o que torna a conta
    estável — na do paciente as linhas injetadas já deslocariam o resultado.
    """
    return ultima_linha_preenchida(pacote_modelo, colunas, aba) + 1


def limpar_area_usuario(pacote, colunas, primeira_linha, aba="Tabela Nutricional",
                        max_linha=400):
    """
    Apaga a área do usuário inteira antes de reinjetar o cadastro vigente (R6.13).

    injetar_alimentos() percorre só o cadastro atual e nunca removia o que havia
    sido gravado antes. Enquanto a cópia era descartável isso não aparecia; com a
    planilha do paciente persistida, apagar um alimento do cadastro deixava a
    linha dele viva no arquivo — e o PROCV continuava encontrando. Pior: a linha
    órfã passava a contar em ultima_linha_preenchida(), empurrando a injeção
    seguinte para baixo e acumulando lixo a cada consulta.

    Apagar tudo e regravar cobre exclusão e renomeação sem guardar estado nenhum.
    """
    limpadas = 0
    for linha in range(primeira_linha, max_linha):
        if (pacote.texto(aba, "%s%d" % (colunas.get("Nome", "A"), linha)) or "").strip():
            _limpar_linha(pacote, linha, colunas, aba)
            limpadas += 1
    return limpadas


def injetar_alimentos(pacote, alimentos, colunas, primeira_linha,
                      aba="Tabela Nutricional"):
    """
    R6.7/R6.8/R6.11 — escreve os alimentos do usuário na CÓPIA de trabalho.

    Sem colisão de nome: entra depois da última linha preenchida (as faixas dos
    PROCV são colunas inteiras, então acrescentar no fim não desloca nada).

    COM colisão: o PROCV só enxerga a PRIMEIRA linha com aquele nome. Escrever no
    fim fazia a skill dizer "usei o seu cadastro" enquanto a planilha calculava
    com o alimento original — falha silenciosa confirmada em 27/07/2026
    (Whey Protein: revisão dizia 0,95, planilha calculava 0,70).
    Solução: LIMPAR a primeira linha colidente e gravar o do usuário ali.
    Nunca inserir linha no meio — isso obrigaria a renumerar tudo e quebraria
    calcChain, validações e formatação condicional.

    Levanta ErroPlanilha se algum campo não corresponder a uma coluna da tabela:
    ignorar em silêncio fazia o nutriente sumir da dieta sem aviso.
    """
    usadas = []
    proxima_livre = primeira_linha
    for alimento in alimentos:
        nome = str(alimento.get("nome", "")).strip()
        if not nome:
            continue
        if any(c in nome for c in CURINGAS_PROCV):
            raise ErroPlanilha(
                'O nome "%s" tem um dos caracteres %s, que a planilha usa como '
                "coringa de busca — ela acabaria pegando outro alimento. "
                "Escolha um nome sem esses símbolos."
                % (nome, " ".join(CURINGAS_PROCV)))

        valores = alimento.get("valores") or {}
        desconhecidos = [t for t in valores if t not in colunas]
        if desconhecidos:
            raise ErroPlanilha(
                "Não reconheço %s na tabela de alimentos. Se eu gravasse assim, "
                "esses valores sumiriam da conta sem aviso. Os campos válidos "
                "são: %s." % (", ".join('"%s"' % d for d in desconhecidos),
                              ", ".join(sorted(c for c in colunas
                                               if c not in ("Nome", "Medida")))))

        colidente = _linha_do_nome(pacote, nome, colunas, aba)
        if colidente is not None:
            _limpar_linha(pacote, colidente, colunas, aba)
            linha = colidente
        else:
            linha = proxima_livre
            proxima_livre += 1

        pacote.escrever(aba, "%s%d" % (colunas["Nome"], linha), nome, "texto")
        if colunas.get("Medida"):
            pacote.escrever(aba, "%s%d" % (colunas["Medida"], linha),
                            alimento.get("medida") or "g", "texto")
        for titulo, valor in valores.items():
            if isinstance(valor, (int, float)):
                pacote.escrever(aba, "%s%d" % (colunas[titulo], linha),
                                valor, "numero")
        usadas.append(linha)
    return usadas


def extrair_todas(pacote, abas):
    """
    R9.11/R9.14 — extrai CADA aba ativa separadamente.
    Nunca soma macronutrientes de abas diferentes: 5 opções de 2.000 kcal não
    são uma dieta de 10.000 kcal.
    """
    return [extrair(pacote, aba) for aba in abas]


def cobertura_micronutrientes(dados_da_aba, catalogo_por_nome):
    """
    R9.15 — quantos alimentos da dieta não têm valor cadastrado para cada
    micronutriente. Campo vazio conta ZERO no cálculo, e um número parcial num
    documento assinado é pior do que um travessão.
    """
    alimentos = [i["alimento"] for r in dados_da_aba["refeicoes"] for i in r["itens"]]
    total = len(alimentos)
    saida = []
    for micro in dados_da_aba["micros"]:
        sem_valor = 0
        for nome in alimentos:
            valores = (catalogo_por_nome.get(nome) or {})
            if not valores.get(micro["nome"]):
                sem_valor += 1
        cobertos = total - sem_valor
        saida.append(dict(
            micro,
            alimentos_sem_valor=sem_valor,
            alimentos_total=total,
            sem_cobertura=(total > 0 and cobertos * 2 < total),   # menos da metade
        ))
    return saida


def extrair_tmb(pacote):
    return {
        "meta_kcal": pacote.numero("TMB", "C12"),
        "kcal_por_kg": pacote.numero("TMB", "C13"),
        "massa_gorda": pacote.numero("TMB", "C16"),
        "massa_magra": pacote.numero("TMB", "C17"),
        "peso": pacote.numero("TMB", "C6"),
    }


# ---------------------------------------------------------------- pasta de trabalho

PREFIXO_TEMP = "cass-dieta-"


IDADE_ORFA = 3600   # segundos: um cálculo leva segundos; com 1 hora ninguém usa mais


def limpar_orfaos():
    """
    R10.5 — pastas de execuções interrompidas (Esc, queda, falta de luz).

    B11 — só as abandonadas há mais de IDADE_ORFA. A pasta temporária do sistema
    é compartilhada entre conversas: apagar toda `cass-dieta-*` derrubava o
    cálculo de outra conversa rodando ao mesmo tempo.
    """
    base = tempfile.gettempdir()
    removidas = 0
    try:
        nomes = os.listdir(base)
    except OSError:
        return 0
    limite = time.time() - IDADE_ORFA
    for nome in nomes:
        caminho = os.path.join(base, nome)
        if not nome.startswith(PREFIXO_TEMP):
            continue
        try:
            if os.path.getmtime(caminho) > limite:
                continue
        except OSError:
            continue
        if remover_pasta(caminho):
            removidas += 1
    return removidas


def remover_pasta(caminho):
    """Remove pasta lidando com o limite de 260 caracteres do Windows."""
    if sys.platform == "win32" and not caminho.startswith("\\\\?\\"):
        alvo = "\\\\?\\" + os.path.abspath(caminho)
    else:
        alvo = caminho
    try:
        shutil.rmtree(alvo, ignore_errors=False)
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


class PastaDeTrabalho:
    """Contexto que garante limpeza mesmo quando dá erro (R10.4)."""

    def __init__(self):
        self.caminho = None

    def __enter__(self):
        limpar_orfaos()
        self.caminho = tempfile.mkdtemp(prefix=PREFIXO_TEMP)
        return self.caminho

    def __exit__(self, *_):
        if self.caminho and not remover_pasta(self.caminho):
            # não mascarar: é dado de saúde
            print("Aviso: não consegui apagar a pasta temporária %s. "
                  "Apague manualmente." % self.caminho)
        return False


def preparar_copia(mestre, pasta_trabalho, hash_referencia=None):
    """
    R3.2/R3.3 — cópia sem nome de paciente, com conferência do mestre.

    `hash_referencia` só é passado para a planilha-MODELO (P1a), a única que tem
    impressão digital conhecida. Planilha de paciente entra sem hash, porque é
    diferente do modelo por definição — a conferência dela é estrutural e está em
    conferir_planilha_paciente() (P1b).
    """
    if hash_referencia:
        atual = sha256(mestre)
        if atual != hash_referencia:
            raise ErroPlanilha(
                "A planilha de cálculo que veio com a skill está diferente da "
                "original. Se você a alterou de propósito, avise o suporte; se "
                "não, reinstale a skill. (Isto é a planilha-modelo, não a de "
                "nenhum paciente — as dos pacientes podem ser diferentes.)"
            )
    destino = os.path.join(pasta_trabalho, "trabalho.xlsm")
    shutil.copy2(mestre, destino)
    return destino


# ------------------------------------------- fórmulas de gasto calórico

# (número em TMB!H23, nome, célula do resultado, exige % de gordura)
FORMULAS = [
    (1, "Harris-Benedict", "H13", False),
    (2, "Mifflin", "H14", False),
    (3, "Tinsley (peso)", "H15", False),
    (4, "Tinsley (massa livre de gordura)", "H16", True),
    (5, "Cunningham", "H17", True),
    (6, "Valor definido pelo nutricionista", "H18", False),
]


def nome_da_formula(numero):
    for n, nome, _, _ in FORMULAS:
        if n == int(numero or 0):
            return nome
    return None


def exige_gordura(numero):
    """Fórmulas 4 e 5 sem TMB!C15 devolvem meta VAZIA, sem erro nenhum."""
    return any(n == int(numero or 0) and precisa for n, _, _, precisa in FORMULAS)


def ler_formulas(pacote_calculado):
    """
    As seis fórmulas com o que cada uma deu para este paciente.

    A planilha calcula TODAS ao mesmo tempo (TMB!H13..H18); TMB!H23 apenas
    escolhe qual vira a Meta Kcal. Medido em 28/07 com um paciente de 80 kg:
    2.788 kcal no Mifflin contra 3.190 no Tinsley (P) — 402 kcal de diferença,
    14%, para a mesma pessoa.

    Como os números já existem, escondê-los seria tirar do nutricionista uma
    informação que a planilha dele produziu. Ele continua escolhendo (P5); só
    não escolhe às cegas. Fórmula sem resultado sai com kcal=None — é o caso das
    que precisam do % de gordura quando ele está em branco.
    """
    saida = []
    for numero, nome, celula, precisa in FORMULAS:
        saida.append({
            "numero": numero,
            "nome": nome,
            "kcal": pacote_calculado.numero("TMB", celula),
            "exige_gordura": precisa,
        })
    return saida


# ------------------------------------------- retomada


CAMPOS_FICHA = {"C2": "nome", "C3": "objetivo", "C6": "peso", "C7": "altura",
                "C8": "idade", "C9": "fa", "C10": "sexo", "C15": "gordura",
                "C18": "gestante", "H23": "formula", "H18": "gcd_manual"}
TEXTOS_FICHA = {"nome", "objetivo", "sexo", "gestante"}


def ler_ficha(pacote):
    """
    Os dados que o nutricionista informou, lidos de volta da planilha dele.

    Lê ENTRADA, não resultado: nome, objetivo, medidas e fórmula escolhida são
    valores literais gravados nas células e sobrevivem em qualquer situação. Meta
    calórica e totais são fórmula, e a planilha do paciente é guardada sem os
    valores em cache (decisão de 28/07) — quem quiser os números recalcula.

    É isto que sustenta a retomada sem inventar formato de arquivo novo.
    """
    ficha = {}
    for ref, chave in CAMPOS_FICHA.items():
        valor = (pacote.texto("TMB", ref) if chave in TEXTOS_FICHA
                 else pacote.numero("TMB", ref))
        if valor not in (None, ""):
            ficha[chave] = valor.strip() if isinstance(valor, str) else valor
    return ficha


def ler_dieta(pacote, aba):
    """As refeições gravadas: alimentos e quantidades, que também são literais."""
    return _extrair_refeicoes(pacote, aba)


def assinatura_de_calculo(pacote):
    """
    As fórmulas de toda a planilha, para reconhecer quando o modelo mudou.

    Não guarda número de versão em lugar nenhum: a própria planilha é a prova.
    Se o Cassiano corrigir uma conta no modelo — como as 40 fórmulas de IDR que
    aplicavam a recomendação feminina a todos os pacientes, corrigidas em 26/07 —
    as fórmulas passam a divergir das que estão na planilha do paciente antigo.

    O que ISTO NÃO PEGA: correção de valor de alimento na Tabela Nutricional, que
    é dado e não fórmula. Esse caso já está coberto por outro caminho — alimento
    corrigido entra pelo cadastro do nutricionista e vence o da planilha em todo
    cálculo.

    Usa _CELULA, o padrão que casa UMA célula por vez. Um `.*?` procurando o
    `<f>` a partir da abertura da célula atravessa o documento inteiro quando a
    célula não tem fórmula — foi assim que procurar_erros() levou 458 segundos
    numa aba de 1,4 MB em 27/07. Aqui a mesma varredura leva 0,02 s.
    """
    achadas = set()
    for aba in ABAS:
        for m in _CELULA.finditer(pacote.xml(aba)):
            corpo = m.group(2)
            if not corpo or "<f" not in corpo:
                continue
            formula = re.search(r"<f[^>]*>(.*?)</f>", corpo, re.S)
            if formula:
                achadas.add((aba, m.group(1), formula.group(1)))
    return achadas


def modelo_mudou(caminho_modelo, caminho_paciente):
    """Quantas contas diferem entre o modelo atual e a planilha deste paciente."""
    try:
        with Pacote(caminho_modelo) as m, Pacote(caminho_paciente) as p:
            return len(assinatura_de_calculo(m) ^ assinatura_de_calculo(p))
    except (zipfile.BadZipFile, OSError, KeyError):
        return 0


def migrar(caminho_paciente, caminho_modelo):
    """
    Traz a dieta deste paciente para o modelo novo, sem calcular.

    Usa o mesmo passar_a_limpo() da retomada — as 5 abas, ligadas ou não, e a
    ficha inteira — montado numa pasta temporária. O arquivo do paciente só é
    trocado no fim, pela gravação com backup único (`.bak`).
    """
    with PastaDeTrabalho() as pasta:
        novo = preparar_copia(caminho_modelo, pasta)
        with Pacote(caminho_paciente) as velho, Pacote(novo) as pk:
            passar_a_limpo(velho, pk)
            limpar_cache(pk)
            pk.salvar(novo)
        conferir_membros(caminho_modelo, novo)
        with Pacote(novo) as pk:
            return gravar_planilha_paciente(pk, caminho_paciente, caminho_modelo)



# ------------------------------------------- opções por refeição (F1)

_OPCAO = re.compile(r"\s*[-–—]?\s*op[cç][aã]o\s*(\d+)\s*$", re.I)


def _base_e_opcao(nome):
    """'Jantar - Opção 3' -> ('Jantar', 3); 'Lanche da Tarde' -> ('Lanche da Tarde', 1)."""
    m = _OPCAO.search(nome or "")
    if not m:
        return (nome or "").strip(), 1
    return nome[:m.start()].strip(), int(m.group(1))


def distribuir_opcoes(refeicoes):
    """
    F1 — reparte as refeições ditadas (na ordem do documento) pelas 5 abas.

    A planilha compara o bloco N de cada aba alternativa com o bloco N da
    principal (linha "Diferença"), então a opção K de uma refeição vai para a aba
    K, NA MESMA POSIÇÃO da refeição principal. Opção 1, ou refeição sem opção,
    fica na principal. Devolve {aba: [refeição ou None por bloco]} para as 5 abas.
    """
    posicao, saida = {}, {aba: [] for aba in ABAS_CALCULO}
    for ref in refeicoes:
        base, n = _base_e_opcao(ref["nome"])
        if n > len(ABAS_CALCULO) or n < 1:
            raise ErroPlanilha(
                'A planilha comporta até %d opções por refeição, e "%s" seria a %dª.'
                % (len(ABAS_CALCULO), ref["nome"], n))
        chave = base.lower()
        if chave not in posicao:
            posicao[chave] = len(posicao)
        bloco = posicao[chave]
        aba = saida[ABAS_CALCULO[n - 1]]
        while len(aba) <= bloco:
            aba.append(None)
        if aba[bloco] is not None:
            raise ErroPlanilha('"%s" apareceu duas vezes.' % ref["nome"])
        aba[bloco] = ref
    for chave, bloco in posicao.items():
        principal = saida[ABAS_CALCULO[0]]
        if bloco >= len(principal) or principal[bloco] is None:
            nome = next(r["nome"] for r in refeicoes if _base_e_opcao(r["nome"])[0].lower() == chave)
            raise ErroPlanilha(
                '"%s" tem opção alternativa, mas falta a opção principal (a 1) dessa '
                "refeição." % _base_e_opcao(nome)[0])
    if len(posicao) > MAX_REFEICOES:
        raise ErroPlanilha("A planilha comporta %d refeições e você montou %d."
                           % (MAX_REFEICOES, len(posicao)))
    return saida


def _agrupar_por_refeicao(refeicoes_por_aba):
    """
    refeicoes_por_aba: [(aba, [refeição extraída, ...]), ...] na ordem das abas.
    Devolve [(refeição principal ou None, [opções dela])] na ordem do documento.

    Agrupa pelo NOME da refeição ("Jantar - Opção 3" é do "Jantar"), não pela
    posição: planilha antiga pode ter a opção em outro bloco. Opção sem refeição
    principal de mesmo nome vai ao fim, sozinha — nunca some.
    """
    principal = sorted(dict(refeicoes_por_aba).get(ABAS_CALCULO[0], []), key=lambda r: r["bloco"])
    alternativas = [(ABAS_CALCULO.index(aba), r) for aba, refs in refeicoes_por_aba
                    if aba != ABAS_CALCULO[0] for r in sorted(refs, key=lambda r: r["bloco"])]
    usadas, grupos = set(), []
    for r in principal:
        base = _base_e_opcao(r["nome"])[0].lower()
        mesmas = sorted(((_base_e_opcao(a["nome"])[1], i, id(a), a) for i, a in alternativas
                         if id(a) not in usadas and _base_e_opcao(a["nome"])[0].lower() == base),
                        key=lambda x: (x[0], x[1]))
        usadas.update(x[2] for x in mesmas)
        grupos.append((r, [x[3] for x in mesmas]))
    for _, a in alternativas:
        if id(a) not in usadas:
            grupos.append((None, [a]))
    return grupos


def ordem_do_documento(refeicoes_por_aba):
    """As refeições na ordem em que saem no documento: cada uma seguida das opções."""
    saida = []
    for principal, opcoes in _agrupar_por_refeicao(refeicoes_por_aba):
        saida.extend(([principal] if principal else []) + opcoes)
    return saida


def ler_opcoes(pacote):
    """O inverso de distribuir_opcoes: as refeições de todas as abas, na ordem do
    documento — cada refeição da principal seguida das suas opções."""
    por_aba = [(aba, _extrair_refeicoes(pacote, aba)) for aba in ABAS_CALCULO]
    return [dict({"nome": r["nome"], "itens": [(i["alimento"], i["quantidade"]) for i in r["itens"]]},
                 **({"horario": r["horario"]} if r.get("horario") else {}))
            for r in ordem_do_documento(por_aba)]


def _opcoes_do_resultado(abas_extraidas):
    """Para a revisão: as kcal de cada opção, lidas da planilha, por refeição."""
    saida = []
    for principal, opcoes in _agrupar_por_refeicao(
            [(a["aba"], a["refeicoes"]) for a in abas_extraidas]):
        if principal and opcoes:
            todas = [principal] + opcoes
            saida.append({"refeicao": _base_e_opcao(principal["nome"])[0],
                          "opcoes": [{"nome": r["nome"], "kcal": r["kcal"]} for r in todas]})
    return saida

# ------------------------------------------- comando único de cálculo (E2)

def _copiar_blocos(velho, novo, aba):
    """Copia, célula a célula, nome das refeições, alimentos e quantidades de uma
    aba — inclusive blocos vazios no meio, que ler_dieta() descartaria."""
    for i in range(MAX_REFEICOES):
        cab, primeira = _linhas_bloco(i)
        refs = [("E%d" % cab, "texto")]
        for j in range(ALIMENTOS_POR_REFEICAO):
            refs += [("C%d" % (primeira + j), "texto"), ("D%d" % (primeira + j), "numero")]
        for ref, tipo in refs:
            valor = velho.texto(aba, ref)
            if valor in (None, ""):
                continue
            if tipo == "numero" and _numero(valor) is None:
                tipo = "texto"
            novo.escrever(aba, ref, valor, tipo)


def passar_a_limpo(velho, novo):
    """
    B2/B10 — leva para uma folha nova do modelo tudo o que é do paciente: a
    ficha, quais abas estão ligadas e as 5 abas de dieta (ligadas ou não).
    A tabela de alimentos fica a do modelo: valor mexido à mão não sobrevive,
    e o cadastro do nutricionista é reinjetado a cada cálculo.
    """
    limpar_ficha_paciente(novo)
    escrever_paciente(novo, ler_ficha(velho), conferir=False)
    ligar_abas(novo, abas_ativas(velho))
    for aba in ABAS_CALCULO:
        limpar_blocos(novo, aba)
        _copiar_blocos(velho, novo, aba)


def calcular_dieta(mestre, hash_mestre, soffice, ficha, dietas=None, planilha_paciente=None,
                   paciente_novo=False, alimentos_usuario=(), abas_ligadas=None,
                   salvar=False):
    """
    O ciclo inteiro numa chamada só: monta, calcula, confere e — só se tudo
    fechar e `salvar` for pedido — grava na planilha do paciente.

    ficha        o que foi dito nesta consulta (na retomada, só o que mudou)
    dietas       {aba: [refeições]} — só as abas reescritas agora; as outras
                 ficam como estavam na planilha do paciente
    abas_ligadas quais abas valem; sem informar, as que já estavam ligadas
                 mais as que receberam dieta agora
    salvar       False = consulta/simulação: o arquivo do paciente não muda

    Devolve {"problemas", "abas", "opcoes", "formulas", "tmb", "salvo", "backup"}.
    `abas` traz cada aba com dieta (a principal primeiro); `opcoes`, as kcal de
    cada opção por refeição, para a revisão. Com
    problemas, nada é gravado (E2). A conferência do LibreOffice vai para uma
    cópia que nunca é gravada no paciente (B5).
    """
    dietas = dietas or {}
    resultado = {"problemas": [], "abas": [], "opcoes": [], "formulas": [], "tmb": {},
                 "salvo": None, "backup": None}
    if salvar and not planilha_paciente:
        raise ErroPlanilha("Para salvar preciso saber qual é a planilha do paciente.")
    retomada = bool(planilha_paciente) and not paciente_novo and os.path.exists(planilha_paciente)

    with PastaDeTrabalho() as pasta:
        limpa = preparar_copia(mestre, pasta, hash_mestre)
        with Pacote(mestre) as modelo, Pacote(limpa) as pk:
            colunas = _colunas(pk)
            if retomada:
                with Pacote(planilha_paciente) as velho:
                    passar_a_limpo(velho, pk)
                    ligadas = abas_ativas(velho)
            else:
                limpar_ficha_paciente(pk)
                for aba in ABAS_CALCULO:
                    limpar_blocos(pk, aba)
                ligadas = [ABAS_CALCULO[0]]
            escrever_paciente(pk, ficha)
            for aba, refeicoes in dietas.items():
                escrever_refeicoes(pk, aba, refeicoes)
            if abas_ligadas is None:
                abas_ligadas = list(ligadas) + [a for a, r in dietas.items() if r]
            abas_ligadas = [a for a in ABAS_CALCULO if a in abas_ligadas]
            ligar_abas(pk, abas_ligadas)
            primeira = primeira_linha_usuario(modelo, colunas)
            limpar_area_usuario(pk, colunas, primeira)
            injetar_alimentos(pk, list(alimentos_usuario), colunas, primeira)
            limpar_cache(pk)
            pk.salvar(limpa)
        conferir_membros(mestre, limpa)

        # abas com dieta (ligadas ou não) entram no resultado: as opções de uma
        # refeição moram nelas. A conferência vai numa aba vazia de uma cópia
        # descartável; sem aba vazia, numa cópia gêmea calculada à parte.
        with Pacote(limpa) as pk:
            com_dieta = [a for a in ABAS_CALCULO if a in abas_ligadas or ler_dieta(pk, a)]
        vazias = [a for a in ABAS_CALCULO if a not in com_dieta]
        aba_conf = vazias[-1] if vazias else ABA_CONFERENCIA
        com_conferencia = os.path.join(pasta, "com_conferencia.xlsm")
        shutil.copy2(limpa, com_conferencia)
        with Pacote(com_conferencia) as pk:
            gravar_conferencia(pk, _colunas(pk), aba_conf)
            limpar_cache(pk)
            pk.salvar(com_conferencia)

        if vazias:
            with Pacote(calcular(com_conferencia, soffice, pasta)) as calc:
                validar_conferencia(calc, aba=aba_conf)
                _ler_resultado(calc, com_dieta, resultado)
        else:
            gemea = os.path.join(pasta, "gemea")
            os.makedirs(gemea)
            with Pacote(calcular(com_conferencia, soffice, gemea)) as calc:
                validar_conferencia(calc, aba=aba_conf)
            principal = os.path.join(pasta, "principal")
            os.makedirs(principal)
            copia = os.path.join(principal, "trabalho.xlsm")
            shutil.copy2(limpa, copia)
            with Pacote(calcular(copia, soffice, principal)) as calc:
                _ler_resultado(calc, com_dieta, resultado)

        if resultado["problemas"] or not salvar:
            return resultado
        with Pacote(limpa) as pk:
            resultado["backup"] = gravar_planilha_paciente(pk, planilha_paciente, mestre)
        resultado["salvo"] = planilha_paciente
    return resultado


def _colunas(pacote):
    return catalogo.colunas_da_tabela(pacote)


def _ler_resultado(calc, abas, resultado):
    resultado["problemas"] = conferir_conclusao(calc, abas)
    resultado["formulas"] = ler_formulas(calc)
    resultado["tmb"] = extrair_tmb(calc)
    if not resultado["problemas"]:
        resultado["abas"] = [dict(extrair(calc, aba), aba=aba,
                                  por_alimento=extrair_por_alimento(calc, aba))
                             for aba in abas]
        resultado["opcoes"] = _opcoes_do_resultado(resultado["abas"])


# ------------------------------------------- planilha do paciente (P1b)

def conferir_planilha_paciente(modelo, caminho_paciente):
    """
    A planilha deste paciente ainda serve? Devolve os problemas em português.

    Ela É diferente do modelo por definição — tem os dados de quem é atendido —
    então impressão digital não serve aqui. O que se confere é estrutura: nenhum
    membro do pacote perdido e os rótulos-âncora no lugar.

    A mensagem NUNCA manda reinstalar a skill: isso vale para o modelo. Esta
    planilha é do consultório, e a saída é restaurar o backup ou refazer a partir
    do modelo (P1b, item 5).
    """
    problemas = []
    if not os.path.exists(caminho_paciente):
        return ["não encontrei a planilha deste paciente onde ela deveria estar"]
    try:
        faltando = _membros(modelo) - _membros(caminho_paciente)
    except (zipfile.BadZipFile, OSError):
        return ["o arquivo da planilha deste paciente está danificado e não abre"]
    if faltando:
        problemas.append(
            "a planilha deste paciente perdeu partes do arquivo (%d), o que "
            "costuma acontecer quando ela é salva por outro programa"
            % len(faltando))
    try:
        with Pacote(caminho_paciente) as pk:
            conferir_ancoras_tmb(pk)
    except ErroPlanilha:
        problemas.append(
            "a ficha do paciente nesta planilha não está no formato esperado — "
            "ela pode ter sido editada à mão")
    except (zipfile.BadZipFile, OSError, KeyError):
        problemas.append("não consegui ler o conteúdo da planilha deste paciente")
    return problemas


def gravar_planilha_paciente(pacote, caminho, modelo):
    """
    Grava a planilha do paciente com rede embaixo (P1b, itens 1 e 2).

    Backup primeiro, grava, confere que nenhum membro se perdeu. Perdeu — que é
    o acidente do P2, o mesmo que destruiu 20 dos 84 membros em 26/07 — restaura
    o backup e não deixa o estrago em pé.
    """
    backup = caminho + ".bak"
    if os.path.exists(caminho):
        shutil.copy2(caminho, backup)
    pacote.salvar(caminho)
    faltando = _membros(modelo) - _membros(caminho)
    if faltando:
        if os.path.exists(backup):
            shutil.copy2(backup, caminho)
            raise ErroPlanilha(
                "A gravação perdeu partes da planilha deste paciente, então "
                "voltei para a versão anterior — nada foi perdido. Tente de novo; "
                "se repetir, avise o suporte.")
        raise ErroPlanilha(
            "A gravação perdeu partes da planilha deste paciente e não havia "
            "versão anterior para restaurar. Não use este arquivo.")
    return backup if os.path.exists(backup) else None


def _membros(caminho):
    with zipfile.ZipFile(caminho) as z:
        return {i.filename for i in z.infolist()} - {"xl/calcChain.xml"}


def conferir_membros(original, copia):
    """R3.5 — nenhuma peça do arquivo pode se perder (ignorando calcChain)."""
    faltando = _membros(original) - _membros(copia)
    if faltando:
        raise ErroPlanilha(
            "A gravação perdeu partes do arquivo (%s). Interrompi para não "
            "estragar nada." % ", ".join(sorted(faltando)[:3])
        )
    return True
