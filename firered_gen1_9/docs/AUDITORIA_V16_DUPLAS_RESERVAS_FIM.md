# Auditoria v16 — reservas insuficientes e encerramento em duplas

**04/11/2026 — FireRed Gen 1–9 / VYK-57.** ROM v16 exata, mGBA 0.10.5, equipes e estados exclusivamente sintéticos. **ROM, payload e aplicador inalterados; sem v17 nesta etapa.**

## Resultado

**21/21 verificações aprovadas, sem skips**, incluindo **cinco métodos novos / 44 subcasos**. Os dois processos finais terminaram com código zero. Nenhum novo defeito de engine foi demonstrado neste recorte.

Com uma reserva sobrevivente, a batalha continua com o outro banco marcado como ausente. Sem sobreviventes, o jogo conclui vitória ou derrota, preserva a EXP esperada e retorna ao modo de campo. A cura após derrota restaura HP e PP; o observador distingue essa recuperação dos KOs e do dano de entrada. A engine continua parcial.

## Matriz nova

Arquivo: `tests/test_motor_v16_doubles_endings_mgba.py`.

| Método / cenário | Subcasos | Exigência |
|---|---:|---|
| Adversário com um sobrevivente | 2 hazards × 2 atores × 2 configurações = **8** | Uma reserva viva, ou primeira reserva cai e a segunda sobrevive; banco 3 ausente e outro turno |
| Vitória | 2 × 2 × 3 configurações = **12** | Sem reserva, última reserva cai, ou ambas caem na entrada; EXP concluída e volta ao campo |
| Jogador com um sobrevivente | 2 × 2 × 2 = **8** | Escolha real pela UI, banco 2 ausente e um único menu de ação no turno seguinte |
| Derrota em contexto sintético de treinador | 2 × 2 × 3 = **12** | Sem reserva ou KO de uma/duas reservas; resultado de derrota, retorno e cura |
| Whiteout em dupla selvagem sintética | 2 hazards × 2 adversários = **4** | Aceitar o próximo Pokémon, sem escolher fuga; último reserva cai, texto “apagou!”, fim e cura |
| **Total** | **44** | **Cinco métodos** |

Spikes **191**, uma camada; Stealth Rock **445**, testados separadamente. Rock Slide **157** derruba os dois ativos, que começam vivos com 1 HP. Os atores do jogador são os bancos **0/2** e os adversários são **1/3**. Os números são IDs locais da ROM.

Os dois desmaios iniciais vêm de uma execução real de Rock Slide, não de alteração de HP durante o turno. A fixture testa as consequências dos KOs, **não a fórmula moderna do dano de área, a chance de flinch ou a legalidade das equipes**.

## Preparação e preservação

O construtor deriva da auditoria anterior de duas reposições. Todos os membros começam no nível 10 e com EXP 560, PIDs distintos e OT coerente. Há um ovo e um slot vazio além dos quatro membros principais; não devem servir como reservas de batalha.

As cinco configurações dos reservas 2/3 são:

| Configuração | HP inicial dos reservas | Uso |
|---|---|---|
| Uma reserva | `400 / 0` | Um sobrevivente |
| Cadeia com sobrevivente | `dano / 400` | Primeiro cai, segundo mantém a batalha |
| Nenhuma reserva | `0 / 0` | Encerramento após o golpe de área |
| Última reserva cai | `dano / 0` | Um KO adicional por hazard |
| Ambas caem | `dano / dano` | Dois KOs adicionais por hazard |

`dano` é **50 para Spikes** e **100 para Stealth Rock**, com HP máximo 400 e tipo Fire carregado nativamente. O sobrevivente fica com **350/400** ou **300/400**.

Os hazards são colocados por golpes reais no primeiro turno, sem dano imediato aos ativos. Depois de começar a execução, não se escrevem HP, hazards, índices, alvo, RNG, EXP ou histórico para obter os resultados. Menus e escolhas são operados por botões.

O jogador que pode ganhar EXP começa com HP/maxHP sintéticos 32, em vez dos 4.000 da fixture anterior: três ou quatro KOs cruzam o nível 11 e provocam recálculo nativo. Isso evita um overflow artificial de HP na preparação. Nas sondas, o recálculo mudou **32→30**; essa mudança não é classificada como dano de hazard.

## Bancos ausentes e continuidade

O marcador de bancos ausentes da ROM expandida fica em `0x020215AD`, endereço já utilizado pelos hooks do próprio projeto.

- **Um adversário sobrevivente:** o banco 1 ocupa a reserva 2 ou 3, e o banco **3** fica ausente: máscara **`0x08`**. Os índices finais são `(0, reserva, 1, 1)`.
- **Um jogador sobrevivente:** o banco 0 ocupa a reserva 2 ou 3, e o banco **2** fica ausente: máscara **`0x04`**. Os índices finais são `(reserva, 0, 1, 1)`.

