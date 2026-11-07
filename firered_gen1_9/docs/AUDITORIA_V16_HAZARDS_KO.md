# Auditoria v16 — Spikes, Stealth Rock e KO durante a entrada

**03/11/2026 — FireRed Gen 1–9 / VYK-57.** ROM v16 exata, equipes e estados exclusivamente sintéticos. **Nenhuma alteração de ROM, payload ou aplicador; sem v17 nesta etapa.**

## Resultado

**41 verificações concluídas, sem skips**, incluindo **sete testes novos / 27 subcasos**. Nenhum novo defeito foi demonstrado neste recorte de singles, com hazards no lado adversário:

- Spikes e Stealth Rock são colocados por uso real dos golpes antes da troca; não são injetados no campo.
- O entrante recebe o dano esperado. Se desmaia, há concessão de EXP e reposição; o substituto também recebe os hazards da própria entrada.
- Spikes seguido de Stealth Rock aplica cada dano uma vez nas entradas observadas. Se Spikes já provoca KO, não há mensagem de Stealth Rock contra aquele membro desmaiado.
- Dragon Tail/Circle Throw que derrubam o alvo são seguidos de reposição normal, sem mensagem de arrastamento nem troca adicional observada.
- Dois desmaios consecutivos por hazard terminam em vitória, EXP concluída, subida ao nível 11 e retorno ao callback do mapa.
- PP de equipe/batalha e histórico permanecem coerentes; Eerie Spell após a reposição não herda o golpe do ocupante anterior.

A conclusão não abrange todos os hazards, habilidades, itens, lados ou modos de batalha. A engine continua parcial.

## Matriz dos testes novos

Arquivo: `tests/test_motor_v16_hazards_ko_mgba.py`.

IDs locais: Spikes **191**, Stealth Rock **445**, Roar **46**, Whirlwind **18**, Dragon Tail **521**, Circle Throw **508**, Eerie Spell **720**. Não confundir o ID local 445 com o ID oficial de Stealth Rock.

| Cenário | Subcasos | Exigência principal |
|---|---:|---|
| Entrada sem KO | 2 hazards × 4 golpes de phazing = **8** | Dano, PP, histórico zero e dois turnos seguintes de Eerie |
| KO na entrada e reposição | 2 × 4 = **8** | Índices `0→1→0`, EXP, novo dano de hazard e PP próprios |
| Flying | **2** | Charizard ignora Spikes, mas recebe Stealth Rock com fraqueza quádrupla |
| Spikes + Stealth Rock | **2** | Sobrevivência ou KO no segundo hazard, sem dano repetido |
| KO pelo próprio golpe | 2 hazards × 2 golpes com dano = **4** | Reposição normal, dano de entrada, EXP e ausência de arrastamento extra |
| KO em cadeia / vitória | **2** | Ambos os adversários caem por hazard; resultado de vitória e retorno ao mapa |
| KO no primeiro de dois hazards | **1** | Spikes derruba o entrante; Stealth Rock só atinge o substituto vivo |
| **Total** | **27** | |

As fixtures têm dois membros adversários. No KO do entrante, o membro que acabara de sair é o único substituto vivo, tornando a sequência de reposição verificável sem escolher o resultado do RNG por memória.

## Dano medido e histórico

As reservas têm HP máximo sintético **400**. Os tipos da reserva são carregados nativamente na entrada:

| Reserva | Uma camada de Spikes | Stealth Rock |
|---|---:|---:|
| Charmander, Fire | **50** (1/8) | **100** (fraqueza 2× a Rock) |
| Charizard, Fire/Flying | **0** | **200** (fraqueza 4× a Rock) |

Com Charmander inicialmente a 400 HP, o primeiro Eerie após phazing age antes de sua primeira ação: não drena PP, deixando apenas o custo de Splash, **31→30**. No turno seguinte, já existe histórico de Splash: três PP drenados mais um pelo uso próprio, **30→26**.

