# Auditoria v17 — hazards combinados nas reposições do jogador em duplas

**04/11/2026 — FireRed Gen 1–9 / VYK-57.** ROM v17 exata, mGBA 0.10.5, equipes e estados exclusivamente sintéticos. **Auditoria sem alteração de ROM, payload ou aplicador; sem v18 nesta etapa.**

## Resultado

**23/23 métodos distintos aprovados, sem skips**, com cinco métodos novos / **30 cenários** e 18 regressões reexecutadas. Todos os processos finais terminaram com código zero. **Nenhum novo defeito de engine foi demonstrado neste recorte.**

A v17 preservou a ordem dos hazards nas escolhas reais do jogador, incluindo KO do primeiro reserva, absorção nos dois bancos, rejeição de candidatos inválidos e continuidade com um ou dois sobreviventes. Isso não é certificação completa de Scarlet/Violet.

## Matriz nova

Arquivo: `tests/test_motor_v17_player_combined_hazards_mgba.py`. Descoberta conferida: **cinco métodos distintos**, sem duplicação de classes auxiliares.

| Grupo | Configuração | Subcasos |
|---|---|---:|
| Spikes primeiro | 1/2/3 camadas × saudável, KO no primeiro hazard, KO no segundo | **9** |
| Stealth Rock primeiro | 1/2/3 camadas × saudável, KO no primeiro hazard, KO no segundo | **9** |
| Limites e escolhas invertidas | Ambas as ordens, três camadas, quarta tentativa de Spikes/segunda de SR, ator adversário 3 e reserva 3 escolhido primeiro | **2** |
| Quatro hazards, absorção e KO | Duas ordens × Poison primeiro, Poison segundo, HP 50 e HP 100 do Poison escolhido primeiro | **8** |
| Guarda de atributos após KO | Atacante 3, Poison com 50 HP, ambas as ordens de quatro hazards | **2** |
| **Total novo** | **Cinco métodos** | **30** |

Nos dois grupos principais, o atacante adversário é o banco **1**, e os reservas são escolhidos na ordem **2→3**. Os controles de limite usam o atacante **3** e escolhas **3→2**. Nos controles de quatro hazards, escolher o Fire primeiro também usa o atacante 3. Não se afirma a matriz completa de todas as configurações em ambos os atacantes.

As duas ordens de quatro hazards são:

1. **Stealth Rock → Toxic Spikes → Sticky Web → Spikes**.
2. **Toxic Spikes → Spikes → Sticky Web → Stealth Rock**.

Esses controles e os dois controles adicionais de atributos após KO usam **uma camada de Spikes e uma de Toxic Spikes**. Não são as 24 permutações dos quatro hazards, nem uma matriz de envenenamento grave por duas camadas.

## Preparação, colocação e origem dos hazards

Todos os casos começam com os dois ativos do jogador vivos, com **1 HP**. Há dois reservas elegíveis, com PIDs distintos e HP máximo **400**, além de um ovo e um slot vazio. Os adversários ficam vivos durante todo o recorte.

Os hazards são colocados por **golpes reais do jogador no lado adversário**, em turnos separados. Depois, um **Court Change real** leva as condições e sua ordem para o lado do jogador. Esse caminho evita depender de a IA escolher uma sequência específica de quatro golpes. A fila, os contadores de camadas e as condições dos dois lados são conferidos antes dos KOs.

**Não se trata de uma auditoria da colocação adversária direta**, Magic Bounce ou colocação indireta. A origem via Court Change é parte explícita deste recorte, não uma gravação artificial do estado final de hazards na RAM.

Golpes por IDs locais da ROM: Spikes **191**, Stealth Rock **445**, Toxic Spikes **390**, Sticky Web **560**, Court Change **681**, Rock Slide **157**, Splash **150** e Protect **182**. Os IDs modernos de algumas referências não são transplantados para a ROM expandida.

### Controle sintético da IA, somente no preparo

O adversário atacante tem Rock Slide e Splash. **Antes de executar a fixture**, Rock Slide é marcado como desabilitado pelo número de turnos de colocação mais Court Change; Splash recebe exatamente essa quantidade de PP. A cada turno, exige-se:

