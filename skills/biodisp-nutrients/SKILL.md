---
name: biodisp-nutrients
description: "Use when answering questions about nutrient bioavailability, mechanisms, interactions, metabolism, tables, units, or values from the bundled Cozzolino book corpus."
---

# Biodisponibilidade de Nutrientes

© 2026 Cassiano Diniz. Skill criada por [Cassiano Diniz](https://instagram.com/cassiano.diniz).

**Autores:** Silvia M. Franciscato Cozzolino (org.)
**Páginas físicas:** 910 | **Capítulos:** 53

## Distribuição completa

As fontes e referências acompanham esta skill. Resolva todos os caminhos a partir
da pasta deste SKILL.md e execute os scripts originais nesta pasta. Não exija
configuração em pastas externas nem arquivos adicionais do usuário para consultar
o material incluído. Registros de paciente e saídas continuam fora do plugin.

## Estado obrigatório

Leia `metadata/extraction.json` antes de responder. Enquanto `release_allowed=false`, use a skill para localização e estudo, mas não apresente números, tabelas, fórmulas ou recomendações como verificados.

## Contrato obrigatório de proveniência

1. Leia `references/PROVENANCE.md` antes de formular a resposta.
2. As únicas fontes factuais do livro são `references/pages/`, `references/chapters/*-source.md` e `references/source/full-text.md`.
3. Nunca trate conversa anterior, memória do modelo, saída do Claude, outra skill, `chapters/` ou `facts/` como prova do que o livro diz.
4. Antes de toda resposta factual, crie o registro interno em `/tmp/`, nunca dentro da skill ou do projeto do usuário. Declare `Origem: livro`, `Origem: externa` ou `Não localizado no livro`.
5. No registro interno, `Origem: livro` exige `Cozzolino (2012), PDF p. N` e `Evidência [PDF p. N]: trecho curto` copiado de `references/pages/page-NNNN.md`.
6. Se houver conteúdo do livro e externo, separe-os no registro sob `Separação de fontes:`. Nunca misture silenciosamente.
7. Use de 3 a 6 evidências centrais numa resposta normal. Execute `python3 scripts/check_answer_provenance.py <registro-interno.md>` uma vez depois de montar o registro e só responda após `PASS`.
8. Na resposta ao usuário, omita por padrão o registro, a página e o trecho quando toda a resposta vier diretamente do livro.
9. Mostre a proveniência quando o usuário pedir, quando houver conflito/ambiguidade ou quando a conferência explícita for necessária.
10. Sempre avise visivelmente se usar fonte externa, se o dado não for localizado no livro ou se houver `Inferência:`.
11. `scripts/test_provenance_guard.py` é teste de manutenção; não o execute durante uma resposta normal.

## Como encontrar dados

Uma vitamina ou um mineral pode aparecer em muitos capítulos. O capítulo principal é o ponto de partida, não o limite da busca.

1. Execute `python3 scripts/search_book.py "pergunta completa" --json --comprehensive`.
2. Leia `detected_topics`, `coverage` e os resultados. O buscador faz duas passagens: prioriza o capítulo principal e varre globalmente todas as páginas por aliases cadastrados.
3. Em perguntas focadas, use os resultados padrão. Em perguntas amplas — `interações`, `o que aumenta`, `o que diminui`, `tudo sobre` — use `--limit 20 --per-chapter 2`. A cobertura global já foi calculada; não repita a varredura com `rg`.
4. Os resultados são diversificados por capítulo: a primeira rodada traz a melhor página de cada capítulo antes de repetir um capítulo. Não substitua isso pelos primeiros resultados em ordem de página.
5. Abra somente os `page_path` efetivamente usados na resposta. `snippet` localiza o contexto; `evidence` é um trecho literal curto, pronto para o registro de proveniência. Não altere sua pontuação.
6. Organize a síntese por mecanismo: capítulo principal, fatores que aumentam, fatores que reduzem, interação com outros nutrientes, condições clínicas e limites/incertezas.
7. Para números e tabelas, use `facts/` apenas para localizar candidatos; confirme cada valor na página exata.
8. Use `chapters/` somente como roteiro de navegação, nunca como evidência factual.
9. Se a busca interna não sustentar a resposta, diga `Não localizado no livro`; só procure fora se o usuário pedir.

### O que o índice garante

- `references/search/topic-aliases.json` registra nomes equivalentes e o capítulo principal de cada nutriente.
- `references/search/book-search.sqlite3` contém FTS5 e um mapa determinístico alias → página → capítulo.
- `coverage.matching_pages` e `coverage.matching_chapters` contam todas as ocorrências delimitadas do tópico principal antes do recorte de resultados.
- `source_scope=book-only` e `external_sources_used=false` deixam explícito que a recuperação não consultou a internet.
- O mapa não cria relações por inteligência artificial. Uma interação só pode entrar na resposta quando estiver sustentada pela página aberta.

### Atualizar o índice

Se páginas ou aliases forem alterados, execute `python3 scripts/build_search_index.py`. Depois rode `python3 tests/test_retrieval_v2.py -v` e `python3 scripts/test_provenance_guard.py`.

## Navegação por capítulos

Use `references/INDEX.md` para a lista completa dos 53 capítulos e suas faixas de páginas. O índice é navegação; a evidência factual continua sendo `references/pages/`.

## Arquivos

- `references/source/full-text.md` — fonte integral recuperada e marcada por página.
- `references/pages/` — uma página recuperada por arquivo para revisão e citação.
- `references/chapters/` — fonte integral dividida por capítulo.
- `references/PROVENANCE.md` — contrato que separa livro, fonte externa e inferência.
- `references/search/topic-aliases.json` — aliases e capítulos principais.
- `references/search/book-search.sqlite3` — índice local FTS5 e mapa de ocorrências.
- `chapters/` — roteiros mecânicos sem autoridade factual.
- `facts/` — índices mecânicos de candidatos; todo dado deve ser confirmado na página.
- `reports/source-coverage.md` — cobertura e revisão.

## Limites

Esta é uma fonte histórica. O corpus integral e seus índices acompanham esta distribuição. Para decisão clínica, combine o livro com avaliação profissional e evidência atualizada.
