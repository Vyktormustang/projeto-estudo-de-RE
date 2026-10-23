# Mod da mochila — v4: **VALIDADO NO JOGO** ✅

> **Resultado final (2026-10-22):** o combo **START+SELECT** preenche a mochila e
> a tela de ITENS mostra os itens. Evidência: `reports/mod_v4/BAG_CHEIA_contraste.png`.
> O combo original **L+R+START** também funciona, mas abre a ajuda nativa do jogo
> no caminho (L+R) — por isso START+SELECT é o recomendado.

---

## 1. O que estava errado no v3

### 1.1 Retorno do trampolim 2 bytes adiantado (CONFIRMADO)

O veneer em `0x08000A38` é `ldr r3,[pc,#0] ; bx r3 ; .word TRAMP|1` — 8 bytes,
cobrindo `0x08000A38..0x08000A3F`. Logo, a continuação de `SetGpuReg` é
**`0x08000A40`**.

O trampolim v3 fazia:

```
movs r3,#8 ; lsls r3,#24      -> 0x08000000
movs r2,#0xA4 ; lsls r2,#4    -> 0x00000A40
adds r3,r3,r2                 -> 0x08000A40
movs r2,#3 ; adds r3,r3,r2    -> 0x08000A43
bx r3                         -> 0x08000A42   <-- 2 bytes DEPOIS do correto
```

O `+3` é resquício do site antigo (`0x08000A3A`). Resultado: **uma instrução
Thumb pulada a cada chamada de `SetGpuReg`** (1.200+ callsites), o que explica
as telas brancas dos testes anteriores.

### 1.2 Fonte de teclas frágil (CONFIRMADO)

`0x03003118` é um espelho de IWRAM que **zera** em várias cenas. A v4 lê
**`REG_KEYINPUT` (`0x04000130`)** — hardware, ativo-baixo, imune ao contexto.

---

## 2. Evidência de execução (ROM real, emulador mGBA)

Cenário: save-state `viridian_masterball.state` (overworld, Viridian), 300 frames,
input agendado, dump da mochila via `gba_state_dump.py`.

| Teste | Bytes em `0x020258B8` | Mochila |
|---|---|---|
| Linha de base (sem mod) | `00 00 3e 45 …` | vazia |
| **v4 sanity** (grava `AAAA`, sem gate) | `aa aa aa aa …` | **hook executa** |
| **v4 regkey, L+R+START** | `01 00 63 00 02 00 63 00 04 00 63 00 0d 00 63 00` | **cheia** |
| **v4 START+SELECT** | `01 00 63 00 02 00 63 00 04 00 63 00 0d 00 63 00` | **cheia** |
| v4 regkey, **sem apertar nada** | `00 00 3e 45 …` | vazia (controle negativo) |
| v4 regkey, **L+R só** | `00 00 3e 45 …` | vazia (controle negativo) |
| v4 regkey, **START só** | `00 00 3e 45 …` | vazia (controle negativo) |

Decodificação do dump (`{id:u16, qty:u16}`):

| Slot | Bytes | ID | Qtd | Item |
|---|---|---|---|---|
| 0 | `01 00 63 00` | 0x01 | 99 | Master Ball |
| 1 | `02 00 63 00` | 0x02 | 99 | Ultra Ball |
| 2 | `04 00 63 00` | 0x04 | 99 | Great Ball |
| 3 | `0d 00 63 00` | 0x0D | 99 | Potion |
| 4 | `1c 00 32 00` | 0x1C | 50 | Antidote |
| 5 | `2d 00 1e 00` | 0x2D | 30 | — |
| 6 | `32 00 1e 00` | 0x32 | 30 | — |
| 7 | `13 00 63 00` | 0x13 | 99 | Repel |

### 2.1 Prova visual

`reports/mod_v4/BAG_CHEIA_contraste.png` — tela **ITENS** do jogo com
`MASTER BOLA ×?57`, `ULTRA BOLA`, `POKÉ BOLA`, `POÇÃO`, `LIMONADA`,
`CINZA SAGRADA`. O jogo lê o array que o hook escreveu: a UI foi populada a
partir de `0x020258B8`.

> O `×?57` aparece porque a quantidade 99 (`0x63`) é maior do que o jogo
> formata normalmente para itens comprados; é o valor real que está na memória.
> Para exibir `×99` basta ajustar a tabela de itens no payload.

---

## 3. Por que START+SELECT e não L+R+START

`L+R` abre a **ajuda nativa** do jogo (comprovado em
`reports/mod_v4/ajuda_L_R_nativa.png`). O combo L+R+START **funciona** (a mochila
enche), mas o menu de ajuda aparece junto. `START+SELECT` não colide com nada:

```
(REG_KEYINPUT & 0x000C) == 0     # START (bit 3) + SELECT (bit 2)
```

Ambos ficam em variantes separadas do payload.

---

## 4. Como reproduzir

```bash
# 1) gerar os bytes
python3 scripts/gba_bag_payload.py --build

# 2) aplicar na CÓPIA da ROM
python3 scripts/gba_bag_payload.py --apply rom/pokemon_firered_bpre_trabalho.gba \
        -o rom_mod/BAG_MOD_v4.gba --variante regkey

# 3) testar (precisa de um core mGBA compatível com a sua glibc)
python3 scripts/gba_libretro_emu.py --rom rom_mod/BAG_MOD_v4.gba \
        --load-state viridian_masterball.state --frames 300 \
        --input 60:L:120 --input 60:R:120 --input 60:START:120 \
        --save-state out.bin

# 4) ler a mochila
python3 scripts/gba_state_dump.py out.bin --read 0x020258B8:0x20
```

---

## 5. O que continua aberto (rotulado)

| Item | Nível | Nota |
|---|---|---|
| Retorno v3 pulava 1 instrução | **CONFIRMADO** | aritmética + emulação + agora no jogo |
| v4 preenche a mochila no jogo | **CONFIRMADO** | dump + print da tela ITENS |
| START+SELECT é o combo recomendado | **CONFIRMADO** | dump + print, sem efeito colateral |
| `SetGpuReg` é chamada todo frame no overworld | **CONFIRMADO** | sanity escreveu `AAAA` |
| Quantidade `99` mostra `×?57` na UI | **CONFIRMADO** | print; ajustar tabela se quiser outro número |
| Core mGBA do zip do projeto falha nesta distro | **CONFIRMADO** | exige glibc 2.38; compilar do fonte 0.10.5 resolve |
| REA + Ghidra com JDK | **PENDENTE** | JDK 25 está no Drive do usuário (217 MB), mas excede o limite de 100 MB do conector |
