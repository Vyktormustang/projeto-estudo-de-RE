# Auditoria Técnica (`estojo_v2` / `motor_v5`) e Motor Parcial `v6`

Este documento registra exclusivamente **fatos verificados por desmontagem, reconstrução determinística e execução em mGBA 0.10.5 headless com saves/estados sintéticos**, separados de limitações conhecidas e pendências. Nenhuma ROM comercial, save pessoal ou save state foi incluído no Git.

---

## 1. Cadeia de Reconstrução e Hashes SHA-256

Todas as transformações leem a ROM de entrada em modo somente leitura, validam o SHA-256 antes de aplicar alterações e gravam um **arquivo novo** de 32 MiB (`33.554.432` bytes):

| Etapa | Script gerador | Entrada esperada (SHA-256) | Saída determinística (SHA-256) |
|---|---|---|---|
| Base expandida 32 MiB (`parcial`) | — (base privada fora do Git) | — | `6155b6a5fe62528b7b67836d3a47752b1cb3b1a71c1f2b59bfa7a68af0100d67` |
| Estojo paginável (`estojo_v2`) | `scripts/estojo_expandido.py` | `6155b6a5fe62528b7b67836d3a47752b1cb3b1a71c1f2b59bfa7a68af0100d67` | `93dc62e86cfa3dc70c8057fa4ea25031761d48fc5ce4f7615a5a66d4fc280907` |
| Motor ampliado (`motor_v5`) | `scripts/motor_ampliado.py` | `93dc62e86cfa3dc70c8057fa4ea25031761d48fc5ce4f7615a5a66d4fc280907` | `cf1de0e237feefcfda6789bc81c726ed13d91d512b85c54b9f857520a7a4fc87` |
| **Motor parcial (`motor_v6`)** | `scripts/motor_v6.py` | `cf1de0e237feefcfda6789bc81c726ed13d91d512b85c54b9f857520a7a4fc87` | `75d66d3c36e560df29f6c613666b91a6c81ce24663b6a3f76f4dd2ea7d747ce6` |

Insumos versionados do `motor_v6` (derivados de `PokeAPI/pokeapi@6b8db7f3cb31cfaa37cb74e5c3edff124bcba5ce` por `scripts/gerar_motor_v6.py` e compilados para ARM7TDMI Thumb-1):

| Arquivo | Tamanho | SHA-256 |
|---|---:|---|
| `patches/motor_v6/payload.bin` | `588` B | `7d0fbcc8d1344d5ced74bbb4775a17e70ec42b562bfbf95cf50a8face4d44736` |
| `data/tms_motor_v6.csv` | 229 linhas | `aece81a00878e6da6e3a4287ee6448ef6885c828a3393a9e2b732a980c493ab0` |
| `data/compatibilidade_tms_motor_v6.bin` | `29.754` B | `649d97ea5e3d45e52ac19c3545a4ec448bfa4b46c21f17c3b41eac8a460c873e` |
| `data/learnsets_motor_v6.csv` | 14.323 linhas | `9e7fd32c36a9a5e0c81e5eea639d904f534db9b1667308efcdca4078b21871d0` |
| `data/fling_itens_motor_v6.bin` | `1.210` B | `50b4f285764945c3d0798fc383150b629b7c82176d769e22cb642b0ad7df57ab` |

---

## 2. Resultados da Auditoria Técnica (`estojo_v2` e `motor_v5`)

### 2.1 Defeitos reais confirmados e corrigidos em `motor_v6`

