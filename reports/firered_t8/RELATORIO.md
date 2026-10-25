# T8 — Varredura final + regressão + entrega (VYK-45)

Data: 2026-10-25. ROM final: **md5 `a6dc773f5162041c04301924af8505ca`**
(pokefirered MODERN=1 + port Gen 1-9 + tradução PT-BR T1-T8).

## O que entrou na varredura

### 1. `src/strings.c` — 62 sobras traduzidas (dict T2 → 664 entradas)

Pokédex (LISTA POKéMON/BUSCA), bolsos da bolsa (ITENS-CHAVE, BOLSO DE
ITENS/ITENS-CHAVE/POKé BALLS), rótulos ALT./PESO, aviso do MYSTERY GIFT,
apagador de golpes ("1, 2, e‥ Puf!"), resumo (encontro do destino com
ovos), whiteout fora de batalha, diploma, barra do caça-níqueis
(COMBOS/APOSTA/PARAR/SAIR), barras do Sistema de AJUDA (MOVER/OK/SAIR),
fragmentos de uso de item (" foi usado em", " subiu para o nível"),
Direita/Esquerda, easy chat completo (perfil, entrevista, carta, canção
do BARDO).

### 2. Pokédex em MÉTRICO (`apply_t8_varredura.py` em `pokedex_screen.c`)

`DexScreen_PrintMonHeight/Weight` imprimiam pés/polegadas e libras
(CONFIRMADO no código: `10000*height/254`, `weight*100000/4536`).
Agora: altura em `m` com vírgula ("0,5 m") e peso em `kg` ("10,2 kg") —
a dex guarda decímetros e hectogramas, conversão exata sem arredondar.
Não capturado = "??,? m" / "????,? kg".

### 3. Nomes do mapa (popup de área, mapa de voo, dex)

`region_map_sections.json` (fonte do `.h` auto-gerado): ROUTE n→ROTA n
(27), FLORESTA VIRIDIAN, MONTE LUA, CAMINHO SUBTERRÂNEO (×2), CAVERNA
DIGLETT, ESTRADA DA VITÓRIA, ESCONDERIJO ROCKET, MANSÃO POKéMON, ZONA
DO SAFÁRI, LIGA POKéMON, ILHAS SEAFOAM, TORRE POKéMON, CAVERNA
CERULEAN, USINA, MONTE EMBER, DEPÓSITO ROCKET, LABIRINTO AQUÁTICO,
CÂNION SEVAULT, ENTRADA DO CÂNION, CAVERNA ICEFALL, SPA EMBER, RUÍNAS/
CÂMARAS/CHAVE TANOBY e as 7 câmaras Unown. Nomes próprios ficam em
inglês (cidades, ilhas, S.S. ANNE, SILPH CO., ROCK TUNNEL etc.),
consistente com o glossário do T7.

O gerador deriva o símbolo C do texto do nome, então
`apply_t8_varredura.py` também renomeia as 13 referências fixas em
`region_map.c` (lista de dungeons).

### 4. Bloco com `#ifdef` no meio

`PalletTown_RivalsHouse_Text_ThereYouGoAllDone` (DAISY penteando o
POKéMON) — as duas variantes (BUGFIX e JP) traduzidas pelo script.

### Fica em inglês (deliberado, documentado)

- Créditos (nomes e cargos da equipe original).
- Telas exclusivas de wireless/link multiplayer (Berry Crush, Pokémon
  Jump, colheita de Berries, Wonder Card/News, chat da Union Room):
  sem como provar em jogo neste ambiente (contrato: nada de alegação
  sem prova). PROVÁVEL que caibam, mas ficaram EN.
- `gTypeNames` (tipos), nomes de golpes/itens/espécies/habilidades —
  decisão do usuário.
- "HELP"/"LR"/"L=A" (valores do MODO BOTÃO), "OT", "PP", "TM/HM",
  termos idênticos.

## Provas em jogo (CONFIRMADO)

| Prova | Evidência |
| --- | --- |
| Popup de área "ROTA 1" ao voltar de Pallet | `prova_popup_rota1.png` |
| Índice da dex: LISTA POKéMON, MODO NUMÉRICO KANTO/NACIONAL, HABITATS, Vistos/Capturados | `prova_dex_indice.png` |
| Lista nacional: cabeçalho LISTA POKéMON, Nº915 LECHONK capturado | `prova_dex_lista.png` |
| Entrada do LECHONK: "Porco POKéMON", **ALT. 0,5 m**, **PESO 10,2 kg**, descrição PT-BR (T6), rodapé GRITO/PRÓX. DADOS/SAI | `prova_dex_metrica.png` |

Os valores métricos batem com os oficiais do Lechonk (0,5 m / 10,2 kg).

## Regressão E8 — PASS (ROM final)

```
PASS  verificar_rom na ROM real
PASS  E4 golpes modernos em batalha (6 rodadas)
PASS  E5 habilidade moderna (Earth Eater 3/3)
PASS  E7 encontro+captura de Gen 9 na Rota 1
REGRESSÃO: PASS (todas as etapas)
```

## Erro de método registrado (não repetir)

1. **Nunca editar um script shell enquanto um processo o executa** —
   o bash lê o arquivo em pedaços; a edição desloca bytes e quebra o
   parse no meio da execução (foi o que derrubou o setup na etapa 9).
2. **O link do Makefile upstream mascara falha do `ld`**
   (`ld ... | cat` → exit code do `cat`). Um `.elf` VELHO fica no lugar
   e o `.gba` sai "novo" porém sem as mudanças. Sempre `rm -f *.elf`
   antes do build final e conferir bytes esperados dentro da ROM.
3. **Gerador Inja deriva identificadores C do TEXTO traduzido**
   (`cleanString(name)`): traduzir o JSON do region map exige renomear
   as referências fixas em `region_map.c`.
