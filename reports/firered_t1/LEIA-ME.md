# T1 — Fundação da tradução PT-BR: fonte com ã/õ + ferramentas

**Status: CONCLUÍDA (2026-10-24).** ROM de prova `60a0e662…` (base: build
final da E9 + fonte PT-BR + intro traduzida).

## O problema

O FireRed ocidental **não tem ã, õ, Ã, Õ** no charset (tem á é í ó ú â ê ô
ç à, e o til só no ñ/Ñ). Todos os 256 códigos de caractere estão ocupados.

## A solução (CONFIRMADO em jogo)

Reaproveitamos 4 códigos de glifos que o português nunca usa — nenhum
texto do jogo os usa (conferido por grep):

| código | era | virou | base do desenho | til tirado de |
|---|---|---|---|---|
| 0x09 | Ì | **Ã** | Â (0x03) | Ñ (0x14) |
| 0x10 | Œ | **Õ** | Ô (0x0F) | Ñ (0x14) |
| 0x1E | ì | **ã** | â (0x68) | ñ (0x29) |
| 0x22 | ò | **õ** | ô (0x24) | ñ (0x29) |

O pixel art é **composto programaticamente**: pega o glifo base, apaga o
circunflexo (linhas de tinta acima do primeiro vão) e carimba o til do ñ
alinhado pelo centro e pela base do acento original. Feito nas 4 fontes
latinas + charmap.txt + 5 tabelas de largura em `src/text.c`.

Script: `scripts/firered/aplicar_fonte_ptbr.py` (`--check/--write/--self-test`,
idempotente). Tradução aplicada/validada por
`scripts/firered/aplicar_traducao.py` (charset, placeholders, comprimento
de linha) com os textos versionados em `scripts/firered/traducao/`.

## Pegadinhas descobertas (não repetir)

1. **As células das fontes têm fundo índice 3** (0 = fora da caixa, 1 =
   tinta, 2 = sombra, 3 = fundo da caixa). Detectar "linha vazia" por
   `== 0` engole a letra inteira — o primeiro Ã saiu uma cópia do Ñ.
   Vazio de verdade é `∉ {1,2}`.
2. **`latin_small.png` tem células 8×16 (32 por linha)**; as outras três
   são 16×16 (16 por linha). Usar a geometria errada corrompe glifos
   vizinhos.
3. As fontes são PNG **2 bpp** — `png_indexado.py` ganhou suporte a
   profundidade 2 (leitura e escrita).

## Prova em jogo (screenshots)

| arquivo | o que mostra |
|---|---|
| `01_glifos_compostos.png` | células geradas: Â Ã Ô Õ â ã ô õ ñ Ñ (normal + small) |
| `02_controles_opcoes_com_til.png` | "Também serve para escolher **opções** nas listas" — õ |
| `03_pikachu_vao_voce_as.png` | "Novos caminhos **vão** se abrir…", "**Às** vezes, **você**…" — ã, À, ê |
| `04_oak_sao_estimacao.png` | "POKéMON **são** bichos de **estimação**" — ã, ç |
| `05_menu_novo_nome.png` | menu "NOVO NOME" e "…qual era mesmo o nome dele?" |

Intro completa traduzida (`traducao/data/text/new_game_intro.inc`): fala do
Oak, páginas do Pikachu, guia de controles, pergunta de gênero, escolha de
nomes. `verificar_rom.py` segue 100% na ROM com a fonte nova.

## Como repetir

```bash
bash scripts/firered/setup_ambiente.sh          # religa /tmp
python3 scripts/firered/aplicar_fonte_ptbr.py --pokefirered /tmp/pokefirered --write
python3 scripts/firered/aplicar_traducao.py --pokefirered /tmp/pokefirered --write
cd /tmp/pokefirered && make -j2 MODERN=1 CC1_DAEMONS=2
```

Windows: rodar dentro do WSL (`wsl bash …`), ver `docs/FIRERED.md`.
