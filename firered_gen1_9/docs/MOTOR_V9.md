# Motor parcial `v9` — +49 Golpes de Subida de Nível (+368 entradas → 14.995; 695/729 = 95,3% restauradas) preservando 229/229 TMs de Scarlet/Violet

> **Escopo e regras de segurança:** este documento aplica-se exclusivamente à trilha **FireRed PT-BR Gen 1–9 (32 MiB)** (`VYK-57`), sobre `motor_v8.gba`. Nunca misture endereços ou estados com a ROM histórica de 16 MiB (`BAG_MOD`). Nenhuma ROM comercial (`.gba`), save pessoal (`.sav`) ou save-state é versionado no Git; todos os testes de integração usam exclusivamente saves e estados sintéticos descartáveis em mGBA `0.10.5`.

---

## 1. Cadeia determinística de hashes SHA-256

| Etapa | Gerador (`firered_gen1_9/`) | Entrada (SHA-256) | Saída (SHA-256) |
|---|---|---|---|
| Base parcial 32 MiB | — | — | `6155b6a5fe62528b7b67836d3a47752b1cb3b1a71c1f2b59bfa7a68af0100d67` |
| Estojo expandido `v2` | `scripts/estojo_expandido.py` | `6155b6a5...` | `93dc62e86cfa3dc70c8057fa4ea25031761d48fc5ce4f7615a5a66d4fc280907` |
| Motor ampliado `v5` | `scripts/motor_ampliado.py` | `93dc62e8...` | `cf1de0e237feefcfda6789bc81c726ed13d91d512b85c54b9f857520a7a4fc87` |
| Motor parcial `v6` | `scripts/motor_v6.py` | `cf1de0e2...` | `75d66d3c36e560df29f6c613666b91a6c81ce24663b6a3f76f4dd2ea7d747ce6` |
| Motor parcial `v7` | `scripts/motor_v7.py` | `75d66d3c...` | `6321d8e2900cc44dcaefb2dedfbaf5b0952b2796ca27a4cb9d8dc0875827de09` |
| Motor parcial `v8` | `scripts/motor_v8.py` | `6321d8e2...` | `32fd47c87b581952f54f05656f590c5f7da55d5cc3d186d81951508899ec54f0` |
| **Motor parcial `v9`** | `scripts/motor_v9.py` | `32fd47c8...` | **`ad911117b4e1072f614ae51d1d6b1b99643562d2b9cdf7701fbcd04baab3a297`** |

Insumos versionados verificados por SHA-256 antes de aplicar `scripts/motor_v9.py`:

| Arquivo | Tamanho | SHA-256 |
|---|---:|---|
| `patches/motor_v9/payload.bin` | `12.296` B | `71283bda3341ad5b55e7cd0b9fecf40bf53e49a26737ed20d2a05484d9553f24` |
| `data/learnsets_motor_v9.csv` | `415.049` B | `a9fee458d097a83a6dde27af745bb3efc3bb603b84208b960c1c9dcb424ce4d8` |
| `data/learnsets_motor_v8.csv` | `404.233` B | `19abc5661267157524b9dcdc9ad769cdf12a20f9f44a3be63f134ae2ec9120f7` |

---

## 2. O que foi implementado em `motor_v9` (fatos confirmados)

Ocupando de forma estruturada os **13 slots livres remanescentes (`243..255`)** da tabela de scripts de batalha (`gBattleScriptsForMoveEffects` em `0x0900A000`), o `motor_v9` implementa **49 golpes** agrupados em 5 famílias mecânicas e restaura **+368 entradas de subida de nível** antes omitidas (`14.627` → **`14.995` linhas**, alcançando **`695 / 729` = `95,3%`** das entradas históricas de `docs/golpes_pendentes_complemento.csv`), preservando byte a byte as **229/229 TMs de Scarlet/Violet**, as 8 HMs infinitas, o estojo paginável `estojo_v2`, a loja, o treino EV/IV e as tabelas de encontros/eventos.

### 2.1. Família 1 — Alteração de tipos, 3º tipo efêmero e vulnerabilidade elemental (`6` golpes, `+48` entradas)

