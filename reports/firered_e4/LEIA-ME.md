# E4 — golpes das Gen 4-9

**Data:** 2026-10-23
**ROM:** `pokefirered_modern.gba`, sha256
`9bda1da4bf7a89239e5441b059faa2ee42e97b9f4ee42fae8b915d889813265d`
(md5 `d3d940bd16a82e3f1db71ce65eb05311`, 16 777 216 B)
**Base:** `pret/pokefirered` @ `ce6406d` + E1 + E2 + E3 + **E4**
(`gen_move_data.py --write`)
**Build:** `make -j$(nproc) MODERN=1` → EXIT 0, 0 `error:`; ROM 9 584 280 B
(`+39 KB` em relação à E3)
**Custo em espaço:** 442 × (12 B da tabela + 17 B do nome + ~70 B de descrição)

---

## O que esta etapa entrega

O FireRed tem **355 golpes** (Gen 1-3). As 639 espécies novas da E2 trouxeram
**3 123 referências de golpe filtradas** porque o motor não conhecia o `MOVE_*`.
Esta etapa devolve os **446 golpes** que alguma espécie realmente aprende:

- **442 golpes novos** com ID 355…796;
- **4 golpes que só mudaram de nome** depois da Gen 3 viram `#define` para o
  nome antigo do FireRed (`MOVE_VISE_GRIP` → `MOVE_VICE_GRIP`,
  `MOVE_HIGH_JUMP_KICK`, `MOVE_FEINT_ATTACK`, `MOVE_SMELLING_SALTS`);
- `MOVES_COUNT` 355 → **797**. Os IDs 0-354 **não mudam**.

Cada golpe novo ganhou nome, descrição, tipo, poder, precisão, PP, alvo,
prioridade, flags e categoria física/especial — e uma **animação**.

---

## O que está CONFIRMADO

| # | Afirmação | Evidência |
|---|---|---|
| 1 | Compila e linka | `make` EXIT 0, 0 erros; sha256 novo |
| 2 | 797 golpes **no ROM** | `verificar_rom.py` percorre `gBattleMoves` (passo medido de **12 B**) e compara **todos** os campos com o gerado |
| 3 | Nomes de 17 B (16 + terminador) | `verificar_rom.py` decodifica `gMoveNames` com o charmap e compara com o `move_names.h` |
| 4 | Descrições por ponteiro | `verificar_rom.py` lê `gMoveDescriptionPointers[442]` e confere que cada ponteiro cai dentro do ROM e aponta texto não vazio |
| 5 | Categoria física/especial | `verificar_rom.py` compara a contagem de físicos do ROM com `battle_moves_category.h` |
| 6 | **Toda animação existe** | `verificar_rom.py` lê `gBattleAnims_Moves[797]`; os 442 novos apontam para o script de TACKLE (fallback) |
| 7 | Batalha com golpe novo **funciona** | `01_moonblast_usado.png`: "SYLVEON used MOONBLAST!" |
| 8 | Menu de golpes mostra os novos | `02_menu_golpes_novos.png`: MOONBLAST / DAZZLING GLEAM / SPIRIT BREAK / PLAY ROUGH, `TYPE/FAIRY` |
| 9 | Kanto sem regressão | `03_batalha_kanto.png`: Rattata selvagem na Rota 1 |
| 10 | **12/12 batalhas aleatórias sem travar** | `prova_golpes_e4.py --rodadas 12 --seed 7` |

### O teste de batalha (o critério de aceite)

`prova_golpes_e4.py` monta, a cada rodada, um time com **4 golpes sorteados**
dos 442 novos (o slot 1 é sempre um golpe de dano), entra na grama da Rota 1,
martela A por 3 200 frames lendo `gBattleMons` a cada 100 e aprova se o HP de
alguém mudou (ou a batalha terminou). HP parado com A martelado = travamento.

```
rodada 1: golpes [604, 432, 557, 689] -> ok (HP mudou: jogador 202->202, inimigo 15->0)
...
rodada 12: golpes [766, 512, 641, 773] -> ok (HP mudou: jogador 202->202, inimigo 15->0)

12/12 rodadas ok
```

Cada rodada tem até 2 tentativas: um golpe de precisão 80 que erra **no mesmo
turno** em que o inimigo usa um golpe de status não muda HP nenhum — isso é
sorte, não travamento (foi o falso positivo da rodada 4 com seed 7).

**Cobertura honesta:** as 12 rodadas *executam* 12 golpes novos diferentes e
*desenham* 48 no menu. A garantia sobre os 442 vem do teste de dados
(item 2), não da batalha — não dá para batalhar 442 vezes em tempo razoável.

---

## Como os efeitos foram resolvidos

O RHH tem 281 efeitos de golpe; o FireRed, 214. Sem reescrever o motor, cada
golpe novo precisa de um efeito que **exista** (senão o script de batalha salta
para um endereço inválido).

| como | golpes | o que acontece |
|---|---|---|
| efeito com o mesmo nome | 233 | comportamento idêntico ao RHH |
| `EFFECT_STAT_CHANGE` inferido | 9 | vira `EFFECT_ATTACK_DOWN`, `EFFECT_SPEED_UP_2`, `EFFECT_BULK_UP`… a partir do `ADDITIONAL_EFFECTS` |
| equivalente semântico | 9 | `EFFECT_ROOST`→`RECOVER`, `NATURE'S MADNESS`→`SUPER FANG`, cargas de 2 turnos→`RAZOR WIND`… |
| **fallback de dano** | 90 | `EFFECT_HIT`: dá o dano certo, perde o efeito extra |
| **fallback de status** | 101 | `EFFECT_SPLASH`: **não faz nada**, mas nunca trava |

