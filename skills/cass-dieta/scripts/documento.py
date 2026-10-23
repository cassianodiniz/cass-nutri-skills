# -*- coding: utf-8 -*-
"""
Monta o HTML da dieta com o modelo aprovado e gera o PDF pelo motor disponível.

O PDF é gerado em arquivo temporário, VERIFICADO, e só então movido para o
destino. Falhou a verificação, o arquivo é apagado: melhor não entregar nada
do que entregar documento clínico com número errado.
"""
import os
import base64
import re
import shutil
import subprocess
import sys
import zipfile
import zlib
from html import escape, unescape

import planilha
import trocas as trocas_mod

TEXTO_CFN = (
    "A Resolução CFN nº 600/2018 determina que toda prescrição dietética contenha "
    "data, Valor Energético Total, consistência, macro e micronutrientes, "
    "fracionamento, assinatura com carimbo, número e região do CRN. "
    "Gostaria de pular esta etapa?"
)

PASTAS_NUVEM = ("onedrive", "google drive", "meu drive", "dropbox",
                "icloud", "sync", "nextcloud")

_ERRO_CELULA = re.compile(r"#(N/A|REF|VALOR|VALUE|DIV/0|NOME|NAME|NUM|NULO|NULL)",
                          re.I)   # o texto é comparado em minúsculas
_PROIBIDOS_NOME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVADOS = {"CON", "PRN", "AUX", "NUL"} | {"COM%d" % i for i in range(1, 10)} \
              | {"LPT%d" % i for i in range(1, 10)}


class ErroDocumento(Exception):
    """Mensagem já escrita para leigo."""


# ---------------------------------------------------------------- CSS

# Cada cor mantém seu kit; texto é sempre preto no modelo aprovado.
# O CSS abaixo está escrito no kit "verde"; css_da_cor() troca o kit inteiro.
PALETAS = {
    "verde":    {"forte": "#009044", "fundo": "#edf6f0", "borda": "#cfe4d8", "listra": "#f5faf7"},
    "azul":     {"forte": "#1e3a8a", "fundo": "#eef1fa", "borda": "#ccd6ee", "listra": "#f5f7fc"},
    "roxo":     {"forte": "#4c1d95", "fundo": "#f2edfa", "borda": "#d8cbee", "listra": "#f8f5fd"},
    "mostarda": {"forte": "#8a6400", "fundo": "#f8f4e7", "borda": "#e4d7ae", "listra": "#fcfaf2"},
    "laranja":  {"forte": "#b45309", "fundo": "#faf1e8", "borda": "#eed4b8", "listra": "#fdf8f2"},
    "vermelho": {"forte": "#991b1b", "fundo": "#f9eded", "borda": "#ecc9c9", "listra": "#fdf5f5"},
    "marrom":   {"forte": "#5d4037", "fundo": "#f4efed", "borda": "#ddcfc9", "listra": "#faf7f6"},
}
COR_PADRAO = "verde"


def css_da_cor(cor):
    """Devolve o CSS no kit da cor pedida. Cor desconhecida → erro claro (P4)."""
    nome = (cor or COR_PADRAO).strip().lower()
    if nome not in PALETAS:
        raise ErroDocumento(
            "Não conheço a cor %r. As cores disponíveis são: %s."
            % (cor, ", ".join(PALETAS)))
    css, verde, kit = CSS, PALETAS["verde"], PALETAS[nome]
    for tom in ("forte", "fundo", "borda", "listra"):
        css = css.replace(verde[tom], kit[tom])
    css = css.replace("#1b4036", "#1b4036" if nome == "verde" else kit["forte"])
    return css