Um índice antigo no banco ausente não é tratado como Pokémon ativo. A correspondência HP/PP/PID/OT/nível entre batalha e equipe é exigida apenas dos bancos presentes, que precisam ter HP positivo. A máscara, os índices e os eventos de entrada são verificados separadamente.

No turno posterior:

- Com um adversário, os dois jogadores escolhem Splash e somente o adversário presente executa seu Splash. Não há novos danos ou trocas; os PP/histórico do banco ausente ficam inalterados.
- Com um jogador, apenas **uma** escolha de ação é enviada. O sobrevivente usa seu próprio Protect, Rock Slide não causa dano, os adversários gastam os PP de suas ações e o banco ausente não ganha histórico nem gasta PP.

As listas de mudanças de HP são observadas **por PID**, inclusive enquanto a tela de equipe reordena temporariamente os registros. O KO do primeiro reserva seguido de sobrevivência do segundo produz nova entrada no **mesmo banco**, não duplica o sobrevivente nos dois bancos.

## Vitória e EXP após três/quatro KOs

A vitória exige resultado **1**, saída da flag de batalha e retorno ao callback do modo de campo observado antes da fixture, com estabilização adicional de 120 frames. Texto de desmaio ou de vitória sozinho não basta.

| Total de adversários derrubados | EXP de cada um dos dois participantes | Nível final |
|---:|---:|---:|
| 2, sem reservas | **560→698** | **10** |
| 3, uma reserva derrubada por hazard | **560→767** | **11** |
| 4, duas reservas derrubadas por hazard | **560→836** | **11** |

A distribuição é a nativa da fixture: 69 por KO para cada participante. **Não certifica a fórmula moderna de Scarlet/Violet.** Os PIDs/OT, a EXP dos demais membros e os checksums são preservados. O HP do jogador precisa ser positivo e não ultrapassar o máximo após o recálculo.

Na vitória, o parceiro mais lento não executa o Splash que ainda estava na fila; não deve gastar seu PP. Quando há um sobrevivente adversário, essa ação acontece normalmente antes do retorno ao menu. O teste distingue esses dois custos, além de conferir os PP de todos os membros.

## Derrota, seleção e cura posterior

A derrota exige resultado **2**, flag fora de batalha e retorno ao callback de campo, também estabilizado. O observador guarda o **primeiro estado com resultado não zero** e a lista de mudanças de HP até esse instante. Assim, pode exigir HP zero nos quatro membros não-ovo antes da cura, sem confundir a recuperação posterior com dano ou ressurreição indevida durante a batalha.

Quando o primeiro reserva cai, a tela de equipe reabre e o segundo é escolhido pela UI. Se ele também cai, a batalha termina sem tentar usar o ovo, o slot vazio ou um membro já desmaiado. Se sobrevive, continua com apenas um banco do jogador presente.

Antes da cura, só o adversário que usou Rock Slide gasta PP no turno encerrado por derrota; a ação do parceiro fica interrompida. Depois de voltar ao campo:

- HP é restaurado ao máximo nos cinco membros presentes da equipe, inclusive os que já estavam desmaiados no preparo.
- PP é restaurado de acordo com a tabela de golpes **da própria ROM**, não com os valores artificiais da fixture. O teste confirma ausência de PP Ups.
- PID/OT, nível, EXP e checksum permanecem coerentes.

O cenário com flag de treinador é sintético, derivado de encontro, e as sondas exibiram falas do rival. Isso não é certificação do encerramento de qualquer treinador de campanha. Há quatro controles adicionais com flags **`0x05`**, dupla selvagem sintética, sem flag de treinador. Neles a pergunta “Usar o próximo Pokémon?” recebe **A**, não uma tentativa de fuga; o teste exige “apagou!” e ausência de texto de tentativa de escapar, além do resultado 2, retorno e cura.

Não são certificados valor de dinheiro perdido, destino específico da recuperação, diálogos de todos os treinadores ou perda simultânea das duas equipes. “Retorno ao campo” identifica o callback/estado de jogo, não afirma retorno às mesmas coordenadas após whiteout.

## Observador e sondas preliminares

A observação de mensagens tem limite de **128** confirmações com saída antecipada; a finalização de batalha tem limite de **160**, sem espera infinita. Os dois participantes podem receber EXP e abrir quadros de level-up; o limite é do observador, não uma alteração da engine.

Três cuidados do observador são tratados explicitamente:

1. A queda de HP por recálculo de atributos no level-up é separada dos eventos do lado adversário atingido pelos hazards.
2. A cura depois da derrota é separada pelo primeiro estado terminal. No contexto selvagem, a pergunta de continuação é aceita explicitamente; uma sonda que apenas confirmava tudo com B chegou a tentar fugir, e não é usada como aprovação do controle final de whiteout.

