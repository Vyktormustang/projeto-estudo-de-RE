# Motor v15 — duração fixa de Disable e Encore

**03/11/2026 — correção restrita sobre v14 exato.** FireRed Gen 1–9 / VYK-57, não o hook BAG_MOD da outra ROM. Entrada identificada por SHA-256, saída em arquivo novo e testes somente com equipes/saves sintéticos. ROMs e saves não integram o Git.

> **Adendo da auditoria posterior (03/11/2026):** histórico/PP após pivôs e trocas forçadas foi testado sem alterar a ROM. Foram concluídas 25 verificações, incluindo uma caracterização de **outro defeito ainda aberto**: phazing por Dragon Tail/Circle Throw pode falhar por nível mesmo após causar dano em contexto de treinador. Veja [AUDITORIA_V15_PIVOS_PHAZING.md](AUDITORIA_V15_PIVOS_PHAZING.md). Os 76 testes e a correção de duração abaixo conservam o registro da entrega original; não certificam esse comportamento de phazing.

## Defeito confirmado e correção

A rotina nativa mantinha durações aleatórias da geração III: Disable sorteava 2–5 e Encore 3–6. A v15 fixa **Disable em quatro oportunidades de ação do alvo** e **Encore em três**, contando a ação do turno de aplicação se ainda estiver pendente. Quando o alvo já agiu, acrescenta-se uma unidade ao contador, pois o motor decrementa o timer no fim desse mesmo turno.

A base v14 foi executada separadamente, com fixtures construídas nela, antes dos testes positivos com fixtures novas na v15. Primeiro o alvo usa seu golpe normalmente; o outro participante aplica o efeito no segundo turno. Não se injetam histórico, timers ou trava para fabricar a aplicação.

| Efeito / golpe do alvo | Aplicação em relação à ação do alvo | v14: restante / inicial no fim do turno 2 | v15: restante / inicial |
|---|---|---:|---:|
| Disable / Tackle | antes | **4 / 5** | **3 / 4** |
| Disable / Tackle | depois | **1 / 2** | **4 / 5** |
| Encore / Rollout | antes | **5 / 6** | **2 / 3** |
| Encore / Rollout | depois | **4 / 5** | **3 / 4** |

Esses valores da v14 são as amostras determinísticas reproduzidas, não uma duração universal. A suíte exige os quatro resultados antigos somente na base; nunca herda essas expectativas para a saída corrigida. Os contadores modernos também foram acompanhados até a expiração para Tackle, Rollout e Ice Ball, nas duas ordens de ação.

## Implementação

Dois wrappers chamam **as rotinas nativas**, conservando suas verificações de sucesso/falha e a chamada original a `Random`. Somente após aplicação nova bem-sucedida são normalizados os dois nibbles (restante/inicial) do timer. Não foi removida a chamada ao RNG nem adicionada outra; isso preserva o consumo daquela rotina, **não promete trajetórias aleatórias idênticas por toda a batalha após mudar a duração**.

Guardas: golpe 50/227, alvo válido, ausência prévia do efeito, mesmo golpe/alvo depois da chamada, avanço do cursor exatamente em cinco bytes e efeito agora não nulo. Falhas e reaplicações não ganham timer novo.

A ordem é obtida da fila nativa, não de uma comparação de velocidades nem do `acted_turn_mask` v10: certos caminhos de impedimento não marcam esse bit. São inspecionadas apenas posições posteriores à ação corrente, buscando o alvo com ação de golpe (`0`). Sem ação pendente, soma-se um turno residual.

| Local | Uso |
|---|---|
| ROM `0x10CFE8C` | comando A3, `0x080620A9` → `0x090D9001` |
| ROM `0x10CFE90` | comando A4, `0x08062169` → `0x090D9009` |
| ROM `0x10D9000..0x10D912F` | payload Thumb de **304 bytes** |
| RAM `0x020213F4` | contagem de bancos |
| RAM `0x02021404` / `0x02021408` / `0x0202140C` | ações por ordem / bancos por ordem / posição atual |
| RAM `0x02021648 + 28*b` | DisableStruct do banco: efeito +4/+6, timer +11/+14 |

