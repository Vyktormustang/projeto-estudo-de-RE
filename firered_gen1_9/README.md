# gba-re 🔧 Engenharia Reversa de GBA + Mod Menu (item cheat)

## Motor parcial `v10` (Motor de Berries, +3 aprendizados → 15.008 = 708/729 [97,1%], 200 golpes consolidados e correção de `acc=0`, preservando 229/229 TMs SV)

Uma nova etapa determinística (`scripts/motor_v10.py`, sobre `motor_v9.gba`, saída SHA-256 `a533d1812812e2348bbe62a95a8c3817dd9d8372a89ff283f0e747c6c7ddeb09`) ocupa o último slot livre `255` de `gBattleScriptsForMoveEffects` em conjunto com `CMD_TABLE_V10` (`0x00, 0x01, 0x04, 0x05, 0x06, 0x0C, 0x88, 0xDD`) para consolidar **200 golpes** (`162` atualizações na tabela de golpes + `38` golpes `eff=0` enriquecidos nos hooks de cálculo): motor unificado de consumo de Berries `133..175` (`Stuff Cheeks`, `Teatime`, `Bug Bite / TM182`, `Pluck`, `Incinerate` e `Belch` rastreado por slot da equipe), dreno `75%` (`Draining Kiss / TM037`, `Oblivion Wing`) e `Matcha Gotcha`, `Knock Off / TM181` `1.5x` com item, multi-hit especializados (`Scale Shot / TM200`, `Population Bomb`, `Surging Strikes`, `Triple Dive`, `Double Iron Bash`), críticos garantidos (`Flower Trick`, `Wicked Blow`, `Surging Strikes`, `Storm Throw`, `Frost Breath`) e **correção do defeito Gen 3 de `acc == 0` em 11 golpes infalíveis Gen 4–9** (incluindo `TM032 Disarming Voice` e `TM053 Smart Strike`), aterramento sem colaterais de `Ingrain` (`Smack Down`, `Thousand Arrows`), limpeza de terrenos (`Ice Spinner`, `Steel Roller`), tipos/categorias adaptativos e quebra-telas (`Raging Bull`, `Freeze-Dry`, `Flying Press`, `Photon Geyser`, `Secret Sword`, `Tera Blast`, `Pollen Puff` em aliado), prioridade/resíduos/travas (`Sucker Punch`, `Thunderclap`, `Grassy Glide`, `Spectral Thief`, `Salt Cure`, `Syrup Bomb`, `Throat Chop`, `Gigaton Hammer`, `Blood Moon`, `Dragon Tail`, `Circle Throw`) e potências dinâmicas / peso (`Rage Fist`, `Last Respects`, `Bolt Beak`, `Fishious Rend`, `Collision Course`, `Electro Drift`, `Autotomize` + `Heavy Slam`/`Heat Crash`/`Low Kick`). Restaura mais **+3 aprendizados por nível** (`15.005` → **15.008** linhas em `data/learnsets_motor_v10.csv`, **708 / 729 = 97,1%**), preservando byte a byte as **229/229 TMs de Scarlet/Violet**, as 8 HMs infinitas, o `estojo_v2` e o `treino_ev`. **Continua parcial quanto ao motor geral de SV:** exatamente **4 golpes (`21` entradas = `2,9%`)** dependentes de habilidades/UI ausentes na base Gen 3 (`Simple Beam`, `Ally Switch`, `Instruct`, `Revival Blessing`), além de itens/habilidades pós-Gen 3 e Terastalização, permanecem fora de escopo e documentados. Veja a [especificação técnica, hashes, limitações e testes de `motor_v10`](docs/MOTOR_V10.md) e o [catálogo atualizado de aprendizados por nível](data/learnsets_motor_v10.csv). ROMs e saves permanecem fora do Git.

## Motor parcial `v9` (+51 golpes não-TM de subida de nível e +378 aprendizados → 15.005; 705/729 = 96,7% restaurados, preservando 229/229 TMs SV)

