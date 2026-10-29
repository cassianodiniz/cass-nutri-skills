# -*- coding: utf-8 -*-
"""
Ambiente: encontrar (ou instalar) LibreOffice e navegador, e guardar o cadastro
profissional.

Regras que governam este módulo:
  - nunca instalar nada sem o usuário mandar (P8)
  - nunca executar comando com elevação nem pedir senha (R1.8)
  - nenhum link de download com versão fixa (P9) — a versão é descoberta na hora
  - o que for baixado direto é conferido antes de rodar (R1.7)
"""
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request

INDICE_LIBREOFFICE = "https://download.documentfoundation.org/libreoffice/stable/"

CAMINHOS_LIBREOFFICE = {
    "win32": [r"C:\Program Files\LibreOffice\program\soffice.exe",
              r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"],
    "darwin": ["/Applications/LibreOffice.app/Contents/MacOS/soffice"],
    "linux": ["/usr/bin/soffice", "/usr/bin/libreoffice",
              "/usr/local/bin/soffice", "/snap/bin/libreoffice",
              "/var/lib/flatpak/exports/bin/org.libreoffice.LibreOffice",
              os.path.expanduser("~/.local/share/flatpak/exports/bin/"
                                 "org.libreoffice.LibreOffice")],
}
CAMINHOS_NAVEGADOR = {
    # Edge primeiro no Windows: vem de fábrica, então quase sempre resolve
    "win32": [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    "darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
               "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
               "/Applications/Chromium.app/Contents/MacOS/Chromium"],
    "linux": ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
              "/usr/bin/chromium", "/usr/bin/chromium-browser",
              "/usr/bin/microsoft-edge", "/snap/bin/chromium"],
}

def _casa():
    """
    Costura de teste (R16) — NÃO remover por "limpeza".

    Com CASS_DIETA_CASA definida, toda descoberta de pastas parte dela e a skill
    fica cega para a máquina real — é o que permite o eval de condução rodar numa
    arena com iscas, sem nenhum risco às pastas de pacientes de verdade. No uso
    normal a variável não existe e nada muda.
    """
    return os.environ.get("CASS_DIETA_CASA") or os.path.expanduser("~")


PASTA_USUARIO = os.path.join(_casa(), ".cass-dieta")
ARQUIVO_PERFIS = os.path.join(PASTA_USUARIO, "perfis.json")

CAMPOS_PERFIL = ["nome", "crn"]
CAMPOS_OPCIONAIS = ["telefone", "site", "instagram", "endereco"]


class ErroAmbiente(Exception):
    """Mensagem já escrita para leigo."""


# ---------------------------------------------------------------- localizar

def _procurar(caminhos):
    for c in caminhos.get(sys.platform, caminhos.get("linux", [])):
        if os.path.exists(c):
            return c
    return None


def achar_libreoffice():
    return _procurar(CAMINHOS_LIBREOFFICE)


def achar_navegador():
    return _procurar(CAMINHOS_NAVEGADOR)


VENV_WEASYPRINT = os.path.join(PASTA_USUARIO, "weasyprint-venv")


def _python_do_venv(pasta_venv):
    if sys.platform == "win32":
        return os.path.join(pasta_venv, "Scripts", "python.exe")
    return os.path.join(pasta_venv, "bin", "python")


def _importa_weasyprint(interpretador, timeout=15):
    """R19.2 — a única prova válida é rodar de verdade, nunca checar caminho."""
    if not interpretador or not os.path.exists(interpretador):
        return False
    try:
        r = subprocess.run([interpretador, "-c", "import weasyprint"],
                           timeout=timeout, capture_output=True)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


