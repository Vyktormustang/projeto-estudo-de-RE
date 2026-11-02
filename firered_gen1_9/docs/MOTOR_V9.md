# Motor parcial `v9` — +51 golpes não-TM de subida de nível (+378 aprendizados → 15.005; 705/729 = 96,7% restaurados, preservando 229/229 TMs SV)

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
| **Motor parcial `v9`** | `scripts/motor_v9.py` | `32fd47c8...` | **`2936a08fc95f40c7788b6136f209ab5cab31aec062d615f2a458f45b123e0e6f`** |

Insumos versionados verificados por SHA-256 antes de aplicar `scripts/motor_v9.py`:

| Arquivo | Tamanho | SHA-256 |
|---|---:|---|
| `patches/motor_v9/payload.bin` | `12.692` B | `0cdc8e30ea289e49b5ea6f7c645078f8bec59f1ebc1f4d8eeeb1c4db93f67749` |
| `data/learnsets_motor_v9.csv` | `415.359` B | `de3f00717240a20c513899422789082d20e7e56f911671677c92abbf26ccfeae` |
| `data/learnsets_motor_v8.csv` | `404.233` B | `19abc5661267157524b9dcdc9ad769cdf12a20f9f44a3be63f134ae2ec9120f7` |

*(Observação: o SHA-256 de `payload.bin` acima reflete exatamente o binário compilado em `patches/motor_v9/payload.bin` e verificado em `scripts/motor_v9.py`.)*

---

## 2. O que foi implementado em `motor_v9` (fatos confirmados)

`motor_v9` preserva integralmente (byte a byte) todas as **229/229 TMs de Scarlet/Violet**, a loja ampliada, a matriz de compatibilidade `compatibilidade_tms_motor_v8.bin`, as 8 HMs infinitas, o `estojo_v2` paginado, o `treino_ev` e os eventos fixos, e ocupa `12` slots livres de `gBattleScriptsForMoveEffects` (`243..254`, mantendo `255` livre) para implementar **51 golpes não-TM** em seis famílias mecânicas compartilhadas:

### 2.1. Família A — Modificação de tipo, 3º tipo efêmero e eletrificação (`6` golpes, `+50` registros)

- `Soak` (`486`, eff `243`): converte o alvo para Água pura `(11, 11)`; falha atrás de `Substitute`, contra `Multitype`/Arceus (`#493`) ou se o alvo já for Água pura `(11, 11)`.
- `Magic Powder` (`675`, eff `243`): converte o alvo para Psíquico puro `(14, 14)` com as mesmas guardas.
- `Reflect Type` (`512`, eff `244`): copia `(type1, type2)` do alvo para o usuário (inclusive através de `Substitute`, exceto quando o alvo não tem tipo válido).
- `Trick-or-Treat` (`563`, eff `243`) e `Forest's Curse` (`567`, eff `243`): gravam um 3º tipo efêmero (`Ghost = 7` ou `Grass = 12`) vinculado à tag de identidade do Pokémon em campo (`PID ^ slot`), avaliado em `hook_typecalc_v9` (`0x06`, incluindo imunidades `0x`, super-eficácia/resistência líquida e STAB/imunidades de solo/status).
- `Electrify` (`578`, eff `244`): eletrifica o próximo golpe do alvo neste turno (`bstruct[0x13] = 0x40 | 13` em `hook_damage_v9` e `hook_typecalc_v9`); falha se o alvo já agiu no turno.

### 2.2. Família B — Trocas, divisões, inversões e impulsos compostos de stats (`21` golpes, `+101` registros)

