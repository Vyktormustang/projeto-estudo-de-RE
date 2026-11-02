# Motor parcial `v10` — Motor de Berries (+3 aprendizados → 15.008; 708/729 = 97,1%) e consolidação mecânica de 200 golpes Gen 1–9 / TMs SV

> **Escopo e regras de segurança:** este documento aplica-se exclusivamente à trilha **FireRed PT-BR Gen 1–9 (32 MiB)** (`VYK-57`), sobre `motor_v9.gba`. Nunca misture endereços ou estados com a ROM histórica de 16 MiB (`BAG_MOD`). Nenhuma ROM comercial (`.gba`), save pessoal (`.sav`) ou save-state é versionado no Git; todos os testes de integração usam exclusivamente saves e estados sintéticos descartáveis em mGBA `0.10.5`.

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
| Motor parcial `v9` | `scripts/motor_v9.py` | `32fd47c8...` | `2936a08fc95f40c7788b6136f209ab5cab31aec062d615f2a458f45b123e0e6f` |
| **Motor parcial `v10`** | `scripts/motor_v10.py` | `2936a08f...` | **`a533d1812812e2348bbe62a95a8c3817dd9d8372a89ff283f0e747c6c7ddeb09`** |

Insumos versionados verificados por SHA-256 antes de aplicar `scripts/motor_v10.py`:

| Arquivo | Tamanho | SHA-256 |
|---|---:|---|
| `patches/motor_v10/payload.bin` | `15.276` B | `4fdfbe8c0502fb875f5ed3cb50d1480a239587fbbc48dff0e8d595d5d060dce2` |
| `data/learnsets_motor_v10.csv` | `415.448` B | `53b4785cc81963624885be62a3d8d85896786edd98b890021b1feba9dec8caa1` |
| `data/learnsets_motor_v9.csv` | `415.359` B | `de3f00717240a20c513899422789082d20e7e56f911671677c92abbf26ccfeae` |

---

## 2. O que foi implementado em `motor_v10` (fatos confirmados)

`motor_v10` preserva byte a byte todas as **229/229 TMs de Scarlet/Violet**, a loja ampliada, `compatibilidade_tms_motor_v8.bin`, as 8 HMs infinitas, o `estojo_v2` paginado, o `treino_ev` e os encontros selvagens/fixos, e utiliza o último slot livre `255` (`EFF_V10_DISPATCH`) de `gBattleScriptsForMoveEffects` em conjunto com `CMD_TABLE_V10` (`0x00, 0x01, 0x04, 0x05, 0x06, 0x0C, 0x88, 0xDD`) para consolidar **200 golpes** (`162` atualizações em `MOVE_TABLE` + `38` golpes `eff=0` enriquecidos nos hooks de cálculo) e restaurar mais **3 aprendizados por nível**:

### 2.1. Família A — Motor unificado de Berries (`133..175`) e +3 learnsets (`Stuff Cheeks` e `Teatime`)

- **Motor de efeitos de Berry (`hook_berry_step_v10` sobre `NEW_ITEMS_TABLE = 0x08E11000`, `holdEffect` `1..21`):**
  - Cura de HP (`he == 1` e `10..14`): `Oran Berry` (`+10` HP), `Sitrus Berry` (`142`, `25%` do `maxHP` conforme padrão Gen 4–9) e `Figy/Wiki/Mago/Aguav/Iapapa` (`33%` do `maxHP`), respeitando `Heal Block` / `Psychic Noise`.
  - Cura de status (`he == 2..6, 8, 9`): `Cheri`, `Chesto`, `Pecha`, `Rawst`, `Aspear`, `Persim` e `Lum` sincronizando `BattlePokemon.status1/status2`, `Pokemon` (`MON_DATA_STATUS = 0x37`), `EmitSetMonData(0x28)` e `updatestatusicon` (`0x98` + `waitstate` `0x3A`).
  - Restauração de PP (`he == 7`, `Leppa Berry`): restaura até `+10` PP priorizando slots zerados e respeitando `ppBonuses` (`MON_DATA_PP1..4 = 0x11..0x14`).
  - Impulsos de estágio e crítico (`he == 15..21`): `Liechi/Ganlon/Salac/Petaya/Apicot` (`+1`), `Lansat` (`Focus Energy`) e `Starf` (`+2` em atributo aleatório elegível).
