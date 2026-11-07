# Motor parcial `v7` — 219/229 TMs de Scarlet/Violet, trocas automáticas (pivots) e 59 aprendizados por nível

> **Escopo e regras de segurança:** este documento aplica-se exclusivamente à trilha **FireRed PT-BR Gen 1–9 (32 MiB)** (`VYK-57`), sobre `motor_v6.gba`. Nunca misture endereços ou estados com a ROM histórica de 16 MiB (`BAG_MOD`). Nenhuma ROM comercial (`.gba`), save pessoal (`.sav`) ou save-state é versionado no Git; todos os testes de integração usam exclusivamente saves e estados sintéticos descartáveis em mGBA `0.10.5`.

---

## 1. Cadeia determinística de hashes SHA-256

| Etapa | Gerador (`firered_gen1_9/`) | Entrada (SHA-256) | Saída (SHA-256) |
|---|---|---|---|
| Base parcial 32 MiB | — | — | `6155b6a5fe62528b7b67836d3a47752b1cb3b1a71c1f2b59bfa7a68af0100d67` |
| Estojo expandido `v2` | `scripts/estojo_expandido.py` | `6155b6a5...` | `93dc62e86cfa3dc70c8057fa4ea25031761d48fc5ce4f7615a5a66d4fc280907` |
| Motor ampliado `v5` | `scripts/motor_ampliado.py` | `93dc62e8...` | `cf1de0e237feefcfda6789bc81c726ed13d91d512b85c54b9f857520a7a4fc87` |
| Motor parcial `v6` | `scripts/motor_v6.py` | `cf1de0e2...` | `75d66d3c36e560df29f6c613666b91a6c81ce24663b6a3f76f4dd2ea7d747ce6` |
| **Motor parcial `v7`** | `scripts/motor_v7.py` | `75d66d3c...` | **`6321d8e2900cc44dcaefb2dedfbaf5b0952b2796ca27a4cb9d8dc0875827de09`** |

Insumos versionados verificados por SHA-256 antes de aplicar `scripts/motor_v7.py`:

| Arquivo | Tamanho | SHA-256 |
|---|---:|---|
| `patches/motor_v7/payload.bin` | `3.376` B | `4b2c1948aa0ac7a46ed976e114445a71242bf1d1c69c0ba59adc22d9181f6843` |
| `data/tms_motor_v7.csv` | `9.791` B | `ef1fd0c595e644805a3b2722d30ac146807632c925ac5108cae1314cfcc8dace` |
| `data/compatibilidade_tms_motor_v7.bin` | `29.754` B | `618563d9dbc6ead8ecce2ae0f38978ec62ff0da5ebae2e294efaffbb7e1420d7` |
| `data/learnsets_motor_v7.csv` | `396.726` B | `ed8e02a3bb3665a68ed3d53a59c2532d273bf0cbda630ef77aee56e6cbc6c2fe` |

---

## 2. O que foi implementado em `motor_v7` (fatos confirmados)

### 2.1. 9 novas TMs de Scarlet/Violet habilitadas (`813..821` → total **219/229 TMs SV**)