def achar_weasyprint():
    """
    R19.2/R19.3 — devolve o caminho de um interpretador Python que importa
    `weasyprint` de verdade, testado via subprocesso (nunca por existência de
    caminho, e nunca por import direto no Python da sessão: no macOS o Python
    do sistema não carrega as bibliotecas nativas do WeasyPrint).
    """
    candidatos = [_python_do_venv(VENV_WEASYPRINT), sys.executable]
    from shutil import which
    for nome in ("python3", "py"):
        c = which(nome)
        if c:
            candidatos.append(c)
    candidatos.append("/opt/homebrew/bin/python3")
    for c in candidatos:
        if c and _importa_weasyprint(c):
            return c
    return None


def instrucoes_de_instalacao_weasyprint():
    """
    O que a skill DIZ ao usuário para instalar o WeasyPrint (R19.4/R19.5).
    Sem sudo, sem senha (R1.8) — o Homebrew instala pango sem elevação, e o
    venv é criado na pasta do usuário.
    """
    passos = []
    if sys.platform == "darwin":
        passos.append({
            "tipo": "automatico",
            "comando": ["brew", "install", "pango"],
            "explicacao": "No Mac, o Chrome headless às vezes trava para gerar "
                          "o PDF. Vou instalar o WeasyPrint, que é mais rápido e "
                          "confiável — primeiro uma biblioteca de texto (pango) "
                          "pelo Homebrew, sem pedir sua senha.",
        })
    passos.append({
        "tipo": "automatico",
        "comando": [sys.executable, "-m", "venv", VENV_WEASYPRINT],
        "explicacao": "Depois crio um ambiente Python isolado só para o "
                      "WeasyPrint, na pasta de dados da skill (.cass-dieta, "
                      "dentro da sua pasta de usuário) — não mexe no resto do "
                      "seu computador.",
    })
    passos.append({
        "tipo": "automatico",
        "comando": [_python_do_venv(VENV_WEASYPRINT), "-m", "pip", "install",
                    "weasyprint"],
        "explicacao": "E instalo o WeasyPrint dentro desse ambiente.",
    })
    return passos


def _bases_para_venv():
    """
    Interpretadores candidatos a BASE do venv do WeasyPrint, na ordem de tentativa.

    No macOS o Python do sistema (Command Line Tools) não carrega as bibliotecas
    nativas do Homebrew (libgobject) mesmo com elas instaladas — um venv criado
    dele nasce cego e a conferência falha. Bug real pego no eval de 04/08/2026:
    `sys.executable` era o do sistema e a instalação inteira falhava. Por isso o
    Homebrew vem primeiro no Mac; `sys.executable` fica de reserva.
    """
    candidatos = []
    if sys.platform == "darwin":
        candidatos += ["/opt/homebrew/bin/python3", "/usr/local/bin/python3"]
    candidatos.append(sys.executable)
    vistos, unicos = set(), []
    for c in candidatos:
        if c and c not in vistos and os.path.exists(c):
            vistos.add(c)
            unicos.append(c)
    return unicos or [sys.executable]


def instalar_weasyprint(timeout=180, venv=None, bases=None):
    """
    Executa os passos automáticos de `instrucoes_de_instalacao_weasyprint()` e
    devolve o interpretador do venv criado (ou levanta ErroAmbiente).

    A instalação só é dada por boa PELO RESULTADO: o venv precisa importar o
    weasyprint de verdade. Falhou com uma base, o venv é refeito com a próxima —
    é o que conserta o venv cego herdado de uma tentativa anterior.
    """
    venv = venv or VENV_WEASYPRINT
    if sys.platform == "darwin":
        try:
            subprocess.run(["brew", "install", "pango"],
                           timeout=timeout, capture_output=True)
        except (OSError, subprocess.TimeoutExpired):
            pass  # pode já estar instalado, ou o Homebrew pode faltar — segue

    erros = []
    for base in (bases or _bases_para_venv()):
        interpretador = _python_do_venv(venv)
        try:
            if os.path.isdir(venv):
                shutil.rmtree(venv, ignore_errors=True)
            subprocess.run([base, "-m", "venv", venv],
                           timeout=timeout, capture_output=True, check=True)
            subprocess.run([interpretador, "-m", "pip", "install", "weasyprint"],
                           timeout=timeout, capture_output=True, check=True)
        except (OSError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired) as e:
            erros.append("%s: %s" % (base, e))
            continue
        try:
            importa = subprocess.run(
                [interpretador, "-c", "import weasyprint"],
                timeout=60, capture_output=True).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            importa = False
        if importa:
            return interpretador
        erros.append("%s: o ambiente criado não consegue carregar o WeasyPrint"
                     % base)
    raise ErroAmbiente(
        "Não consegui instalar o WeasyPrint (%s)." % "; ".join(erros[:3]))