O fallback é uma decisão consciente: um golpe de status que não faz nada é
recuperável na E5/E7; um efeito inexistente corrompe a batalha.

### Duas armadilhas do `moves_info.h` do RHH

1. **Os IDs estão num `enum`**, com incremento implícito e sentinelas no meio
   (`MOVES_COUNT_GEN1`, `MOVE_ROOST = MOVES_COUNT_GEN3`). Ler só `#define`
   devolve **0 golpes**; e os aliases (`MOVE_DOUBLESLAP = MOVE_DOUBLE_SLAP`)
   fazem o mesmo golpe aparecer duas vezes.
2. **Os valores são ternárias de configuração**:
   `.power = B_UPDATED_MOVE_DATA >= GEN_6 ? 90 : 70`. É preciso avaliar a
   comparação com `GEN_LATEST = GEN_9 = 8` — inclusive porque
   `>= GEN_CHAMPIONS` (9) é **falso** e escolhe o **segundo** ramo. Pegar
   sempre o primeiro ramo dava poder errado em 24 golpes e tipo errado em 1
   (Snap Trap virava Aço em vez de Planta).

---

## O que muda no jogo (e o que não muda)

- **`MOVES_COUNT` 355 → 797**: toda tabela indexada por golpe cresceu
  (`gBattleMoves`, `gMoveNames`, `gMoveDescriptionPointers`, `gMoveCategories`,
  `gBattleAnims_Moves`). Nada mais do FireRed foi tocado.
- **`MOVE_NAME_LENGTH` 12 → 16** (o maior nome do conjunto tem 16 colunas,
  "Collision Course"). Apóstrofo some ("King's Shield" → "KINGS SHIELD")
  porque **não existe** no charmap do FireRed.
- **Limitação conhecida:** o *menu de golpes em batalha* tem largura para 12
  colunas — "DAZZLING GLEAM" aparece cortado em `DAZZLING GLEA`. É layout de
  janela (E7), não dado: a ficha do Pokémon e a descrição mostram o nome
  inteiro. Corrigir exige alargar a janela do menu de golpes.
- **Animação:** os 442 golpes usam a animação genérica de TACKLE (impacto +
  tremida + som). Animações próprias são trabalho de E6.

---

## Como reproduzir

```bash
# 1) dados (idempotente: rodar duas vezes não muda nada)
python3 scripts/firered/gen_move_data.py --self-test
python3 scripts/firered/gen_move_data.py --pokefirered /tmp/pokefirered \
    --reference /tmp/fre --write
python3 scripts/firered/gen_move_data.py --pokefirered /tmp/pokefirered \
    --reference /tmp/fre --check

# 2) build
cd /tmp/pokefirered && make -j"$(nproc)" MODERN=1

# 3) prova no binário
python3 scripts/firered/verificar_rom.py --pokefirered /tmp/pokefirered

# 4) prova em batalha (mGBA)
python3 scripts/firered/prova_golpes_e4.py --self-test
python3 scripts/firered/prova_golpes_e4.py --preparar-estado   # título -> Rota 1
python3 scripts/firered/prova_golpes_e4.py --rodadas 12 --seed 7
```

---

## Erros de método desta etapa (para não repetir)

1. **`gBattleAnims_Moves` é uma tabela em assembly com 355 entradas.** Golpe
   com ID novo lia um ponteiro **fora da tabela** e o jogo executava um script
   de animação aleatório — a batalha congelava. Foi o próprio teste de batalha
   que pegou. Agora a tabela é completada com `Move_TACKLE` e o
   `verificar_rom.py` confere as 797 entradas.
2. **Savestate só vale para a ROM exata.** Ele guarda ponteiros para o ROM
   (callbacks, scripts); ao reconstruir, o estado antigo carrega e o jogador
   fica **congelado** (nenhum botão responde). Sempre regerar depois de um
   build — por isso `--preparar-estado` termina com `estado_responde()`.
3. **`nav.py --out` salva no frame final.** Se a rota termina antes, o
   `break` cortava o run na chegada e o estado saía no meio do passo. Passar
   `--shots -1` mantém o run até `--frames` e deixa o jogo assentar.
4. **`--parar-quando gBattleTypeFlags` no passo de luta parava no frame 4**
   (a flag já estava ligada) → zero leituras de `gBattleMons`.
5. **A a cada 55 frames é pouco**: a caixa de texto do FireRed avança ~20
   frames por letra. Com 40 frames o turno fecha.
6. **`--write` não era idempotente**: `montar_tudo()` calculava os "golpes
   novos" a partir do `moves.h` já aplicado, então a segunda execução via
   **0 novos** e apagava os 442. Agora `golpes_existentes()` remove o bloco
   `// E4` antes de ler, e o `--self-test` aplica duas vezes num clone falso.
7. **A grama da Rota 1 não fica onde a rota da E3 mandava.** O `map.bin` é
   row-major 24×40 e as únicas células `MB_TALL_GRASS` são as bordas (x=0/22)
   e a coluna x=8 nas linhas 5-9. O corredor de entrada (x=12-13, y=36-39) é
   grama **de encontro**: subir e descer ali funciona; a rota "12,38;12,39;
   13,39;13,38" travava na cerca.