| Golpe interno (PokéAPI) | Nome | Slot de efeito | Mecânica implementada e validada em mGBA |
|---:|---|---:|---|
| `486` (`487`) | `Soak` | `244` | Converte o alvo para tipo Água puro (`type1=11, type2=11`, limpando 3º tipo); falha sob `Substitute` ou se o alvo já for Água puro. |
| `675` (`750`) | `Magic Powder` | `244` | Converte o alvo para tipo Psíquico puro (`type1=14, type2=14`, limpando 3º tipo); bloqueado por alvos de tipo Planta (`12`), `Substitute` ou já Psíquico puro. |
| `512` (`513`) | `Reflect Type` | `244` | Copia `type1`, `type2` e eventual `extra_type` do alvo para o usuário (ignora `Substitute`). |
| `563` (`567`) | `Trick-or-Treat` | `244` | Adiciona Fantasma (`extra_type = 7`) como 3º tipo do alvo, concedendo STAB `1,5x` e aplicando imunidades (`0x` Lutador/Normal) e fraquezas (`2x` Sombrio/Fantasma) em `hook_typecalc_v9`. |
| `567` (`571`) | `Forest's Curse` | `244` | Adiciona Planta (`extra_type = 12`) como 3º tipo do alvo (STAB, eficácia elemental e imunidade a `Magic Powder` / reconhecimento em `Rototiller` e `Flower Shield`). |
| `674` (`749`) | `Tar Shot` | `246` | Reduz `Speed -1` do alvo e marca `tar_shot_mask`, dobrando (`2x`) a eficácia de golpes de tipo Fogo (`10`) contra o alvo marcado. |

### 2.2. Família 2 — Manipulação de habilidades nativas Gen 3 e eletrificação (`5` golpes, `+70` entradas)

| Golpe interno (PokéAPI) | Nome | Slot de efeito | Mecânica implementada e validada em mGBA |
|---:|---|---:|---|
| `380` (`380`) | `Gastro Acid` | `244` | Suprime a habilidade ativa do alvo (`ability = 0`, ex.: anula `Levitate` permitindo `Earthquake`); falha sob `Substitute` ou se já suprimida. |
| `388` (`388`) | `Worry Seed` | `244` | Muda a habilidade do alvo para `Insomnia` (`15`) e, se o alvo estiver dormindo (`status1 & 0x07`), acorda-o imediatamente sincronizando `MON_DATA_STATUS` via `EmitSetMonData`. |
| `493` (`494`) | `Entrainment` | `244` | Transfere a habilidade do usuário para o alvo (respeitando habilidades protegidas Gen 3: `Wonder Guard` `25`, `Truant` `54`, `Forecast` `59` e `Trace` `36`). |
| `759` (`867`) | `Doodle` | `244` | Copia a habilidade do alvo para o usuário (e para o parceiro ativo em batalhas em dupla), respeitando a mesma lista de habilidades não copiáveis. |
| `578` (`582`) | `Electrify` | `244` | Se o alvo ainda não agiu no turno atual, marca `electrified_mask` convertendo o tipo dinâmico (`bstruct[0x13] = 0x40 | 13`) do golpe do alvo neste turno em Elétrico (`13`). |

### 2.3. Família 3 — Trocas, divisões, inversão, sinergias de campo/equipe e `Strength Sap` (`18` golpes, `+100` entradas)

