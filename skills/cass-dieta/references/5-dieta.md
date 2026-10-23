> **Quando ler:** Passo 6: a dieta ditada — resolver alimentos, "ou", refeições modelo, opções por refeição e a tabela de cada refeição.

# Passo 6 — A dieta ditada

O catálogo é o cadastro dele mais a tabela da planilha, nessa ordem:
`catalogo.montar_catalogo(planilha.Pacote(MESTRE), ambiente.arquivo_alimentos(perfil))`.
Para cada alimento: `catalogo.resolver(texto, catalogo)`.

| Resposta | O que fazer |
|---|---|
| `exato` | usa; se o texto era diferente, guarde para mostrar na revisão |
| `automatico` | usa, **e obrigatoriamente mostra na revisão** |
| `perguntar` | apresente as opções e espere — nunca escolha |
| `nao_encontrado` | mostre o que encontrou de parecido e ofereça cadastrar |

Depois `catalogo.conferir_unidade(alimento, unidade)`:

| Resultado | O que fazer |
|---|---|
| `ok` | segue |
| `perguntar` | **pare** — o alimento está numa medida diferente da que ele falou |
| `caseira` | pergunte quantos gramas ele considera. **Nunca converta.** |

### Refeições modelo

`catalogo.listar_refeicoes(ambiente.arquivo_refeicoes(perfil))`. Ele pediu "usa o modelo 1",
ou você percebe que a refeição é uma delas — mostre os alimentos e **pergunte as quantidades**:

> Café proteico — Pão, Ovo, Queijo prato, Maçã. Quanto de cada um?

**O modelo traz os alimentos; a dose é sempre dele.** Se ele tiver guardado quantidade junto,
ela aparece como sugestão a confirmar, nunca aplicada calada — modelo que prescreve dose é a
skill decidindo clínica (P5).

`catalogo.conferir_refeicao(modelo, catalogo)` **antes de usar.** Devolveu alguma coisa, aquele
alimento saiu do cadastro depois que o modelo foi criado: diga **qual** e siga com o resto, em
vez de quebrar a refeição inteira.

**Criar modelo a partir do que ele acabou de montar** é o caminho natural — ninguém senta para
cadastrar do zero. Ofereça quando ele repetir uma refeição, e use
`catalogo.refeicao_do_prato(nome, ...)`, que já guarda o nome exato da planilha. Peça um nome
que descreva ("Café proteico", "Almoço padrão"): na vigésima, "Modelo 3" não diz nada.

Outras regras deste passo:
- `ou` na fala ("macarrão ou mandioca ou arroz 150 g") → separe só a quantidade e passe o nome
  **inteiro, com os "ou"**, a `resolver`. Não divida antes: dividido, "arroz" e "mandioca" casam
  com os itens avulsos, que têm outros valores. O resultado já diz se é o item agrupado (em
  qualquer ordem), se ele libera algo que não foi dito, ou se são alimentos separados — o
  `aviso` vem escrito: repasse e espere a resposta.
- Item agrupado escolhido → avise quantas opções libera (`len(alimento.opcoes)`) e **de qual
  alimento são os valores**:
  `catalogo.fonte_dos_valores(pacote_do_modelo, alimento, catalogo)`. Devolveu `None`: diga que
  a tabela não informa de qual são.
- Quantidade e nome separados antes de resolver.
- Quantidade sempre número puro; "à vontade" vira quantidade + sufixo, nunca zero.
- Máximo **10 alimentos por refeição** e 12 refeições — avise se passar.

### Opções por refeição

Ele pode dar mais de uma opção para a mesma refeição ("Almoço - Opção 2", "Jantar - Opção 5").
Guarde o nome **como ele disse** e monte a lista inteira na ordem em que vai sair no documento
(cada refeição seguida das opções dela). `planilha.distribuir_opcoes(lista)` reparte pelas 5
abas: a opção N vai para a aba N, na mesma posição da refeição principal — é assim que a
planilha compara as calorias de cada opção com a principal. Refeição sem opção fica só na
principal. Passe o que ela devolveu direto em `dietas` (Passo 8).

- Até **5 opções** por refeição, porque a planilha tem 5 abas. Passou: `distribuir_opcoes`
  recusa com a mensagem pronta — repasse e espere ele escolher quais ficam.