CSS = """
@page{size:A4;margin:18mm 18mm 23mm}
*{box-sizing:border-box}
body{font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;color:#000;font-size:10pt;
     line-height:1.3;margin:0;overflow-wrap:break-word}
.logo{text-align:center;margin:0 0 16px}
.logo img{width:220px;max-width:65%;max-height:105px;object-fit:contain}
.hero{text-align:center;margin:0 0 14px;padding-bottom:6px;border-bottom:1px solid #009044}
.hero h1{font-size:18pt;margin:0;font-weight:600;line-height:1.15}
.hero h1.m{font-size:15pt}
.hero h1.p{font-size:13pt}
.hero .s{font-size:9.75pt;margin-top:4px}
.pills{margin:0 0 10px;font-size:8.5pt;text-align:center}
.pill{display:inline-block;margin:0 6px 3px}
h2{font-size:10.5pt;color:#000;margin:14px 0 6px;padding:4px 8px 1px;
   border-left:3px solid #009044;border-bottom:1px solid #009044;
   background:linear-gradient(to right,#edf6f0,#fff);break-after:avoid;font-weight:600}
h2 em{font-style:normal;font-weight:400;font-size:9pt;margin-left:10px}
.bloco{break-inside:avoid}
.opcao{font-size:9pt;font-weight:600;margin:12px 0 2px}
ul{list-style:none;padding:0;margin:0}
li{padding:3px 0;display:flex;justify-content:space-between;gap:14px;font-size:9.75pt;
   border-bottom:1px solid #e5e5e5;break-inside:avoid}
li>span:first-child{min-width:0}
li .q{color:#000;white-space:nowrap;flex-shrink:0}
.nutrientes{width:78%;margin:18px auto 0;break-inside:avoid}
.nutrientes h3{text-align:center;font-size:9.75pt;font-weight:600;margin:0 0 4px;break-after:avoid}
table{width:100%;border-collapse:collapse;font-size:9pt;color:#000}
th{background:#edf6f0;padding:4px 5px;text-align:left;font-weight:600}
th.n,td.n{text-align:center;white-space:nowrap}
td{padding:4px 5px;border-bottom:1px solid #e5e5e5}
tr.t td{font-weight:700;border-top:1px solid #009044;border-bottom:none}
.obs{margin-top:12px;font-size:9pt;border-left:2px solid #009044;padding:4px 8px}
.ass{margin:40px auto 32px;text-align:center;break-inside:avoid;line-height:1.15}
.ass .linha{width:180px;border-top:1px solid #000;margin:0 auto 6px}
.ass .nome{font-size:9.75pt;font-weight:600;margin:0}
.ass .s{font-size:8.25pt;margin:0}
.rod{position:fixed;bottom:-15mm;left:0;right:0;padding-top:5px;
     border-top:1px solid #009044;font-size:8.25pt;color:#000;line-height:1.3;text-align:center}
.rod span{display:inline-block;margin:0 8px 2px;max-width:100%;overflow-wrap:anywhere}
.canto{position:fixed;z-index:-1;color:#1b4036}
.canto.topo{top:-18mm;right:-18mm;width:28mm;height:23mm}
.canto.base{bottom:-23mm;left:-18mm;width:25.4mm;height:4.1mm}
@media screen and (max-width:600px){.nutrientes{width:94%}}
"""


# ---------------------------------------------------------------- números

def num(valor, casas=0):
    """Formata no padrão brasileiro. None vira travessão."""
    if valor is None:
        return "—"
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return escape(str(valor))
    texto = ("%%.%df" % casas) % v
    inteiro, _, dec = texto.partition(".")
    sinal = ""
    if inteiro.startswith("-"):
        sinal, inteiro = "-", inteiro[1:]
    grupos = []
    while len(inteiro) > 3:
        grupos.insert(0, inteiro[-3:])
        inteiro = inteiro[:-3]
    grupos.insert(0, inteiro)
    saida = sinal + ".".join(grupos)
    return saida + ("," + dec if dec else "")


def quantidade(item):
    q = item.get("quantidade")
    med = (item.get("medida") or "").strip()
    casas = 0 if q is not None and float(q) == int(float(q)) else 1
    texto = "%s %s" % (num(q, casas), med) if med else num(q, casas)
    sufixo = (item.get("sufixo") or "").strip()
    # a própria medida cadastrada pode já trazer o sufixo — "g (ou mais)".
    # Sem esta checagem sai "150 g (ou mais) (ou mais)".
    if sufixo and _limpa(sufixo) not in _limpa(texto):
        texto += " %s" % sufixo
    return texto.strip()


def linha_com_trocas(item):
    """F2 — a troca numa linha só: 'Arroz - 150 g ou Batata doce - 225 g ou ...'."""
    medida = (item.get("medida") or "g").strip()
    partes = ["%s - %s" % (item["alimento"], quantidade(item))]
    partes += ["%s - %s %s" % (nome, num(q), medida) for nome, q in item["trocas"]]
    return " ou ".join(partes)


