# Motor parcial `v8` — 229/229 TMs de Scarlet/Violet (100% do catálogo), Clima Snow, 4 Terrenos, Salas, Gravidade, Hazards e +245 aprendizados por nível

> **Escopo e regras de segurança:** este documento aplica-se exclusivamente à trilha **FireRed PT-BR Gen 1–9 (32 MiB)** (`VYK-57`), sobre `motor_v7.gba`. Nunca misture endereços ou estados com a ROM histórica de 16 MiB (`BAG_MOD`). Nenhuma ROM comercial (`.gba`), save pessoal (`.sav`) ou save-state é versionado no Git; todos os testes de integração usam exclusivamente saves e estados sintéticos descartáveis em mGBA `0.10.5`.

---

## 1. Cadeia determinística de hashes SHA-256

| Etapa | Gerador (`firered_gen1_9/`) | Entrada (SHA-256) | Saída (SHA-256) |
|---|---|---|---|
| Base parcial 32 MiB | — | — | `6155b6a5fe62528b7b67836d3a47752b1cb3b1a71c1f2b59bfa7a68af0100d67` |
| Estojo expandido `v2` | `scripts/estojo_expandido.py` | `6155b6a5...` | `93dc62e86cfa3dc70c8057fa4ea25031761d48fc5ce4f7615a5a66d4fc280907` |
| Motor ampliado `v5` | `scripts/motor_ampliado.py` | `93dc62e8...` | `cf1de0e237feefcfda6789bc81c726ed13d91d512b85c54b9f857520a7a4fc87` |
| Motor parcial `v6` | `scripts/motor_v6.py` | `cf1de0e2...` | `75d66d3c36e560df29f6c613666b91a6c81ce24663b6a3f76f4dd2ea7d747ce6` |
| Motor parcial `v7` | `scripts/motor_v7.py` | `75d66d3c...` | `6321d8e2900cc44dcaefb2dedfbaf5b0952b2796ca27a4cb9d8dc0875827de09` |
| **Motor parcial `v8`** | `scripts/motor_v8.py` | `6321d8e2...` | **`32fd47c87b581952f54f05656f590c5f7da55d5cc3d186d81951508899ec54f0`** |

Insumos versionados verificados por SHA-256 antes de aplicar `scripts/motor_v8.py`:

| Arquivo | Tamanho | SHA-256 |
|---|---:|---|
| `patches/motor_v8/payload.bin` | `8.264` B | `fc2d75763a5611f0fb5cf4bcd7e48966e088ecce6bb18b25b05859e2ef098131` |
| `data/tms_motor_v8.csv` | `11.968` B | `20eba409d81c459393d6156f5053a3f5bf71e4ac99c7c4574287a39f2b95523c` |
| `data/compatibilidade_tms_motor_v8.bin` | `29.754` B | `358a1b9fa456a23a22f8c3249d5381f75585139a5385690c58a43c1de8eea3ac` |
| `data/learnsets_motor_v8.csv` | `404.233` B | `19abc5661267157524b9dcdc9ad769cdf12a20f9f44a3be63f134ae2ec9120f7` |

---

## 2. O que foi implementado em `motor_v8` (fatos confirmados)

### 2.1. As 10 TMs finais de Scarlet/Violet habilitadas (**229/229 TMs SV = 100% do catálogo**)

