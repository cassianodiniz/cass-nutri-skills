# -*- coding: utf-8 -*-
"""
A pasta de cada paciente dentro do consultório (bloco 6).

Cada paciente tem uma pasta com o nome dele, e dentro dela a planilha própria
(cópia do modelo) e os PDFs das dietas. A identidade do paciente é a PASTA — não
há arquivo de cadastro paralelo, porque a planilha já guarda o nome, o objetivo e
as medidas, e dois registros da mesma coisa divergem sem avisar.

Só biblioteca padrão.
"""
import os
import re
import shutil
import unicodedata

import planilha


class ErroPaciente(Exception):
    """Mensagem já escrita para leigo."""


EXTENSAO = ".xlsm"
SUFIXO_BACKUP = ".bak"


# ---------------------------------------------------------------- nomes

def nome_de_pasta(nome):
    """
    O nome do paciente virando nome de pasta.

    Reusa o saneamento do documento (mesma regra do PDF): barra, dois-pontos e
    companhia saem, espaço dobrado é colapsado, ponto final some. Um nome que
    sobrasse vazio viraria pasta "paciente", que é ruim mas é achável — melhor
    que quebrar no meio do atendimento.
    """
    from documento import sanear_nome
    return sanear_nome(nome, limite=60)


def chave(nome):
    """
    A forma de comparar dois nomes de paciente.

    Quatro coisas são achatadas de propósito:
      - acentuação em formas diferentes: "José" digitado no Mac e no Windows
        chega como sequências de bytes distintas (NFD e NFC). Sem normalizar, a
        mesma pasta some ao trocar de computador com a pasta no Drive
      - o acento em si: ninguém digita "José" ao procurar um paciente. O preço é
        que "Sofía" e "Sofia" contam como a mesma pessoa — e isso é o que se
        quer, porque quase sempre É a mesma pessoa digitada de dois jeitos. Se
        um dia forem duas mesmo, criar() recusa e pede um diferenciador, que é o
        desfecho seguro
      - maiúsculas: "maria silva" e "Maria Silva" são a mesma pessoa
      - espaço sobrando no meio ou nas pontas

    Não reusa catalogo.normalizar() de propósito: aquela é para nome de alimento
    e vai ganhar tratamento de plural e sinônimo, que em nome de gente estaria
    errado ("Mendes" não é plural de "Mende").
    """
    texto = unicodedata.normalize("NFD", str(nome or "").strip().lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto)


# ---------------------------------------------------------------- localizar

def caminho_da_pasta(consultorio, nome):
    return os.path.join(consultorio, nome_de_pasta(nome))


def caminho_da_planilha(pasta):
    """A planilha daquele paciente, pelo nome esperado ou pela primeira achada."""
    esperado = os.path.join(pasta, os.path.basename(pasta) + EXTENSAO)
    if os.path.exists(esperado):
        return esperado
    try:
        achados = sorted(f for f in os.listdir(pasta)
                         if f.lower().endswith(EXTENSAO)
                         and not f.startswith("~$"))
    except OSError:
        return esperado
    return os.path.join(pasta, achados[0]) if achados else esperado


def listar(consultorio):
    """
    Todas as pastas do consultório, em ordem alfabética. Criada à mão também vale.

    Ignora as que começam com "." ou "_": é a convenção de "isto não é conteúdo",
    e a pasta `_Modelo` do próprio nutricionista aparecia como se fosse gente.
    """
    try:
        nomes = os.listdir(consultorio)
    except OSError:
        return []
    pastas = [n for n in nomes
              if os.path.isdir(os.path.join(consultorio, n))
              and not n.startswith((".", "_"))]
    return sorted(pastas, key=chave)


def tem_dieta(consultorio, nome):
    """Esta pasta tem planilha dentro? É o que separa paciente de pasta comum."""
    return os.path.exists(caminho_da_planilha(os.path.join(consultorio, nome)))


