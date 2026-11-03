# Motor v14 — PP de Rollout/Ice Ball interrompidos por Protect/Detect

**03/11/2026 — correção dirigida sobre o v13 exato.** A saída é gravada em arquivo novo; apenas ROM identificada por SHA-256 e estados sintéticos. Nenhum save pessoal foi usado.

> **Adendo da auditoria ampliada (03/11/2026):** sem mudar o payload ou a ROM, foram acrescentados testes de usuários nos quatro bancos em duplas e de flinch/confusão/paralisia criados por golpes reais. A etapa concluiu 21 verificações, incluindo sete testes novos; veja [AUDITORIA_V14_DUPLAS_INTERRUPCOES.md](AUDITORIA_V14_DUPLAS_INTERRUPCOES.md). O escopo e os números abaixo conservam o registro da entrega original do v14; algumas lacunas de interrupções/duplas foram reduzidas pela auditoria posterior, não eliminadas integralmente.

## Defeito e resultado

O [desvio de PP auditado no v13](AUDITORIA_ROLLOUT_POTENCIA.md) ocorre porque o ramo de Protect limpa a trava antes de o script verificar se deve dispensar o desconto de PP. O v14 conserva o cancelamento da sequência, mas impede o desconto adicional de uma ação que já era continuação.

| Fase, inicialmente 4 PP | v13 | v14 |
|---|---:|---:|
| Primeiro impacto | 3 | 3 |
| Segundo impacto da mesma sequência | 3 | 3 |
| Continuação interrompida por Protect | **2 — defeito** | **3** |
| Novo uso após a interrupção | 1 | **2** |

A base v13 foi reexecutada em fixtures próprias para Rollout e Ice Ball, com/sem Defense Curl, e continua reproduzindo 2 PP no turno protegido. Na saída v14, os casos positivos exigem 3 PP. **Não se herdou a expectativa defeituosa como resultado desejado da saída.** Estados mGBA não são transferidos entre versões.

A potência permanece **30→60→120→240→480**, ou **60→120→240→480→960** após Defense Curl. O novo código não altera fórmula, timer ou tabela de potência. Protect/Detect continuam interrompendo a sequência, e o próximo uso reinicia em 30/60.

## Implementação restrita

Payload Thumb de **210 bytes**, sem RAM adicional, novos aprendizados ou alteração de save. Um wrapper do comando `attackcanceler` encadeia a rotina v10 existente, que por sua vez mantém a cadeia anterior.

Antes da chamada anterior, captura somente em variáveis locais:

- cursor exatamente no início do script Rollout, `0x08186348`;
- golpe **205 (Rollout)** ou **301 (Ice Ball)**;
- bancos válidos dentro da contagem da batalha;
- trava `STATUS2_MULTIPLETURNS` ativa no atacante.

Depois da chamada, exige simultaneamente:

- mesmo golpe, atacante e alvo;
- cursor avançado exatamente para `0x08186349`;
- alvo com o bit nativo de Protect/Detect;
- resultado marcado como falha e trava agora removida.

Só nesse caminho acrescenta **`HITMARKER_NO_PPDEDUCT = 0x800`**. O fluxo subsequente permanece nativo:

`attackstring → jumpifstatus2 (falso após cancelamento) → ppreduce`

O próprio `ppreduce` consome o marcador, inclusive quando PP já é zero. O wrapper **não** o arma em continuações normais, que saltam esse comando, nem em desvios para sono, nem no primeiro uso. Não é restaurado o marcador inteiro, preservando bits de outros mecanismos.

Esse recorte evita uma implementação ampla que marcasse toda continuação: nesse desenho incorreto, o bit poderia ficar pendente porque o script não passa por `ppreduce`.

### Endereços e escritas

| Endereço/offset | Papel |
|---|---|
| ROM `0x10CFC00..0x10CFC03` | comando `0x00`: ponteiro anterior `0x090D0019` → `0x090D8001` |
| ROM `0x10D8000..0x10D80D1` | payload de 210 bytes; entrada Thumb `0x090D8001` |
| `0x020215B0` | cursor de script |
| `0x02021586` | golpe corrente |
| `0x020215A8` / `0x020215A9` | atacante / alvo |
| `0x020213F4` | contagem de bancos |
| `0x02021410 + 0x5C*b + 0x54` | status2; trava `0x1000` |
| `0x020216CC + 16*b` | ProtectStruct, bit 0 de proteção |
| `0x02021608` | flags de resultado; bit 0 de falha |
| `0x0202160C` | marcador; isenção de PP `0x800` |

