# F1 — Tela "FICHA DE PERSONAGEM" (menu START)

Data: 2026-10-25 · Status: **CONFIRMADO em jogo**

## O que foi pedido

Adicionar ao jogo a "FICHA DE PERSONAGEM" (modelo de ficha de RPG estilo
MHA/BNHA enviado pelo usuário), adaptada ao design do FireRed, com liberdade
para modificações.

## Adaptação feita (decisões)

A ficha original é um formulário em branco para preencher à mão. No jogo, ela
virou uma tela viva, preenchida automaticamente pelo save, no estilo visual
do FireRed (janela branca, texto cinza-escuro/vermelho, barra de título
escura ecoando as barras pretas da ficha original):

| Campo da ficha original | Na tela do jogo |
|---|---|
| NOME/CODINOME | Nome do jogador |
| TIPO SANGUÍNEO | Derivado do ID do treinador (A/B/AB/O — estável por save) |
| ALTURA | 1,40 m (menino) / 1,38 m (menina) |
| DOB/IDADE | 11 ANOS (canônico de FRLG) |
| AFILIAÇÃO (LADO) | Evolui com as insígnias: NOVATO DE PALLET → TREINADOR POKéMON → DESAFIANTE DA LIGA → ELITE DE KANTO |
| INDIVIDUALIDADE | O parceiro: 1º POKéMON da equipe (espécie + nível; OVO POKéMON/NENHUMA) |
| HABILIDADES | Contador INSÍGNIAS: n na barra de título |
| UNIFORME/TRAJE | Omitido (sem espaço útil em 240×160; o cartão de treinador já mostra o retrato) |
| EQUIPAMENTOS | Item registrado no SELECT (ou NENHUM) |
| Hexágono de atributos | **Radar desenhado pixel a pixel** com os 6 stats do parceiro, escalados pelo maior stat |

Mapa dos 6 eixos (sentido horário a partir do topo, cores da ficha original
aproximadas pela paleta de texto do jogo):
PODER=Ataque · TÉCNICA=At. Esp. · VELOCIDADE=Veloc. · CONTROLE=Defesa ·
COOPERAÇÃO=PS · INTELIGÊNCIA=Def. Esp. Legenda com marcadores coloridos,
pontos coloridos nos vértices (como na ficha original).

## Como acessar no jogo

START → **FICHA** (novo item, entre o cartão do treinador e SALVAR).
A/B fecha e volta ao menu. Descrição no modo AJUDA:
"Sua FICHA DE PERSONAGEM, no estilo de uma ficha de RPG."

## Implementação

- `src/ficha_personagem.c` + `include/ficha_personagem.h` (novos; base:
  estrutura do `src/diploma.c`): 2 BGs/2 janelas (600 tiles > 512 de um só
  charbase), radar via Bresenham sobre o pixel buffer da janela
  (`FillWindowPixelRect`), paleta padrão de texto (`GetTextWindowPalette(2)`).
- `src/start_menu.c`: item FICHA (enum, tabela de ações, descrição,
  `SetUpStartMenu_NormalField`, callback no padrão do cartão de treinador).
- Menu START com 8 itens ficava por baixo da caixa de ajuda: espaçamento dos
  itens 15→14 px e janela 1 tile menor **somente quando há 8+ itens**
  (`src/new_menu_helpers.c`); com ≤7 itens o visual é 100% o original.
- Tudo aplicado por `scripts/firered/aplicar_ficha.py` (idempotente, patch
  sempre a partir do HEAD do git, `--self-test`), chamado pelo passo 9 do
  `setup_ambiente.sh`.

## Provas (CONFIRMADO)

- `prova_menu_ficha.png` — menu START com FICHA + descrição; os 8 itens
  visíveis (SAIR inteiro acima da caixa de ajuda).
- `prova_tela_ficha.png` — a tela: título, INSÍGNIAS: 0, NOME, IDADE 11 ANOS,
  SANGUE TIPO O, ALTURA 1,40 m, NOVATO DE PALLET, SYLVEON Nv.60, NENHUM,
  radar com polígono + pontos coloridos + legenda.
- `prova_volta_menu.png` — B sai da ficha e volta ao campo com o menu aberto.
- Regressão E8: **PASS em todas as etapas** nesta ROM.

## ROM entregue

- md5 `6971baf2ecfd89beca050f44961addbf`
- sha1 `c71db48ff735af2eab73d8dd0501c69c979deefc`
- sha256 `ae5f1dff3d6ae72354b76c39ffebdcf27b78f9f5054a6705ae77173fd48b00d9`
- 16.777.216 bytes
- Drive (público): https://drive.google.com/file/d/1R0A1slLvh4OchEkJ7NHtbIqIrxkgeWZB/view
  (o link da build anterior foi para a lixeira — use este)