1. **Nomes de golpes `797..807+` suprimidos em mensagens de batalha (`BufferStringBattle`)**
   - **Endereço e causa**: `0x08055B36`, `0x08056350` e `0x08056370` comparavam `moveId > 796` (`movs r2, #0xC7; lsls r2, r2, #2` = `796`) antes de indexar `gMoveNames` (`0x09003000`). Como `complemento_gen9` adicionou os golpes `797..806` e `motor_v5` adicionou `807` (`HARD PRESS`), usar qualquer um desses golpes em batalha produzia texto vazio (`"A usou\n!"`).
   - **Distinção crítica verificada**: `0x0810AEE6` e `0x0810AF6C` usam `797` (`0x031D` / `0x29FD`) como **sentinela de fim da tabela `gEggMoves`**, e **não** são tetos de `gMoveNames`. Alterá-los corromperia a leitura de Egg Moves; por isso permanecem intocados.
   - **Correção em `motor_v6`**: os três sítios de batalha foram atualizados para `movs r2, #0xCB; lsls r2, r2, #2` (`812 = MOVE_COUNT - 1`). Validado em batalha real no mGBA 0.10.5 para `797` (`TRAILBLAZE`) e `807..812`.

2. **Overflow de 1 byte em EWRAM ao formatar nomes de golpes de 15–16 letras (`gBattleTextBuff2` -> `gBattleTextBuff3`)**
   - **Endereço e causa**: `gBattleTextBuff2` ocupa `16` bytes (`0x020202F0..0x020202FF`), imediatamente antes de `gBattleTextBuff3` (`0x02020300`). O gancho em `0x08E030BA` copiava até `15` bytes (`movs r2, #0x0F`) antes de gravar `'!'` (`0xAB`) e `0xFF`, escrevendo `17` bytes e sobrescrevendo `gBattleTextBuff3[0]` com `0xFF` em golpes como `566` (`PARABOLIC CHARGE`, 16 caracteres).
   - **Correção em `motor_v6`**: `0x08E030BA` ajustado para `movs r2, #0x0E` (`14` caracteres + `'!'` + `0xFF` = `16` bytes exatos). Confirmado no mGBA com sentinela `0xAA` em `0x02020300` preservado após `566` e `810`.

3. **Ícones de itens `375..603` e colisão com `ITEM_LIST_END` (`RETURN_TO_FIELD` = `375`)**
   - **Endereço e causa**: `AddItemIconSprite` (`0x080CB1BE`) e `AddCustomItemIconSprite` (`0x080CB2D8`) faziam clamp `itemId > 375 -> 0` (ícone `?`), enquanto a entrada `375` da `sItemIconTable` original (`0x0862FC74`) era `gItemIcon_ReturnToFieldArrow` (seta de voltar em Bag/PC/Shop/Berry Pouch). Assim, `TM001` (`375`) exibia uma seta de retorno e `TM002..TM229` (`376..603`) exibiam `?`.
   - **Correção em `motor_v6`**:
     - Nova tabela `ICON_TABLE_V6` (`605 × 8 = 4.840` bytes) gravada em `0x090BC000`: entradas `0..374` idênticas à base; entradas `375..603` apontam para o gráfico de disco TM (`0x085F8080`) e para a paleta TM correspondente ao tipo do golpe (incluindo `TYPE_MYSTERY = 9` de `TM224 Curse` mapeado à paleta Ghost `0x085F8384`); entrada `604` recebe `gItemIcon_ReturnToFieldArrow`.
     - Ponteiros da tabela atualizados em `0x080CB288` e `0x080CB3A4`; clamps em `0x080CB1BE` e `0x080CB2D8` elevados para `> 604` (`97 23 9b 00 9c 42 52 d8`); e os 4 chamadores da seta de retorno (`0x080C7C0A/12` Bag, `0x080CBA1A/1C` ItemPC, `0x0813BA86/8E` Shop, `0x080766A6/AA` BerryPouch) atualizados de `375` para `604`.

4. **Correções em duas suítes de teste existentes**
   - `tests/test_motor_ampliado_mgba.py`: restaurados a constante `CAN = 0x080F8460` (`CanMonLearnTMHM`) e o helper `call(...)` ausentes no arquivo do pacote.
   - `tests/test_treino_ev_mgba.py`: corrigido 1 nibble divergente no hash esperado da base `parcial_32mb` (`...d3a47752b...`) e incluídos os hashes de `estojo_v2`, `motor_v5` e `motor_v6` em `EXPECTED_ROMS`.

