# Cass Nutri Skills

Versão 0.7.0 — pacote com fontes incluídas, pronto para consulta após instalar.

| Skill | Conteúdo incluído |
|---|---|
| dieta | Planilha, scripts e instruções de prescrição |
| biodisp-nutrients | PDF original e corpus integral de Cozzolino: 910 páginas, 53 capítulos, índice e conferência de proveniência |
| nutricao-canetas | Três PDFs originais, 51 páginas, textos integrais, imagens de revisão e índice de busca |
| exames-laboratoriais | PDF original de Costa (2013), 273 páginas extraídas, tabelas conferidas e 11 imagens de revisão |

Não é preciso fornecer os livros nem baixar fontes por fora para consultar esse
material. Os caminhos são relativos à skill instalada. As fontes históricas e os
limites de revisão visual continuam identificados; incluir a obra não a torna
diretriz clínica atual. O suplemento online não fornecido dos documentos de
canetas continua identificado como ausente.

## Instalação

```sh
codex plugin marketplace add cassianodiniz/cass-nutri-skills --ref main
codex plugin add cass-nutri-skills@cass-nutri-skills
```

Atualização: `codex plugin marketplace upgrade cass-nutri-skills`, seguido de
`codex plugin add cass-nutri-skills@cass-nutri-skills`.

Use `dieta`, `biodisp-nutrients`, `nutricao-canetas` ou `exames-laboratoriais`.
Scripts de consulta usam Python 3.10+. A prescrição com planilha requer as
ferramentas indicadas em dieta. Perfis, pacientes, documentos produzidos e
programas instalados continuam fora do plugin e são preservados nas atualizações.

## Validação

`python3 tests/validar_pacote.py` confere estrutura, contagens, fontes e integridade.
As buscas são verificadas também em cópia limpa sem configuração pessoal. Isso
confere distribuição e recuperação, não um atendimento clínico completo.
