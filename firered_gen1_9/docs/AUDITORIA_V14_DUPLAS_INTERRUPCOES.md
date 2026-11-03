# V14 — auditoria de duplas, flinch, confusão e paralisia

**03/11/2026 — ampliação de testes, sem alteração do motor.** Base de trabalho: motor v14 identificado por SHA-256, mGBA libretro 0.10.5, exclusivamente estados sintéticos. Não foram usados saves pessoais.

## Escopo

Esta etapa amplia a validação da correção de PP de Rollout/Ice Ball entregue no [motor v14](MOTOR_V14.md). Não cria outro patch nem moderniza todas as mecânicas de status.

A nova suíte `tests/test_motor_v14_interruptions_mgba.py` tem **sete testes de integração**, com **22 subcasos dirigidos**:

- Quatro testes de duplas: 16 subcasos, cobrindo usuários nos bancos 0, 1, 2 e 3.
- Três testes de interrupções naturais em singles: seis subcasos, para os dois golpes.

**21/21 verificações concluídas nesta etapa, sem testes pulados.** Não foi demonstrado novo defeito nos cenários cobertos: a isenção de PP ficou restrita ao usuário bloqueado em duplas, e os três tipos de interrupção natural encerraram a sequência sem PP extra. O v14 permanece inalterado; não há motivo demonstrado aqui para criar v15.

## 1. Duplas — jogadores nos bancos 0 e 2

Para cada golpe, Rollout (205) e Ice Ball (301), o teste percorre a matriz controlada:

| Usuário | Alvo selecionado pela interface |
|---:|---:|
| 0 | 1 |
| 0 | 3 |
| 2 | 1 |
| 2 | 3 |

O jogador escolhe o golpe e o alvo por botões. O aliado usa Splash e é mais lento que o usuário da sequência. Os adversários dispõem de Splash/Protect; o teste não escreve um estado de proteção artificial nem força a decisão da AI.

Como a AI pode proteger-se antes de a sequência começar ou falhar em Proteções consecutivas, a execução acompanha até dez turnos e exige um **bloqueio real de continuação já ativa**. Não confunde primeiro uso bloqueado com continuação:

- Antes de existir trava, cada novo uso desconta um PP.
- Com trava prévia, a continuação não desconta outro PP, inclusive quando Protect a interrompe.
- O golpe atinge somente o alvo selecionado quando causa dano.
- No bloqueio, não há dano, a trava termina e o PP do usuário permanece.
- **Os três outros bancos gastam seus próprios PPs normalmente**, inclusive o aliado lento que age depois do usuário bloqueado.
- O usuário escolhe Tackle em seguida: o PP de Tackle cai de 10 para 9, sem consumir outro PP de Rollout/Ice Ball.

Essa matriz cobre a correção nas quatro combinações de atacante/alvo inimigo controladas pelo jogador; não é uma matriz de todos os alvos possíveis do motor (incluindo aliados, redirecionamentos ou troca de alvo).

## 2. Duplas — adversários nos bancos 1 e 3

Para cada golpe e banco inimigo, há dois valores iniciais de PP: **10 e 1**. O alvo da AI é **observado**, não escolhido pelo teste. Ambos os jogadores selecionam Protect no turno da interrupção, para bloquear o ataque independentemente de qual deles é escolhido.

### Com PP positivo

1. Primeiro impacto a potência 30: 10→9 PP, trava ativa.
2. Continuação bloqueada: permanece 9 PP, sem dano, trava encerrada.
3. Novo uso: 9→8 PP, novo impacto a potência 30.

### Com um PP inicial

1. Primeiro impacto: 1→0 PP, trava ativa.
2. Continuação bloqueada: permanece zero, trava encerrada, sem underflow.
3. Próxima ação: Struggle, sem restaurar PP nem a trava.

Em ambos os casos, o outro inimigo e os dois jogadores continuam pagando seus próprios PPs. São conferidos os quatro conjuntos de PP em batalha e nas equipes criptografadas, os checksums e o HP correspondente nas equipes.

**Limite:** esses casos cobrem usuários inimigos 1/3 e os alvos realmente escolhidos pela AI; não comprovam cada combinação inimigo→jogador. Também não incluem todas as combinações simultâneas de duas sequências travadas.

## 3. Observação do marcador de isenção

O teste avança um frame por vez, inclusive durante a escolha de ações e confirmação de mensagens. Registra cada transição de zero para `HITMARKER_NO_PPDEDUCT` (`0x800` em `0x0202160C`).

No turno de bloqueio de uma continuação, exige exatamente o registro:

`(atacante esperado, alvo protegido, golpe 205/301, cursor 0x08186349)`

O alvo controlado deve coincidir com o escolhido na interface; nos casos da AI, deve ser um dos jogadores. Ao voltar ao menu, o marcador precisa estar limpo. Os gastos de PP dos outros bancos e de Tackle no turno seguinte fornecem controles funcionais adicionais.

Isso é **observação por frame e verificação dos efeitos**, não instrumentação de cada instrução da CPU ou prova de ausência de qualquer transição intermediária possível em todos os contextos.

## 4. Outras interrupções — estados criados por golpes reais

Em singles, o adversário começa com um impacto normal a potência 30 e fica travado. O jogador, mais rápido, usa um dos golpes abaixo; não se injeta o status correspondente nem se zera a trava manualmente.

