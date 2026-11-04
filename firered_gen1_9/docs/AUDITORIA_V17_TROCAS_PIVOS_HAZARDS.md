# Auditoria v17 — trocas voluntárias e pivôs sob hazards, com aliado ativo

**Data:** 04/11/2026. **Escopo:** FireRed Gen 1–9, motor parcial v17, não o projeto histórico BAG_MOD.

## Resultado

**22/22 métodos distintos aprovados, sem skips**, incluindo quatro métodos novos / **32 cenários**. Nenhum novo defeito de engine demonstrado neste recorte. **ROM, payload e aplicador v17 inalterados; não há v18.** Os totais históricos de 23 métodos da auditoria anterior e de 46 da entrega original não foram somados aos desta etapa.

## Método e isolamento

Módulo: `tests/test_motor_v17_switch_pivot_hazards_mgba.py`. Reutiliza a fábrica de duplas, o observador por PID e os verificadores de integridade já existentes; desabilita os cinco métodos herdados para não duplicar descoberta. Define quatro métodos novos, com 32 subcasos:

| Método | Recorte | Subcasos |
|---|---|---:|
| Troca voluntária | Dois bancos do jogador × duas ordens × sobrevivência / KO no primeiro / KO no segundo hazard | 12 |
| Pivôs com sobrevivência | Quatro golpes × dois bancos/configurações de velocidade e ordem | 8 |
| Pivôs com KO | Mesmas oito configurações, com KO no primeiro hazard e escolha de outro reserva | 8 |
| Quatro hazards | Absorção, interrupção por KO, status, Speed e residual, por troca manual ou pivô | 4 |

A ROM tem SHA verificado antes e depois. mGBA 0.10.5/libretro; saves/estados exclusivamente sintéticos. A fixture inicial configura equipes, PP, atributos, velocidades e reservas. **Não há escrita de RAM entre as ações:** hazards são colocados por golpes reais e levados ao lado do jogador por Court Change, e as escolhas são feitas pela UI nativa.

Diferentemente da auditoria anterior de dois KOs simultâneos, esta preparação **não usa Disable nem Rock Slide**: os adversários só têm PP utilizável em Splash. Isso mantém o aliado e o retirado vivos e isola o efeito da troca. Não é um teste de decisões competitivas da IA ou de equipes/atributos legalmente obtidos em campanha.

Os dois jogadores começam com HP/maxHP 4.000; o reserva tem maxHP 400 e HP escolhido pelo cenário. Há outro reserva saudável, um ovo e uma posição vazia. O Pokémon retirado continua vivo. Não são testes de derrota ou de ausência de reservas elegíveis.

## Matriz de entrada

### Trocas voluntárias: 12 casos

Um dos bancos do jogador (0 ou 2) escolhe Pokémon pela tela de ações, tenta selecionar o aliado já ativo e recebe a rejeição nativa. Depois escolhe o reserva 2; quando ele cai, escolhe o reserva 3 para **o mesmo banco**. O outro jogador escolhe Splash no turno da troca.

| Ordem | HP inicial do primeiro reserva Fire | Eventos exigidos |
|---|---:|---|
| Spikes → Stealth Rock | 400 | 400 → 350 → 250 |
| Spikes → Stealth Rock | 50 | 50 → 0; não executar SR no morto |
| Spikes → Stealth Rock | 150 | 150 → 100 → 0 |
| Stealth Rock → Spikes | 400 | 400 → 300 → 250 |
| Stealth Rock → Spikes | 100 | 100 → 0; não executar Spikes no morto |
| Stealth Rock → Spikes | 150 | 150 → 50 → 0 |

Cada linha é executada nos dois bancos. Após o KO, o reserva Fire saudável recebe os dois danos na ordem preservada e termina com 250 HP. Este recorte usa **uma camada de Spikes**; as três quantidades de camadas pertencem à auditoria anterior e às regressões explicitamente listadas, não a uma matriz nova de trocas com todas as camadas.

### Quatro pivôs: 16 casos

IDs locais: U-turn **369**, Volt Switch **517**, Flip Turn **708**, Parting Shot **571**.

Para cada golpe:

