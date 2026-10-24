# T2 — Interface em PT-BR (onda 1) — provas em jogo

Data: 2026-10-24 · Issue: VYK-39 · ROM (onda 2): `pokefirered_modern.gba` md5 `69f7f9e4874db2bfdff214bcb598910d`

## O que foi traduzido nesta onda (CONFIRMADO em jogo)

- **602 strings de `src/strings.c`** (onda 1: 255; onda 2: +347) via dicionário
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
| `09_pc_menu.png` | PC: GUARDA-ITENS / CORREIO / DESLIGAR + “O que você quer fazer?” |
| `10_guarda_itens.png` | RETIRAR ITEM / GUARDAR ITEM / SAIR + “Retira itens do PC.” |
| `11_menino_menina.png` | Escolha MENINO / MENINA na intro |
| `12_seu_nome_teclado.png` | “SEU NOME?” + barra MOVER/OK/VOLTA |

## Regressão

`verificar_rom.py --amostras 0`: **ok** — 639 espécies/learnsets, E3-E7
conferidos na ROM nova (Gen 1-9 intacto).

## Onda 2 (mesmo dia)

+347 strings: campo/HMs, menu “escolha um POKéMON”, PC (guarda-itens,
correio, Boxes com ações e fundos), resumo do Pokémon (páginas, memo do
treinador, ovos), telas de nome, mapa da região (controles + 21 descrições
de áreas), trocas, creche/tutor de golpes, pesca, Fame Checker UI, Mystery
Gift, registros de batalha, easy chat. ROM md5 `69f7f9e4…`, regressão verde.

## Pendente (próximas ondas da T2)

Restam ~700 strings de `src/strings.c`, em grande parte Teachy TV, créditos
(ficam em inglês), restos JP não usados e textos de link/e-Reader raros.
O que faltar de visível será varrido junto da T3 (batalha).