def conferir_weasyprint(interpretador, pasta_teste, timeout=30):
    """R19.6 — espelha conferir_libreoffice: não basta instalar, tem que gerar PDF de verdade."""
    entrada = os.path.join(pasta_teste, "teste_weasyprint.html")
    saida = os.path.join(pasta_teste, "teste_weasyprint.pdf")
    with open(entrada, "w", encoding="utf-8") as f:
        f.write("<html><body><p>teste</p></body></html>")
    try:
        subprocess.run([interpretador, "-m", "weasyprint", entrada, saida],
                       timeout=timeout, capture_output=True)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return os.path.exists(saida) and os.path.getsize(saida) > 1000


def conferir_libreoffice(caminho, pasta_teste, timeout=120):
    """R1.6 — não basta existir: tem que responder."""
    amostra = os.path.join(pasta_teste, "teste.csv")
    with open(amostra, "w", encoding="utf-8") as f:
        f.write("a,b\n1,2\n")
    perfil = os.path.join(pasta_teste, "perfil_teste")
    url = "file:///" + perfil.replace("\\", "/").lstrip("/")
    try:
        subprocess.run(
            [caminho, "--headless", "--norestore", "--nolockcheck",
             "-env:UserInstallation=" + url,
             "--convert-to", "xlsx", "--outdir", pasta_teste, amostra],
            timeout=timeout, capture_output=True)
    except (subprocess.TimeoutExpired, OSError):
        return False
    return os.path.exists(os.path.join(pasta_teste, "teste.xlsx"))


# ---------------------------------------------------------------- instalar

def comando_gerenciador():
    """
    Comando do gerenciador de pacotes do sistema — a via preferida, porque ele
    já confere assinatura e sempre pega a versão vigente.
    Devolve (lista_do_comando, precisa_de_senha).
    """
    if sys.platform == "win32":
        return (["winget", "install", "-e", "--id",
                 "TheDocumentFoundation.LibreOffice", "--scope", "user",
                 "--accept-package-agreements", "--accept-source-agreements"], False)
    if sys.platform == "darwin":
        return (["brew", "install", "--cask", "libreoffice"], False)
    for gerenciador, comando in [
            ("flatpak", ["flatpak", "install", "-y", "flathub",
                         "org.libreoffice.LibreOffice"]),
            ("apt", ["sudo", "apt", "install", "-y", "libreoffice-calc"]),
            ("dnf", ["sudo", "dnf", "install", "-y", "libreoffice-calc"])]:
        if _existe_programa(gerenciador):
            return (comando, comando[0] == "sudo")
    return (None, False)


def _existe_programa(nome):
    from shutil import which
    return which(nome) is not None


def descobrir_versao_vigente(timeout=30):
    """
    P9 — a versão NUNCA é fixa no código. Os links da 26.2.5 funcionavam em
    26/07/2026, mas a Document Foundation move versões antigas para o arquivo:
    as 26.2.0 e 26.2.1 já saíram. Aqui a versão é lida na hora.
    """
    try:
        with urllib.request.urlopen(INDICE_LIBREOFFICE, timeout=timeout) as r:
            pagina = r.read().decode("utf-8", "replace")
    except Exception:
        return None
    versoes = set(re.findall(r'href="(\d+\.\d+\.\d+)/"', pagina))
    if not versoes:
        return None
    return max(versoes, key=lambda v: tuple(int(p) for p in v.split(".")))


