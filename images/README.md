# Calendários 2026 + 2027 (dois anos, empilhados)

Imagens com **dois calendários anuais completos**, cada um em formato paisagem
ocupando a largura toda, **um em cima e outro embaixo**: 2026 na metade
superior e 2027 na metade inferior. Cada ano traz os 12 meses em grade 4×3,
com nomes em português, semana começando no **domingo** e fins de semana
destacados.

## Arquivos

| Arquivo | O que é |
|---|---|
| `calendario-biblico-2026-2027.png` | **Versão com tema bíblico** (1600×2000). Pergaminho, tinta sépia, dourado, capitular Cinzel, versículo do ano e cruz ornamental. Datas conferidas por código. |
| `calendario-2026-2027.png` | Versão minimalista/suíça (1600×2000), mesma estrutura. |
| `calendario-2026-2027-ilustrado-ia.png` | Versão ilustrada gerada por IA (1122×1402). Bonita, mas **contém erros de alinhamento** — não usar como calendário de referência. |

## Tema bíblico — elementos

- **Paleta**: pergaminho (`#F4ECDB`), tinta sépia (`#3A2C20`), dourado
  (`#B08D44`) e vinho para fins de semana (`#802E28`).
- **Tipografia**: Cinzel (capitular romana, inspirada em inscrições lapidares)
  para anos/meses e EB Garamond (serifada clássica, com algarismos *lining*)
  para dias e versículos.
- **Versículo por ano**, em itálico, sob o número do ano:
  - 2026 — “O Senhor é o meu pastor; nada me faltará.” (Salmos 23:1)
  - 2027 — “Eis que faço novas todas as coisas.” (Apocalipse 21:5)
- **Rodapé** — “Lâmpada para os meus pés é a tua palavra · Salmos 119:105”.
- **Ornamentos**: cruz latina sobre cada ano, filetes duplos, florões,
  losango central na divisória e cantos ornamentados nos painéis.
- **Textura**: ruído suave + vinheta quente geradas com NumPy (pergaminho).

## Gerar / mudar o ano

```bash
pip install pillow numpy
python3 scripts/gen_calendario_biblico.py 2026 2027 images/calendario-biblico-2026-2027.png
python3 scripts/gen_calendario_dois_anos.py  2026 2027 images/calendario-2026-2027.png   # versão minimalista
```

Argumentos: `ano1 ano2 [saida.png]`. Para trocar o versículo de um ano, edite o
dicionário `VERSICULOS` no script.

## Fontes

`assets/fonts/` contém Cinzel e EB Garamond (SIL Open Font License — ver
`OFL-Cinzel.txt` e `OFL-EBGaramond.txt`), instanciadas das fontes variáveis
oficiais do repositório google/fonts. Os arquivos `*-LF.ttf` são o EB Garamond
com os algarismos remapeados para a variante *lining* (sem eles, o “1” de
“23:1” e o “0” saem em estilo oldstyle, parecendo minúsculas).

## Verificação

- Semana iniciando no domingo (`calendar.Calendar(firstweekday=6)`).
- Grade dos 24 meses comparada programaticamente com
  `calendar.monthdayscalendar` → **idêntica**.
- Meses com 6 semanas (ex.: maio/2026, agosto/2026, janeiro/2027) exibem a
  6ª linha corretamente.
- Feriados não estão marcados: as imagens são calendários-base.