Uma nova etapa determinística (`scripts/motor_v9.py`, sobre `motor_v8.gba`, saída SHA-256 `2936a08fc95f40c7788b6136f209ab5cab31aec062d615f2a458f45b123e0e6f`) ocupa **12 slots livres (`243..254`, mantendo `255` livre)** de `gBattleScriptsForMoveEffects` para implementar **51 golpes não-TM** em 6 famílias mecânicas — alteração de tipos, 3º tipo efêmero e eletrificação (`Soak`, `Magic Powder`, `Reflect Type`, `Trick-or-Treat`, `Forest's Curse`, `Electrify`), trocas/divisões/inversão de atributos e impulsos compostos (`Power Trick`, `Speed Swap`, `Power/Guard Split`, `Power/Guard/Heart Swap`, `Topsy-Turvy`, `Acupressure`, `Decorate`, `Spicy Extract`, `No Retreat`, `Clangorous Soul`, `Fillet Away`, `Take Heart`, `Venom Drench`, `Toxic Thread`, `Tar Shot`, `Rototiller`, `Flower Shield`, `Magnetic Flux`, `Gear Up`), regeneração/drenagem por Atk/sacrifício/pivot com `Substitute` e purificação (`Aqua Ring`, `Strength Sap`, `Healing Wish`, `Lunar Dance`, `Shed Tail`, `Psycho Shift`, `Purify`, `Jungle Healing`, `Lunar Blessing`, `Dark Void` restrito a Darkrai `#491`), manipulação de habilidades Gen 3 (`Gastro Acid`, `Worry Seed`, `Entrainment`, `Doodle`), cópia/ordem de turno/foco crítico/dano por HP e `Natural Gift` com consumo real de Berry (`Copycat`, `After You`, `Quash`, `Laser Focus`, `Final Gambit`, `Natural Gift`) e sala de itens/prisão (`Magic Room` com supressão segura em `GetHoldEffect`, `Octolock`, `Fairy Lock`) — restaurando **+378 aprendizados por nível** (`14.627` → **15.005** registros em `data/learnsets_motor_v9.csv`, alcançando **705 / 729 = 96,7%** das entradas originalmente omitidas) e preservando byte a byte as **229/229 TMs de Scarlet/Violet**, as 8 HMs infinitas, o `estojo_v2` e o `treino_ev`. **Continua parcial quanto ao motor geral de SV:** exatamente **6 golpes (`24` entradas = `3,3%`)** dependentes de habilidades/UI inexistentes na base Gen 3 (`Simple Beam`, `Ally Switch`, `Instruct`, `Stuff Cheeks`, `Teatime`, `Revival Blessing`) seguem retidos e documentados. Veja a [especificação técnica, hashes, limitações e testes de `motor_v9`](docs/MOTOR_V9.md) e o [catálogo atualizado de aprendizados por nível](data/learnsets_motor_v9.csv). ROMs e saves permanecem fora do Git.

## Motor parcial `v8` (229/229 TMs SV habilitadas — 100% do catálogo, Clima Snow, 4 Terrenos, Salas, Gravidade, Hazards e +245 aprendizados por nível)

Uma nova etapa determinística (`scripts/motor_v8.py`, sobre `motor_v7.gba`, saída SHA-256 `32fd47c87b581952f54f05656f590c5f7da55d5cc3d186d81951508899ec54f0`) habilita as **10 TMs finais de Scarlet/Violet** (`TM052 Snowscape`, `TM091 Toxic Spikes`, `TM113 Tailwind`, `TM116 Stealth Rock`, `TM136 Electric Terrain`, `TM137 Grassy Terrain`, `TM138 Psychic Terrain`, `TM139 Misty Terrain`, `TM161 Trick Room` e `TM178 Gravity`, completando **229/229 TMs SV disponíveis = 100% do catálogo** sem nenhuma TM pendente), integra os golpes e sinergias das mesmas famílias (`Wonder Room`, `Magnet Rise`, `Aurora Veil`, `Chilly Reception`, `Shore Up`, `Sticky Web`, `Stone Axe`, `Ceaseless Edge`, `Mortal Spin`, `Rapid Spin`, `Defog`, `Tidy Up`, `Court Change`, `Blizzard`, `Weather Ball`, `Brick Break`, `Psychic Fangs`, `Floral Healing`, `Expanding Force`, `Rising Voltage`, `Terrain Pulse`, `Psyblade`, `Grassy Glide`, `Steel Roller` e `Misty Explosion`) e restaura mais **245 aprendizados por nível** em 18 golpes (elevando `learnsets_motor_v8.csv` para **14.627** registros, preservando 100% dos anteriores). **Continua parcial quanto ao motor geral de SV:** itens e habilidades modernos inexistentes na base Gen 3 (`Heavy-Duty Boots`, `Terrain Extender`, `Light Clay`, `Surge` abilities etc.) não existem, `Expanding Force` mantém cursor de alvo único em duplas, e `402` registros de nível (`57` golpes não-TM) seguem documentados. Veja a [especificação técnica, hashes, limitações e testes de `motor_v8`](docs/MOTOR_V8.md) e o [catálogo completo de 229 TMs](data/tms_motor_v8.csv). ROMs e saves permanecem fora do Git.

