# Motor v16 — phazing de treinador sem falha por nível

**03/11/2026 — correção dirigida sobre v15 exato, FireRed Gen 1–9 / VYK-57.** Entrada verificada por SHA-256, saída em arquivo novo, somente saves/equipes sintéticos. Não é o projeto BAG_MOD da ROM histórica.

> **Adendo posterior (03/11/2026):** sem alterar a ROM, a auditoria de duplas/múltiplas reservas concluiu 29 verificações, incluindo cinco testes novos com 60 subcasos. Veja [AUDITORIA_V16_DUPLAS_PHAZING.md](AUDITORIA_V16_DUPLAS_PHAZING.md). Os 85 testes e a matriz de singles abaixo conservam o registro da entrega original; as lacunas de duplas foram reduzidas nesse recorte, não eliminadas integralmente.

## Defeito e comparação

A [auditoria v15](AUDITORIA_V15_PIVOS_PHAZING.md) demonstrou Dragon Tail e Circle Throw causando dano, mas sem trocar um alvo de nível superior apesar de haver reserva viva e contexto de treinador. O comando nativo `0x8F` ainda chama `TryDoForceSwitchOut`, que pode falhar por um sorteio baseado nos níveis.

A nova suíte primeiro reproduz esse defeito na **base v15**, depois cria fixtures próprias na **v16**. Não se transferem estados entre versões nem se herdam expectativas defeituosas para a saída corrigida.

| Golpe usado pelo adversário de nível inferior | Slots ativos do jogador após T1 / T2 / T3 na v15 | Na v16 |
|---|---|---|
| Dragon Tail, ID local 521 | **0 / 1 / 0** | **1 / 0 / 1** |
| Circle Throw, ID local 508 | **1 / 1 / 0** | **1 / 0 / 1** |

Roar (46) e Whirlwind (18) também exigem **1 / 0 / 1** na saída v16 com atacante de nível inferior. O nível do atacante não fica alterado; PP próprio cai de 20 para 19, 18 e 17. Cada troca limpa o histórico do banco que recebe o novo membro.

**Escopo:** retirar essa chance legada no phazing dos quatro golpes em batalha com flag de treinador. Não moderniza todas as regras de Roar/Whirlwind/Dragon Tail/Circle Throw, habilidades, prioridades, imunidades ou encontros selvagens.

## Implementação restrita

Payload Thumb de **300 bytes**, um wrapper do comando `0x8F`. Sem nova RAM persistente, alteração de save, catálogo ou payloads anteriores.

1. Fora de batalha com flag `BATTLE_TYPE_TRAINER = 8`, fora dos quatro golpes ou com bancos inválidos, chama a rotina nativa uma vez e retorna.
2. Se o nível do atacante já é maior/igual ao do alvo, também não interfere.
3. Com níveis válidos e atacante inferior, salva cursor, destino de falha, bancos, golpe e níveis; chama a rotina nativa **primeiro**, inclusive seu sorteio original.
4. Só se ela retorna exatamente ao destino de falha e o contexto permanece igual, restaura o cursor, equipara **temporariamente o nível de batalha** do atacante ao do alvo e chama o comando nativo uma segunda e última vez.
5. Restaura imediatamente o nível original, antes de devolver o controle ao motor. Não escreve nível/EXP na equipe nem recalcula atributos.

A segunda chamada não sorteia outra chance por nível, pois os níveis temporários são iguais. Continua passando pela validação nativa da equipe e pela seleção de reserva. **Sem reserva elegível, a segunda chamada também falha.** O wrapper não escolhe diretamente um slot nem força um índice de equipe.

Suction Cups/Ingrain e os bloqueios anteriores ao comando permanecem nos scripts/hooks existentes. O wrapper não torna um golpe protegido ou imune um impacto válido.

O consumo do sorteio da primeira tentativa é conservado. Quando uma falha antiga agora vira troca, passa a ocorrer a seleção aleatória de reserva que antes não acontecia; portanto **não se promete sequência global de RNG idêntica em batalhas modificadas**. Encontros selvagens seguem a chamada nativa única e não recebem a equiparação temporária.

