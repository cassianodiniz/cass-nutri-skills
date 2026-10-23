# Modelo visual aprovado

Aprovado por Cassiano nesta conversa em 03/10/2026. A cópia exata da prévia está em
[assets/modelo-visual-aprovado.html](../assets/modelo-visual-aprovado.html).

Este arquivo registra o design escolhido. A amostra usa dados fictícios e a logo de
Cassiano; nas dietas reais, a marca, os contatos e a identificação vêm do perfil de cada
profissional. Não reutilizar os alimentos ou números da amostra como prescrição.

## Escolhas aprovadas

- Fundo branco, fonte sem serifa e textos pretos, inclusive assinatura, contatos e tabelas.
- Logo centralizada no topo; paciente e objetivo centralizados logo abaixo. Sem título
  “Plano alimentar” ou identificação adicional acima do paciente.
- Linha verde próxima ao objetivo. Margens laterais folgadas para todo o conteúdo.
- Nomes de refeições com fundo verde suave, detalhe à esquerda e linha verde abaixo,
  próxima ao texto. Linhas de alimentos compactas e intervalos iguais entre títulos e listas.
- Tabela de macronutrientes mais estreita que as refeições, com fonte menor e linhas
  compactas. Título próximo à tabela e centralizado sobre ela. Colunas numéricas centralizadas;
  nomes dos nutrientes alinhados à esquerda. Cabeçalho em verde suave.
- Assinatura somente na última página: linha, nome do profissional, CRN e data próximos.
  Contatos no rodapé de todas as páginas, com a linha verde próxima aos contatos.
- Detalhes geométricos nos cantos superior direito e inferior esquerdo: manter apenas a
  parte verde escura, sem a faixa de verde mais claro. Contatos permanecem no rodapé,
  sem coluna lateral.

## Medidas da prévia

As medidas em pixels descrevem a amostra de 700 px de largura; não são medidas físicas
de um PDF já validado. Consulte o HTML para a composição e os estilos completos.

| Elemento | Medida |
|---|---|
| Margens laterais | 42 px |
| Logo | 220 px de largura |
| Paciente / objetivo | 24 px / 13 px |
| Espaço do objetivo até a linha | 6 px |
| Refeições / alimentos | 14 px / 13 px |
| Espaço inferior do nome da refeição até a linha | 1 px |
| Linhas de alimentos | 3 px de espaço interno acima e abaixo |
| Tabela dos macros | 78% da largura do conteúdo; texto de 12 px |
| Título dos macros | 13 px; 4 px até a tabela |
| Linhas da tabela | 4 px de espaço interno acima e abaixo |
| Linha da assinatura até o nome | 6 px |
| Nome, CRN e data | Entrelinha de 1,15; sem margem extra entre linhas |
| Linha do rodapé até os contatos | 5 px |
| Verde das linhas / verde escuro dos cantos | `#009044` / `#1b4036` |

## Estado da aplicação

O modelo está aplicado em `scripts/documento.py`, preservando `montar_doc`, as conferências
e o conteúdo calculado. A verificação no macOS com WeasyPrint incluiu PDFs reais de uma,
duas e três páginas, rodapés em todas as páginas, assinatura somente no fim, outra paleta
e perfis com e sem logo. As evidências estão em
registro de desenvolvimento do autor (não distribuído).
Windows e outros ambientes não foram verificados após estas alterações.