## Motor parcial `v7` (219/229 TMs SV, trocas automáticas e +59 aprendizados por nível)

Uma nova etapa determinística (`scripts/motor_v7.py`, sobre `motor_v6.gba`, saída SHA-256 `6321d8e2900cc44dcaefb2dedfbaf5b0952b2796ca27a4cb9d8dc0875827de09`) habilita mais **9 TMs de Scarlet/Violet** (`TM195 Burning Jealousy`, `TM199 Lash Out`, `TM207 Temper Flare`, `TM213 Coaching`, `TM220 Meteor Beam`, `TM226 Dragon Cheer`, `TM227 Alluring Voice`, `TM228 Psychic Noise` e `TM229 Upper Hand`, elevando o total para **219/229 TMs SV**), implementa as **trocas automáticas pós-golpe** (`TM048 Volt Switch`, `TM060 U-turn`, `TM196 Flip Turn` e `Parting Shot`, sem herdar estágios/Substitute de `Baton Pass`), atualiza `Stomping Tantrum` (`TM179`) após falha anterior e restaura **59 aprendizados por nível** em 5 golpes (`Heal Pulse`, `Parting Shot`, `Geomancy`, `Floral Healing` e `Life Dew`, totalizando **14.382** registros). **Continua parcial:** 10 TMs SV de campo/clima/terreno/hazards (`TM052, TM091, TM113, TM116, TM136..139, TM161, TM178`) e 647 registros de nível (75 golpes) seguem adiados e documentados. Veja a [especificação técnica, hashes, limitações e testes de `motor_v7`](docs/MOTOR_V7.md) e o [catálogo atualizado de TMs](data/tms_motor_v7.csv). ROMs e saves permanecem fora do Git.

## Auditoria (`estojo_v2` / `motor_v5`) e Motor parcial `v6`

Uma nova etapa determinística (`scripts/motor_v6.py`, sobre a saída de `scripts/motor_ampliado.py` e `scripts/estojo_expandido.py`) corrige três defeitos reais identificados na auditoria — teto `796` de nomes de golpes em batalha (`797..812`), overflow de 1 byte em `gBattleTextBuff2` (`0x020202F0`) e ícones de itens `375..603` / seta `RETURN_TO_FIELD` (`604`) — e habilita mais **6 TMs de Scarlet/Violet** (`TM043 Fling`, `TM170 Steel Beam`, `TM198 Poltergeist`, `TM201 Misty Explosion`, `TM210 Supercell Slam` e `TM212 Triple Axel`, elevando o total para **210/229 TMs SV**) mais **23 aprendizados por nível** de `Fling`. **Continua parcial:** 19 TMs SV, as trocas automáticas (`U-turn`/`Volt Switch`/`Flip Turn`) e 706 registros de nível seguem pendentes. Veja [auditoria completa, hashes, testes e pendências](docs/AUDITORIA_E_MOTOR_V6.md) e o [catálogo atualizado de TMs](data/tms_motor_v6.csv). ROMs e saves permanecem fora do Git.

## Complemento expandido de TMs e golpes — parcial