- **Trocas e divisões diretas (eff `244`):**
  - `Power Trick` (`379`): permuta `Atk` ↔ `Def` brutos em `BattlePokemon` (`+0x02` ↔ `+0x04`).
  - `Speed Swap` (`638`): permuta `Speed` bruto entre usuário e alvo (`+0x06`).
  - `Power Swap` (`384`), `Guard Swap` (`385`) e `Heart Swap` (`391`): permutam entre usuário e alvo os estágios `Atk/SpA`, `Def/SpD` ou todos os `7` estágios (`1..7`).
  - `Guard Split` (`469`) e `Power Split` (`470`): igualam `Def/SpD` ou `Atk/SpA` de usuário e alvo à média inteira `(a + b) >> 1` (mínimo `1`).
  - `Topsy-Turvy` (`572`): inverte todos os estágios não neutros do alvo (`stage' = 12 - stage`); falha atrás de `Substitute` ou quando todos os estágios são `6`.
- **Fila sequencial animada de stats com efeitos acoplados (eff `245` c/ precisão, eff `246` s/ precisão):**
  - `Acupressure` (`367`, eff `246`): escolhe uniformemente um atributo `< +6` entre `Atk..Evasion` e eleva `+2`.
  - `Decorate` (`684`, eff `246`): eleva `Atk +2` e `SpA +2` do alvo (incluindo aliado em Duplas).
  - `Spicy Extract` (`750`, eff `246`): aplica `Atk +2` e `Def -2` no alvo (bloqueado por `Substitute`).
  - `No Retreat` (`673`, eff `246`): eleva `Atk/Def/Speed/SpA/SpD +1`, aplica `STATUS2_ESCAPE_PREVENTION` (`0x04000000`) + tag dedicada `no_retreat_tag` e falha em uso repetido enquanto a trava persistir.
  - `Clangorous Soul` (`682`, eff `246`, `acc=0, tgt=0x10`): consome `floor(maxHP / 3)` de HP e eleva `Atk/Def/Speed/SpA/SpD +1` (falha se `HP <= custo` ou todos os 5 atributos já estiverem em `+6`).
  - `Fillet Away` (`760`, eff `246`): consome `floor(maxHP / 2)` de HP e eleva `Atk/SpA/Speed +2` com a mesma guarda de HP/teto.
  - `Take Heart` (`743`, eff `246`, `10` PP): cura condições não voláteis de status do usuário (sincronizando `BattlePokemon`, `Pokemon` da equipe via `MON_DATA_STATUS = 0x37` e ícone de HUD via `0x98`) e eleva `SpA +1` e `SpD +1`.
  - `Venom Drench` (`595`, eff `245`, `tgt=0x08`): reduz `Atk/SpA/Speed -1` em oponentes envenenados (`Poison` ou `Bad Poison`); falha se nenhum alvo válido estiver envenenado.
  - `Toxic Thread` (`627`, eff `245`): reduz `Speed -1` e envenena o alvo (`0x08`).
  - `Tar Shot` (`674`, eff `245`): reduz `Speed -1` e marca `tar_shot_tag[tgt]`, dobrando (`2x`) o dano recebido de golpes de Fogo (`10`) em `hook_typecalc_v9`.
  - `Rototiller` (`559`, eff `246`, `tgt=0x10`): eleva `Atk/SpA +1` de todos os Pokémon de Planta (`12`) **aterrados** em campo.
  - `Flower Shield` (`575`, eff `246`, `tgt=0x10`): eleva `Def +1` de todos os Pokémon de Planta (`12`) em campo (aterrados ou não).
  - `Magnetic Flux` (`598`, eff `246`, `tgt=0x10`) e `Gear Up` (`629`, eff `246`, `tgt=0x10`): elevam `Def/SpD +1` ou `Atk/SpA +1` do usuário e do aliado (em Duplas) que possuam `Plus` (`57`) ou `Minus` (`58`).

### 2.3. Família C — Regeneração, drenagem por Atk, sacrifício/substituto e purificação (`11` golpes, `+60` registros)

