# Auditoria v16 — Spikes em camadas e hazards combinados em duplas

**04/11/2026 — FireRed Gen 1–9 / VYK-57.** mGBA 0.10.5, ROM v16 exata, somente equipes e estados sintéticos. **Auditoria: ROM, payload e aplicador inalterados; não há v17 nesta etapa.**

## Defeito confirmado, ainda não corrigido

A v16 executa **Spikes antes de Stealth Rock mesmo quando Stealth Rock foi colocado primeiro**. O oráculo moderno fixado exige a **ordem de criação dos hazards**, não uma prioridade fixa por espécie de hazard.

O HP final pode coincidir e esconder o defeito. Por isso o teste compara os eventos intermediários de HP **e a sequência das mensagens**, inclusive nos casos em que ambos causam 100 de dano. A divergência também aparece quando Stealth Rock deveria derrubar o entrante imediatamente, sem executar Spikes.

**Um teste negativo com resultado `ok` confirma a reprodução do defeito; não aprova a mecânica moderna.** A suíte separa expressamente esses casos dos controles positivos com Spikes colocado primeiro.

## Matriz nova

Arquivo: `tests/test_motor_v16_combined_hazards_mgba.py`. Descoberta conferida: **quatro métodos distintos**, sem classes auxiliares importadas sob alias global.

| Grupo | Configuração | Subcasos | Classificação |
|---|---|---:|---|
| Spikes primeiro | 1/2/3 camadas × reserva saudável, KO no primeiro hazard, KO no segundo | **9** | Controle positivo |
| Stealth Rock primeiro | 1/2/3 camadas × HP 400, HP 100, HP igual à soma dos danos | **9** | Caracterização negativa da ordem |
| Limite/repetição, Spikes primeiro | Ator no banco 2; quatro usos de Spikes e dois de Stealth Rock | **1** | Controle positivo |
| Limite/repetição, Stealth Rock primeiro | Mesmas tentativas com ordem de criação inversa | **1** | Caracterização negativa da ordem |
| **Total novo** | **Dois métodos positivos e dois negativos** | **20** | **10 controles positivos + 10 reproduções negativas** |

Nos dois grupos de nove casos, o ator é o banco 0. Os dois controles de limite usam o banco 2. Não se afirma a matriz completa de todas as combinações em ambos os atores.

Os golpes são **Spikes 191**, **Stealth Rock 445** e **Rock Slide 157**, IDs locais da ROM. O ID oficial de Stealth Rock na referência é 446; não é transplantado para a ROM.

## Preparação e ações reais

O teste deriva das fixtures de duas reposições e reservas insuficientes:

- Os dois adversários originais começam vivos, com **1 HP**. Os reservas 2/3 têm PIDs distintos, HP máximo **400**, tipo Fire carregado na entrada e são afetados pelos dois hazards.
- Os hazards são colocados por comandos reais, em turnos separados. A cada turno, o teste confere o contador de Spikes, o estado de Stealth Rock, ausência de dano/troca prematuros, PP, histórico, identidade e EXP.
- Rock Slide derruba os dois ativos. A ordem relativa desses dois KOs pode variar; exige-se exatamente o par, antes dos eventos ordenados de entrada.
- A IA seleciona as reservas. O teste observa a cada frame os eventos de HP por PID, índices de banco e mensagens. Não há escrita em HP, RNG, hazards, histórico, índices ou EXP durante a execução para forçar a sequência.
- O segundo reserva começa sempre com **400 HP** e sobrevive. Se o primeiro cair na entrada, o segundo ocupa o mesmo banco 1; o banco 3 fica ausente, máscara **`0x08`**. Se ambos sobreviverem, ocupam bancos distintos, sem ausentes.
- Há um turno posterior com Splash: sem nova perda de HP ou troca, com custos de PP coerentes apenas para os bancos presentes e continuidade no menu de batalha.

A fixture é sintética; os atributos e PP de preparação não certificam legalidade de equipe. O golpe de área serve para produzir KOs reais: não é uma auditoria da fórmula moderna de Rock Slide ou de sua chance de flinch.

## Dano e ordem esperada

Para o entrante Fire com HP máximo 400:

| Camadas de Spikes | Dano de Spikes | Dano de Stealth Rock | Spikes primeiro, observado e esperado | Stealth Rock primeiro, esperado moderno |
|---:|---:|---:|---|---|
| 1 | **50** | **100** | **400→350→250** | **400→300→250** |
| 2 | **66** | **100** | **400→334→234** | **400→300→234** |
| 3 | **100** | **100** | **400→300→200** | **400→300→200**, mas mensagens em ordem inversa |