- **Golpes integrados ao motor de Berries:**
  - `Stuff Cheeks` (`672`, restaura `#819 Skwovet` nv. `10` e `#820 Greedent` nv. `1`): falha sem Berry ou sob `Magic Room`; consome a Berry equipada aplicando seu efeito completo e em seguida eleva `Defense +2`.
  - `Teatime` (`677`, restaura `#855 Polteageist` nv. `0`): varre todos os bancos vivos em Simples ou Duplas e faz cada portador de Berry consumi-la imediatamente (ignorando `Substitute`).
  - `Bug Bite` (`449`, `TM182`) e `Pluck` (`365`): após causar dano, roubam e consomem imediatamente a Berry do alvo no usuário (respeitando `Sticky Hold = 60`).
  - `Incinerate` (`509`): incinera a Berry do alvo sem disparar seu efeito (respeitando `Sticky Hold = 60`).
  - `Belch` (`558`, `120` BP): rastreia por slot da equipe (`ate_berry_mask[side]`, tanto por `Stuff Cheeks`/`Teatime`/`Bug Bite`/`Pluck` quanto por consumo natural via `sync_berry_watchers`) e falha enquanto o Pokémon ainda não tiver comido uma Berry na batalha.

### 2.2. Família B — Dreno 75%, Knock Off 1.5x, Multi-hit especializados, Críticos 100% e correção de golpes `acc == 0`

- **Dreno de 75% (`hook_negativedamage_v10`, `CMD 0x88`):** `Draining Kiss` (`573`, `TM037`) e `Oblivion Wing` (`605`) drenam `floor(3 * dano / 4)` (mín. `1`), enquanto `Horn Leech` (`528`), `Parabolic Charge` (`566`), `Bitter Blade` (`778`) e `Matcha Gotcha` (`786`, com `20%` de queimadura) drenam `50%`.
- **`Knock Off` (`282`, `TM181`):** atualizado para `65` BP base com multiplicador `1.5x` (`97,5` BP efetivos) em `hook_damage_v10` quando o alvo segura um item.
- **Multi-hit especializados:**
  - `Scale Shot` (`703`, `TM200`): `2–5` hits seguidos de `Def -1` e `Speed +1` no usuário (`_sub_scale_shot` preservando os `7` B completos de `tryfaintmon` antes de `0x08185832`).
  - `Population Bomb` (`752`): até `10` acertos independentes de `20` BP fixos.
  - `Surging Strikes` (`712`, `3` hits + crítico garantido), `Triple Dive` (`757`, `3` hits) e `Double Iron Bash` (`668`, `2` hits + `30%` Flinch), além de `Tail Slap` (`537`), `Water Shuriken` (`590`), `Double Hit` (`457`), `Dual Chop` (`526`), `Gear Grind` (`540`), `Dragon Darts` (`676`), `Twin Beam` (`775`) e `Tachyon Cutter` (`795`).
- **Crítico garantido (`100%`) e razão crítica elevada (`hook_critcalc_v10`, `CMD 0x04`):**
  - `Storm Throw` (`479`), `Frost Breath` (`520`), `Wicked Blow` (`711`), `Surging Strikes` (`712`) e `Flower Trick` (`762`) sempre resultam em crítico salvo `Battle Armor` (`4`) ou `Shell Armor` (`75`).
  - `Snipe Shot` (`670`), `Esper Wing` (`733`), `Triple Arrows` (`736`) e `Ivy Cudgel` (`788`) acumulam `+1` estágio crítico junto aos seus efeitos secundários; `Night Slash` (`400`), `Psycho Cut` (`427`), `Attack Order` (`453`), `Spacial Rend` (`459`), `Cross Poison` (`439`) e `Aqua Cutter` (`782`) recebem `eff=43`/`209`.
- **Defeito real corrigido em `CMD 0x01` (`hook_accuracycheck_v10`):** na engine Gen 3, `acc == 0` em `MOVE_TABLE` só ignora checagem de precisão quando `eff == 17` (`Swift`/`Aerial Ace`); golpes ofensivos Gen 4–9 com `acc == 0` e `eff != 17` (`Flower Trick 762`, `Kowtow Cleave 761`, `Smart Strike 639 / TM053`, `Disarming Voice 570 / TM032`, `Tachyon Cutter 795`, `Clear Smog 498`, `Magnet Bomb 442`, `False Surrender 698`, `Trump Card 376`, `Hyperspace Hole 589` e `Hyperspace Fury 613`) calculavam `0%` de acerto e erravam sempre. Em `motor_v10`, todos os `11` acertam infalivelmente (respeitando voo/mergulho/escavação, enquanto `Feint 364`, `Hyperspace Hole 589`, `Hyperspace Fury 613` e `Hyper Drill 774` atravessam `Protect`/`Detect`).

