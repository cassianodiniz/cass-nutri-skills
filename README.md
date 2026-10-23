# Cass Nutri Skills

Plugin para nutricionistas. Versão 0.3.0. Contém **cass-dieta** e **cass-book-biodisp-nutrients**.
O nutricionista toma as decisões clínicas; a skill executa a prescrição informada,
confere o cálculo e prepara o documento depois da revisão autorizada.

## Fonte

A base de 22 arquivos foi importada originalmente de
[cass-dieta.skill](https://skills.praxios.com.br/assets/cass-dieta.skill).
SHA-256: `07b57c4fcc1bc16ca2fbcbcc7924ce601dcabc92184930f4c51a56fb65b738c6`.
Desde a versão 0.3.0, a cass-dieta inclui filtros por FODMAPs, lactose e restrições
informadas pelo profissional: alimento/porção/fonte, três resultados (compatível,
incompatível, verificar), conferência de modelos e alternativas. Não inclui uma
base clínica completa nem presume classificação pela memória do modelo. Dados e
restrições permanecem nas pastas externas do profissional e do paciente.

A distribuição pública não é uma cópia exata da dieta pessoal do autor: a planilha
é preparada para distribuição e esta versão ainda não inclui o recurso local de
alternativas textuais no documento. Não usa pacientes ou perfis do autor.

## Instalar

```sh
codex plugin marketplace add cassianodiniz/cass-nutri-skills --ref main
codex plugin add cass-nutri-skills@cass-nutri-skills
```

Depois peça: “Use cass-dieta para montar a prescrição que vou informar”.
Para consultar a obra, peça: “Use cass-book-biodisp-nutrients para consultar meu corpus local”. A consulta bibliográfica é separada da prescrição; não altera a dieta automaticamente.

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

## Biodisponibilidade de Nutrientes

A skill `cass-book-biodisp-nutrients` integra o corpus de Cozzolino com busca por
página e conferência de proveniência. O livro é uma fonte histórica; informação
atual não deve ser atribuída a ele. Sua transcrição, o índice SQLite e os registros
privados não são distribuídos neste repositório público.

No primeiro uso, forneça o arquivo `.skill` de uma cópia a que você tenha acesso
autorizado. A preparação guarda o corpus em `~/.cass-book-biodisp-nutrients/corpus/`,
confere hashes internos, a liberação da extração e a integridade SQLite e preserva
qualquer instalação anterior. O plugin só distribui a integração e o preparador.
Python 3.10+ com sqlite3 é suficiente; não precisa instalar bibliotecas adicionais.

Comandos a partir da pasta `skills/cass-book-biodisp-nutrients/`:

```sh
python3 scripts/corpus_local.py instalar --pacote /caminho/da-copia-autorizada.skill
python3 scripts/corpus_local.py verificar
```

O preparador não faz consultas nem altera o buscador, o índice ou o conferente
originais. Depois da preparação, a skill lê as instruções originais na pasta
privada e executa aquele motor. Atualizar o plugin preserva essa pasta externa.
Não envie o corpus para o GitHub; não coloque dados ou registros do usuário no
plugin. Se o corpus não estiver disponível, a skill informa a pendência em vez
de apresentar memória do modelo como conteúdo consultado.

O pacote fonte verificado nesta versão tem SHA-256
`8881d2600aba87058a46eafbaa85ec2417c2f348240227993fad7fa8c9b41d1c`.
Os testes do preparador usam somente conteúdo sintético:
`python3 -m unittest discover -s tests -p 'test_*.py' -v`.