### Escritas e guardas

| Local | Alteração/uso |
|---|---|
| ROM `0x10CFE3C..0x10CFE3F` | comando 8F: `0x08060DD1` → `0x090DA001` |
| ROM `0x10DA000..0x10DA12B` | payload, 300 bytes |
| RAM `0x02020374` | flags de batalha |
| RAM `0x02021586`, `0x020215A8`, `0x020215A9` | golpe, atacante, alvo |
| RAM `0x020215B0` | cursor do script |
| RAM `0x02021410 + 0x5C*b + 0x2C` | nível de batalha; temporário e restaurado |

**Dois intervalos físicos, 304 bytes escritos**, nem todos diferentes da base. O patcher exige v15 exato, payload exato, ponteiro anterior correto, área livre até `0x10DB000` e hash final. Testes restauram precisamente os dois intervalos e exigem igualdade integral com a entrada. A escrita exclusiva rejeita arquivo existente, symlink e hardlink.

Nenhum byte de catálogo, compatibilidade de TMs/HMs, estojo, encontros, eventos ou formato de save é alterado. A engine permanece com 15.008 registros de aprendizado e 708/729 omissões restauradas.

## Testes dirigidos

`tests/test_motor_v16_mgba.py`: dez métodos, incluindo a reprodução negativa separada da base.

- **Base v15:** as duas trajetórias defeituosas antigas são exigidas em fixtures criadas nela.
- **Nível inferior, treinador:** os quatro golpes efetuam três trocas consecutivas; PP/histórico e nível são verificados após cada turno.
- **Sem reserva viva:** os quatro golpes continuam sem trocar; não terminam a batalha indevidamente.
- **Suction Cups e Ingrain:** bloqueiam os quatro golpes mesmo com atacante inferior. Ingrain é criado por uso real do golpe, não por injeção do bit no meio da batalha.
- **Protect e imunidade de tipo:** bloqueiam Dragon Tail/Circle Throw, sem dano nem troca, mas com consumo próprio de PP. Protect é usado pela interface; tipos/habilidade de controle são condições sintéticas iniciais.
- **Encontros selvagens:** oito comparações v15/v16, quatro golpes usados pelo jogador e pelo adversário. Conferem resultado de batalha, flag de batalha ativa, índices, HP persistente e PP das equipes. O jogador de nível superior continua encerrando o encontro selvagem; não se afirma modernização das regras selvagens.
- **Histórico de pivôs/phazing:** os quatro positivos da auditoria v15 são reexecutados sobre v16: pivôs nas duas ordens, ida/volta forçadas nos dois lados e Suction Cups preservando histórico quando não há troca.

A cada turno dirigido são conferidos os níveis persistentes de ambos os membros por lado e a correspondência entre nível de batalha e equipe ativa, além dos controles herdados de PP/checksum, HP, menu e marcador `0x800`. O código só escreve temporariamente no nível do Pokémon em batalha; nenhum aumento de nível é aplicado à equipe.

## Execução final

- Dirigidos: **10/10, 252,272 s**, nenhum skip.
- Estrutura/build e treino EV/IV: **14/14, 18,681 s**, nenhum skip.
- Regressões positivas: **61/61, 1.457,680 s**, nenhum skip.

**Total final: 85/85 verificações, sem skips; todos os processos com código zero.** Inclui uma reprodução negativa do defeito na base v15, separada dos controles positivos na saída. Não significa 85 mecânicas modernas distintas. As 61 regressões são 20 de Eerie/HP/PP/KO, sete de famílias/estojo/save, seis de histórico, 13 de Protect/potência, sete de duplas/interrupções naturais e oito de duração de Encore/Disable.

A suíte `test_motor_v16_regressions` cria fixtures novas sobre a v16 verificada. Reexecuta os positivos anteriores de Eerie Spell/HP/PP/KO/EXP, famílias/estojo/save, histórico/trocas, Protect/potência/Pressure, duplas/interrupções e as oito verificações positivas de duração de Encore/Disable. Negativos próprios de v12/v13/v14 não são tratados como propriedades da saída v16. Isso não é execução da totalidade das suítes históricas.

