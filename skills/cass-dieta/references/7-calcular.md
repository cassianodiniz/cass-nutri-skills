> **Quando ler:** Passo 8: todo cálculo — o comando único, o que ele devolve e quando para.

# Passo 8 — Calcular

Um comando só faz o ciclo inteiro — monta, calcula, confere e grava. **Não monte o ciclo à mão
com as funções soltas** (`preparar_copia`, `escrever_refeicoes`, `calcular`…): era assim que
dieta alternativa sumia e o alimento de teste da skill ia parar na planilha do paciente.

```python
soffice = ambiente.achar_libreoffice()
caminho = paciente.caminho_da_planilha(pasta_do_paciente)   # novo: o que criar() devolveu
meus_alimentos = catalogo.listar_alimentos(ambiente.arquivo_alimentos(perfil))

r = planilha.calcular_dieta(
    MESTRE, HASH, soffice,
    ficha=ficha,                      # paciente novo: tudo o que ele disse; retomada: só o que mudou
    dietas={"Cálculo de Dieta": refeicoes},   # com opções: planilha.distribuir_opcoes(lista)
    planilha_paciente=caminho,
    paciente_novo=paciente_novo,
    alimentos_usuario=meus_alimentos,
    salvar=True)                      # consulta e simulação: salvar=False
```

`refeicoes` é a lista `[{"nome": "Almoço", "itens": [(nome_planilha, quantidade), ...]}]`.
**Aba passada em `dietas` é reescrita inteira**: na retomada, leia a dieta dela
(`planilha.ler_dieta`), aplique a mudança e passe **todas** as refeições daquela aba — passar só
a que mudou apaga as outras. Abas que não foram passadas ficam exatamente como estavam.

O que volta em `r` — os números já vêm prontos também quando `salvar=True`; não rode outro
cálculo só para reler:

| Campo | O que é |
|---|---|
| `problemas` | lista já escrita para o nutricionista. **Não vazia: nada foi gravado** — mostre como veio (já nomeia o alimento culpado) e pare |
| `tmb["meta_kcal"]`, `formulas` | a meta e as seis fórmulas (para dizer qual produziu o número) |
| `abas` | uma por aba com dieta, a principal primeiro: `refeicoes`, `macros`, `total_kcal`, `diferenca_gcd`, `micros`, `por_alimento` |
| `opcoes` | por refeição que tem opções: o nome e as kcal de cada opção, lidas da planilha |
| `salvo`, `backup` | onde gravou e a versão anterior guardada ao lado |

Ficha recusada ou conta que o LibreOffice não confirmou chegam como erro (`ErroPlanilha`) com a
mensagem pronta: repasse e não gere documento.

**Salve aqui, não depois da autorização do documento.** Um atendimento inteiro — ficha, cinco
refeições, quarenta alimentos ditados — se perderia se ele fechasse a janela na revisão. A
planilha é o trabalho dele; o PDF é o que foi entregue. Mudou alguma coisa na revisão e
recalculou? Salva de novo. Avise que leva alguns segundos.

**Com opções, o total e a meta são os da dieta principal** (`r["abas"][0]`). O total de uma
aba alternativa sozinho não quer dizer nada — ela só tem as refeições que têm opção — então
nunca o compare com a meta.
