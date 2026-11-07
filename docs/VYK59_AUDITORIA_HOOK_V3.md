# VYK-59 — auditoria Capstone do site e do trampolim (BAG_MOD v3)

**Data:** 07/11/2026 · **Issue:** [VYK-59](https://linear.app/vyktormustang/issue/VYK-59/16-auditar-com-capstone-os-bytes-do-site-e-do-trampolim-v4)
**Script:** `scripts/auditoria_vyk59_v3.py` (com `--self-test`)
**Evidência:** `reports/vyk59_auditoria_v3.json`

## Resumo

| | v3 como entregue | v3 corrigido |
|---|---|---|
| Itens conferidos | **2/8 OK** | **8/8 OK** |
| Veredito | **REPROVA** | confere |

A auditoria desmontou os bytes reais do v3 (`reports/site_v3.hex`,
`reports/tramp_v3.hex`, `reports/payload_bag_mod.hex`, dentro de
`gba-re_project (1).zip`) e aplicou as correções do plano sobre **os mesmos
bytes**. Nada foi montado "de cabeça": tudo é decodificado com Capstone e
simulado registrador por registrador.

## Resultado item a item

| # | Item do checklist | v3 | Correção necessária |
|---|---|---|---|
| 1 | `ldr` do site lê o literal pretendido `0x08000A3C` | ❌ `01 4b` → `ldr r3,[pc,#4]` lê **`0x08000A40`** | primeiro halfword `00 4b` (imediato `#0`) |
| 2 | literal do site aponta para o trampolim | ✅ `0x08EB0C01` | — |
| 3 | retorno após o replay é `0x08000A41` | ❌ `bx` simulado vai para **`0x08000A43`** | ver "retorno é aritmético" |
| 4 | escrita em `0x020258B8` | ❌ escreve em **`0x022058B8`** — **fora da EWRAM** (`0x02000000–0x0203FFFF`) | `0x022058B8` → `0x020258B8` |
| 5 | `ldrh` lê `REG_KEYINPUT` (`0x04000130`) | ❌ lê **`0x03003118`** (IWRAM, não é registrador de teclas) | `movs r2,#3 / lsls #24` → `movs r2,#4 / lsls #24` |
| 6 | máscara do combo presente | ✅ `0x308` (`L+R+START` = `0x200|0x100|0x8`) | — |
| 7 | teste do keypad compatível com registro **ativo em zero** | ❌ `ands r1,r2` + `cmp r1,r2` exige bits em **1** = botões **soltos** | `ands` + `bne fim` |
| 8 | prólogo original reexecutado no trampolim | ✅ `30 b5 00 06 04 0e 09 04` presente | — |

## Dois defeitos que **não** estavam no plano

1. **`ldrh` no endereço errado.** O payload v3 constrói `0x03003118` — IWRAM, não
   `REG_KEYINPUT`. Mesmo com máscara e teste corretos, ele leria lixo e o combo
   nunca dispararia de forma confiável.
2. **Polaridade invertida.** `REG_KEYINPUT` é **ativo em zero**: botão apertado =
   bit 0. A comparação `(k & mask) == mask` só é verdadeira com os bits em 1, ou
   seja, com os botões **soltos**. É o oposto do pretendido.

Sobre o item 6: o documento histórico fala em `0xFF00 → 0x3FF`, mas os bytes
gravados já usam `0x308`, que é a máscara correta de `L+R+START`. **O plano
estava desatualizado nesse ponto** — não há o que corrigir na máscara.

## O retorno é aritmético, não literal

O plano manda mudar `A43` → `A41` como se fosse um `.word`. Não é. O trampolim
v3 termina com:

```text
08eb0c8e  08 23     movs  r3, #8
08eb0c90  1b 06     lsls  r3, r3, #0x18     ; 0x08000000
08eb0c92  a4 22     movs  r2, #0xa4
08eb0c94  12 01     lsls  r2, r2, #4        ; 0x0A40
08eb0c96  9b 18     adds  r3, r3, r2        ; 0x08000A40
08eb0c98  03 22     movs  r2, #3            ; ← o defeito está AQUI
08eb0c9a  9b 18     adds  r3, r3, r2        ; 0x08000A43
08eb0c9c  18 47     bx    r3
```

Para voltar em `0x08000A41` o imediato tem de ser `#1`: **`03 22` → `01 22`**.
Procurar um `.word 0x08000A43` não acha nada — foi exatamente o falso negativo
que a primeira versão desta auditoria produziu.

## O site do v3 não existe nas nossas bases

`0x08000A38` na V42 e na base PT-BR Gen 1–9 contém `46 46 33 48 33 4a 98 43`
(`mov r6,r8`…), não o prólogo `30 b5 00 06 04 0e 09 04`. Confirma a nota do
projeto **Hook v3 (BAG_MOD)**: *não transferir offsets desta ROM para a Gen 1–9*.

| ROM | bytes em `0x08000A38` |
|---|---|
| `FireRed_Gen1-9_motor_v42.gba` | `46 46 33 48 33 4a 98 43` |
| `pokefirered_gen1-9_ptbr.gba` | `46 46 33 48 33 4a 98 43` |
| `ptbr_gen1-9_selvagens_treino_tms_gen9.gba` | `46 46 33 48 33 4a 98 43` |

## Reprodução

```sh
python3 scripts/auditoria_vyk59_v3.py --self-test
python3 scripts/auditoria_vyk59_v3.py --zip gba-re_project_historico.zip \
    --json-out reports/vyk59_auditoria_v3.json
```

O ZIP histórico é material de auditoria: é o mesmo arquivo que acompanha a
issue (5,0 MiB, sem ROM). Nenhuma ROM e nenhum save entram no Git.

## Armadilhas registradas

- Três falsos negativos próprios, todos no simulador do auditor: `add rXd, rXs`
  de 2 operandos, `adds` de 3 operandos e `ldr`/`bx` **aritméticos** em vez de
  literais. O `--self-test` agora cobre os três.
- `ldr rX,[pc,#imm]` no Thumb: o imediato **já está em bytes** e conta a partir
  de `Align(site+4,4)`. Multiplicar por 4 dá o endereço errado.