Ambiente temporário foi reconstruído: mGBA **0.10.5**, Zig **0.17.0**, cadeia parcial→estojo v2→v5…v15 verificada em cada etapa. A base privada foi somente baixada do Drive, sem atualização ou upload. O checkout foi realinhado ao commit já publicado `9c86b54` após confirmar que os arquivos locais coincidiam integralmente; nenhum trabalho local divergente foi descartado.

## Hashes e reprodução

| Artefato | SHA-256 |
|---|---|
| Entrada v15, 33.554.432 bytes | `a6b454f7cbafad8c05e1b8aa2028087a596bbeff4f0184c826a92ebb7e554147` |
| Payload v16, 300 bytes | `f1946a84a7932215b83e6d01e4d6794e4b1dbab334fb49c2236b48ad185c0ceb` |
| Saída v16, 33.554.432 bytes | `644b140dc4fd1f4fab4c7ed9304fb266865d3e81825140c01c2c275564dc0fcc` |

Na raiz do repositório, com ROM própria e saída ainda inexistente:

```sh
python3 firered_gen1_9/scripts/motor_v16.py \
  --rom /privado/motor_v15.gba --saida /privado/motor_v16.gba
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V16_BASE=/privado/motor_v15.gba
export MOTOR_V16_ROM=/privado/motor_v16.gba
export MGBA_CORE=/privado/mgba_libretro.so
export TREINO_TEST_ROM="$MOTOR_V16_ROM"
python3 -m unittest test_motor_v16 test_treino_ev_mgba -v
python3 -m unittest test_motor_v16_mgba -v
python3 -m unittest test_motor_v16_regressions -v
```

Recompilação independente produziu payload byte a byte idêntico:

```sh
python3 -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi \
  -mthumb -Os -fno-builtin -nostdlib -Wall -Wextra -Werror \
  -Wl,--nmagic -Wl,-e,entry_forcerandomswitch_v16 \
  -Wl,-T,firered_gen1_9/patches/motor_v16/payload.ld \
  firered_gen1_9/patches/motor_v16/entry.s \
  firered_gen1_9/patches/motor_v16/motor_v16.c -o /tmp/v16-rebuilt.elf
python3 -m ziglang objcopy -O binary /tmp/v16-rebuilt.elf /tmp/v16-rebuilt.bin
cmp /tmp/v16-rebuilt.bin firered_gen1_9/patches/motor_v16/payload.bin
```

## Limitações e próximos controles

A matriz nova de correção por nível é singles. As regressões de duplas não são prova de phazing em todos os bancos, três ou mais reservas, exclusão dos dois membros já ativos, redirecionamento, múltiplos treinadores ou link. Esses cenários devem ser auditados separadamente, ainda que a escolha de reserva continue nativa.

Não se certificam todos os casos de Substitute, KO do alvo/atacante, hazards na entrada, Magic Bounce, Soundproof/Good as Gold, Eject Button/Emergency Exit, prioridades modernas ou pivôs adversários. Não houve validação integral de campanha, Teachy TV ou migração de saves pessoais. Não foi alterado o histórico de golpes falhados/impedidos nem completada a implementação moderna de Encore/Disable.

**ROMs, saves e estados continuam fora do Git. Drive não atualizado.** O pacote lá armazenado não passa automaticamente a ser v16.

## Referências fixadas

- [pret/pokefirered, `battle_script_commands.c`, ce6406d](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c): `TryDoForceSwitchOut`, chance por nível e `Cmd_forcerandomswitch`, validação/seleção de reserva.
- [Pokémon Showdown, `battle-actions.ts`, 035c1a1](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/battle-actions.ts): `forceSwitch`/`dragIn`, alvo vivo, reserva elegível e eventos de bloqueio, sem esse sorteio de nível no contexto de treinador.
- [Auditoria v15, diagnóstico e referências de histórico](AUDITORIA_V15_PIVOS_PHAZING.md).
