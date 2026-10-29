# Contrato de proveniência — Biodisponibilidade de Nutrientes

## Autoridade factual

Somente estes artefatos podem provar o que o livro diz:

- `pages/page-NNNN.md`: autoridade preferencial para resposta e citação.
- `chapters/*-source.md`: recorte integral para leitura contínua.
- `source/full-text.md`: cópia integral recuperada, marcada por página.

`../chapters/` e `../facts/` são índices mecânicos de navegação e candidatos. Eles nunca são evidência final.

## Registro interno obrigatório

Antes de responder, crie em arquivo temporário um registro de auditoria contendo:

- `Origem: livro` — inclua `Cozzolino (2012), PDF p. N` ou a obra equivalente desta skill e uma linha `Evidência [PDF p. N]: trecho curto` copiada da página correspondente.
- `Origem: externa` — somente quando o usuário pedir informação externa ou atual. Inclua `Fonte externa:` e um link verificável.
- `Não localizado no livro` — use quando a busca na fonte recuperada não sustentar a afirmação.

Nunca apresente memória do modelo, conversa anterior, texto do Claude, outra skill ou um resumo antigo como se fosse conteúdo do livro. Uma síntese própria só pode combinar trechos já comprovados e deve ser marcada como `Inferência:`.

Valide o registro interno antes da resposta final:

```bash
python3 scripts/check_answer_provenance.py /caminho/do/registro-interno.md
```

## O que mostrar ao usuário

- Em respostas normais baseadas somente no livro, entregue a resposta limpa. Não mostre automaticamente `Origem: livro`, página ou trecho de evidência.
- Mostre página e evidência quando o usuário pedir a fonte, quando houver conflito/ambiguidade na extração ou quando isso for necessário para conferir um dado sensível.
- Sempre avise visivelmente quando usar fonte externa, quando algo não for localizado no livro ou quando a conclusão for uma inferência em vez de afirmação direta da obra.

A ausência de referência visível nunca dispensa o registro e a validação internos.
