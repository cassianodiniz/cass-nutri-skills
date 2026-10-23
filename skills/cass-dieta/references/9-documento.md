> **Quando ler:** Passo 10: gerar e entregar o PDF, depois da autorização dele.

# Passo 10 — O documento

**Referência visual aprovada:** consulte [design-aprovado.md](design-aprovado.md) ao
trabalhar no layout. A amostra aprovada está salva em `assets/modelo-visual-aprovado.html`;
o registro também identifica o que ainda falta aplicar ao renderizador.

Pergunte antes: mostrar calorias e macronutrientes ao paciente? E micronutrientes
(desligados por padrão)?

Se ele desligar itens exigidos pela norma, exiba **uma vez** `documento.TEXTO_CFN` e registre
a escolha. **Não bloqueia** — ele decide.

**Ligou os micronutrientes?** `micros=True` em `montar_doc` — é só isso. A adequação
(total ÷ recomendado) já vem calculada pela própria planilha e **sempre aparece**, pra todo
micronutriente (R9.15, decisão Cassiano 04/08/2026: nunca esconder um número que já existe).

**A cor do documento** vem do perfil: `cor=perfil.get("cor")`. Sem cor
gravada, sai o verde padrão — não pergunte a cada documento. As 7 opções estão em
`documento.PALETAS` (verde, azul, roxo, mostarda, laranja, vermelho, marrom). Quando o
nutricionista pedir pra trocar ("muda a cor pra azul"), grave no perfil
(`perfil["cor"] = "azul"` + `ambiente.adicionar_perfil(perfil)`) e confirme em uma linha —
vale pra todos os documentos dali em diante. Cor que não existe na lista: diga as válidas e
espere; nunca escolha parecida por conta.

```python
doc = documento.montar_doc(r, perfil, {"nome": nome_paciente, "objetivo": objetivo}, data,
                           mostrar_numeros=mostrar, micros=micros, cor=perfil.get("cor"),
                           trocas=trocas_aprovadas)   # as que ele aprovou na revisão
with planilha.PastaDeTrabalho() as pasta:
    html = documento.montar_html(doc)
    pdf = documento.gerar_pdf(html, doc, None, navegador, pasta, weasyprint=weasyprint)
    final = documento.entregar(pdf, pasta_do_paciente, nome_paciente, objetivo, data)
```

`montar_doc` monta o conteúdo a partir do cálculo (`r` do Passo 8): **nunca copie número nem
alimento para o documento à mão.** `weasyprint` é o interpretador achado no Passo 1 (pode ser
`None`; aí a rota é o navegador).

Conferência do HTML reprovou (dentro de `gerar_pdf`) = não gera PDF nenhum. `entregar` confere
o arquivo que chegou e recusa mais de 3 páginas = não entrega. O que a conferência acusou é dito
ao nutricionista em uma linha — nunca resolvido em silêncio.

Sai `João Pedro - Ganho de massa 28-07-26.pdf`, **na pasta do paciente**, ao lado da planilha
dele. `entregar()` é a **última** operação do atendimento — a planilha já foi gravada no
Passo 8.

O objetivo é texto livre e pode ter barra ou virar uma frase inteira. A skill limpa e encurta
sozinha; **mostre o nome do arquivo antes de salvar** e deixe ele encurtar se quiser.

Se a pasta for sincronizada com nuvem (`pasta_e_sincronizada`), avise uma vez que o arquivo vai
para a internet.

**Termine abrindo a pasta do paciente:** `ambiente.abrir_pasta(pasta_do_paciente)`. Não pergunte
se ele quer — abra. Dizer o caminho e parar transfere para ele uma tarefa de computador; a pasta
aberta com o documento dentro é o trabalho entregue. Diga em uma linha o que apareceu na tela.

Abra a **pasta**, nunca o arquivo: abrir a planilha a deixaria travada para o próximo cálculo.
