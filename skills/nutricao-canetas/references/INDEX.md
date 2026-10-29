# Índice de evidências

E = consenso europeu, ch01, 24 páginas; A = advisory americano, ch02, 24 páginas; B = perspectiva bariátrica, ch03, 3 páginas. As páginas abaixo são as páginas físicas de cada PDF.

| Pergunta/tema | Fatos e raciocínio | Fonte original |
|---|---|---|
| Quando suplementar? Abaixo de 1.500 kcal? | [Suplementação e exames](../facts/suplementacao-exames.md); decisão operacional no SKILL.md | E pp.9-10; A p.10; B pp.1-2 |
| Vitalício ou enquanto persistir risco? | [Suplementação e exames](../facts/suplementacao-exames.md); [divergências](../reports/conflitos-entre-fontes.md) | E pp.9-12; B pp.1-2 |
| Quais exames e quando repetir? | [Suplementação e exames](../facts/suplementacao-exames.md) | E pp.9-10, nota p.12; A p.10; B p.2 |
| Qual peso usar na proteína? | [Proteína e energia](../facts/proteina-energia.md) | E pp.4-5,9-10; A p.10; B p.1 |
| Qual valor sinaliza ingestão muito baixa? | [Proteína e energia](../facts/proteina-energia.md) | E pp.4,9-10; A pp.3-4 |
| Náusea, vômitos, constipação ou diarreia? | [Sintomas](../facts/sintomas-hidratacao.md) | E pp.6-7; A p.9; B p.2 |
| Fibras, psyllium e água? | [Sintomas](../facts/sintomas-hidratacao.md) | E pp.3-7,10 |
| Queda de força, massa magra e exercício? | [Função e exercício](../facts/funcao-exercicio.md) | E pp.11-12,15-17; A pp.10-11; B pp.1-2 |
| Figura com oito prioridades e tabela 5As? | [ch02](../chapters/ch02-advisory-americano.md) | A p.7, recuperada visualmente |
| GLIM, PG-SGA SF e avaliação funcional? | [ch01](../chapters/ch01-consenso-europeu.md) | E pp.8,15-16 |
| COM-B e food noise? | [ch03](../chapters/ch03-ponte-bariatrica.md) | B p.2; E pp.12-15 |
| Manutenção, jejum e dietas específicas? | [ch02](../chapters/ch02-advisory-americano.md) | A p.16 |
| Qual a cobertura e quais arquivos faltam? | [Cobertura](../reports/source-coverage.md) | Suplemento online de E não fornecido |

## Fontes privadas completas

- [ch01 — EASO/EFAD/ECPO](chapters/ch01-consenso-europeu-source.md).
- [ch02 — ACLM/ASN/OMA/TOS](chapters/ch02-advisory-americano-source.md).
- [ch03 — Bridging](chapters/ch03-ponte-bariatrica-source.md).
- [Corpus completo](source/full-text.md); proveniência e hashes em `source/provenance.json`. Extração estruturada auxiliar do Docling em `source/docling/`; para citação de página prevalece a paginação canônica do PDF original.

Índice global: páginas 1-24 = E; 25-48 = A (subtraia 24 para obter a página original); 49-51 = B (subtraia 48). Cada página tem cabeçalho com fonte e número original. Use `python3 scripts/search_book.py "pergunta" --json --comprehensive --limit 100 --per-chapter 100` na raiz da skill; leia os arquivos recuperados.

As referências integrais são privadas e podem não estar presentes em uma cópia sincronizada sem fontes. Não preencher lacunas com citações inventadas.
