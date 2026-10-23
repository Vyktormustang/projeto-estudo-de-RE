# Evidências do build Gen 1–9

Capturas feitas no emulador **mGBA 0.10.5** (compilado neste ambiente) rodando
`pokemon_emerald_expansion_gen1-9.gba`.

| Arquivo | Frame | O que mostra |
|---|---|---|
| `01_gamefreak.png` | 600 | tela de abertura **GAME FREAK** |
| `02_titulo.png` | 7200 | título **Pokémon EMERALD VERSION** |
| `03_teclado_nome.png` | 9600 | teclado "YOUR NAME?" (jogo já iniciado) |
| `04_pronto.png` | 12000 | "All right, are you ready?" com o protagonista |

Os frames são contados desde o reset. Do 1200 ao 9000 o botão **A** foi
apertado periodicamente para pular a intro, e **START** no 9000 para entrar no
menu — ou seja, o jogo responde a input normalmente.

Reproduzir:

```bash
python3 /tmp/boot_test.py rom/pokeemerald_expansion_gen1-9.gba 7200
python3 /tmp/jogar.py     rom/pokeemerald_expansion_gen1-9.gba 12000
```