- Splash como ação elegível efetivamente utilizada, com seu PP consumido;
- contador nativo de Disable diminuindo até zero e golpe desabilitado sendo limpo;
- ausência de dano ou troca prematuros;
- identidade, nível, EXP e checksums coerentes.

No turno seguinte, Disable já expirou e Splash está sem PP: o adversário usa **Rock Slide real**, derrubando os dois ativos. Não se escrevem HP, hazards, índices, RNG, histórico, EXP ou timers durante as ações para provocar o resultado.

Essa temporização inicial, inclusive durações sintéticas maiores que quatro, **não é teste da aplicação/duração moderna do golpe Disable**. Serve para isolar a reposição. A primeira sonda tentou depender só da preferência da IA pelo slot de Splash; a IA antecipou Rock Slide. A fixture foi corrigida, não a engine, e essa sonda não integra a contagem final.

## Seleção real, rejeição e bancos

As escolhas usam botões na tela de equipe, não escrita do índice do ocupante.

1. Os dois KOs originais são exigidos antes da entrada de qualquer reserva. A ordem relativa desses dois alvos de Rock Slide pode variar.
2. O primeiro reserva é escolhido; seus hazards terminam antes da próxima escolha.
3. Ainda no menu, tenta-se enviar o candidato atual novamente. Se está vivo e ativo, exige-se o texto nativo **“em batalha!”**; se desmaiado, **“para batalhar!”**.
4. A rejeição deve manter o callback da tela, índices, registros das duas equipes, eventos de HP e transições. A mensagem precisa aparecer na RAM de texto; apenas permanecer no menu não é evidência suficiente.
5. O segundo reserva vivo é escolhido e a batalha continua.

Se ambos sobrevivem, ocupam os bancos **0 e 2**, em ordem **2/3** ou **3/2** conforme a escolha. Se o primeiro morre nos hazards, o segundo preenche novamente o **banco 0**, e o banco **2** fica ausente, máscara **`0x04`**. O membro morto não é reutilizado.

A tela reorganiza temporariamente os registros da equipe. Por isso o observador acompanha HP **por PID**, e só compara a ordem persistente dos slots quando a batalha estabiliza. O teste não confunde reordenação visual com dano ou cura.

## Dano e mensagens

Os reservas Fire, carregados nativamente na entrada, recebem:

| Camadas | Spikes | Stealth Rock | Spikes primeiro, HP 400 | SR primeiro, HP 400 |
|---:|---:|---:|---|---|
| 1 | **50** | **100** | **400→350→250** | **400→300→250** |
| 2 | **66** | **100** | **400→334→234** | **400→300→234** |
| 3 | **100** | **100** | **400→300→200** | **400→300→200**, mensagens em ordem inversa |

O teste compara os eventos intermediários **e as mensagens**. Com três camadas, o empate de dano não pode mascarar a ordem incorreta.

Para o primeiro reserva cair no primeiro hazard, o HP inicial é **50/66/100** quando Spikes vem primeiro e **100** quando SR vem primeiro. Para cair no segundo, é **150/166/200**, a soma dos danos. Depois do KO, nenhum hazard restante atinge aquele membro; o segundo reserva recebe sua própria sequência.

A quarta tentativa de Spikes não cria uma quarta camada, e SR repetido não cria uma segunda aplicação. O sobrevivente não recebe outro dano de hazard simplesmente por começar o turno seguinte.

## Toxic Spikes, absorção e Sticky Web

Nos oito casos de quatro hazards, o reserva 2 é preparado como **Bulbasaur Grass/Poison**; o reserva 3 permanece Fire. A espécie é alterada e o checksum é recalculado **antes** da execução. Tipos e habilidade são carregados nativamente quando entra — não se força Poison em RAM durante a batalha.

Para o Poison aterrado com maxHP 400, SR e uma camada de Spikes causam **50 cada**. Toxic Spikes é absorvido quando sua etapa é alcançada; Sticky Web reduz Speed de estágio **6 para 5**.

