# E3 — tipo Fada + split físico/especial

**Data:** 2026-10-23
**ROM:** `pokefirered_modern.gba`, sha256
`748dbec766f7ffc137ac36049691d22cbcc5c54fa5fc78d0df2fb8c1d4ccd1b6`
(16 777 216 B)
**Base:** `pret/pokefirered` @ `ce6406d` + E1 (`apply_e1_port.py`) + E2
(`gen_species_data.py --write`) + E3 (`apply_e3_port.py`)
**Build:** `make -j2 MODERN=1 CC1_DAEMONS=2` → EXIT 0, 0 `error:`
**ROM de prova (só para os testes em batalha):** `7017ffba…`, gerada por
`prova_batalha_e3.py --aplicar` e **removida** depois (a ROM de entrega é a de
cima).

---

## O que esta etapa entrega

1. **Tipo Fada** como 19º tipo (`TYPE_FAIRY = 18`, `NUMBER_OF_MON_TYPES = 19`):
   tabela de efetividade com as 12 regras que a Gen 6 mudou, nome nas telas,
   mensagem de batalha, ícone na lista de golpes, paleta e placa "FAIRY" no
   seletor de tipo.
2. **Split físico/especial por golpe** (o FireRed usa o *tipo* para decidir se o
   dano usa Attack/Defense ou SpAttack/SpDefense): cada um dos 355 golpes passa a
   ter categoria própria em `gMoveCategories`, gerada do `moves_info.h` do RHH.

## O que está CONFIRMADO

