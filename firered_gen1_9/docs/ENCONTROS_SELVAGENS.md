# FireRed PT-BR Gen 1–9: encontros selvagens

Esta é uma edição **separada** da ROM PT-BR Gen 1–9 existente. A mudança foi feita nas tabelas de espécies selvagens; a ROM original, o código, os níveis, as taxas, os objetos e os scripts de eventos não foram regravados. Os slots de lendários/míticos que já existiam também permanecem iguais. Isso preserva os dados da ficha de personagem e dos eventos estáticos, mas **não equivale a testar cada função em jogo**.

## Como jogar com segurança

1. Abra `ptbr_gen1-9_selvagens.gba` em um emulador de GBA. Mantenha `pokefirered_gen1-9_ptbr.gba` original como backup.
2. Faça backup do seu save `.sav`. Se quiser experimentar a partida anterior, faça **uma cópia** do save com o mesmo nome da nova ROM, por exemplo `ptbr_gen1-9_selvagens.sav`, conforme as regras do seu emulador. Seu save específico não foi testado; não substitua a única cópia.
3. Consulte [guia_encontros.csv](guia_encontros.csv) para buscar por nome ou número da Pokédex. O arquivo abre em planilhas; os nomes das espécies usam identificadores em inglês e os mapas usam os nomes internos do FireRed. O guia informa **uma** localização de tabela por espécie, não todas as localizações existentes.

### Como ler o guia

- `metodo`: grama/caverna ou **surf**. Surf exige a habilidade e o progresso normais do jogo; algumas áreas também dependem de ilhas, itens, insígnias ou eventos.
- `nivel_min` e `nivel_max`: menor e maior nível dos slots daquela espécie na tabela; valores intermediários não são garantidos.
- `chance_por_encontro_pct`: soma dos pesos dos slots **depois que um encontro daquele método acontece**, usando as probabilidades de referência do FireRed. Não é chance por passo nem garantia de frequência: a expansão pode alterar a lógica, e repelentes ou outras condições podem interferir. A referência usa 20/20/10/10/10/10/5/5/4/4/1/1 para terra e 60/30/5/4/1 para surf. Há **79 entradas do guia com 1%**; elas podem demorar muito para aparecer.
- `situacao`: `adicionado` significa que o patch acrescentou uma ocorrência em tabela elegível; `ja existente` significa que já havia uma. A edição também conserva pesca e Rock Smash, mas o guia não depende deles como única opção.
- Os mapas do guia têm tiles de encontro conforme a auditoria de layouts; **não foi demonstrado que todo tile está acessível** em todas as etapas da história ou que cada espécie funciona sem problemas. Se uma localização parecer bloqueada, confira o progresso e informe espécie e mapa.

## Escopo e política para Pokémon especiais

- A base identificada tem **1.025 nomes** correspondentes às espécies nacionais 1–1025. Pela classificação de lendário/mítico do catálogo PokéAPI utilizado, 94 são protegidas e **931 são não lendárias/míticas**.
- Na verificação das tabelas finais, 930 dessas 931 têm pelo menos um slot de grama/caverna ou surf em um mapa elegível; **Unown** permanece nas câmaras Tanoby originais. Essas são **contagens estruturais**, não capturas verificadas individualmente.
- Foram acrescentadas **730 espécies** que não tinham uma ocorrência elegível nesses métodos; 619 alterações são em terra e 111 em surf. Antes havia 201 espécies não protegidas cobertas pelo mesmo critério. Para manter variedade, a edição preserva espécies já presentes em cada método elegível e representantes comuns das tabelas locais.
- Os 94 lendários/míticos não são acrescentados, e seus slots originais não são modificados. Por exemplo, os slots originais de Cresselia, Type: Null e Terapagos não foram editados. Isso não garante, por si só, que todos eles já fossem capturáveis na base.
- **Ultra Beasts e Pokémon Paradoxo** não estão marcados como lendários ou míticos nas flags da PokéAPI e, por isso, foram incluídos entre os 931, inclusive Walking Wake, Iron Leaves, Gouging Fire, Raging Bolt, Iron Boulder e Iron Crown. Se você considerar esses grupos como lendários para o seu projeto, será necessário gerar uma variante com essas espécies protegidas.
- Unown não é adicionado fora das ruínas: no FireRed de referência, a criação da forma usa código específico das câmaras e pode causar travamento fora delas. Ele depende da liberação e das regras originais de Tanoby.
- S.S. Anne, Altering Cave, Safari, Lost Cave, câmaras Tanoby e Route 21 South não são usadas para colocar novas espécies. Route 21 South tem tabela terrestre, mas a auditoria não encontrou tile terrestre de encontro. Pesca, Rock Smash e áreas excluídas não foram alterados.
- As formas regionais, alternativas ou cosméticas não são contadas separadamente; ter um nome na tabela também não prova que todos os sprites, golpes, habilidades, evoluções ou dados da espécie estejam corretos.