Spikes usa as frações 1/8, 1/6 e 1/4, arredondadas para baixo. Stealth Rock usa a efetividade de Rock contra Fire: 1/4 do HP máximo neste recorte. Não se generaliza o dano de 100 a todos os tipos.

A v16 produz a coluna **Spikes primeiro** nas duas ordens de colocação. Com três camadas, só olhar os números seria insuficiente: o teste exige as mensagens de Spikes (`Inimigo A sofre\ncom os ESPINHOS!`) e Stealth Rock (prefixo `Pedras pontiagudas feriram`) na ordem observada, e compara essa lista com a ordem moderna independente.

### KO expõe a diferença de causa

Com **Stealth Rock colocado primeiro** e primeiro reserva entrando com **100 HP**:

| Camadas | V16 observada | Esperado moderno |
|---:|---|---|
| 1 | Spikes **100→50**, depois Stealth Rock **50→0** | Stealth Rock **100→0**; nenhum Spikes nesse entrante |
| 2 | Spikes **100→34**, depois Stealth Rock **34→0** | Stealth Rock **100→0**; nenhum Spikes nesse entrante |
| 3 | Spikes **100→0**; nenhum Stealth Rock nesse entrante | Stealth Rock **100→0**; nenhum Spikes nesse entrante |

A sobrevivência final é a mesma nesses casos, mas o processamento e, na terceira linha, a causa exibida do KO estão errados em relação ao oráculo moderno. Não foi demonstrado aqui um efeito adicional sobre habilidades ou itens.

Quando **Spikes é colocado primeiro**, os controles de KO usam HP inicial 50/66/100 para morrer já em Spikes e 150/166/200 para morrer no segundo hazard. O próximo hazard não atinge o membro já desmaiado; a reposição seguinte recebe a sua própria sequência completa. Essa interrupção correta na ordem fixa não corrige a falta de ordenação por criação.

## Camadas, repetição e preservação

Os controles com ator 2 fazem três colocações de Spikes, uma de Stealth Rock e depois mais uma tentativa de cada. O estado continua com **três camadas e um Stealth Rock**, e os reservas saudáveis sofrem somente **100 + 100**. A ordem inicial é invertida no controle negativo correspondente; a divergência das mensagens persiste.

Na referência, camadas adicionais chamam `SideRestart` sobre o estado existente, sem criar outro `effectOrder`. Uma tentativa repetida de Stealth Rock não cria um novo hazard. Não se pode usar o último uso de Spikes como se fosse a criação de um hazard novo.

As verificações herdadas exigem checksums válidos, PID/OT e nível coerentes entre equipe e bancos presentes, HP positivo dos ativos, PP persistentes e marcador `0x800` limpo. Os bancos recém-ocupados começam com histórico zero. Cada participante do jogador recebe a EXP nativa da fixture:

- Dois KOs: **560→698**, nível 10.
- Três KOs, com o primeiro reserva derrubado: **560→767**, nível 11.

Os outros membros não ganham EXP. O recálculo nativo de HP do jogador ao subir de nível não é classificado como dano de entrada adversário. A distribuição de EXP é a nativa observada, **não certificação da fórmula moderna**.

## Causa no código e próximo trabalho

Em `patches/motor_v8/motor_v8.c`, herdado pela v16, `hook_switchineffects_v8` chama `ORIG_SWITCHINEFFECTS()` antes das etapas customizadas. Isso permite a execução dos Spikes nativos primeiro. Depois vêm o complemento de Spikes sob condições de aterramento, Stealth Rock, Toxic Spikes e Sticky Web em etapas fixas. Não há nesse fluxo um agendamento baseado na ordem de colocação dos hazards.

O emulador confirma a divergência prevista por esse fluxo **no recorte desta auditoria**. Não é um defeito causado pelo wrapper de phazing por nível introduzido na v16.

**Próximo trabalho recomendado: correção dirigida da ordem de hazards**, mantendo estes negativos como reprodução na base e exigindo a ordem moderna na nova saída. Não basta trocar globalmente Spikes e Stealth Rock: isso quebraria a ordem oposta que já está correta. O desenho deve considerar criação, incremento de camadas, remoção/recriação, limpeza por batalha, troca de lados (Court Change), colocação indireta e reinício das etapas a cada entrada/KO. Esses pontos são requisitos para uma correção futura, não validações realizadas nesta etapa.

## Execuções finais

| Processo desta etapa | Métodos | Tempo | Resultado |
|---|---:|---:|---|
| Matriz combinada: dois positivos e dois negativos, 20 subcasos | **4** | **593,552 s** | **OK, sem skips** |
| Duas reposições anteriores, jogador e IA (2), build v16 (5), treino EV/IV (9) | **16** | **291,498 s** | **OK, sem skips** |

