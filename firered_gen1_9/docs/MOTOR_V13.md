# Motor v13 — Eerie Spell, Substitute e Shield Dust

**02/11/2026 — duas correções concluídas; projeto ainda parcial.** Esta etapa parte do v12 exato e grava um novo arquivo. Foram usados apenas estados/saves sintéticos em mGBA 0.10.5. ROMs e saves continuam fora do Git.

> **Adendo da auditoria KO/EXP (02/11/2026):** a espera descrita neste relatório foi atribuída ao cenário sintético: Pokémon nível 10 com EXP total 1. Corrigindo somente EXP/checksum para 560, v12 e v13 encerram a batalha. As fábricas foram corrigidas; o teste KO agora verifica EXP, vitória e retorno ao mapa. **ROM v13 inalterada**, 54 verificações passaram na nova etapa. Veja [AUDITORIA_EXP_FIXTURES.md](AUDITORIA_EXP_FIXTURES.md). A seção KO/EXP abaixo conserva o registro histórico anterior à identificação da causa.

## Correções confirmadas

1. **Eerie Spell (720) atravessa Substitute:** o alvo recebe dano e perde até três PPs do último golpe usado; o boneco mantém seu HP e seu bit de status.
2. **Shield Dust (habilidade 19) impede somente o dreno de PP:** o dano continua atingindo o alvo, inclusive através de Substitute. O bit de supressão de habilidade já usado nos motores v9/v10 desativa esse bloqueio.
3. **Soundproof do v12 continua funcionando:** impede dano e dreno, inclusive com Substitute.

Nenhum novo golpe, aprendizado, item ou habilidade foi habilitado. Continuam **15.008 registros de aprendizado e 708/729 omissões restauradas**, com Simple Beam, Ally Switch, Instruct e Revival Blessing adiados (21 registros). Não há reserva nova de RAM ou alteração do formato do save.

### Reprodução comparativa

Alvo adormecido com 480 HP, golpes `(33,150,45,39)`, PPs `(10,10,10,10)` e último golpe Growl (45, slot 2). Fixtures são criadas separadamente em v12 e v13, nunca transferidas entre ROMs.

| Cenário | v12 — defeito reproduzido | v13 — resultado ao fim do turno |
|---|---|---|
| Substitute de 200 HP, habilidade neutra | boneco perde HP, alvo mantém 480 HP e todos os PPs | boneco mantém 200 HP, alvo perde HP e Growl cai a 7 PP |
| Substitute de 1 HP, habilidade neutra | boneco quebra, alvo mantém 480 HP e todos os PPs | boneco mantém 1 HP, alvo perde HP e Growl cai a 7 PP |
| Shield Dust, sem Substitute | dano e dreno indevido de três PPs | dano sem dreno |
| Shield Dust + Substitute de 1 ou 200 HP | não é uma correção do v12 | dano no alvo, sem dreno e sem consumir o boneco |

O teste de **Substitute criado naturalmente** deixa o alvo mais rápido usar o golpe 164 no mesmo turno, sem injetar `status2`, HP do boneco ou histórico. Dos 480 HP, ele paga 120; Eerie Spell o atinge depois, preserva o boneco de 120 HP e reduz o PP de Substitute além do gasto próprio.

Também foram confirmados:

- **Endure + Substitute:** um alvo de 1 HP sobrevive a Eerie Spell com 1 HP, preservando o boneco. O PP total cai de 160 para 156 (uso de Endure + dreno).
- **Sem vazamento do bypass:** Tackle continua acertando o boneco no turno seguinte e o Tackle do adversário também acerta o boneco do jogador no mesmo turno. O bit temporário de bypass está limpo ao final.
- **Protect e imunidade Dark:** não há dano/dreno nem perda de HP do boneco.
- **Duplas, bancos 1 e 3:** seleção pela interface, dano/dreno só no alvo; outro oponente e aliados preservados. Shield Dust no banco 3 impede o dreno, Soundproof impede dano/dreno. PPs da equipe criptografada e checksums são verificados, inclusive no segundo slot inimigo.
- Regressões de PP v11: último golpe, ausência de fallback, limites 0/1/2/3 PP, Transform/Mimic, histórico natural e sincronização com a equipe.

## Implementação e endereços

O v13 não reimplementa a redução de PP: encadeia o helper v11, que continua intacto. Novos wrappers Thumb são restritos ao ID 720. Para os três comandos de cálculo/HP, exige-se também o endereço exato da instrução no script padrão; demais movimentos e usos dos comandos seguem a cadeia anterior.

