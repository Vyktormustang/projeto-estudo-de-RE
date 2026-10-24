# T2 — Interface em PT-BR (onda 1) — provas em jogo

Data: 2026-10-24 · Issue: VYK-39 · ROM: `pokefirered_modern.gba` md5 `0d1dfff71bbfdffa180f9516c8fc631b`

## O que foi traduzido nesta onda (CONFIRMADO em jogo)

- **255 strings de `src/strings.c`** via dicionário novo
  `scripts/firered/traducao_strings_ptbr.py` (chave = nome da variável C,
  aplicado/validado pelo `aplicar_traducao.py`, que agora também trata `.c`).
- **`data/text/save.inc`** completo (diálogo de salvar) via árvore
  `scripts/firered/traducao/`.

Áreas cobertas: menu principal (CONTINUAR/NOVO JOGO/OPÇÕES), menu de pausa e
descrições, salvar, tela de opções, bolsa, loja, menu do time, cartas,
uso de itens, aprender golpes, Pokédex UI, Trainer Card, Hall da Fama,
teclado de apelido, cassino. Nomes de ATAQUES e ITENS ficam em inglês
(decisão do usuário).

## Capturas (mGBA libretro, ROM rodando)

| Arquivo | O que prova |
|---|---|
| `01_menu_principal_continuar.png` | CONTINUAR / JOGADOR / TEMPO / INSÍGNIAS / NOVO JOGO |
| `02_controles_barra_avanca.png` | Tela CONTROLES com barra `A AVANÇA` |
| `03_menu_pausa_descricao.png` | BOLSA/SALVAR/OPÇÕES/SAIR + descrição da bolsa em PT |
| `04_salvar_pergunta_sim_nao.png` | “Você quer salvar o jogo?” + SIM/NÃO + janela JOGADOR/INSÍGNIAS/TEMPO |
| `05_salvando_nao_desligue.png` | “SALVANDO… NÃO DESLIGUE O CONSOLE.” |
| `06_salvou_o_jogo.png` | “AAAAAA salvou o jogo.” |
| `07_opcoes.png` | VELOC. TEXTO/ANIMAÇÃO/ESTILO LUTA/SOM/MODO BOTÃO/MOLDURA/SAIR |
| `08_bolsa_itens.png` | Bolsa aberta: bolso ITENS, FECHAR BOLSA |

## Regressão

`verificar_rom.py --amostras 0`: **ok** — 639 espécies/learnsets, E3-E7
conferidos na ROM nova (Gen 1-9 intacto).

## Pendente (próximas ondas da T2)

Restam ~1.000 strings menos visíveis em `src/strings.c` (PC/Box, link,
Teachy TV, Fame Checker, resumo do Pokémon etc.) e os `.c` auxiliares
(~40 strings). Serão cobertas nas ondas seguintes junto de T3 (batalha).
