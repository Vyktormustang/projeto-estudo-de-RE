# Rollout/Ice Ball — potência confirmada, PP extra com Protect ainda aberto

**02/11/2026 — auditoria no motor v13 exato, sem alteração da ROM.**

## Conclusão

A progressão de potência está correta nos cenários medidos:

- **30 → 60 → 120 → 240 → 480** em cinco impactos.
- Com **Defense Curl usado naturalmente**: **60 → 120 → 240 → 480 → 960**.
- Eerie Spell zerar os PPs não interrompe nem reduz essa progressão.
- Reiniciar uma sequência volta a 30, ou 60 enquanto persiste o bônus de Defense Curl.
- Ice Ball compartilha esse comportamento nos casos testados.

**Porém foi encontrado um desvio de PP, ainda não corrigido:** Protect interrompendo uma sequência já ativa faz o v13 descontar um PP extra de Rollout ou Ice Ball. Isso contraria a referência moderna consultada, que não cobra novo PP por uma continuação travada. O reset de potência funciona; o gasto de PP é o problema.

**Não há v14 nesta etapa.** Foram entregues reprodução automatizada, diagnóstico do fluxo e critérios de correção. Não foi criado ou validado um patch. A prioridade seguinte passa a ser corrigir esse desconto sem alterar o gasto do primeiro uso nem deixar marcadores afetarem outras ações.

## 1. Método e isolamento

Arquivo: `tests/test_rollout_power_mgba.py`. Ambiente: mGBA libretro **0.10.5**, somente estados sintéticos.

- Jogador nível 10/EXP 560 preparado pelas fábricas corrigidas; adversário da fixture selvagem gerado naturalmente (nível 3 nesta execução), sem reescrever sua EXP.
- Atributos e HP deliberadamente sintéticos: atacante com Atk 300, defensor com Def 100, HP suficiente para sobreviver à sequência. Atributos/HP/movesets/PP relevantes sincronizados entre batalha e equipe.
- Tipos de batalha Normal/Normal: sem STAB de Rock/Ice e com efetividade neutra. Battle Armor no defensor impede críticos. Acurácia elevada isola o caso de impactos consecutivos.
- Defense Curl, Protect, Eerie Spell, histórico e travas vêm de ações da batalha. Não se injeta o contador de Rollout nem o bit de Defense Curl.
- O observador avança **um frame por vez**, inclusive durante confirmação de mensagens. Captura `gBattleMovePower` e `gCurrentMove` quando o **HP real** do defensor muda; não usa o valor global depois que outro golpe o sobrescreveu.
- Cada impacto deve produzir exatamente uma alteração de HP, a potência esperada e dano pertencente ao conjunto calculado com os 16 fatores aleatórios nativos, de 85% a 100%.
- Ao fim de cada turno exige-se o menu `vai fazer?`. PPs de batalha/equipe, checksums e HP da equipe são conferidos.

Não se exige que o **dano** dobre exatamente: existem o termo constante da fórmula, truncamentos inteiros e RNG. O oráculo de dano é restrito à fórmula física FireRed, neutra e sem modificadores. **Não é uma validação geral da fórmula de dano Scarlet/Violet.**

### Por que os danos baixos anteriores pareciam não crescer

Na auditoria anterior, o atacante selvagem era nível 3, com Atk 100 contra Def 500. Nesse cenário, a fórmula nativa produz estes conjuntos de dano possíveis:

| Potência | Dano possível |
|---:|---:|
| 30 | 2–3 |
| 60 | 2–3 |
| 120 | 2–3 |
| 240 | 3–4 |
| 480 | 5–7 |

A amostra exploratória anterior **2, 3, 2, 3, 6** cabe nesses conjuntos. Não era evidência suficiente de potência travada. A nova suíte separa esse problema de observação do defeito real de PP encontrado com Protect.

## 2. Casos positivos automatizados

