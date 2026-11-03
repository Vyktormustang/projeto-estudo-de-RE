# Auditoria v15 — histórico após pivôs e trocas forçadas

**03/11/2026 — FireRed Gen 1–9 / VYK-57.** Auditoria sobre a v15 exata, somente com equipes e estados sintéticos. **Nenhuma mudança na ROM; não há v16 nesta etapa.**

## Resultado e ressalva principal

O histórico usado por Eerie Spell é limpo nas trocas efetivamente realizadas pelos quatro pivôs e pelos quatro golpes de troca forçada testados. O entrante não herda o último golpe do ocupante anterior; depois de agir, passa a ter histórico próprio. Os PPs persistentes de ambos os membros são preservados nas saídas e retornos.

**Foi encontrado um defeito distinto, ainda aberto:** Dragon Tail e Circle Throw podem atingir e causar dano, mas não forçar a troca quando o atacante tem nível inferior ao alvo, mesmo em batalha com flag de treinador e reserva válida. A v15 ainda usa a probabilidade legada de `TryDoForceSwitchOut`. A referência moderna consultada não aplica essa chance de falha por nível nesse contexto.

**25 verificações concluídas, sem skips**, incluindo **uma caracterização negativa desse defeito em dois subcasos**. O `ok` desse teste significa que o defeito foi reproduzido, **não que o phazing esteja inteiramente correto**. A falha não foi apagada nem tratada como comportamento moderno desejável.

## Matriz executada

Arquivo novo: `tests/test_motor_v15_switch_history_mgba.py`, cinco métodos e 22 subcasos.

| Grupo | Casos | Evidência |
|---|---:|---|
| U-turn 369, Volt Switch 517, Flip Turn 708, Parting Shot 571 | 4 × 2 ordens = 8 | Pivô antes/depois de Eerie, entrada sem histórico, nova ação e retorno manual |
| Roar 46, Whirlwind 18, Dragon Tail 521, Circle Throw **508** sobre o adversário | 4 | Ida e volta forçadas, Eerie no entrante antes da primeira ação, dreno correto depois da nova ação |
| Mesmos quatro golpes sobre o jogador | 4 | Ida e volta, atacante de nível 10 no controle positivo, histórico zerado e PPs próprios preservados |
| Suction Cups bloqueando os quatro golpes | 4 | Sem troca, sem apagar histórico; Eerie posterior ainda drena o golpe registrado |
| Defeito de nível v15: Dragon Tail/Circle Throw | 2 | Atacante de nível inferior; impacto confirmado por HP, reserva viva e falha de troca em turnos determinísticos |

Os números são IDs **desta ROM**, não necessariamente os IDs oficiais. Circle Throw é 508; Dragon Tail é 521; Eerie Spell é 720.

### Pivôs e Eerie Spell

O jogador começa com `(Splash, pivô, Eerie Spell, Tackle)`, 20 PP por slot. O reserva conhece `(Tackle, pivô, Splash, Growl)`, com PP `(13,12,11,10)`. Compartilhar os golpes relevantes permite detectar tanto um histórico indevidamente herdado quanto um fallback incorreto para o primeiro slot.

1. Splash registra histórico naturalmente. Se o jogador é mais rápido, Eerie drena seus PP no mesmo turno; se é mais lento, Eerie age antes de haver histórico.
2. No turno do pivô, o Pokémon que sai termina com **`(16,19,20,20)`** nas duas ordens. Na ordem lenta, Eerie drena o Splash anterior antes da saída; na rápida, atinge o entrante depois da troca, mas **não drena seus PP**.
3. O entrante tem histórico zero e PP **`(13,12,11,10)`**. Seu HP diminui somente quando Eerie age depois da troca.
4. Tackle registra histórico próprio; uso + Eerie deixam **`(9,12,11,10)`**.
5. Retorno manual ao membro inicial limpa novamente o histórico e conserva os PPs de ambos os membros.

### Trocas forçadas e Eerie Spell