### 2.2 Subsistemas auditados e confirmados íntegros

- **Fronteiras de IDs de item (`289..338`, `339..346`, `347..374`, `375..603`)**: a lacuna `347..374` (itens chave/fósseis/parcel) é explicitamente rejeitada nos classificadores de animação (`0x081149E4`, `0x08115344`), nos ganchos de consumo (`0x08E19000`) e no mapeamento de estojo (`estojo.c`), sem risco de tratar itens chave como TMs.
- **Consumo único de TMs vs. HMs infinitas**: os três caminhos de ensino (`PartyMenu` slot vazio `0x080FCCB8`, substituição de 4º golpe `0x080FCD7C` e retorno de `MoveTutor/Summary` `0x08115B78`) consomem 1 unidade apenas de TMs (`289..338` e `375..603`) após aprendizado efetivo, preservam todas as 8 HMs (`339..346`) e não consomem em incompatibilidade, golpe já conhecido ou cancelamento.
- **Quest Log (`0x0812C310`, ganchos `0x0812C3BC` e `0x0812C3EC`)**: distingue `"HM"` (`339..346`) e `"TM"` (`289..338`, `375..603`) com ou sem substituição de golpe.
- **Pokedude / Teachy TV / Link (`0x080C7014`, `0x080C7068`, `0x08E00019`)**: a extensão `T9X1` em `SaveBlock1 + 0x34D8` (`400` bytes) não é zerada pelo `ClearBag` temporário do Pokedude/Link e não invade `BerryPouch` (`+0x054C`).
- **Persistência em Flash (128 KiB) e Poké Mart**: compra, venda nas páginas `0..2`, cancelamento e recarga de save preservam quantidades até `999` e migram saves anteriores sem perda.
- **Preservação de encontros selvagens, eventos fixos especiais/lendários e treino EV/IV**: `0x08F80000..0x08FA0000` (`treino_ev` + `eventos_fixos`) e `0x08E00000..0x08E03000` (`estojo_v2`) permanecem idênticos byte a byte entre `motor_v5` e `motor_v6`.

---

## 3. Avanço Incremental no `motor_v6`: +6 TMs SV (`204 -> 210/229`) e +23 Learnsets

### 3.1 Infraestrutura adicionada
- **Tabela de comandos de BattleScript realocada (`CMD_TABLE_V6 = 0x090BD400`)**: copia os 248 opcodes existentes (`0x082097F0`), redireciona o opcode `5` (`damagecalc`) para `entry_damage_v6` (`0x090BE001`) e registra `0xF8..0xFF` como `callasm` (`0x090BE009`), atualizando as 5 referências da tabela (`0x0538D4`, `0x0549B4`, `0x054BE8`, `0x054C1C`, `0x071DDC`).
- **Payload Thumb-1 puro (`0x090BE000`, `588` B)**: compilado com `-mcpu=arm7tdmi -mthumb -Os`, verificado sem instruções ARMv5+/Thumb-2 (`blx reg`, `uxth`, `sxth`, `rev`, `cbz`). Preserva integralmente os cálculos anteriores de `damagecalc` (incluindo `807 Hard Press`) e acrescenta o suporte a `Fling`, `Poltergeist`, `Steel Beam` e `Supercell Slam`.
- **Reserva de learnsets (`0x08F50000..0x08F60000`)**: reconstruída preservando todas as `14.300` linhas anteriores e adicionando as `23` entradas SV de nível de `Fling` (`move 374`, ex.: `Cubone Lv. 20`), sem tocar `0x08F80000` (`treino_ev`).

### 3.2 TMs habilitadas nesta etapa (`210/229` disponíveis)