def url_do_instalador(versao):
    """Monta a URL a partir da versão descoberta — nunca gravada no código."""
    base = INDICE_LIBREOFFICE + versao
    if sys.platform == "win32":
        return "%s/win/x86_64/LibreOffice_%s_Win_x86-64.msi" % (base, versao)
    if sys.platform == "darwin":
        arq = "aarch64" if _mac_arm() else "x86_64"
        nome = "LibreOffice_%s_MacOS_%s.dmg" % (versao, arq)
        return "%s/mac/%s/%s" % (base, arq, nome)
    return "%s/deb/x86_64/LibreOffice_%s_Linux_x86-64_deb.tar.gz" % (base, versao)


def _mac_arm():
    try:
        import platform
        return platform.machine() in ("arm64", "aarch64")
    except Exception:
        return False


def conferir_integridade(caminho_arquivo, url_original, timeout=60):
    """
    R1.7 — o que foi baixado é mesmo o oficial?
    O índice de onde a URL saiu é conteúdo de rede; sem esta conferência, uma
    rede comprometida entregaria um instalador qualquer para ser executado.
    """
    import hashlib
    try:
        with urllib.request.urlopen(url_original + ".sha256", timeout=timeout) as r:
            publicado = r.read().decode("utf-8", "replace").split()[0].strip()
    except Exception:
        return (False, "não consegui baixar a soma de verificação oficial")

    h = hashlib.sha256()
    with open(caminho_arquivo, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    if h.hexdigest().lower() != publicado.lower():
        return (False, "o arquivo baixado não confere com o oficial — sua rede "
                       "pode estar interferindo")
    return (True, None)


def instrucoes_de_instalacao():
    """
    O que a skill DIZ ao usuário. Ela nunca roda comando com senha (R1.8):
    quando é preciso, mostra a linha para a pessoa colar no terminal dela.
    """
    comando, precisa_senha = comando_gerenciador()
    passos = []
    if comando and not precisa_senha:
        passos.append({
            "tipo": "automatico",
            "comando": comando,
            "explicacao": "Vou instalar o LibreOffice pelo instalador do próprio "
                          "sistema. Pode aparecer uma janela pedindo permissão — "
                          "é normal, pode aceitar. São cerca de 350 MB, então "
                          "leva alguns minutos.",
        })
    elif comando and precisa_senha:
        passos.append({
            "tipo": "manual",
            "comando": comando,
            "explicacao": "Este comando precisa da sua senha de administrador, e "
                          "eu não peço senha. Copie a linha abaixo, cole no seu "
                          "terminal e digite a senha quando ele pedir.",
        })
    versao = descobrir_versao_vigente()
    if versao:
        passos.append({
            "tipo": "download",
            "url": url_do_instalador(versao),
            "versao": versao,
            "explicacao": "Se preferir, baixo o instalador oficial (versão %s) e "
                          "confiro se o arquivo é autêntico antes de abrir."
                          % versao,
        })
    passos.append({
        "tipo": "manual_navegador",
        "url": "https://www.libreoffice.org/download/download-libreoffice/",
        "explicacao": "Último caminho: abro a página oficial no seu navegador e "
                      "te acompanho passo a passo.",
    })
    return passos


# ---------------------------------------------------------------- perfis

def _garantir_pasta():
    if not os.path.isdir(PASTA_USUARIO):
        os.makedirs(PASTA_USUARIO, exist_ok=True)
        if sys.platform != "win32":
            try:
                os.chmod(PASTA_USUARIO, 0o700)
            except OSError:
                pass


def chave_crn(crn):
    """
    B3 — o que identifica o nutricionista é o número do CRN, não a grafia:
    "CRN 108212", "108212", "CRN 10 8212" e "CRN 108212 " são a mesma pessoa.
    """
    digitos = re.sub(r"\D", "", str(crn or ""))
    return digitos or str(crn or "").strip().lower()


def _juntar_mesmo_crn(perfis):
    """
    Perfis com o mesmo número viram um só quando não divergem em nada: o nome é
    o mesmo e nenhum campo tem dois valores diferentes. Divergiu, ficam
    separados — e a skill continua perguntando quem está emitindo.
    """
    grupos = {}
    for p in perfis:
        grupos.setdefault(chave_crn(p.get("crn")), []).append(p)
    saida, juntou = [], False
    for chave, grupo in grupos.items():
        if len(grupo) == 1:
            saida.append(grupo[0])
            continue
        campos = {}
        conflito = False
        for p in sorted(grupo, key=len, reverse=True):
            for k, v in p.items():
                if str(v).strip() == "":
                    continue
                if k in campos and str(campos[k]).strip().lower() != str(v).strip().lower():
                    if k != "crn":
                        conflito = True
                    continue
                campos.setdefault(k, v)
        if conflito:
            saida.extend(grupo)
        else:
            saida.append(campos)
            juntou = True
    return saida, juntou


def carregar_perfis():
    if not os.path.exists(ARQUIVO_PERFIS):
        return []
    try:
        with open(ARQUIVO_PERFIS, encoding="utf-8") as f:
            dados = json.load(f)
    except (ValueError, OSError):
        return []
    perfis = dados if isinstance(dados, list) else [dados]
    perfis, juntou = _juntar_mesmo_crn(perfis)
    if juntou:
        shutil.copy2(ARQUIVO_PERFIS, ARQUIVO_PERFIS + ".bak")
        salvar_perfis(perfis)
    return perfis


def salvar_perfis(perfis):
    _garantir_pasta()
    tmp = ARQUIVO_PERFIS + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(perfis, f, ensure_ascii=False, indent=1)
    os.replace(tmp, ARQUIVO_PERFIS)


def perfil_valido(perfil):
    return bool(perfil) and all(str(perfil.get(c, "")).strip() for c in CAMPOS_PERFIL)


def campos_faltando(perfil):
    return [c for c in CAMPOS_PERFIL if not str((perfil or {}).get(c, "")).strip()]


def adicionar_perfil(perfil):
    faltando = campos_faltando(perfil)
    if faltando:
        raise ErroAmbiente(
            "Para emitir uma prescrição preciso de %s."
            % " e ".join({"nome": "seu nome completo",
                          "crn": "seu número de CRN com a região"}[c]
                         for c in faltando))
    perfis = carregar_perfis()
    for i, p in enumerate(perfis):
        if chave_crn(p.get("crn")) == chave_crn(perfil["crn"]):
            atualizado = dict(p)
            atualizado.update({k: v for k, v in perfil.items() if str(v).strip() != ""})
            perfis[i] = atualizado
            salvar_perfis(perfis)
            return atualizado
    perfis.append(perfil)
    salvar_perfis(perfis)
    return perfil


def remover_perfil(crn):
    perfis = [p for p in carregar_perfis() if chave_crn(p.get("crn")) != chave_crn(crn)]
    salvar_perfis(perfis)
    return perfis


def arquivo_alimentos(perfil):
    """Catálogo por profissional: o de um não entra nas dietas do outro."""
    return _arquivo_do_perfil(perfil, "alimentos")


def arquivo_refeicoes(perfil):
    """Refeições modelo, também por profissional — pelo mesmo motivo: um modelo
    aponta para alimentos do cadastro de quem o criou."""
    return _arquivo_do_perfil(perfil, "refeicoes")


def arquivo_trocas(perfil):
    """
    Trocas proporcionais, também por profissional (a proporção é dele). No primeiro
    uso o arquivo nasce do kit de exemplo; depois é só dele — o que ele apagar
    não volta.
    """
    caminho = _arquivo_do_perfil(perfil, "trocas")
    if not os.path.exists(caminho):
        import trocas
        tmp = caminho + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(trocas.carregar_kit(), f, ensure_ascii=False, indent=1)
        os.replace(tmp, caminho)
    return caminho


def falta_avisar_substituicoes(perfil):
    """A frase "se quiser substituições, é só me pedir" sai uma vez por profissional."""
    return not (perfil or {}).get("avisou_substituicoes")


def marcar_aviso_substituicoes(perfil):
    adicionar_perfil(dict(perfil, avisou_substituicoes=True))


def _arquivo_do_perfil(perfil, tipo):
    _garantir_pasta()
    chave = chave_crn((perfil or {}).get("crn", "sem-crn"))
    seguro = re.sub(r"[^A-Za-z0-9_-]", "_", chave)
    destino = os.path.join(PASTA_USUARIO, "%s-%s.json" % (tipo, seguro))
    _juntar_arquivos_antigos(tipo, chave, destino)
    return destino


JUNTADO = ".antes-de-juntar"


def _juntar_arquivos_antigos(tipo, chave, destino):
    """
    B3 — antes, o nome do arquivo saía da grafia do CRN ("alimentos-CRN_108212",
    "alimentos-108212"). Os arquivos antigos do mesmo número são juntados no
    novo, sem perder nada: cada original fica guardado com JUNTADO no nome.
    O mesmo item com conteúdo diferente em dois arquivos não é escolhido —
    a junção para e pede a decisão.
    """
    prefixo = tipo + "-"
    antigos = []
    for nome in sorted(os.listdir(PASTA_USUARIO)):
        caminho = os.path.join(PASTA_USUARIO, nome)
        if (not nome.startswith(prefixo) or not nome.endswith(".json") or JUNTADO in nome
                or caminho == destino):
            continue
        if chave_crn(nome[len(prefixo):-len(".json")]) == chave:
            antigos.append(caminho)
    if not antigos:
        return
    juntos, de_onde = {}, {}
    for caminho in ([destino] if os.path.exists(destino) else []) + antigos:
        with open(caminho, encoding="utf-8") as f:
            itens = json.load(f)
        for item in itens if isinstance(itens, list) else []:
            nome_item = str(item.get("nome", "")).strip().lower()
            if nome_item in juntos and juntos[nome_item] != item:
                raise ErroAmbiente(
                    'Encontrei "%s" duas vezes no seu cadastro, com dados diferentes '
                    "(em %s e %s). Qual dos dois vale?"
                    % (item.get("nome"), os.path.basename(de_onde[nome_item]),
                       os.path.basename(caminho)))
            juntos[nome_item] = item
            de_onde[nome_item] = caminho
    for caminho in ([destino] if os.path.exists(destino) else []) + antigos:
        shutil.copy2(caminho, caminho[:-len(".json")] + JUNTADO + ".json")
    tmp = destino + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(list(juntos.values()), f, ensure_ascii=False, indent=1)
    os.replace(tmp, destino)
    for caminho in antigos:
        os.remove(caminho)


# ---------------------------------------------------------------- consultório

def pasta_documentos():
    """
    A pasta Documentos de verdade — não o palpite.

    No Windows ela é lida do registro, porque "Documentos" costuma estar
    redirecionada para o OneDrive e o caminho no disco raramente é o óbvio.
    Medido em 28/07/2026 numa máquina real: existiam ~/Documents E
    ~/OneDrive/Documentos ao mesmo tempo, com o registro apontando para a
    primeira. Chutar acertaria por sorte e erraria em quem tem redirecionamento
    ativo — o usuário procuraria o arquivo numa pasta e ele estaria na outra.
    """
    desvio = os.environ.get("CASS_DIETA_CASA")
    if desvio:
        # R16: casa desviada — o registro apontaria para a máquina real,
        # que o eval não pode enxergar.
        for nome in ("Documents", "Documentos"):
            caminho = os.path.join(desvio, nome)
            if os.path.isdir(caminho):
                return caminho
        return desvio
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Explorer"
                    r"\Shell Folders") as k:
                caminho = winreg.QueryValueEx(k, "Personal")[0]
            caminho = os.path.expandvars(caminho)
            if os.path.isdir(caminho):
                return caminho
        except (ImportError, OSError, ValueError):
            pass
    for nome in ("Documents", "Documentos"):
        caminho = os.path.join(os.path.expanduser("~"), nome)
        if os.path.isdir(caminho):
            return caminho
    return os.path.expanduser("~")