def _item_html(item):
    if item.get("trocas"):
        return '<li><span>%s</span></li>' % _ou_em_italico(linha_com_trocas(item))
    return ('<li><span>%s</span><span class="q">%s</span></li>'
            % (_ou_em_italico(item["alimento"]), escape(quantidade(item))))


def _ou_em_italico(nome):
    return re.sub(r"\s+ou\s+", " <i>ou</i> ", escape(nome), flags=re.I)


def com_unidade(valor, unidade, casas=0):
    """R20.5 — todo número da tabela de macros vem com a unidade ao lado."""
    if valor is None:
        return "—"
    return "%s %s" % (num(valor, casas), unidade)


def _tamanho_classe(texto, limites):
    """Seleciona a classe de fonte pelo comprimento do nome.
    `limites`: [(máx_caracteres, classe_css), ...],
    a última classe vale para qualquer tamanho acima do penúltimo limite."""
    n = len(texto or "")
    for limite, classe in limites:
        if n <= limite:
            return classe
    return limites[-1][1]


# ---------------------------------------------------------------- montagem

def _item_doc(item, trocas_aprovadas):
    """Item do documento; com troca aprovada na revisão, ganha a linha completa (F2)."""
    saida = dict(alimento=item["alimento"], quantidade=item["quantidade"], medida=item["medida"])
    troca = trocas_mod.troca_para(item["alimento"], list(trocas_aprovadas))
    if troca:
        saida["trocas"] = trocas_mod.linha_da_troca(troca, item["quantidade"])[1:]
    return saida


def montar_doc(resultado, profissional, paciente, data, mostrar_numeros=True,
               micros=False, observacoes=(), cor=None, consistencia=None, trocas=()):
    """
    O conteúdo do documento, montado pelo código a partir do resultado de
    planilha.calcular_dieta() — o agente não copia número nenhum à mão (B4).
    Refeições: a principal com as opções logo abaixo; números: a dieta principal.
    `trocas`: as trocas que ele APROVOU na revisão — só elas saem no documento.
    """
    if resultado.get("problemas") or not resultado.get("abas"):
        raise ErroDocumento("O cálculo não fechou; não há documento para montar.")
    principal = resultado["abas"][0]
    # F1 — cada refeição da principal seguida das suas opções (mesmo bloco nas
    # abas alternativas), como no PDF real; a tabela é a da dieta principal.
    ordem = planilha.ordem_do_documento([(a["aba"], a["refeicoes"]) for a in resultado["abas"]])
    doc = {
        "profissional": dict(profissional),
        "paciente": {"nome": paciente["nome"], "objetivo": paciente.get("objetivo", "")},
        "data": data,
        "mostrar_numeros": mostrar_numeros,
        "opcoes": [{"rotulo": "Opção 1", "refeicoes": [
            {"nome": r["nome"], "horario": r.get("horario"),
             "itens": [_item_doc(i, trocas) for i in r["itens"]]}
            for r in ordem]}],
        "n_refeicoes": len(principal["refeicoes"]),
        "macros": principal["macros"],
        "total_kcal": principal["total_kcal"],
        "kcal_por_kg": principal["kcal_por_kg"],
        "observacoes": list(observacoes),
    }
    if micros:
        doc["micros"] = principal["micros"]
    if cor:
        doc["cor"] = cor
    if consistencia:
        doc["consistencia"] = consistencia
    return doc


