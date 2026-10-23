> **Quando ler:** Passo 1: no início de todo atendimento, e quando faltar LibreOffice, navegador ou WeasyPrint.

# Passo 1 — Ambiente

1. `ambiente.achar_libreoffice()` e `ambiente.achar_navegador()`.
2. Faltando algum: apresente `ambiente.instrucoes_de_instalacao()` e **espere o usuário
   decidir**. Explique antes o que vai aparecer na tela e quanto tempo leva.
   - Passo marcado `manual` exige senha → **mostre o comando para ele colar**, não execute.
   - Download direto → confira com `conferir_integridade()` antes de abrir. Não conferiu,
     não abre.
3. Instalou: `conferir_libreoffice()` para garantir que responde.
4. `ambiente.achar_weasyprint()` — o motor preferido para o PDF (Passo 10). Achou, guarde o
   interpretador devolvido. Não achou e há navegador: **no Mac, recomende instalar o
   WeasyPrint mesmo assim** — o navegador comprovadamente trava lá (Chrome headless, bug
   conhecido). Nenhum dos dois: aplique o mesmo protocolo do item 2
   (`ambiente.instrucoes_de_instalacao_weasyprint()`, sem senha, explicando antes) e confirme
   com `ambiente.conferir_weasyprint()` ao final.

## Onde isto foi verificado de verdade

Declarado por honestidade, não por burocracia — quem usa assina um documento clínico.

| | Situação |
|---|---|
| Windows 11 · LibreOffice 26.2.5 · Edge | ✅ verificado, com dieta cheia (120 itens) |
| macOS · LibreOffice 26.2 · WeasyPrint | ✅ verificado, com dieta cheia (120 itens) |
| Linux | ⚠️ **nunca executado.** Os caminhos existem no código, mas ninguém rodou |
| Outras versões do LibreOffice | ⚠️ não testadas |

**Por que isso não trava a skill:** o cálculo do Passo 8 mede o **resultado**, não o sistema.
Ele grava um alimento próprio com valores conhecidos numa cópia descartável e exige que a
planilha devolva exatamente esses números, coluna por coluna. Se o LibreOffice daquele sistema
ou versão não recalcular direito, ele **para antes de gravar ou gerar qualquer documento**.

**No primeiro uso no Linux:** avise uma vez que a skill ainda não foi rodada naquele sistema, e
peça que o nutricionista confira o primeiro documento com atenção.
