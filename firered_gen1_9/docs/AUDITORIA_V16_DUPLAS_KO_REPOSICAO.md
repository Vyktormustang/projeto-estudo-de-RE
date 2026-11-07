# Auditoria v16 — KO, hazards e duas reposições em duplas

**04/11/2026 — FireRed Gen 1–9 / VYK-57.** Equipes e estados exclusivamente sintéticos, mGBA 0.10.5, ROM v16 exata. **ROM, payload e aplicador inalterados; sem v17 nesta etapa.**

## Resultado

**23/23 verificações distintas aprovadas, sem skips**, incluindo **quatro métodos novos / 52 subcasos**. Foram 28 execuções aprovadas nos três processos finais; cinco eram repetições e não aumentam o total distinto. Todos os processos terminaram com código zero.

Nenhum novo defeito foi demonstrado neste recorte. Foram conferidos KO adversário por hazard, duas reposições pela IA, duas escolhas de substitutos do jogador após um golpe de área, dano em cada entrada, recusa de duplicata, EXP, PP, histórico e continuidade da batalha. A engine continua parcial.

## Matriz nova

Arquivo: `tests/test_motor_v16_doubles_hazards_ko_mgba.py`.

| Método / cenário | Subcasos | Controles |
|---|---:|---|
| Entrada adversária sem KO, seguida de Eerie | 2 hazards × 2 atores × 2 alvos = **8** | Roar, reserva, dano, PP e histórico novo |
| KO adversário por hazard e reposição | 2 hazards × 4 phazers × 2 atores × 2 alvos = **32** | Reserva desmaia; membro retirado volta, recebe hazard e conserva identidade/PP |
| Dois KOs do jogador por golpe de área | 2 hazards × 2 adversários × 2 ordens de seleção = **8** | Duas escolhas reais, rejeição de duplicata, dois danos de entrada e turno seguinte |
| Dois KOs adversários por golpe de área | 2 hazards × 2 atores = **4** | Duas reposições distintas pela IA, EXP, hazards e dois turnos de Eerie |
| **Total** | **52** | **Quatro métodos novos** |

IDs locais: Spikes **191**, Stealth Rock **445**, Roar **46**, Whirlwind **18**, Dragon Tail **521**, Circle Throw **508**, Rock Slide **157**, Eerie Spell **720**, Protect **182**. O ID local 445 não é o ID oficial de Stealth Rock.

Nos 40 subcasos de entrada/phazing, os atores são os bancos **0/2** e os alvos são **1/3**, escolhidos pela interface. Nos oito de dois KOs do jogador, Rock Slide vem dos bancos adversários **1/3**, e as duas ordens escolhidas são reservas **2→3** e **3→2**. Nos quatro de dois KOs adversários, Rock Slide vem dos bancos **0/2**; a IA escolhe a ordem dos reservas, sem forçar o RNG.

## Preparação e controles de segurança

A fixture parte do construtor da auditoria anterior de phazing em duplas, com identidades distintas e contexto sintético de treinador, não link/multi. Todos os membros usados estão no nível 10, com EXP inicial coerente **560**. Não se reutiliza o ator de nível 5 do antigo teste de diferença de nível: esta etapa isola KO/reposição, não revalida aquele defeito.

- Na entrada por phazing há dois ativos por lado, uma reserva viva elegível, uma desmaiada, um ovo e um slot vazio.
- Nos controles de dois KOs há dois reservas vivos no lado atingido; ovo e slot vazio continuam inelegíveis.
- Os ativos têm máximo sintético de 4.000 HP; os reservas de entrada têm máximo 400. Nos controles de dois KOs, ambos os alvos começam com 1 HP, mas vivos.
- Spikes/Stealth Rock são colocados por golpes reais no primeiro turno, sem dano imediato ao alvo já em campo. No caso de dois KOs do jogador, o adversário tem apenas um PP do hazard e só Rock Slide disponível depois de gastá-lo.
- Os dois desmaios do controle de área resultam de **uma execução de Rock Slide**. Isso não significa que as escritas de HP ou os scripts de desmaio ocorram no mesmo frame.
- Os PIDs permanecem únicos. O observador herdado acompanha HP por identidade, inclusive durante a reordenação temporária da tela de equipe.
- Depois de iniciar as ações, não há escrita em HP, histórico, índices, hazards, RNG, alvo ou EXP para produzir o resultado. As escolhas são botões na UI.

Os atributos/PP/HP são sintéticos, não equipes legais de campanha. Rock Slide contra 1 HP demonstra os dois KOs e a sequência posterior, **não a fórmula moderna de dano de área nem a probabilidade de flinch**.

## Entrada adversária, dano e EXP

Para Charmander/Fire com máximo 400:

