# notes_estrutura.md — Mapa verificado de estruturas da ROM (FireRed BR)

> Somente o que tem evidência reproduzível. Offsets = posição no arquivo;
> endereço GBA = offset + 0x08000000. Atualizado por ciclo.

## Identidade / integridade (Ciclo 2)

| Item | Valor | Confiança | Evidência |
|---|---|---|---|
| Família | Pokémon FireRed (BPRE, USA) | CONFIRMADO | cabeçalho GBATEK completo válido |
| Variante | imagem modificada | CONFIRMADO | CRC32 7a6ef5f5 ≠ No-Intro Rev0/Rev1 |
| Idioma da variante | **Português (PT-BR), fã-tradução** | CONFIRMADO | texto decodificado: você×719, Você×577, ção×174, está×345, Está×53, Olá×40, Parabéns×10 + diálogos completos legíveis |
| Resíduo EN | strings EN restantes em algumas regiões (" the "×64, "You"×26, "Thank"×17) | PROVÁVEL: blocos traduzidos parcialmente | marcadores EN (poketext_markers.json) |

## Charset de texto (Gen 3 + remap PT-BR) — CONFIRMADO

- Núcleo padrão Gen 3 inalterado (A–Z, a–z, 0–9, espaço, !?.-): validado por
  âncoras de conteúdo conhecido (BULBASAUR, IVYSAUR, VENUSAUR, CHARMANDER,
  POTION, POUND) com slots contíguos na tabela de espécies.
- A tradução **remapeou acentos** (descoberta empírica, arquivo `notes_charset_remap_br.json`):
  `0x17=á  0x19=ç  0x1B=é  0x1C=ê  0x68=â  0xF4=ã  0xF5=õ`
  (0xF4/0xF5 eram slots livres; 0x17/0x19/0x1B/0x1C sobrescrevem o estoque).
- Mantidos do estoque com aparência de corretos: `0x06=É`, `0x01=À`.
- Ainda não mapeados (aparecem como [NN]): demais acentos raros (ó, í, ú, â/ã/õ
  maiúsculos etc.) — trabalho do próximo ciclo de refino.

## Tabelas de dados verificadas

