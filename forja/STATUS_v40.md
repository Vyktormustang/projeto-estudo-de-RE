# FORJA v40.0.0 — ciclo de dia e noite

> Base: v39.0.0 (fábrica de APK assinado + núcleo do xadrez testado).
> Este ciclo adiciona a **primeira peça de experiência do usuário** que o v39 não
> tinha: o app muda de cara ao longo do dia.

## Resumo em uma linha

O FORJA agora tem **relógio de jogo**: cinco fases (madrugada, amanhecer, dia,
entardecer, noite), luminosidade contínua e uma paleta por fase — tudo em funções
puras cobertas por **38 testes novos** (32 de núcleo + 6 de UI em jsdom).

## O que entrou

| Arquivo | O que é | Testes |
|---|---|---|
| `forja/web/src/dia-noite.ts` | Núcleo puro: fases, luminosidade, paletas, formatação, avanço do relógio | 32 |
| `forja/web/src/dia-noite.test.ts` | Casos de fronteira, laço completo de 1 440 min, anti-salto | — |
| `forja/web/src/ui-dia-noite.test.ts` | Monta `main.ts` em **jsdom** e lê o CSS que chega ao cartão | 6 |
| `forja/web/src/main.ts` | Cartão "Ciclo de dia e noite" + botões −1 h / Agora / +1 h | — |
| `forja/web/src/style.css` | Cartão do céu: transição de paleta, barra do dia, marcador, sol | — |

Total da suíte: **58 testes verdes** (20 herdados + 38 novos) e `tsc --noEmit`
limpo.

## Como o ciclo funciona (números, não adjetivos)

Fronteiras em minutos desde a meia-noite:

| Faixa | Fase | Luminosidade |
|---|---|---|
| 00:00–04:00 | Madrugada | 18 % |
| 04:00–06:00 | Amanhecer | sobe 18 % → 100 % |
| 06:00–17:00 | Dia | 100 % |
| 17:00–19:00 | Entardecer | cai 100 % → 22 % |
| 19:00–23:00 | Noite | 22 % |
| 23:00–24:00 | Madrugada | 18 % |

- A curva é **smoothstep entre keyframes**, não degrau: um teste varre os 1 440
  minutos e exige que nenhum passo de 1 minuto mude mais de 5 % da escala —
  é o que impede "piscada" na virada do dia.
- `normalizarMinutos` aceita lixo (NaN, `Infinity`, string, `null`) e devolve um
  minuto válido; `-1440 % 1440` dá `-0` em JS e o módulo normaliza para `0`
  (regressão real encontrada por teste, ver abaixo).
- O relógio entra no app por **uma única porta** (`minutosDaData(Data)`), o que
  mantém o resto do módulo sem `Date` e 100 % determinístico.

## Prova de UI sem navegador

Não há Chrome no sandbox (o download é bloqueado), então a UI é validada em
**jsdom**: `ui-dia-noite.test.ts` importa o `main.ts` de verdade, clica nos
botões e lê `--ceu-fundo`, `#ceu-hora`, `#ceu-marcador` etc.:

```
✓ src/dia-noite.test.ts      (32 tests)
✓ src/forja.test.ts          (20 tests)
✓ src/ui-dia-noite.test.ts   ( 6 tests)
  Test Files  3 passed (3)
       Tests  58 passed (58)
```

Esse teste **pegou dois bugs reais** antes de qualquer build:
`Object.is(-0, 0) === false` na normalização e a expectativa errada de patamar
em 21:00 (a curva já está na rampa 19:00 → 23:00).

## Preview

O dev server (`npx vite`) agora aceita hostnames dinâmicos
(`server.allowedHosts: true`) — antes, qualquer preview fora de `localhost`
recebia **403 Blocked request** do Vite. Isso afeta **só** o dev server; o APK
continua servindo de `file:///android_asset/`.

## O que o v40 NÃO faz (honesto)

- **Não** traz a UI/conteúdo do v38 — o bloqueio continua o mesmo: o Drive só
  tem APKs, não o fonte (ver `FIX_v39.md`).
- **Não** existe build assinado do 40.0.0 neste repositório ainda: o CI assina a
  cada push que toque `forja/**`; o `version.json` já está em `40.0.0` / `4000`,
  então a próxima run publica `Forja_Apice_v40.0.0.apk`.
- O ciclo **não** pune o usuário de madrugada (decisão de produto: só escurece).

## Próximo passo sugerido

Somar os **minutos de estudo** ao relógio: cada lição concluída avança o dia, de
modo que a paisagem vire recompensa — `minutosDecorridos()` e `avancar()` já
existem para isso e estão testados.