| Origem | Interrupção exigida | Evidência adicional |
|---|---|---|
| **Stomp (23)** | flinch durante uma continuação | bit `flinchImmobility` observado durante a ação |
| **Confuse Ray (109)** | autoataque por confusão durante uma continuação | bit `confusionSelfDmg`, perda de HP do próprio adversário e nenhum impacto no jogador |
| **Thunder Wave (86)** | imobilidade por paralisia durante uma continuação | bit `prlzImmobility` e status de paralisia preservado |

Para **Rollout e Ice Ball**, exige-se:

- PP do golpe preservado quando a ação é impedida.
- Nenhum dano desse golpe no jogador no turno interrompido.
- Trava removida ao fim da ação.
- Nenhum acionamento observado do marcador de isenção `0x800` nesses desvios.
- Tackle do jogador continua gastando PP no turno seguinte.
- O próximo impacto que o adversário consegue executar começa de novo a **potência 30** e cobra um novo PP.

Confusão/paralisia podem impedir mais ações. O teste espera o próximo impacto dentro de um limite, sem curar artificialmente o adversário. As sequências usam fixtures e entradas determinísticas; **não medem as probabilidades** de flinch, autoataque ou imobilidade, nem a redução de velocidade por paralisia.

## 5. Preparação corrigida durante a investigação

A primeira execução dos casos com usuário inimigo falhou antes do cenário de interrupção: não havia impacto nem desconto de PP, e o último golpe dos inimigos terminava em `0xFFFF`.

A primeira ação inimiga dessa fixture de duplas usa o **slot 1**. A preparação inicial colocava o único golpe com PP no slot 0 e deixava o slot 1 sem PP. A preparação foi corrigida para colocar o golpe atacante — e o Splash do aliado inimigo — no slot 1, com PP válido e movimentos distintos. Isso removeu o caminho artificial de falta de PP.

Não se mudou a ROM, o alvo da AI, o histórico ou o estado de trava para contornar o resultado. A execução final exige o primeiro impacto real antes de testar a interrupção. **A falha inicial era da preparação e não demonstrava um defeito novo no v14.** Os resultados da tentativa inicial e dos probes não entram na contagem final.

## 6. Referências e diagnóstico completo

A análise do fluxo não deve parar na função C de cancelamento. Em particular, o código nativo contém uma chamada comentada de CancelMultiTurnMoves no ramo de paralisia; o **script de paralisia chama `cancelmultiturnmoves` depois**. O script de autoataque por confusão também cancela a sequência. A ausência da chamada naquele ponto isolado do C não é, por si só, evidência de bug.

Referências fixadas:

- pret/pokefirered `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`: [flinch, confusão e paralisia no cancelador](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_util.c#L1361-L1449), [scripts de paralisia/confusão](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/data/battle_scripts_1.s#L3713-L3755) e [bits de ProtectStruct](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/include/battle.h#L176-L208).
- Showdown `035c1a1f3c2ed286cda4c0d8623800699cd2c1c0`: [Rollout e duração da trava](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L15360-L15425), [condições de status](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/conditions.ts) e [PP durante golpe travado](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/battle-actions.ts#L335-L349).

As referências apoiam a expectativa; os fatos sobre esta ROM são os resultados mGBA. Não houve teste em cartucho Scarlet/Violet.

## 7. Execução e reprodução

| Execução final | Resultado | Tempo |
|---|---:|---:|
| Nova suíte de duplas/interrupções | **7/7**, com 22 subcasos | 406,744 s |
| Build v14 + treino EV/IV | **14/14** (5 + 9) | 16,693 s |

**Total: 21/21, nenhum pulado.** A execução inicial com a fixture inconsistente e as repetições exploratórias não foram somadas.

```sh
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V14_ROM=/caminho/motor_v14.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest test_motor_v14_interruptions_mgba -v

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V14_BASE=/caminho/motor_v13.gba \
TREINO_TEST_ROM=/caminho/motor_v14.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest test_motor_v14 test_treino_ev_mgba -v
```

Nesta etapa não foram reexecutadas integralmente as 14 verificações dirigidas e as 33 regressões herdadas da entrega original do v14. Seus resultados anteriores não são somados aos atuais. A suíte nova amplia a cobertura; não altera as fábricas históricas compartilhadas nem relaxa a validação dos hashes.

SHA-256 v14, conferido antes/depois das classes de integração:

`2302ba1c88194fec190d0da062f91380ba062ee06e5a4a626902767412a9682c`

Nenhum aplicador, payload, catálogo ou formato de save mudou. Continuam 15.008 aprendizados, 708/729 omissões restauradas e quatro golpes/21 registros adiados. Não há ROM v15 nesta etapa. Drive não atualizado.

## Próximas lacunas

- Encore/Disable e seus efeitos sobre seleção, PP e reinício.
- Histórico após pivôs/trocas forçadas, redirecionamento e substituição de alvos durante a sequência.
- Combinações adicionais em duplas: dois usuários travados ao mesmo tempo, Pressure/Detect com todos os alvos, derrotas e substituições.
- Taxas e durações modernas de status, habilidades/itens especiais, campanha/link/Teachy TV e fidelidade integral SV.
