# TMs modernas e ajustes de golpes — atualização parcial

Esta variante parte da ROM PT-BR de encontros, treino e golpes por nível. **Ela acrescenta TMs sem substituir as TMs e HMs antigas**, mas não transforma o jogo inteiro em Scarlet/Violet. A ROM de entrada não foi sobrescrita; ROMs e saves não fazem parte do Git.

- Entrada, SHA-256: `412bcd89214d4126d92f6c2256a56227c6f30fa138e0b262ef287f5b12b3997b`
- Nova ROM, SHA-256: `36cf2355789eca9273c2e4110606872fff8ab8ece82dae9ee090cd3bfa0546db`

## Como encontrar e usar as TMs novas

1. Em **Pallet**, examine a **placa ao lado da casa do protagonista**. O texto da placa continua aparecendo; depois, responda **SIM** à pergunta sobre a loja de TMs modernas.
2. A loja oferece **189 das 229 TMs de Scarlet/Violet**, por 3.000 cada. A descrição informa o nome do golpe antes da compra. A loja fica disponível desde cedo; isso pode facilitar o jogo, pois não exige insígnias.
3. Use o **estojo de TMs/HMs** nos itens-chave para ensinar o golpe a um Pokémon compatível. As TMs novas são **reutilizáveis**, ao contrário das TMs consumíveis em Scarlet/Violet e das TMs antigas desta ROM. As HMs antigas continuam reutilizáveis.
4. Os itens modernos se chamam `TM9-001` a `TM9-229`, e no estojo aparecem como `N001`, `N002` etc. **Essa numeração é diferente da antiga**: a TM9-001 ensina Take Down; a TM01 antiga continua Focus Punch. Os dois itens são diferentes.

O estojo continua com **58 espaços para tipos de item distintos**, compartilhados por todas as TMs antigas, HMs e TMs novas. Quantidades iguais empilham; as 189 TMs não cabem simultaneamente. Quando está cheio, a compra de um tipo adicional é recusada. Para liberar espaço, é possível usar uma TM antiga consumível ou vender uma TM que não queira em uma loja; TMs antigas vendidas podem não ser fáceis de recuperar. HMs não devem ser descartadas e continuam necessárias para a história.

Consulte [tms_gen9.csv](../data/tms_gen9.csv) para os números, nomes e status. `disponivel` significa que o item pode ser comprado e ensinado na ROM, **não que todos os seus efeitos imitem fielmente a Gen 9**. As 40 marcadas `nao_disponivel` não são vendidas: 25 não existem na ROM, 10 têm efeito placeholder e cinco usam poder dinâmico não implementado. As razões são critérios de filtragem, não uma auditoria completa dos outros golpes.

A compatibilidade das TMs novas é obtida da PokéAPI: Scarlet/Violet para as espécies presentes; Sword/Shield, BDSP ou USUM como fallback para as demais. Há 37.033 combinações espécie/TM registradas. Os critérios anteriores de compatibilidade das TMs/HMs antigas permanecem; HMs não foram renumeradas. Formas alternativas e todas as combinações não foram testadas individualmente.

## O que mudou nos golpes

- As listas por nível passaram de **14.018 para 14.184 entradas**: 166 aprendizados antes omitidos foram acrescentados sem retirar os anteriores. Permanecem **845 ocorrências omitidas**, relativas a 87 nomes, listadas em [golpes_ainda_nao_incluidos.csv](golpes_ainda_nao_incluidos.csv). Os Pokémon já salvos não têm seus golpes substituídos automaticamente.
- Foram implementados ou corrigidos efeitos de **Hone Claws, Work Up, Noble Roar, Tearful Look, Quiver Dance, Coil, Cotton Guard, Shift Gear, Air Slash, Inferno, Struggle Bug, Flare Blitz e Fire Fang**. Fire Fang pode queimar e causar flinch; Flare Blitz causa recuo e pode queimar.
- Foram adicionados efeitos ou comportamentos básicos também para **Acid Spray, Flame Charge, Charge Beam, Low Sweep, Snarl, Zen Headbutt, Waterfall, Poison Jab, Flash Cannon, Dark Pulse, Iron Head, Gunk Shot, Liquidation, Energy Ball, Play Rough, Earth Power, Focus Blast, Bug Buzz, Lunge, Scald, Electroweb, Sludge Wave, Skitter Smack, Breaking Swipe, Hurricane, Drain Punch, Shadow Claw, Drill Run, Stone Edge, Aura Sphere e Leaf Storm**. São adaptações ao motor antigo, não portações integrais.
- Os seguintes poderes foram ajustados globalmente, inclusive para golpes obtidos por nível ou TMs antigas: Thief **40→60**; Rock Tomb **50→60**, precisão **80→95**; Air Cutter **55→60**; Leech Life **20→80**; Giga Drain **60→75**; Surf, Flamethrower, Thunderbolt e Ice Beam **95→90**; Fire Blast, Hydro Pump, Blizzard e Thunder **120→110**. PP não foi atualizado, para não alterar diretamente os PP dos Pokémon existentes. Muitos outros poderes e precisões continuam legados.
- A comparação global de chance de efeito secundário foi corrigida de `sorteio ≤ chance` para `sorteio < chance`; isso pode reduzir em um ponto percentual a chance anteriormente observada também em golpes antigos. O caminho de efeito garantido foi preservado.

