# T3 — Tradução PT-BR do sistema de batalha (src/battle_message.c)

Data: 2026-10-24 · Build da prova: `pokefirered_modern.gba` md5 `59aebb7111a058f7931b8448a41ea499`
(o md5 identifica a build desta rodada; ele muda a cada rebuild e não é critério de regressão)

## O que foi feito (CONFIRMADO)

- Novo dicionário `scripts/firered/traducao_batalha_ptbr.py` com **481 entradas**
  (de 529 strings do arquivo; as ~48 restantes são JP/Unused/pokeblock/vazias,
  que o plano manda não traduzir).
- `scripts/firered/aplicar_traducao.py` agora aplica **múltiplos dicionários**
  (strings.c + battle_message.c) e aceita variáveis `static const u8`.
- Aplicação: `481/481 OK, 0 problemas` (placeholders idênticos, charmap válido).
- ROM recompilada (`make MODERN=1`) e `verificar_rom.py --amostras 0`: ok.

## Decisões de estilo

- Nomes de **golpes, itens e habilidades em inglês** (pedido do usuário);
  todo o resto da batalha em PT-BR.
- Prefixos concatenados pelo engine: "Selvagem ", "Inimigo ", "Aliado"
  (ordem fixa prefixo+nome: "Selvagem PIDGEY desmaiou!").
- Frases compostas por buffers mantêm a ordem inglesa:
  "drasticamente " + "aumentou!" / "caiu!".
- Menu de ações: LUTAR / BOLSA / POKéMON / FUGIR; Safári: BOLA / ISCA / PEDRA / FUGIR.
- Efetividade: "É super efetivo!", "Não é muito efetivo…", "Um golpe crítico!".

## Provas em jogo (screenshots, mGBA headless)

| Arquivo | O que prova |
| --- | --- |
| `01_pidgey_selvagem_apareceu.png` | "Um PIDGEY selvagem apareceu!" |
| `02_menu_lutar_bolsa_pokemon_fugir.png` | "O que SYLVEON vai fazer?" + LUTAR/BOLSA/POKéMON/FUGIR |
| `03_tela_golpes_ingles_pp_tipo.png` | Golpes em inglês (ROOST/GRAVITY/…), "PP" e "TIPO/" |
| `04_sylveon_usou_wakeup_slap.png` | "SYLVEON usou WAKE-UP SLAP!" |
| `05_selvagem_pidgey_desmaiou.png` | "Selvagem PIDGEY desmaiou!" |
| `06_ganhou_pontos_de_exp.png` | "SYLVEON ganhou 23 pontos de EXP" |
| `07_menu_batalha_rattata.png` | Segundo encontro (RATTATA), menu PT-BR |
| `08_e_super_efetivo.png` | "É super efetivo!" |
| `09_escapou_em_seguranca.png` | "Escapou em segurança!" |

## Método (reprodutível)

1. `bash scripts/firered/setup_ambiente.sh` (religa toolchain/mGBA/offsets em /tmp).
2. `python3 scripts/firered/aplicar_traducao.py --pokefirered /tmp/pokefirered --write`
3. `make -j2 MODERN=1` em /tmp/pokefirered.
4. `python3 scripts/firered/prova_golpes_e4.py --preparar-estado` → estado na grama da Rota 1.
5. `nav.py --parar-quando gBattleTypeFlags` para cair em batalha; screenshots com `--shots -1 --every 40`.
   **Armadilha reconfirmada:** `gBattleTypeFlags` fica sujo após a batalha —
   novos encontros SEMPRE a partir de um estado salvo antes de qualquer batalha.

No Windows: use os scripts via WSL (`wsl bash scripts/firered/setup_ambiente.sh` etc.),
conforme `docs/FIRERED.md`.