def documentos_alternativos():
    """
    Outras pastas "Documentos" que existem na máquina.

    Quando há mais de uma, o padrão precisa ser CONFIRMADO em vez de assumido:
    quem tem OneDrive costuma chamar de "Documentos" a do OneDrive, que pode não
    ser a que o sistema reporta.
    """
    principal = os.path.normcase(pasta_documentos())
    achadas = []
    casa = _casa()
    for relativo in ("Documents", "Documentos",
                     os.path.join("OneDrive", "Documentos"),
                     os.path.join("OneDrive", "Documents")):
        caminho = os.path.join(casa, relativo)
        if os.path.isdir(caminho) and os.path.normcase(caminho) != principal:
            achadas.append(caminho)
    return achadas


# Palavras-raiz, sem acento de propósito: "consult" cobre consultório e
# consultorio. Falso positivo é barato — aparece uma pasta a mais na lista e
# ele descarta. Falso negativo é caro: é a pasta duplicada nascendo.
RAIZES_DE_CONSULTORIO = ("paciente", "consult", "atendimento")


def consultorios_candidatos(perfil=None, bases=None):
    """
    Pastas de pacientes que JÁ existem na máquina (R12.1).

    Sem isto, "você já tem uma pasta onde guarda seus pacientes?" é uma pergunta
    que o nutricionista leigo não sabe responder com um caminho, e a skill acaba
    criando outra ao lado da que ele usa. Aconteceu de verdade em 31/07/2026:
    "Documents\\Pacientes - Cassiano Diniz" nasceu a um palmo de
    "Documents\\Pacientes", que já tinha paciente com contrato dentro.

    Procura um nível abaixo dos lugares onde uma pasta dessas costuma estar, e
    devolve as de mais gente primeiro — a mais cheia é quase sempre a de verdade.
    **Nunca escolhe**: quem escolhe é o nutricionista (R12.2).
    """
    from paciente import listar               # local: evita import circular

    if bases is None:
        casa = _casa()
        bases = ([pasta_documentos()] + documentos_alternativos()
                 + [casa, os.path.join(casa, "Desktop"),
                    os.path.join(casa, "Área de Trabalho")])
    registrada = os.path.normcase(consultorio(perfil) or "\0") if perfil else "\0"

    achadas, vistos = [], set()
    for base in bases:
        try:
            nomes = os.listdir(base)
        except OSError:
            continue                          # base que não existe não é erro
        for nome in nomes:
            if not any(r in nome.lower() for r in RAIZES_DE_CONSULTORIO):
                continue
            caminho = os.path.abspath(os.path.join(base, nome))
            marca = os.path.normcase(caminho)
            if marca in vistos or not os.path.isdir(caminho):
                continue
            vistos.add(marca)
            achadas.append({"caminho": caminho,
                            "pacientes": listar(caminho),
                            "registrada": marca == registrada})
    achadas.sort(key=lambda c: (-len(c["pacientes"]), c["caminho"]))
    return achadas