### 2.3. Família C — Aterramento, Terrenos, Quebra-telas, Tipos/Categorias adaptativos e Cura de aliado

- **Aterramento sem colaterais de `Ingrain`:** `Smack Down` (`478`, `TM065`) e `Thousand Arrows` (`606`) gravam `smacked_down_tag[tgt]` em `V10_STATE` (sem ligar `STATUS3_INGRAIN`), derrubando alvos `Flying` / `Levitate` / `Magnet Rise`. No primeiro impacto contra alvo não aterrado, `Thousand Arrows` causa dano neutro `1x` de `Ground`.
- **Remoção de terreno:** `Ice Spinner` (`753`, `TM124`) limpa qualquer terreno ativo após causar dano; `Steel Roller` (`702`, `TM204`) falha sem terreno ativo e destrói o terreno ao acertar.
- **Adaptação de tipo, categoria e eficácia:**
  - `Raging Bull` (`765`): assume tipo `Fire`/`Water`/`Fighting`/`Normal` conforme o usuário e usa `eff=186` (`Brick Break`) para quebrar `Reflect`, `Light Screen` e `Aurora Veil`.
  - `Freeze-Dry` (`569`): trata `Water` (`11`) como fraco (`2x`) durante `hook_typecalc_v10` (atingindo `Water/Flying` com `4x`) e mantém `10%` de congelamento.
  - `Flying Press` (`556`): combina a eficácia de `Fighting` (`1`) com o multiplicador adicional de `Flying` (`2`).
  - `Photon Geyser` (`667`), `Shell Side Arm` (`704`), `Tera Starstorm` (`790`) e `Tera Blast` (`804`, `TM171`): comparam `Atk` vs `SpA` efetivos (com estágios) e usam `Atk vs Def` quando `Atk > SpA` (preservando `Wonder Room` de `motor_v8`); `Secret Sword` (`544`) atinge a Defesa física do alvo; `Sunsteel Strike` (`659`), `Moongeist Beam` (`660`) e `Photon Geyser` (`667`) ignoram habilidades defensivas.
  - `Revelation Dance` (`641`), `Ivy Cudgel` (`788`) e `Aura Wheel` (`688`, exclusivo de Morpeko `#877`, `+1 Speed` e alternância `Electric`/`Dark`); `Ion Deluge` (`565`) e `Plasma Fists` (`666`) eletrificam golpes `Normal` no turno; `Burn Up` (`637`) e `Double Shock` (`779`) consomem o tipo `Fire` / `Electric` do usuário.
  - `Pollen Puff` (`631`, `TM131`): cura o aliado em `50%` do `maxHP` em Duplas ou causa dano normal (`90` BP `Bug`) em oponentes.

### 2.4. Família D — Prioridade condicional, Phazing, Resíduos de fim de turno, Som e Travas

- `Sucker Punch` (`389`) e `Thunderclap` (`793`): prioridade `+1`; falham se o alvo já agiu ou escolheu golpe de status.
- `Grassy Glide` (`805`, `TM194`): recebe prioridade `+1` em `hook_turn_start_v10` quando o usuário está aterrado sob `Grassy Terrain`.
- `Dragon Tail` (`521`, `TM044`) e `Circle Throw` (`508`): causam dano e forçam troca aleatória do oponente (`CMD 0x8F`, respeitando `Suction Cups` e `Ingrain`).
- `Spectral Thief` (`658`) rouba todos os estágios positivos do alvo antes do cálculo de dano; `Clear Smog` (`498`) zera todos os estágios do alvo; `Sacred Sword` (`529`), `Chip Away` (`497`) e `Darkest Lariat` (`618`) ignoram estágios de Defesa/Evasão.
- **Resíduos encadeados em `hook_endturn_v10`:**
  - `Salt Cure` (`756`): causa `1/8` do `maxHP` por turno (`1/4` se o alvo tiver tipo `Water` ou `Steel`).
  - `Syrup Bomb` (`787`, `TM209`): reduz `Speed -1` do alvo por `3` turnos.
  - `Throat Chop` (`630`, `TM221`): bloqueia todos os golpes de som do alvo por `2` turnos (`is_sound_move_v10`, incluindo `Snarl 551`, `Noble Roar 564`, `Hyper Voice 304`, `Torch Song 763`, `Alluring Voice 819` e `Psychic Noise 820`).