- **Poison primeiro, saudável:** absorve Toxic Spikes; o Fire escolhido depois não é envenenado. O Poison termina a entrada com **300 HP**, o Fire com **250 HP**.
- **Fire primeiro, Poison segundo:** o Fire já é envenenado na primeira entrada; a absorção posterior remove o hazard, mas **não cura esse status**. O Fire vai a **250 HP** pelos hazards e depois **200** pelo veneno residual. O Poison termina com **300 HP**.
- **Poison com 50 HP, SR primeiro:** SR o derruba antes da absorção. Toxic Spikes permanece e envenena o Fire seguinte.
- **Poison com 50 HP, Toxic Spikes primeiro:** absorve a condição e cai em Spikes; não executa Web nem SR depois do KO. O Fire seguinte não é envenenado.
- **Poison com 100 HP:** absorve antes de cair no segundo hazard de dano, nas duas ordens testadas. Web ocorre apenas se sua posição é anterior ao KO.

O observador exige a sequência por identidade de **HP, status, estágio de Speed e remoção de Toxic Spikes**. Dois controles adicionais, com atacante 3 e Poison entrando com 50 HP, também vigiam o banco enquanto seu HP já é zero: exigem status zero e nenhuma nova queda de Speed. A guarda precisa ser efetivamente exercitada. Isso evita esconder uma aplicação tardia de Web ao excluir a limpeza nativa de atributos do trace normal de entrada. A ordem esperada vem de um oráculo separado, não da fila lida da engine.

A fila v17 pode manter um zero na posição da condição absorvida até a próxima entrada; isso evita saltar a etapa seguinte. O teste aceita **somente o estado exato previsto**: se há outra entrada depois da absorção, exige a compactação que preserva a ordem; se a absorção ocorre na segunda entrada, exige a posição vazia. Court Change deixou o lado adversário sem hazards e ele deve continuar assim.

## Histórico, PP, EXP e turno posterior

Após as escolhas, cada banco presente do jogador começa com histórico **zero**. Os entrantes não executam nem gastam PP da ação Splash escolhida pelos membros que morreram. No turno posterior, o jogador escolhe seu próprio **Protect**, uma vez em cada banco presente. Exige-se histórico **182** e o gasto correspondente.

Com apenas um sobrevivente, a UI recebe uma única escolha. O banco ausente conserva histórico e PP de batalha; o slot morto não ganha nova ação. Os PP persistentes dos 12 registros são conferidos após colocação, KOs, escolhas e continuação.

Nenhum adversário cai neste recorte: EXP e níveis de todas as equipes devem permanecer inalterados. PID/OT e checksums são verificados. Isso não é certificação de toda a fórmula moderna de EXP.

O dano de veneno no fim do turno é tratado separadamente: **50 por turno** para o Fire com maxHP 400 e poison regular. Protect impede o novo Rock Slide, mas não impede esse residual. Assim, o teste não chama o residual de reaplicação de hazard nem o ignora para afirmar continuidade sem dano. Nos casos sem veneno, exige-se ausência total de novas perdas de HP.

## Execuções finais

| Processo final desta etapa | Métodos | Cenários novos | Tempo | Resultado |
|---|---:|---:|---:|---|
| Camadas e KO nas duas ordens | **2** | **18** | **849,984 s** | OK, sem skips |
| Limites, escolha inversa e quatro hazards | **2** | **10** | **632,021 s** | OK, sem skips |
| Guarda adicional de atributos após KO, atacante 3 | **1** | **2** | **102,672 s** | OK, sem skips |
| Regressões: limites adversários (2), quatro hazards/Intimidate (1), jogador com uma reserva (1), build (5), EV/IV (9) | **18** | — | **698,325 s** | OK, sem skips |

**Total: 2 + 2 + 1 + 18 = 23 métodos distintos.** Os cinco novos foram chamados por nome em três processos, sem sobreposição, e a descoberta final confirma exatamente cinco métodos no módulo. Os dois controles adicionais usam atacante 3 onde a matriz de quatro hazards usava atacante 1, além da guarda de atributos do banco morto. São 30 cenários novos, sem somar os subcasos das regressões.