| Golpes internos | Nomes | Slots | Mecânica implementada e validada em mGBA |
|---|---|---:|---|
| `379`, `638` | `Power Trick`, `Speed Swap` | `245` | Permutam respectivamente `Attack ↔ Defense` brutos do usuário (`+0x02`/`+0x04`) ou `Speed` bruta (`+0x06`) entre usuário e alvo. |
| `470`, `469` | `Power Split`, `Guard Split` | `245` | Igualam `Attack` e `Sp. Atk` (`Power Split`) ou `Defense` e `Sp. Def` (`Guard Split`) de usuário e alvo à média aritmética inteira `(a + t) >> 1`. |
| `384`, `385`, `391` | `Power Swap`, `Guard Swap`, `Heart Swap` | `245` | Permutam estágios de `Atk`/`Sp. Atk` (`Power Swap`), `Def`/`Sp. Def` (`Guard Swap`) ou todos os `7` estágios `Atk..Eva` (`Heart Swap`) entre usuário e alvo. |
| `572` | `Topsy-Turvy` | `245` | Inverte todos os estágios não neutros do alvo (`stage = 12 - stage`); falha sob `Substitute` ou quando todos os estágios são `6`. |
| `367`, `684`, `750` | `Acupressure`, `Decorate`, `Spicy Extract` | `246` | `Acupressure`: `+2` aleatório em atributo `< 12` do usuário; `Decorate`: `+2 Atk` e `+2 Sp. Atk` no alvo (ignora `Substitute`); `Spicy Extract`: `+2 Atk` e `-2 Def` no alvo. |
| `595`, `627` | `Venom Drench`, `Toxic Thread` | `246` | `Venom Drench`: `-1 Atk / -1 Sp. Atk / -1 Speed` em oponentes envenenados; `Toxic Thread`: `-1 Speed` + envenena o alvo (`0x08`, respeitando tipos/habilidades/`Misty Terrain`). |
| `559`, `575`, `598`, `629` | `Rototiller`, `Flower Shield`, `Magnetic Flux`, `Gear Up` | `247` (`tgt=0x10`) | `Rototiller`: `+1 Atk / +1 Sp. Atk` em Planta (`12`) aterrados; `Flower Shield`: `+1 Def` em todos os Planta (`12`) em campo; `Magnetic Flux` (`+1 Def/Sp. Def`) e `Gear Up` (`+1 Atk/Sp. Atk`) para aliados com `Plus` (`57`) ou `Minus` (`58`). |
| `623` | `Strength Sap` | `250` | Calcula o Ataque efetivo atual do alvo (com estágios), reduz `Attack -1` via `statbuffchange` (respeitando `Clear Body` / `Hyper Cutter` / `Mist`), bloqueia cura sob `Psychic Noise`, causa dano ao usuário contra `Liquid Ooze` (`64`) ou restaura HP igual ao Ataque efetivo pré-queda. |

### 2.4. Família 4 — Sacrifício de HP, clérigo, cura contínua, crítico garantido, pivot com `Substitute` e `Dark Void` (`15` golpes, `+85` entradas)

| Golpes internos | Nomes | Slots | Mecânica implementada e validada em mGBA |
|---|---|---:|---|
| `514` | `Final Gambit` | `243` | Verifica imunidades a Lutador (`Ghost`, `Wonder Guard`); se atingir, causa dano fixo exato igual ao HP atual do usuário (`0x69` `adjustnormaldamage2`, respeitando `Endure`) e sacrifica o usuário. |
| `760`, `682`, `673` | `Fillet Away`, `Clangorous Soul`, `No Retreat` | `248` | `Fillet Away`: consome `maxHP / 2` e eleva `Atk / Sp. Atk / Speed +2`; `Clangorous Soul` (`acc=0`): consome `maxHP / 3` e eleva `Atk..Speed +1`; `No Retreat`: eleva `Atk..Speed +1`, aplica `STATUS2_ESCAPE_PREVENTION` (`0x04000000`) e falha se reutilizado enquanto `no_retreat_mask` estiver ativo. |
| `392`, `628` | `Aqua Ring`, `Laser Focus` | `249` | `Aqua Ring`: cura `max(1, maxHP / 16)` por turno ao fim do turno (respeitando `Psychic Noise`); `Laser Focus`: garante acerto crítico (`CRIT_MULTIPLIER = 2`) até o fim do próximo turno do usuário (exceto contra `Battle Armor`/`Shell Armor`). |
| `375`, `640`, `743`, `710`, `742` | `Psycho Shift`, `Purify`, `Take Heart` (`pp=10`), `Jungle Healing`, `Lunar Blessing` | `251` | `Psycho Shift`: transfere `status1` do usuário para o alvo e limpa o usuário; `Purify`: cura `status1` do alvo e restaura `50%` do HP do usuário; `Take Heart`: cura `status1` do usuário e eleva `Sp. Atk / Sp. Def +1`; `Jungle Healing` e `Lunar Blessing`: curam `25%` do HP e limpam `status1` do usuário e do aliado em duplas. |
| `463` | `Dark Void` | `252` | Restrito a **Darkrai (`species == 491`)** (qualquer outra espécie como Smeargle falha com mensagem dedicada); precisão `50%` (escalada por `Compound Eyes`, estágios e `Gravity`) contra ambos os oponentes, respeitando `Insomnia`/`Vital Spirit`/`Safeguard`/`Electric Terrain`/`Misty Terrain`. |
| `361`, `460` | `Healing Wish`, `Lunar Dance` | `253` | Exigem aliado apto na equipe; sacrificam o usuário e gravam `healing_wish_pending[side]`. Na entrada (`hook_switchineffects_v9`), se o substituto já entra ferido/statusado/com PP gasto, curam **antes** dos hazards de entrada (evitando nocaute prematuro por `Stealth Rock`); se entra saudável e sofre dano/status dos hazards, curam logo após; se permanece ileso, mantêm o desejo armazenado (Gen 8/9). `Lunar Dance` restaura também todos os `4` slots de PP ao máximo. |
| `770` | `Shed Tail` | `254` | Exige aliado apto, ausência de `Substitute` prévio e `curHP > ceil(maxHP / 2)`; consome `ceil(maxHP / 2)` do usuário, cria `Substitute` de `max(1, maxHP / 4)` HP e executa troca imediata preservando `STATUS2_SUBSTITUTE`, `gDisableStructs[atk].substituteHP` e o boneco visual (`4E 01 01`) no Pokémon entrante. |