Uma cópia de 32 MiB acrescenta 14 TMs à variante anterior, reintroduz 116 aprendizados por nível e adapta cálculos e efeitos selecionados. **Continua incompleta:** há 26 TMs e 729 registros de nível omitidos, e o estojo permanece com 58 espaços. Consulte [instruções, backups, limitações e testes](docs/COMPLEMENTO_GEN9.md), as [TMs](data/tms_gen9_complemento.csv) e as [omissões restantes](docs/golpes_pendentes_complemento.csv). O aplicador é `scripts/complemento_gen9.py`; ROMs e saves continuam fora do Git.

## Variante anterior: TMs modernas e golpes

Uma nova cópia **acrescenta 189 TMs de Scarlet/Violet sem substituir as antigas ou as HMs**, amplia algumas listas por nível e corrige efeitos e poderes selecionados. As novas TMs são reutilizáveis, compartilham os 58 espaços do estojo com as antigas e podem facilitar a campanha: a loja abre desde cedo. **A atualização de batalha não é completa**; há 40 TMs indisponíveis e outros golpes disponíveis ainda têm mecânicas legadas ou incompletas. Veja [local da loja, backups, diferenças e testes](docs/ATUALIZACOES_GEN9.md), a [lista de TMs](data/tms_gen9.csv) e as [omissões por nível](docs/golpes_ainda_nao_incluidos.csv). O instalador é `scripts/atualizacoes_gen9.py`; ROMs e saves continuam fora do Git.

## Variante anterior: golpes aprendidos por nível

A variante anterior atualiza os aprendizados por nível usando Scarlet/Violet quando disponível e corrige o truncamento dos IDs acima de 511. Nela, **efeitos/animações e TMs/HMs ainda não haviam sido atualizados**. Veja [uso, backups, limitações e testes dessa variante](docs/GOLPES_POR_NIVEL.md), o [catálogo anterior](data/learnsets_gen1_9.csv) e as [omissões anteriores](docs/golpes_por_nivel_nao_incluidos.csv). O instalador é `scripts/golpes_gen9.py`.

## Correção dos Pokémon fixos comuns

Uma nova cópia da ROM com treino retira 224 objetos comuns do sistema adicional de encontros fixos; lendários, míticos, Ultra Beasts e Paradox são preservados. Eventos originais de história, incluindo Snorlax, continuam. Veja [instruções, saves, critérios e testes](docs/EVENTOS_FIXOS.md) e o [inventário dos objetos](docs/eventos_fixos_inventario.csv). A ROM e os saves continuam fora do Git.

## Treinamento EV/IV estilo RPG

A ROM de encontros tem uma variante separada com visualização de EVs e IVs no resumo da equipe e redistribuição dos EVs já conquistados. **Nenhum ponto extra é criado; IVs são apenas exibidos.** Veja os [controles, testes e cuidados com saves](docs/TREINAMENTO_EV_IV.md) e a [pesquisa](docs/PESQUISA_TREINAMENTO_EV_IV.md). O instalador é `scripts/treino_ev.py`; o código Thumb e o payload estão em `patches/treino_ev/`. A ROM e saves privados não estão no repositório.

## Trabalho atual: encontros selvagens Gen 1–9

A edição PT-BR mais recente tem uma variante com encontros selvagens adicionais.
O [guia de encontros](docs/guia_encontros.csv), as [instruções e os limites da
validação](docs/ENCONTROS_SELVAGENS.md), o gerador reproduzível
`scripts/encontros_selvagens.py` e seus testes estão neste repositório. A ROM e
os saves privados ficam fora do Git.

A verificação estrutural cobre 931 espécies não lendárias/míticas pela PokéAPI;
alguns encontros e capturas foram testados no mGBA, mas **não todas as espécies
ou rotas**. Lendários e míticos existentes não foram alterados. Ultra Beasts e
Paradoxo seguem a classificação e as ressalvas explicadas na documentação.