- `Gigaton Hammer` (`780`) e `Blood Moon` (`785`): impedem uso em turnos consecutivos pelo mesmo slot da equipe (`prev_heavy_slot` 1-based).
- `Thousand Waves` (`607`), `Spirit Shackle` (`617`), `Anchor Shot` (`632`) e `Jaw Lock` (`671`) aplicam `STATUS2_ESCAPE_PREVENTION` no impacto; `Wake-Up Slap` (`358`), `Sparkling Aria` (`619`), `Core Enforcer` (`642`), `Fell Stinger` (`561`), `Glaive Rush` (`754`), `Dire Claw` (`721`), `Malignant Chain` (`796`), `Eerie Spell` (`720`), `Victory Dance` (`730`) e auto-modificações pós-dano (`Hammer Arm`, `Ice Hammer`, `Spin Out`, `Clanging Scales`, `Make It Rain`, `V-create`, `Torch Song`, `Aqua Step`, `Mystical Power`, `Psyshield Bash`, `Esper Wing`) completam o despacho.

### 2.5. Família E — Potências dinâmicas, Peso com `Autotomize` e ajustes numéricos SV

- `Rage Fist` (`776`): `50 + 50 * hits` (máx. `350` BP), contado por slot da equipe em `hook_datahpupdate_v10` **apenas no frame efetivo em que `CURR_INSTR` avança** (`CONTROLLER_EXEC_FLAGS == 0` e fora de resíduos de fim de turno), evitando contagem múltipla durante a animação da barra de HP.
- `Last Respects` (`746`): `50 + 50 * aliados_desmaiados` na equipe do usuário.
- `Bolt Beak` (`679`) e `Fishious Rend` (`680`): `170` BP quando o usuário age antes do alvo (`85` BP caso contrário).
- `Collision Course` (`768`) e `Electro Drift` (`769`): multiplicador adicional de `4/3x` (`+33%`) em acertos super efetivos.
- `Autotomize` (`474`): cada uso reduz em `100,0 kg` (`1000 hg`, mín. `0,1 kg`) o peso efetivo consultado por `Low Kick` (`67` / `Grass Knot` via `CMD 0xDD`), `Heavy Slam` (`483`, `TM186`) e `Heat Crash` (`531`, `TM189`).
- Demais potências dinâmicas e `19` atualizações numéricas SV em golpes Gen 1–3 (`Fly 90`, `Dig 80`, `Outrage 120/10PP`, `Future Sight 120/100%/10PP`, `Overheat 130`, `Heat Wave 95`, `Muddy Water 90`, `Uproar 90`, `Fire Spin/Whirlpool/Sand Tomb 35/85%`, `Bullet Seed/Icicle Spear 25`, `Thunder Wave/Toxic/Rock Blast 90%`, `Will-O-Wisp 85%`, `Scary Face 100%`, `Brine`, `Payback`, `Assurance`, `Trump Card`, `Wring Out`/`Crush Grip`, `Punishment`, `Last Resort`, `Round`, `Echoed Voice`, `Retaliate`, `Grav Apple`, `Dragon Energy`, `Barb Barrage`, `Infernal Parade`, `Psyblade`, `Hydro Steam`, `Fickle Beam`).

---

## 3. Contabilidade consolidada dos 729 aprendizados por nível originalmente omitidos

Partindo dos `729` registros (`81` golpes) listados em `docs/golpes_pendentes_complemento.csv`:

| Etapa | Golpes restaurados na etapa | Registros restaurados | Total em `learnsets_motor_*.csv` | Acumulado restaurado |
|---|---:|---:|---:|---:|
| Base `motor_v5` | — | — | `14.300` | `0 / 729` (`0,0%`) |
| `motor_v6` | `1` (`Fling`) | `+23` | `14.323` | `23 / 729` (`3,2%`) |
| `motor_v7` | `5` (`Heal Pulse`, `Parting Shot`, `Geomancy`, `Floral Healing`, `Life Dew`) | `+59` | `14.382` | `82 / 729` (`11,2%`) |
| `motor_v8` | `18` (terrenos, salas, gravidade, hazards, `Snowscape`, `Tailwind`, `Shore Up`, `Tidy Up`, `Court Change`, `Defog`) | `+245` | `14.627` | `327 / 729` (`44,9%`) |
| `motor_v9` | `51` golpes não-TM (tipos, trocas/splits, curas/pivots, habilidades, ordem de turno, `Natural Gift`, `Magic Room`) | `+378` | `15.005` | `705 / 729` (`96,7%`) |
| **`motor_v10`** | **`2` golpes de Berry (`Stuff Cheeks`, `Teatime`)** | **`+3`** | **`15.008`** | **`708 / 729` (`97,1%`)** |

Restam **exatamente `4` golpes (`21` registros = `2,9%`)** documentadamente fora de escopo por dependerem de habilidades ou fluxos de UI ausentes na engine Gen 3:

| ID interno | Nome | Registros | Motivo técnico objetivo da retenção |
|---:|---|---:|---|
| `492` | `Simple Beam` | `5` | Altera a habilidade do alvo para `Simple`, habilidade inexistente na tabela Gen 3 (`1..77`) desta ROM. |
| `501` | `Ally Switch` | `13` | Exige permuta simultânea de sprites, OAMs, shadow data, `gBattlerPartyIndexes` e mira pendente entre bancos aliados `0 ↔ 2` / `1 ↔ 3` em Duplas. |
| `644` | `Instruct` | `1` | Exige reexecução aninhada completa da máquina de estados de ação de outro combatente dentro do mesmo passo de script. |
| `755` | `Revival Blessing` | `2` | Exige modo dedicado de UI de equipe capaz de selecionar e reviver aliados desmaiados (`HP == 0`) durante o turno sem disparar troca de entrada. |

---

## 4. Arquitetura técnica, endereços na ROM e EWRAM

| Região / Hook | Endereço (arquivo / CPU) | Função |
|---|---|---|
| `BATTLE_INIT_LIT` | `0x051D74` → `0x090D0001` | Zera `V10_STATE` (`0x0203FD60..0x0203FDEF`) no início da batalha e encadeia para `hook_battle_init_v9` (`0x090C9001`). |
| `TURN_START_LIT` | `0x05439C` → `0x090D0009` | Sincroniza watchers de Berry e aliados desmaiados, avança travas de `Gigaton Hammer`/`Blood Moon`, promove `Grassy Glide` sob `Grassy Terrain` e encadeia para `hook_turn_start_v9` (`0x090C9009`). |
| `ENDTURN_CONT_LIT` | `0x053208` → `0x090D0011` | Preserva fast-path imediato para `0x08053221` quando nenhum efeito `v8`..`v10` está ativo; caso contrário, executa `v8` → `v9` → `Salt Cure`, `Syrup Bomb` e expiração de `Throat Chop`. |
| `BATTLE_STRINGS_TABLE_REFS` | `8` literais + teto `0x055C5A` (`480`) | Realoca `gBattleStringsTable` (`445` → `467` ponteiros, `sid 12..478 < 480`) em `0x090CE400`, gravando `22` novas mensagens PT-BR em `0x090CF000`. |
| `SCRIPTS_V10` | `0x10CD000..0x10CE3FF` (`0x090CD000`) | Sub-scripts fixos de despacho (`SCRIPT_TABLE[255] = 0x090CD000`), consumo de Berry, fila de estágios, multi-hit (`Population Bomb`, `Scale Shot`, `Triple Dive`, `Double Iron Bash`), `Matcha Gotcha` e `Pollen Puff`. |
| `CMD_TABLE_V10` | `0x10CFC00..0x10CFFFF` (`0x090CFC00`) | Clona `CMD_TABLE_V9` e encadeia `0x00`, `0x01`, `0x04`, `0x05`, `0x06`, `0x0C` (`datahpupdate`, preservando `0x0B` `healthbarupdate` em `0x090C0029`), `0x88` e `0xDD`. |
| `PAYLOAD_V10` | `0x10D0000..0x10D3BAB` (`0x090D0000`, `15.276` B) | Payload ARM7TDMI Thumb-1 puro (`16` vetores `0x090D0001..0x090D0079`, auditado por Capstone sem instruções Thumb-2/ARMv6 e sem divisão por software não mapeada). |
| `V10_STATE` (EWRAM) | `0x0203FD60..0x0203FDEF` (`144` B `<= 152` B livres) | Estado efêmero por batalha, contíguo após `V9_STATE` (`0x0203FCA0..0x0203FD5F`), com slots 1-based (`0 = nenhum`) e zero impacto em `SaveBlock1`/`SaveBlock2`. |