| # | Afirmação | Evidência |
|---|---|---|
| 1 | Compila e linka | `make` EXIT 0, 0 erros; sha256 novo |
| 2 | 12 regras de Fada **no ROM** | `verificar_rom.py`: percorre `gTypeEffectiveness` (124 entradas) no binário |
| 3 | 41 espécies com Fada **no ROM** | `verificar_rom.py` conta byte a byte em `gSpeciesInfo` |
| 4 | Categorias por golpe **no ROM** | `verificar_rom.py`: POUND/BODY_SLAM físicos, FLAMETHROWER/THUNDERBOLT especiais, GROWL/SWORDS_DANCE status, 80–200 físicos |
| 5 | Ficha do Pokémon mostra `TYPE/FAIRY` | `01_ficha_sylveon_type_fairy.png` (Sylveon #700) |
| 6 | Menu de golpes mostra `TYPE/FAIRY` | `02_menu_golpes_fairy.png` |
| 7 | **Fada × Dragão = 2×** em batalha real | `03_super_efetivo_fada_vs_dragao.png` — "It's super effective!" |
| 8 | **Dragão × Fada = 0×** em batalha real | `04_dragao_nao_afeta_fada.png` — "It doesn't affect SYLVEON" (Outrage do Dratini) |
| 9 | **Split físico/especial funciona em batalha** | tabela abaixo — dois golpes de 40 BP, mesmo tipo, mesmo alvo, dano diferente |
| 10 | Batalha de Kanto sem regressão | `05_batalha_kanto_rattata.png` — Rattata selvagem na Rota 1, batalha normal |
| 11 | Boota e joga até o quarto em Pallet | ROM final: título → novo jogo → quarto |

### Prova do split (a medida que importa)

Os dois golpes de prova têm **40 de poder**, **tipo Fada** e o mesmo alvo
(Dratini selvagem nível 50, Dragão puro → 2× nos dois). Sylveon nível 30:
Attack 53, Defense 53, SpAttack 80, SpDefense 92; Dratini: Defense 60,
SpDefense 68. Os dois golpes foram usados em batalhas separadas, a partir do
mesmo savestate, e o HP do inimigo foi lido no `gBattleMons` do savestate.

| golpe | categoria | stat usada no dano | HP antes → depois | dano medido | faixa prevista (Gen 3) |
|---|---|---|---|---|---|
| PLAY ROUGH | física | Atk 53 vs Def 60 | 108 → 79 | **29** | 28–33 |
| MOONBLAST | especial | SpA 80 vs SpD 68 | 108 → 70 | **38** | 38–45 |

Se o split **não** existisse, os dois golpes seriam do tipo Fada — e no FireRed
vanilla o tipo decide a stat, então os dois dariam **o mesmo dano**. Dão 29 e 38.

## O que muda no jogo (e o que não muda)

- **Efetividade**: Fada→Lutador/Dragão/Sombrio 2×; Fada→Veneno/Aço/Fogo 0,5×;
  Lutador/Inseto/Sombrio→Fada 0,5×; Dragão→Fada 0×; Veneno/Aço→Fada 2×.
- **Dano**: 55 dos 218 golpes com dano trocam de stat em relação à Gen 3
  (Fire/Ice/Thunder Punch viram físicos; Vine Whip, Bite, Gust viram especiais —
  é a mudança oficial da Gen 4). Os outros 163 continuam iguais; 137 são status.
- **Copas/Concursos**: `NUM_DISC_COLORS` cresceu 32 B de EWRAM para caber a cor
  da Fada no estojo de TM (288 → 320 u16).
- **Nada mais do FireRed foi tocado**: mapa, scripts, treinadores, música e
  textos continuam os originais.

## Como reproduzir

```bash
# 1) port (idempotente)
python3 scripts/firered/apply_e3_port.py --self-test
python3 scripts/firered/apply_e3_port.py --pokefirered /tmp/pokefirered
python3 scripts/firered/apply_e3_port.py --check          # falha se alguém editar à mão

# 2) build
cd /tmp/pokefirered && make -j2 MODERN=1 CC1_DAEMONS=2

# 3) prova no binário
python3 scripts/firered/verificar_rom.py --pokefirered /tmp/pokefirered

# 4) prova em batalha (ROM de prova + mGBA)
python3 scripts/firered/prova_batalha_e3.py --self-test
python3 scripts/firered/prova_batalha_e3.py --pokefirered /tmp/pokefirered --aplicar
cd /tmp/pokefirered && make -j2 MODERN=1 CC1_DAEMONS=2 && cd -

export MGBA_CORE=/tmp/mgba-0.10.5/build/mgba_libretro.so
python3 scripts/firered/nav.py --rom /tmp/pokefirered/pokefirered_modern.gba \
  --map /tmp/pokefirered/pokefirered_modern.map --outdir /tmp/e3 \
  --frames 1000 --pulsos "40:A:5,100:A:5,160:A:5,220:A:5"     # pula a intro de batalha

# 5) desfazer a prova e voltar à ROM de entrega
python3 scripts/firered/prova_batalha_e3.py --pokefirered /tmp/pokefirered --reverter
cd /tmp/pokefirered && make -j2 MODERN=1 CC1_DAEMONS=2 && cd -
```

## Erros de método desta etapa (para não repetir)

1. **`sizeof` de array `extern` sem tamanho** não compila (`incomplete type`) →
   o tamanho tem de estar num `#define` (`TYPE_EFFECT_TABLE_SIZE`) usado no
   `extern` **e** na definição.
2. **Verificar contagem por regex perdia a linha sentinela** `TYPE_ENDTABLE` →
   contar linhas que começam com `TYPE_`.
3. **`revert` com `copy2` preserva o mtime antigo** → o `make` não recompilava e
   a ROM continuava com a prova aplicada (hash não voltava) → `touch` no arquivo
   restaurado.
4. **`MAP_ROUTE1` aparece duas vezes** no `wild_encounters.json` (FireRed e
   LeafGreen) → pegar o **último** alterava só a LeafGreen. Filtrar por
   `base_label` com "FireRed".
5. **Slot 0 de grama = 20 % de chance** → o teste dependia de sorte. Para prova,
   trocar os **12 slots**.
6. **Pokémon criado com OT de outro treinador desobedece** acima do nível
   permitido pelas insígnias ("SYLVEON ignored orders!") → usar o OT e o nome do
   jogador, lidos do SaveBlock2.
7. **`gPlayerPartyCount` do SaveBlock1 fica 0 até salvar o jogo** → o menu START
   escondia o item POKéMON. Ler a global `gPlayerPartyCount` (EWRAM).
8. **`FLAG_SYS_POKEMON_GET` (0x828)** também é necessária para o item aparecer.
9. **O nível 50 no Dratini** (em vez de 30) é o que permite os dois golpes
   caberem no mesmo alvo com o Sylveon nível 30 — com 30 o Dratini caía no
   primeiro golpe e não dava para comparar.
10. **A porta não abre andando para baixo**: `MB_SOUTH_ARROW_WARP` só dispara com
    a direção certa; e o `OAK` da Rota 1 bloqueia a saída de Pallet até o script
    rodar (é do jogo original, não é regressão).