| Caso | Resultado |
|---|---|
| Rollout, sem Eerie Spell | Cinco potências 30..480; PPs 4→3 no primeiro uso e estáveis nas continuações; sexta ação inicia nova sequência a 30 e consome novo PP. |
| Rollout, com Eerie Spell | Primeiro uso 4→3 e dreno 3→0; cinco potências 30..480; depois Struggle, sem underflow. |
| Defense Curl + Rollout, sem dreno | Preparação por golpe 111, +1 Def e bit próprio; potências 60..960; reinício a 60. |
| Defense Curl + Rollout, com dreno | Potências 60..960 mesmo com PP zero; depois Struggle. |
| Ice Ball, sem dreno | Potências 30..480 e reinício a 30; gasto próprio apenas no início de cada sequência. |
| Defense Curl + Ice Ball, com dreno | Potências 60..960 a PP zero; depois Struggle. |
| Protect depois de Eerie Spell já zerar PP | Para ambos os golpes, Protect bloqueia dano e encerra a trava; PP permanece zero e a ação seguinte é Struggle. |

Ice Ball é um golpe histórico mantido pelo projeto Gen 1–9; a referência consultada o marca como `Past`. Este teste **não afirma que Ice Ball esteja disponível em Scarlet/Violet**.

## 3. Defeito reproduzido — Protect cobra PP de uma continuação

Reproduzido com **Rollout e Ice Ball**, cada um **com e sem Defense Curl**: quatro subcasos. Sem Eerie Spell nessa reprodução, para não confundir o desconto extra com dreno.

| Ação | PP esperado pela referência moderna | PP observado no v13 |
|---|---:|---:|
| Antes do primeiro impacto | 4 | 4 |
| Primeiro impacto | 3 | 3 |
| Segundo impacto | 3 | 3 |
| Continuação bloqueada por Protect | **3** | **2** |
| Novo uso após a interrupção | **2** | **1** |

Protect é selecionado pela interface e executado no terceiro turno da sequência. Não há dano nesse turno. A trava é removida; Defense Curl, quando presente, permanece. No turno seguinte a potência reinicia corretamente em 30/60. **A perda adicional de PP é confirmada tanto em batalha quanto na equipe criptografada, com checksum válido.**

### Resultado inicial e caracterização final

A primeira execução permanente usava a expectativa moderna de 3 PP após Protect e **falhou** nos dois subcasos então escritos (Rollout com/sem Defense Curl), observando 2 PP. A investigação foi estendida a Ice Ball e ao caso de PP zero.

O teste final chama-se explicitamente:

`test_reproduz_pp_extra_v13_em_protect_mas_potencia_reinicia`

Ele exige a divergência em relação a 3 PP e caracteriza os 2 PP observados na ROM v13 identificada por hash. **Seu resultado `ok` significa reprodução bem-sucedida de um defeito aberto, não aprovação da mecânica moderna.** Não se deve herdar essa expectativa como comportamento desejado de uma futura versão corrigida.

## 4. Diagnóstico de código e endereços

Na ROM exata, ambos os golpes têm efeito **117**, potência base **30** e apontam para o mesmo script nativo, **`0x08186348`**. A suíte verifica o ponteiro e os primeiros 13 bytes:

```text
00 02 1d 01 00 10 00 00 55 63 18 08 03
```

A sequência é:

1. `attackcanceler`;
2. `attackstring`;
3. `jumpifstatus2 BS_ATTACKER, STATUS2_MULTIPLETURNS, RolloutCheckAccuracy`;
4. `ppreduce` se a trava já não estiver presente.

O código nativo de `attackcanceler`, no ramo de Protect, chama **CancelMultiTurnMoves**, que limpa a trava e o timer de Rollout. Portanto, o teste posterior no script já encontra a trava apagada e executa `ppreduce`. É a ordem correspondente ao comportamento observado.

Isso identifica um fluxo herdado de Gen 3; **não foi demonstrado que o problema tenha sido introduzido pelo v13**, nem foram testadas dinamicamente todas as versões anteriores. O helper de Eerie Spell não participa da reprodução de PP extra, que usa Splash no jogador até o turno de Protect.

| Dado/endereço | Uso |
|---|---|
| `0x02021864` | `gBattleMovePower`, potência observada no impacto |
| `0x02021586` | `gCurrentMove` |
| `0x02021792` | `gDynamicBasePower`, preenchido pelo cálculo nativo de Rollout |
| `0x02021410 + 0x5C*b` | Pokémon de batalha; HP `+0x2A`, PP `+0x25`, status2 `+0x54` |
| `status2 & 0x1000` | sequência de múltiplos turnos |
| `status2 & 0x40000000` | bônus de Defense Curl |
| `0x020215D4` | histórico `gLastMoves` |
| ROM `0x1000000 + 12*move` | tabela expandida de golpes |
| ROM `0x100A000 + 4*117` | ponteiro do script compartilhado |
| `0x08062E81` | entrada Thumb nativa do cálculo de Rollout, comando `0xB3` |

