# Cass Nutri Skills

Plugin para nutricionistas. Versão 0.1.0. Contém somente **cass-dieta**.
O nutricionista toma as decisões clínicas; a skill executa a prescrição informada,
confere o cálculo e prepara o documento depois da revisão autorizada.

## Fonte

Os 22 arquivos foram importados sem alterações de
[cass-dieta.skill](https://skills.praxios.com.br/assets/cass-dieta.skill).
SHA-256: `07b57c4fcc1bc16ca2fbcbcc7924ce601dcabc92184930f4c51a56fb65b738c6`.
A distribuição pública não é uma cópia exata da dieta pessoal do autor: a planilha
é preparada para distribuição e esta versão ainda não inclui o recurso local de
alternativas textuais no documento. Não usa pacientes ou perfis do autor.

## Instalar

```sh
codex plugin marketplace add cassianodiniz/cass-nutri-skills --ref main
codex plugin add cass-nutri-skills@cass-nutri-skills
```

Depois peça: “Use cass-dieta para montar a prescrição que vou informar”.
O plugin contém apenas essa skill; entrevista e pesquisa não foram adicionadas.

## Preparação e arquivos permanentes

Python, LibreOffice e um motor de PDF são necessários. A skill verifica o ambiente
antes do atendimento e só instala dependências com autorização, sem senha.
Leia `skills/cass-dieta/references/1-ambiente.md`.

Perfis, cadastros e o ambiente WeasyPrint ficam em `~/.cass-dieta/`, fora do plugin.
As planilhas e documentos dos pacientes ficam no consultório confirmado pelo
profissional. A planilha-modelo distribuída permanece somente para leitura;
os cálculos usam cópias descartáveis e as versões anteriores são preservadas.
Atualizar o plugin não deve substituir esses diretórios externos. Nunca salve
perfis, pacientes ou prescrições dentro da pasta instalada do plugin.

Uma dieta local existente continua independente. Use o nome do plugin/skill
explicitamente para testar esta distribuição sem substituir sua instalação local.

## Atualizações e validação

Novas versões são publicadas neste GitHub. A disponibilidade do refresh automático
depende do cliente; no Codex CLI, o catálogo pode ser atualizado com
`codex plugin marketplace upgrade cass-nutri-skills`, seguido de
`codex plugin add cass-nutri-skills@cass-nutri-skills`.
Não há garantia de que um chat já aberto recarregue as instruções.

`python3 tests/validar_pacote.py` confere manifesto, arquivos, links, sintaxe e hash
da planilha. Isso valida o empacotamento, sem substituir a conferência clínica ou
provar um atendimento real em todos os sistemas. A skill informa os limites de
plataforma e faz sua própria conferência do cálculo antes de gerar documentos.
