# Investigação preliminar: golpes e listas da geração 9

> Registro da pesquisa **anterior** à autorização e à implementação. Para o estado atual, o que mudou, os testes e as limitações, consulte [Golpes por nível](GOLPES_POR_NIVEL.md). As recomendações de próximos passos abaixo são históricas.

A investigação abaixo **não modifica a ROM**. A ROM analisada é a variante de selvagens, treino e fixos comuns, SHA-256 `c563d43a8f15976314ad5fb271ad44a83cdf3143749389311f261ffd506a466b`.

## Observações verificadas

- A lista de nomes de golpes começa no offset `0x235930`, com 17 bytes por entrada. `FLARE BLITZ` está no índice interno 394; `AIR SLASH` no 403. Há nomes de alguns golpes criados na nona geração, incluindo `RAGING BULL` e `TIDY UP`; isso não demonstra que efeitos/animações desses golpes funcionem corretamente.
- Não foram encontrados `TERA BLAST`, `DRAGON CHEER` ou `TEMPER FLARE` nos nomes de golpes varridos. Isso é evidência de ausência na tabela analisada, não uma prova geral de que não haja algum mecanismo alternativo ou nome diferente.
- A tabela de ponteiros de movimentos por nível começa em `0x6BB728`; espécies usam IDs nacionais. A lista de Charizard (#6) começa em `0x6A92E8`. Ela corresponde à lista original de FireRed/LeafGreen, incluindo Flamethrower no 34, Wing Attack no 36, Slash no 44, Dragon Rage no 54 e Fire Spin no 64. Não inclui Flare Blitz ou Air Slash. O código em torno de `0x08109790` consulta esses ponteiros para o aprendizado por nível.
- Como comparação, os registros da PokéAPI para Scarlet/Violet (`version_group_id=25`) incluem **Flare Blitz no nível 62** para Charizard. Flare Blitz é da geração 4, não um golpe exclusivo da 9. Charizard também consta como compatível com `Dragon Cheer` (TM226), `Temper Flare` (TM207) e `Tera Blast` (TM171) em Scarlet/Violet; esses golpes são da geração 9.
- Comparação de conjuntos `(golpe, nível)` entre a ROM e os dados da PokéAPI para FireRed/LeafGreen (`version_group_id=7`): as listas por nível das **151 espécies da primeira geração** coincidem com FireRed/LeafGreen. Isso não compara TMs, HMs, tutores, ovos, formas ou o restante das espécies.
- A codificação e a rotina de aprendizado por nível que foram observadas usam apenas **9 bits para o ID do golpe**, enquanto a tabela de nomes contém índices acima de 511. Isso limita o trabalho de uma atualização: não basta gravar o ID de um golpe acima de 511 nesse formato. Seria necessário investigar/substituir o formato e os consumidores relevantes, incluindo golpes iniciais, subida de nível e o lembrete, e testar os efeitos em jogo. Não tratar os nomes presentes como garantia de implementação completa.
- Em mGBA 0.10.5 foi invocada diretamente a rotina real de aprendizado de nível (`0x08109790`), usando Pokémon e estado sintéticos, sem modificar a ROM nem usar save do usuário: Charizard no nível 62 não recebeu golpe; no 64 recebeu `FIRE SPIN` (ID 83). Tarountula no nível 5 recebeu `PAY DAY` (ID 6), embora a lista Scarlet/Violet indique `STRUGGLE BUG` nesse nível (nome que corresponde ao índice interno 518). Emboar no nível 31 recebeu `FLY` (ID 19), embora Scarlet/Violet indique `HEAT CRASH` (índice interno 531). O teste confirma divergências reais na rotina e é consistente com o truncamento de IDs; não é uma batalha ou subida de nível completa realizada normalmente.

## Limites e próximos passos se houver autorização

- Não foi auditado se Charizard pode aprender Flare Blitz por um tutor, evento ou outro método específico da ROM, nem a compatibilidade de todas as TMs/HMs. A verificação mGBA invocou a rotina diretamente em estado sintético; não cobriu o fluxo visual completo de batalha e subida de nível.
- Atualizar os aprendizados por nível requer uma política para diferenças entre jogos/atualizações da Gen 9, golpes exclusivos ausentes, formas regionais e espécies ausentes de Scarlet/Violet. TMs/HMs, tutores e ovos são sistemas separados.
- Antes de qualquer alteração, combinar o escopo com o usuário; manter uma cópia independente, salvar backups e não prometer compatibilidade com todos os saves, golpes ou mecânicas sem validação.

Fonte comparativa: [PokéAPI CSV no commit `6b8db7f3cb31cfaa37cb74e5c3edff124bcba5ce`](https://github.com/PokeAPI/pokeapi/tree/6b8db7f3cb31cfaa37cb74e5c3edff124bcba5ce/data/v2/csv), arquivos `pokemon_moves.csv`, `moves.csv`, `machines.csv` e `version_groups.csv`. Referência técnica do mecanismo Gen III: [pret/pokefirered](https://github.com/pret/pokefirered).
