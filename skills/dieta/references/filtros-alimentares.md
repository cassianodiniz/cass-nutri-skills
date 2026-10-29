# Filtros alimentares na prescrição

Leia ao colher as restrições, buscar alimentos ou revisar uma dieta com FODMAPs,
intolerância à lactose ou exclusões específicas informadas pelo nutricionista.
“Food maps” neste contexto significa FODMAPs; se houver dúvida, confirme.

## Definir o filtro

Na ficha, pergunte uma vez pelas restrições ainda não informadas. Na retomada,
confirme o que permanece. O nutricionista define o critério: filtrar opções,
apenas sinalizar a dieta ditada, quais alimentos/subgrupos restringir e a tolerância.
Não diagnostique pelos sintomas nem inicie uma dieta de exclusão por iniciativa própria.

- **FODMAPs:** registre a fase (redução, reintrodução ou personalização), subgrupos
  relevantes e porções do plano informado. Se faltarem, peça apenas o necessário
  para executar o pedido. Não aplique a fase de redução para sempre nem elimine
  automaticamente todos os grupos. Uma classificação depende do alimento,
  preparo, produto e porção; não é um atributo universal do nome.
- **Lactose:** confirme se a orientação é evitar lactose ou limitar segundo uma
  tolerância informada. Não atribua um limite numérico padrão ao paciente.
  Intolerância à lactose e alergia à proteína do leite são condições distintas:
  “zero lactose” não comprova adequação para alergia. Um filtro de lactose não
  comprova baixo FODMAP em todos os outros subgrupos, nem ausência de leite.
- **Outras exclusões:** execute somente a restrição que ele informou. Não deduza
  ausência de glúten, leite, alérgenos ou ingredientes pela categoria do alimento.

Guarde a orientação confirmada e suas atualizações em `restricoes.md` na pasta
do paciente, fora do plugin. Sem paciente (consulta ao catálogo), mantenha somente
o contexto da sessão. Não grave dados de paciente no cadastro compartilhado.

## Conferir evidências e filtrar

1. Resolva nomes no catálogo existente, preservando marca, preparo e variante.
   O catálogo nutricional e o livro histórico de biodisponibilidade não são uma
   base de teores/classificações de FODMAPs ou lactose.
2. Consulte fonte atual adequada: Monash para classificação FODMAP por porção;
   rótulo/fabricante do produto exato para lactose e ingredientes; dados
   específicos apresentados pelo nutricionista. Abra e confira a fonte, registre
   referência, data de consulta, porção e passagem/dado que sustenta o resultado.
   Não classifique por memória, trecho de busca, carboidratos totais ou lista
   genérica sem porção. Guia geral de método não classifica um produto específico.
3. Se a porção estiver em base fechada à qual você não tem acesso, diga isso e
   peça ao profissional a informação autorizada do item/porção. Não simule acesso
   ao aplicativo nem copie sua base inteira para o GitHub.
4. Use `scripts/restricoes.py` para comparar registros conferidos. Ele confere
   correspondência, não valida a verdade clínica da fonte. “Compatível” significa
   apenas compatível com os critérios e a porção consultados; não garante
   tolerância individual ou adequação nutricional da dieta completa.

O cadastro de evidências do profissional fica ao lado do seu cadastro de alimentos,
em `Path(ambiente.arquivo_alimentos(perfil)).with_name("filtros-" +
Path(ambiente.arquivo_alimentos(perfil)).name)`. Essa pasta já é externa ao plugin.
Use `restricoes.carregar(caminho)`. Ausência de arquivo = base vazia; JSON inválido
é erro a corrigir, não uma lista de alimentos liberados. Preserve os registros
existentes ao acrescentar evidências verificadas; nenhuma gravação na planilha mestre.

Cada registro tem este formato (exemplo **sintético**, não classificação clínica):

```json
{
  "alimento": "Alimento exemplo — marca e preparo exatos",
  "criterio": "fodmap",
  "quantidade": 30,
  "unidade": "g",
  "resultado": "compativel",
  "fonte": {
    "referencia": "referência verificável do dado específico",
    "consultado_em": "2026-10-23",
    "trecho": "passagem/dado conferido para essa porção e esse critério"
  }
}
```

`criterio` identifica a orientação confirmada: `fodmap` para avaliação global,
`fodmap:frutanos` ou outro subgrupo explícito para avaliação daquele subgrupo,
`lactose` para a orientação de lactose **descrita na fonte e no contexto**.
Não reutilize `lactose` de pacientes com limites diferentes: o registro deve
fundamentar a decisão no critério atual; quando depender da tolerância individual,
use uma chave específica para essa orientação somente no contexto privado do
paciente, sem gravá-la no cadastro comum. `resultado` é `compativel` ou
`incompativel` para a porção exata, nunca “seguro para todos”.

Depois do preâmbulo padrão, importe `restricoes`. Com os critérios e registros
conferidos, chame `restricoes.filtrar(catalogo, quantidade, unidade, criterios,
registros)` para a busca; na dieta ditada, chame `restricoes.avaliar(nome,
quantidade, unidade, criterios, registros)` por item e por alternativa.
Quantidade e unidade são as informadas pelo profissional, sem conversão autônoma.

| Resultado | Mostrar e fazer |
|---|---|
| `compativel` | Listar alimento, porção, critério e fonte. O profissional escolhe. |
| `incompativel` | Tirar das opções filtradas, mas mostrar na lista de excluídos com o motivo; se já prescrito, sinalizar para decisão do profissional. |
| `verificar` | Separar como pendência: faltou evidência exata, fonte completa, unidade ou houve divergência. Nunca chamar de liberado. |

Os filtros combinados são uma interseção: todos os critérios devem estar
fundamentados para entrar nos compatíveis. O motor não extrapola nem para porções
maiores nem menores. Uma fonte para 30 g não prova classificação para 15 g ou 60 g.
Falta de cadastro não significa incompatibilidade, tampouco compatibilidade.

## Modelos, trocas e revisão

Confira também refeições modelo, todas as opções, cada membro dos itens com “ou”
e todas as alternativas de troca, inclusive as que não entram na conta da planilha.
Preserve o resolver de itens agrupados: não separe antes de `catalogo.resolver`.
O avaliador verifica todos os membros de um agrupado na mesma porção; trocas com
porções diferentes devem ser avaliadas separadamente nas respectivas quantidades.
Não estime efeito combinado de uma refeição somando cores ou teores desconhecidos.

Na revisão, mostre restrições em vigor, compatíveis, conflitos e pendências com
alimento/porção/fonte. Antes do documento, peça a decisão sobre cada conflito ou
pendência presente na dieta. A decisão fica registrada sem alterar a classificação
da fonte. Não tire/troque alimentos nem ajuste quantidades silenciosamente.

## Referências do método

- [Monash — classificação por porção](https://www.monashfodmap.com/blog/traffic-light-system/).
- [Monash — fases da dieta](https://www.monashfodmap.com/blog/3-phases-low-fodmap-diet/).
- [NIDDK — alimentação e intolerância à lactose](https://www.niddk.nih.gov/health-information/digestive-diseases/lactose-intolerance/eating-diet-nutrition).

Essas páginas orientam o método; não constituem uma tabela completa de alimentos.