| Caso | Uma camada de Spikes | Stealth Rock |
|---|---:|---:|
| Sobrevive | **400→350** | **400→300** |
| Desmaia na entrada | **50→0** | **100→0** |
| Membro de máximo 4.000 que retorna | **−500** | **−1.000** |

Após phazing com KO, a sequência exigida no banco alvo é `original→reserva 2→original`. O parceiro adversário não muda de índice e permanece a 4.000 HP. Roar/Whirlwind produzem somente os eventos de hazard; Dragon Tail/Circle Throw têm um evento de dano próprio anterior, separado dos eventos de entrada. As listas de eventos e transições são verificadas, não apenas o HP final.

A concessão nativa de um KO é dividida entre os dois participantes: **69 EXP para cada um**, de **560→629**, sem subida de nível. Nos dois KOs adversários, cada participante recebe **138** ao todo, de **560→698**, também abaixo do nível 11. A EXP dos demais membros e adversários é preservada, com checksum válido.

Esses valores são controles da fixture e do comportamento nativo; **não certificam a fórmula de EXP de Scarlet/Violet**.

### EXP persistente não é o cache de batalha

Uma sonda inicial exigia igualdade imediata entre a EXP persistente e o campo de EXP do `BattlePokemon`. Falhou com **560 no cache / 629 na equipe**. O código público de `Task_GiveExpToMon` atualiza `gPlayerParty` com `SetMonData(MON_DATA_EXP)`; `Cmd_getexp` só sincroniza determinados atributos de batalha quando há level-up, não esse campo de EXP a cada concessão.

A verificação final distingue os dois: **cache de batalha permanece em 560** nestas fixtures sem subida de nível; a EXP persistente deve ser exatamente 629 ou 698 e sobreviver aos turnos seguintes. Não se alterou a ROM para forçar igualdade entre campos com ciclos de atualização diferentes. A colisão inicial de nome entre um helper e o dicionário de identidades do observador também foi corrigida no teste, antes das execuções finais. Sondas preliminares não contam como aprovações finais.

## Eerie após reposição

Nos controles adversários, o ator é mais rápido que os entrantes. Após a entrada, o histórico do banco deve estar zerado. O primeiro Eerie não deve drenar o Splash do ocupante anterior: o alvo perde somente um PP ao executar seu próprio Splash. No segundo Eerie, já há histórico de Splash: são **três PP drenados mais um do uso próprio**.

Isso é conferido tanto quando a reserva sobrevive quanto quando o original volta após KO da reserva, e também após dois KOs com duas reservas novas. São checados PP de todos os membros de ambos os lados, HP persistente/batalha, PID/OT, nível, checksum, histórico, índices distintos e marcador `0x800` limpo. A EXP persistente deve continuar correta depois dos dois turnos de Eerie.

## Dois KOs do jogador: duas escolhas pela UI

O primeiro Rock Slide após a colocação do hazard derruba os dois ativos antes de suas ações escolhidas. Ambos passam de 1 HP a zero; **não gastam PP nesse turno**. A tela de equipe abre, com callback diferente do de batalha.

1. Escolhe-se o reserva 2 ou 3 para o banco 0. Ele entra, recebe o hazard e fica com 350 ou 300 HP.
2. A segunda tela de escolha é observada com o primeiro substituto já em campo. Tentar enviá-lo novamente deve produzir **“em batalha!”**, preservando os índices e todos os 600 bytes de cada equipe.
3. Escolhe-se o outro reserva para o banco 2. Ele também recebe exatamente um dano de entrada, independente do primeiro.
4. O jogo retorna ao callback de batalha; os índices são `(2,0,3,1)` ou `(3,0,2,1)`. Os membros originais continuam desmaiados, e nenhum dos entrantes herdou/gastou a ação dos mortos.

No turno seguinte, cada novo membro usa seu próprio **Protect** pela UI. Isso isola a continuidade do flinch aleatório de Rock Slide: ambos gastam o próprio PP e registram Protect, o adversário gasta Rock Slide, e não há nova perda de HP nem troca. A EXP de toda a equipe permanece igual à inicial.

As confirmações são finitas. O observador exige a primeira entrada antes da segunda escolha, os dois danos por identidade, a mensagem de rejeição e o retorno à batalha; não infere sucesso apenas porque um texto antigo permanece em RAM.

## Dois KOs adversários: duas reposições pela IA

Rock Slide derruba os dois adversários originais antes de suas ações. A IA deve colocar os reservas **2 e 3**, um em cada banco, sem duplicá-los ou escolher o ovo/slot vazio. A ordem concreta não é fixada pelo teste.

São exigidos exatamente dois eventos `1→0` dos membros originais e dois eventos de entrada `400→350` ou `400→300` dos reservas, além de uma transição por banco adversário. Os mortos não gastam o PP da ação interrompida; os reservas não gastam PP nesse turno. O aliado do jogador executa somente sua própria ação de Splash. Depois, dois turnos de Eerie verificam o histórico novo e o consumo correto de PP, sem perder os **698 de EXP** persistentes dos dois participantes.

