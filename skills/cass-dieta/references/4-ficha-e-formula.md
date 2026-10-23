> **Quando ler:** Passo 5: dados do paciente (peso, altura, idade, sexo, FA, objetivo) e a fórmula de gasto calórico.

# Passo 5 — Dados do paciente

Colha também as restrições alimentares ainda não informadas: intolerância à
lactose, orientação para FODMAPs e exclusões específicas. Leia
`filtros-alimentares.md` e registre a orientação confirmada na pasta do paciente.
Na retomada, apresente o que foi guardado para confirmar mudanças.

**Pergunte os dados ANTES da fórmula** (decisão Cassiano 04/08/2026). A ordem:

1. Peso, altura, idade, sexo, fator de atividade, objetivo — numa pergunta só ou como ele
   preferir ditar. Gestante só quando o sexo for feminino.
2. **A fórmula por último**, já sugerindo pela tabela abaixo a partir do objetivo dito.
3. O % de gordura NÃO entra na lista inicial: é pedido logo depois da escolha da fórmula,
   **apenas quando ela exigir** (4 ou 5). Quem usa as outras nunca ouve essa pergunta.

| # | Fórmula | O nutricionista usa para | Exige % gordura |
|---|---|---|---|
| 1 | Harris-Benedict | crescimento muscular, desempenho, ganho de peso, **gestação** | não |
| 2 | Mifflin | emagrecimento | não |
| 3 | Tinsley (peso) | atletas | não |
| 4 | Tinsley (massa livre de gordura) | atletas | **sim** |
| 5 | Cunningham | atletas | **sim** |
| 6 | Valor definido por ele | calorimetria, ou arbítrio profissional | não (pede as kcal) |

**Para condição de saúde — hipertensão, diabetes, doença renal — não existe fórmula
recomendada aqui.** Se ele perguntar qual usar nesses casos, **diga que você não tem essa
orientação** e devolva a escolha. Não deduza por analogia e não invente recomendação clínica.
Vale para qualquer objetivo fora da tabela acima.

**A fórmula é escolhida no início do objetivo e se mantém por meses.** Não pergunte a cada
dieta: na retomada, use a que está gravada (`ler_ficha` traz em `formula`).

**Trocou o objetivo → ofereça trocar a fórmula.** Sempre com as três portas abertas:

> Você mudou de "ganho de massa" para "emagrecimento". Para emagrecimento você usa Mifflin:
> 2.788 kcal. As outras dão: Harris-Benedict 2.911 · Tinsley (P) 3.190 · Tinsley (MLG) 3.173 ·
> Cunningham 3.109. Ou me passe o valor que quiser usar. Qual vai ser?

A terceira porta é o caso da **calorimetria indireta**: ele tem a medida real do paciente, e
nenhuma estimativa ganha de um valor medido. Vai em `gcd_manual` com a fórmula 6.

**Sempre que mostrar calorias a ele, diga qual fórmula produziu** (`nome_da_formula`). Nunca um
número solto — as seis saem juntas de `ler_formulas()` e diferem em até 14% para o mesmo
paciente.

**Escolheu 4 ou 5 (`exige_gordura`)?** Peça o % de gordura antes de calcular, explicando que sem
ele a fórmula não fecha. O campo `TMB!C15` **por natureza fica em branco** — quem decide
preencher é o nutricionista. Você nunca estima, nunca converte de outro dado.

O fator de atividade em palavras — sedentário 1,2 · pouco ativo 1,3-1,4 · moderado 1,5-1,6 ·
muito ativo 1,7-1,8 · extremamente ativo 1,9+. **Dito em palavras, use o meio da faixa e
declare na hora qual número usou** ("anotei FA 1,75 — se preferir outro valor da faixa, me
diga"); dito em número, use o número (R4.14).

**Não pergunte gestante quando o sexo for masculino.**

**Passe a ficha como ele disse — quem confere é o código.** Sexo por extenso vira M/F; altura
em metros, medida fora da faixa (peso 20-300 kg · altura 100-250 cm · idade 1-120 · gordura
3-70%), fórmula fora de 1 a 6, fórmula 4/5 sem % de gordura e fórmula 6 sem o valor em kcal são
recusados com o motivo escrito (a planilha usa altura em centímetros). Recusou: repasse a mensagem e pergunte — nunca corrija o número
por conta própria (1,78 não vira 178 sem ele confirmar).

**Gestante e % de gordura:** não dito = fica o que estava; "não" = apaga. A planilha considera
gestante qualquer coisa escrita no campo, por isso nunca escreva "não" lá à mão.

**Paciente novo começa do zero** (`paciente_novo=True` no Passo 8): campo não dito fica vazio, e
nada é herdado de outro paciente.

**Retomada leva tudo o que já estava** — passe só o que mudou nesta consulta. Mas **declare o
que herdou e espere resposta antes de calcular**:

> João Pedro — herdei da última consulta: 82 kg, 1,78 m, FA 1,6, objetivo "ganho de massa",
> fórmula Harris-Benedict. Mudou alguma coisa?

Sem isso, um paciente que emagreceu 6 kg sai com a dieta calculada no peso velho e ninguém vê.