def recentes(consultorio, quantos=10):
    """
    Os últimos ATENDIDOS primeiro — só quem tem planilha.

    Listar 300 pastas numa conversa não ajuda ninguém: quem tem consultório cheio
    volta quase sempre a um dos últimos, e para o resto existe procurar().

    Pasta sem planilha fica de fora porque esta lista responde "quem você já
    atendeu": um consultório de verdade tem `Contratos` e `Fotos antes e depois`
    ao lado dos pacientes, e oferecer "atender Contratos" queima a confiança na
    lista inteira. Quem foi criado à mão e ainda não tem dieta continua achável
    por `procurar()` e por `existe()` — some da vitrine, não do consultório.
    """
    def quando(nome):
        alvo = caminho_da_planilha(os.path.join(consultorio, nome))
        try:
            return os.path.getmtime(alvo)
        except OSError:
            return 0
    com_dieta = [n for n in listar(consultorio) if tem_dieta(consultorio, n)]
    return sorted(com_dieta, key=quando, reverse=True)[:quantos]


def procurar(consultorio, texto):
    """Busca por pedaço do nome, ignorando acento e maiúscula."""
    alvo = chave(texto)
    if not alvo:
        return []
    return [n for n in listar(consultorio) if alvo in chave(n)]


def existe(consultorio, nome):
    """A pasta deste paciente já existe? Devolve o nome real dela, ou None.

    Compara por chave() e não por caminho: no Mac a pasta "José" pode estar
    gravada numa forma de acentuação que o os.path.exists do Windows não acha.
    """
    alvo = chave(nome_de_pasta(nome))
    for existente in listar(consultorio):
        if chave(existente) == alvo:
            return existente
    return None


# ---------------------------------------------------------------- criar

def criar(consultorio, nome, modelo):
    """
    Cria a pasta do paciente e põe a planilha dele dentro (cópia do modelo).

    Já existir é ERRO, não silêncio: duas pacientes chamadas Maria Silva é caso
    real, e escrever por cima da dieta da primeira seria irreparável. Quem chama
    consulta existe() antes e resolve a ambiguidade com o nutricionista.
    """
    if not os.path.isdir(consultorio):
        raise ErroPaciente(
            "Não achei a pasta onde ficam seus pacientes. Me diga onde ela está "
            "antes de cadastrar alguém novo.")
    ja = existe(consultorio, nome)
    if ja:
        raise ErroPaciente(
            'Já existe uma pasta para "%s". Se for a mesma pessoa, é só abrir; se '
            "for outra, escolha um nome que diferencie as duas." % ja)

    pasta = caminho_da_pasta(consultorio, nome)
    os.makedirs(pasta)
    destino = os.path.join(pasta, os.path.basename(pasta) + EXTENSAO)
    shutil.copy2(modelo, destino)

    # A planilha de fábrica vem com uma dieta de exemplo preenchida — 4 refeições,
    # começando por Pão, Ovo e Queijo — e com "Definição Muscular" no objetivo.
    # Enquanto a cópia era descartável isso morria no primeiro cálculo, porque
    # escrever_refeicoes() limpa antes de escrever. Com a planilha guardada, um
    # paciente recém-criado passa a ter esse exemplo como se fosse a dieta dele:
    # a retomada leria e mostraria alimentos que ninguém prescreveu.
    with planilha.Pacote(destino) as pk:
        planilha.limpar_ficha_paciente(pk)
        for aba in planilha.ABAS_CALCULO:
            planilha.limpar_blocos(pk, aba)
        pk.salvar(destino)
    return pasta


