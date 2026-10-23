> **Quando ler:** Passo 9: a revisão antes do documento.

# Passo 9 — Revisão, em duas etapas

**Etapa 1 — só o que a máquina decidiu.** Bloco curto, item a item, resposta obrigatória:

> Você disse "pão" — usei **Pão**
> Você disse "frango" — usei **Peito de Frango**
> Confirma os dois?

Sem "aprovar tudo". Substituição não pega carona na aprovação do documento.

As trocas também entram aqui, uma a uma: a linha completa, com as quantidades de
`trocas.linha_da_troca(troca, quantidade)`, para ele aprovar ou tirar. Só as aprovadas vão para
o documento (`trocas=` no Passo 10).

**Etapa 2 — a dieta completa**: ficha do paciente (peso, altura, fórmula), refeições com as
quantidades **e a medida vinda da planilha**, e os totais. Ele edita se quiser; mudou alimento
ou quantidade, recalcule.

**Diga sempre quanto a dieta ficou longe da meta** — `r["tmb"]["meta_kcal"]` e, na aba, o
`total_kcal` e a `diferenca_gcd`; é a informação que ele mais usa nesta etapa:

> Meta: 2.862 kcal (Harris-Benedict) · Dieta: 1.298 kcal · **faltam 1.564 kcal**

O documento do paciente não traz a meta, só o total — quem precisa da comparação é quem
prescreve. Sem ela na revisão, uma dieta pela metade do alvo passa parecendo normal: os totais
sozinhos não denunciam nada. **Apenas informe a diferença; ajustar quantidade para fechar a meta
é decisão dele (P5), nunca sua.**

**Mostre também a tabela de macros por alimento, em gramas** (R8.8) — uma linha por
alimento, agrupada por refeição, com as colunas Prot.A, Prot.V, CHO, G.Sat, G.Poli, G.Mono.
Vem de `r["abas"][i]["por_alimento"]`, lido das MESMAS células já calculadas pela planilha —
nenhuma conta nova é feita. As chaves de `macros` viram as colunas assim: `Ptn (A)` Prot.A ·
`Ptn (V)` Prot.V · `Carbs` CHO · `Fat` G.Sat · `Poli` G.Poli · `Mono` G.Mono. Exemplo:

> **Café da manhã**
> | Alimento + Quantidade | Prot.A | Prot.V | CHO | G.Sat | G.Poli | G.Mono |
> |---|---|---|---|---|---|---|
> | Pão Francês — 50 g | 0,0 | 4,2 | 28,5 | 0,3 | 0,1 | 0,2 |
> | Ovo — 100 g | 12,6 | 0,0 | 0,6 | 3,1 | 0,7 | 4,1 |

**Essa tabela é só desta conversa de revisão — o documento do paciente (Passo 10) não a
inclui**, só os totais de sempre.

**Com opções, mostre as calorias de cada uma lado a lado** (`r["opcoes"]`), para ele ver se
estão equilibradas:

> Jantar — opção 1: 186 kcal · opção 2: 105 kcal · opção 3: 232 kcal

Só informe; igualar as opções é decisão dele. O documento não traz essa comparação.

Planilha antiga pode ter uma opção sem a refeição principal de mesmo nome (um "Jantar - Opção 5"
sem jantar na aba principal). Ela fica fora da comparação e sai sozinha no fim do documento:
avise na revisão e pergunte se ele quer organizar.

**Primeira revisão deste profissional?** (`ambiente.falta_avisar_substituicoes(perfil)`) No fim
dela, diga `trocas.FRASE_SUBSTITUICOES` e marque com
`ambiente.marcar_aviso_substituicoes(perfil)`. Uma vez só: nunca repita, nem em outro paciente.

**Sem autorização explícita aqui, não existe PDF.**