As sondas e a tentativa inicial com escolha precoce da IA foram excluídas dos totais finais. Não foram somados resultados históricos da entrega v17, nem reexecutadas todas as suítes anteriores. Os três grupos principais rodaram em paralelo, compartilhando CPU; os tempos não são uma comparação de desempenho da engine.

SHA da ROM v17, payload e base v16 reconferidos e inalterados. Manifesto do pacote atualizado e verificado: **253 entradas**, sem incluir o próprio manifesto.

## Reprodução

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V17_BASE=/privado/motor_v16.gba
export MOTOR_V17_ROM=/privado/motor_v17.gba
export MGBA_CORE=/privado/mgba_libretro.so
export TREINO_TEST_ROM="$MOTOR_V17_ROM"
python3 -m unittest test_motor_v17_player_combined_hazards_mgba -v
python3 -m unittest \
  test_motor_v17_combined_hazards_mgba.MotorV17CombinedHazardsTests.test_quarta_camada_e_sr_repetido_nao_aumentam_dano \
  test_motor_v17_combined_hazards_mgba.MotorV17CombinedHazardsTests.test_ordem_inversa_persiste_apos_tentativas_repetidas \
  test_motor_v17_lifecycle_mgba.MotorV17LifecycleTests.test_quatro_hazards_ordenados_absorcao_e_ko_antes_de_habilidade \
  test_motor_v17_regressions.MotorV17EndingsTests.test_jogador_com_uma_reserva_ou_ko_seguido_de_sobrevivente \
  test_motor_v17 test_treino_ev_mgba -v
```

| Artefato inalterado | SHA-256 |
|---|---|
| ROM v17, 33.554.432 bytes | `5db05cbb54add61a6c50e08d3e392ba610e87ca3ef462095de168de5d3e32957` |
| Payload v17, 3.148 bytes | `f25e560c02cd3681a508812050e9fd0bed9d4b652d788dffa221d2a10983703f` |
| Base v16 usada pelos testes de build | `644b140dc4fd1f4fab4c7ed9304fb266865d3e81825140c01c2c275564dc0fcc` |

## Limites e próximo recorte

A matriz nova começa com **dois KOs do jogador por Rock Slide** e mantém ao menos um reserva sobrevivente. Não certifica derrota por hazards combinados, escolha de todas as posições de equipe, todas as permutações, duas camadas de Toxic Spikes, tipos/itens/habilidades/aterramento completos ou colocação direta pela IA. Os atributos/PP e a temporização de Disable do preparo são sintéticos; não provam legalidade das equipes ou regras completas desses golpes.

As regressões do lado adversário e de reservas insuficientes não ampliam silenciosamente esse escopo. Não houve auditoria completa de campanha, link/multi, Teachy TV, save states entre versões ou migração de saves pessoais. A engine continua parcial.

Próximo recorte recomendado: **trocas voluntárias e pivôs do jogador sob hazards combinados, com aliado ainda ativo**, incluindo KO na entrada e seleção do substituto.

**Nenhum save pessoal utilizado. ROMs, saves, estados e capturas de jogo fora do Git. Drive não atualizado.**

## Referências fixadas

- [Motor v17, implementação, hashes e validação original](MOTOR_V17.md).
- [Auditoria anterior de seleção do jogador](AUDITORIA_V16_HAZARDS_JOGADOR.md), [duas reposições](AUDITORIA_V16_DUPLAS_KO_REPOSICAO.md) e [bancos ausentes](AUDITORIA_V16_DUPLAS_RESERVAS_FIM.md).
- [Pokémon Showdown, `sim/battle.ts`, 035c1a1, L1002–1007](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/battle.ts#L1002-L1007): ordem de criação dos hazards.
- [Pokémon Showdown, `data/moves.ts`, Toxic Spikes](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L19745-L19783): absorção pelo tipo Poison aterrado e poison regular com uma camada.
- [Pokémon Showdown, `data/moves.ts`, Sticky Web](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L17931-L17955): redução de um estágio de Speed para entrante aterrado no recorte sem itens de imunidade.