- **Banco 0 rápido:** Speed 600, aliado 200, adversários 100; ordem SR → Spikes. O aliado ainda conserva o histórico de Court Change e não gastou o PP de Splash quando a primeira tela de seleção do pivô abre.
- **Banco 2 lento:** Speed 40, aliado 200, adversários 100; ordem Spikes → SR. Ao abrir a seleção, o aliado já usou Splash, com exatamente um PP gasto e histórico 150.
- Cada configuração é repetida com reserva sobrevivente (400 HP) e com KO no primeiro hazard (100 ou 50 HP, conforme a ordem), seguido de outra escolha.

**Não é um produto cartesiano completo:** velocidade e ordem estão acopladas ao banco nos pivôs. Não foram testados aqui banco 0 lento ou banco 2 rápido para todos os golpes, nem KO no segundo hazard em cada pivô.

Os três pivôs de dano precisam causar uma perda positiva, não letal, ao primeiro adversário; não se usa um valor calculado de dano para certificar toda a fórmula moderna. Parting Shot deve reduzir Attack e Special Attack do alvo de 6 para 5, sem perda de HP. O ator começa com Attack +2, mas o entrante deve aparecer no estágio neutro 6, sem herança de Baton Pass.

### Quatro hazards: quatro controles

Uma camada de Toxic Spikes; Pokémon aterrados, sem itens. O tipo Poison usa espécie Bulbasaur; o Fire, Charmander.

| Ação / banco | Ordem | Primeiro reserva | Resultado de entrada e continuidade |
|---|---|---|---|
| Manual / 0 | SR → TSpikes → Web → Spikes | Poison, 400 HP | SR 50, absorção, Speed −1, Spikes 50; termina com 300 HP, sem veneno |
| Manual / 2 | TSpikes → Spikes → Web → SR | Poison, 50 HP | Absorve e cai em Spikes; não sofre Web/SR. O segundo reserva recebe Spikes, Web e SR, sem veneno |
| U-turn / 0 | SR → TSpikes → Web → Spikes | Poison, 50 HP | Cai em SR antes de absorver. O segundo Fire é envenenado, perde Speed e recebe os dois danos; 250 após entrada, 200 após residual |
| Parting Shot / 2 | TSpikes → Spikes → Web → SR | Fire, 400 HP | Veneno, Spikes, Speed −1 e SR; 250 após entrada, 200 após residual |

A absorção pode deixar um zero na fila até a entrada seguinte compactá-la. Não se exige compactação antecipada em um turno sem nova entrada. O oráculo independente acompanha tanto os eventos quanto a persistência do campo compartilhado.

## Invariantes verificados

- Danos intermediários por identidade/PID, mensagens na ordem esperada, status, redução de Speed e absorção. HP final igual, sozinho, não é aceito como prova de ordem.
- Uma troca para o reserva 2; em caso de KO, uma segunda para o 3 no mesmo banco. Nenhum banco ausente ou duplicação do aliado ativo ao terminar.
- Rejeição do aliado pela UI antes da primeira seleção, sem mudança de equipe, HP ou índices. Não é nova cobertura de todas as recusas de candidatos inválidos.
- Durante a resolução e a seleção, a cada frame observado: identidade/índice, atributos, tipos/habilidade, HP/maxHP, EXP, status e estágios do aliado permanecem iguais. Seu histórico só pode passar de Court Change (681) para o próprio Splash (150), nunca zerar ou voltar ao anterior.
- Gasto de PP do aliado e dos adversários exatamente uma vez por turno. O pivô gasta um PP do retirado; a troca manual não gasta PP dele. Reservas, inclusive o que cai, não recebem gasto de uma ação herdada.
- Histórico do entrante zerado ao terminar o turno da troca. No turno seguinte ele usa seu próprio Splash, passa a histórico 150 e gasta seu próprio PP.
- Identidades, checksums, níveis e EXP das duas equipes preservados. Cópias de HP e PP entre BattleMon e equipe coerentes.
- Guarda de HP zero exercitada em cada caso com KO: nenhum status ou novo decréscimo de Speed no morto. Os casos escolhidos não fazem um entrante já envenenado morrer depois; esse cenário não está certificado por esta guarda.
- Mais um turno completo sem nova troca ou reaplicação de hazards. Quando há veneno, exige-se **somente o residual de 50 HP**, separado do dano de entrada. Aliado e retirado permanecem com 4.000 HP.

## Execuções finais