- `Aqua Ring` (`392`, eff `244`): ativa véu de água no usuário, curando `max(1, maxHP / 16)` ao fim de cada turno (`hook_endturn_v9`, respeitando `Psychic Noise` / `Heal Block`).
- `Strength Sap` (`623`, eff `247`): calcula o `Atk` efetivo do alvo (com estágio atual), reduz `Atk -1` do alvo e cura o usuário por esse valor (respeitando `Heal Block`; contra `Liquid Ooze` `64`, causa esse mesmo valor em dano ao usuário).
- `Healing Wish` (`361`, eff `248`) e `Lunar Dance` (`460`, eff `248`): sacrificam o usuário (quando há reserva apta) e armam `wish_pending[side]` (`1` ou `2`). Em `hook_switchineffects_v9` (`0x52`), o próximo aliado que entrar ferido/com status/com PP gasto recebe restauração total de HP, limpeza de status (`BattlePokemon` + `MON_DATA_STATUS = 0x37` + `0x98`) e, no caso de `Lunar Dance`, restauração completa dos PPs dos 4 golpes considerando `ppBonuses` (`MON_DATA_PP1..4 = 0x11..0x14`).
- `Shed Tail` (`770`, eff `249`): exige reserva apta, ausência de `Substitute` ativo e `HP > ceil(maxHP / 2)`; consome `ceil(maxHP / 2)` de HP, executa troca automática de pivot (`51 01 02` + `4E 01 01` preservando bit de substituto) e instala no aliado entrante um `Substitute` de `max(1, maxHP_usuario / 4)` em `gDisableStructs[bank].substituteHP` (`0x02021648 + 28*bank + 0x0A`).
- `Psycho Shift` (`375`, eff `250`): transfere a condição não volátil do usuário ao alvo (respeitando imunidades elementais, habilidades Gen 3, `Safeguard` e `Misty Terrain`) e cura o próprio usuário.
- `Purify` (`640`, eff `250`): cura a condição não volátil do alvo e restaura `max(1, maxHP / 2)` do usuário; falha se o alvo não tiver condição de status.
- `Jungle Healing` (`710`, eff `250`) e `Lunar Blessing` (`742`, eff `250`): curam `max(1, maxHP / 4)` e removem condições não voláteis do usuário (e do parceiro vivo em Duplas).
- `Dark Void` (`463`, eff `251`, `50%` acc, `tgt=0x08`): adormece ambos os oponentes em Duplas (ou o oponente em Simples) e falha explicitamente com `"Mas {ATK} não consegue usar o golpe!"` quando a espécie do usuário não é **Darkrai (`#491`)** (regra oficial Gen 7+).

### 2.4. Família D — Manipulação de habilidade (`4` golpes, `+82` registros)

- `Gastro Acid` (`380`, eff `243`): seta `STATUS3_GASTRO_ACID` (`0x00010000`) e zera `BattlePokemon.ability` (`u16` em `+0x20`), suprimindo habilidades como `Levitate` (`26`); falha atrás de `Substitute` ou contra habilidades insuprimíveis (`Wonder Guard = 25`, `Forecast = 59`, `Multitype`/ausentes).
- `Worry Seed` (`388`, eff `243`): altera a habilidade do alvo para `Insomnia` (`15`) e acorda imediatamente alvos adormecidos (sincronizando equipe e HUD); falha contra `Truant` (`54`), `Insomnia` (`15`) ou `Substitute`.
- `Entrainment` (`493`, eff `243`): impõe a habilidade do usuário ao alvo (bloqueado por `Truant`, `Wonder Guard`, `Trace`, `Forecast` e `Substitute`).
- `Doodle` (`759`, eff `243`): copia a habilidade do alvo para o usuário **e** para o parceiro vivo em Duplas.

### 2.5. Família E — Cópia, ordem de turno, foco crítico, dano por HP e Natural Gift (`6` golpes, `+59` registros)