## Diferenças e limitações importantes

- **A atualização de batalha é parcial.** Muitas TMs disponíveis ainda ensinam golpes com mecânicas antigas ou incompletas. Por exemplo, **U-turn, Volt Switch e Flip Turn** ainda não fazem a troca esperada; **Ice Fang e Thunder Fang** ainda não têm todos os efeitos secundários; **Body Press, Foul Play, Psyshock, Acrobatics e Stored Power** não tiveram seus cálculos especiais portados. A filtragem do catálogo não detecta todas as diferenças. A IA, habilidades, alvos, animações, formas, categorias e outras regras também podem diferir de Scarlet/Violet.
- Por exemplo, **Trailblaze, Tera Blast, Gyro Ball e Heat Crash** estão entre as TMs não oferecidas. Além das 40 TMs, há aprendizados por nível omitidos no CSV; não há suporte integral à Gen 9.
- A alteração dos poderes e a loja disponível desde cedo mudam o equilíbrio da campanha. Não há progressão por insígnias para esses novos itens. Todos custam o mesmo valor e são reutilizáveis.
- O relembrador continua limitado a **24 golpes mais Cancelar**. Nem todos os golpes, interações em batalhas duplas, tutores, reprodução, trocas, itens no PC, emuladores ou eventos da campanha foram testados.

## Saves e preservação

1. **Faça uma cópia de segurança do `.sav` original e mantenha a ROM anterior.** Nunca use seu único save como teste.
2. Duplique o save feito pelo menu do jogo para o nome esperado pela ROM nova, geralmente `ptbr_gen1-9_selvagens_treino_tms_gen9.sav`, ou use a função de importação do emulador. O nome/pasta pode variar conforme o emulador.
3. Carregue a cópia, confira equipe, golpes, itens e progresso, e salve pelo menu. Se um objeto fixo antigo continuar visível, saia do mapa e entre novamente.
4. **Não reutilize save states/estados rápidos da ROM anterior.** Não volte para a ROM antiga com o único save que já contém TMs novas: ela não conhece esses IDs e pode perder ou tratar mal os itens. Guarde o backup anterior separado.

Um save **sintético**, criado na ROM anterior, foi carregado na nova; a equipe foi comparada e o save foi salvo e recarregado. Nenhum save pessoal foi utilizado. A compatibilidade de todos os saves e emuladores não é garantida.

As tabelas de encontros selvagens, os 1.982 objetos de mapa e o código de treino foram comparados com a entrada. Lendários e eventos especiais mantêm seus lugares; Phione e Moltres foram testados por amostragem. O treino continua em Equipe → Resumo → Atributos → SELECT, com redistribuição dos EVs já ganhos e IVs somente para consulta. As listas de golpes de Pokémon recém-criados, inclusive especiais, podem mudar, como na variante anterior.

## Reprodução e testes

A compilação confere SHA, catálogos, hooks, ponteiros e áreas livres, e só grava um arquivo novo:

```sh
python3 scripts/atualizacoes_gen9.py --rom minha_rom_anterior.gba --saida nova_copia.gba
```

Dados da [PokéAPI, commit `6b8db7f3cb31cfaa37cb74e5c3edff124bcba5ce`](https://github.com/PokeAPI/pokeapi/tree/6b8db7f3cb31cfaa37cb74e5c3edff124bcba5ce/data/v2/csv); licença BSD em [POKEAPI_LICENSE.txt](../data/POKEAPI_LICENSE.txt). `scripts/gerar_atualizacoes_gen9.py` regenera os catálogos a partir da ROM de entrada e dos CSVs desse commit. Código e payload Thumb estão em `patches/atualizacoes_gen9/`; os scripts de batalha, em `scripts/efeitos_gen9.py`.

No mGBA 0.10.5 foram testados, por amostragem: abertura da loja e descrição, compra da primeira e última TMs disponíveis, ensino, retenção e save/reload; TM antiga consumida, HM04 preservada, TM224, ovo, incompatibilidade e golpe já conhecido; estojo cheio; diversos efeitos em batalha, limites de atributos e chance zero, limites, Serene Grace e efeito garantido. Para alguns efeitos, chances foram forçadas apenas em **cópias temporárias**, não na ROM final. Os testes de eventos, relembrador, evolução, encontros, migração e treino foram repetidos.

A suíte completa executou **116 testes: 113 aprovados e 3 pulados** por falta da ROM privada de origem da primeira variante de encontros. São testes amostrais, não uma campanha completa. Para repeti-los com suas próprias ROMs e o core:

```sh
ATUALIZACOES_TEST_ROM=/caminho/nova.gba \
FIXOS_TEST_BASE=/caminho/treino.gba FIXOS_TEST_ROM=/caminho/nova.gba \
GOLPES_TEST_BASE=/caminho/sem_fixos.gba GOLPES_TEST_ROM=/caminho/nova.gba \
TREINO_TEST_ROM=/caminho/nova.gba MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s tests -v
```