| Wrapper | Entrada Thumb | Comportamento |
|---|---|---|
| Ajuste de dano, comando `0x07` | `0x090D7101` | Em `0x090CD40D`, oculta o bit Substitute apenas durante a chamada síncrona a `0x08058FED`. O nativo testa `status2`, não o marcador de bypass; isso preserva o caminho de Endure/Focus Band. Endure foi testado; a ativação aleatória de Focus Band não foi testada dedicadamente. |
| Barra de HP, comando `0x0B` | `0x090D7109` | Em `0x090CD414`, acrescenta temporariamente `HITMARKER_IGNORE_SUBSTITUTE` ao chamar o wrapper anterior `0x090C0029`. |
| HP real, comando `0x0C` | `0x090D7111` | Em `0x090CD416`, faz o mesmo ao chamar `0x090D0041`, preservando a cadeia de dano/berries v10. |
| Pós-impacto | `0x090D7119` | Se Shield Dust estiver ativo, vai a moveend. Caso contrário, oculta apenas o bit Substitute durante a chamada síncrona ao helper v11 `0x090D6101` e o restaura antes de o controller processar a sincronização de PP. |

O bit de bypass adicionado pelos wrappers `0x0B/0x0C` é removido **antes de retornar**, mesmo se o comando estiver esperando o controller e não avançar a instrução. Não é mantido entre frames/comandos; não se restaura o marcador inteiro, pois o nativo pode alterar outros bits. Um bit já presente segue a semântica anterior.

Referências RAM nesta base:

- `gBattleMons`: `0x02021410`, stride `0x5C`; habilidade `+0x20`, HP `+0x2A`, status2 `+0x54`.
- Substitute: bit `0x01000000` de status2; HP do boneco em `0x02021648 + 28*b + 0x0A`.
- `gHitMarker`: `0x0202160C`, bypass `0x100`.
- `gStatuses3`: `0x02021638`, supressão de habilidade `0x00010000` por banco.
- `gBattlescriptCurrInstr`: `0x020215B0`.

### Escopo exato das escritas

| Offset de arquivo | Escrita |
|---|---|
| `0x10CFC1C..0x10CFC1F` | ponteiro do comando `0x07` |
| `0x10CFC2C..0x10CFC2F` | ponteiro do comando `0x0B` |
| `0x10CFC30..0x10CFC33` | ponteiro do comando `0x0C` |
| `0x10CD428..0x10CD42C` | callasm pós-impacto |
| `0x10D7100..0x10D72C5` | payload de **454 bytes** |

São cinco escritas, **471 bytes ao todo**, nem todos diferentes da base. O aplicador verifica SHA-256 completo, payload, espaço livre, ponteiros e instruções anteriores. O teste restaura essas escritas e exige igualdade integral com v12. Soundproof v12, helper PP v11, tabelas de golpes/aprendizados, estojo, TMs/HMs, encontros, eventos e treino não foram alterados.

## Testes executados — 42 verificações, nenhuma pulada

- **5 estruturais:** payload/vetores Thumb, entrada inválida, saídas existentes incluindo links, hash/preservação integral, corrupção/reaplicação.
- **21 verificações na classe singles:** 20 verificam resultados ao fim do turno (incluindo reprodução v12 e regressões); **uma é observação intermediária de KO e caracterização da limitação de EXP descrita abaixo**.
- **1 teste dedicado de duplas**, com quatro subcasos: alvo banco 1; banco 3; banco 3 com Shield Dust; banco 3 com Soundproof.
- **6 regressões herdadas de batalha/estojo/save**, executadas sobre v13 com fixtures próprias.
- **9 regressões de treino EV/IV** sobre v13.

`test_motor_v13*.py`: **33/33**, 360,418 s. EV/IV: **9/9**, 24,670 s. Payload recompilado e comparado byte a byte. Não houve execução integral de todas as suítes históricas do repositório nesta etapa.

### Ressalva importante: KO/experiência ainda não encerra nesta fixture

O teste originalmente planejado para confirmar vitória após KO **não passou nesse critério**. Na investigação:

- v12, alvo de 1 HP **sem Substitute**, e v13, alvo de 1 HP **atrás de Substitute**, chegam a HP 0 sem drenar os PPs observados.
- Após confirmação da mensagem de desmaio, ambos permanecem em `A ganhou 21 pontos de EXP.!`, com cursor `0x08187142` (comando `0x23`, getexp), `gBattleOutcome = 0` e controller ativo no diagnóstico.
- A sequência de doze confirmações B usada no teste não encerra a batalha. Tentativas adicionais exploratórias com B e A também não resolveram a espera.