No KO de entrada, o reserva começa exatamente a 50 ou 100 HP. Seu HP chega a zero, o banco retorna ao slot 0 e o histórico é limpo. O membro que retorna conserva os **38 PP de Splash** após suas duas ações anteriores; o primeiro Eerie posterior não drena, e a ação própria o deixa com **37**. O desmaiado conserva os 31 PP não usados.

O membro inicial tem máximo 4.000 HP. Quando volta, perde **500 por Spikes** ou **1.000 por Stealth Rock**. Eventual dano anterior de Dragon Tail/Circle Throw é distinguido desse último evento de entrada. Os testes observam HP persistente por frame, não só a barra ou a mensagem.

## Dois hazards e interrupção por KO

A ordem efetivamente testada é **Spikes criado primeiro, Stealth Rock depois**. A ordem inversa não foi auditada.

Com ambos ativos:

- Reserva a 400 HP: **400→350→250**.
- Reserva a 100 HP: **100→50→0**; o membro que retorna sofre **4.000→3.500→2.500**.
- Reserva a 50 HP: **50→0** por Spikes. Há apenas uma mensagem de Stealth Rock na sequência, referente ao substituto vivo, que sofre **4.000→3.500→2.500**.

As listas completas de transições são exigidas. Não basta conferir apenas o HP final, que poderia esconder execução indevida ou repetição de etapas.

## KO pelo golpe e vitória por hazards

Para o KO direto, o alvo inicial é preparado com 1 HP antes dos turnos. O hazard é colocado enquanto ele usa Splash; depois Dragon Tail/Circle Throw o derruba. Os testes exigem:

- HP do slot 0 igual a zero;
- somente a transição `0→1` e a mensagem de desmaio, sem mensagem de arrastamento;
- reserva com 350/300 HP após o respectivo hazard;
- consumo único do golpe e PP do reserva intactos até sua primeira ação;
- EXP concluída e histórico zero antes da ação do novo ocupante.

Para o encerramento por KO em cadeia, usa-se Roar: o reserva cai no primeiro ingresso e o membro inicial cai ao voltar. As duas mortes são atribuídas aos hazards, sem dano de golpe intermediário.

Nesta fixture, cada Charmander nível 10 derrotado concede **138 EXP**: um KO leva **560→698**; dois levam **560→836**, cruzando o nível 11, cujo limiar é 742. **Esses valores são controles da engine/fixture, não certificação da fórmula de EXP de SV.**

No caso de vitória, não se encerra a observação no primeiro texto de desmaio nem no valor intermediário 742. O helper espera o término da distribuição de EXP e do quadro de atributos, exigindo **resultado de vitória, flag fora de batalha e callback do mapa**. Também confere nível 11, HP positivo dentro do máximo e PP persistentes.

## Integridade e sincronização

Os Pokémon são sintéticos; EXP/nível e checksums são coerentes. HP, atributos, movesets e tipos iniciais de controle são deliberadamente preparados para isolar as situações. Não são dados de campanha nem saves pessoais.

- Hazards, ataques, phazing e reposições são executados por scripts reais e entradas de interface.
- Não há escrita em histórico, hazards ou índices ativos entre turnos.
- São acompanhados por frame o HP dos dois slots adversários, transições de índice e textos.
- No retorno ao menu, os testes exigem PP de batalha iguais aos da equipe criptografada/checksum, HP persistente, batalha ativa e marcador `0x800` limpo.
- No retorno ao mapa, exigem-se o resultado/callback adequados e a EXP final, em vez das invariantes de um menu de batalha ainda aberto.

**Correção do observador, não da ROM:** 16 confirmações B não concluíram a primeira sonda de reposição; com 32, uma entrada contendo ambos os hazards ainda terminou na mensagem de Spikes. O limite final é **64 confirmações**, saindo antes quando o menu aparece e aguardando mais 120 frames para a transição terminar. O helper de vitória também tem espera limitada. Com o fluxo concluído, as transições e danos exatos passaram; não se alteraram as asserções para aceitar um estado intermediário.