**Três escritas lógicas, dois intervalos físicos, 312 bytes escritos** (nem todos diferentes). Nenhuma RAM persistente nova, mudança no formato de save, catálogo, TMs/HMs, estojo, encontros ou payloads anteriores. A preservação byte a byte fora dos dois intervalos é exigida pelo teste estrutural.

O patcher rejeita base divergente, payload corrompido, reaplicação, espaço ocupado e ponteiros anteriores incorretos. Confere ainda o SHA completo da saída. A escrita exclusiva protege arquivos existentes, inclusive symlink/hardlink.

## Cobertura dirigida

Nove métodos em `tests/test_motor_v15_mgba.py`:

- Contrafactual v14 em quatro combinações, separado da validação v15.
- Disable/Tackle e Encore/Tackle, antes e depois da ação do alvo, até expirar.
- Disable/Rollout/Ice Ball: cancelamento natural, nenhum PP extra na continuação impedida, Struggle enquanto o único golpe fica indisponível e reinício a potência 30 gastando um PP.
- Encore/Rollout/Ice Ball: cada impacto da sequência **30→60→120→240→480**, um único PP gasto; expiração de Encore não encerra a trava própria. Reinício custa outro PP e retorna a 30. A espera é limitada pelo número esperado de impactos, sem laço infinito.
- Reaplicação falha sem renovar o timer; ausência de histórico falha sem criar efeito.
- Aplicação com PP zero falha, mas a continuação já iniciada de Rollout/Ice Ball ainda atinge com potência 60.
- Encore termina antecipadamente quando Tackle consome o último PP; próxima ação é Struggle.

São observados a cada frame o início do efeito, HP e potência nos impactos; no menu conferem-se duração, PP de batalha versus equipe criptografada/checksum, HP persistente, gasto próprio do outro participante e ausência de isenção de PP pendente. As velocidades sintéticas garantem as duas ordens. Os únicos golpes disponíveis do adversário são deliberadamente limitados para observar a duração sem depender da escolha da IA.

**Nota de fixture:** a primeira sonda reutilizava um observador que rejeitava qualquer marcador `0x800`; isso rejeitou Struggle legítimo durante Disable. Não era defeito da ROM. O observador dirigido exige que o marcador esteja limpo no retorno ao menu, sem proibir seu uso nativo por Struggle.

## Execução e regressões

- Testes dirigidos: **9/9, 334,280 s**, sem skips.
- Estrutura/build + treino EV/IV: **14/14, 16,932 s**, sem skips.
- Regressões positivas: **53/53, 1.085,219 s**, sem skips.

**Total final: 76/76 verificações, nenhum teste pulado.** Todos os processos finais terminaram com código zero em mGBA 0.10.5. A contagem inclui a caracterização negativa da base v14; não é uma alegação de 76 mecânicas modernas distintas. As 53 regressões se dividem em 20 Eerie/HP/PP/KO, sete famílias/estojo/save, seis histórico/trocas manuais, 13 Protect/potência/interrupções e sete duplas/interrupções naturais.

A execução preliminar de três métodos e as sondas não entram na contagem final. Uma primeira execução estrutural pulou dois casos por referência à variável de ambiente antiga; a referência foi corrigida e os 14 casos acima foram reexecutados sem skips.

`tests/test_motor_v15_regressions.py` reconstrói/verifica a saída v15 e cria fixtures novas nela para os positivos históricos: Eerie Spell/PP/HP/KO/EXP, famílias de golpes, estojo/save/duplas, histórico/trocas manuais, Protect/Detect/Pressure/Defense Curl, sono/miss e interrupções naturais. Os testes negativos próprios de v12/v13 são explicitamente excluídos dessa herança. Isso não equivale a rodar toda a suíte histórica.