| TM | Item ID | Move ID | Golpe | Tipo / Cat. / BP / Acc / PP | Mecanismo implementado e testado no mGBA | Limitação conhecida no motor Gen 3 |
|---|---:|---:|---|---|---|---|
| `TM043` | `417` | `374` | `Fling` | Dark / Fís. / var. / 100 / 10 | Consulta `FLING_TABLE_V6` (`0x090BD800`, 605 itens), bloqueia vazio/Poké Balls/Key Items/fósseis/TMs/HMs, aplica BP tabelado + efeito secundário (`PSN`, `TOX`, `BRN`, `PAR`, `Flinch`) e consome o item em `BattlePokemon` e na estrutura criptografada da equipe (`gPlayerParty`/`gEnemyParty`). Inclui +23 aprendizados por nível. | Bagas/ervas arremessadas causam 10 BP e são consumidas, mas não ativam o efeito de consumo da baga no alvo. |
| `TM170` | `544` | `808` | `Steel Beam` | Steel / Esp. / 140 / 95 / 5 | Dano especial de 140 BP + perda própria de `ceil(HP máx / 2)` tanto em acerto quanto em erro de precisão, com autonocaute se `HP <= ceil(HP máx / 2)`. | Habilidade `Magic Guard` não existe para isentar o custo. |
| `TM198` | `572` | `809` | `Poltergeist` | Ghost / Fís. / 110 / 90 / 5 | Verifica `target.item != 0` via `callasm`; falha sem causar dano se o alvo não segura item; causa 110 BP físico Ghost sem consumir o item do alvo. | Não exibe o nome do item do alvo num diálogo separado antes do impacto. |
| `TM201` | `575` | `810` | `Misty Explosion` | Fairy / Esp. / 100 / 100 / 5 | Usa o fluxo nativo de `Explosion` (`eff 7`, `target = 0x20`) com tipo Fairy (`18`) e categoria Especial, desmaiando o usuário e respeitando `Damp`/imunidades. | Sem bônus de `1,5x` de `Misty Terrain` (terrenos não existem no motor). |
| `TM210` | `584` | `811` | `Supercell Slam` | Electric / Fís. / 100 / 95 / 15 | 100 BP sem recuo ao acertar; se errar, bater em `Protect` ou atingir alvo imune (`Ground`), exibe mensagem de queda e aplica `floor(HP máx / 2)` ao usuário (limpando `MOVE_RESULT_NO_EFFECT` antes do `datahpupdate`). | Interações modernas pós-Gen 3 não portadas seguem o motor FireRed. |
| `TM212` | `586` | `812` | `Triple Axel` | Ice / Fís. / 20→40→60 / 90 / 10 | Script nativo relocado de `Triple Kick` (`eff 104`) com checagem de precisão por golpe e incremento `+20` em `0x0202181A` (`20`, `40`, `60` BP). | Sem `Loaded Dice` nem alteração Gen 8+ de `Skill Link`. |

---

## 4. Organização das Pendências Restantes por Mecanismo

Continuam **explicitamente indisponíveis** `19` das `229` TMs de Scarlet/Violet (fora da loja e com `internal_move = 0` em `NEW_MOVE_TABLE` para impedir ensino de golpe sem mecânica), além das trocas automáticas pós-ataque e de `706` entradas de nível distribuídas em `80` golpes ainda não portados:

