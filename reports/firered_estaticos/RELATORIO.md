# Encontros estáticos: os inobtíveis aparecem no mapa como os lendários

Pedido: *"Quero que os pokemons inobitiveis apareçam no mapa como os
lendários"*. Depois da mistura de encontros (E7) e dos scripts do jogo, 500
das 1025 espécies não tinham NENHUMA forma de obtenção. Agora cada família
inobtível tem a FORMA BASE parada no overworld, no padrão do MEWTWO da
Caverna Cerulean: sprite visível no mapa → A → grito + mensagem → música de
confronto → batalha única. O resto da família vem por evolução.

## Números (medidos no fonte, CONFIRMADO)

- Obtíveis antes: 525 espécies (322 por grama/água/scripts/trocas + fecho
  por evolução). Inobtíveis: **500** (lista em
  `scripts/firered/estaticos/inobtiveis.json`).
- Famílias inobtíveis → **334 formas base**, TODAS colocadas em **57 mapas**
  (log completo em `distribuicao_gerada.log`).
- Nível do encontro pela soma de atributos-base: ≥580 → Lv70, ≥480 → Lv55,
  ≥380 → Lv40, senão Lv25. Lendários/míticas caem no endgame (Victory Road,
  Cerulean Cave, Sevii) pela ordem de progressão do gerador.

## Como funciona (3 truques, zero mudança no formato do save)

1. **Espécie no template do objeto**: o campo `trainer_sight_or_berry_tree_id`
   (u16 livre com `TRAINER_TYPE_NONE`) guarda `SPECIES_X`. Um único script
   (`EventScript_EncontroEstatico`) serve para os 334 objetos: o special
   `EstaticoPrepararEncontro` acha o template pela localId tocada.
2. **Sprite = ícone do Pokémon**: graphics id novo (`OBJ_EVENT_GFX_MON_ESTATICO`,
   152) com hook no spawn que copia o 1º quadro do ícone (32×32, 0x200 B)
   direto para o VRAM do sprite e carrega a paleta do ícone no slot
   `PALSLOT_NPC_SPECIAL`. Por isso todos os estáticos de um mapa usam a MESMA
   paleta de ícone (restrição do gerador), e mapas com Meteorite/Seagallop/
   S.S. Anne (donos do slot) ficam de fora.
3. **Flag virtual 0x5000+espécie**: o campo flag do objeto não gasta flag do
   save — `FlagGet` responde "a espécie já foi capturada?" direto da Pokédex.
   Capturou → o objeto some para sempre; fugiu/desmaiou → continua lá.

## Provas (ROM md5 `692b33ae6c4d46bd126f18b96a356d17`)

| arquivo | o que mostra |
|---|---|
| `prova_icone_no_mapa.png` | CHIKORITA (ícone) parada na Rota 1 (16,15), acima do jogador |
| `prova_mensagem.png` | "O CHIKORITA selvagem está te encarando!" após A |
| `prova_batalha_chikorita.png` | batalha: CHIKORITA Lv25, igual encontro lendário |
| `prova_sumico_apos_captura.png` | mesma câmera com a dex marcada "capturada": o objeto NÃO respawna (LOTAD e TAROUNTULA do mapa continuam) |

Variáveis lidas da RAM na interação (CONFIRMADO): `VAR_0x8004=0x98`
(SPECIES_CHIKORITA), `VAR_0x8005=25` (nível), 6 templates estáticos na Rota 1.

Regressão E8 completa: **PASS** (self-tests, verificar_rom, E4, E5, E7).

## Erros de método encontrados (e corrigidos)

- `def_special` adicionado DEPOIS de `gSpecialsEnd::` fica fora da tabela — o
  comando `special` valida o índice contra o fim e vira no-op silencioso.
- `specialvar` com função `void` sobrescreve `VAR_RESULT` com lixo (r0); o
  special agora escreve `gSpecialVar_Result` e o script usa `special`.
- O hook de sprite precisa ficar no CALLER (`TrySpawnObjectEventTemplate`):
  `TrySetupObjectEventSprite` tem `sprite->images` sobrescrito logo depois.
- Objetos inanimados nunca disparam a cópia de frame do sistema de animação —
  a cópia do ícone para o VRAM tem de ser direta (`CpuFastCopy`).
- Prova E5 era frágil: o Orthworm se fere SOZINHO com recoil de TAKE DOWN
  (85→81 com "restaurou HP usando EARTH EATER" na tela). Critério agora
  tolera 30% de perda por recoil.
- Prova E7: o frame do teclado de apelido desliza com o RNG; START agora é
  repetido em 3 janelas (3500/4400/5300).
