# Ciclo 18 — Tabela de espécies, progressão de nível e cálculo de stats

**Estado:** rastreamento estático local de uma cadeia BoxMon → equipe, cálculo de stats e tabelas de espécie/experiência. Sem validação dinâmica.

## Pergunta e continuidade

Este ciclo continua o ciclo 17: em vez de repetir os accessors, segue um consumidor que os usa para converter um BoxMon em registro de equipe e recalcular os valores derivados. O recorte também procura uma primeira tabela local de dados de espécies.

## Identidade e ferramentas

- ROM somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`
- Tamanho: `16.777.216` bytes; SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- Mapeamento ROM: `VA GBA = offset + 0x08000000`.
- Decodificação: Capstone 5.0.7, Thumb, mais leituras/asserts Python nos bytes locais.
- Ghidra/REA não estavam disponíveis; não lhes atribuo os achados. Nenhuma execução em emulador nem inspeção/alteração do save.
- Cruzamento semântico separado: `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`; hashes dos arquivos usados ao fim do relatório.

## Cadeia local observada

```text
0x0803E774  conversão BoxMon → registro de equipe
  copia 0x50 bytes
  zera status, HP atual e HP máximo; define mail = 0xFF
       ↓
0x0803E47C  recálculo de stats
  lê espécie, IVs, EVs, HP anterior e nível derivado da experiência
       ├─ 0x08254784  registros de dados de espécies (stride local 0x1C)
       └─ 0x08253AE4  tabelas de experiência por growth rate (stride 0x194)
  grava nível, HP máximo, cinco stats e HP via SetMonData (0x0804037C)