def montar_html(dados):
    """
    dados: {
      profissional: {nome, crn, telefone, site, instagram, logo?},
      logo: caminho local PNG/JPEG/SVG ou data URI de imagem; ausente = sem logo,
      paciente: {nome, objetivo}, data: "26/07/2026",
      consistencia: "normal",
      opcoes: [ {rotulo, refeicoes:[{nome, horario, itens:[...]}]} , ...],
      macros: [...], total_kcal, kcal_por_kg,
      micros: [...] ou None,   mostrar_numeros: bool,
      observacoes: [str, ...],
      cor: nome de PALETAS (opcional; ausente = verde)  # R20.8
    }
    """
    prof = dados["profissional"]
    pac = dados["paciente"]
    mostrar = dados.get("mostrar_numeros", True)
    css = css_da_cor(dados.get("cor"))
    cor = (dados.get("cor") or COR_PADRAO).strip().lower()
    escuro = "#1b4036" if cor == "verde" else PALETAS[cor]["forte"]
    rod = [prof.get("telefone"), prof.get("site"), prof.get("instagram")]
    partes = ['<div class="rod">%s</div>' % "".join(
        '<span>%s</span>' % escape(r) for r in rod if r)]
    # Fixos aparecem em todas as páginas; somente os polígonos escuros aprovados.
    partes += [
        '<div class="canto topo"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 110 90"><polygon fill="%s" points="44,0 110,0 110,66"/></svg></div>' % escuro,
        '<div class="canto base"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 16"><polygon fill="%s" points="0,0 42,0 58,16 0,16"/></svg></div>' % escuro,
    ]
    if prof.get("logo"):
        partes.append('<div class="logo"><img alt="Logo do profissional" src="%s"></div>'
                      % escape(_logo_uri(prof["logo"]), quote=True))

    classe_pac = _tamanho_classe(pac["nome"], [(28, ""), (40, "m"), (999, "p")])
    partes.append('<div class="hero"><h1 class="%s">%s</h1><div class="s">%s</div></div>'
                  % (classe_pac, escape(pac["nome"]), escape(pac.get("objetivo", ""))))

    if mostrar:
        n_ref = dados.get("n_refeicoes") or max(len(o["refeicoes"]) for o in dados["opcoes"])
        pills = ["%s kcal/dia" % num(dados.get("total_kcal")),
                 "%d refeições" % n_ref]
        if dados.get("consistencia"):
            pills.append("Consistência %s" % dados["consistencia"])
        partes.append('<div class="pills">%s</div>'
                      % "".join('<span class="pill">%s</span>' % escape(p) for p in pills))

    varias = len(dados["opcoes"]) > 1
    for opcao in dados["opcoes"]:
        if varias:
            partes.append('<div class="opcao">%s</div>' % escape(opcao["rotulo"]))
        for ref in opcao["refeicoes"]:
            hora = (' <em>%s</em>' % escape(ref["horario"])) if ref.get("horario") else ""
            itens = "".join(_item_html(i) for i in ref["itens"])
            partes.append('<div class="bloco"><h2>%s%s</h2><ul>%s</ul></div>'
                          % (escape(ref["nome"]), hora, itens))

    if mostrar and dados.get("macros"):
        linhas = "".join(
            '<tr><td>%s</td><td class="n">%s</td><td class="n">%s</td>'
            '<td class="n">%s</td><td class="n">%s</td></tr>'
            % (escape(m["nome"]), com_unidade(m["gramas"], "g"),
               com_unidade(m["percentual"], "%"),
               com_unidade(m["kcal"], "kcal"),
               com_unidade(m["g_por_kg"], "g/kg", 1))
            for m in dados["macros"])
        # R20.4 — única linha de total, com o total de kcal; kcal/kg sai da tabela.
        partes.append(
            '<section class="nutrientes"><h3>Macronutrientes</h3>'
            '<table><thead><tr><th>Macronutriente</th><th class="n">g/dieta</th>'
            '<th class="n">%%/kcal</th><th class="n">kcal</th><th class="n">g/kg</th>'
            '</tr></thead><tbody>%s'
            '<tr class="t"><td>Total</td><td class="n">&mdash;</td>'
            '<td class="n">100 %%</td>'
            '<td class="n">%s</td><td class="n">&mdash;</td></tr></tbody></table></section>'
            % (linhas, com_unidade(dados.get("total_kcal"), "kcal")))

    if dados.get("micros"):
        # R9.15 (04/08/2026) — a adequação é conta pronta da própria planilha
        # (total ÷ recomendado), não estimativa: sempre mostrada, nunca travessão.
        linhas = "".join(
            '<tr><td>%s</td><td class="n">%s</td><td>%s</td>'
            '<td class="n">%s</td><td class="n">%s</td></tr>'
            % (escape(m["nome"]), num(m["total"], 1), escape(m.get("unidade", "")),
               num(m["idr"], 1), num((m["adequacao"] or 0) * 100) + "%")
            for m in dados["micros"])
        partes.append(
            '<section class="nutrientes"><h3>Micronutrientes</h3>'
            '<table><thead><tr><th>Micronutriente</th><th class="n">Total</th>'
            '<th>Unid.</th><th class="n">Recomendado</th><th class="n">Adequação</th>'
            '</tr></thead><tbody>%s</tbody></table></section>' % linhas)

    for obs in dados.get("observacoes", []):
        partes.append('<div class="obs">%s</div>' % escape(obs))

    # Assinatura no fluxo, uma única vez, ao final; contatos ficam no rodapé fixo.
    partes.append(
        '<div class="ass"><div class="linha"></div><div class="nome">%s</div>'
        '<div class="s">Nutricionista · %s</div><div class="s">Emitido em %s</div></div>'
        % (escape(prof["nome"]), escape(prof["crn"]), escape(dados["data"])))

    # R20.8 — a cor vem do perfil do profissional (dados["cor"]); sem ela, verde.
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<title>%s</title><style>%s</style></head><body>%s</body></html>'
            % (escape(pac["nome"]), css, "".join(partes)))