## Hashes e reprodução

| Artefato | SHA-256 |
|---|---|
| Entrada v14, 33.554.432 bytes | `2302ba1c88194fec190d0da062f91380ba062ee06e5a4a626902767412a9682c` |
| Payload v15, 304 bytes | `fc5fe98249fe3e4b7e3d2ac044ee077542ab2ea67a7e0873518cb0eaae6b9d8e` |
| Saída v15, 33.554.432 bytes | `a6b454f7cbafad8c05e1b8aa2028087a596bbeff4f0184c826a92ebb7e554147` |

Recompilação independente com Zig 0.17.0 produziu payload byte a byte idêntico. Na raiz do repositório, usando ROM própria e caminhos de saída ainda inexistentes:

```sh
python3 firered_gen1_9/scripts/motor_v15.py \
  --rom /privado/motor_v14.gba --saida /privado/motor_v15.gba

export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V15_BASE=/privado/motor_v14.gba
export MOTOR_V15_ROM=/privado/motor_v15.gba
export MGBA_CORE=/privado/mgba_libretro.so  # mGBA 0.10.5
export TREINO_TEST_ROM="$MOTOR_V15_ROM"
python3 -m unittest test_motor_v15 test_treino_ev_mgba -v
python3 -m unittest test_motor_v15_mgba -v
python3 -m unittest test_motor_v15_regressions -v
```

Recompilação (com o pacote `ziglang` 0.17.0 instalado):

```sh
python3 -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi \
  -mthumb -Os -fno-builtin -nostdlib -Wall -Wextra -Werror \
  -Wl,--nmagic -Wl,-e,entry_disable_v15 \
  -Wl,-T,firered_gen1_9/patches/motor_v15/payload.ld \
  firered_gen1_9/patches/motor_v15/entry.s \
  firered_gen1_9/patches/motor_v15/motor_v15.c -o /tmp/v15-rebuilt.elf
python3 -m ziglang objcopy -O binary /tmp/v15-rebuilt.elf /tmp/v15-rebuilt.bin
cmp /tmp/v15-rebuilt.bin firered_gen1_9/patches/motor_v15/payload.bin
```

## Referências fixadas e limites

- [Pokémon Showdown, moves.ts, commit 035c1a1](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts): duração de Disable/Encore, ajuste pela ação pendente e expiração de Encore por PP zero.
- [pret/pokefirered, battle_script_commands.c, commit ce6406d](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c): aplicação nativa, sorteio e cursor.
- [pret/pokefirered, battle_util.c, mesmo commit](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_util.c): decremento residual, expiração e cancelamento por Disable.

**Engine continua parcial.** A correção é de duração, não uma reimplementação completa de Encore/Disable modernos. Permanecem as exclusões e condições de aplicação nativas; não se moderniza aqui o significado de `gLastMoves` em ações falhadas/impedidas, nem se afirma cobertura de todas as interações com habilidades ou golpes chamados indiretamente.

A nova matriz de duração usa singles e alvo no banco 1. Regressões de duplas anteriores não constituem teste de todas as posições de aplicação de Encore/Disable, redirecionamento, alterações da fila, alvos já impedidos ou efeitos simultâneos. Essas combinações ficam abertas.

**Na entrega original, a próxima auditoria era:** histórico de pivôs (`U-turn`, `Volt Switch`, `Flip Turn`, `Parting Shot`) e trocas forçadas. Essa auditoria foi posteriormente realizada no recorte descrito no adendo acima; a correção da chance legada de phazing por nível permanece pendente. Campanha integral, link, Teachy TV completa e migração de saves pessoais tampouco foram certificados. Catálogo permanece em 15.008 registros, 708/729 omissões restauradas, sem novas inclusões.

**Drive não atualizado nesta etapa.** O pacote/ROM anteriormente armazenado lá não passa automaticamente a ser v15.
