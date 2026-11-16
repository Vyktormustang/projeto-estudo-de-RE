# Calendários 2026 + 2027 (dois anos, empilhados)

Imagens com **dois calendários anuais completos**, cada um em formato paisagem
ocupando a largura toda, **um em cima e outro embaixo**: 2026 na metade
superior e 2027 na metade inferior. Cada ano traz os 12 meses em grade 4×3,
com nomes em português, semana começando no **domingo** e fins de semana
destacados.

## Arquivos

| Arquivo | O que é |
|---|---|
| `calendario-2026-2027.png` | **Versão oficial** (1600×2000). Gerada por código com os dias alinhados e conferidos contra o `calendar` do Python. |
| `calendario-2026-2027-ilustrado-ia.png` | Versão ilustrada gerada por IA (1122×1402). Bonita, mas **contém erros de alinhamento** — não usar como calendário de referência. |

## Por que a versão de IA não serve como calendário

Modelos de imagem erram a aritmética de datas. Na imagem ilustrada há meses com
o dia 1 na coluna errada (por exemplo, junho/2027 deveria começar na terça e
aparece na segunda; agosto/2027 também sai deslocado). A versão em código é
calculada, não "desenhada de memória".

## Regenerar / mudar o ano

```bash
pip install pillow
python3 scripts/gen_calendario_dois_anos.py 2026 2027 images/calendario-2026-2027.png
```

Argumentos: `ano1 ano2 [saida.png]`. Sem argumentos, gera 2026/2027 no caminho
padrão. Para outros anos basta trocar os números.

## Detalhes de verificação

- Semana iniciando no domingo (`calendar.Calendar(firstweekday=6)`).
- Grade de cada mês comparada programaticamente com `calendar.monthdayscalendar`
  para os 24 meses → resultado idêntico.
- Meses com 6 semanas (ex.: maio/2026, agosto/2026, janeiro/2027) exibem a
  6ª linha corretamente.
- Feriados não estão marcados: a imagem é um calendário-base.
