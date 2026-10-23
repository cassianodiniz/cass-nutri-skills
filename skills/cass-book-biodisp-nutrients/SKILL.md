---
name: cass-book-biodisp-nutrients
description: "Use when answering questions about nutrient bioavailability, absorption, metabolism, nutrient interactions, or exact tables and values from the user's Cozzolino book corpus. Do not use to create a dietary prescription or claim current evidence without checking appropriate sources."
---

# Biodisponibilidade de Nutrientes

Consulta o corpus local do livro de Cozzolino, com recuperação por página e
conferência de proveniência. O plugin distribui esta integração; a transcrição e
o índice do livro ficam privados no computador do usuário, fora do GitHub.

## Preparar ou retomar

Rode `python3 scripts/corpus_local.py localizar`, com o caminho deste script
resolvido a partir da pasta deste SKILL.md. O comando confere integridade e mostra
`corpus` e `instrucoes`; não faz pesquisa nem gera uma resposta sobre nutrientes.

Se o corpus não estiver preparado, peça o arquivo `.skill` da cópia autorizada do
usuário. Explique que será guardado em `~/.cass-book-biodisp-nutrients/corpus/`,
fora do plugin, e execute `python3 scripts/corpus_local.py instalar --pacote
<arquivo-local.skill>` quando o usuário autorizar essa preparação. Não baixe nem
redistribua o livro por iniciativa própria. Não substitua uma instalação existente;
`CASS_BIODISP_HOME` permite escolher outra pasta externa. Pacote inválido é recusado
antes de instalar. Não trate falta de corpus como ausência de informação no livro.

Se a conferência falhar, informe o erro e preserve o corpus existente. Não faça
busca ou resposta factual com arquivos cuja integridade não foi confirmada.

## Consultar o livro

Depois de localizar, leia integralmente o `SKILL.md` original apontado em
`instrucoes` e `references/PROVENANCE.md` dentro do corpus. Execute o fluxo original
da obra, usando os scripts e caminhos daquela pasta externa. O buscador, o índice
e o conferente de proveniência são os originais, sem troca de motor.

1. Confira `metadata/extraction.json`; só apresente valores como verificados quando
   a extração estiver liberada, conforme as instruções originais.
2. Use `scripts/search_book.py` do corpus para localizar páginas. Um resumo ou
   snippet não substitui a leitura da página usada como evidência.
3. Registre a proveniência em arquivo temporário da sessão, fora da skill e do
   projeto. Confira cada número/tabela na página exata e rode o conferente original
   `scripts/check_answer_provenance.py`. Só responda depois de PASS.
4. Preserve o contrato original: separar livro, inferência e eventual fonte externa;
   não pesquisar fora automaticamente quando o dado não for localizado. Se o pedido
   exigir evidência atual, diga que o livro é histórico e use fontes atuais acessíveis
   com identificação explícita, sem atribuí-las ao livro.
5. Se a ferramenta não permitir consulta local ou o conferente falhar, explique a
   limitação; não alegue leitura, valor confirmado ou PASS que não ocorreram.

A dieta permanece uma skill separada: esta consulta não muda quantidades, metas,
fórmulas ou prescrições por iniciativa própria. Não publique transcrições integrais,
corpus, índices ou registros privados no repositório do plugin.