- `Copycat` (`383`, eff `252`, `tgt=0x10`): rastreia `last_used_move` em `hook_attackcanceler_v9` e executa o último golpe utilizado na batalha (excluindo golpes de cópia/proteção/troca forçada/auto-sacrifício incompatíveis).
- `After You` (`494`, eff `244`) e `Quash` (`510`, eff `243`): reordenam dinamicamente `gBattlerByTurnOrder` (`0x02021408`) e `gActionsByTurnOrder` (`0x02021404`) para as posições ainda pendentes (`> gCurrentTurnActionNumber`), movendo o alvo imediatamente para a próxima ação (`After You`) ou para o fim do turno (`Quash`); falham se o alvo já agiu neste turno.
- `Laser Focus` (`628`, eff `244`): garante golpe crítico no turno seguinte do usuário via `hook_critcalc_v9` (`0x04`), respeitando `Battle Armor` (`4`), `Shell Armor` (`75`) e `Lucky Chant` (`0x00008000` em `gStatuses3`).
- `Final Gambit` (`514`, eff `253`): verifica imunidade Fantasma e `Substitute` antes do sacrifício; se válido, sacrifica todo o HP atual do usuário e aplica exatamente esse valor de dano direto ao alvo.
- `Natural Gift` (`363`, eff `254`): consulta a tabela oficial Gen 6–9 para as Berries `133..175` (`Cheri`..`Enigma`, `80..100` BP e tipos elementais correspondentes), consome a Berry em `BattlePokemon.item` (`+0x30`), `Pokemon` (`MON_DATA_HELD_ITEM = 0x0C`) e via `EmitSetMonData(REQUEST_HELDITEM_BATTLE = 0x02)`, e falha sem consumir sob `Magic Room` ou sem Berry equipada.

### 2.6. Família F — Sala de itens e travas de troca (`3` golpes, `+26` registros)

- `Magic Room` (`477`, eff `244`, `tgt=0x10`, `5` turnos com toggle): intercepta `GetHoldEffect` (`0x080C725C`) **exclusivamente quando `gMain.inBattle` (`0x03004A45 & 0x02`) está ativo e `gBattleOutcome == 0`**, retornando `0` para suprimir todos os itens segurados em batalha sem afetar chamadas fora de batalha.
- `Octolock` (`678`, eff `243`): aplica `STATUS2_ESCAPE_PREVENTION` enquanto o usuário permanecer em campo e reduz `Def -1` e `SpD -1` do alvo ao fim de cada turno (`hook_endturn_v9`).
- `Fairy Lock` (`583`, eff `244`, `tgt=0x10`): bloqueia fugas e trocas de todos os Pokémon em campo durante o turno seguinte (`hook_turn_start_v9`).

---

## 3. Contabilidade completa dos 729 aprendizados por nível antes omitidos

Partindo dos `729` registros (`81` golpes) listados em `docs/golpes_pendentes_complemento.csv`:

| Etapa | Golpes restaurados na etapa | Registros restaurados | Total em `learnsets_motor_*.csv` | Acumulado restaurado |
|---|---:|---:|---:|---:|
| Base `motor_v5` | — | — | `14.300` | `0 / 729` (`0,0%`) |
| `motor_v6` | `1` (`Fling`) | `+23` | `14.323` | `23 / 729` (`3,2%`) |
| `motor_v7` | `5` (`Heal Pulse`, `Parting Shot`, `Geomancy`, `Floral Healing`, `Life Dew`) | `+59` | `14.382` | `82 / 729` (`11,2%`) |
| `motor_v8` | `18` (terrenos, salas, gravidade, hazards, `Snowscape`, `Tailwind`, `Shore Up`, `Tidy Up`, `Court Change`, `Defog`) | `+245` | `14.627` | `327 / 729` (`44,9%`) |
| **`motor_v9`** | **`51` golpes não-TM (Famílias A–F acima)** | **`+378`** | **`15.005`** | **`705 / 729` (`96,7%`)** |

Restam **exatamente `6` golpes (`24` registros = `3,3%`)** deliberadamente retidos por bloqueios estruturais da base Gen 3:

| ID interno | Nome | Registros | Motivo técnico objetivo da retenção |
|---:|---|---:|---|
| `492` | `Simple Beam` | `9` | Altera a habilidade do alvo para `Simple`, habilidade inexistente na tabela Gen 3 (`1..77`) desta ROM. |
| `501` | `Ally Switch` | `2` | Exige permuta física simultânea de sprites, OAMs, shadow data, `gBattlerPartyIndexes` e alvos pendentes entre bancos aliados `0 ↔ 2` / `1 ↔ 3` em Duplas. |
| `644` | `Instruct` | `1` | Exige reexecução aninhada completa da máquina de estados de ação de outro combatente dentro do mesmo passo de script. |
| `672` | `Stuff Cheeks` | `4` | Exige motor completo de ativação imediata arbitrária de todas as Berries de batalha além do escopo de `ItemBattleEffects` nativo. |
| `677` | `Teatime` | `4` | Exige consumo simultâneo multi-banco de qualquer Berry em até `4` combatentes com disparo encadeado de efeitos de Berry. |
| `755` | `Revival Blessing` | `4` | Exige modo de UI de equipe dedicado capaz de selecionar e reviver aliados desmaiados (`HP == 0`) em meio ao turno sem tratá-los como troca de entrada. |

---

## 4. Arquitetura técnica, endereços na ROM e EWRAM

| Região / Hook | Endereço (arquivo / CPU) | Função |
|---|---|---|
| `BATTLE_INIT_LIT` | `0x051D74` → `0x090C9001` | Zera `V9_STATE` (`0x0203FCA0..0x0203FD5F`) no início da batalha e encadeia para `hook_battle_init_v8` (`0x090C3001`). |
| `TURN_START_LIT` | `0x05439C` → `0x090C9009` | Atualiza `Laser Focus`, limpa `electrified_mask`, processa `Fairy Lock` e encadeia para `hook_turn_start_v8` (`0x090C3009`). |
| `ENDTURN_CONT_LIT` | `0x053208` → `0x090C9011` | Mantém fast-path exato para `0x08053221` quando nenhum efeito `v8`/`v9` está ativo; caso contrário, executa `v8` e em seguida `Aqua Ring`, `Octolock` e expiração de `Magic Room`. |
| `GET_HOLD_EFFECT_SITE` | `0x0C725C` → `0x090C9019` | Wrapper de `8` B em `GetHoldEffect`: retorna `0` apenas durante batalha ativa (`0x03004A45 & 2` e `gBattleOutcome == 0`) com `magic_room_turns > 0`; fora disso, lê `NEW_ITEMS_TABLE[44 * id + 0x12]`. |
| `BATTLE_STRINGS_TABLE_REFS` | `8` literais + teto `0x055C5A` (`f0 23` = `480`) | Realoca `gBattleStringsTable` (`408` → `445` ponteiros, `sid 12..456`) em `0x090C7000`, gravando `37` novas mensagens PT-BR em `0x090C7A00`. |
| `SCRIPTS_V9` | `0x10C6000..0x10C6FFF` (`0x090C6000`) | Sub-scripts fixos (`0x090C6000..0x090C631F`) e BattleScripts dos efeitos `243..254` (`0x090C6340..`). |
| `CMD_TABLE_V9` | `0x10C8800..0x10C8BFF` (`0x090C8800`) | Clona `CMD_TABLE_V8` e encadeia `0x00` (`attackcanceler`), `0x04` (`critcalc`), `0x05` (`damagecalc`), `0x06` (`typecalc`) e `0x52` (`switchineffects`). |
| `PAYLOAD_V9` | `0x10C9000..0x10CC193` (`0x090C9000`, `12.692` B) | Payload ARM7TDMI Thumb-1 puro (`28` vetores `0x090C9001..0x090C90D9`, verificado por Capstone e `_Static_assert`). |
| `V9_STATE` (EWRAM) | `0x0203FCA0..0x0203FD5F` (`<= 192` B) | Estado efêmero por batalha, contíguo após `V8_STATE` (`0x0203FC60..0x0203FC9F`), sem tocar `SaveBlock1`/`SaveBlock2`. |

