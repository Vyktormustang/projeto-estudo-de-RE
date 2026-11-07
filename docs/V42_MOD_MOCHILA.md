# Mod da mochila na base FireRed Gen1–9 **V42** (07/11/2026)

> Escopo: aplicar o cheat já homologado (combo → 8 itens na mochila) na ROM de
> 32 MiB do projeto Gen1–9, que é uma base **diferente** das anteriores.
> Nada aqui foi validado em hardware — só no emulador próprio (`tools/gba_shim`).

## Resultado

| Item | Valor |
|---|---|
| ROM base | `FireRed_Gen1-9_motor_v42.gba`, 33 554 432 B, SHA-256 `6997366b…bbd99a` (confere com `SHA256SUMS.txt` do Drive) |
| ROM modificada | `rom_mod/MOD_BAG_V42.gba`, SHA-256 `c1a861eb…` |
| Site do hook | **`0x0808EB88`** (203 callsites), prólogo `30 b5 81 b0 6b 46 04 04` |
| Veneer | `00 4b 18 47 01 0c eb 08` → trampolim `0x08EB0C00` |
| Trampolim | 154 B em run 0xFF |
| Mochila | pocket `0x0202B79C` → `{slots, cap}`; slots em `0x0202D3AC`, cap **42**; Poké Balls em `0x0202B7A4`, cap 30 |
| Combo | **A + B + DOWN** |
| Prova | `reports/ptbr_v42_bolsa_cheia.png` (tela ITENS com MASTER BALL…RARE CANDY) e `reports/mod_v42_evidencia.json` |

Slots após o combo (uma store de 32 bits por slot, `(qtd<<16)|id`):

```
01 00 63 00  02 00 63 00  03 00 63 00  04 00 63 00
0d 00 63 00  13 00 63 00  2d 00 63 00  39 00 63 00     (1,2,3,4,13,19,45,57 ×99)
```

## Por que o combo mudou

A v42 do motor usa **L/R e SELECT** para telas nativas de AJUDA/dica. Controle
negativo executado na ROM **limpa**, a partir do mesmo estado:

| Sequência | START depois abre o menu? |
|---|---|
| nenhuma | ✅ (`md5 263f4133`) |
| L+R, L+R+START, L+R+SELECT, R+SELECT, L+SELECT | ❌ abre a AJUDA (`md5 0242e9ab`) |
| SELECT, SELECT+UP, A+SELECT | ❌ abre dica (`md5 551435fb`) |
| START+SELECT | ❌ (`md5 3069755f`) |
| **A+B+DOWN** | ✅ idêntico à ROM limpa |

Ou seja: o cheat **funcionava** com `START+SELECT`, mas o combo em si quebrava a
UI seguinte. `A+B+DOWN` não colide com nada do motor.

## Armadilhas encontradas (não repetir)

1. **`0x08AEC910` está OCUPADO** nesta ROM (o motor cresceu): gravar o trampolim
   ali corrompe dados e o jogo congela no primeiro START. Usar `0x08EB0C00`.
2. **`0x080BDB58` congela** ao ser desviado — mesmo com um payload inofensivo
   que só incrementa um contador. Site escolhido por teste, não por heurística.
3. Os endereços da base de 16 MiB **não valem**: site, pocket e espaço livre
   mudaram. O pocket andou **+0x84** (`0x0202B718` → `0x0202B79C`).
4. A caixa de texto do quarto inicial **bloqueia o menu** — precisa sair do
   quarto. Isso não tem relação com o mod (acontece na ROM limpa também).

## Reprodução

```bash
# 1) ROM do Drive (pasta "Motor v42 — 2026-11-07"), confira o SHA-256
sha256sum -c SHA256SUMS.txt

# 2) estado de overworld (o repositório não distribui save/state)
#    boot → GAME FREAK → tutorial → nome do rival → quarto → sair do quarto

# 3) gerar a ROM modificada
python3 - <<'PY'
import sys; sys.path.insert(0,'scripts'); import gba_modkit as mk
rom=open('google_drive/FireRed_Gen1-9_motor_v42.gba','rb').read()
SITE, TRAMP, POCKET = 0x0808EB88, 0x08EB0C00, 0x0202B79C
r=mk.receita(site_va=SITE, prologo=rom[SITE-0x08000000:SITE-0x08000000+8],
             va_tramp=TRAMP, payload_asm=mk.payload_mochila(mk.PADRAO,"A+B+DOWN",ptr_bolsa=POCKET))
img=bytearray(rom); img[SITE-0x08000000:SITE-0x08000000+8]=r['site']
img[TRAMP-0x08000000:TRAMP-0x08000000+len(r['tramp'])]=r['tramp']
open('rom_mod/MOD_BAG_V42.gba','wb').write(img)
PY

# 4) no jogo: segurar A+B+DOWN ~0,1 s no overworld, soltar, START → BOLSA
```

## Limites (o que NÃO está provado)

- Persistência do save após SAVE/Continuar no **hardware**.
- Comportamento em mapas com scripts de NPC disputando o mesmo frame.
- Campanha completa: o estado usado é sintético (tutorial automatizado), como o
  próprio projeto Gen1–9 declara nos relatórios das ilhas.
