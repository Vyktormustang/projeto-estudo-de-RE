# E9 — entrega da ROM

**Arquivo:** `pokefirered_gen1-9_E7.gba`
**md5:** `821f35a7805fa2738576a33b6682c1b2` · 16 777 216 B
**Google Drive (público):** https://drive.google.com/file/d/1g5CCRzxsPp5QtI-aNL5DjabzPzxDURRF/view

A ROM não é versionada aqui (`*.gba` está no `.gitignore`, regra do projeto).
Para regerar: `bash scripts/firered/setup_ambiente.sh`.

## O que está provado nesta build

| item | prova |
|---|---|
| título e boot do FireRed | `setup_ambiente.sh` compila e `prova_golpes_e4.py --preparar-estado` sai do título sozinho |
| sair de casa e ir até a Rota 1 | `prova_golpes_e4.py --preparar-estado` (mapa 4:1 → 4:0 → 3:0 → 3:19) |
| entrar na casa pela porta | `reports/firered_e9/01_entrou_na_casa_pela_porta.png` (mapa 3:0 → 4:0 em (6,7)) |
| sair da casa pela porta | `reports/firered_e9/02_saiu_da_casa_para_pallet.png` (4:0 → 3:0) |
| selvagem Gen 9 na Rota 1 | `prova_encontros_e7.py --prova` → `[16, 19, 915]` |
| captura do Gen 9 | `prova_encontros_e7.py --prova --capturar` → time `[700, 915]` |
| ficha da dex da espécie nova | `No915 LECHONK`, "Hog POKéMON", HT 1'08", WT 22.5 lbs. |
| Pokédex até #1025 | `verificar_rom.py` → 4 ordens + 9 páginas de habitat com 1025 |
| batalha com golpes novos (E4) | `prova_golpes_e4.py --rodadas 2` → 2/2 ok |

## Como jogar (Windows)

1. Baixe o `.gba` no link acima.
2. Abra no **mGBA** (`https://mgba.io/downloads.html`) — apenas jogue; nada de patcher.
3. Sem ROM base: este arquivo já é a ROM completa.

> Nota: PNGs regerados em 2026-10-24 após o conserto do conversor de cores do
> `nav.py` (RGB565 com vermelho deslocado 1 bit — detalhe no LEIA-ME da E7).
