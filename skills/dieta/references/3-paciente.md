> **Quando ler:** Passo 4: escolher, criar, renomear ou retomar um paciente, e o modo consulta (porta 3).

# Passo 4 — Qual paciente

`paciente.recentes(consultorio)` traz os últimos atendidos. Mostre esses, não a lista
inteira: quem tem consultório cheio volta quase sempre a um dos últimos, e para o resto
existe `paciente.procurar(consultorio, texto)` — que acha sem acento e sem ligar para
maiúscula.

**`recentes` só traz quem tem dieta.** O consultório de verdade tem `Contratos`,
`Fotos antes e depois` e `_Modelo` ao lado dos pacientes, e oferecer "atender Contratos"
queima a confiança na lista inteira. Quem ele criou à mão e ainda não atendeu **não some do
consultório** — aparece em `procurar()` e em `listar()`, e `existe()` continua barrando criação
por cima. Se ele disser um nome que não está nos recentes, procure antes de concluir que é novo.

**Paciente conhecido:** `paciente.conferir(consultorio, nome, MESTRE)` **antes de perguntar
qualquer coisa**. Reclamou, resolva primeiro — as mensagens já vêm escritas e já dizem o que
fazer (planilha aberta no Excel, salva como `.xlsx`, pasta sumida).

Passou: abra com `paciente.caminho_da_planilha()`, leia `planilha.ler_ficha(pack)` e
`planilha.ler_opcoes(pack)` (todas as refeições, cada uma seguida das opções dela), e **mostre
onde ele parou antes de perguntar o que fazer**:

Na mesma abertura, leia `restricoes.md` na pasta desse paciente e apresente as
restrições guardadas. Antes de filtrar alimentos ou fazer ajustes por qualquer
porta, confirme se continuam válidas e siga `filtros-alimentares.md`. Isso também
vale para a porta 1 e para um ajuste iniciado dentro da porta 3, que não passam
pelo Passo 5. Arquivo ausente ou ilegível não significa “sem restrições”: colha a
orientação faltante antes do ajuste. Na porta 3 só de consulta, apresente o que
está registrado sem gravar mudanças; não transforme a consulta em prescrição.

> **João Pedro** — última mexida em 12/06
> Ganho de massa · Harris-Benedict · 82 kg · 1,78 m · 41 anos · FA 1,6
> Café da manhã: Pão 60 g · Ovo inteiro 2 · Queijo 20 g
> Almoço: Peito de Frango 150 g · Arroz 100 g · Feijão 100 g
> Você gostaria de:
> **(1) Ajustar mantendo o objetivo** (Ganho de massa, que está na tabela)
> **(2) Ajustar para um novo objetivo?** (por exemplo: trocar de emagrecimento para ganho de massa)
> **(3) Ainda não decidi** — abrir e olhar; dá para ajustar depois, se quiser

A pergunta é **sempre esta, com as três portas** — a porta 1 cita o objetivo gravado na
tabela, e o exemplo da porta 2 é obrigatório: é ele que faz o nutricionista entender do que
se trata. O que cada porta liga:

| Porta | O que fazer |
|---|---|
| **1 — manter o objetivo** | a fórmula fica a que está gravada, **sem pergunta nenhuma sobre fórmula**. Siga para os ajustes |
| **2 — novo objetivo** | pergunte o objetivo novo e siga o **Passo 5, "Trocou o objetivo"** — a fórmula sugerida, as outras e o valor manual, sempre as três portas abertas |
| **3 — ainda não decidi** | modo consulta: mostre tudo e responda o que ele perguntar, sem pressa e sem empurrar decisão. **Nada é gravado na planilha do paciente.** Pergunta numérica ("quanto dava de proteína?") é respondida por **cálculo descartável em cópia** — a planilha dele não muda |

Na porta 3, **mostrar a dieta é mostrar a dieta com os totais**: o verbatim vem com a tabela
de macronutrientes logo abaixo — macros com unidade ("95 g", "381 kcal"), total e diferença
pra meta. Os totais não ficam guardados (são fórmula), então avise em uma linha que vai
calcular (alguns segundos) e rode `planilha.calcular_dieta(...)` com a planilha dele e
**sem** `salvar` (Passo 8), com `ficha={}` e sem `dietas` — o arquivo dele não muda. **O cálculo falhou? O verbatim sai mesmo
assim**, com uma linha dizendo que os totais não saíram e por quê — a dieta dele nunca fica
refém da conta. Pediu de novo: **calcule de novo**, nunca repita número de um cálculo anterior
(alguém pode ter mexido no arquivo no meio). A abertura da retomada continua instantânea, sem
tabela — ela entra quando ele pede pra ver a dieta.

Dentro da porta 3, a decisão pode chegar no meio da conversa — e aí **não reapresente o menu**:

| Ele disse | O que fazer |
|---|---|
| um ajuste, sem falar de objetivo ("troca o arroz para 120 g") | siga como a **porta 1**, declarando em uma linha: *"seguindo com o objetivo Emagrecimento, que está na tabela"*. A linha é a chance dele corrigir — nada muda em silêncio |
| um objetivo novo em qualquer forma | caia no fluxo da **porta 2** (fórmula sugerida + as outras + valor manual) |
| encerrou sem decidir ("é só isso, obrigada") | feche dizendo em uma linha que **nada foi alterado** na planilha dele |

Meta e totais **não** aparecem aqui: são fórmula, e a planilha é guardada sem os valores em
cache. Eles voltam no primeiro cálculo. Diga isso se ele perguntar, não invente número.

**Todo cálculo monta a planilha a partir do modelo atual** e leva para ela a ficha, as chaves
das abas e as 5 abas de dieta dele, ligadas ou não. Se `planilha.modelo_mudou(MESTRE, dele)`
devolver mais que zero, diga em uma linha que a planilha dele vai para a versão nova das contas
quando for salva, com a anterior guardada ao lado.

**Paciente novo:** `paciente.existe(consultorio, nome)` primeiro.

| Resultado | O que fazer |
|---|---|
| `None` | `paciente.criar(consultorio, nome, MESTRE)` e siga |
| devolveu um nome | **pergunte se é a mesma pessoa ou outra.** Nunca decida |

Sendo a mesma, é retomada. Sendo outra — duas pacientes chamadas Maria Silva é caso real —
peça um nome que diferencie as duas (bairro, sobrenome do meio). Criar por cima da pasta
existente é recusado pela skill, e é bom que seja: escreveria por cima da dieta da primeira.

**Renomear** (casou, ou o nome saiu errado na primeira consulta):
`paciente.renomear(consultorio, atual, novo)`. Acompanham a pasta, o arquivo da planilha **e o
nome gravado dentro dela** — sem esse último, o documento seguinte sairia assinado com o nome
antigo. **Os PDFs já entregues ficam com o nome antigo** — são documentos assinados que existem
impressos e na mão do paciente, e reescrever o nome deles depois seria adulterar registro
clínico. Diga isso a ele.

Reclamou que não conseguiu trocar o nome dentro da planilha: ela está aberta no Excel. A pasta
já foi renomeada e nada ficou pela metade — peça para fechar e renomear de novo.

**Quer só simular** ("quanto dá se eu trocar o arroz por batata doce?"): não crie paciente
nenhum. Trabalhe sobre uma cópia do modelo, mostre o resultado e não grave nada.