| TM | Item ID | Golpe interno | Nome | Tipo / Cat. / PP / Alvo | Efeito implementado e validado em mGBA |
|---:|---:|---:|---|---|---|
| `TM052` | `426` | `773` | `Snowscape` | Ice / Status / `10` / `0x10` | Ativa `WEATHER_SNOW_BIT` (`0x0100` em `gBattleWeather`) por `5` turnos sem dano residual; concede `+50%` Defesa física para Pokémon de tipo Gelo (`15`), torna `Blizzard` (`59`) infalível, converte `Weather Ball` (`311`) para Gelo `100` BP e habilita `Aurora Veil` (`649`). |
| `TM091` | `465` | `390` | `Toxic Spikes` | Poison / Status / `20` / `0x20` | Empilha até `2` camadas no lado oponente (`1` camada = veneno comum `0x08`; `2` camadas = veneno grave `0x80` na entrada de Pokémon aterrados); absorvido automaticamente por Pokémon Venenoso (`3`) aterrado; imune em Aço (`8`), `Immunity` (`17`), `Safeguard`, `Substitute` ou `Misty Terrain`. |
| `TM113` | `487` | `366` | `Tailwind` | Flying / Status / `15` / `0x10` | Dobra (`2x`) a Velocidade efetiva do lado aliado na ordenação de turno (`hook_set_turn_order_v8`) por `4` turnos. |
| `TM116` | `490` | `445` | `Stealth Rock` | Rock / Status / `20` / `0x20` | Armadilha de entrada contra todos os Pokémon (aterrados ou não), causando `(maxHP * mult) >> 5` conforme eficácia dupla de Rocha (`5`) (`1/32` a `1/2` do HP máximo, mínimo `1` HP). |
| `TM136` | `510` | `599` | `Electric Terrain` | Electric / Status / `10` / `0x10` | Terreno Elétrico por `5` turnos: `+30%` em golpes Elétricos (`13`) de atacantes aterrados, bloqueia sono e `Yawn` em alvos aterrados, dobra `Rising Voltage` (`705` → `140` BP) contra alvos aterrados e ativa `Psyblade` (`783` → `120` BP). |
| `TM137` | `511` | `576` | `Grassy Terrain` | Grass / Status / `10` / `0x10` | Terreno de Grama por `5` turnos: `+30%` em golpes de Planta (`12`) de atacantes aterrados, cura `max(1, maxHP / 16)` ao fim de cada turno nos aterrados (respeitando `Psychic Noise`), concede prioridade `+1` a `Grassy Glide` (`805`) quando o usuário está aterrado, reduz em `50%` `Earthquake` (`89`), `Magnitude` (`222`) e `Bulldoze` (`519`) e eleva `Floral Healing` (`621`) para `2/3` do HP máximo em alvos aterrados. |
| `TM138` | `512` | `633` | `Psychic Terrain` | Psychic / Status / `10` / `0x10` | Terreno Psíquico por `5` turnos: `+30%` em golpes Psíquicos (`14`) de atacantes aterrados, bloqueia golpes com prioridade efetiva `> 0` de oponentes contra alvos aterrados e eleva `Expanding Force` (`701`) em `1,5x` (`80 → 120` BP) quando o atacante está aterrado. |
| `TM139` | `513` | `577` | `Misty Terrain` | Fairy / Status / `10` / `0x10` | Terreno Nebuloso por `5` turnos: bloqueia condições primárias/secundárias de status, sono, `Yawn` e confusão por golpe em Pokémon aterrados, reduz pela metade (`0,5x`) o dano de golpes Dragão (`16`) contra alvos aterrados e eleva `Misty Explosion` (`810`) em `1,5x` (`100 → 150` BP) quando o atacante está aterrado. |
| `TM161` | `535` | `433` | `Trick Room` | Psychic / Status / `5` / `0x10` (prio `-7`) | Sala de Truques por `5` turnos (alterna/desliga se usada novamente enquanto ativa): inverte a ordem de Velocidade dentro de cada faixa de prioridade. |
| `TM178` | `552` | `356` | `Gravity` | Psychic / Status / `5` / `0x10` | Gravidade por `5` turnos: aterra todos os Pokémon em campo (inclusive Voadores, `Levitate` e `Magnet Rise`, removendo imunidade de solo e ativando terrenos/hazards terrestres), multiplica a precisão por `5/3` e bloqueia/interrompe `Bounce` (`340`), `Fly` (`19`), `High Jump Kick` (`136`), `Jump Kick` (`26`), `Splash` (`150`) e `Flying Press` (`556`). |

### 2.2. Golpes de subida de nível e sinergias mecânicas integrados na mesma família

- **Salas, barreiras, gravidade e clima:**
  - `Wonder Room` (`471`, prio `0`, `5` turnos com toggle): troca `Def` ↔ `Sp. Def` (valores base e estágios correspondentes) no cálculo de dano físico e especial (exceto `Body Press`, que continua usando a Defesa física do atacante).
  - `Magnet Rise` (`393`, `5` turnos): concede levitação temporária (imune a golpes Terrestres e a hazards/terrenos de solo; falha sob `Gravity` ou `Ingrain`).
  - `Aurora Veil` (`649`, `5` turnos): exige `Snow` ou `Hail`; reduz dano físico e especial pela metade em simples (`2/3` em duplas), não acumula multiplicador extra com `Reflect`/`Light Screen` e é destruído por `Brick Break` (`280`), `Psychic Fangs` (`652`) e `Defog` (`432`).
  - `Chilly Reception` (`771`): anuncia a piada, invoca `Snow` por `5` turnos (se ainda não estiver nevando) e executa troca automática de pivot pelo fluxo seguro `51 01 02` sem herdar estágios.
  - `Shore Up` (`614`): restaura `1/2` do HP máximo normalmente e `2/3` sob `Sandstorm` (respeitando `Psychic Noise`).