---

## 5. Como reconstruir e executar as suítes de testes

### 5.1. Aplicar `motor_v9` em um arquivo novo (verificando SHA-256)

```bash
PYTHONPATH=firered_gen1_9 python3 -m scripts.motor_v9 \
  --rom /caminho/para/motor_v8.gba \
  --saida /caminho/para/motor_v9.gba
```

### 5.2. Testes estruturais e auditoria estrita de bytes (`test_motor_v9.py`)

```bash
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V9_BASE=/caminho/para/motor_v8.gba \
python3 -m unittest firered_gen1_9/tests/test_motor_v9.py -v
```

### 5.3. Testes de integração headless em mGBA `0.10.5` (`test_motor_v9_mgba.py` + `test_treino_ev_mgba.py`)

```bash
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V9_ROM=/caminho/para/motor_v9.gba \
MOTOR_V9_BASE=/caminho/para/motor_v8.gba \
TREINO_TEST_ROM=/caminho/para/motor_v9.gba \
MGBA_CORE=/caminho/para/mgba_libretro.so \
python3 -m unittest \
  firered_gen1_9/tests/test_motor_v9_mgba.py \
  firered_gen1_9/tests/test_treino_ev_mgba.py -v
```

Resultados verificados nesta entrega:
- `test_motor_v9.py`: **`7/7` OK** (hashes de insumos, ISA ARM7TDMI Thumb-1 pura com `28` vetores, `+378` aprendizados = `15.005` linhas preservando 100% de `v8` e fechando `705/729` + `6` retidos / `24` linhas, determinismo `2936a08f...`, auditoria byte a byte de regiões autorizadas e preservação integral de `estojo_v2`, `229` TMs SV, HMs, `treino_ev` e `payload_v6..v8`).
- `test_motor_v9_mgba.py`: **`6/6` OK** em mGBA `0.10.5` cobrindo todas as seis famílias (`Soak`, `Magic Powder`, `Reflect Type`, `Trick-or-Treat`, `Forest's Curse`, `Tar Shot`, `Electrify`; `Power Trick`, `Speed Swap`, `Power Swap`, `Topsy-Turvy`, `Guard Split`, `Toxic Thread`, `Venom Drench`, `No Retreat`, `Clangorous Soul`, `Fillet Away`, `Take Heart`, `Spicy Extract`, `Acupressure`, `Flower Shield`, `Rototiller`, `Gear Up`; `Aqua Ring`, `Strength Sap` + `Liquid Ooze`, `Psycho Shift`, `Purify`, `Jungle Healing`, `Dark Void` bloqueado fora de Darkrai `#491` e ativo em `#491`; `Lunar Dance` restaurando HP/status/PP com `PP Ups` e `Shed Tail` transferindo `Substitute` de `40` HP em troca real; `Gastro Acid`, `Worry Seed`, `Entrainment`, `Copycat`, `Laser Focus`, `Final Gambit` normal e vs Ghost, `Natural Gift` consumindo Berry, `Magic Room` suprimindo `Choice Band`, `Octolock`, `Fairy Lock`, e Duplas com `Decorate`, `Quash`, `After You` e `Doodle`; aprendizado real por nível em `Bulbasaur`, `Cresselia`, `Darkrai`, `Cyclizar` e `Veluza`, regressão `Snowscape` e persistência em save Flash/reload com `estojo_v2`).
- `test_treino_ev_mgba.py` (sobre `motor_v9.gba`): **`9/9` OK**.
- Suíte estrutural completa da cadeia (`v5` → `v6` → `v7` → `v8` → `v9` + subsistemas): **`90/90` executados OK**.
