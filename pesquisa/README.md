# pesquisa/ — base de conhecimento das trilhas

Índice das análises de produto/referência que alimentam a engenharia reversa deste repositório.

| Trilha | Documento | O que contém | Data |
|---|---|---|---|
| **chess.com (site)** | [`chesscom/jogabilidade.md`](chesscom/jogabilidade.md) | Jogabilidade: regimes de jogo, ciclo da partida, relógio, pre-move × lance condicional, matriz de fins/empates, variantes, rating, fair play, acessibilidade, divergências e checklist para RE do APK | 2026-10-25 |

## Como estas notas se relacionam com o código

- `android_re/` — pipeline que **extrai** as funcionalidades de um APK (manifest, DEX, strings, ELF/JNI).
  O ruleset `android_re/rules/chess.json` é a tradução direta do checklist do §14 do documento de
  jogabilidade: cada teoria sobre "como o app se comporta" vira um padrão verificável no binário.
- Contrato de verdade: `CONFIRMADO` / `PROVÁVEL` / `INFERIDO` / `DESCONHECIDO`, sempre com fonte e data.
- Nada aqui contém asset protegido: só análise, links e medições.