- **Sinergias de terreno existentes completadas:**
  - `Terrain Pulse` (`706`): em usuário aterrado sob terreno ativo, dobra para `100` BP e assume o tipo do terreno (`Electric=13`, `Grass=12`, `Psychic=14`, `Fairy=18`).
  - `Steel Roller` (`806` / `TM204`): falha quando não há terreno ativo (`terrain_turns == 0`) e, ao causar dano, destrói o terreno ativo.
- **Armadilhas de entrada, ataques com hazards e limpeza de campo:**
  - `Sticky Web` (`560`): aplica teia pegajosa no lado oponente (`-1` estágio de Velocidade na entrada de Pokémon aterrados, respeitando `Clear Body`/`White Smoke`/`Mist`).
  - `Stone Axe` (`723`) e `Ceaseless Edge` (`738`): após acertar o alvo, instalam respectivamente `Stealth Rock` ou `+1` camada de `Spikes` (`até 3`) no lado oponente.
  - `Rapid Spin` (`229`, `50` BP Gen 8+, `+1` Speed já presente na base): o comando `0xBE` (`Cmd_rapidspinfree`) passa a limpar também `Stealth Rock`, `Toxic Spikes` e `Sticky Web` do lado do usuário.
  - `Mortal Spin` (`758`): causa dano físico Venenoso (`30` BP), envenena o alvo (`100%`) e executa a limpeza completa `0xBE` (`Wrap`, `Leech Seed`, `Spikes`, `Stealth Rock`, `Toxic Spikes` e `Sticky Web`) do lado do usuário.
  - `Defog` (`432`): inescapável (`0xFFFF`), reduz `Evasão -1` do alvo (se não protegido por `Substitute`), remove barreiras/`Mist`/`Safeguard`/`Aurora Veil` do lado do alvo, limpa todos os hazards (`Spikes`, `Stealth Rock`, `Toxic Spikes`, `Sticky Web`) **dos dois lados** e dissipa o terreno ativo.
  - `Tidy Up` (`772`): remove todos os hazards (`Spikes`, `Stealth Rock`, `Toxic Spikes`, `Sticky Web`) e `Substitute` de ambos os lados e eleva `Atk +1` e `Speed +1` do usuário.
  - `Court Change` (`681`): permuta entre os lados `0` e `1` `Reflect`, `Light Screen`, `Mist`, `Safeguard`, `Aurora Veil`, `Tailwind`, `Spikes` (camadas), `Stealth Rock`, `Toxic Spikes` e `Sticky Web`.
- **`+245` aprendizados por nível restaurados** (`14.382` → **`14.627`** registros em `0x08F50000..0x08F5AAAF`, abaixo do teto `0x08F60000`), cobrindo `18` golpes (`356, 366, 390, 393, 432, 433, 445, 471, 560, 576, 577, 599, 614, 633, 649, 681, 772, 773`; `723` já constava em Kleavor `#900` Lv. 0 em `v7`, e `738`/`771` pertencem a formas regionais/evoluções fora dos IDs base `1..1025`).

---

## 3. Arquitetura técnica, endereços na ROM e EWRAM