São **dois intervalos, 214 bytes escritos**, nem todos diferentes da base. O aplicador verifica SHA completo de entrada, payload, espaço livre até `0x10D9000`, ponteiro anterior, prefixo do script, efeito compartilhado 117 e potência base 30 dos dois golpes. O teste reconstrói a saída e restaura os dois intervalos, exigindo igualdade integral com v13.

Nenhum byte de catálogo, estojo, TMs/HMs, encontros, eventos, treino ou payloads anteriores é alterado. A mudança funcional nos outros golpes é evitada pelos filtros acima; as regressões verificam uma seleção desses fluxos, não todas as combinações possíveis.

## Cobertura dirigida

- **Protect e Detect:** Rollout/Ice Ball com e sem Defense Curl; o turno bloqueado não causa dano, conserva PP, limpa a trava e preserva o bônus de Defense Curl.
- **Primeiro uso protegido:** ainda gasta um PP. O próximo uso começa a potência 30 e gasta outro PP.
- **Pressure:** 4→2 no primeiro uso, permanece 2 nas continuações e no bloqueio, reinício gasta mais dois e chega a zero.
- **PP zerado por Eerie Spell:** progressão completa e Struggle depois do fim normal; se Protect interrompe antes, não há underflow e a próxima ação é Struggle.
- **Miss real:** Sand Attack reduz acurácia por ações normais; a falha durante a trava não gasta PP extra e um impacto posterior reinicia a potência.
- **Sono real:** Hypnosis age antes da continuação; o caminho de sono cancela a trava sem armar isenção pendente.
- **Atacante no banco 0:** jogador inicia Rollout/Ice Ball; adversário usa seu único Splash e depois Protect. A sequência automática para com 3 PP, e o Tackle escolhido a seguir gasta seu próprio PP, mesmo quando protegido.
- **Atacante no banco 1:** os demais cenários dirigidos usam o adversário como usuário da sequência. A cada turno também se confere o gasto próprio do outro banco e a ausência de `0x800` no menu.
- **Dados persistentes:** PP e checksum na equipe criptografada, PP de batalha e HP da equipe são conferidos. As fixtures de EXP continuam coerentes.

O teste do banco 0 espera o menu concluir sua transição antes da próxima escolha: texto de menu em RAM não prova, sozinho, que a entrada já é aceita. Não se força callback, registrador ou trava para avançar a batalha.

## Regressões e execução final

**61/61 verificações concluídas, nenhum teste pulado**, em mGBA 0.10.5:

| Execução final | Resultado | Tempo |
|---|---:|---:|
| `test_motor_v14` + `test_motor_v14_mgba` | **19/19** | 479,648 s |
| `test_motor_v14_regressions` | **33/33** | 340,461 s |
| Treino EV/IV sobre v14 | **9/9** | 23,565 s |

A contagem inclui uma reprodução negativa do defeito no v13, separada das asserções positivas na saída corrigida. Execuções exploratórias, subconjuntos e duas tentativas interrompidas pelo executor não foram somados; as duas suítes longas foram reexecutadas integralmente com término e código de saída zero.

Arquivos:

- `tests/test_motor_v14.py`: cinco verificações de build, hash, preservação integral, payload, entrada inválida/reaplicação e saída exclusiva, inclusive links.
- `tests/test_motor_v14_mgba.py`: 14 testes dirigidos, incluindo o contrafactual v13 e controles positivos v14.
- `tests/test_motor_v14_regressions.py`: 33 regressões com fixtures novas no v14 — 20 de Eerie/HP/PP/KO, sete de famílias/estojo/save/duplas e seis de histórico/trocas/travas.
- `tests/test_treino_ev_mgba.py`: nove regressões de treino, agora aceitando explicitamente o SHA v14 sem remover os hashes anteriores.