Em fixture de singles com contexto de treinador e dois membros válidos por lado, o adversário primeiro usa Eerie Spell. O jogador o força a sair depois de sua ação. O reserva também conhece Eerie, de modo que um histórico herdado seria observável por PP.

- Após a troca, histórico do banco adversário é zero; o membro que saiu conserva **18 PP de Eerie** e o entrante conserva `(20,12,0,0)`.
- Eerie do jogador atinge antes da primeira ação do entrante: apenas o gasto próprio posterior da IA é permitido. A IA pode usar Splash ou Eerie, mas não se aceitam perdas adicionais de três PP.
- No turno seguinte, o dreno de três PP é exigido exatamente no golpe registrado anteriormente, além de um PP pela ação atual. O teste calcula os dois descontos separadamente, inclusive quando a IA muda de golpe.
- Nova troca forçada traz de volta o membro inicial, com histórico zero e seus 18 PP preservados. Eerie antes de sua próxima ação não drena; o uso próprio deixa 17 PP.

No controle de Suction Cups, o adversário não sai, conserva o histórico de Eerie e cai de 18 para **14 PP** no turno seguinte: três drenados + um pelo próprio uso. Isso distingue limpeza por troca real de uma limpeza indevida apenas pela tentativa de phazing.

## Defeito confirmado: chance legada de falha por nível

As fixtures negativas usam o adversário original do encontro, de nível inferior aos dois membros do jogador (nível 10). Há flag de treinador, reserva viva, nenhuma condição inicial de Suction Cups/Ingrain/Substitute no alvo e acurácia elevada para isolar o histórico de misses. Não se escreve no histórico nem se força a troca por memória.

| Golpe adversário | Slot ativo do jogador após T1 / T2 / T3 | Falha confirmada |
|---|---|---|
| Dragon Tail 521 | **0 / 1 / 0** | T1 causa dano, mas não troca |
| Circle Throw 508 | **1 / 1 / 0** | T2 causa dano, mas não troca |

Nos turnos sem troca, o HP do alvo diminui, o adversário gasta exatamente um PP, a reserva continua viva e o histórico da ação do alvo permanece. Nas trocas seguintes, o histórico é zerado normalmente. Portanto, **não é um defeito de limpeza do histórico nem uma simples falha de acurácia**.

Os controles positivos sobre o jogador usam um atacante sintético nível 10, com EXP/checksum coerentes, para testar ida e volta sem essa probabilidade legada. A caracterização negativa mantém o atacante original de nível inferior e as expectativas defeituosas explicitamente separadas.

### Caminho identificado na ROM e no código

- O tail do motor v10 em ROM `0x10CD300` chama o comando `0x8F`, com retorno de falha para `0x081853F6` (fim do golpe).
- Na tabela atual, o ponteiro em `0x10CFE3C` continua sendo **`0x08060DD1`**, o comando nativo.
- A rotina em **`0x08060D18`** lê os níveis de `BattlePokemon + 0x2C`; a comparação em `0x08060D38` desvia para a chamada de RNG em `0x08060D5A` se o atacante tem nível inferior. A decisão em `0x08060D82..84` pode tomar o retorno de falha.
- O código de referência `TryDoForceSwitchOut` implementa a condição equivalente: `((random8 * (nivel_atacante + nivel_alvo) >> 8) + 1) <= nivel_alvo / 4`. `Cmd_forcerandomswitch` também chama esse helper no ramo de treinador.
- O hook do motor v10 verifica dano/alvo vivo, Substitute, Suction Cups e Ingrain antes de chamar esse tail, mas não remove a checagem legada de nível.

A chamada é compartilhada com outros caminhos de phazing. A reprodução negativa desta etapa confirma **Dragon Tail e Circle Throw**; o alcance dinâmico sobre outros golpes/contextos não foi esgotado. Não se deve confundir uma correção para batalhas de treinador com a regra de encerramento de encontros selvagens.

## Execução final

mGBA **0.10.5**, saídas finais com código zero:

| Suíte | Resultado | Tempo |
|---|---:|---:|
| Nova auditoria de pivôs/phazing | **5/5**, incluindo a caracterização negativa | 129,135 s |
| Histórico anterior sobre v15 + estrutura/build v15 + treino EV/IV | **20/20** (6 + 5 + 9) | 97,630 s |
| Total desta etapa | **25/25 verificações, sem skips** | |