| TM | Item ID | Golpe interno | Nome | Tipo / Cat. / Poder / Prec. / PP | Efeito implementado e validado em mGBA |
|---:|---:|---:|---|---|---|
| `TM195` | `569` | `813` | `Burning Jealousy` | Fire / Esp. / `70` / `100` / `5` (alvo `0x08` ambos oponentes) | Efeito `231`: queima cada alvo atingido cujo estágio subiu no turno atual (`stat_up_this_turn` avaliado por alvo, inclusive em duplas). |
| `TM199` | `573` | `814` | `Lash Out` | Dark / Fís. / `75` / `100` / `5` | Efeito `0` + `hook_damage_v7`: dobra o poder dinâmico para `150` BP se algum estágio do usuário caiu no turno atual (`stat_down_this_turn`). |
| `TM207` | `581` | `815` | `Temper Flare` | Fire / Fís. / `75` / `100` / `10` | Efeito `0` + `hook_damage_v7`: dobra para `150` BP quando a ação anterior do usuário falhou, errou, bateu em imunidade ou foi cancelada (ex.: Flinch). |
| `TM213` | `587` | `816` | `Coaching` | Fighting / Status / `0` / `0` / `10` | Efeito `228`: em duplas, eleva `Atk +1` e `Def +1` do parceiro vivo; falha em batalha simples ou com parceiro desmaiado. |
| `TM220` | `594` | `817` | `Meteor Beam` | Rock / Esp. / `120` / `90` / `10` | Efeito `226`: turno 1 carrega (`STATUS2_MULTIPLETURNS`), exibe `"[user] está brilhando!"` e eleva `Sp. Atk +1`; turno 2 executa o disparo especial de Rocha. |
| `TM226` | `600` | `818` | `Dragon Cheer` | Dragon / Status / `0` / `0` / `15` | Efeito `229`: em duplas, concede `+1` estágio crítico ao parceiro (`+2` se o parceiro tiver tipo Dragão `16`); não acumula nem convive com Focus Energy (`0x00100000`). |
| `TM227` | `601` | `819` | `Alluring Voice` | Fairy / Esp. / `80` / `100` / `10` | Efeito `232`: confunde o alvo se algum estágio dele subiu no turno atual. |
| `TM228` | `602` | `820` | `Psychic Noise` | Psychic / Esp. / `75` / `100` / `10` | Efeito `233`: aplica bloqueio de cura por `2` turnos (`heal_block_turns[tgt] = 2`), impedindo curas diretas (`Recover`, `Heal Pulse`, `Life Dew`, etc.) e absorção de HP (`Mega Drain` causa dano ao alvo, mas cancela a cura do atacante). |
| `TM229` | `603` | `821` | `Upper Hand` | Fighting / Fís. / `65` / `100` / `15` (prio `+3`) | Efeito `230`: acerta com `100%` de hesitação (`Flinch`) apenas se o alvo escolheu golpe ofensivo de prioridade `> 0` e ainda não agiu neste turno; falha contra golpes de prioridade `<= 0` ou de status (ex.: `Baby-Doll Eyes`). |

### 2.2. Trocas automáticas pós-golpe (pivots) e golpes existentes aprimorados

- **`TM060 U-turn` (`369`), `TM048 Volt Switch` (`517`) e `TM196 Flip Turn` (`708`)** → efeito `224`: após causar dano (e executar `moveend 2, 16`), verifica reserva apta na equipe do atacante e aciona `openpartyscreen (50 01)` + `switchhandleorder (51 01 02)` + `switchindataupdate (4D 01)` + `jumpifcantswitch (4E 01 00)`, **sem** herança de estágios ou Substitute de `Baton Pass` (`226`). Se não houver reserva viva ou o alvo estiver imune/desviar, não abre tela de troca.
- **`Parting Shot` (`571`)** → efeito `225`: reduz `Atk -1` e `Sp. Atk -1` do alvo e, se pelo menos uma redução teve efeito (ex.: bloqueado por `Clear Body` impede a troca), realiza a troca automática pelo mesmo fluxo seguro `51 01 02`.
- **`Stomping Tantrum` (`653` / `TM179`)**: integrado ao rastreador `prev_failed_mask` em `hook_damage_v7`, dobrando de `75` para `150` BP após falha/cancelamento da ação anterior do banco.
- **`Geomancy` (`597`)** → efeito `227`: ciclo de 2 turnos (`STATUS2_MULTIPLETURNS` no turno 1; `Sp. Atk +2`, `Sp. Def +2` e `Speed +2` no turno 2).
- **`Heal Pulse` (`504`) e `Floral Healing` (`621`)** → efeito `234`: curam `ceil(maxHP / 2)` do alvo selecionado e falham se HP já estiver cheio ou sob `Psychic Noise`.
- **`Life Dew` (`696`)** → efeito `235`: cura `max(1, maxHP / 4)` do usuário e, em duplas, também do parceiro vivo (respeitando `Psychic Noise` individualmente).
- **`+59` aprendizados por nível restaurados** (`14.323` → **`14.382`** entradas em `0x08F50000..0x08F5A8BA`, abaixo do limite `0x08F60000`), cobrindo integralmente as entradas de Scarlet/Violet de `Heal Pulse` (`504`, `22` entradas), `Parting Shot` (`571`, `8`), `Geomancy` (`597`, `1` — Xerneas Lv. 55), `Floral Healing` (`621`, `1` — Comfey Lv. 30) e `Life Dew` (`696`, `27`), funcionando tanto na subida de nível (`0x08109790`) quanto no Move Relearner (`0x0810E808`).

