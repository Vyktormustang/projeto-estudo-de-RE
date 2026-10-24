# E5 — Habilidades (Gen 4-9)

**ROM de referência:** `pokefirered_modern.gba`
md5 `0faf41817ba5a32f036eb9c05f50fc88` ·
sha256 `a5ac58fc91c3336d37de516d50ead1f95930f133186782f1ed1e0fd054edd033` ·
9 604 608 B usados (arquivo de 16 777 216 B) · EWRAM 259 338 B (98,93 %)

Base: `pret/pokefirered` + E1 (1025 espécies) + E2 (dados) + E3 (Fada/split) + E4 (797 golpes).

---

## 1. O que esta etapa entrega

| item | antes | depois |
|---|---|---|
| habilidades no jogo | 78 (Gen 3) | **321** |
| nomes em `gAbilityNames` | 78 | **321** (16 colunas) |
| descrições (`gAbilityDescriptionPointers`) | 78 | **321** |
| espécies novas com habilidade de verdade | 0 | **639** |
| habilidades usadas por alguma espécie | 78 | **172 novas** (IDs 78-249) |
| habilidade de Gen 9 com efeito no motor | 0 | **1** (Earth Eater) |

`ABILITY_CACOPHONY` (FireRed 76) não existe no RHH e `ABILITY_AIR_LOCK` está em 76 lá e
77 aqui: o casamento é **por nome**, e os IDs 0-77 não foram tocados.

---

## 2. Evidências

| # | prova | comando | resultado |
|---|---|---|---|
| 1 | gerador idempotente | `gen_ability_data.py --write` 2× | 2ª passada: `nada a fazer` |
| 2 | conferência contra o clone | `gen_ability_data.py --check` | `ok: habilidades batem com o RHH e com o gerador` |
| 3 | autoteste do gerador | `gen_ability_data.py --self-test` | `7 casos` |
| 4 | compilação | `make modern` | EXIT 0 |
| 5 | dados no binário | `verificar_rom.py` | `E5 ok: 321 habilidades, 320/320 nomes e 321 descrições conferidas; habilidades de 639 espécies novas batem com o gerado` |
| 6 | tudo o resto continua | `verificar_rom.py` | `E3 ok` (12 regras de Fada), `E4 ok` (797 golpes), `ok: dados do ROM batem com o gerado` |
| 7 | autoteste do verificador | `verificar_rom.py --self-test` | 2 casos novos de E5 (aprova o certo, reprova o errado) |
| 8 | Earth Eater em batalha | `prova_habilidades_e5.py --prova` | **3/3 batalhas**, ver §3 |

### Capturas

| arquivo | o que mostra |
|---|---|
| `01_buldoze_anunciado.png` | `SYLVEON used BULLDOZE!` — Orthworm selvagem nível 30 com HP cheio |
| `02_earth_eater.png` | **`Wild ORTHWORM's EARTH EATER made ...`** — a habilidade tratou o golpe |
| `03_sem_habilidade_super_efetivo.png` | mesma batalha com a habilidade zerada: `It's super effecti[ve]` e a barra caiu |

---

## 3. A prova de batalha (diferencial triplo)

O selvagem da Rota 1 é trocado por **Orthworm (No968) nível 30** numa **cópia** da ROM
(12 slots de encontro, 2 bytes cada). O jogador é um Sylveon nível 60 com o golpe no
slot 1. Três batalhas, só muda o golpe/habilidade:

| batalha | golpe | Orthworm tem Earth Eater? | HP do inimigo | leitura |
|---|---|---|---|---|
| controle | TACKLE (Normal) | sim | 84 → **72** | a batalha fere |
| Earth Eater | BULLDOZE (Terra) | sim | 84 → **84** | **zero dano** |
| prova negativa | BULLDOZE (Terra) | **não** (habilidade zerada na cópia) | 84 → **0** | era a habilidade |

Por que o controle negativo importa: Orthworm é **Aço**, então Terrestre é 2× — sem a
habilidade o golpe não só fere, ele **nocauteia**. "Buldoze não fez nada" só pode vir da
habilidade.

---

## 4. As duas armadilhas que quase passaram

### 4.1 `abilities[2]` é `u8` — ID acima de 255 vira outra habilidade

`struct SpeciesInfo` guarda duas habilidades em **um byte cada**. Com 321 habilidades,
66 IDs passam de 255 e o `u8` **trunca em silêncio**: `ABILITY_QUARK_DRIVE` (283) vira
`EFFECT_SPORE` (27), `ABILITY_HUNGER_SWITCH` (259) vira `SPEED_BOOST` (3). Não quebra
nada — só a habilidade errada em 67 espécies.

Foi o `verificar_rom.py` que pegou (`habilidades [27, 0] != [283, 0]`).

**Solução (sem alargar struct):** ordenar as IDs novas por **uso**. As 172 habilidades que
alguma espécie do jogo usa vão para 78-249 (cabe no byte); as 71 que nenhuma usa ficam em
250-320. O gerador **para** se as usadas não couberem (`SystemExit`), em vez de truncar.
Alargar para `u16` continua sendo o certo a médio prazo — está anotado como dívida.