**Fato:** o bloqueio é reproduzível também no controle v12, sem os wrappers novos e sem Substitute. **Causa ainda indeterminada:** pode decorrer da construção do cenário sintético ou de uma falha do motor herdado. Não há evidência suficiente para classificá-lo como defeito geral de campanha ou descartá-lo como mero problema do teste.

O teste final chama-se `test_observacao_ko_sem_dreno_e_limite_de_experiencia_da_fixture`: confirma a observação intermediária e a igualdade da fase de espera com o controle. **Não prova vitória, término do turno após KO, retorno ao mapa ou ausência de dreno em todas as etapas posteriores.** Ele está incluído nas 42 verificações com essa ressalva explícita; não foi escondido como correção concluída.

## Hashes e reprodução

| Artefato | SHA-256 |
|---|---|
| Entrada `motor_v12.gba` | `fb28ad767a11add187d0fa69dec0164b3de73a9887a0c5834c5feccc675725c1` |
| Saída `motor_v13.gba`, 33.554.432 bytes | `71756c820ebb71c0c64735b0e8f36cf420da29ac419f8ee09a39109d9cb4951c` |
| Payload, 454 bytes | `158d2d621bfb6d977a9014c411ac2eaff8fe3701cafc4f834624cb1785c95355` |

```sh
# Saída inexistente; jamais sobrescrever a base ou saves pessoais.
python3 firered_gen1_9/scripts/motor_v13.py \
  --rom /caminho/motor_v12.gba --saida /caminho/nova_motor_v13.gba

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V13_BASE=/caminho/motor_v12.gba \
MOTOR_V13_ROM=/caminho/nova_motor_v13.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_motor_v13*.py' -v

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
TREINO_TEST_ROM=/caminho/nova_motor_v13.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_treino_ev_mgba.py' -v
```

Compilação reproduzida com Zig 0.17.0:

```sh
python3 -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi \
  -mthumb -Os -fno-builtin -nostdlib -Wall -Wextra -Werror \
  -Wl,--nmagic -Wl,-e,entry_adjust_v13 \
  -Wl,-T,firered_gen1_9/patches/motor_v13/payload.ld \
  firered_gen1_9/patches/motor_v13/entry.s \
  firered_gen1_9/patches/motor_v13/motor_v13.c -o /tmp/motor_v13.elf
python3 -m ziglang objcopy -O binary /tmp/motor_v13.elf /tmp/payload_v13.bin
sha256sum /tmp/payload_v13.bin
```

## Limites e próximos passos

1. **Prioridade de investigação:** reduzir o cenário KO/EXP ao mínimo e comparar com uma batalha sintética sem alterações de stats/HP, antes de alegar encerramento de batalha/campanha validado.
2. Histórico após troca e esgotamento de PP durante travas multi-turno continuam sem validação dedicada. Não houve patch em CancelMultiTurnMoves.
3. A supressão de Shield Dust foi testada com o bit de estado sintético existente; isso não equivale a validar todos os fluxos de Gastro Acid/Core Enforcer. Mold Breaker, Covert Cloak e habilidades/itens ausentes continuam fora de escopo.
4. Não há modernização geral dos golpes sonoros, da IA, link ou Teachy TV completa. Os quatro golpes/21 aprendizados adiados permanecem fora do catálogo.
5. Não houve comparação visual quadro a quadro das animações. Os testes cobrem HP, PP, status, mensagens e controllers; não são prova de fidelidade gráfica ou mecânica integral de Scarlet/Violet.

Referências de comportamento moderno e código nativo estão fixadas em [MOTOR_V12.md](MOTOR_V12.md#referências-técnicas-fixadas). O ajuste de Endure vem da inspeção de `Cmd_adjustnormaldamage` nessa mesma revisão de pret/pokefirered. A ordem do cursor de alvos em duplas foi conferida em [battle_controller_player.c, revisão ce6406d8](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_controller_player.c): LEFT seleciona o segundo inimigo a partir do primeiro; RIGHT iria para o aliado na fixture.

O pacote do Drive **não foi atualizado** nesta etapa. Registro no repositório e em VYK-57. Manter backups separados de saves normais; não transferir save states de v12 para v13. Não misturar esta base Gen 1–9 com a ROM histórica BAG_MOD.
