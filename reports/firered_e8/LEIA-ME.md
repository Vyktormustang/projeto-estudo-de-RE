# E8 — Regressão completa na ROM final (2026-10-24)

**ROM testada:** `pokefirered_modern.gba`, md5 `7fcfdf53cc541f8dd571436ba8887759`
(build `make -j2 MODERN=1 CC1_DAEMONS=2`, inclui E1-E7 completas: 1025 espécies,
golpes, habilidades, sprites, encontros, habitats, treinadores e evoluções).

## Matriz de regressão

| etapa | prova | resultado |
|---|---|---|
| E2 dados | `verificar_rom.py`: 639 espécies + dex + learnsets + evoluções byte a byte | **ok** (639/639/639/215) |
| E3 Fada | `verificar_rom.py`: 12 regras de tipo, 42 espécies com Fada, categorias físico/especial | **ok** |
| E4 golpes | `prova_golpes_e4.py`: 24 golpes modernos sorteados em 6 rodadas de batalha real | **ok (6/6)** |
| E5 habilidades | `prova_habilidades_e5.py --prova`: Earth Eater imune a Bulldoze + controle + prova negativa | **ok (3/3)** |
| E6 sprites | `verificar_rom.py`: sprite/costas/paleta/shiny/ícone/pegada das 639 | **ok** |
| E7 encontros | `prova_encontros_e7.py --prova --capturar`: Lechonk #915 selvagem na Rota 1, capturado, dex | **APROVADO** |
| E7 treinadores | `verificar_rom.py`: 481 slots com espécie nova = marcas no fonte | **ok** |
| E7 evoluções | `verificar_rom.py` (233 novas c/ evolução, zero troca/item 0) + prova em jogo (Magnezone/Lucario/Gigalith) | **ok** |
| boot | `prova_golpes_e4.py --preparar-estado` refaz jogo novo (intro → Oak → Rota 1) nesta ROM | **ok** |

Self-tests das ferramentas (sem ROM): `gen_species_data` (13 mapeamentos de
evolução + conflitos), `verificar_rom` (E7 11/11), `savestate`, `nav` — todos ok.

## Pegadinha encontrada (e consertada) pela regressão

`prova_habilidades_e5.py` não achava mais a tabela da Rota 1: o scanner exigia
espécies `1..386`, mas desde a E7 a rota tem Gen 4-9 (915, 819). Teto corrigido
para 1025 no próprio script. **Lição:** prova que embute premissa do conteúdo
antigo quebra quando o conteúdo evolui — limites devem vir de `NUM_SPECIES`.

## Como repetir

```
bash scripts/firered/setup_ambiente.sh        # religa /tmp (clone, toolchain, core)
python3 scripts/firered/verificar_rom.py --pokefirered /tmp/pokefirered
python3 scripts/firered/prova_golpes_e4.py
python3 scripts/firered/prova_habilidades_e5.py --prova
python3 scripts/firered/prova_encontros_e7.py --prova --capturar
```
(Windows: WSL — ver bloco PowerShell/WSL em `docs/FIRERED.md`.)