### 2.5. Família 5 — Cópia, controle de ordem de ação e prisão (`5` golpes, `+65` entradas)

| Golpe interno (PokéAPI) | Nome | Slot de efeito | Mecânica implementada e validada em mGBA |
|---:|---|---:|---|
| `383` (`383`) | `Copycat` (`tgt=0x10`) | `255` | Redireciona para o script do último golpe executado na batalha (`V9_STATE->last_used_move`, gravado em `hook_attackcanceler_v9`) com `HITMARKER_NO_PPDEDUCT`, recalculando alvo via `GetMoveTarget`; falha se nenhum golpe copiável ocorreu. |
| `494` (`495`) | `After You` | `255` | Reordena `gBattlerByTurnOrder` / `gActionsByTurnOrder` movendo a ação pendente do alvo para imediatamente após o usuário (`gCurrentTurnActionNumber + 1`). |
| `510` (`511`) | `Quash` (`acc=100`) | `255` | Reordena `gBattlerByTurnOrder` / `gActionsByTurnOrder` empurrando a ação pendente do alvo para o último lugar do turno atual (respeitando `Substitute`). |
| `678` (`753`) | `Octolock` | `246` | Prende alvo não-Fantasma (`STATUS2_ESCAPE_PREVENTION`) e reduz `Def -1` e `Sp. Def -1` a cada fim de turno enquanto ambos os Pokémon permanecerem em campo. |
| `583` (`587`) | `Fairy Lock` (`tgt=0x10`) | `247` | Bloqueia fuga/troca de todos os Pokémon não-Fantasma em campo até o fim do turno seguinte (`fairy_lock_turns: 2 → 1 → 0`). |

---

## 3. Arquitetura técnica, endereços na ROM e EWRAM

