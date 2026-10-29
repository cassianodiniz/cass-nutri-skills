# Evals ponta a ponta da recuperação multicapítulo

Data: 2026-08-08

## Veredito

- Integridade de fonte: **10/10 PASS**. Nenhum agente usou fonte externa e todos os trechos foram encontrados literalmente nas páginas declaradas.
- Qualidade semântica revisada: **10/10 adequadas** para as perguntas propostas. As respostas mantiveram ressalvas sobre estudos animais, controvérsias, associações e inferências.
- Tempo completo: mediana **71,13 s**, média **79,44 s**, mínimo **64,70 s**, máximo **116,57 s**.
- Busca local isolada: mediana de parede **394,63 ms**, máximo **985,22 ms** nas dez perguntas.

O tempo dominante não é o SQLite. Ele vem da leitura da skill, seleção das páginas, conferência literal, criação do registro temporário, execução do gate e redação da resposta.

## Casos

| ID | Pergunta resumida | Tempo | Fonte/evidência | Revisão semântica |
|---|---|---:|---|---|
| e01 | Vitamina E e outras vitaminas/minerais | 64,70 s | PASS | PASS após refinamento e reteste |
| e02 | Vitamina C com ferro e vitamina E | 116,57 s | PASS | PASS |
| e03 | Zinco e vitamina A | 71,49 s | PASS | PASS |
| e04 | Selênio, iodo e tireoide | 65,76 s | PASS | PASS |
| e05 | Facilitadores e inibidores do ferro | 82,51 s | PASS | PASS |
| e06 | Fitato, fibra, zinco e minerais | 70,77 s | PASS | PASS |
| e07 | Vitamina D, cálcio e osso | 65,65 s | PASS | PASS |
| e08 | Folato e vitamina B12 | 74,59 s | PASS | PASS |
| e09 | Vitamina E, cardiovascular e câncer | 68,71 s | PASS | PASS |
| e10 | Micronutrientes após bariátrica | 113,67 s | PASS | PASS |

## Falhas encontradas e corrigidas durante a campanha

1. A busca antiga devolvia páginas em ordem física e podia parar antes das ocorrências importantes.
2. `vitamina E` produzia falso positivo em frases como `vitamina em eritrócitos`; códigos de vitaminas de uma letra agora são reconhecidos com caso preservado na fonte.
3. O snippet podia selecionar outro parágrafo da mesma página; agora ele contém o tópico detectado.
4. O agente alterava pontuação ao montar a evidência e o gate rejeitava corretamente. O buscador agora entrega `evidence` literal, sem reticências artificiais.
5. A primeira versão do ranking multicapítulo favorecia coocorrências genéricas. O ranking final exige tópico principal, outro nutriente e sinal relacional na mesma frase para aplicar o bônus.
6. O registro interno apareceu como edição da skill durante um teste. A skill agora obriga o uso de `/tmp/`.

## Limite de desempenho

A versão final entrega com fidelidade, mas não é instantânea: perguntas amplas ficaram em torno de um a dois minutos. Remover o gate de proveniência reduziria tempo, porém diminuiria a proteção contra respostas inventadas ou misturadas. A recomendação é manter o gate e distinguir:

- pergunta focada: 2–4 evidências centrais;
- pergunta multinutriente ampla: até 6 evidências e expectativa de 60–120 segundos.

## Artefatos verificáveis

- `tests/test_retrieval_v2.py`: 15 testes técnicos.
- `scripts/test_provenance_guard.py`: 9 cenários de pressão do gate.
- `evals/questions.json`: dez perguntas.
- `evals/results/2026-08-08/`: respostas estruturadas dos agentes.
