> **Quando ler:** Passo 7: só quando ele pedir para cadastrar um alimento que não está na tabela.

# Passo 7 — Cadastro de alimento novo

1. Base do rótulo (100 g, porção de N g, unidade, N ml). Não está claro → **pergunte**.
2. `catalogo.converter_para_unidade(valores, base)`.
3. Origem da proteína: `inferir_origem_proteina()` resolve a maioria (laticínio, ovo, carne,
   peixe e suplementos são animais). Declare o que assumiu; só pergunte no ambíguo.
4. `validar_valores()` — recusa o impossível.
5. `campos_vazios()` — **liste o que ficará valendo zero nas dietas.**
6. Confira duplicidade com `resolver()` antes de gravar.
7. Grave em `ambiente.arquivo_alimentos(perfil)` — **nunca na planilha**.
8. Mostre o resumo: "1 g de X = 0,80 g de proteína animal. Confere?"
9. `pares_acima_de(catalogo)` — avise se o alimento novo criou risco de troca.
