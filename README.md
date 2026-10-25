# Projeto — xadrez (pesquisa + app) e RE de GBA

> **Mapa rápido deste repositório**
> * [`app/`](app/) — **Xadrez Studio**: app local para jogar contra o Stockfish, analisar partidas e
>   explicar cada lance em português. Roda com `cd app && npm install && npm start`.
> * [`android/`](android/) — o **APK** do mesmo app para Android (offline, sem Play Store):
>   build sem Gradle em [`android/build.sh`](android/build.sh). O arquivo fica no **Google Drive**
>   (não no GitHub): <https://drive.google.com/file/d/1lt3-goUhaGpYS4-CPnBY5AXwi4YYQuis/view>
>   — versão **1.1**, com a interface refeita (referência chess.com) e o tabuleiro
>   destravado; instala por cima da 1.0.
> * [`pesquisa/chesscom/`](pesquisa/chesscom/) — pesquisa de jogabilidade do chess.com
>   ([solo e bots](pesquisa/chesscom/solo-e-bots.md) · [contra pessoas](pesquisa/chesscom/jogabilidade.md)).
> * O texto abaixo descreve o projeto anterior de **engenharia reversa de GBA** (Pokémon FireRed),
>   mantido como registro histórico; os scripts dele não fazem parte deste repositório.

---

# gba-re 🔧 Engenharia Reversa de GBA + Mod Menu (item cheat)

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
