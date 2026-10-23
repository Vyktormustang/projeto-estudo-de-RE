# Base pura do FireRed — provas de que a E0 está concluída

Estas imagens foram capturadas da **ROM compilada do `pret/pokefirered` sem nenhuma alteração**
(commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`), como linha de base do projeto
[`docs/PLANO_FIRERED_GEN1-9.md`](../../docs/PLANO_FIRERED_GEN1-9.md).

| Arquivo | O que mostra |
|---|---|
| `01_titulo.png` | Tela de título do FireRed (Charizard, "© 2004 GAME FREAK inc.") |
| `02_quarto.png` | Novo jogo: quarto do jogador em Pallet Town |
| `03_pallet_town.png` | Rua de Pallet Town, saindo da casa pela porta |
| `04_porta_casa_1f.png` | Sala do 1º andar, em cima do tapete da porta |

## Números do build

```
arquivo : pokefirered_modern.gba
tamanho : 16.777.216 bytes
sha256  : 32e26d4ff5a1564d90b82a68e4ae84b662098014ee1cc512fd244c15a083e978
header  : POKEMON FIRE / BPRE / maker 01
build   : 8min19s com make -j2 MODERN=1 CC1_DAEMONS=2
ROM     : 9.345.048 / 33.554.432 B (27,85%)
EWRAM   : 259.182 / 262.144 B (98,87%)   <- gargalo
IWRAM   :  29.592 /  32.768 B (90,31%)
```

## Como foi feito (reproduzível)

O driver é o mesmo `scripts/firered/nav.py` usado nos testes anteriores. A diferença é o `--map`:

```bash
cd pokefirered
cp pokefirered_modern.gba /tmp/
cd ../projeto-estudo-de-RE

# 1) título
python3 scripts/firered/nav.py --rom /tmp/pokefirered_modern.gba \
  --map /tmp/pokefirered_modern.map \
  --outdir /tmp/base0 --frames 1800 --shots 1790 --out /tmp/base0/title.bin

# 2) START no título -> menu
python3 scripts/firered/nav.py --rom /tmp/pokefirered_modern.gba \
  --map /tmp/pokefirered_modern.map \
  --outdir /tmp/base1 --in /tmp/base0/title.bin --frames 2000 \
  --script "20-40:START;60-70:A" --out /tmp/base0/menu.bin

# 3) assistente de controles + fala do Oak + nome -> quarto
python3 scripts/firered/nav.py --rom /tmp/pokefirered_modern.gba \
  --map /tmp/pokefirered_modern.map \
  --outdir /tmp/base2 --in /tmp/base0/menu.bin --frames 4200 \
  --script "$(python3 -c "print(';'.join(f'{i}-{i+7}:A' for i in range(20,4000,24)))")" \
  --every 400 --out /tmp/base0/room.bin
```

A partir do quarto, os warps:

- **escada** (2F → 1F): o tile é o metatítulo 7, behavior `0x6F`
  (`MB_DOWN_LEFT_STAIR_WARP`). Warp direcional: só dispara **entrando andando para a esquerda**.
  Basta ir para `(11,2)` e apertar `LEFT`.
- **porta** (1F → Pallet Town): o tile é o metatítulo 19, behavior `0x65`
  (`MB_SOUTH_ARROW_WARP`), na posição `(4,8)`. Vá para `(4,7)` e aperte `DOWN`.

```bash
# escada 4:1 -> 4:0  (posicao lida da RAM)
python3 scripts/firered/nav.py --rom /tmp/pokefirered_modern.gba \
  --map /tmp/pokefirered_modern.map --outdir /tmp/s --in /tmp/base0/room.bin \
  --frames 400 --script "10-25:RIGHT;60-140:LEFT" --pos 50 --out /tmp/base0/1f.bin

# porta 4:0 -> 3:0
python3 scripts/firered/nav.py --rom /tmp/pokefirered_modern.gba \
  --map /tmp/pokefirered_modern.map --outdir /tmp/s --in /tmp/base0/1f.bin \
  --frames 700 --script "20-40:UP;80-100:LEFT;140-240:DOWN" --pos 60
```

O log deve mostrar `mapa=4:1` → `mapa=4:0` → `mapa=3:0`.

## Por que isso importa

O fork rejeitado tinha portas e escadas quebradas. Aqui, na base pura, elas funcionam — e o motivo
do defeito anterior ficou claro: warp no FireRed depende do **behavior do metatítulo**, e vários
behaviors de escada são **direcionais**. Quem só troca o gráfico do mapa (sem o metatítulo certo)
ganha uma escada decorativa. Isso vira regra de teste para todas as etapas seguintes.