**20 métodos distintos executados, nenhum skip, ambos os processos com código zero.** São 16 regressões reexecutadas agora, dois métodos positivos novos e dois de caracterização negativa. **Não são 20 aprovações de fidelidade moderna:** os dois negativos contêm 10 subcasos que reproduzem a ordem incorreta.

Os 12 subcasos das duas regressões de reposição não são somados aos 20 novos. Sondas preliminares, incluindo uma chamada cujo tempo de espera do terminal se esgotou, não integram a contagem final; a execução integral acima terminou e teve seu código de saída verificado. Não houve soma de resultados históricos nem reexecução integral de todas as suítes anteriores.

Manifesto do pacote atualizado e verificado: **240 entradas**, sem incluir o próprio manifesto. Hashes da ROM v16, entrada v15 e payload conferidos novamente e inalterados.

## Reprodução

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V16_ROM=/privado/motor_v16.gba
export MOTOR_V16_BASE=/privado/motor_v15.gba
export MGBA_CORE=/privado/mgba_libretro.so
export TREINO_TEST_ROM="$MOTOR_V16_ROM"
python3 -m unittest test_motor_v16_combined_hazards_mgba -v
python3 -m unittest \
  test_motor_v16_doubles_hazards_ko_mgba.MotorV16DoublesHazardsKOTests.test_dois_kos_por_golpe_de_area_selecao_distinta_e_hazard_nas_duas_entradas \
  test_motor_v16_doubles_hazards_ko_mgba.MotorV16DoublesHazardsKOTests.test_dois_kos_adversarios_reposicao_distinta_exp_e_dano_de_entrada \
  test_motor_v16 test_treino_ev_mgba -v
```

A suíte nova é intencionalmente vinculada ao SHA da **v16 defeituosa**: uma versão corrigida não deve ser aprovada apenas por reutilizar suas expectativas de caracterização. As funções `entry_events` e `messages_for` calculam separadamente a ordem moderna; os negativos exigem explicitamente divergência, em vez de redefinir a regra moderna como a ordem fixa.

| Artefato inalterado | SHA-256 |
|---|---|
| ROM v16, 33.554.432 bytes | `644b140dc4fd1f4fab4c7ed9304fb266865d3e81825140c01c2c275564dc0fcc` |
| Entrada v15 | `a6b454f7cbafad8c05e1b8aa2028087a596bbeff4f0184c826a92ebb7e554147` |
| Payload v16, 300 bytes | `f1946a84a7932215b83e6d01e4d6794e4b1dbab334fb49c2236b48ad185c0ceb` |

## Limites

A matriz combinada nova cobre **reposições adversárias em duplas**, não a seleção do jogador, singles, trocas voluntárias ou pivôs. As regressões de seleção do jogador usam hazards separados e não ampliam esse escopo. Não cobre Toxic Spikes/Sticky Web combinados, todas as condições de aterramento, habilidades/itens, remoção/recriação dos hazards, Court Change, todas as entradas indiretas, derrota de ambas as equipes, link/multi ou campanha. Teachy TV e migração de saves pessoais continuam fora.

O ambiente temporário foi reconstruído com mGBA 0.10.5 e a cadeia parcial→estojo v2→motor v5…v16, verificando SHA de entrada antes de cada aplicação e gerando arquivos novos. A base privada foi apenas lida do Drive. Nenhum save pessoal foi usado. **ROMs, saves, estados e capturas ficam fora do Git. Drive não atualizado. Engine ainda parcial e defeito de ordem aberto.**

## Referências fixadas

- [Pokémon Showdown, `sim/battle.ts`, 035c1a1, L1002–1007](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/battle.ts#L1002-L1007): `effectOrder` desempata hazards na ordem em que foram criados; `comparePriority` e `initEffectState` ordenam e atribuem esse contador.
- [Pokémon Showdown, `sim/side.ts`, 035c1a1, L413–443](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/side.ts#L413-L443): `addSideCondition`, estado novo versus `SideRestart`, preservando a identidade/ordem ao acrescentar camadas.
- [Pokémon Showdown, `data/moves.ts`, 035c1a1, Spikes](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L17496-L17528): limite de três camadas e frações de dano.
- [Pokémon Showdown, `data/moves.ts`, 035c1a1, Stealth Rock](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L17810-L17836): condição de lado e dano por efetividade.
- [Implementação herdada](../patches/motor_v8/motor_v8.c), [auditoria de duas reposições](AUDITORIA_V16_DUPLAS_KO_REPOSICAO.md) e [reservas insuficientes/encerramento](AUDITORIA_V16_DUPLAS_RESERVAS_FIM.md).
