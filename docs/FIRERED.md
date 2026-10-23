# FireRed com os Pokémon novos (Gen 1–9) — build próprio

> **⚠️ DOCUMENTO HISTÓRICO (fork pokeemerald-expansion — rejeitado como base).**
> A entrega descrita aqui existe e funciona, mas **não é o alvo do projeto**.
> A base oficial agora é o FireRed de verdade (`pret/pokefirered`), com plano em
> [`docs/PLANO_FIRERED_GEN1-9.md`](PLANO_FIRERED_GEN1-9.md) e etapas no Linear (VYK-28…VYK-37).
> Mantido como registro: as provas de encontro selvagem continuam válidas como técnica.

**O que é:** um `.gba` que começa em **Pallet Town, Kanto**, com a tela de título
**“Pokémon FIRE RED Version”**, rodando na engine **pokeemerald-expansion 1.15**
— ou seja, com as espécies, movimentos, habilidades e mecânicas das **Gens 1 a 9**.

| item | valor |
|---|---|
| Arquivo | `pokefirered_expansion_gen1-9.gba` |
| Tamanho | 33 554 432 bytes (32 MB) |
| sha256 | `890c0d06c3cf9f3709c372f81a9d6499d3eee2d23eece08de529006556870744` |
| Cabeçalho interno | `POKEMON FIRE` / código `BPRE` / maker `01` |
| Link (Google Drive, público) | https://drive.google.com/file/d/1ddQIcLe6nZ03Eq4JOA3F24VybAz_dBpP/view?usp=drivesdk |
| Download direto | https://drive.google.com/uc?id=1ddQIcLe6nZ03Eq4JOA3F24VybAz_dBpP&export=download |

> Regra do projeto: o arquivo **não** vai para o Git (`*.gba` é ignorado). O link
> acima é a entrega. Trabalhe sempre sobre uma cópia.

---

## O que está CONFIRMADO (com evidência)

| # | afirmação | evidência |
|---|---|---|
| 1 | Compila do zero, sem erro | `make firered` terminou `EXIT=0`; ELF + `pokefirered.gba` gerados |
| 2 | É um ROM de FireRed no cabeçalho | bytes `0xA0`–`0xB0` = `POKEMON FIRE`, `BPRE`, `01` |
| 3 | A tela de título é a de FireRed | `reports/firered/01_titulo_firered.png` (frame 8400) |
| 4 | O jogo começa em Kanto | novo jogo leva ao quarto em Pallet Town: `reports/firered/03_quarto_pallet.png`; `src/new_game.c` faz `SetWarpDestination(MAP_PALLET_TOWN_PLAYERS_HOUSE_2F)` |
| 5 | Existem Pokémon das Gens 2–9 na tabela selvagem | lido **direto do ROM**: `sRoute1_FireRed_LandMons` = Pidgey, **Starly, Stufful, Pidove**, … ; `sRoute22_FireRed_LandMons` = Rattata, **Pancham, Tandemaus, Clobbopus**, … |
| 5b | **Encontro selvagem real com Pokémon novo, jogando** | andando na grama da **Rota 1**: *“You encountered a wild Starly!”* — `reports/firered/05_encontro_starly.png`; batalha iniciada em `06_batalha.png` |
| 5c | O seletor de espécies mostra as Gen 9 com sprite | debug *Give → Pokémon*: **Glimmora #1572** com sprite correto, e **Klefki #707**, **Rufflet #627** |
| 6 | As espécies novas estão habilitadas na engine | `include/config/species_enabled.h`: `P_GEN_7/8/9_POKEMON TRUE`; 1671 `SPECIES_*`, última `SPECIES_GLIMMORA_MEGA 1572` |
| 7 | O arquivo no Drive é idêntico ao construído | sha256 do Drive (`890c0d06…0744`) = sha256 local |

## O que é PROVÁVEL (não testei até o fim)

- **Capturar** o Pokémon novo (jogar a Poké Ball). O encontro acontece e a
  batalha roda; eu não tinha Poké Bolas na bolsa para fechar a captura. A
  mecânica de captura é a do expansion e não foi alterada, então deve funcionar.
- **As 1025 espécies aparecem no Pokédex.** O modo FireRed usa o Pokédex
  regional de Kanto (`REGIONAL_DEX_COUNT = KANTO_DEX_COUNT`, 151 entradas);
  espécies fora de Kanto dependem da parte nacional, que no expansion é
  dinâmica. Não verifiquei na tela.

## Problemas conhecidos do fork (não resolvidos)

- **A escada do quarto em Pallet Town é sólida.** O warp do andar de cima está
  em (10,2), mas o metatilo com `MB_DOWN_LEFT_STAIR_WARP` está em (9,3) e é
  bloqueante; os warps das portas do andar de baixo também não têm metatilo de
  porta. Ou seja: **dá para andar por Kanto, mas não dá para sair/entrar de
  casas normalmente** pela porta. É um desalinhamento de dados do fork, não do
  build. Contorno usado nos testes: **debug menu (R+START) → Utilities → Warp
  to map warp → grupo 037, mapa 019** (Rota 1) ou **000** (Pallet Town).