def _logo_uri(logo):
    logo = str(logo)
    if re.fullmatch(r"data:image/(?:png|jpeg|svg\+xml);base64,[A-Za-z0-9+/=\s]+", logo):
        return logo
    tipo = {".png": "png", ".jpg": "jpeg", ".jpeg": "jpeg", ".svg": "svg+xml"}.get(
        os.path.splitext(logo)[1].lower())
    if not tipo:
        raise ErroDocumento("A logo precisa ser uma imagem PNG, JPEG ou SVG local.")
    try:
        with open(logo, "rb") as f:
            conteudo = f.read()
    except OSError as erro:
        raise ErroDocumento("Não consegui abrir a logo do profissional. Confirme o arquivo antes de gerar o documento.") from erro
    return "data:image/%s;base64,%s" % (tipo, base64.b64encode(conteudo).decode("ascii"))


# ---------------------------------------------------------------- nome de arquivo

def sanear_nome(texto, limite=60):
    """R9.10 — nome de paciente virando nome de arquivo, sem quebrar o sistema."""
    limpo = _PROIBIDOS_NOME.sub("", str(texto or "").strip())
    limpo = re.sub(r"\s+", " ", limpo).strip(" .")
    if limpo.upper().split(".")[0] in _RESERVADOS:
        limpo = "_" + limpo
    limpo = limpo[:limite].strip(" .")
    return limpo or "paciente"


def pasta_e_sincronizada(caminho):
    baixo = str(caminho).lower()
    return any(p in baixo for p in PASTAS_NUVEM)


# ---------------------------------------------------------------- geração

def gerar_pdf(html, dados, destino, navegador, pasta_trabalho, timeout=120,
              weasyprint=None):
    """Gera em temporário, verifica e só então move (R9.16).

    R18.3 — a conferência roda por dentro, contra `dados` (nunca número
    formatado à mão pelo chamador). Reprovou, nem chega a acionar motor
    nenhum: sem `dados` válido não existe caminho de geração.

    R19.1 — `weasyprint`, quando informado (o interpretador achado por
    `ambiente.achar_weasyprint()`), é o motor preferido: no macOS o Chrome
    headless comprovadamente trava (03/08/2026) enquanto o WeasyPrint
    converte o mesmo HTML em frações de segundo. Sem `weasyprint`, a rota é
    a de sempre — o navegador — comportamento inalterado.
    """
    problemas = verificar_html(html, [], dados=dados)
    # O fluxo gera HTML exclusivamente por montar_html. Texto escondido ou
    # estilos alterados não podem liberar uma quantidade visível diferente.
    if html != montar_html(dados):
        problemas.append("o conteúdo ou o estilo foi alterado depois da montagem; monte o documento novamente")
    if problemas:
        raise ErroDocumento(
            "O documento não passou na conferência antes de virar PDF: %s."
            % "; ".join(problemas))

    entrada = os.path.join(pasta_trabalho, "dieta.html")
    with open(entrada, "w", encoding="utf-8") as f:
        f.write(html)
    saida_tmp = os.path.join(pasta_trabalho, "dieta.pdf")

    if weasyprint:
        pdf = _gerar_pdf_weasyprint(weasyprint, entrada, saida_tmp, timeout)
    else:
        pdf = _gerar_pdf_navegador(navegador, entrada, saida_tmp, pasta_trabalho, timeout)
    problemas = verificar_pdf(pdf, dados=dados, interpretador=weasyprint)
    if problemas:
        os.remove(pdf)
        raise ErroDocumento("O PDF não passou na conferência: %s. Nada foi entregue." % "; ".join(problemas))
    return pdf