- Opção 2 sem a 1 é recusada: a principal é a opção 1 (com ou sem esse nome).
- Retomada de quem tem opções:
  - mudou só refeição da principal (ou refeição sem opção) → passe **só a aba principal** em
    `dietas`; as outras abas ficam como estão;
  - mexeu numa opção (criou, mudou ou tirou) → comece de `planilha.ler_opcoes(pacote)` — a lista
    completa, na ordem do documento —, aplique a mudança e distribua de novo;
  - `distribuir_opcoes` recusou por causa de uma planilha antiga (opção sem a principal, por
    exemplo) → mostre a mensagem e pergunte como ele quer organizar. Não force.
- Opções são alternativas da mesma dieta, não dietas diferentes: **nunca some abas**, e a meta
  se compara só com a dieta principal.

### Trocas proporcionais

"Arroz ou Mandioca ou Macarrão - 100g ou Batata Doce - 150g ou Batata Inglesa - 220g": alimentos
com quantidades **diferentes** na mesma linha. A proporção é dele; a skill só multiplica. A
planilha calcula só pelo primeiro (o alimento-base); a linha completa sai no documento.
(Agrupado com uma quantidade só — "Arroz ou mandioca ou macarrão 150 g" — não é troca.)

- **Ditou uma troca:** `trocas.ler_troca_ditada(linha, catalogo)`. Voltou `pendencias`: pergunte
  com as opções que vieram, nunca escolha. Na dieta entra só o alimento-base, com a quantidade
  dita. Ofereça guardar como troca dele — com o sim,
  `trocas.salvar_troca(ambiente.arquivo_trocas(perfil), troca)`. Se ele já tiver troca para o mesmo alimento,
  ela recusa mostrando a atual: pergunte qual vale, e só com a escolha pela nova chame de novo
  com `substituir=True`.
- **Usou um alimento que tem troca guardada** (`trocas.troca_para(nome,
  trocas.listar_trocas(ambiente.arquivo_trocas(perfil)))`): a linha completa vai para a revisão
  (Passo 9) para ele aprovar ou tirar. Nada fica guardado por paciente: vale sempre a troca
  atual dele.
- **"Minhas trocas":** `listar_trocas` mostra, `salvar_troca` com o mesmo alimento-base edita,
  `remover_troca` apaga. No primeiro uso a lista dele já nasce com as trocas de exemplo do kit;
  ao mostrá-la pela primeira vez, diga que são exemplos e que ele pode mudar ou apagar.
- **Equivalência por carboidrato — só quando ele pedir** ("quanto de batata dá o mesmo
  carboidrato de 150 g de arroz?"): `trocas.equivalente_por_carboidrato(pacote_do_modelo,
  catalogo, base, quantidade, alvo)`. Mostre a `conta` e a sugestão; ela só vale com o sim dele,
  e pode virar troca guardada se ele quiser. Nunca ofereça essa conta por conta própria.
  Os nomes passam antes por `catalogo.resolver`, como qualquer alimento: "arroz" é o Arroz;
  se o resolver perguntar, pergunte a ele.
- O arredondamento de 5 em 5 g é do código e só vale para quantidade que a skill calculou;
  a que ele ditou fica como ele disse.

### A tabela da refeição, na hora (R8.9)

**Fechou uma refeição — todos os alimentos resolvidos e unidades conferidas — calcule e
mostre a tabela dela ali mesmo.** O mesmo vale quando ele **altera** uma refeição já ditada
(quantidade, troca ou remoção de alimento). Avise a espera ("calculando, leva alguns
segundos") e rode `planilha.calcular_dieta(...)` como no Passo 8, com TODAS as refeições até
aqui e **sem** `salvar`.

Ditou a dieta inteira de uma vez: **um cálculo só**, e a tabela de cada refeição sai dele.
A tabela sai de `resultado["abas"][i]["por_alimento"]`: uma tabela só da refeição que
acabou de fechar/mudar, colunas **Alimento | Quantidade** (separadas) + Prot.A, Prot.V, CHO,
G.Sat, G.Poli, G.Mono em gramas, e a linha **Total** vinda de `refeicao["totais"]` — a
planilha calcula essa linha em cada bloco; a skill só lê, **nunca soma**. Havendo mais de
uma refeição, acrescente a linha **Total da dieta** com `resultado["abas"][i]["macros"]` (a
coluna `gramas` dos 6 macros). Total em branco = a função já para com erro claro — repasse a
mensagem, nunca mostre zero no lugar.

O Passo 8 continua igual: o cálculo final antes da revisão roda sempre, por inteiro.
