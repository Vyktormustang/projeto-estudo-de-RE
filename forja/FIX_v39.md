# FIX do v39 — checklist e protocolo de regressão

O v38 saiu em três builds em sequência (`v38.0` → `v38.0_FIXADO` → `v38.0_FIXADO_v2`),
o que indica correções empilhadas sem documentação de causa-raiz. Sem o
código-fonte e sem o relato do sintoma, não há como "consertar" com honestidade:
conserto às cegas viraria um quarto build empilhado.

## Protocolo (usado assim que o sintoma chegar)

1. **Reproduzir** — descrever o passos mínimos (tela, ação, resultado esperado ×
   obtido). Se possível, um print. Isso vira um teste em `web/src/*.test.ts`
   que **falha** antes do fix (red).
2. **Localizar** — com o fonte no repositório, isolar o módulo culpado no núcleo
   (`forja.ts` ou equivalente) em vez de remendar a UI.
3. **Corrigir** — a menor mudança que faz o teste passar (green).
4. **Blindar** — teste de regressão permanente + entrada no
   `CHANGELOG` com causa-raiz, não com "fix".
5. **Provar no dispositivo** — o APK do CI é a evidência: Release com SHA-256.

## O que já sei sobre o v38 (evidência do Drive)

| Dado | Valor |
|---|---|
| Builds | `v38.0` (15:26), `v38.0_FIXADO` (18:19), `v38.0_FIXADO_v2` (18:55) — 29/10 |
| Tamanho | 552736 → 536169 → 536265 bytes (o "FIXADO" **removeu ~16 KB**) |
| Certificado | mudou em relação ao v15 (instalação limpa) |

Leitura provável (HIPÓTESE, não fato): o "FIXADO" removeu código/assets, isto é,
cortou algo que quebrava (crash ou tela branca) em vez de corrigi-lo — e o `_v2`
ajustou o resto. Enquanto isso não for confirmado, o fix do v39 começa por:
detectar crash/tela-branca no WebView (handler global de erro + fallback visível),
para que uma falha de runtime nunca mais exija um APK novo.

## Perguntas que destravam o fix (responder 1 ou 2)

1. Qual foi o **sintoma** que motivou o `FIXADO`? (ex.: tela preta ao abrir,
   xadrez travando, Cofre perdendo dados, lição não abrindo…)
2. O que **ainda está quebrado** no `FIXADO_v2`?
3. Onde está o **código-fonte** (repo GitHub ou ZIP)? → é o bloqueio real do v39.