| Região / Hook | Endereço (arquivo / CPU) | Função |
|---|---|---|
| `BATTLE_INIT_LIT` | `0x051D74` → `0x090C9001` | Zera `V9_STATE` (`100` B em `0x0203FCA0..0x0203FD03`) no início de cada batalha e encadeia para `hook_battle_init_v8` (`0x090C3001`). |
| `TURN_START_LIT` | `0x05439C` → `0x090C9009` | Zera `electrified_mask` e `endturn_step`, sincroniza identidades por banco, decrementa `laser_focus_turns` e encadeia para `hook_turn_start_v8` (`0x090C3009`). |
| `ENDTURN_CONT_LIT` | `0x053208` → `0x090C9011` | Quando nenhum efeito `v9` de fim de turno está ativo, delega imediatamente a `hook_endturn_v8` (`0x090C3019`, preservando macros frame-exatas); caso contrário executa `DoFieldEndTurnEffects`, processa `Aqua Ring` (`1/16`), `Octolock` (`-1 Def / -1 Sp. Def`) e decaimento de `Fairy Lock`, e delega a `hook_endturn_v8`. |
| `BATTLE_STRINGS_TABLE_REFS` | `8` literais + teto `0x055C5A` (`eb 23`) | Realoca `gBattleStringsTable` (`408` → `442` ponteiros, `sid 0x000C..0x01C5`) para `0x090C7000`, adicionando `34` strings PT-BR em `0x090C7800`. |
| `SCRIPTS_V9` | `0x10C6000..0x10C6FFF` (`0x090C6000`) | Sub-scripts fixos (`Aqua Ring`, `Octolock`, fila reutilizável `SUB_STAT_QUEUE`, `Healing Wish` / `Lunar Dance`, `Worry Seed`, `Liquid Ooze`, `Sleep` com `return`, `34` caudas de mensagem) e BattleScripts dos slots `243..255`. |
| `CMD_TABLE_V9` | `0x10C8800..0x10C8BFF` (`0x090C8800`) | Tabela realocada `gBattleScriptingCommandsTable`: encadeia `0x00` (`attackcanceler`), `0x04` (`critcalc`), `0x06` (`typecalc`) e `0x52` (`switchineffects`) sobre `CMD_TABLE_V8`, mantendo intactos todos os demais `252` opcodes. |
| `PAYLOAD_V9` | `0x10C9000..0x10CC007` (`0x090C9000`, `12.296` B) | Payload ARM7TDMI Thumb-1 puro (`32` vetores fixos `0x090C9001..0x090C90F9` + lógica C sem `libgcc`). |
| `V9_STATE` (EWRAM) | `0x0203FCA0..0x0203FD03` (`100` B) | Estado transitório por batalha, contíguo após `V8_STATE` (`0x0203FC60..0x0203FC9F`) e estritamente abaixo de `0x0203FD50`, fora de `SaveBlock1`/`SaveBlock2` (zero impacto em saves `.sav`). |
| `level.TABLE` | `0x08F50000..0x08F5FFFF` | Tabelas de subida de nível recompiladas com `14.995` registros (`+368` sobre `motor_v8`, preservando `100%` dos anteriores). |

---

## 4. Os 8 golpes finais mantidos fora de escopo (`34 / 729 = 4,7%`) e limitações conhecidas

Seguindo a diretriz estrita do projeto de **separar fatos confirmados de hipóteses e nunca expor golpes sem mecânica fiel nos aprendizados por nível**, exatamente **8 golpes (`34` entradas de `729`, ou `4,7%`)** permanecem deliberadamente fora de `learnsets_motor_v9.csv`:

| Golpe interno | PokéAPI ID | Nome | Entradas retidas | Justificativa técnica verificada |
|---:|---:|---|---:|---|
| `363` | `363` | `Natural Gift` | `3` | Removido em Scarlet/Violet e dependente de tabela completa de tipo/poder por Berry ausente na base. |
| `477` | `478` | `Magic Room` | `7` | Supressão transversal de todos os held items exige hooks invasivos fora da tabela de comandos de script (cálculo de atributos, cura de fim de turno, Berries e itens de escolha). |
| `492` | `493` | `Simple Beam` | `4` | A habilidade `Simple` não existe na tabela nativa de habilidades Gen 3 (`0..77`). |
| `501` | `502` | `Ally Switch` | `2` | Permutação física de bancos ativos, OAM/sprites de parceiros e redirecionamento de alvos no meio do turno em duplas Gen 3. |
| `644` | `689` | `Instruct` | `1` | Reexecução aninhada de ação completa de outro battler dentro de `RunBattleActionsFunctions`. |
| `672` | `747` | `Stuff Cheeks` | `4` | Consumo ativo de Berry equipada com disparo da rotina interna `ItemBattleEffects` fora de janela de gatilho. |
| `677` | `752` | `Teatime` | `2` | Consumo simultâneo de Berries em todos os bancos ativos (inclusive através de `Substitute`) com disparo individual de efeitos. |
| `755` | `863` | `Revival Blessing` | `11` | Seleção interativa de Pokémon desmaiado (`HP == 0`) exige patch dedicado na máquina de estados de UI `party_menu` (que bloqueia confirmação em aliados nocauteados). |

Outras limitações documentadas herdadas da base GBA Gen 3:
- Itens e habilidades modernos pós-Gen 3 (`Heavy-Duty Boots`, `Terrain Extender`, `Light Clay`, `Surge` abilities, `Simple`, `Contrary`, `Good as Gold`, `Mycelium Might` etc.) permanecem ausentes na engine base.
- `Acupressure` (`367`) utiliza `tgt = 0x10` (usuário), pois o byte `MOVE_TARGET_USER_OR_SELECTED` de Emerald não existe no seletor de alvos nativo de FireRed.
- Em duplas, `Expanding Force` mantém cursor de alvo único estático da `MOVE_TABLE`.