| Região / Hook | Endereço (arquivo / CPU) | Função |
|---|---|---|
| `BATTLE_INIT_LIT` | `0x051D74` → `0x090C3001` | Zera `V8_STATE` (`64` B em `0x0203FC60`) no início de cada batalha e encadeia para `hook_battle_init_v7` (`0x090C0001`). |
| `TURN_START_LIT` | `0x05439C` → `0x090C3009` | Zera `endturn_step` no início do turno e encadeia para `hook_turn_start_v7` (`0x090C0009`). |
| `SET_TURN_ORDER_LIT` | `0x0538E0` → `0x090C3011` | Ordena os bancos no turno com prioridades dinâmicas (`Trick Room -7`, `Grassy Glide +1`, `Upper Hand +3`), `Tailwind 2x` e inversão de Velocidade em `Trick Room`. |
| `ENDTURN_CONT_LIT` | `0x053208` → `0x090C3019` | Intercepta `BattleTurnPassed` (`0x08053221`, verificando `gBattleControllerExecFlags` em `0x020213F0`), executa `DoFieldEndTurnEffects` (`0x0806D069`) preservando `gBattleMainFunc == 0x08053221`, processa cura de `Grassy Terrain` (`1/16`) e decaimento de `Snow`, `Tailwind`, `Aurora Veil`, terrenos, `Gravity`, `Trick Room`, `Wonder Room` e `Magnet Rise`, e delega o restante do turno a `0x08053221` (no-op exato quando nenhum efeito `v8` está ativo). |
| `BATTLE_STRINGS_TABLE_REFS` | `8` literais + teto `0x055C5A` (`d4 23`) | Realoca `gBattleStringsTable` (`374` → `408` ponteiros, `sid 12..419`) para `0x090C1800`, adicionando `34` strings PT-BR em `0x090C2000`. |
| `SCRIPTS_V8` | `0x10C1000..0x10C17FF` (`0x090C1000`) | Sub-scripts fixos de hazards/fim de turno/cancelamento e BattleScripts dos efeitos `234` (atualizado para `Grassy Terrain`) e `236..242`. |
| `CMD_TABLE_V8` | `0x10C2800..0x10C2BFF` (`0x090C2800`) | Tabela realocada `gBattleScriptingCommandsTable`: preserva hooks de `v6`/`v7` (`0x04, 0x0B, 0x0C, 0x49, 0x89, 0xF8..0xFF`) e instala wrappers em `0x00, 0x01, 0x05, 0x06, 0x15, 0x16, 0x17, 0x52, 0x84, 0xBE, 0xE9, 0xEE`. |
| `PAYLOAD_V8` | `0x10C3000..0x10C5047` (`0x090C3000`, `8.264` B) | Payload ARM7TDMI Thumb-1 puro (`28` vetores fixos `0x090C3001..0x090C30D9` + lógica C sem `libgcc`). |
| `V8_STATE` (EWRAM) | `0x0203FC60..0x0203FC9F` (`64` B) | Estado transitório por batalha, contíguo após `V7_STATE` (`0x0203FC00..0x0203FC5F`), fora de `SaveBlock1`/`SaveBlock2` (zero impacto em saves `.sav`). |

---

## 4. Limitações conhecidas, fatos vs. hipóteses e escopo restante

Seguindo a diretriz estrita do projeto de **separar fatos confirmados de hipóteses e não tratar 229/229 TMs habilitadas como fidelidade integral ao motor de Scarlet/Violet**:

1. **Itens e habilidades modernos ausentes na base Gen 3 (fatos confirmados):**
   - A tabela de itens (`0..604`) e a tabela de habilidades de FireRed não contêm itens modernos (`Heavy-Duty Boots`, `Terrain Extender`, `Light Clay`, `Icy Rock`, `Room Service`, `Electric/Grassy/Misty/Psychic Seed`, `Iron Ball`, `Air Balloon`, `Power Herb`) nem habilidades modernas (`Electric/Grassy/Misty/Psychic Surge`, `Slush Rush`, `Ice Body`, `Snow Cloak`, `Magic Guard`, `Defiant`, `Competitive`, `Contrary`, `Good as Gold`). Portanto, clima/terrenos/véu duram sempre `5` turnos (`Tailwind` `4` turnos), e não há imunidade por `Heavy-Duty Boots` a hazards.
2. **Seleção de alvo em batalhas em dupla para `Expanding Force` (`701`):**
   - Em `Psychic Terrain` com atacante aterrado, `Expanding Force` recebe o bônus de `1,5x` (`120` BP), porém mantém o cursor nativo de alvo único da tabela estática `MOVE_TABLE` de FireRed em duplas (não altera dinamicamente o menu de seleção de alvos para spread).
3. **Aprendizados por nível ainda omitidos (documentados):**
   - Dos `729` registros (`81` golpes) originalmente listados em `docs/golpes_pendentes_complemento.csv`, **`327` registros (`24` golpes)** já foram restaurados com efeito funcional entre `motor_v6` (`+23`), `motor_v7` (`+59`) e `motor_v8` (`+245`), restando **`402` registros distribuídos em `57` golpes não-TM** ainda omitidos para não expor golpes sem efeito dedicado na subida de nível.
