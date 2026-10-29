---
name: nutricao-canetas
description: "Use quando um nutricionista precisar orientar, montar ou revisar alimentação de adultos em uso de canetas para obesidade, agonistas de GLP-1 ou agonistas duais GLP-1/GIP, especialmente com baixa ingestão, náuseas, constipação, risco de deficiência nutricional ou perda de força. Use também para consultar os três documentos de referência sobre esses temas."
---

# Nutrição Canetas

Base documental: Dobbie et al., EASO/EFAD/ECPO, 2026; Mozaffarian et al., ACLM/ASN/OMA/TOS, 2025; Spreckley, Ruggiero e Brown, 2025/2026. Três fontes, 51 páginas. Criada em 29/10/2026, Brasília.

## Distribuição completa

As fontes e referências acompanham esta skill. Resolva todos os caminhos a partir
da pasta deste SKILL.md e execute os scripts originais nesta pasta. Não exija
configuração em pastas externas nem arquivos adicionais do usuário para consultar
o material incluído. Registros de paciente e saídas continuam fora do plugin.

## Prioridade clínica

Transforme a redução do apetite em um plano que preserve ingestão de nutrientes, força, função e qualidade de vida. Menor ingestão energética pode coexistir com baixa qualidade alimentar. Investigue especificamente frequência e quantidade de frutas, verduras, legumes, feijões, cereais integrais e fontes proteicas; o uso do medicamento, sozinho, não demonstra o padrão alimentar da pessoa.

**Conduta operacional de prevenção:** ingestão habitual abaixo de **1.500 kcal/dia**, ou exclusão habitual de grupos nutritivos/baixa variedade alimentar, deve acionar avaliação de adequação e **recomendação de multivitamínico-mineral completo diário quando houver ingestão inadequada ou risco relevante**, após conferir contraindicações, comorbidades, fórmula e exposição total. Não condicione a prevenção à existência de um exame alterado. Baixo consumo de frutas e verduras é um sinal relevante, mas a avaliação considera o conjunto da alimentação.

**Duração:** mantenha a suplementação enquanto persistirem ingestão inadequada ou risco nutricional. O uso pode ser prolongado, com reavaliação periódica da indicação, composição e doses. Se a inadequação persistir por toda a vida, a necessidade pode persistir; não prescreva duração vitalícia irrevogável a todo usuário de GLP-1. Em pacientes pós-bariátrica, siga o protocolo específico da cirurgia. Suplementação preventiva e tratamento de deficiência são decisões distintas.

Essa regra operacional enfatiza prevenção no contexto de baixa ingestão. Para a evidência exata, EASO descreve <1.500 kcal como sinal de risco e <1.200 kcal como indicação para considerar multivitamínico; a recomendação também se aplica a dieta de má qualidade acima desses valores. Não atribua aos três documentos um limiar universal de suplementação ou uso vitalício. Consulte [suplementação e exames](facts/suplementacao-exames.md) antes de definir a conduta.

## Aplicação ao atendimento

1. Identifique medicamento informado, fase do tratamento, ingestão real, sintomas, perda ponderal, função, comorbidades, cirurgia bariátrica anterior e suplementos já usados. Se faltarem informações que mudem a conduta, solicite apenas essas informações; apresente o que já pode ser concluído.
2. Classifique a vulnerabilidade nutricional: ingestão muito baixa, pouca variedade, intolerância persistente, fragilidade, dieta restritiva, insegurança alimentar e deficiências prévias justificam maior atenção. A presença de obesidade não exclui desnutrição.
3. Ajuste volume, frequência, textura e distribuição das refeições aos sintomas. Priorize densidade nutricional e proteína tolerável. Evite acrescentar restrição severa sobre uma ingestão já insuficiente.
4. Defina proteína com **base de cálculo explícita** e conforme condição clínica. Associe plano de treino de força progressivo e acompanhamento funcional. Use [proteína e energia](facts/proteina-energia.md).
5. Resolva suplementação preventiva, investigação laboratorial e eventual reposição específica como decisões separadas. Defina motivo, objetivo e gatilho de reavaliação; não invente doses ausentes nas fontes.
6. Reavalie ingestão, sintomas, hidratação, força e trajetória do peso. Quando o paciente não consegue manter alimentação ou hidratação, articule avaliação clínica e revisão do tratamento com a equipe responsável.

Ao entregar uma orientação, inclua: achados relevantes; plano alimentar compatível com tolerância; meta de proteína com método; decisão de suplementação; exames justificados; acompanhamento e sinais que exigem revisão. Para calcular e entregar uma prescrição dietética completa, associe ao fluxo de cálculo dietético habitual do nutricionista, com composição dos alimentos verificada.

## Decisões essenciais