| Processo final | Métodos | Cenários novos | Tempo | Resultado |
|---|---:|---:|---:|---|
| Trocas voluntárias | **1** | **12** | **683,166 s** | OK, sem skips |
| Quatro pivôs: sobrevivência e KO | **2** | **16** | **884,277 s** | OK, sem skips |
| Quatro hazards + regressões | **19** | **4** | **1.031,023 s** | OK, sem skips |

**Total: 1 + 2 + 19 = 22 métodos distintos.** O terceiro processo reúne um método novo e 18 regressões: dois controles de limites/ordem adversários, um de quatro hazards/Intimidate, um de reservas insuficientes do jogador, cinco de build/integridade e nove de treino EV/IV. Os subcasos dessas regressões não entram nos 32 novos.

Os quatro métodos novos foram chamados por nome sem sobreposição; a descoberta confirma exatamente quatro no módulo. As oito sondas anteriores foram excluídas dos totais finais. Os processos rodaram em paralelo, compartilhando CPU; os tempos não medem desempenho comparativo da engine. Não foi reexecutada toda a suíte histórica.

Manifesto atualizado e verificado: **255 entradas**, sem incluir o próprio manifesto. Hashes finais reconferidos:

| Artefato inalterado | SHA-256 |
|---|---|
| ROM v17, 33.554.432 bytes | `5db05cbb54add61a6c50e08d3e392ba610e87ca3ef462095de168de5d3e32957` |
| Payload v17, 3.148 bytes | `f25e560c02cd3681a508812050e9fd0bed9d4b652d788dffa221d2a10983703f` |
| Base v16 | `644b140dc4fd1f4fab4c7ed9304fb266865d3e81825140c01c2c275564dc0fcc` |

## Reprodução

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V17_BASE=/privado/motor_v16.gba
export MOTOR_V17_ROM=/privado/motor_v17.gba
export MGBA_CORE=/privado/mgba_libretro.so
export TREINO_TEST_ROM="$MOTOR_V17_ROM"
python3 -m unittest test_motor_v17_switch_pivot_hazards_mgba -v
python3 -m unittest \
  test_motor_v17_combined_hazards_mgba.MotorV17CombinedHazardsTests.test_quarta_camada_e_sr_repetido_nao_aumentam_dano \
  test_motor_v17_combined_hazards_mgba.MotorV17CombinedHazardsTests.test_ordem_inversa_persiste_apos_tentativas_repetidas \
  test_motor_v17_lifecycle_mgba.MotorV17LifecycleTests.test_quatro_hazards_ordenados_absorcao_e_ko_antes_de_habilidade \
  test_motor_v17_regressions.MotorV17EndingsTests.test_jogador_com_uma_reserva_ou_ko_seguido_de_sobrevivente \
  test_motor_v17 test_treino_ev_mgba -v
```

## Limites e próximo recorte

Não certifica todas as permutações de hazards, duas camadas de Toxic Spikes, hazards com todas as imunidades/itens/habilidades, pivôs falhos/bloqueados, pivôs do adversário, dano de adversários ao aliado durante a troca, falta de reservas, fim da batalha, campanha, link/multi, Teachy TV ou migração de saves. Nenhuma disponibilidade de TM ou sucesso de fixture equivale a fidelidade integral a Scarlet/Violet.

Próximo recorte sugerido: **pivôs impedidos/falhos e reservas inelegíveis**, verificando que não há troca, dano de entrada ou limpeza indevida do histórico, e que a ação do aliado continua corretamente.

Nenhum save pessoal utilizado. ROMs, saves, estados e capturas de jogo fora do Git. Drive não atualizado.

## Referências

- [Motor v17: implementação, hashes e entrega original](MOTOR_V17.md).
- [Auditoria anterior: dois KOs do jogador e hazards combinados](AUDITORIA_V17_HAZARDS_COMBINADOS_JOGADOR.md).
- [Auditoria anterior: pivôs e histórico v15](AUDITORIA_V15_PIVOS_PHAZING.md), sem reutilizar estados entre versões.
- [Showdown fixado em 035c1a1: ordem dos efeitos](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/battle.ts#L1002-L1007).
- [Toxic Spikes: absorção e status](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L19745-L19783); [Sticky Web](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L17931-L17955). As referências não certificam as interações excluídas acima.