| Grupo técnico | TMs / Golpes pendentes | Bloqueador real no motor FireRed |
|---|---|---|
| **1. Terrenos de batalha (4 TMs)** | `TM136 Electric Terrain` (`510`), `TM137 Grassy Terrain` (`511`), `TM138 Psychic Terrain` (`512`), `TM139 Misty Terrain` (`513`) | O motor Gen 3 não possui estado global de terreno, contadores de 5/8 turnos nem ganchos de fim de turno/imunidade de prioridade/multiplicadores de tipo ligados a terreno. |
| **2. Condições globais de campo, clima Snow e armadilhas de entrada (6 TMs)** | `TM052 Snowscape` (`426`), `TM091 Toxic Spikes` (`465`), `TM113 Tailwind` (`487`), `TM116 Stealth Rock` (`490`), `TM161 Trick Room` (`535`), `TM178 Gravity` (`552`) | Exigem variáveis persistentes de campo/lado em EWRAM, ganchos no cálculo de ordem de turno (`Trick Room`/`Tailwind`), no envio de Pokémon (`Stealth Rock`/`Toxic Spikes`), na precisão/imunidade (`Gravity`) e na Defesa de tipo Ice (`Snowscape`). |
| **3. Histórico de variação de atributos ou falha no turno (4 TMs)** | `TM195 Burning Jealousy` (`569`), `TM199 Lash Out` (`573`), `TM207 Temper Flare` (`581`), `TM227 Alluring Voice` (`601`) | Exigem bits por combatente rastreando aumento/redução de estágio no turno corrente e falha do movimento anterior. |
| **4. Carregamento com buff, bloqueio de cura, prioridade condicional e suporte de aliado (5 TMs)** | `TM213 Coaching` (`587`), `TM220 Meteor Beam` (`594`), `TM226 Dragon Cheer` (`600`), `TM228 Psychic Noise` (`602`), `TM229 Upper Hand` (`603`) | Exigem estado de `Heal Block` moderno (`Psychic Noise`), detecção da ação prioritária escolhida pelo alvo (`Upper Hand`), carregamento em dois turnos com `+1 Sp. Atk` (`Meteor Beam`) e buffs direcionados ao parceiro em duplas (`Coaching`/`Dragon Cheer`). |
| **5. Troca automática pós-acerto (pivô)** | `U-turn` (`TM060`), `Volt Switch` (`TM048`), `Flip Turn` (`TM196`) | Os três já estão disponíveis como golpes de dano, mas ainda não abrem a seleção forçada de substituto após acertar. |
| **6. Aprendizados por nível omitidos** | `706` registros em `80` golpes (`729` anteriores menos as `23` linhas de `Fling` habilitadas em `motor_v6`) | Dependem dos mesmos mecanismos acima ou de efeitos exclusivos de espécies Gen 4–9 ainda não implementados. |

---

## 5. Como Reconstruir e Executar os Testes

### 5.1 Reconstrução determinística (sempre em novos arquivos)
```bash
python3 firered_gen1_9/scripts/estojo_expandido.py \
  --rom /caminho/ptbr_gen1-9_complemento_parcial_32mb.gba \
  --saida /caminho/estojo_v2.gba

python3 firered_gen1_9/scripts/motor_ampliado.py \
  --rom /caminho/estojo_v2.gba \
  --saida /caminho/motor_v5.gba

python3 firered_gen1_9/scripts/motor_v6.py \
  --rom /caminho/motor_v5.gba \
  --saida /caminho/motor_v6.gba
```

### 5.2 Testes estruturais (sem ROM)
```bash
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_*.py'
```

### 5.3 Testes completos de integração em mGBA 0.10.5 (somente saves sintéticos)
```bash
# Motor parcial v6 (19 testes: dados + build + batalha real + ícones + 3 páginas do estojo + Flash + nível)
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V6_ROM=/caminho/motor_v6.gba \
MOTOR_V6_BASE=/caminho/motor_v5.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_motor_v6*.py' -v

# Regressão motor v5 (18 testes), estojo v2 (18 testes) e treino EV/IV em motor_v6 (9 testes)
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_TEST_ROM=/caminho/motor_v5.gba \
MOTOR_TEST_BASE=/caminho/estojo_v2.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_motor_ampliado*.py' -v

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
ESTOJO_TEST_ROM=/caminho/estojo_v2.gba \
ESTOJO_TEST_BASE=/caminho/ptbr_gen1-9_complemento_parcial_32mb.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_estojo_expandido*.py' -v

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
TREINO_TEST_ROM=/caminho/motor_v6.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_treino_ev_mgba.py' -v
```