- **O jogo começa sem Pokémon** e o fluxo do laboratório do Oak não foi
  exercitado por mim. Para testar batalhas: debug → *Give → Pokémon (Basic)*
  (funciona; foi assim que entrou o Raticate da captura).


## O que é DESCONHECIDO

- Se **todo** o enredo de Kanto (ginásios, eventos, Sevii) está jogável de ponta
  a ponta. O fork traz 939 mapas, mas não há garantia de que todos os scripts
  foram portados para a engine do expansion. Trate como “base jogável”, não
  como remake completo.
- Compatibilidade com saves/trades oficiais: **nenhuma** (é outra engine).
- Se os sprites de todas as 1025 espécies estão presentes (a engine tem, mas o
  fork pode ter lacunas).

---

## Como foi construído (reproduzível)

Tudo em `scripts/firered/`:

```bash
# Linux/WSL/macOS
./scripts/firered/buildar_firered_expansion.sh ~/FireRedExpansion
```

```powershell
# Windows (PowerShell, com WSL instalado)
wsl bash ./scripts/firered/buildar_firered_expansion.sh ~/FireRedExpansion
```

O script: clona `CharonChaos88/FireRedExpansion` → `make tools` → aplica os dois
patches → mistura os encontros → `make MAP_VERSION=firered generated` →
`make firered -jN`.

### Os dois patches (e por quê)

1. **`patches/0001-hidden-itens-firered.patch`** — `asm/macros/map.inc`.
   No modo FireRed o fork zera as flags de item escondido de Hoenn
   (`include/constants/flags_frlg.h`, 1011 defines `= 0`). Os mapas de Hoenn
   continuam no ROM, então a montagem de `data/map_events.o` abortava com
   *“Hidden Item flag 0 is too small”*. O patch aceita flag 0 **só** quando
   `FIRERED` está definido; o comportamento no modo Emerald não muda.
2. **`patches/0002-map-version-firered.patch`** — `map_data_rules.mk`.
   A regra que gera `data/maps/*/header.inc|events.inc|connections.inc` estava
   fixa em `mapjson map emerald`, ignorando `MAP_VERSION`. Resultado: os `.inc`
   saíam em modo Emerald e o link quebrava com
   `undefined reference to gTileset_Building` / `gTileset_MysteryEventsHouse`
   (tilesets que só existem em Hoenn). Trocado por `$(MAP_VERSION)`.

### A mistura de encontros

`scripts/firered/misturar_encontros.py` (tem `--self-test`, 18/18):

- mantém o **slot 0** de cada tabela (a espécie mais comum da rota continua lá);
- troca slots a partir do 1 até somar **~40%** da probabilidade da tabela,
  usando os pesos de Gen 3;
- sorteia o substituto de forma **determinística** (sha256 de mapa+tabela+slot)
  entre espécies de **Gen 2–9 que sejam forma base** (exclui Mega/Alolan/etc.),
  **não míticas**, com **BST a ±120** do original e, de preferência, do **mesmo
  tipo primário**;
- preserva os níveis originais do slot.

Resultado: **2306 slots trocados em 374 mapas**, 629 tabelas tratadas;
espécies Gen 2+ distintas nos encontros: **110 → 374**.
Distribuição: Gen 2 = 423, Gen 3 = 549, Gen 4 = 204, Gen 5 = 410, Gen 6 = 131,
Gen 7 = 187, Gen 8 = 191, Gen 9 = 211.

Exemplos: Rota 1 → `PIDGEY, STARLY, STUFFUL, PIDOVE`;
Rota 22 → `RATTATA, PANCHAM, TANDEMAUS, CLOBBOPUS`.

---

## Como jogar no Windows

1. Baixe o `.gba` pelo link do Drive.
2. Instale o **mGBA** (https://mgba.io/downloads.html) — recomendado; VisualBoyAdvance-M e
   RetroArch também servem.
3. `File → Load ROM…` (ou arraste o arquivo) e jogue.
4. O jogo salva normalmente (`.sav` ao lado do ROM). Use `Save State` (`Shift+F1`)
   antes de testar coisas arriscadas.

Não precisa de patch, nem de BIOS, nem do FireRed original.

---

## Limitações e fase 2

- **Idioma: inglês.** O fork é baseado no expansion, que é em inglês. Traduzir
  PT-BR é um trabalho à parte (fase 2) — envolve reescrever os textos com o
  charmap do expansion e recolocar acentos.
- **Não é o FireRed original “de verdade”**: a engine é a do Emerald/expansion.
  Aparência de menus, sons e alguns sistemas são os de Emerald; o mapa, o
  enredo e a tela de título são de Kanto/FireRed.
- **Não usa o FireRed PT-BR** como base (decisão registrada: incompatível).
- Próximo passo natural: andar na Rota 1 e capturar um Pokémon de Gen 8/9 em
  jogo, com captura de tela, para promover o item “PROVÁVEL” a “CONFIRMADO”.