3. A ordem dos dois alvos de Rock Slide não é fixa. A execução integral inicial terminou com **uma falha, em 666,411 s**, no subcaso selvagem Spikes / ator 3: os slots caíram na ordem **1→0**, mas o teste exigia **0→1**. O observador final exige exatamente os dois KOs antes da entrada, aceitando qualquer ordem entre eles; mantém a ordem exata dos eventos de hazard, as transições de banco e todas as verificações posteriores. A sonda do subcaso corrigido passou, e a reexecução integral dos cinco métodos também passou. Não houve correção de ROM.

Sondas, a execução inicial com falha e capturas/estados temporários não integram a contagem final. Estados/capturas ficam fora do Git. A descoberta do unittest foi conferida previamente: **exatamente cinco métodos novos**, sem importar uma classe auxiliar sob alias global.

## Execuções finais

| Processo | Métodos | Tempo | Resultado |
|---|---:|---:|---|
| Matriz nova de reservas/encerramento, reexecução integral | **5** | **652,107 s** | **OK, sem skips** |
| Duas reposições anteriores, jogador e IA (2), build v16 (5), treino EV/IV (9) | **16** | **280,462 s** | **OK, sem skips** |

**Total final: 5 + 16 = 21 métodos, sem repetições na contagem.** As regressões anteriores de duas reposições foram chamadas por nome, não pelo módulo inteiro. Seus 12 subcasos não são somados aos 44 novos. Não houve reexecução integral das suítes históricas, nem soma de resultados de etapas anteriores.

O ambiente temporário foi reconstruído: mGBA 0.10.5 e cadeia parcial→estojo v2→motor v5…v16, com SHA de entrada verificado antes de cada aplicação e saídas novas. A base privada foi somente baixada em leitura do Drive. O checkout foi realinhado ao commit publicado `ec48126` apenas após confirmar igualdade integral dos arquivos locais; nenhum trabalho divergente foi descartado.

## Reprodução

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V16_ROM=/privado/motor_v16.gba
export MOTOR_V16_BASE=/privado/motor_v15.gba
export MGBA_CORE=/privado/mgba_libretro.so
export TREINO_TEST_ROM="$MOTOR_V16_ROM"
python3 -m unittest test_motor_v16_doubles_endings_mgba -v
python3 -m unittest \
  test_motor_v16_doubles_hazards_ko_mgba.MotorV16DoublesHazardsKOTests.test_dois_kos_por_golpe_de_area_selecao_distinta_e_hazard_nas_duas_entradas \
  test_motor_v16_doubles_hazards_ko_mgba.MotorV16DoublesHazardsKOTests.test_dois_kos_adversarios_reposicao_distinta_exp_e_dano_de_entrada \
  test_motor_v16 test_treino_ev_mgba -v
```

| Artefato inalterado | SHA-256 |
|---|---|
| ROM v16, 33.554.432 bytes | `644b140dc4fd1f4fab4c7ed9304fb266865d3e81825140c01c2c275564dc0fcc` |
| Entrada v15 | `a6b454f7cbafad8c05e1b8aa2028087a596bbeff4f0184c826a92ebb7e554147` |
| Payload v16, 300 bytes | `f1946a84a7932215b83e6d01e4d6794e4b1dbab334fb49c2236b48ad185c0ceb` |

## Limites e próximo recorte

Só uma camada de Spikes ou Stealth Rock, separadamente. Não cobre hazards combinados, várias camadas, Toxic Spikes/Sticky Web, habilidades/itens/efeitos de entrada simultâneos, perdas simultâneas das duas equipes, troca voluntária/pivôs com banco ausente, link/multi ou campanha completa. Teachy TV e migração de saves pessoais permanecem fora.

Próximo recorte recomendado: **hazards combinados e múltiplas camadas nas reposições em duplas**, especialmente interrupção das etapas quando o primeiro hazard já causa KO. A engine permanece parcial.

**Sem saves pessoais. ROMs, saves, estados e capturas de jogo fora do Git. Drive não atualizado; seu pacote não passa automaticamente a ser v16.**

## Referências

- [pret/pokefirered, `battle_util.c`, ce6406d](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_util.c): `HandleFaintedMonActions`, concessão de EXP, reposição e bancos ausentes.
- [pret/pokefirered, `battle_script_commands.c`, ce6406d](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c): `HasNoMonsToSwitch` e marcação de bancos ausentes nos comandos de reposição.
- [pret/pokefirered, `battle_main.c`, ce6406d](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_main.c): fim por derrota e tratamento especial do rival.
- [pret/pokefirered, `battle_setup.c`, ce6406d](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_setup.c): `CB2_EndWildBattle`, `CB2_WhiteOut` e diferenças do encerramento de treinador. Offsets da versão original não são transplantados para a ROM expandida.
- [Auditoria anterior de duas reposições](AUDITORIA_V16_DUPLAS_KO_REPOSICAO.md) e [especificação da v16](MOTOR_V16.md).