```

Os nomes descritivos são cruzados com upstream; as operações, endereços, ponteiros e valores abaixo foram conferidos na ROM local.

### Conversão de BoxMon para equipe — `0x0803E774`

O código local preserva os argumentos, chama `0x081E5E78` com destino, origem e tamanho `0x50`, depois chama `SetMonData` (`0x0804037C`) com os campos `0x37`, `0x39`, `0x3A` e `0x40`. Os valores passados zeram status, HP atual e HP máximo e definem mail para `0xFF`. Por fim, chama `0x0803E47C` para recalcular os dados de equipe.

No cruzamento upstream, isso corresponde ao caminho `BoxMonToMon → CalculateMonStats`. É uma ligação estrutural entre o bloco persistente de BoxMon e a extensão de equipe identificada no ciclo 17; ainda não prova em qual fluxo de jogo cada chamador usa a conversão.

### Cálculo dos stats — `0x0803E47C`

A sequência local lê por `GetMonData`:

- HP máximo antigo e HP atual: campos `0x3A` e `0x39`;
- IVs e EVs para HP, ataque, defesa, velocidade e os dois stats especiais;
- espécie pelo campo `0x0B`;
- nível por chamada ao helper `0x0803E7C4`, usando a experiência e o growth rate da espécie.

A rotina calcula HP máximo e os cinco stats, chama `0x08042E9C` e `0x08043698` durante o cálculo dos stats não-HP, e grava os resultados pelo setter local. O upstream identifica essas chamadas, respectivamente, como obtenção da nature e ajuste de stat por nature; os símbolos não existem na ROM local.

O fluxo local implementa a estrutura das fórmulas de Gen III:

- HP: `floor(((2 × baseHP + HP_IV + floor(HP_EV/4)) × nível)/100) + nível + 10`;
- demais stats antes de nature: `floor(((2 × baseStat + IV + floor(EV/4)) × nível)/100) + 5`.

A rotina compara a espécie com o literal local `0x12F`; nesse ramo força HP máximo a 1. O cruzamento upstream associa esse ID a Shedinja. Para espécies normais, o HP atual é ajustado pela diferença entre HP máximo novo e antigo; um Pokémon recém-inicializado (HP e máximo antigos ambos zero) recebe o HP máximo novo, enquanto o ramo de HP zero com máximo antigo não-zero retorna preservando o estado desmaiado. Não foi feita validação dinâmica desses ramos.

### Nível a partir da experiência — `0x0803E7C4`

O helper local lê espécie pelo campo `0x0B`, experiência pelo campo `0x19` e usa a espécie como índice de uma estrutura de stride `0x1C`. Lê o byte em `+0x13`, multiplica-o por `0x194` e caminha pela curva correspondente na tabela de experiência. O loop começa no nível 1, compara o limiar com a experiência e termina no primeiro limiar superior ou no limite 100, retornando o nível encontrado.

Esse caminho mostra uma dependência adicional para qualquer espécie nova: além de stats válidos, o campo de growth rate tem que selecionar uma curva existente e coerente. Nos caminhos locais examinados, o ID de espécie é usado como índice sem clamp visível antes do acesso; limites/proteções em outros consumidores ainda precisam ser auditados.

## Tabelas locais e amostra

O literal em `0x0803E734` e o literal em `0x0803E82C` apontam ambos para `0x08254784` (offset de arquivo `0x254784`). Em `CalculateMonStats`, a aritmética local é `species × 7 × 4`, portanto stride de **28 bytes (`0x1C`)**. O helper de nível usa o mesmo endereço e lê `+0x13` do registro.

A tabela de experiência é apontada pelo literal em `0x0803E828` para `0x08253AE4` (offset `0x253AE4`). O código multiplica o growth rate por `0x194` (404 bytes, 101 palavras u32), compatível com uma curva por nível de 0 a 100.

Amostra local no registro de ID 1, em `0x082547A0` (offset `0x2547A0`):

```text
2D 31 31 2D 41 41 0C 03 2D 40 00 01 00 00 00 00
1F 14 46 03 01 07 41 00 00 03 00 00
```

Os seis primeiros bytes são `45, 49, 49, 45, 65, 65`; os bytes 6–7 são `12, 3`; o byte `+0x13` é `3`; os dois últimos bytes do registro amostrado são zero. O registro 0 imediatamente anterior é zero. No cruzamento upstream, ID 1 é Bulbasaur, os seis primeiros valores são seus base stats, `12/3` são Grass/Poison e o growth rate `3` é Medium Slow. A ROM local fornece os bytes; esses nomes e interpretações são rótulos de upstream.

Na tabela de experiência local, a curva de índice 0 começa `0, 1, 8, 27, 64, 125…`; a curva de índice 3 começa `0, 1, 9, 57, 96…`. Os valores foram lidos diretamente da ROM. O código local seleciona índice 3 para o byte de growth rate 3 da amostra acima.

**Nota de layout:** o cabeçalho upstream descreve campos de `SpeciesInfo` até `+0x19`, enquanto o código local indexa registros com stride `0x1C`; a amostra local tem dois bytes finais zero. Para qualquer expansão, o stride observado na ROM (`0x1C`) é o requisito seguro. A causa precisa desses bytes de alinhamento/padding e o limite final da tabela local ainda não foram determinados.

## Cruzamento semântico upstream — não é evidência local

No commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, os caminhos correspondentes são `BoxMonToMon`, `CalculateMonStats` e `GetLevelFromMonExp`; a tabela em `src/data/pokemon/species_info.h` é `gSpeciesInfo`, e `src/data/pokemon/experience_tables.h` define as curvas de XP. O header `include/pokemon.h` rotula os campos de `SpeciesInfo`; `include/constants/species.h` atribui nomes aos IDs como Bulbasaur e Shedinja.

SHA-256 dos arquivos cruzados:

- `src/pokemon.c`: `116a470cd9ebfa226aa8d85c2eb63591e176d726837c67baaa1ac6260d50f2ec`
- `include/pokemon.h`: `a6881fee07ae10f57ebf3ec7af1cabd2e900d8ba8d3da644313c087d16e1617e`
- `include/constants/species.h`: `ec3f9f9c2717dcd453aa7a27506c32e1e6ca067864534dee494695d74344c51a`
- `src/data/pokemon/species_info.h`: `9c2da1284f7859700b315abda0499334c422f2c6776d576c788fcd1e4050f71e`
- `src/data/pokemon/experience_tables.h`: `9a236761640676e251b76b7950b86e5881ee23dfe920ca27bbe47b4541542731`

A coincidência de funções, offsets e registros serve para dar semântica aos padrões locais; não demonstra que a ROM BR foi compilada dessa árvore upstream.

## Verificações reproduzíveis

- SHA-256 e tamanho da ROM conferidos antes da análise.
- Capstone nos intervalos `0x0803E47C`, `0x0803E774` e `0x0803E7C4`; leitura dos literais em `0x0803E734`, `0x0803E828` e `0x0803E82C`.
- Asserts sobre ROM local passaram para ponteiros das tabelas, stride `0x1C`, registro ID 1, growth rate, curvas 0 e 3 e sequência BoxMon→equipe→recalculo.
- Não há teste dinâmico nem validação de todas as linhas/limites da tabela.

## Lacunas e próximo passo

1. Determinar o limite real da tabela de espécies e as verificações de faixa em todos os callers; amostras de poucos registros não provam capacidade para IDs novos.
2. Localizar e rastrear tipos, habilidades, itens carregados, EV yield, learnsets e evoluções como campos/estruturas efetivamente consumidos na ROM local.
3. Localizar o catálogo de golpes e distinguir dados de golpe dos handlers de efeito de batalha.
4. Ainda não foi analisada a tabela de encontros selvagens por mapa; a amostra de `MapEvents` dos ciclos 12–16 não substitui esse subsistema.
5. Verificar em Ghidra e, depois, em emulador isolado, sem modificar a ROM/save original.

O ciclo 18 localiza e segue uma primeira fatia funcional dos dados de espécie, mas não fecha o catálogo nem autoriza adicionar espécies. Próximo recorte: determinar extensão/limites da tabela e seguir dois consumidores adicionais (tipos e habilidade/learnsets) antes de qualquer prova de expansão.