| Estrutura | Offset arquivo | Endereço GBA | Confiança | Evidência |
|---|---|---|---|---|
| Nomes de espécies, slot espécie #0 ("???") | 0x245EE0 | 0x08245EE0 | CONFIRMADO | espaçamento 11 B validado |
| gSpeciesNames[#1] = BULBASAUR | 0x245EEB | 0x08245EEB | CONFIRMADO | âncora + IVYSAUR @+11, VENUSAUR @+22, CHARMANDER @+33 |
| Descrições Pokédex (PT-BR) — ex.: Charmander | 0x18E1A0 | 0x0818E1A0 | CONFIRMADO | "É super fácil treiná-lo", texto legível |
| Região de diálogos/script text (NPCs, ajuda) | ~0x172000–0x1B3200 | — | PROVÁVEL (limites exatos TBD) | contextos legíveis: 0x172315…0x1B2FC9 |
| Hits "POTION" (item name/tabela/textos) | 0x1A5F5F, 0x1A6150, 0x1B32D0 | — | DESCONHECIDO qual é a tabela-mestra | 5 ocorrências; triangular depois |
| Hits "POUND" (golpe) | 0x24FCF9, 0x3E83DE | — | HIPÓTESE: tabela de golpes ≈0x24FC00 | 2 ocorrências |

## Sistemas de código (Ciclo 2)

| Item | Detalhe | Confiança |
|---|---|---|
| Save | lib **FLASH1M_V103** (128 KiB) | CONFIRMADO (string @0x6FBF14 + No-Intro) |
| Wireless | lib **RFU_V1024** (adaptador wireless) | CONFIRMADO (string @0x6FC05C) |
| Boot | entry `B 0x08000204`; init SDK em ARM (modos/pilhas) | CONFIRMADO (decode manual) |
| Corpo de código | 0x000000–0x15FFFF: candidatos densos, Thumb BL 17–41/KiB, **0 ARM BL** | HIPÓTESE forte (heurística); ilhas: 0x1E0000, 0x4B0000 (109 ARM BL) |

## Arquitetura de boot (Ciclo 4) — CONFIRMADO por desassembly rastreado

| Item | Valor | Evidência |
|---|---|---|
| Entry ARM | 0x08000000 → `B 0x08000204` | boot_trace (reports/*_disasm_boot.json) |
| SP IRQ | **0x03007FA0** | literal @0x0800023C |
| SP USR/SYS | **0x03007E40** | literal @0x08000238 |
| Célula de handler IRQ [0x03007FFC] | ← **0x08000248** | `str r0,[r1]` no boot; literal @0x08000240 |
| IRQ dispatcher (ARM) | **0x08000248** | desassembly: dispatcher IE/IF/IME clássico (REG_IE/IF @0x04000200, REG_IME @0x04000208, scan de flags) |
| Entry principal (Thumb) | **0x080003A4** | `ldr r1,=0x080003A5; mov lr,pc; bx r1` — 13 instr. ARM antes da transição |
| Funções por BL direto | **7.565 alvos únicos** (44.758 callsites); 78% prólogo canônico | censo capstone, dual-check manual 100% sem divergência |
| Mais chamadas (fortes candidatas a rotinas de runtime) | 0x0803FBE8 ×1363 · 0x08000A38 ×1238 · 0x0804037C ×728 · 0x080722CC ×651 | censo; identificar por assinatura no próx. ciclo |
| Modo do binário | Thumb dominante: CONFIRMADO; ARM = boot + ISR | H-0003 (384 páginas: ARM-hit em prólogo = 0,0 em todas) |

**functions.csv:** 7.566 linhas (7.565 auto por BL direto + 1 manual: IRQ handler).

## Funções nomeadas com evidência (Ciclo 5) — ver `names_registry.json`

| Endereço | Nome | Confiança | Assinatura |
|---|---|---|---|
| 0x08000A38 ×1238 | `SetGpuReg_like` | PROVÁVEL | buffer 0x03000000↔regs 0x04000000..(96×u16), VCOUNT/DISPSTAT |
| 0x080009C0 | `gpu_commit_idx_like` | PROVÁVEL | commit do buffer; merge especial DISPSTAT (mask 0xFFE7) |
| 0x0803FBE8 ×1363 | `DISPATCHER_34c_tbl0803FC08` | CONFIRMADO (estrutura) | 34 casos (r1−0x37), tabela @0x0803FC08 |
| 0x0804037C ×728 | `DISPATCHER_34c_tbl0804039C` | CONFIRMADO (estrutura) | gêmeo; alvos 0x08040424/3C/46… |
| 0x08074480 ×462 | `DISPATCHER_5c_tbl0807449C` | CONFIRMADO (estrutura) | 5 casos; dados 0x083AE01C |
| 0x0807741C ×372 | `alloc_slot28_arr03005090_like` | PROVÁVEL | pool 0x28 B em 0x03005090 (H-0010) |
| 0x08077508 ×432 | `free_slot28_arr03005090_like` | PROVÁVEL | par do alocador |
| 0x080751C4 | `byte_flag0_arr02023BD6_like` | PROVÁVEL | flag &1 de array de bytes |
| 0x080722CC ×651 | `gate_wrapper_081DD0F4_like` | HIPÓTESE | gates 0x02031DD8/0x0203ADFA |
| 0x081DD0F4 | `lookup_2tabs_084A32CC_329C_like` | HIPÓTESE | lookup hierárquico (código em 0x1Dxxxx!) |
| 0x080003A4 | `ENTRY_THUMB_main` | **CONFIRMADO** | transição do boot (não chamada por BL) |

**Observação estrutural (atualizada, ciclo 6):** o censo ampliado cobriu
0x0–0xEC0000 (toda a ROM útil). Resultado: **5.978 funções com prólogo limpo**
(contra 51.268 alvos de BL) e top-8 inalterado → quase todo código real está
em 0x0–0x160000; além há dados com ilhas Thumb (0x1Dxxxx, 0x1Exxxx).
functions.csv agora contém **apenas os 5.981 nós com prova de prólogo**
(auto+registry+manuais; baixa prova fica no TSV do censo).

## Callgraph — primeiro mapa arquitetural (Ciclo 6)

Construído por `scripts/gba_callgraph.py` (nós = functions.csv; arestas =
`reports/*_callsites.tsv`; **só BL direto** — handlers de tabela/IRQ ainda
fora do grafo, limitação registrada em `callgraph/callgraph_metrics.json`):

- **5.981 nós; 21.314 arestas únicas** (36.578 ponderadas).
- **BFS de ENTRY_THUMB_main: 2.609 nós alcançáveis (43,6%)** só por BL
  direto — o resto inclui handlers indiretos reais (NÃO é prova de código morto).
- **5.266 SCCs; o maior tem 585 nós** (≈10% de todo o código) — H-0012:
  núcleo da máquina de estados de jogo.
- Top indegree reproduz o top-8 do censo → validação cruzada do pipeline ✓.
- **Novos hubs por OUTDEGREE (candidatos a gerentes de subsistema):**

  | Endereço | Callees distintos |
  |---|---:|
  | 0x0808CFF8 | **117** |
  | 0x0806A40C | 79 |
  | 0x081186C8 | 76 |
  | 0x08046ED0 | 72 |
  | 0x081508EC | 69 |

- Artefatos: `callgraph/callgraph.dot` (Graphviz), `callgraph/edges.tsv`,
  `callgraph/callgraph_metrics.json`.

## FASE 4 DESBLOQUEADA (Ciclos 17–20)

- Driver v0.3→completo: N frames, PNG/snapshots por frame, agenda de input
  (frame:botão:hold), save/load state (528 KiB), mem-read (rg0=SAVE).
- Ciclo 17: boot 600 frames OK; tela GAME FREAK; demo de texto boot idêntico.
- Ciclo 18: **hook de código validado dinamicamente** (paleta→branco).
- Ciclo 19: START pula intro → título **POKéMON FIRE RED BR** na tela.
- Ciclo 20: A navegou o menu até tela **CONTROLE** (tutorial PT-BR);
  save-states marcos em `emu/state_*.bin`.



`gba_libretro_emu.py` roda o mGBA 0.10.5 (core libretro de .deb Debian,
sem root) dentro do sandbox: 600 frames confirmados (240×160 @59,728 fps,
RGB565), PNG de framebuffer, leitura de EWRAM. Boot original e da ROM
PATCHADA (texto PIDGEY!) byte-idênticos na intro (reports/emu_*.png).
Driver com self-test 5/5; pegadinhas documentadas: av_info só após
load_game; log interface variádic não suportada via ctypes.

## Sonda dos handlers dos dispatchers (Ciclos 6–7)

As tabelas 0x0803FC08 e 0x0804039C têm 34 ponteiros válidos cada; handlers são
**Thumb stubs sem prólogo** (por isso ausentes do functions.csv) —
CONFIRMADO-estrutural (H-0013); a forma exata do salto com bit 0 ainda é
HIPÓTESE sendo verificada.

**Mapa dos 34 casos (Ciclo 7, `gba_table_probe.py --n 34`):**

| Caso | tbl3FC08 (GET, H-0014 PROVÁVEL) | tbl4039C (SET espelho, H-0015 PROVÁVEL) |
|---:|---|---|
| 0 | ldr [r4+0x50] (u32, status) | u16 LE de [r2] (escrita) |
| 1 | ldrb [r4+0x54] (u8, nível) | strb [r3+0x54] ← [r2] |
| 2–3 | ldrh [r4+0x56/0x58] (hp/maxHP) | u16 LE de [r2] |
| 4–8 | `bl 0x08044674` com sel r1=1..5 (índice) | u16 LE de [r2] |
| 9 | ldrb [r4+0x55] (u8) | strb [r3+0x55] ← [r2] |
| 10–28 (GET) / 11–28 (SET) | via helper comum 0x0803FD44 / 0x080404D0 (subdados) | idem; caso[10] SET = **no-op** (`pop;pop;bx`) |
| 29–33 | ldrh [r4+0x5A..0x62] (5 stats) | u16 LE de [r2] |

Leitura conjunta: pares GET/SET de um objeto com layout
status/nível/hp/maxHP/stats (+19 subcampos de caixa) → acesso a dados de
unidade ("mon"). Helpers 0x0803FD44/0x080404D0 são continuações (não funções)
→ **fora do registry** de propósito; helper 0x08044674 virou
`acc_sel1-5_read_tbl3FC08_like` (PROVÁVEL, registry 12 entradas).

**Ciclo 9 — corpo do loop principal (ENTRY_THUMB_main, H-0017 CONFIRMADO):**
init (waitstate `[0x04000204]←0x4014`, paleta 0x05000000, ~12 inits) →
`memzero_ewram_like` (0x02000000, 0x1C000 B) → loop por frame:
`per_frame_update_like` 0x080005E8 → **checagem de soft-reset
A+B+START+SELECT** (`[0x030030F0+0x28]` &1 e bits 0xE==0xE → trio
0x081E09D4/0x081E08F8/0x080008D8) → **`game_loop_body_like` 0x080582E0**
(retorna flag: 1 = caminho especial dequear?) e repete. Registry → 21.
SET de caixa fechado (0x080404D0 confirmado; encrypt 0x0803F8F8 = HIPÓTESE).
**Detalhe do corpo (Ciclo 10):** 0x080582E0 = **predicado**
(`combo_pred_cb08057ded_like`, 35 insns — correção: nome anterior superestimado;
historico preservado). Sequência por frame: tick(0x080004B0) → combo(0x08058274)
→ `frame_counter59_rollover_like` (rollover 0x3B) → **`dispatch16/8`-case**
`dispatch8_idx03000FC4like` @0x0807194C (jump table @0x0807196C, `mov pc,r0` —
mesmo idioma dos 34c) → `vblank_flag_sync_like` @0x08000890 →
`b 0x0800041A` (loop fechado).

**Ciclo 11 — dispatch8 + célula de callback:** casos `[0,2,3,4]=no-op`;
`[1]=avança state + bl 0x080722A0`; `[5-7]=bl 0x08071DD4 (guarda) →
0x08071C9C` → dispatch8 = **máquina de estados por-frame** (task manager).
Rastro de [0x03000E84] (5 usos): struct-base **0x03000E80**, sentinelas
0x80/0x81; `cb_task_state_machine_like` 0x080579C4 (HIPÓTESE) usa os
ponteiros Thumb 0x08057DA5/0x08057DED = **callbacks de estado**. Registry →
25. Elo do hub indireto 0x0808CFF8 ainda pendente (helpers pendentes ou mGBA).

**Ciclo 12 — task manager + pool com callback:** predicado-guarda
`pred_flag03007304zero_like`; `pool_find_bycb_arr03005090like` 0x08077650
(busca slot **pela função de callback** no pool H-0010 — o pool é de objetos
orientados a callback!); `cb_install_thumbptr_like` 0x080578FC; callback-alvo
0x08057DEC = `statecb_step_r4{0x11,0x1A}_like` (retorna próximo estado);
`lookup_sanitized_idx081dd0f4like` 0x080722A0. Registry → 31. Arquitetura
CONFIRMADA-estrutural: **sistema de processos/tarefas por-frame com
callbacks registrados e estados numéricos**.

**Ciclo 8 — helpers CONFIRMADOS:** 0x0803FD44 = `get_boxmondata_84case_like`
(4 substructs sel 0..3 via `get_substruct_0-3_like` 0x0803F940; recompute via
`checksum_boxsubstructs_like` 0x0803E3E8 vs [r8+0x1C]; flags bad-egg
[r8+0x13]|=5 / sub+7|=0x40; XOR `decrypt_xor_boxsubdata_like` 0x0803F91C;
jump table **84 casos** @0x0803FDD8); 0x080404D0 = espelho SET (HIPÓTESE,
corpo pendente). Registry → 17 entradas. (CSV reflete nomes na próxima
regeneração do censo — registry é a fonte autoritativa.)

**Hub 0x0808CFF8 (outdegree 117) — REVISÃO (Ciclo 13):** o "117 callees" é
artefato de atribuição — nenhum site/bl/branch/pointer/ADR referencia o nó;
no gap de **7.956 B** até o próximo nó do CSV (0x0808EF0C) há uma floresta
de funções sem prólogo cujos sites foram somados ao hub. 252 ponteiros
**intra-chunk** (literal pools/switchs internos) e 0 ponteiros externos → o
chunk 0x0808CFF8–0x0808EF0B só entra via **registro dinâmico** (blx por
ponteiro de slot). Análise estática exaurida → identificação = mGBA
(PC-trace/watchpoint na instalação do ponteiro; H-0016 BLOQUEADO-p/-estática).
Correção arquivística: tratar "hubs de outdegree" próximos (0x0806A40C etc.)
com a mesma suspeita até verificação de gap.

## Primeiro modificador de ROM: texto (Ciclo 6)

`scripts/gba_patch_text.py` (self-test 7/7): patch de slot de texto
terminado em 0xFF, com pré-condição `--expect`, `--slot-size` p/ registros
de passo fixo (aborta se padding não for 00/FF), recusa in-place, relatório
hexdump+SHA-256+perfil, log em `logs/gba_patch_text_runs.jsonl`.
**Demo real:** espécie #16 em 0x245F90 (slot passo 11) `PIDGEY → PIDGEY!` em
`rom_mod/PATCH_TEXTO_DEMO_PIDGEY.gba` — 2 bytes alterados, vizinho intacto,
ROM original intacta.

## Implicação operacional importante

A tradução expân­diu/repontou dados: **offsets das ferramentas da comunidade
(pokefirered decomp) NÃO se aplicam diretamente a esta ROM**. Toda referência de
offset deve ser medida nesta ROM (como foi feito acima), nunca copiada de
memorando externo. (Hipótese H-0007 — PROVÁVEL, coerente com hashes modificados.)