def nome_do_consultorio(perfil):
    from documento import sanear_nome        # local: evita import circular
    return "Pacientes - %s" % sanear_nome(perfil.get("nome", ""), limite=40)


def caminho_padrao_consultorio(perfil, base=None):
    return os.path.join(base or pasta_documentos(), nome_do_consultorio(perfil))


def consultorio(perfil):
    """A pasta registrada para este profissional, ou None se ainda não houver."""
    caminho = (perfil or {}).get("consultorio")
    return caminho or None


def definir_consultorio(perfil, caminho):
    """Registra a pasta no perfil e persiste. Não cria a pasta — quem cria é criar_consultorio."""
    novo = dict(perfil)
    novo["consultorio"] = os.path.abspath(os.path.expanduser(caminho))
    return adicionar_perfil(novo)


def criar_consultorio(caminho):
    """Cria a pasta. Já existir não é erro — pode ser uma que ele já usava."""
    caminho = os.path.abspath(os.path.expanduser(caminho))
    try:
        os.makedirs(caminho, exist_ok=True)
    except OSError as e:
        raise ErroAmbiente(
            "Não consegui criar a pasta em %s (%s). Escolha outro lugar, ou "
            "crie a pasta pelo explorador de arquivos e me diga onde ficou."
            % (caminho, e.strerror or "motivo desconhecido"))
    return caminho