def renomear(consultorio, nome_atual, nome_novo):
    """
    Paciente que casou, ou nome digitado errado na primeira consulta.

    A planilha acompanha o nome novo — o arquivo E o nome gravado dentro dela.
    Só renomear a pasta deixava a ficha dizendo o nome antigo, e o próximo PDF
    sairia com ele no cabeçalho: documento clínico assinado com o nome errado.

    Os PDFs já entregues NÃO são renomeados: são documentos assinados que existem
    impressos e na mão do paciente — reescrever o nome deles depois seria
    adulterar registro clínico.
    """
    origem = os.path.join(consultorio, nome_atual)
    if not os.path.isdir(origem):
        raise ErroPaciente('Não encontrei a pasta de "%s".' % nome_atual)
    ja = existe(consultorio, nome_novo)
    if ja and chave(ja) != chave(nome_atual):
        raise ErroPaciente(
            'Já existe uma pasta chamada "%s" — escolha outro nome.' % ja)

    destino = caminho_da_pasta(consultorio, nome_novo)
    planilha_antiga = caminho_da_planilha(origem)
    os.rename(origem, destino)
    if os.path.exists(planilha_antiga.replace(origem, destino)):
        nova = os.path.join(destino, os.path.basename(destino) + EXTENSAO)
        atual = planilha_antiga.replace(origem, destino)
        if os.path.abspath(atual) != os.path.abspath(nova):
            os.rename(atual, nova)
        _regravar_nome(nova, nome_novo)
    return destino


def _regravar_nome(alvo, nome_novo):
    """
    O nome novo dentro da ficha da planilha (P1b: backup antes, e confere depois).

    A conferência compara com o backup em vez de com o modelo: a planilha de um
    paciente é diferente do modelo por definição, e o que importa aqui é não ter
    perdido peça na gravação.
    """
    backup = alvo + SUFIXO_BACKUP
    shutil.copy2(alvo, backup)
    try:
        with planilha.Pacote(alvo) as pk:
            planilha.escrever_paciente(pk, {"nome": nome_novo})
            pk.salvar(alvo)
        planilha.conferir_membros(backup, alvo)
    except Exception:
        shutil.copy2(backup, alvo)          # volta ao que era: nada pela metade
        raise ErroPaciente(
            "Renomeei a pasta, mas não consegui trocar o nome dentro da planilha "
            "— ela pode estar aberta no Excel. Feche o Excel e me peça para "
            "renomear de novo, senão o próximo documento sai com o nome antigo.")


# ---------------------------------------------------------------- estado

def planilha_aberta(caminho):
    """
    Alguém está com esta planilha aberta no Excel ou no LibreOffice?

    Sem isso o cálculo falha com um erro técnico que não diz nada. Duas pistas,
    porque nenhuma sozinha cobre os dois programas e os dois sistemas:
      - o arquivo de bloqueio que os dois criam ao lado (~$nome / .~lock.nome#)
      - tentar abrir para escrita: no Windows isso já falha com o arquivo em uso
    """
    pasta, nome = os.path.split(caminho)
    for marca in ("~$" + nome, ".~lock." + nome + "#"):
        if os.path.exists(os.path.join(pasta, marca)):
            return True
    if not os.path.exists(caminho):
        return False
    try:
        with open(caminho, "r+b"):
            return False
    except (OSError, IOError):
        return True


def conferir(consultorio, nome, modelo):
    """
    Este paciente está pronto para ser atendido? Problemas em português.

    Junta tudo que pode estar errado antes de perguntar qualquer coisa a quem
    está atendendo: pasta sumida, planilha ausente, salva como .xlsx (perdendo as
    macros), estragada, ou aberta em outro programa.
    """
    pasta = os.path.join(consultorio, existe(consultorio, nome) or nome_de_pasta(nome))
    if not os.path.isdir(pasta):
        return ['não encontrei a pasta de "%s" entre os seus pacientes' % nome]

    alvo = caminho_da_planilha(pasta)
    if not os.path.exists(alvo):
        soltos = [f for f in os.listdir(pasta) if f.lower().endswith(".xlsx")]
        if soltos:
            return ["a planilha deste paciente foi salva como .xlsx e perdeu as "
                    "partes que fazem as contas. Posso montar uma nova a partir "
                    "do modelo e trazer a dieta que estava lá"]
        return ["não encontrei a planilha deste paciente na pasta dele"]

    if planilha_aberta(alvo):
        return ["a planilha deste paciente está aberta em outro programa. "
                "Feche o Excel (ou o LibreOffice) e me avise"]

    return planilha.conferir_planilha_paciente(modelo, alvo)
