# Recuperação multicapítulo v2

## Problema observado

O buscador anterior exigia que todos os termos aparecessem em uma página, percorria as páginas em ordem numérica e parava no limite. No baseline, `vitamina E interação` começou por páginas sobre recomendações gerais e outros nutrientes, sem priorizar o capítulo 12 nem garantir cobertura global.

## Mecânica

1. Detectar o nutriente por aliases delimitados e sensíveis aos códigos de uma letra.
2. Consultar o mapa completo de menções no SQLite.
3. Dar prioridade ao capítulo principal sem excluir outros capítulos.
4. Favorecer páginas que contêm todos os tópicos de uma pergunta relacional.
5. Classificar pelos termos e sinais do pedido.
6. Diversificar por capítulo antes de repetir páginas do mesmo capítulo.
7. Entregar caminhos de páginas reais para conferência obrigatória.

## Decisão sobre grafo

O núcleo não usa Graphify. Relações inferidas por modelo poderiam parecer fatos do livro. FTS5 acelera texto livre, enquanto o mapa determinístico preserva cobertura e proveniência. Um grafo futuro só deve materializar relações já confirmadas em páginas e manter a página em cada aresta.
