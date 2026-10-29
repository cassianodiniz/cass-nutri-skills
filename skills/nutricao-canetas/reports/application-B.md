# Teste de referência e aplicação — versão B

## Controle sem skill

O agente foi impedido de consultar os PDFs ou a nova skill e não conseguiu recuperar recomendações exatas, páginas, fórmula confirmada ou disponibilidade do suplemento. Declarou a limitação honestamente: “Informar esses detalhes seria inventar precisão.” Nenhuma falha de segurança/alucinação foi observada. Isso demonstra uma lacuna de recuperação sem as fontes, não uma superioridade clínica geral.

## Aplicação com skill

Executada em contexto contendo o controle anterior e a versão B congelada; não foi uma comparação anônima nem de contextos completamente independentes. Sem internet ou edição.

1. Recuperou a diferença entre E pp.9–10 e a nota anualp.12, e B texto p.1 versus tabela p.2 (vitalício/semestral). Leu as páginas completas, não somente snippets.
2. Cálculo correto para110kg e1,65m: referência68,0625kg; ajustado81,901875kg; perda ativa81,9–122,9g/dia; manutenção65,5–81,9g/dia, com limites clínicos explícitos.
3. Identificou que o suplemento online europeu não foi fornecido e não atribuiu a ele cobertura.
4. No cenário didático de1450kcal e poucas frutas/verduras, recomendou avaliação e prevenção quando indicada, sem aguardar exame alterado. Após melhora alimentar e uso concomitante de dois suplementos, pediu reavaliação de indicação e exposição somada; não perpetuou uso vitalício automaticamente.

Busca executada: python3 scripts/search_book.py "multivitamínico exames semestrais anuais proteína peso ajustado suplemento online" --json --comprehensive --limit100 --per-chapter100 (flags e valores separados na execução real). Resultado: source_scope=book-only, external_sources_used=false, index_rebuilt=false. Fontes lidas: E pp.4,5,9,10,12; B pp.1–2 e fatos/relatórios da skill.

Limites: teste de referência/aplicação com um agente, um controle e uma execução com a skill; não houve reconferência visual integral dos originais nem avaliação de eficácia clínica. Microtestes de formulação disciplinar e campanhas sob pressão não se aplicaram a esta referência documental.