---

## 3. Arquitetura técnica, endereços na ROM e EWRAM

| Região / Hook | Endereço (arquivo / CPU) | Função |
|---|---|---|
| `MOVE_NAME_CAP_SITES` | `0x055B36`, `0x056350`, `0x056370` | `mov r2, #0xCE` (`0xCE << 2 = 824`), cobrindo golpes `0..821` + sentinelas seguros `822..824`. |
| `BATTLE_INIT_LIT` | `0x051D74` → `0x090C0001` | Zera `V7_STATE` (`96` B em `0x0203FC00`) no início de cada batalha e encadeia para `0x08052725`. |
| `TURN_START_LIT` | `0x05439C` → `0x090C0009` | Atualiza `prev_failed_mask`, decrementa `heal_block_turns[0..3]`, limpa flags por turno (`stat_up_this_turn`, `stat_down_this_turn`) e encadeia para `0x080544B9`. |
| `SCRIPTS_V7` | `0x10BF000` (`0x090BF000`, `477` B) | BattleScripts dos efeitos `224..235` + rotina de cancelamento de cura por `Psychic Noise`. |
| `DESC_TEXT_V7` | `0x10BF800` (`0x090BF800`) | Descrições PT-BR de golpes (`813..821`) e descrições de itens das 9 novas TMs. |
| `CMD_TABLE_V7` | `0x10BFC00` (`0x090BFC00`, `1.024` B) | Tabela realocada `gBattleScriptingCommandsTable`: preserva `0xF8..0xFF` (`callasm` `0x090BE009` de `motor_v6`) e instala wrappers em `0x00, 0x04, 0x05, 0x0B, 0x0C, 0x15, 0x16, 0x17, 0x49, 0x89`. |
| `PAYLOAD_V7` | `0x10C0000` (`0x090C0000`, `3.376` B) | Payload ARM7TDMI Thumb-1 puro (`26` vetores fixos `0x090C0001..0x090C00C9` + lógica C sem `libgcc`). |
| `V7_STATE` (EWRAM) | `0x0203FC00..0x0203FC5F` (`96` B) | Estado transitório por batalha (fora do `SaveBlock1`/`SaveBlock2`; zero impacto em saves `.sav`). |

> **Nota crítica de engenharia reversa (`Cmd_switchhandleorder` `0x51`):** na ROM FireRed PT-BR (`0x0805DBBA`), `51 01 01` (`arg2 == 1`) lê `*(gBattleStruct + 0x60 + bank)` sem copiar a seleção de `openpartyscreen` (`gBattleBufferB[bank][1]`), causando troca fora de faixa (slot `6`). Após `openpartyscreen` (`50 01`), o opcode obrigatório é **`51 01 02`** (`arg2 == 2`, `0x0805DBFA`), seguido de `4D 01` e `4E 01 00`. A herança de estágios/Substitute só ocorre em `switchindataupdate` quando `gCurrentMove == 226` (`Baton Pass`) e `4E 01 01`.

---

## 4. Limitações conhecidas, fatos vs. hipóteses e escopo adiado

Seguindo a diretriz estrita do projeto de **não tratar disponibilidade de item ou testes sintéticos como fidelidade completa ao motor de Scarlet/Violet**:

1. **Interações modernas não existentes no motor base Gen 3 (fatos confirmados):**
   - `Meteor Beam` (`817`) e `Geomancy` (`597`) executam sempre o ciclo de 2 turnos (o item moderno `Power Herb` não existe na tabela `0..604`).
   - `Floral Healing` (`621`) cura `50%` do HP máximo (não há estado global de `Grassy Terrain` para elevar a `2/3`).
   - `Dragon Cheer` (`818`), `Alluring Voice` (`819`) e `Psychic Noise` (`820`) não implementam imunidade especial por `Soundproof` nem bypass de `Substitute` de golpes sonoros modernos.
   - `U-turn`, `Volt Switch`, `Flip Turn` e `Parting Shot` realizam a troca padrão da equipe, sem itens/habilidades modernos de saída forçada (`Eject Button`, `Red Card`, `Eject Pack`, `Emergency Exit`, `Wimp Out`) nem bloqueio especial de `Pursuit` na escolha de golpe.
   - `Psychic Noise` (`820`) bloqueia comandos de cura por script (`Recover`, `Rest`, `Heal Pulse`, `Floral Healing`, `Life Dew` e absorções `0x08` de HP negativo) durante 2 turnos; curas passivas não roteadas por script ou uso direto de poção pelo menu da mochila não são interceptadas por `Psychic Noise`.
   - `BattleScript` de IA do oponente usa a lógica nativa de FireRed para seleção de golpes; treinadores da campanha original não possuem heurísticas dedicadas para `Coaching` ou `Upper Hand`.