---

## 5. Como reconstruir e executar as suítes de testes

### 5.1. Regerar `learnsets_motor_v9.csv` (opcional, a partir do commit fixado do PokéAPI) e aplicar `motor_v9`

```bash
PYTHONPATH=firered_gen1_9 python3 -m scripts.gerar_motor_v9 \
  --pokeapi-csv /caminho/para/pokeapi/data/v2/csv

PYTHONPATH=firered_gen1_9 python3 -m scripts.motor_v9 \
  --rom /caminho/para/motor_v8.gba \
  --saida /caminho/para/motor_v9.gba
```

### 5.2. Testes estruturais e invariantes da cadeia (`v5` → `v6` → `v7` → `v8` → `v9`)

```bash
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V6_BASE=/caminho/para/motor_v5.gba \
MOTOR_V7_BASE=/caminho/para/motor_v6.gba \
MOTOR_V8_BASE=/caminho/para/motor_v7.gba \
MOTOR_V9_BASE=/caminho/para/motor_v8.gba \
python3 -m unittest \
  firered_gen1_9/tests/test_motor_v6.py \
  firered_gen1_9/tests/test_motor_v7.py \
  firered_gen1_9/tests/test_motor_v8.py \
  firered_gen1_9/tests/test_motor_v9.py -v
```

### 5.3. Testes de integração headless em mGBA `0.10.5` (apenas saves/estados sintéticos)

```bash
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V9_ROM=/caminho/para/motor_v9.gba \
MOTOR_V9_BASE=/caminho/para/motor_v8.gba \
TREINO_TEST_ROM=/caminho/para/motor_v9.gba \
MGBA_CORE=/caminho/para/mgba_libretro.so \
python3 -m unittest \
  test_motor_v9 \
  test_motor_v9_mgba \
  test_treino_ev_mgba -v
```

Resultados verificados nesta entrega:
- `test_motor_v9.py`: **`6/6` OK** (partição exata `49` habilitados / `+368` entradas → `14.995` linhas e `8` retidos / `34` entradas = `695 + 34 = 729`, payload ARM7TDMI Thumb-1 puro com `32` vetores, determinismo `ad911117...`, slots `243..255`, strings `0x01A4..0x01C5`, `CMD_TABLE_V9` e preservação byte a byte das `229/229` TMs SV, loja, `estojo_v2`, `treino_ev` e payloads `v6`–`v8`).
- `test_motor_v9_mgba.py`: **`7/7` OK** em mGBA `0.10.5` (`Soak`, `Magic Powder`, `Trick-or-Treat` `2x` Dark / `0x` Fighting, `Reflect Type`, `Tar Shot` `2x` Fire; `Gastro Acid` + `Earthquake`, `Worry Seed` acordando alvo adormecido, `Entrainment` + bloqueio em `Truant`, `Doodle`, `Electrify` anulando golpe em Terra; `Power Trick`, `Speed Swap`, `Power Split`, `Topsy-Turvy`, `Spicy Extract`, `Decorate`, `Venom Drench`, `Acupressure`, `Rototiller`, `Magnetic Flux`, `Toxic Thread`, `Strength Sap` + `Liquid Ooze`; `Fillet Away`, `Clangorous Soul`, `Take Heart`, `No Retreat`, `Aqua Ring`, `Laser Focus` crítico garantido, `Psycho Shift`, `Purify`, `Final Gambit` + imunidade em Ghost, `Dark Void` exclusivo de Darkrai `#491`; `Shed Tail` transferindo `Substitute` real e `Lunar Dance` salvando aliado ferido sob `Stealth Rock`; `Copycat`, `Octolock`, `Fairy Lock` e duplas com `After You`, `Quash` e `Jungle Healing`; subida de nível + Move Relearner + ensino real nas 3 páginas do `estojo_v2` com save/reload sintético + regressão cruzada `Psychic Noise` × `Aqua Ring` × `Grassy Terrain`).
- `test_treino_ev_mgba.py` (sobre `motor_v9.gba`): **`9/9` OK**.
- Suíte estrutural completa do pacote (`test_*.py` sem mGBA): **`99/99` executados OK** (`0` falhas, `0` erros).