Os **76 testes da entrega original v15 não foram reexecutados integralmente** nesta etapa e não foram somados a esses 25.

Correções e diagnóstico durante o desenvolvimento dos testes:

- A primeira rodada usou 509 para Circle Throw; a ROM usa 508. Corrigiu-se o teste, não o catálogo.
- Um controle esperava apenas o consumo próprio de Eerie do jogador, mas o entrante podia responder com seu próprio Eerie e drenar outros três PP. A asserção passou a exigir o resultado exato conforme a ação realmente registrada da IA.
- Elevar acurácia não resolveu as falhas de Dragon Tail/Circle Throw sobre o jogador; a observação de dano e a inspeção da rotina nativa identificaram a checagem de nível. Ela permanece registrada como defeito, sem relaxar a expectativa moderna de sucesso.
- Execuções exploratórias e tentativas anteriores não integram a contagem final.

Em todos os finais de turno, a suíte verifica retorno ao menu, PP de batalha versus equipe criptografada/checksum, HP persistente e ausência do marcador de isenção de PP `0x800`. Os estados são criados na v15; não são reutilizados entre versões. Stats/movesets/HP/habilidades iniciais são condições sintéticas, não dados de campanha. Trocas são executadas por comandos de batalha e entradas de interface, sem escrever índices ativos ou histórico após o começo dos turnos.

## Reprodução

Na raiz do repositório, com ROM própria já identificada:

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V15_BASE=/privado/motor_v14.gba
export MOTOR_V15_ROM=/privado/motor_v15.gba
export MGBA_CORE=/privado/mgba_libretro.so
export TREINO_TEST_ROM="$MOTOR_V15_ROM"
python3 -m unittest test_motor_v15_switch_history_mgba -v
python3 -m unittest test_motor_v15_regressions.MotorV15HistoryTests \
  test_motor_v15 test_treino_ev_mgba -v
```

SHA-256 v15 permanece **`a6b454f7cbafad8c05e1b8aa2028087a596bbeff4f0184c826a92ebb7e554147`**, 33.554.432 bytes. Payload e aplicador não foram alterados. Catálogo permanece em 15.008 registros; nenhuma ROM/save pessoal ou comercial foi incluída no Git. **Drive não atualizado.**

## Próxima correção e lacunas

Próximo trabalho: eliminar a chance legada por nível **no contexto apropriado de batalhas de treinador**, mantendo seleção de reserva válida, bloqueios por habilidades/estado, falha sem reserva e regras distintas de encontros selvagens. Reexecutar a reprodução negativa contra a base e exigir sucesso na saída corrigida, com fixtures novas para cada versão. Ainda não existe implementação v16 nesta etapa.

Não foram auditados aqui pivôs do adversário, todos os bancos em duplas, redirecionamento, múltiplos reservas, KO/hazards durante a entrada, Eject Button/Emergency Exit, Baton Pass/Shed Tail/Chilly Reception, todas as condições de falha dos pivôs ou toda a temporização de Encore/Disable em duplas. A campanha, link, Teachy TV e migração de saves pessoais continuam não certificados. **A engine permanece parcial.**

## Referências fixadas

- [Showdown `moves.ts`, commit 035c1a1](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts): Eerie Spell consulta `target.lastMove`; pivôs e `forceSwitch`.
- [Showdown `pokemon.ts`, mesmo commit](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/pokemon.ts): `clearVolatile` limpa `lastMove`.
- [Showdown `battle-actions.ts`, mesmo commit](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/battle-actions.ts): `forceSwitch`/`dragIn`, reserva válida e eventos de bloqueio, sem chance por nível.
- [pret `battle_script_commands.c`, commit ce6406d](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c): `TryDoForceSwitchOut` e `Cmd_forcerandomswitch`.
- [pret `battle_main.c`, mesmo commit](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_main.c): `SwitchInClearSetData` zera `gLastMoves`.
