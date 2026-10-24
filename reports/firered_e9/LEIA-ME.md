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


---

## Build FINAL (2026-10-24) — E9 fechada

**Download (link público):**
<https://drive.google.com/file/d/1P3F4sLYEik4mBwidRFkJmSERjM8A2HyD/view>
(download direto: <https://drive.google.com/uc?id=1P3F4sLYEik4mBwidRFkJmSERjM8A2HyD&export=download>)

| campo | valor |
|---|---|
| arquivo | `pokefirered_gen1-9.gba` (16 777 216 B) |
| md5 | `7fcfdf53cc541f8dd571436ba8887759` |
| sha256 | `b2874f30abc9805a4de90f97e058908a292baa5fbd10816e183abec1d29ec2d8` |
| base | `pret/pokefirered` (FireRed de verdade), build `MODERN=1` |
| conteúdo | E1-E7 completas: 1025 espécies, golpes, habilidades, sprites, encontros selvagens, habitats da dex, 481 slots de treinador e evoluções modernas |
| regressão | E8 completa nesta build (ver `reports/firered_e8/LEIA-ME.md`) |

Cópia local no workspace: `rom/pokefirered_gen1-9.gba` (a pasta `rom/` não é
versionada — regra do projeto). A build intermediária da E7-2a ficou no Drive
renomeada `pokefirered_gen1-9_E7_DESATUALIZADA.gba` para não ser confundida.

Como conferir no Windows (PowerShell):
```powershell
Get-FileHash .\pokefirered_gen1-9.gba -Algorithm SHA256
Get-FileHash .\pokefirered_gen1-9.gba -Algorithm MD5
```