---

## 5. Como reconstruir e executar as suítes de testes

### 5.1. Reconstruir `learnsets_motor_v10.csv` e aplicar `motor_v10` em arquivo novo

```bash
python3 firered_gen1_9/scripts/gerar_motor_v10.py
python3 firered_gen1_9/scripts/motor_v10.py \
  --rom /caminho/para/motor_v9.gba \
  --saida /caminho/para/motor_v10.gba
```

### 5.2. Testes estruturais e auditoria estrita de bytes (`7/7`)

```bash
MOTOR_V10_BASE=/caminho/para/motor_v9.gba \
python3 -m unittest firered_gen1_9/tests/test_motor_v10.py -v
```

### 5.3. Testes de integração headless em mGBA `0.10.5` (`6/6` + `9/9` EV/IV + `110/110` estruturais)

```bash
MOTOR_V10_ROM=/caminho/para/motor_v10.gba \
MOTOR_V10_BASE=/caminho/para/motor_v9.gba \
MGBA_CORE=/caminho/para/mgba_libretro.so \
python3 -m unittest firered_gen1_9/tests/test_motor_v10_mgba.py -v

TREINO_TEST_ROM=/caminho/para/motor_v10.gba \
MGBA_CORE=/caminho/para/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_treino_ev_mgba.py' -v
```

---

## 6. Limitações conhecidas e separação entre fatos confirmados e pendências

- **Fatos confirmados por testes automatizados:** reconstrução determinística byte a byte (`a533d181...`), auditoria completa dos `32 MiB` garantindo zero mutações fora das janelas declaradas, código Thumb-1 ARM7TDMI puro, funcionamento real em mGBA `0.10.5` das famílias A–E (Berries + `Stuff Cheeks`/`Teatime`/`Belch`/`Bug Bite`/`Incinerate`, `Pollen Puff` em aliado, dreno `75%`, `Knock Off` `1.5x`, `Scale Shot`, `Population Bomb`, `Flower Trick` `acc==0` + `100%` crit, `Thousand Arrows` → `Earthquake`, `Ice Spinner`/`Steel Roller`, `Raging Bull`, `Freeze-Dry`, `Photon Geyser`, `Thunderclap`, `Spectral Thief`, `Salt Cure`, `Throat Chop`, `Gigaton Hammer`, `Dragon Tail`, `Rage Fist`, `Last Respects`, `Bolt Beak`, `Collision Course`, `Autotomize` + `Heavy Slam`) e preservação de `estojo_v2`, `229/229` TMs SV, HMs, save/reload sintético e `treino_ev` (`9/9`).
- **Limitações conhecidas da base Gen 3 (não tratar como paridade 100% com Scarlet/Violet):**
  1. Os `4` golpes de subida de nível listados na Seção 3 (`Simple Beam`, `Ally Switch`, `Instruct`, `Revival Blessing` = `21/729` linhas) permanecem retidos.
  2. Habilidades Gen 4–9 (`78+`, como `Unaware`, `Cud Chew`, `Ripen`, `Sharpness`, `Supreme Overlord`, `Orichalcum Pulse`, `Hadron Engine` etc.), itens modernos pós-Gen 3 (`Heavy-Duty Boots`, `Loaded Dice`, `Booster Energy`, `Punching Glove`, `Clear Amulet`, `Covert Cloak`) e mecânicas de Terastalização não existem nesta base Gen 3 (`Tera Blast` / `Tera Starstorm` operam como golpes `Normal` adaptativos `Atk`/`SpA`).
  3. Golpes exclusivos de formas pós-Gen 3 (`Aura Wheel`, `Raging Bull`, `Ivy Cudgel`) adaptam-se pelos tipos atuais do usuário em `BattlePokemon` em vez de trocas gráficas de forma em tempo real.