> O restante deste README é um registro **histórico** do projeto anterior de
> mochila/mod menu, não das implementações atuais de encontros e treino. Não use os
> endereços e conclusões antigas como se fossem desta ROM Gen 1–9.
> **Atenção:** o veneer e o retorno do BAG_MOD_v3 descritos abaixo estão errados;
> veja [os bytes e testes](docs/DIAGNOSTICO_HOOK_V3.md). O v3 não é uma solução validada.

![plataforma](https://img.shields.io/badge/plataforma-Game%20Boy%20Advance-blue)
![linguagem](https://img.shields.io/badge/scripts-Python%203.13-informational)
![id-stage](https://img.shields.io/badge/fase-6%20(Mod%20ROM)-brightgreen)
![status-mod](https://img.shields.io/badge/mod%20menu-em%20valida%C3%A7%C3%A3o-orange)

Reconstrução técnica **verificável e automatizada** do código interno de *Pokémon
FireRed* (GBA, ARM7TDMI, Thumb), com **objetivo prático**: um **mod menu** acionado
por combo de botões que entrega **Poké Balls, Potions, itens e mais direto na mochila**,
rodando em cópia da ROM no emulador — **sem jeito-feito**: toda alegação passa
por prova em frames/screenshots/dumps de RAM.

> **Legal:** este repositório **não contém a ROM** nem qualquer asset protegido.
> Tudo é código automático, documentação, hashes e screenshots geradas em sessão.
> Você precisa da sua própria cópia do jogo para reproduzir os resultados.

---

## TL;DR do que já está de pé

| Entrega | Status | Onde |
|---|---|---|
| ROM identificada (BPRE, imagem PT-BR modificada ⚠ não-confere No-Intro) | ✅ CONFIRMADO | `inventory.json` |
| Censo de funções + grafo de chamadas (BL direto, milhares de callsites) | ✅ | `functions.csv`, `callgraph/` |
| Decodificador de texto Gen 3 + charset PT-BR remapeado | ✅ | `scripts/gba_poketext.py` |
| Emulador headless **completo** (frames, input agendado, snaps PNG, save-state, mem-dumps) | ✅ | `scripts/gba_libretro_emu.py` |
| **Mapa da mochila**: array @ `0x020258B8`, 4 B/slot `{id:u16, qty:u16}` | ✅ CONFIRMADO | este README ↓ |
| Formatos/offsets no save-state (EWRAM/IWRAM) p/ inspeção offline | ✅ | `notes_mods_codigo.md` |
| **Mod v3** (hook-veneer + combo L+R+START → preencher 8 slots) | 🛠 em validação | `rom_mod/BAG_MOD_v3.gba` |
| Patch de texto demo (safe-text-slot) — primeiro modificador de ROM | ✅ | `rom_mod/PATCH_TEXTO_DEMO_PIDGEY.gba` |

---

## O Mod (o que você vai usar)

**Como dispara:** pressione **L + R + START** juntos no overworld.

**O que acontece:** o trampolim varre o espelho de teclado a cada chamada do
`SetGpuReg` (rotina tiny per-frame) e, ao ver o combo, escreve na mochila:

| Slot | Item | Qtd |
|---|---|---|
| 0 | `0x0001` Master Ball | 99 |
| 1 | `0x0002` Ultra Ball | 99 |
| 2 | `0x0004` Great Ball | 99 |
| 3 | `0x000D` Potion | 99 |
| 4 | `0x001C` Antidote | 50 |
| 5 | `0x002D` — | 30 |
| 6 | `0x0032` — | 30 |
| 7 | `0x0013` Repel | 99 |

> ℹ Lista trivialmente editável no payload (`reports/payload_bag_mod.hex` /
> tabela de pares `(id, qty)` no builder).
> ⚠ L+R sozinho abre a **ajuda nativa** do jogo — o combo completo convive com isso
> (START+SELECT é o alternativo documentado).

### Design técnico do hook (v3 — o estável)

- **Site** em `0x08000A38` — prólogo de `SetGpuReg` (8 B relocáveis, sem pc-relative):
  ```
  01 4b              ldr  r3, [pc, #4]
  18 47              bx   r3
  01 0c eb 08        .word 0x08EB0C01   ; = tramp | Thumb-bit
  ```
- **Trampolim** em `0x08EB0C00` (run 0xFF livre do `freespace_map.tsv`), 158 B:
  ```
  push {r0-r3} ; payload 130 B (combo-gate → writes) ; pop {r0-r3}
  replay do prólogo original ; constrói 0x08000A43 ; bx r3  (Thumb mantido)
  ```
- **Por que veneer e não BL:** BL Thumb só alcança **±4 MB**; o peso-árido fica
  a ~15,4 MB do site. Não existe freespace ≥256 B na janela ±4 MB
  (`reports/freespace_map.tsv` — verificado). Foi essa a causa-raiz de *todas* as
  travas anteriores (v1/v2). Encoder/decoder de BL foram reescritos e homologados
  contra **6.000 BLs reais** da ROM (decode ≡ capstone, re-encode byte-idêntico).

### Status de validação (honesto)

- Boot v3: **estável no jogo** (overworld ok; sem preenchimento sem combo ✓).
- Combo: **ainda não escreveu** no state de teste — diagnóstico aponta o
  espelho `0x03003118` ser **contexto-dependente** (zera na cena-bedroom).
  Próximo passo da lista: espelho-fonte de teclas robusto + payload sempre-escreve
  de sanidade. *(Ninguém aqui chama de 'feito' antes do print da mochila cheia.)*

---

## Diagrama-mestre (sempre-útil)

```
Cenário: overworld → SetGpuReg chamado a cada frame
────────────   original   ────────────        ─────  hokeado (v3)  ─────────────
0x08000B08  bl  #0x08000A38          |  0x08000B08  bl  #0x08000A38
...                                  |
0x08000A38  push {r4,r5,lr}          |  0x08000A38  ldr r3,[pc,#4] ; bx r3 ; .word TRAMP+1
... function body ...                |             ──────────────────────────────► 0x08EB0C00
                                     |                                              tramp:
                                     |                                                push {r0-r3}
                                     |                                                if (keys & 0x0308)==0x0308:
                                     |                                                    bag[0..7] = ITEMS   # 0x020258B8
                                     |                                                pop {r0-r3}
                                     |                                                push {r4,r5,lr}; lsls..; lsrs..; lsls..
                                     |                                                bx → 0x08000A43 (Thumb ☑)
```

---

## Estrutura do repositório

```
gba-re/
├── README.md                ← você está aqui
├── MEMORIA_CONSOLIDADA.md   ← estado-canônico entre sessões (comece por aqui)
├── inventory.json           ← manifesto da ROM (hashes, header, entropia)
├── functions.csv            ← censo de funções (endereço / confiança)
├── hypotheses.md            ← hipóteses x evidências x testes pendentes
├── progress.md              ← log de execução por ciclo (fonte primária)
├── notes_*.md|json          ← notas verificadas (estrutura, charset, mods)
├── callgraph/               ← grafo de chamadas (DOT, edges, métricas)
├── reports/                 ← relatórios gerados (hex dumps, freespace, PNGs)
├── logs/                    ← logs reproduzíveis de cada run
├── scripts/                 ← toda a automação (tabela abaixo)
├── tests/                   ← fixtures sintéticas rotuladas (NUNCA a ROM real)
├── rom/                     ← sua cópia da ROM (não commitar!)
└── rom_mod/                 ← ROMs modificadas (cópias de trabalho apenas)
```

## Scripts (automação completa, `--self-test` em todos)

| Script | O que faz |
|---|---|
| `gba_ident.py` | Triagem: hashes, header GBATEK, entropia, strings, padrões Thumb/ARM. |
| `gba_poketext.py` | Decodifica charset Gen 3 + remap PT-BR; dump de texto. |
| `gba_disasm.py` | Boot-trace ARM → Thumb, censo de BL → `functions.csv` + callsites. ⚠ `encode_bl_thumb` legado com bug de sinal (fórmula correta no §docs). |
| `gba_callgraph.py` | Gera DOT/edges/métricas do grafo de chamadas. |
| `gba_table_probe.py` | Sonda jump-tables e hubs de handlers. |
| `gba_patch_text.py` | Patch safe de slot de texto (0xFF) + relatório hexdump/SHA-256. |
| `gba_hook_code.py` | Instalador de trampolim (site bl → run 0xFF); 6 validações. |
| `gba_libretro_emu.py` | **Driver libretro headless** (mGBA cores via ctypes): frames, `--input f:BTN:hold` multi-janela, `--snap n=arq.png`, save/load-state, mem-read/dump. |
| `gba_state_dump.py` | Parser de save-state mGBA (IWRAM/EWRAM mapeados, `--read VA:len`). |
| `run_all_tests.sh` | Roda todos os `--self-test` e agrega exit-code. |

---

## Reprodução rápida

```bash
git clone <voce>/gba-re && cd gba-re
bash scripts/setup_env.sh                 # dependências mínimas (capstone)

# 1) identificar SUA cópia da ROM (não incluída por motivos legais!)
python3 scripts/gba_ident.py rom/seu_jogo.gba -o reports --update-inventory inventory.json

# 2) bateria de testes (fixtures sintéticas — serve sem ROM)
bash scripts/run_all_tests.sh

# 3) aplicar o mod (gera rom_mod/BAG_MOD_v3.gba a partir dos .hex em reports/)
python3 scripts/apply_mod_v3.py           # mounter/verificador em construção
# or manual: python3 - <<'PY' ... (ver docs/apply_mod_manual.py)

# 4) testar no emulador headless
python3 scripts/gba_libretro_emu.py --rom rom_mod/BAG_MOD_v3.gba \
    --frames 900 --input 100:L:250 --input 100:R:250 --input 100:START:250 \
    --save-state out.bin --snap 890=bag.png
python3 scripts/gba_state_dump.py out.bin --read 0x020258B8:0x10
# esperado (quando validado): 01 00 63 00 02 00 63 00 ...
```

---

## Regras do projeto (contrato de verdade)

1. ROM original intocada; **sempre** trabalhar em cópia.
2. **Nunca inventar** funções, endereços, nomes ou resultados;
   fatos ≠ inferências ≠ hipóteses — níveis: **CONFIRMADO / PROVÁVEL / HIPÓTESE / DESCONHECIDO**.
3. Nada de redistribuir a ROM nem assets (sprites/textos/áudio).
4. Todo script tem `--self-test`, logs reproduzíveis e IO validado.
5. Antes de qualquer claim "FUNCIONA": boot → alvo chamado → comportamento
   esperado → sem crash por 60 s — tudo com evidência visual/dump.

## Stack

Python 3.13 · Capstone Engine · mGBA (libretro core, ctypes headless) ·
Git · (Ghidra mapeado p/ Fase 2) · zero dependências pagas.

## Roadmap (ETA viva — atualizada por ciclo)

- [x] Fase 0/1: ambiente + identificação + inventário.
- [x] Fase 3: callgraph + sondas.
- [x] Emulador headless com input/snap/state/dump.
- [x] Mapa da mochila + formatos de slot (provado por escrita+leitura).
- [x] Fix/homologação do encoder BL (±4 MB, 6.000 amostras reais).
- [x] Veneer hábil p/ payload distante (v3).
- [ ] **Fonte robusta de teclas** (espelho contexto-independente) — *ciclo atual*.
- [ ] **Validação final**: print da mochila cheia + frame-frame stable ≥ 60 s.
- [ ] Expansão: itens infinitos selector / party-pokemon (dados party já mapeados?).
- [ ] Fase 2 Ghidra (rafinação de nomes) — *deferida*.

**ETA (ciclo 34):** diagnóstico do gating de teclas = **1 ciclo** · mod validado
com prova = **+2 ciclos**.

---

## Referências confiáveis

- GBATEK (Martin Korth) — header/mem-map/registradores.
- Capstone — desassembly homologação BL.
- mGBA + docs de scripting — estados/regiões de memória.
- No-Intro — hashes de referência (uso consultivo apenas).

<sub>Projeto pessoal de estudo de engenharia reversa. Não afiliado a Nintendo/
GAME FREAK/The Pokémon Company. **A ROM comercial NÃO faz parte deste repositório.**</sub>