2. **10 TMs de Scarlet/Violet adiadas (permanecem bloqueadas/ocultas na loja com ícone `?` e `NEW_MOVE_TABLE == 0`):**
   - Clima moderno: `TM052 Snowscape` (`426`)
   - Hazards de entrada: `TM091 Toxic Spikes` (`465`), `TM116 Stealth Rock` (`490`)
   - Condições globais de lado/campo: `TM113 Tailwind` (`487`), `TM161 Trick Room` (`535`), `TM178 Gravity` (`552`)
   - Terrenos: `TM136 Electric Terrain` (`510`), `TM137 Grassy Terrain` (`511`), `TM138 Psychic Terrain` (`512`), `TM139 Misty Terrain` (`513`)
3. **Aprendizados por nível ainda omitidos:** `647` entradas distribuídas em `75` golpes modernos sem efeito fiel implementado permanecem fora de `learnsets_motor_v7.csv` para evitar golpes quebrados ou enganosos na subida de nível.

---

## 5. Como reconstruir e executar as suítes de testes

### 5.1. Aplicar `motor_v7` em um arquivo novo (verificando SHA-256)

```bash
PYTHONPATH=firered_gen1_9 python3 -m scripts.motor_v7 \
  --rom /caminho/para/motor_v6.gba \
  --saida /caminho/para/motor_v7.gba
```

### 5.2. Testes estruturais e invariantes de build

```bash
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V6_BASE=/caminho/para/motor_v5.gba \
MOTOR_V7_BASE=/caminho/para/motor_v6.gba \
python3 -m unittest \
  firered_gen1_9/tests/test_motor_v6.py \
  firered_gen1_9/tests/test_motor_v7.py -v
```

### 5.3. Testes de integração headless em mGBA `0.10.5` (apenas saves/estados sintéticos)

```bash
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V7_ROM=/caminho/para/motor_v7.gba \
MOTOR_V7_BASE=/caminho/para/motor_v6.gba \
TREINO_TEST_ROM=/caminho/para/motor_v7.gba \
MGBA_CORE=/caminho/para/mgba_libretro.so \
python3 -m unittest \
  firered_gen1_9/tests/test_motor_v7_mgba.py \
  firered_gen1_9/tests/test_treino_ev_mgba.py -v
```

Resultado validado nesta entrega:
- `test_motor_v7_mgba.py`: **`11/11 OK`** (nomes `813..821` + sentinela `gBattleTextBuff3`, `Meteor Beam` e `Geomancy` em 2 turnos, `Burning Jealousy`/`Alluring Voice`/`Lash Out`, `Temper Flare` e `Stomping Tantrum` após falha e Flinch, `Upper Hand` `+3`, `Psychic Noise` + `Heal Pulse`/`Floral Healing`, duplas `Coaching`/`Dragon Cheer`/`Life Dew`/`Burning Jealousy` spread, pivots `U-turn`/`Volt Switch`/`Flip Turn`/`Parting Shot` sem herança de `Baton Pass` + bloqueio `Clear Body`, ensino nas 3 páginas do `estojo_v2` com consumo único de TMs, `HM01` infinito e save/reload Flash 128 KiB, learnsets de nível + Move Relearner para `504/571/597/621/696`, e regressão da cadeia `v5`/`v6` `Hard Press`/`Fling`/`Steel Beam`/`Poltergeist`/`Triple Axel`).
- `test_treino_ev_mgba.py` sobre `motor_v7.gba`: **`9/9 OK`**.
- Suítes estruturais do pacote (`12` módulos): **`117` executados (`92 OK`, `25 skipped` de ROMs intermediárias privadas), `0` falhas**.
