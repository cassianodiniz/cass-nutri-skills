# Validação

Data: 29/10/2026, Brasília. Versão de conteúdo clínico: B; pacote final: C (correção documental).

- Controle sem a skill: agente não conseguiu recuperar recomendações exatas, páginas ou fórmula confirmada das fontes; declarou a limitação sem inventar. Isso é lacuna de acesso à referência, não falha de segurança ou alucinação observada. A criação é solicitada explicitamente como conversão documental.
- Corpus: 51 páginas, três documentos; texto por página do PDF original e figura recuperada visualmente; suplemento online ausente identificado.
- Revisão visual: validador de revisão dos PDFs passou, uma página recuperada (A, p.7).
- Recuperação: dez consultas passaram, cobrindo conceito exato, abreviação, dois conceitos, texto livre FTS5 e evidência em três fontes. Cinco verificações na fonte cobriram tabela, limiar, unidade, fase clínica e figura recuperada. Resultados em `retrieval-checks.json`.
- Busca completa usa `--limit 100 --per-chapter 100` porque o runtime padrão devolve apenas duas páginas por capítulo. A instrução de uso foi ajustada para recuperar todas as páginas correspondentes neste corpus.
- Defeito encontrado no catálogo: aliases com/sem acento colidiam após normalização, causando erro UNIQUE no índice. Removidas duplicatas normalizadas no catálogo; índice reconstruído com 51 documentos e 488 menções. Nenhuma mudança no runtime genérico foi necessária.
- Frontmatter e nomenclatura: quick_validate.py passou com o Python do ambiente book-to-skill que contém PyYAML.
- Scanner de segurança: primeira varredura passou sem padrões conhecidos de injeção/autoridade; repetir após finalização.
- Revisão independente B: sem erro clínico material nos trechos conferidos; um achado documental de PNGs ausentes aceito e corrigido em C. Relatório completo em review-B.md. Aplicação B: quatro grupos de verificações passaram; escopo e limites em application-B.md. Resultados de conteúdo e busca B reutilizados em C porque a correção documental não os afeta.

Os testes de recuperação comprovam cobertura dos casos executados, não validação clínica universal de recomendações. Esta é uma skill de referência e aplicação; microtestes de redação para disciplina, múltiplos modelos e campanhas sob pressão não foram executados. Nenhum teste foi apresentado como prova de eficácia clínica de suplementação vitalícia.

## Fechamento independente C

O revisor confirmou o P3 resolvido: os três PNGs estão presentes nos caminhos citados. Conferiu também a extração auxiliar privada e sua indicação no índice. Comparou 67 arquivos de conteúdo, fontes canônicas e runtime com B sem alteração; a revisão de conteúdo B permanece válida com os mesmos limites. Nenhum teste comportamental adicional foi executado. Scanner, frontmatter e revisão dos PDFs passaram novamente no pacote final.