## Testes realizados e limites

- **Estrutural:** leitura de 132 cabeçalhos e 227 tabelas, comparação byte a byte e cobertura das espécies. Dos 16.777.216 bytes da ROM, 1.305 diferem da base; todos estão dentro dos campos de ID de espécie de 730 slots elegíveis. Níveis, taxas, ponteiros, código, mapas, scripts, ficha e objetos ficam fora desses campos.
- **Automatizado:** 22 testes passaram com a ROM base local, incluindo 19 testes com dados sintéticos e 3 de integração local. Cobrem limites de ponteiros, aliases/sobreposições, preservação, cobertura, SHA, saída determinística e proteção contra sobrescrever a entrada por caminho, symlink ou hard link. Sem a ROM privada, os 3 testes de integração são pulados.
- **Emulador mGBA 0.10.5:** boot, título, introdução PT-BR, novo jogo, quarto, Pallet, entrega da encomenda de Oak e obtenção das Poké Balls. Em partidas derivadas do mesmo ponto, Pancham (#674, adicionado) e Lechonk (#915, já existente) foram capturados na Rota 1 com as Poké Balls recebidas no jogo. Wattrel (#940, geração 9, adicionado, peso de 1%) foi encontrado e capturado na Rota 22; a Pokédex e a ficha de personagem exibiram seus dados. A partida de teste foi salva, reiniciada e carregada novamente, mantendo Wattrel na ficha.
- **Surf:** Quagsire (#195, adicionado) apareceu e foi capturado na Rota 21 North. Para alcançar a água sem jogar até a quinta insígnia, a insígnia e o golpe Surf foram inseridos **somente no estado temporário do emulador**; a captura usou Poké Balls obtidas no jogo. O estado de teste não foi entregue nem aplicado à ROM ou ao save do usuário.
- **Evento estático:** um Tarountula existente na Rota 1 foi acionado e iniciou sua batalha de nível 25. Isso é uma amostra, não um teste de todos os eventos.
- **Ainda não testado:** encontros das demais espécies um a um, acessibilidade de cada rota e ilha, todas as evoluções/formas, os outros eventos estáticos e compatibilidade com o save do usuário. Não há garantia de completude funcional dos 931.

## Reproduzir a edição

Requer Python 3 e a cópia exata da ROM base, obtida separadamente. Não é necessário instalar bibliotecas Python de terceiros:

```bash
python3 scripts/encontros_selvagens.py --self-test
python3 scripts/encontros_selvagens.py \
  --rom google_drive/pokefirered_gen1-9_ptbr.gba \
  --saida rom_mod/ptbr_gen1-9_selvagens.gba \
  --guia docs/guia_encontros.csv
```

O comando recusa versões da ROM diferentes, arquivos de saída existentes e qualquer tentativa de sobrescrever a entrada. `--force` permite substituir **saídas**, mas não a ROM de entrada. A distribuição é determinística. ROMs e saves são ignorados pelo Git; não coloque arquivos privados no repositório.

| Arquivo | SHA-256 |
|---|---|
| Base `pokefirered_gen1-9_ptbr.gba` | `ecd157aa7eb642ee81ffbe7397d222981866c407d02643b6a83dd47bbbf8c27d` |
| Edição `ptbr_gen1-9_selvagens.gba` | `3f8cc9e3a52b1bad8a2f22df9a302f79a355e929669c5425ef023017bd4c4e49` |
| `guia_encontros.csv` | `f2b50ff7255c21c0e0c67cbca0978215f631e95deeff791a6eb718ab44ae9484` |

### Referências técnicas

- [pret/pokefirered](https://github.com/pret/pokefirered/tree/ce6406d8c2eaf46d543c8a2606de0c3cb1951982): estruturas e pesos de encontros, mapas e layouts; os offsets desta ROM foram identificados e validados separadamente.
- [Universal Pokémon Randomizer ZX](https://github.com/Ajarmar/universal-pokemon-randomizer-zx/tree/7f00eb866ed35c8fe3963f078b6a2e0979dc2b8c): tratamento de encontros de Gen III e ressalva sobre Unown em FireRed/LeafGreen.
- [PokéAPI, dados CSV](https://github.com/PokeAPI/pokeapi/tree/6b8db7f3cb31cfaa37cb74e5c3edff124bcba5ce/data/v2/csv): nomes, tipos, estatísticas, evolução e flags. Os derivados usados estão em `data/species_gen1_9.csv`; mapas em `data/firered_wild_maps.csv`.
- [mGBA 0.10.5](https://github.com/mgba-emu/mgba/tree/26b7884bc25a5933960f3cdcd98bac1ae14d42e2): core libretro compilado localmente para o teste de emulação.
