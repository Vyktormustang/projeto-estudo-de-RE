# gba-re 🔧 Engenharia Reversa de GBA + Mod Menu (item cheat)

![plataforma](https://img.shields.io/badge/plataforma-Game%20Boy%20Advance-blue)
![linguagem](https://img.shields.io/badge/scripts-Python%203.13-informational)
![id-stage](https://img.shields.io/badge/fase-6%20(Mod%20ROM)-brightgreen)
![status-mod](https://img.shields.io/badge/mod%20v4-projeto%20corrigido%20%2B%20prova%20em%20emulador-brightgreen)

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
| **Emulador próprio** (mGBA compilado aqui): frames, input, PNG, save-state, memória, CPU e breakpoints | ✅ | `tools/gba_shim/` + `scripts/gba_emu.py` |
| **Mapa da mochila**: array @ `0x020258B8`, 4 B/slot `{id:u16, qty:u16}` | ✅ CONFIRMADO | este README ↓ |
| **Montador de mods** com trava ARMv4T + simulação obrigatória antes de gravar | ✅ | `scripts/gba_modkit.py` |
| **Mod v4** (veneer correto + combo L+R+START → 8 slots) | ✅ provado em emulador (ROM de bancada) | `scripts/apply_mod.py` |
| **Prova na ROM real do usuário** (PT-BR Gen1-9): combo → mochila cheia, screenshot | ✅ CONFIRMADO | `reports/ptbr_bolsa_cheia_prova.png` |

---

## O que foi corrigido no mod (v3 → v4)

O mod v3 **não disparava**, e não era por causa das teclas. Dois defeitos de
baixo nível, achados em 2026-11-07 com o emulador novo:

**1. O site apontava o `ldr` para o lugar errado (fatal).**

```
site emitido:  01 4b | 18 47 | 01 0c eb 08        @0x08000A38
ldr r3,[pc,#4] @0x08000A38  ->  lê Align(0x08000A3C,4)+4 = 0x08000A40
literal escrito em          ->  0x08000A3C
```

O `bx r3` recebia `0x08EB0C01` decodificado como instruções
(`lsrs r1,r0,#16` / `lsrs r3,r5,#3`) — ou seja, salto para lixo **em toda
chamada de `SetGpuReg` (1238 callsites)**. O jogo não travava porque o
`0x08EB0C01` caía numa região que acabava retornando, mas o trampolim nunca
executava. Correção: `ldr r3,[pc,#0]` com o literal em `va+4` (o único encaixe
de 8 bytes que satisfaz o alinhamento ARM), montado por assembler e conferido
pela simulação.

**2. `REG_KEYINPUT` (0x04000130) é ativo-BAIXO.** O payload v3 fazia
`(k & mask) == mask`, que é verdadeiro com o combo **solto** (0x3FF & 0x308 ==
0x308) — encheria a mochila sem ninguém apertar nada. O teste correto é
`(k & mask) == 0`: nenhum bit do combo sobrou em 1.

**3. Bônus achado pelo teste de bancada:** o slot era escrito com `str` (id) +
`strh` (qtd), duas stores — um leitor podia ver `{id novo, qty antiga}`.
Agora é **uma** store de 32 bits (`(qty<<16) | id`).

**4. O trampolim de 0x08EB0C00 pode cair fora do arquivo.** Numa ROM de 16 MiB
ele está dentro (`0xEB0C00 < 0x1000000`), mas em ROMs de 8 MiB (0x08000000–
0x087FFFFF) fica além do fim. `apply_mod.py` recusa, a menos que se peça
`--esticar` (preenche com 0xFF).

---

## O Mod (o que você vai usar)

**Como dispara:** pressione **L + R + START** juntos no overworld.

**O que acontece:** a cada chamada de `SetGpuReg` (rotina pequena, chamada aos
milhares pela ROM), o trampolim lê `REG_KEYINPUT` e, se o combo estiver
pressionado, escreve na mochila:

| Slot | Item | Qtd |
|---|---|---|
| 0 | `0x0001` Master Ball | 99 |
| 1 | `0x0002` Ultra Ball | 99 |
| 2 | `0x0003` Great Ball | 99 |
| 3 | `0x0004` Poké Ball | 99 |
| 4 | `0x000D` Potion | 99 |
| 5 | `0x0013` Full Restore | 99 |
| 6 | `0x002D` Sacred Ash | 99 |
| 7 | `0x0039` Rare Candy | 99 |

> ℹ A lista é um parâmetro do montador (`gba_modkit.PADRAO`), trivialmente
> editável; `--payload tudo` injeta os 8 primeiros itens da tabela Gen 3.
> ⚠ L+R sozinho abre a **ajuda nativa** do jogo (por isso o combo tem START);
> `--combo START+SELECT` é o alternativo documentado.

### Design técnico do hook (v4)

- **Site** em `0x08000A38` — prólogo de `SetGpuReg` (8 B, sem pc-relative):
  ```
  00 4b              ldr  r3, [pc, #0]     ; lê 0x08000A3C (Align(va+4,4)+0)
  18 47              bx   r3
  01 0c eb 08        .word 0x08EB0C01      ; tramp | Thumb-bit
  ```
- **Trampolim** em `0x08EB0C00` (run 0xFF), ~150 B:
  ```
  push {r0,r1,r2,r3,r6}
  ; (kp & 0x308) != 0 ? pula : escreve 8 slots com uma store de 32 bits cada
  pop  {r0,r1,r2,r3,r6}
  push {r4,r5,lr} ; lsls r0,#24 ; lsrs r4,r0,#24 ; lsls r1,#16   ; replay do prólogo
  movs r3,#0x08 ; lsls r3,#24 ; adds r3,#0x41 ; bx r3            ; volta p/ site+8
  ```
- **Por que veneer e não BL:** BL Thumb alcança **±4 MB** e o espaço livre fica
  a ~15,4 MB (`reports/freespace_map.tsv` não tem run ≥8 B na janela). O
  montador **recusa** BL fora de alcance — é a lição que custou as travas do v1/v2.

### Status de validação (honesto)

| Prova | Resultado |
|---|---|
| Simulação do payload (unicorn ARMv4T), com e sem combo | ✅ |
| Aplicação numa **ROM de bancada própria** (`tests/fixtures/`) | ✅ |
| Emulador mGBA: combo preenche os 8 slots | ✅ |
| Emulador mGBA: sem combo / só L+R não escrevem nada | ✅ |
| Emulador mGBA: 600 frames com combo, sem travar | ✅ |
| FireRed: combo → screenshot da mochila cheia | ⏳ precisa da sua ROM |

A ROM de bancada tem **conteúdo zero de jogo**: é um laço que chama uma rotina
com o prólogo exato do `SetGpuReg` real, mochila em EWRAM no mesmo endereço e
um contador que sobe a cada chamada (prova de que o hook é executado). Ela prova
o *mecanismo*; o FireRed prova o *endereço*.

```
$ python3 tests/teste_mod_bench.py
  [PASS] A) sem combo: nenhum slot escrito
  [PASS] A) site continua executando (contador > 100k) — 152819
  [PASS] B) combo L+R+START preenche os 8 slots — 0001x99 0002x99 ... 0039x99
  [PASS] B) soltar os botões não apaga a mochila
  [PASS] C) L+R sozinho não dispara
  [PASS] D) agenda dispara no frame marcado
  [PASS] E) 600 frames com combo: ROM viva (contador avança) — 398809 -> 438747
```

---

## Diagrama-mestre

```
Cenário: overworld → SetGpuReg chamado a cada quadro
────────────   original   ────────────        ─────  mod v4  ─────────────
0x08000B08  bl  #0x08000A38          |  0x08000B08  bl  #0x08000A38
...                                  |
0x08000A38  push {r4,r5,lr}          |  0x08000A38  ldr r3,[pc,#0] ; bx r3 ; .word TRAMP|1
... function body ...                |             ──────────────────────────────► 0x08EB0C00
                                     |                                              tramp:
                                     |                                                push {r0-r3,r6}
                                     |                                                if (KEYINPUT & 0x308) == 0:
                                     |                                                    bag[0..7] = ITENS
                                     |                                                pop {r0-r3,r6}
                                     |                                                push {r4,r5,lr}; lsls..; lsrs..
                                     |                                                bx → 0x08000A40 (Thumb ☑)
```

---

## Estrutura do repositório

```
gba-re/
├── README.md                ← você está aqui
├── HANDOFF.md               ← continue daqui (estado + próximos passos)
├── MEMORIA_CONSOLIDADA.md   ← estado-canônico entre sessões
├── inventory.json           ← manifesto da ROM (hashes, header, entropia)
├── functions.csv            ← censo de funções (endereço / confiança)
├── hypotheses.md            ← hipóteses x evidências x testes pendentes
├── progress.md              ← log de execução por ciclo (fonte primária)
├── notes_*.md|json          ← notas verificadas (estrutura, charset, mods)
├── callgraph/               ← grafo de chamadas (DOT, edges, métricas)
├── reports/                 ← relatórios gerados (hex dumps, freespace, PNGs, receitas)
├── logs/                    ← logs reproduzíveis de cada run
├── scripts/                 ← automação (tabela abaixo)
├── tests/                   ← fixtures sintéticas rotuladas + prova do mod
├── tools/gba_shim/          ← shim C sobre libmgba (emulador com CPU/memória)
├── deprecated/              ← driver libretro aposentado (motivo documentado)
├── rom/                     ← sua cópia da ROM (não commitar!)
└── rom_mod/                 ← ROMs modificadas (cópias de trabalho apenas)
```

## Scripts

| Script | O que faz |
|---|---|
| `gba_ident.py` | Triagem: hashes, header GBATEK, entropia, strings, padrões Thumb/ARM. |
| `gba_poketext.py` | Decodifica charset Gen 3 + remap PT-BR; dump de texto. |
| `gba_disasm.py` | Boot-trace ARM → Thumb, censo de BL, `functions.csv`, callsites. |
| `gba_callgraph.py` | DOT/edges/métricas do grafo de chamadas. |
| `gba_table_probe.py` | Sonda jump-tables e hubs de handlers. |
| `gba_patch_text.py` | Patch seguro de slot de texto (0xFF) + relatório SHA-256. |
| `gba_hook_code.py` | Instalador genérico de trampolim (site `bl` → run 0xFF). |
| **`gba_emu.py`** | **Harness mGBA**: frames, agenda de input, PNG, save-state, leitura/escrita de qualquer região, PC/registradores, breakpoints. |
| **`gba_modkit.py`** | **Montador do mod**: keystone + trava ARMv4T + veneer + payload + simulação unicorn. |
| **`apply_mod.py`** | Aplica o mod numa cópia da ROM, com relatório de SHA-256 e desassembly. |
| `gba_state_dump.py` | Parser do save-state mGBA (IWRAM @0x19000, EWRAM @0x21000). |
| `run_all_tests.sh` | Bateria: 11 self-tests + fixture + shim + prova do mod em emulador. |

---

## Reprodução rápida

```bash
git clone <voce>/gba-re && cd gba-re
bash scripts/setup_env.sh                     # capstone + keystone + unicorn
make -C tools/gba_shim -j$(nproc)             # compila o mGBA (+ shim), ~2 min
make -C tools/gba_shim test-shim

# 1) bateria completa (não precisa da ROM comercial)
bash scripts/run_all_tests.sh

# 2) aplicar o mod na SUA cópia do jogo
python3 scripts/apply_mod.py --rom rom/seu_jogo.gba -o rom_mod/MOD_BAG.gba
# (opcional: --combo START+SELECT  --tramp 0x08EB0C00  --esticar, ver --help)

# 3) testar no emulador (aqui o combo já pode ser agendado por frame)
python3 scripts/gba_emu.py --rom rom_mod/MOD_BAG.gba --load-state emu/overworld.bin \
    --input 10:L:90 --input 10:R:90 --input 10:START:90 \
    --read 0x020258B8:32 --snap 300=mochila.png
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

Python 3.13 · Capstone · Keystone · Unicorn · mGBA 0.10.5 compilado localmente
(libmgba + shim C) · Git · zero dependências pagas, zero binário de terceiro
versionado.

## Roadmap (ETA viva — atualizada por ciclo)

- [x] Fase 0/1: ambiente + identificação + inventário.
- [x] Fase 3: callgraph + sondas.
- [x] Emulador próprio com memória e CPU (substitui o core libretro morto).
- [x] Mapa da mochila + formatos de slot (provado por escrita+leitura).
- [x] Fix/homologação do encoder BL (±4 MB) + montador com trava ARMv4T.
- [x] Veneer correto (o `ldr pc-relativo` do v3 apontava 4 B adiante).
- [x] Payload com keypad ativo-baixo e escrita atômica de 32 bits.
- [x] **Prova em emulador**: combo → 8 slots, sem combo → nada, estável.
- [ ] **FireRed**: screenshot da mochila cheia (precisa da ROM do usuário).
- [ ] Menu in-game (UI de escolha de itens) — fase posterior, escopo maior.
- [ ] Fase 2 Ghidra (refinação de nomes) — *deferida*.

**ETA:** validação no FireRed = **1 sessão com a ROM** (o resto está pronto).

---

## Referências confiáveis

- GBATEK (Martin Korth) — header/mem-map/registradores, keypad ativo-baixo.
- Capstone / Keystone / Unicorn — disassembly, montagem e simulação ARMv4T.
- mGBA 0.10.5 (código-fonte) — layout do save-state (0x61000) e do keypad.
- No-Intro — hashes de referência (uso consultivo apenas).

<sub>Projeto pessoal de estudo de engenharia reversa. Não afiliado a Nintendo/
GAME FREAK/The Pokémon Company. **A ROM comercial NÃO faz parte deste repositório.**</sub>