def abrir_pasta(caminho):
    """
    Abre a pasta no explorador de arquivos do sistema.

    Terminar um atendimento e só DIZER onde o arquivo ficou não serve para quem
    não tem familiaridade com computador: caminho escrito é instrução de tarefa,
    pasta aberta é o trabalho pronto na frente da pessoa.

    Nunca abre o arquivo em si — só a pasta. Abrir o PDF dispara o leitor padrão,
    e abrir a planilha a deixaria travada para o próximo cálculo.
    """
    caminho = os.path.abspath(caminho)
    if not os.path.isdir(caminho):
        return False
    try:
        if sys.platform == "win32":
            subprocess.Popen(["explorer", caminho])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", caminho])
        else:
            subprocess.Popen(["xdg-open", caminho])
    except OSError:
        return False        # sem explorador (servidor, sessão sem tela) não é erro
    return True


def conferir_consultorio(perfil):
    """
    A pasta registrada ainda está lá? Devolve os problemas em português.

    Sumir quer dizer que ele MOVEU a pasta — arrastou para o Drive, renomeou,
    trocou de computador. Criar outra em silêncio seria o pior desfecho: ele
    ficaria com duas, meio histórico em cada, sem entender por quê.
    """
    caminho = consultorio(perfil)
    if not caminho:
        return ["ainda não sei onde você guarda seus pacientes"]
    if not os.path.isdir(caminho):
        return ["não encontrei mais a pasta dos seus pacientes onde ela estava "
                "(%s) — você moveu ou renomeou?" % caminho]
    if not os.access(caminho, os.W_OK):
        return ["encontrei a pasta dos seus pacientes, mas não consigo gravar "
                "nela (%s)" % caminho]
    return []


def perfil_unico(perfis):
    """
    O perfil a usar sem perguntar nada — ou None quando a pergunta é necessária.

    Com um profissional cadastrado não existe ambiguidade: perguntar "qual
    nutricionista?" em toda dieta é ruído que a pessoa aprende a responder no
    automático, e resposta no automático não protege ninguém.

    Com dois ou mais a pergunta volta a valer, porque a prescrição sai com o CRN
    de quem assina e não há como adivinhar quem está na frente do computador.

    A rede que substitui a pergunta: o CRN aparece na revisão da dieta, antes da
    autorização do documento — ele vê antes de sair.
    """
    validos = [p for p in perfis if perfil_valido(p)]
    return validos[0] if len(validos) == 1 else None


def confirmacao_de_identidade(perfil):
    """Mostrada quando há mais de um profissional cadastrado (R2.6)."""
    return "Emitindo como %s — %s. Está correto?" % (perfil["nome"], perfil["crn"])