def _gerar_pdf_weasyprint(interpretador, entrada, saida_tmp, timeout):
    """R19.3 — sempre em subprocesso, nunca por import direto na sessão."""
    cmd = [interpretador, "-m", "weasyprint", os.path.abspath(entrada),
           os.path.abspath(saida_tmp)]
    try:
        subprocess.run(cmd, timeout=timeout, capture_output=True)
    except subprocess.TimeoutExpired:
        raise ErroDocumento(
            "O WeasyPrint demorou demais para montar o PDF. Tente de novo.")

    if not os.path.exists(saida_tmp) or os.path.getsize(saida_tmp) < 1000:
        raise ErroDocumento(
            "Não consegui montar o PDF com o WeasyPrint. Verifique se ele "
            "está instalado corretamente.")
    return saida_tmp


def _gerar_pdf_navegador(navegador, entrada, saida_tmp, pasta_trabalho, timeout):
    perfil = os.path.join(pasta_trabalho, "perfil_nav")

    cmd = [navegador, "--headless", "--disable-gpu", "--no-pdf-header-footer",
           "--user-data-dir=" + perfil,
           "--print-to-pdf=" + os.path.abspath(saida_tmp), os.path.abspath(entrada)]
    try:
        subprocess.run(cmd, timeout=timeout, capture_output=True)
    except subprocess.TimeoutExpired:
        raise ErroDocumento(
            "O navegador demorou demais para montar o PDF. Tente de novo.")

    # o navegador devolve código 0 mesmo sem gerar o arquivo — conferimos o arquivo
    if not os.path.exists(saida_tmp) or os.path.getsize(saida_tmp) < 1000:
        raise ErroDocumento(
            "Não consegui montar o PDF. Verifique se o navegador está instalado "
            "corretamente.")
    return saida_tmp


def esperados_do_documento(dados):
    """
    R18.1 — deriva do MESMO `dados` que `montar_html` consome as strings que
    DEVEM aparecer no documento, com a MESMA formatação da montagem. O
    chamador nunca formata número à mão para conferir.

    Devolve pares (rótulo em português de leigo, texto esperado).
    """
    prof = dados["profissional"]
    pac = dados["paciente"]
    mostrar = dados.get("mostrar_numeros", True)

    esperados = [
        ("o nome do paciente", pac["nome"]),
        ("o nome do profissional", prof["nome"]),
        ("o CRN do profissional", prof["crn"]),
        ("a data", dados["data"]),
    ]

    if mostrar:
        esperados.append(
            ("o total de calorias", "%s kcal/dia" % num(dados.get("total_kcal"))))
        if dados.get("macros"):
            for m in dados["macros"]:
                linha = "%s %s %s %s %s" % (
                    m["nome"], com_unidade(m["gramas"], "g"),
                    com_unidade(m["percentual"], "%"),
                    com_unidade(m["kcal"], "kcal"),
                    com_unidade(m["g_por_kg"], "g/kg", 1))
                esperados.append(
                    ("a linha de %s na tabela de macronutrientes" % m["nome"], linha))

    # B4 — cada alimento com a sua quantidade, como o paciente vai ler
    for opcao in dados.get("opcoes", []):
        for ref in opcao["refeicoes"]:
            esperados.append(("a refeição e seu horário", "%s %s" % (ref["nome"], ref.get("horario") or "")))
            for item in ref["itens"]:
                texto = (linha_com_trocas(item) if item.get("trocas")
                         else "%s %s" % (item["alimento"], quantidade(item)))
                esperados.append(('o alimento "%s" (%s)' % (item["alimento"], quantidade(item)),
                                  texto))

    for m in dados.get("micros") or []:
        linha = "%s %s %s %s %s%%" % (
            m["nome"], num(m["total"], 1), m.get("unidade", ""),
            num(m["idr"], 1), num((m["adequacao"] or 0) * 100))
        esperados.append(("a linha de %s na tabela de micronutrientes" % m["nome"], linha))
    return esperados


