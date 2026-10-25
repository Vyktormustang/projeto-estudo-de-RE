# F1 — Tela "FICHA DE PERSONAGEM" dos POKéMON (menu START)

Data: 2026-10-25 · Status: **CONFIRMADO em jogo**

## O que foi pedido

Adicionar ao jogo a "FICHA DE PERSONAGEM" (modelo de ficha de RPG estilo
MHA/BNHA enviado pelo usuário), adaptada ao design do FireRed.
**Correção do usuário: a ficha é dos POKéMON** (v1 mostrava o treinador;
refeita no mesmo dia).

## Adaptação feita (uma ficha por POKéMON)

START → **FICHA** abre a ficha do 1º POKéMON da equipe; **←/→ folheia a
equipe** (indicador "n/total" na barra de título). A/B fecha. Visual no
estilo do FireRed: janela branca, texto cinza-escuro/vermelho, barra de
título escura ecoando as barras pretas da ficha original.

| Campo da ficha original | Na ficha do POKéMON |
|---|---|
| NOME/CODNOME | NOME = espécie · CODINOME = apelido |
| TIPO SANGUÍNEO | TIPO = tipo(s) do POKéMON (ex.: FIRE/FLYING) |
| ALTURA | Altura da espécie (Pokédex), ex.: "ALTURA: 1,7 m" |
| AFILIAÇÃO (LADO) | Treinador original (OT) |
| INDIVIDUALIDADE | A habilidade (ex.: BLAZE, CUTE CHARM) |
| HABILIDADES | Os 4 golpes |
| UNIFORME/TRAJE | Retrato: **ícone animado** do POKéMON (sprite OBJ) |
| EQUIPAMENTOS | Item segurado (ou NENHUM) |
| Hexágono de atributos | **Radar pixel a pixel** com os 6 stats, escalados pelo maior |

Eixos do radar (horário a partir do topo, cores da ficha original
aproximadas pela paleta de texto): PODER=Ataque · TÉCNICA=At. Esp. ·
VELOCIDADE=Veloc. · CONTROLE=Defesa · COOPERAÇÃO=PS · INTELIGÊNCIA=Def. Esp.
Pontos coloridos nos vértices + legenda com marcadores.

Casos especiais: OVO POKéMON (campos "---", radar só com a grade) e equipe
vazia ("NENHUM POKéMON NA EQUIPE.").

## Implementação

- `src/ficha_personagem.c` + `include/ficha_personagem.h` (novos; base:
  estrutura do `src/diploma.c`): 2 BGs/2 janelas (600 tiles > 512 de um só
  charbase), radar via Bresenham sobre o pixel buffer da janela
  (`FillWindowPixelRect`), paleta padrão de texto (`GetTextWindowPalette(2)`),
  ícone via `CreateMonIcon`/`DestroyMonIcon` + `LoadMonIconPalettes`.
- Dados: `GetMonData`, `GetMonNickname`, `GetMonAbility`+`gAbilityNames`,
  `gSpeciesInfo[].types`+`gTypeNames`, `gMoveNames`,
  `gPokedexEntries[SpeciesToNationalPokedexNum()].height` (decímetros → "x,x m").
- `src/start_menu.c`: item FICHA (enum, tabela de ações, descrição
  "A FICHA DE PERSONAGEM dos seus POKéMON, como num RPG.",
  `SetUpStartMenu_NormalField`, callback no padrão do cartão de treinador).
- Menu START com 8 itens ficava por baixo da caixa de ajuda: espaçamento dos
  itens 15→14 px e janela 1 tile menor **somente quando há 8+ itens**
  (`src/new_menu_helpers.c`); com ≤7 itens o visual é 100% o original.
- Tudo aplicado por `scripts/firered/aplicar_ficha.py` (idempotente — patch
  sempre a partir do HEAD do git —, `--self-test`), chamado pelo passo 9 do
  `setup_ambiente.sh`.

## Provas (CONFIRMADO)

- `prova_tela_ficha.png` — ficha 1/2: SYLVEON, CODINOME, TIPO: FAIRY,
  AFILIAÇÃO (OT), CUTE CHARM, NENHUM, 4 golpes, ALTURA: 1,0 m, ícone, radar.
- `prova_segundo_pokemon.png` — após →: ficha 2/2: CHARIZARD,
  TIPO: FIRE/FLYING, BLAZE, FLAMETHROWER/FLY/DRAGON CLAW/SLASH,
  ALTURA: 1,7 m, ícone do CHARIZARD, radar com outro formato.
- `prova_menu_ficha.png` — B fecha e volta ao campo com o menu START aberto
  (FICHA entre o cartão do treinador e SALVAR, descrição nova, 8 itens
  visíveis).
- Regressão E8: **PASS em todas as etapas** nesta ROM.

## ROM entregue

- md5 `98efdd9bca9cb6166f4a3dc69693c48c`
- sha1 `ce8b8b2f7bfb1eda0d77c73291a2a3d6b54d45d2`
- sha256 `30dc33af13ac9d6a681998ba6acc0b9013b65600b4c17a934d49d1bd9aa1f2aa`
- 16.777.216 bytes
- Drive (público): https://drive.google.com/file/d/10Z6_EoI66NhhIqqCFXixseQa1AlWQMHV/view
  (o link da build anterior foi para a lixeira — use este)