## Execução final

mGBA **0.10.5**, três processos finais com código zero:

| Execução | Resultado | Tempo |
|---|---:|---:|
| Suíte com os seis primeiros métodos novos | **6/6** | **405,827 s** |
| Controle adicional de KO por Spikes antes de Stealth Rock | **1/1** | **46,936 s** |
| Eerie/HP/PP/KO/EXP v16 + build + treino EV/IV | **34/34** (20 + 5 + 9) | **182,660 s** |
| **Total** | **41/41**, nenhum skip | |

O sétimo método foi acrescentado depois do início da execução dos seis e executado separadamente. Não se contou duas vezes nenhum método. Sondas, a tentativa inicial com falha de asserção de menu e reexecuções isoladas anteriores foram excluídas da contagem final.

Não se reexecutaram integralmente os 85 testes da entrega v16, a matriz anterior de duplas nem todas as 61 regressões. Os negativos históricos v12/v13 não integram os 20 positivos de Eerie reexecutados nesta etapa.

## Reprodução e artefatos

Na raiz do repositório, usando ROM própria:

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V16_BASE=/privado/motor_v15.gba
export MOTOR_V16_ROM=/privado/motor_v16.gba
export MGBA_CORE=/privado/mgba_libretro.so
export TREINO_TEST_ROM="$MOTOR_V16_ROM"
# O módulo atual contém os sete métodos, que podem ser executados juntos.
python3 -m unittest test_motor_v16_hazards_ko_mgba -v
python3 -m unittest test_motor_v16_regressions.MotorV16EerieTests \
  test_motor_v16 test_treino_ev_mgba -v
```

SHA-256 da ROM v16 permanece **`644b140dc4fd1f4fab4c7ed9304fb266865d3e81825140c01c2c275564dc0fcc`**, 33.554.432 bytes. Payload de 300 bytes permanece **`f1946a84a7932215b83e6d01e4d6794e4b1dbab334fb49c2236b48ad185c0ceb`**. Catálogo permanece em 15.008 registros / 708 de 729 omissões restauradas.

**ROM, payload, aplicador e catálogo inalterados. Nenhuma ROM/save/estado incluído no Git. Drive não atualizado.**

## Limites e próximos controles

Esta matriz é singles, com hazards e KOs no lado adversário. Não valida automaticamente o lado do jogador, duplas com KO, hazards em entradas por pivôs/Baton Pass, redirecionamento, mais reservas ou modos link/multi.

Também permanecem fora: duas/três camadas de Spikes, ordem inversa de colocação, Toxic Spikes/Sticky Web, Gravity/Levitate, Magic Guard, Heavy-Duty Boots, demais habilidades/itens e entradas com efeitos simultâneos. Não se certificam toda a fórmula de EXP, campanha, Teachy TV ou migração de saves pessoais.

**Próximo recorte recomendado:** repetir entrada/KO pelo lado do jogador e em duplas, incluindo seleção do substituto após desmaio. A engine continua parcial.

## Referências fixadas

- [Showdown `moves.ts`, 035c1a1](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts): Spikes, aterramento e frações; Stealth Rock e efetividade de tipo. Itens/habilidades fora do recorte não são validados por esta comparação.
- [pret `battle_scripts_1.s`, ce6406d](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/data/battle_scripts_1.s): scripts de dano/desmaio por Spikes, concessão de EXP e tratamento dos desmaiados.
- `patches/motor_v8/motor_v8.c` e `scripts/motor_v8.py`: processamento adicional de hazards e reutilização da cauda nativa de desmaio.
- [Entrega v16](MOTOR_V16.md) e [auditoria de duplas anterior](AUDITORIA_V16_DUPLAS_PHAZING.md).