def verificar_html(html, obrigatorios, valores=(), dados=None):
    """
    R9.17 — a última rede antes do paciente, aplicada ao HTML.

    Confere a montagem antes de renderizar. gerar_pdf() também confere o texto
    do PDF real por um leitor disponível, além da integridade do arquivo.
    """
    limpo = _limpa(unescape(re.sub(r"<[^>]+>", " ", html)))
    problemas = []
    if _ERRO_CELULA.search(limpo):
        problemas.append("o documento contém células com erro de cálculo")
    for termo in obrigatorios:
        if termo and _limpa(termo) not in limpo:
            problemas.append("não encontrei %r no documento" % termo)
    for v in valores:
        if not re.search(r"(?<![\d,.])%s(?![\d,.])" % re.escape(str(v)), limpo):
            problemas.append("o valor %r não apareceu como esperado" % v)
    if dados is not None:
        for rotulo, esperado in esperados_do_documento(dados):
            if _limpa(esperado) not in limpo:
                problemas.append("%s não apareceu como esperado no documento" % rotulo)
    # m1 — o marcador do modelo é "@KG" solto; "@JP.nutri" é Instagram
    if re.search(r"@[A-Z]{1,4}(?![\w.\-])", html):
        problemas.append("sobrou um marcador de modelo sem substituir")
    return problemas


_PAGINA = re.compile(rb"/Type\s*/Page(?![a-zA-Z])")
# Um byte CR pode pertencer ao zlib, não à quebra de linha do PDF.
# zlib aceita o CR extra de uma terminação CRLF; não remover byte comprimido.
_STREAM = re.compile(rb"stream\r?\n(.*?)\nendstream", re.S)


def contar_paginas(caminho):
    """
    B4 — o WeasyPrint guarda as páginas dentro de trechos comprimidos do PDF;
    procurar só no arquivo cru achava zero e a função devolvia 1. Aqui os
    trechos comprimidos são abertos também. Não achou nenhuma página: None
    (desconhecido), nunca um número inventado.
    """
    with open(caminho, "rb") as f:
        bruto = f.read()
    n = len(_PAGINA.findall(bruto))
    for trecho in _STREAM.findall(bruto):
        try:
            n += len(_PAGINA.findall(zlib.decompress(trecho)))
        except zlib.error:
            continue
    return n or None


def verificar_pdf(caminho, maximo_paginas=None, dados=None, interpretador=None):
    """Integridade, páginas e, quando dados é informado, conteúdo do PDF real."""
    problemas = []
    if not os.path.exists(caminho):
        return ["o arquivo do PDF não foi criado"]
    if os.path.getsize(caminho) < 1000:
        problemas.append("o PDF saiu vazio")
    with open(caminho, "rb") as f:
        if f.read(5) != b"%PDF-":
            problemas.append("o arquivo gerado não é um PDF válido")
    paginas = contar_paginas(caminho)
    if paginas is None:
        problemas.append("não consegui contar as páginas do PDF")
    elif maximo_paginas is not None and paginas > maximo_paginas:
        problemas.append("o documento ficou com %d páginas (esperava até %d)"
                         % (paginas, maximo_paginas))
    if dados is not None and not problemas:
        texto = _texto_pdf(caminho, interpretador)
        if texto is None:
            problemas.append("não consegui conferir o conteúdo do PDF com os leitores disponíveis; envie este erro ao suporte")
        else:
            limpo = _limpa(texto)
            for rotulo, esperado in esperados_do_documento(dados):
                if _limpa(esperado) not in limpo:
                    problemas.append("%s não apareceu como esperado no PDF" % rotulo)
    return problemas