## 5. Referências fixadas e interpretação

**Pokémon Showdown**, commit `035c1a1f3c2ed286cda4c0d8623800699cd2c1c0`:

- [Rollout — potência e Defense Curl](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L15360-L15425).
- [Ice Ball — mecanismo equivalente](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L9238-L9275).
- [runMove — desconto próprio apenas quando não há lockedMove](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/battle-actions.ts#L335-L349).

**pret/pokefirered**, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`:

- [Script Rollout: ordem de cancelamento/teste de trava/PP](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/data/battle_scripts_1.s#L1592-L1602).
- [Protect em attackcanceler](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c#L896-L907), [ppreduce](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c#L1122-L1168) e [rolloutdamagecalculation](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c#L8161-L8194).
- [CancelMultiTurnMoves](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_util.c#L203-L214).
- [Fórmula nativa de dano](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/pokemon.c#L2385-L2649) e [fator aleatório](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c#L1557-L1572).

O esperado moderno foi obtido dessa referência de implementação; não foi executado um teste em cartucho Scarlet/Violet. Os fatos sobre o v13 vêm da medição mGBA.

## 6. Execução final — 27 verificações, incluindo reprodução de defeito

| Suíte | Resultado | Tempo |
|---|---|---:|
| `test_rollout_power_mgba.py` | **10/10**: 2 testes do oráculo, 7 integrações positivas e **1 caracterização de defeito**, com 4 subcasos | 273,618 s |
| `test_eerie_history_mgba.py` | **8/8** | 116,917 s |
| `test_treino_ev_mgba.py` | **9/9** | 33,299 s |

Nenhum pulado. Não se somam as execuções exploratórias, a primeira execução que falhou, nem a repetição isolada dos dois testes de Protect. As suítes completas `test_motor_v13*.py` e de auditoria EXP **não foram reexecutadas nesta etapa**; não houve mudança de motor ou de suas fábricas compartilhadas.

```sh
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
ROLLOUT_POWER_ROM=/caminho/motor_v13.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_rollout_power_mgba.py' -v

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
EERIE_HISTORY_ROM=/caminho/motor_v13.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_eerie_history_mgba.py' -v

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
TREINO_TEST_ROM=/caminho/motor_v13.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_treino_ev_mgba.py' -v
```

SHA-256 v13, conferido antes/depois da nova suíte, permanece:

`71756c820ebb71c0c64735b0e8f36cf420da29ac419f8ee09a39109d9cb4951c`

Nenhum payload/aplicador/catálogo mudou. Não foram criadas ROMs, saves ou estados pessoais, nem incluídos ativos protegidos no Git. Continuam 15.008 aprendizados, 708/729 omissões restauradas e quatro golpes/21 registros adiados. Drive não atualizado nesta etapa.

## 7. Próximo passo e critérios antes de publicar correção

A hipótese de solução é preservar a informação de que a ação **já era uma continuação**, antes de Protect apagar a trava, sem impedir que Protect interrompa a sequência. **É proposta, não patch testado.**

Antes de publicar uma nova ROM:

1. Base v13 deve continuar reproduzindo PP extra; saída corrigida deve manter 3 PP no turno protegido e consumir um novo PP apenas no reinício.
2. Primeiro uso bloqueado deve continuar gastando PP; continuacões bloqueadas não devem gastar novamente. Testar ambos os golpes, PP zero e positivo e Defense Curl.
3. Verificar que nenhum marcador de isenção de PP afete outro golpe, outro banco ou o turno seguinte, inclusive caminhos que não chegam a `ppreduce`.
4. Ampliar controles para Pressure, Detect, miss de acurácia e ambos os lados/duplas, além das regressões de batalha/estojo/EV.
5. Verificar SHA de entrada, gravar somente saída nova e provar preservação byte a byte fora das escritas planejadas.

Não extrapolar esta auditoria para Fury Cutter, Metronome (item), Echoed Voice, todas as habilidades/itens ou todas as formas de interrupção. A potência de Rollout deixa de ser uma dúvida neste recorte; **Protect/PP permanece como defeito aberto prioritário**.