| Situação | Conduta |
|---|---|
| Alimentação abaixo de 1.500 kcal ou pouco variada | Investigar inadequação, priorizar prevenção com multivitamínico-mineral quando indicada e revisar o plano; não esperar deficiência confirmada para agir. |
| Náusea/saciedade limitando ingestão | Refeições menores, frequentes e nutritivas; ajustar gordura, fibras e textura temporariamente. |
| Constipação sem sinais de complicação | Aumentar fibras gradualmente, hidratação adaptada e movimento; usar [manejo de sintomas](facts/sintomas-hidratacao.md). |
| Vômitos persistentes ou impossibilidade de hidratar-se | Avaliação clínica urgente; considerar risco de desidratação, alterações eletrolíticas e deficiência de tiamina. |
| <800 kcal/dia de forma sustentada, por exemplo ≥1 semana | Revisão multidisciplinar da adequação e do tratamento. Não limitar a resposta a adicionar um multivitamínico. |
| Redução de força ou dificuldade nas tarefas | Revisar alimentação, exercício e intensidade do tratamento; ampliar avaliação funcional/composição corporal conforme indicação. |
| Deficiência confirmada | Avaliar reposição específica; multivitamínico preventivo pode ser insuficiente. |
| Bariátrica anterior | Preservar suplementação e monitoramento pós-cirúrgicos próprios. |

A relação aproximada de perda de gordura:massa livre de gordura de 3:1 é ilustrativa, não um teste universal de sucesso. Massa livre de gordura não é sinônimo de músculo. Faixas proteicas, metas de exercício e riscos exigem interpretação; [função e exercício](facts/funcao-exercicio.md) preserva os limites da evidência.

## Consulta às fontes

Para qualquer pergunta exata, comparação ou justificativa quantitativa, execute a partir desta pasta:

```bash
python3 scripts/search_book.py "pergunta completa" --json --comprehensive --limit 100 --per-chapter 100
```

Leia as páginas retornadas antes de responder. A busca usa aliases, mapa de menções e SQLite FTS5; se faltar o índice, ele é reconstruído a partir das referências locais. Se um arquivo do pacote estiver ausente, declare a falha de instalação antes de afirmar uma citação ou valor exato. Não confunda página global do índice com página original: ambas estão no cabeçalho do arquivo.

O resultado tem `source_scope=book-only`: cobre apenas os três PDFs. Coocorrência de dois conceitos não prova interação ou causalidade. Novas diretrizes, doses e regras locais devem ser verificadas em fontes atuais e identificadas separadamente.

| Capítulo | Abrir quando |
|---|---|
| [ch01 — Consenso europeu](chapters/ch01-consenso-europeu.md) | Avaliação de risco, metas, suplementação seletiva, função e cuidado proporcional. |
| [ch02 — Advisory americano](chapters/ch02-advisory-americano.md) | Aplicação dos 5As, alimentação, apoio à adesão, sintomas e manutenção. |
| [ch03 — Ponte com a bariátrica](chapters/ch03-ponte-bariatrica.md) | Examinar extrapolações, proposta de suplementação vitalícia e exames semestrais. |

## Apoios sob demanda

- [Índice de evidências](references/INDEX.md): pergunta → fatos → fonte integral e páginas.
- [Guia rápido](cheatsheet.md): escolher a próxima conduta.
- [Padrões de atendimento](patterns.md): 5As, COM-B e acompanhamento por trajetória.
- [Glossário](glossary.md): termos e siglas.
- [Divergências entre fontes](reports/conflitos-entre-fontes.md): antes de comparar recomendações ou atribuir consenso.
- [Cobertura e proveniência](reports/source-coverage.md): antes de avaliar completude, paginação e suplemento ausente.
- `references/source/full-text.md` e `references/chapters/*-source.md`: texto integral incluído; `references/pages/`: páginas originais, com recuperação visual conferida; `references/search/`: aliases, intervalos e índice local.
- `scripts/build_search_index.py`: reconstruir o índice; `scripts/search_book.py`: recuperar a evidência. [Validação](reports/validation.md) registra as verificações realizadas e seus limites.

## Limites

As fontes tratam principalmente de adultos e contêm muitas recomendações pragmáticas de consenso. Não extrapole automaticamente para crianças, gestação ou condições que exijam protocolo próprio. Não diagnostique deficiência apenas por relato de baixa ingestão. Não apresente a proposta de suplementação vitalícia do artigo de perspectiva como evidência de benefício universal.

Os três PDFs principais estão cobertos; o suplemento online citado pelo consenso europeu não foi fornecido. Os textos integrais, páginas, índice e PDFs fornecidos acompanham o plugin; não é necessário baixar arquivos por fora.
