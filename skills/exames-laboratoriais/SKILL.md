---
name: exames-laboratoriais
description: "Use quando for necessário consultar conceitos, valores históricos ou tabelas do livro Interpretação de Exames Bioquímicos (Costa, 2013), com busca por página física e tabelas visualmente conferidas; não use como diretriz clínica atual."
---

# Exames Laboratoriais

## Distribuição completa

As fontes e referências acompanham esta skill. Resolva todos os caminhos a partir
da pasta deste SKILL.md e execute os scripts originais nesta pasta. Não exija
configuração em pastas externas nem arquivos adicionais do usuário para consultar
o material incluído. Registros de paciente e saídas continuam fora do plugin.

## Escopo

Esta skill consulta uma fonte de 2013. Ela recupera o que o livro declara; não valida atualidade clínica, não diagnostica e não substitui intervalo fornecido pelo laboratório, diretriz vigente ou avaliação profissional.

## Fluxo obrigatório

1. Para qualquer valor, faixa, ponto de corte, unidade ou tabela, consulte primeiro `references/verified-values.md`.
2. Se o dado estiver ali, responda fielmente e cite no formato: `(Costa, 2013, p. impressa X; PDF p. Y; Tabela Z)`.
3. Se não estiver ali, execute `python3 scripts/search.py "termo"`. Use o resultado apenas para localizar a página.
4. Dados numéricos ou tabelas encontrados apenas em `references/full_text.txt` ou `references/pages/` são **não verificados**. Não os apresente como transcrição fiel. Diga qual página física precisa de revisão visual.
5. Para explicações não numéricas, a extração pode ser resumida, sempre citando a página física do PDF e rotulando a evidência como “texto extraído automaticamente, sem revisão visual” quando a página não constar da lista revisada.
6. Se a pergunta pedir recomendação atual, deixe claro que a fonte é histórica e recomende confronto com diretriz vigente e intervalo do laboratório. Não atualize números por memória.

## Regras de fidelidade

- Preserve sinais (`<`, `>`, `≤`, `≥`), unidades, população/idade, condição e redação da tabela.
- Não corrija silenciosamente erros ou inconsistências aparentes da fonte. Reproduza o conteúdo e acrescente uma nota de cautela.
- Diferencie página impressa de página física do PDF. `scripts/search.py` sempre informa a página física.
- Nunca monte uma “tabela completa” juntando linhas de páginas diferentes sem declarar cada origem.
- A ausência de um item da base verificada significa ausência de revisão, não ausência no livro.
- Não atribua ao livro informação que veio de outra fonte.

## Recursos

- `references/source/original.pdf`: PDF-fonte integral, preservado localmente para auditoria e nova revisão visual.
- `references/verified-values.md`: 14 tabelas visualmente conferidas em 10 páginas físicas.
- `references/pages/page-NNN.txt`: texto de cada uma das 273 páginas físicas, para localização.
- `references/full_text.txt`: extração integral por `pdftotext -layout`; recuperação, não fac-símile.
- `assets/page-images/`: evidência de revisão de 11 páginas físicas (10 com tabelas verificadas e 1 página contextual).
- `references/source-metadata.md`: identidade, hash e cobertura.
- `DECISION_LOG.md`: decisões, atalhos recusados, limitações e páginas não verificadas.

## Exemplos de uso

```bash
python3 scripts/search.py "frutosamina"
python3 scripts/search.py "TABELA 4-[1-5]" --regex --context 8
python3 scripts/verify_package.py
```

## Forma da resposta

Forneça: resposta curta; transcrição ou resumo; proveniência exata; nota de atualidade/limitação quando clinicamente relevante. Se houver anomalia conhecida, destaque-a sem substituir o original.