def _texto_pdf(caminho, interpretador=None):
    """Leitores já disponíveis; não instala e não altera a sessão Python."""
    script = ("import sys; from pypdf import PdfReader; "
              "print('\\n'.join(p.extract_text() or '' for p in PdfReader(sys.argv[1]).pages))")
    for python in dict.fromkeys([interpretador, sys.executable]):
        if not python:
            continue
        try:
            r = subprocess.run([python, "-c", script, caminho], capture_output=True,
                               text=True, encoding="utf-8", timeout=30)
            if r.returncode == 0:
                return r.stdout
        except (OSError, subprocess.TimeoutExpired):
            pass
    leitor = shutil.which("pdftotext")
    if leitor:
        try:
            r = subprocess.run([leitor, "-layout", caminho, "-"], capture_output=True,
                               text=True, encoding="utf-8", timeout=30)
            if r.returncode == 0:
                return r.stdout
        except (OSError, subprocess.TimeoutExpired):
            pass
    return None


def _limpa(s):
    return re.sub(r"\s+", " ", str(s)).strip().lower()


LIMITE_CAMINHO_WINDOWS = 255


def data_curta(data):
    """DD-MM-AA, o formato pedido pelo Cassiano. Aceita date ou 'DD/MM/AAAA'."""
    if hasattr(data, "strftime"):
        return data.strftime("%d-%m-%y")
    partes = re.split(r"[/\-.]", str(data).strip())
    if len(partes) == 3:
        d, m, a = partes
        return "%s-%s-%s" % (d.zfill(2), m.zfill(2), a[-2:])
    return str(data).replace("/", "-")


def nome_do_documento(nome_paciente, objetivo, data, espaco_da_pasta=0):
    """
    "Nome do Paciente - Objetivo DD-MM-AA.pdf".

    O objetivo é texto livre ditado na consulta, então tudo pode aparecer nele:
    barra ("emagrecimento / redução de gordura"), frase inteira, ou nada. Barra e
    companhia saem no saneamento; frase longa é encurtada, porque o caminho
    completo — pasta do consultório + pasta do paciente + este nome — tem teto de
    255 caracteres no Windows, e a pasta costuma estar dentro do Google Drive.
    Objetivo vazio simplesmente não aparece, em vez de deixar um traço solto.
    """
    paciente = sanear_nome(nome_paciente)
    alvo = sanear_nome(objetivo, limite=80) if objetivo else ""
    dia = data_curta(data)

    folga = LIMITE_CAMINHO_WINDOWS - espaco_da_pasta - len(paciente) - len(dia) - 8
    if alvo and len(alvo) > max(folga, 0):
        alvo = alvo[:max(folga, 0)].strip(" .")

    meio = " - %s " % alvo if alvo else " - "
    return "%s%s%s.pdf" % (paciente, meio, dia)


MAXIMO_PAGINAS = 3


def entregar(pdf_temporario, pasta_destino, nome_paciente, objetivo, data,
             maximo_paginas=MAXIMO_PAGINAS):
    """
    Publica o PDF na pasta do paciente — e esta é a ÚLTIMA operação do fluxo.

    Publicar por último é o que impede o estado "documento novo, planilha antiga":
    se a energia cair antes daqui, a planilha já está gravada e regerar o PDF
    custa segundos. O contrário deixaria o paciente com um documento que não bate
    com o que ficou registrado.

    A troca final usa os.replace dentro da PASTA DE DESTINO, e não shutil.move a
    partir do temporário do sistema: os dois estão em volumes diferentes (o
    temporário no disco local, a pasta do paciente no Google Drive), e ali move
    vira cópia-e-apaga, que pode ser interrompida no meio. Copiar para um arquivo
    de passagem ao lado do destino e trocar o nome no mesmo volume é atômico.
    """
    nome = nome_do_documento(nome_paciente, objetivo, data,
                             espaco_da_pasta=len(pasta_destino))
    destino = os.path.join(pasta_destino, nome)
    n = 2
    while os.path.exists(destino):
        destino = os.path.join(pasta_destino, nome[:-4] + " (%d).pdf" % n)
        n += 1

    passagem = destino + ".parcial"
    shutil.copy2(pdf_temporario, passagem)
    problemas = verificar_pdf(passagem, maximo_paginas)   # confere o arquivo QUE CHEGOU
    if problemas:
        try:
            os.remove(passagem)
        except OSError:
            pass
        raise ErroDocumento(
            "O documento não chegou inteiro na pasta do paciente (%s). Nada foi "
            "salvo com o nome final. Tente de novo." % problemas[0])
    os.replace(passagem, destino)
    try:
        os.remove(pdf_temporario)
    except OSError:
        pass
    return destino