### 4.2 `#define` no meio do trecho → Fezandipiti virou Ogerpon

`blocos_de_especie()` cortava o bloco da espécie no próximo `[SPECIES_...]`, mas entre dois
blocos o RHH define macros (`#define OGERPON_SPECIES_INFO(...)`, multi-linha). O corpo da
macro entrava no bloco anterior e `campos()` (que fica com a **última** ocorrência) lia
`.abilities`/`.natDexNum` da macro: Fezandipiti saiu com `ABILITY_NONE`, dex de Ogerpon e
tipo errado.

Correção no `gen_species_data.py`: cortar o trecho no primeiro `\n#define`. Efeito colateral
medido: `habilidades_ausentes` 1 → **0**, `tipos_substituidos` 7 → **4**,
`descricao_substituida` 28 → **22**, `evos_puladas` 51 → 50.

### 4.3 Nome de espécie com espaço de enchimento

`gen_species_constants.py` gravava `_("SYLVEON   ")` (`ljust(10)`), e a caixa de batalha
mostrava `Go! SYLVEON   !`. Agora grava `_("SYLVEON")`; o array já tem 11 colunas.

---

## 5. Limitações conhecidas

- **242 das 243 habilidades novas não têm efeito.** Habilidade sem `case` no
  `AbilityBattleEffects` é silenciosa: não trava, simplesmente não acontece nada. É o
  mesmo fallback da E4. Só Earth Eater foi implementada (a de Gen 9 pedida no aceite).
- As **149 habilidades restantes** usadas por espécies estão em IDs ≤ 249 e funcionam como
  dado; falta o motor.
- A ordem das IDs depende do uso: se a E2 mudar quais espécies existem, as IDs mudam. Save
  antigo pode apontar para a habilidade errada — aceitável enquanto o projeto não tem
  release.
- `ABILITY_NAME_LENGTH` foi de 12 para 16 e o buffer do resumo virou
  `[ABILITY_NAME_LENGTH + 1]`; a caixa do resumo desenha o nome em 66 px, então nomes de
  16 colunas encostam na borda (cosmético, E7).
- Menu de golpes continua cortando nomes longos (herdado da E4).
- EWRAM em **98,93 %**: qualquer struct novo no time quebra o build por falta de RAM.

---

## 6. Como reproduzir

```bash
# ambiente (compila o FireRed + o RHH de referência + toolchain)
bash scripts/firered/setup_ambiente.sh

# dados das habilidades e o gancho de motor
python3 scripts/firered/gen_ability_data.py --pokefirered /tmp/pokefirered --reference /tmp/fre --write
python3 scripts/firered/gen_ability_data.py --pokefirered /tmp/pokefirered --reference /tmp/fre --check
python3 scripts/firered/apply_e5_port.py   --pokefirered /tmp/pokefirered --check

# a E2 precisa rodar DEPOIS das habilidades (os nomes passam a existir)
python3 scripts/firered/gen_species_data.py --pokefirered /tmp/pokefirered --reference /tmp/fre --write

# ROM + conferência
cd /tmp/pokefirered && PATH=/tmp/tc/bin:$PATH make modern -j8
python3 scripts/firered/verificar_rom.py

# prova em batalha (precisa do estado da Rota 1 e do núcleo do mGBA)
python3 scripts/firered/prova_golpes_e4.py --preparar-estado     # gera /tmp/e4estado
python3 scripts/firered/prova_habilidades_e5.py --prova
```

No Windows: WSL ou `scripts\win\*.ps1` (ver `docs/FIRERED.md`).

---

## 7. Erros de método (para não repetir)

1. **Savestate só vale para a ROM exata.** Depois de qualquer rebuild, `/tmp/e4estado`
   precisa ser regenerado — um estado antigo carrega com o mapa desenhado e o jogador
   **não anda** (o `pc`/ponteiros apontam para código que mudou de lugar).
2. **`--shots` não é intervalo.** `--shots 40` = capturar no frame 40; o intervalo é
   `--every 40`. O intervalo certo achou a mensagem da habilidade em 20 frames.
3. **`--out` salva no instante em que a rota termina**; use `--shots -1` para não parar
   antes do fim dos frames, senão o estado fica no meio de um passo.
4. **Trocar só o slot 0 do encontro não serve**: o jogo sorteia entre os 12 e veio um
   Rattata nível 3 no meio da "prova do Orthworm". Trocar os 12 custou uma linha.
5. **Regex de chaves** (de novo): o `.abilities` da macro do Ogerpon só apareceu porque o
   corte foi por `#define`, não por chaves.
6. **`--core` do mGBA muda de lugar entre sessões** (`/tmp/mgba-0.10.5/...` vs
   `/tmp/mgba/mgba-0.10.5/...`): o `nav.py` agora procura os dois e respeita `MGBA_CORE`.
7. **Conferir só o fonte não basta**: os 67 truncamentos de `u8` passariam em qualquer
   `--check` de arquivos; só a leitura do ROM em execução mostrou.
