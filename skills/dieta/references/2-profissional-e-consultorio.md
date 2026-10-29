> **Quando ler:** Passos 2 e 3: saber quem assina e onde ficam as pastas dos pacientes — no primeiro uso, com dois profissionais, ou quando a pasta de pacientes sumiu.

# Passo 2 — Quem está emitindo

`ambiente.carregar_perfis()`, depois `ambiente.perfil_unico(perfis)`.

| Situação | O que fazer |
|---|---|
| Nenhum perfil | peça nome completo, CRN com região e os contatos do rodapé |
| `perfil_unico` devolveu alguém | **use, sem perguntar nada.** Siga direto |
| `perfil_unico` devolveu `None` (dois ou mais) | mostre `confirmacao_de_identidade()` de cada um e **espere escolher** |

Com um profissional só não há ambiguidade, e perguntar "qual nutricionista?" em toda dieta é
ruído que a pessoa aprende a responder no automático — e resposta no automático não protege
ninguém. Com dois a pergunta volta a valer: a prescrição sai com o CRN de quem assina.
A rede que substitui a pergunta é a revisão do Passo 9, onde o CRN aparece antes da autorização.

**Cadastrar um segundo profissional só acontece se ele pedir com todas as letras.** Não ofereça.
O que identifica o profissional é o número do CRN: "CRN 108212" e "108212" são o mesmo perfil, e
a skill junta sozinha perfis e cadastros duplicados. Se ela parar dizendo que achou o mesmo
alimento duas vezes com dados diferentes, mostre a mensagem e espere ele dizer qual vale.

Ele pode ver, corrigir e apagar perfil a qualquer momento.

Sugira identificar o paciente por iniciais durante a conversa; peça o nome completo só no
Passo 9.

## Passo 3 — Onde ficam os pacientes

`ambiente.conferir_consultorio(perfil)`. Lista vazia: siga, já está resolvido.

**Nunca registrado: primeiro OLHE, só depois pergunte.**
`ambiente.consultorios_candidatos(perfil)` varre a máquina e traz as pastas que já têm cara de
consultório, cada uma com os nomes de quem está dentro.

| O que voltou | O que fazer |
|---|---|
| **uma só** | mostre com o caminho inteiro e quem está dentro, e **pergunte se é essa mesmo**. Uma candidata não é uma resposta |
| duas ou mais | mostre **cada uma** com o caminho inteiro e quem está dentro, e **espere ele escolher**. A primeira é a mais cheia, não a escolhida |
| nada | ofereça `ambiente.caminho_padrao_consultorio(perfil)` — `Documentos/Pacientes - <nome dele>` |

**Achar não é decidir. A pasta só fica valendo com ele confirmando, nos três casos.** Ele pode
ter uma pasta que você não achou, ou querer começar uma nova mesmo tendo outra — a que ele usa
para outra coisa não vira consultório porque o nome bateu.

Perguntar "você já tem uma pasta de pacientes?" sem ter olhado antes entrega a um leigo a
tarefa de lembrar um caminho, e "acho que sim" vira pasta nova. Foi assim que apareceram duas
pastas de pacientes na mesma máquina em 31/07 — uma com paciente de verdade e contrato dentro,
outra criada pela skill. **Criar não foi o erro** (ela nunca havia perguntado onde era) — o
erro foi não ter olhado antes de perguntar.

**Mostre o caminho inteiro antes de criar e espere ele confirmar.** Não é formalidade: em
máquina com OneDrive existem duas pastas chamadas "Documentos", e a que o sistema reporta pode
não ser a que ele enxerga como sua. Se `ambiente.documentos_alternativos()` devolver alguma
coisa, diga que há mais de uma e deixe escolher.

**A pasta sumiu** (`conferir_consultorio` reclamou): ele moveu, renomeou ou trocou de
computador. **Pergunte onde ela foi parar — nunca crie outra em silêncio.** Duas pastas com
metade do histórico em cada é o pior desfecho possível aqui.

Criou: `ambiente.criar_consultorio()` e depois `ambiente.definir_consultorio(perfil, caminho)`.

Se `documento.pasta_e_sincronizada(caminho)`, avise **uma vez** que tudo que for guardado ali
— planilhas e PDFs de pacientes — vai para a internet junto. E que é isso que protege o
trabalho dele se o computador queimar. As duas coisas na mesma frase, senão parece contradição.
