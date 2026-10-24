# T5 — Golpes e habilidades: descrições em PT-BR (provas em jogo)

ROM: pokefirered (pret) com T1-T5 aplicados, build MODERN=1.
md5 da ROM desta prova: 5ae2e6ea4be9e98a22789da0ab91d255 (muda a cada rebuild).

Decisão vigente (pedido do usuário): NOMES de golpes, itens e habilidades
ficam em INGLÊS; apenas as DESCRIÇÕES são traduzidas.

O que foi traduzido nesta etapa:
- 796 descrições de golpes (`src/move_descriptions.c`), limite 21 chars/linha;
- 321 descrições de habilidades (`src/data/text/abilities.h`), 1 linha <=29 chars.

Dicionários versionados:
- `scripts/firered/traducao_golpes_ptbr.py`
- `scripts/firered/traducao_habilidades_ptbr.py`
Aplicados por `scripts/firered/aplicar_traducao.py --write` (0 problemas).

## Provas (tela de resumo, SYLVEON na equipe de rota 1)

1. `01_golpe_roost.png` — página GOLPES: golpe ROOST (nome inglês) com a
   descrição "Restaura metade do HP máximo do usuário." em PT-BR.
2. `02_habilidade_cute_charm.png` — página ATRIBUTOS: habilidade CUTE CHARM
   (nome inglês) com descrição "Apaixona ao contato." em PT-BR.
3. `03_golpe_miracle_eye.png` — golpe MIRACLE EYE com descrição
   "Anula a evasão e as imunidades do tipo Sombrio." em PT-BR.

Receita de navegação (nav.py, estado /tmp/e4estado/rota1.bin):
`20-26:START;80-86:DOWN;110-116:A;240-246:A;320-326:A;500-506:RIGHT`
(ATRIBUTOS) e `...;600-606:RIGHT;700-706:A` (GOLPES, seleciona o 1º golpe).