A regressão KO exige EXP e retorno ao mapa; não volta à antiga observação incompleta de EXP. A reprodução negativa v12 de Substitute/Shield Dust não é herdada como propriedade do v14. Não foi executada a totalidade das suítes históricas nem a auditoria EXP específica nesta etapa.

## Hashes, aplicação e reprodução

| Artefato | SHA-256 |
|---|---|
| Entrada v13, 33.554.432 bytes | `71756c820ebb71c0c64735b0e8f36cf420da29ac419f8ee09a39109d9cb4951c` |
| Saída v14, 33.554.432 bytes | `2302ba1c88194fec190d0da062f91380ba062ee06e5a4a626902767412a9682c` |
| Payload v14, 210 bytes | `c8dc9a83f1a57f8d1cf339d6908c8c38d51f1108517700ce5156a006b4d0fe11` |

```sh
python3 firered_gen1_9/scripts/motor_v14.py \
  --rom /caminho/motor_v13.gba --saida /caminho/nova_motor_v14.gba

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V14_BASE=/caminho/motor_v13.gba \
MOTOR_V14_ROM=/caminho/nova_motor_v14.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_motor_v14*.py' -v

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
TREINO_TEST_ROM=/caminho/nova_motor_v14.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_treino_ev_mgba.py' -v
```

Ambiente reconstruído nesta etapa: mGBA **0.10.5** (libretro), cadeia parcial→estojo_v2→v5…v13→v14, todos com os hashes exigidos pelos aplicadores. Para o CMake recente foi usado `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`. A base privada foi recuperada do Drive; não foi publicado um novo pacote lá.

Payload recompilado com **Zig 0.17.0**, comparado byte a byte:

```sh
python3 -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi \
  -mthumb -Os -fno-builtin -nostdlib -Wall -Wextra -Werror \
  -Wl,--nmagic -Wl,-e,entry_attackcanceler_v14 \
  -Wl,-T,firered_gen1_9/patches/motor_v14/payload.ld \
  firered_gen1_9/patches/motor_v14/entry.s \
  firered_gen1_9/patches/motor_v14/motor_v14.c -o /tmp/motor_v14.elf
python3 -m ziglang objcopy -O binary /tmp/motor_v14.elf /tmp/payload_v14.bin
cmp /tmp/payload_v14.bin firered_gen1_9/patches/motor_v14/payload.bin
```

ROMs, saves, estados e assets comerciais continuam fora do Git. Manter backups separados; não transferir save states entre v13/v14 e não misturar esta base com BAG_MOD.

## Referências e limites

Comportamento moderno e fórmula de potência: Showdown fixado em `035c1a1f3c2ed286cda4c0d8623800699cd2c1c0`, especialmente [runMove e desconto de PP](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/battle-actions.ts#L335-L349). Diagnóstico nativo: pret/pokefirered `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`, [Protect em attackcanceler](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c#L896-L907), [ppreduce](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c#L1122-L1168) e [script Rollout](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/data/battle_scripts_1.s#L1592-L1602). O marcador correto é `1 << 11`, não o bit usado para suprimir a mensagem de ataque.

- Correção dirigida a Rollout/Ice Ball; não moderniza o consumo de PP de todas as famílias multi-turno.
- Os novos casos de Protect/Detect são singles nos bancos 0/1. Duplas têm regressão de Eerie Spell nos bancos 1/3, **não** uma matriz completa de Rollout/Protect em todos os alvos de duplas.
- Ainda não se generaliza para Encore/Disable, todas as causas de abortar ação, flinch, paralisia, confusão, todas as habilidades/itens ou partidas link.
- Ice Ball é histórico no projeto Gen 1–9, não uma alegação de disponibilidade em SV. As referências de simulador não substituem teste em cartucho SV.
- Catálogo continua com **15.008 aprendizados, 708/729 omissões restauradas**, quatro golpes/21 registros adiados. Nenhum novo golpe foi habilitado.
- Próxima prioridade: ampliar controles de interrupções e duplas, depois retomar histórico de pivôs/trocas forçadas e Encore/Disable. Campanha, IA e Teachy TV continuam sem certificação integral.