## Execuções finais

| Processo | Métodos | Tempo | Situação |
|---|---:|---:|---|
| Três primeiros métodos novos + cinco métodos anteriores redescobertos | **8** | **1.864,447 s** | **OK, sem skips** |
| Método adicional de dois KOs adversários | **1** | **179,605 s** | **OK, sem skips** |
| Hazards/seleção do jogador (5) + build v16 (5) + treino EV/IV (9) | **19** | **821,123 s** | **OK, sem skips** |

O quarto método foi acrescentado após o processo principal começar e executado separadamente. O carregador `unittest` também descobriu cinco métodos anteriores porque a classe auxiliar havia sido importada sob um alias global. A descoberta foi corrigida usando referências pelo módulo; um diagnóstico confirmou exatamente quatro métodos novos no arquivo atual e identidade dos bindings dos helpers, sem executar testes adicionais. As asserções dos cenários não mudaram.

Os três processos somam **8 + 1 + 19 = 28 execuções aprovadas**. As verificações distintas são **3 + 1 + 19 = 23**: as cinco repetições não aumentam esse total. Não houve uma execução única dos quatro métodos novos nem reexecução integral de todas as suítes históricas. Resultados históricos e sondas preliminares ficam fora da contagem.

O ambiente temporário foi reconstruído novamente: mGBA 0.10.5 e cadeia parcial→estojo v2→motor v5…v16, com SHA de entrada verificado antes de cada aplicação, sempre gravando arquivos novos. A base privada foi somente baixada em leitura do Drive. O checkout foi realinhado ao commit publicado `7ee17a5` após confirmar igualdade integral dos arquivos locais com esse commit; nenhuma divergência foi descartada.

## Reprodução

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V16_ROM=/privado/motor_v16.gba
export MOTOR_V16_BASE=/privado/motor_v15.gba
export MGBA_CORE=/privado/mgba_libretro.so
export TREINO_TEST_ROM="$MOTOR_V16_ROM"
python3 -m unittest test_motor_v16_doubles_hazards_ko_mgba -v
python3 -m unittest test_motor_v16_player_hazards_mgba test_motor_v16 test_treino_ev_mgba -v
```

Hoje o arquivo novo completo executa os quatro métodos. A tabela registra os processos efetivamente usados nesta etapa.

| Artefato inalterado | SHA-256 |
|---|---|
| ROM v16, 33.554.432 bytes | `644b140dc4fd1f4fab4c7ed9304fb266865d3e81825140c01c2c275564dc0fcc` |
| Entrada v15 | `a6b454f7cbafad8c05e1b8aa2028087a596bbeff4f0184c826a92ebb7e554147` |
| Payload v16, 300 bytes | `f1946a84a7932215b83e6d01e4d6794e4b1dbab334fb49c2236b48ad185c0ceb` |

## Limites e próximos controles

A matriz de dois KOs sempre dispõe de **dois reservas vivos que sobrevivem à entrada**. Não cobre reservas insuficientes, KO desses substitutos pelo hazard, banco ausente, fim da batalha, vitória ou derrota/whiteout nesse cenário. Próximo recorte recomendado: **duplas com reservas insuficientes e KOs durante a reposição**, verificando também o encerramento da batalha.

Permanecem fora: hazards combinados/múltiplas camadas neste recorte, Toxic Spikes/Sticky Web, habilidades/itens/efeitos de entrada simultâneos, pivôs, link/multi, campanha, Teachy TV e migração de saves pessoais. A engine continua parcial.

**Nenhum save pessoal foi utilizado. ROMs, saves, estados e capturas de jogo permanecem fora do Git. Drive não atualizado; seu pacote não passa automaticamente a ser v16.**

## Referências

- [pret/pokefirered, `battle_script_commands.c`, ce6406d](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c): `Cmd_getexp`, participantes, distribuição de EXP e atualização de atributos em level-up.
- [pret/pokefirered, `battle_controller_player.c`, ce6406d](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_controller_player.c): `Task_GiveExpToMon`, EXP persistente via `SetMonData` em duplas. Os offsets da ROM expandida não são transplantados do original.
- [Auditoria de hazards no jogador](AUDITORIA_V16_HAZARDS_JOGADOR.md): observação por PID, ordem temporária da equipe e validações da UI; cinco métodos reexecutados nesta etapa.
- [Auditoria anterior de hazards/KO](AUDITORIA_V16_HAZARDS_KO.md): dano de entrada e referências fixadas das fórmulas.
- [Especificação v16](MOTOR_V16.md): correção original, hashes e limitações.