4. **IA dos treinadores da campanha:**
   - Os treinadores originais de Kanto utilizam as rotinas nativas de pontuação de IA de FireRed; não possuem heurísticas competitivas específicas para reposicionar `Trick Room`, `Court Change` ou `Chilly Reception`.

---

## 5. Como reconstruir e executar as suítes de testes

### 5.1. Aplicar `motor_v8` em um arquivo novo (verificando SHA-256)

```bash
PYTHONPATH=firered_gen1_9 python3 -m scripts.motor_v8 \
  --rom /caminho/para/motor_v7.gba \
  --saida /caminho/para/motor_v8.gba
```

### 5.2. Testes estruturais e invariantes da cadeia (`v5` → `v6` → `v7` → `v8`)

```bash
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_TEST_BASE=/caminho/para/estojo_v2.gba \
MOTOR_TEST_ROM=/caminho/para/motor_v5.gba \
MOTOR_V6_BASE=/caminho/para/motor_v5.gba \
MOTOR_V7_BASE=/caminho/para/motor_v6.gba \
MOTOR_V8_BASE=/caminho/para/motor_v7.gba \
python3 -m unittest \
  firered_gen1_9/tests/test_encontros_selvagens.py \
  firered_gen1_9/tests/test_eventos_fixos.py \
  firered_gen1_9/tests/test_modelo_treino.py \
  firered_gen1_9/tests/test_treino_ev_patcher.py \
  firered_gen1_9/tests/test_motor_ampliado.py \
  firered_gen1_9/tests/test_motor_v6.py \
  firered_gen1_9/tests/test_motor_v7.py \
  firered_gen1_9/tests/test_motor_v8.py -v
```

### 5.3. Testes de integração headless em mGBA `0.10.5` (apenas saves/estados sintéticos)

```bash
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V8_ROM=/caminho/para/motor_v8.gba \
MOTOR_V8_BASE=/caminho/para/motor_v7.gba \
TREINO_TEST_ROM=/caminho/para/motor_v8.gba \
MGBA_CORE=/caminho/para/mgba_libretro.so \
python3 -m unittest \
  test_motor_v8_mgba \
  test_treino_ev_mgba -v
```

Resultados verificados nesta entrega:
- `test_motor_v8.py`: **`8/8` OK** (catálogo `229/229` com `0` TMs pendentes, matriz de compatibilidade superconjunto estrito de `v7`, `+245` entradas de nível = `14.627` linhas, payload ARM7TDMI Thumb-1 puro com `28` vetores, determinismo `32fd47c8...`, loja com `229` TMs e preservação byte a byte de `estojo_v2`, HMs `339..346`, `treino_ev`, `payload_v6`, `payload_v7` e terminadores de egg moves `797`).
- `test_motor_v8_mgba.py`: **`6/6` OK** em mGBA `0.10.5` (ensino real no `estojo_v2` paginado com consumo único de TM vs HM infinita e persistência em save Flash/reload; subida de nível + Move Relearner nas espécies `v8`; `Snowscape` / Defesa Gelo `+50%` / `Blizzard` infalível / `Weather Ball` Gelo `100` BP / `Aurora Veil` / `Psychic Fangs` / `Chilly Reception` pivot; 4 terrenos + `Grassy Glide` prio `+1` / `Expanding Force` / `Misty Explosion` / `Rising Voltage` / `Psyblade` / `Terrain Pulse` / `Steel Roller`; `Tailwind` / `Trick Room` toggle / `Wonder Room` toggle / `Gravity` / `Magnet Rise` / `Shore Up`; `Stealth Rock` / `Toxic Spikes` 2 camadas + absorção por Venenoso / `Sticky Web` `-1` Speed / `Stone Axe` / `Ceaseless Edge` / `Mortal Spin` / `Defog` / `Tidy Up` / `Court Change`; regressão de `U-turn`, `Meteor Beam`, `Shell Smash`, `Body Press` e `Gyro Ball`).
- `test_treino_ev_mgba.py` (sobre `motor_v8.gba`): **`9/9` OK**.
- `test_motor_v7_mgba.py` (sobre `motor_v7.gba`): **`11/11` OK**.
- Suíte estrutural completa do pacote (`8` arquivos): **`83/83` executados OK** (`7` pulados por exigirem ROMs intermediárias antigas privadas).
