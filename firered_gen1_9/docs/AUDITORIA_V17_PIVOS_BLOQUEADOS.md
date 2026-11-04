# Auditoria v17 — pivôs bloqueados e reservas inelegíveis

**04/11/2026 — FireRed Gen 1–9 / VYK-57.** Não é o BAG_MOD histórico.

## Resultado e estado

**Duas divergências de mecânica confirmadas em seis reproduções finais:** Volt Switch troca contra um alvo Ground apesar de reconhecer a imunidade; Parting Shot ignora Soundproof, reduz os atributos e troca. A segunda já estava declarada como limitação no cabeçalho das fontes v7 e foi agora reproduzida na v17.

**23 métodos distintos concluídos, sem skips: 21 controles positivos e duas caracterizações negativas.** A matriz nova contém 36 cenários, sendo 30 positivos e seis negativos. Os métodos `test_defeito_*` caracterizam o comportamento incorreto da base: um `ok` nesses métodos **não significa conformidade moderna**. ROM/payload/aplicador permanecem inalterados, sem v18 nesta auditoria. A correção é trabalho pendente, não uma entrega implícita deste relatório.

## Matriz nova

Módulo `tests/test_motor_v17_blocked_pivots_mgba.py`: **oito métodos / 36 cenários**, divididos em **30 controles positivos** e **seis reproduções negativas**.

| Grupo | Métodos | Casos | Expectativa |
|---|---:|---:|---|
| Protect × quatro pivôs × dois bancos | 1 | 8 | Não trocar, não causar dano/queda de atributos |
| Volt Absorb / Water Absorb × dois bancos | 1 | 4 | Não trocar nem causar dano, alvo inicialmente com HP cheio |
| Clear Body / ambos os atributos no mínimo × dois bancos | 1 | 4 | Parting Shot não reduz atributos nem troca |
| Quatro pivôs sem reserva elegível × dois bancos | 1 | 8 | Não trocar; dano ou reduções válidos ainda ocorrem |
| Ground sem reserva elegível × dois bancos | 1 | 2 | Volt Switch não causa dano nem abre a seleção |
| Um único atributo no mínimo × dois bancos | 1 | 4 | Parting Shot reduz o outro atributo e troca normalmente |
| **NEGATIVO: Volt Switch contra Ground** | **1** | **3** | V17 abre seleção e aplica hazards; deveria impedir a troca |
| **NEGATIVO: Parting Shot contra Soundproof** | **1** | **3** | V17 reduz atributos, abre seleção e aplica hazards; deveria bloquear o golpe |

Nos casos com dois hazards, banco 0 usa Speed 600 e ordem SR → Spikes; banco 2 usa Speed 40 e ordem Spikes → SR. Aliado: Speed 200; adversários: 100. **Banco, velocidade e ordem estão acoplados**, não formam uma cobertura cartesiana completa.

Cada negativo inclui os dois bancos com Spikes/SR e um controle adicional de quatro hazards: Ground no banco 0, Soundproof no banco 2. A referência moderna é fixada no commit Showdown `035c1a1f3c2ed286cda4c0d8623800699cd2c1c0`; os IDs locais diferem dos oficiais (Volt Switch local 517/oficial 521; Parting Shot local 571/oficial 575).

## Preparação e isolamento

- ROM v17 exata em mGBA 0.10.5/libretro, SHA conferido antes/depois; saves/estados exclusivamente sintéticos.
- Hazards colocados por golpes reais e enviados ao jogador por Court Change. Uma camada de Spikes e, quando usado, uma camada de Toxic Spikes. Não há escrita de RAM entre ações.
- A fixture inicial configura PP, tipos/habilidades ativos, estágios, velocidades e reservas. O tipo Ground é sintético no BattleMon do alvo; não é certificação de espécie/learnset/equipe legal.
- Adversários usam Splash. Só nos controles de Protect, uma configuração inicial de Disable impede Protect durante os três turnos de preparo; Splash tem exatamente três PP. Após Court Change, exige-se Disable expirado e Splash sem PP. O primeiro Protect real é então a única ação elegível do alvo. **Isso não certifica a duração moderna de Disable ou a IA competitiva.**
- Nos casos sem reservas elegíveis, os slots 2 e 3 estão desmaiados; o slot 4 é um ovo vivo e o 5 vazio. O outro banco do jogador permanece ativo e saudável, mas não pode ser escolhido como reserva.
- Jogadores ativos: HP/maxHP 4.000. Reserva escolhido: Fire, maxHP/HP 400. Sem itens, sem KO dos adversários, sem ganho de EXP.

## Divergência A — Volt Switch contra Ground

### Esperado

A imunidade de tipo impede dano e a troca. O ator permanece com sua identidade, HP, estágios e histórico do golpe tentado; não há aplicação de hazards. O aliado continua sua ação normalmente.

### Observado na v17

1. Exibe a mensagem de que o golpe **não afeta** o alvo e não reduz seu HP.
2. Na tela de seleção indevida, o bit `0x08` de `gMoveResultFlags` (`0x02021608`) continua marcado: a imunidade foi reconhecida.
3. Mesmo assim, abre a tela de equipe. O ator ainda possui histórico 517 antes da seleção.
4. Escolher o reserva 2 pela UI troca o banco e aplica os hazards:
   - Banco 0: **400 → 300 → 250** (SR, Spikes).
   - Banco 2: **400 → 350 → 250** (Spikes, SR).
   - Quatro hazards, banco 0: SR → TSpikes → Web → Spikes; **400 → 300 → 250 → 200**, sendo o último dano o residual de poison. Status 8 e Speed no estágio 5.
5. O entrante termina com histórico 0 e Attack neutro; no turno seguinte usa seu próprio Splash. Isso é coerente com a troca que ocorreu, mas **a troca em si não deveria ocorrer**.

O controle Ground **sem reserva** não abre a tela: a inelegibilidade impede a seleção, mas não corrige a ausência de veto por imunidade quando existem reservas. Volt Absorb bloqueia o golpe por outro caminho; seu sucesso não prova imunidade de tipo correta.

### Localização no código

`bs_pivot_hit`, em `scripts/motor_v7.py`, copia o trecho nativo de dano e concatena `_emit_pivot_switch_tail`. Este executa os estados iniciais de moveend, chama `ENTRY_PIVOT_CHECK` (`0x090C0061`) e consulta a disponibilidade de reservas antes de abrir a equipe.

`hook_pivot_check`, em `patches/motor_v7/motor_v7.c`, verifica HP do ator, resultado da batalha, contexto selvagem e adversários vivos, **mas não verifica os flags de falha/imunidade do golpe**. A combinação dessa ausência com o bit 0x08 observado é evidência direta do caminho inadequado. Não houve alteração nem recompilação do payload para esta auditoria.

## Divergência B — Parting Shot contra Soundproof

### Esperado

Parting Shot é sonoro. Soundproof deve bloquear o golpe antes das quedas: Attack/Sp. Atk permanecem 6, nenhum dano, nenhuma troca ou hazard. Isso é diferente de Clear Body e de ambos os atributos já estarem no mínimo.

### Observado na v17

- Soundproof (ability 43) permanece no alvo, mas Attack e Sp. Atk passam **6 → 5**.
- O menu de equipe abre, permitindo a troca e aplicando Spikes/SR nas mesmas ordens e danos do negativo anterior.
- Com quatro hazards no banco 2: TSpikes → Spikes → Web → SR; o reserva recebe poison, Speed −1 e **400 → 350 → 250 → 200**, incluindo o residual separado.
- O aliado continua e não perde HP/atributos/histórico; esse controle de continuidade **não torna correto o bloqueio ausente**.

### Lacuna já documentada e evidência estática

O cabeçalho de `patches/motor_v7/motor_v7.c` já declara Parting Shot entre os golpes sonoros novos sem interação com Soundproof. Não se atribui essa lacuna ao novo scheduler de hazards v17 nem se afirma regressão introduzida nele.

Na ROM v17 exata, a sequência nativa de golpes de Soundproof aparece uma única vez, no offset **`0x20F4E8`** (endereço GBA `0x0820F4E8`): IDs **45, 46, 47, 48, 103, 173, 253, 319, 320, 304, 65535**. O terminador 65535 encerra a lista; Parting Shot local 571 não consta. O fonte nativo fixa essa mesma lista em `sSoundMovesTable` e a consulta em `ABILITYEFFECT_MOVES_BLOCK`.

`is_sound_move_v10` inclui 571, mas seu uso no cancelamento v10 é para **Throat Chop**. A existência desse catálogo não comprova que Soundproof o utilize. O comportamento observado confirma que a imunidade sonora continua ausente neste caso.

## Controles positivos e invariantes

- Protect impede os quatro pivôs. Volt Absorb/Water Absorb anulam os respectivos golpes. Os testes exigem as mensagens correspondentes, além de ausência de dano e de seleção.
- Clear Body bloqueia ambas as quedas de Parting Shot; dois estágios no mínimo também impedem a troca. **Só um estágio no mínimo não deve impedir:** o outro cai e a troca válida ocorre, com hazards.
- Sem reserva, os três pivôs de dano ainda atingem o alvo sem trocar; Parting Shot ainda reduz ambos os atributos. Não se trata de falha completa do efeito primário.
- Nos casos sem troca, ator e aliado são acompanhados por frame: índice/identidade, atributos, tipos/habilidade, HP/maxHP, EXP, status e estágios. O histórico do ator progride do Splash anterior para o pivô tentado, sem zerar; o do aliado progride de Court Change para seu próprio Splash, sem voltar ou zerar.
- PP exatamente uma vez por ação, sem gasto nos reservas; níveis, EXP, identidades, checksums e cópias de HP/PP entre BattleMon e equipe preservados. Campo/fila permanecem iguais; nenhuma mudança de banco ou hazard indevido nos controles que devem permanecer.
- Nos negativos, a guarda do ator é mantida até a tela de equipe e retirada apenas ao autorizar a troca indevida pela UI. O aliado permanece observado durante todo o fluxo.
- Mais um turno completo: o ocupante atual usa Splash, com gasto de seu próprio PP e histórico 150. Nenhum hazard reaplicado; nos dois negativos com poison, somente o residual de 50 HP é permitido.

## Execuções finais

| Processo final | Métodos | Casos novos | Tempo | Interpretação |
|---|---:|---:|---:|---|
| Negativos + mínimo parcial + Ground sem reserva | **4** | **12** | **827,970 s** | Dois negativos reproduzidos + dois positivos, sem skips |
| Protect, absorção, Clear Body e mínimos totais | **3** | **16** | **875,114 s** | Controles positivos, sem skips |
| Reservas inelegíveis + regressões | **16** | **8** | **968,819 s** | Controles positivos, sem skips |

**Total: 4 + 3 + 16 = 23 métodos distintos.** São oito métodos novos e 15 regressões: um método anterior de sucesso dos quatro pivôs (oito subcasos), cinco de build/integridade e nove de EV/IV. Esses subcasos de regressão não entram nos 36 novos. Os métodos foram chamados por nome sem sobreposição; a descoberta confirma exatamente oito no módulo novo, dois deles `test_defeito_*`.

**O retorno OK dos dois métodos negativos significa que o defeito foi reproduzido, não que a v17 passou na regra moderna.** Não há xfail/skip escondendo o diagnóstico. As sondas exploratórias e a validação intermediária do observador foram excluídas dos totais. Os resultados históricos 22/23/46 das etapas anteriores não foram somados. Os processos rodaram em paralelo; os tempos não são comparação de desempenho da engine. Não foi reexecutada toda a suíte histórica.

Manifesto atualizado e verificado: **257 entradas**, sem incluir o próprio manifesto. SHA-256 final dos artefatos inalterados:

| Artefato | SHA-256 |
|---|---|
| ROM v17, 33.554.432 bytes | `5db05cbb54add61a6c50e08d3e392ba610e87ca3ef462095de168de5d3e32957` |
| Payload v17, 3.148 bytes | `f25e560c02cd3681a508812050e9fd0bed9d4b652d788dffa221d2a10983703f` |
| Base v16 usada nos testes de build | `644b140dc4fd1f4fab4c7ed9304fb266865d3e81825140c01c2c275564dc0fcc` |

## Reprodução

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V17_BASE=/privado/motor_v16.gba
export MOTOR_V17_ROM=/privado/motor_v17.gba
export MGBA_CORE=/privado/mgba_libretro.so
export TREINO_TEST_ROM="$MOTOR_V17_ROM"
# Inclui dois métodos negativos explícitos; OK não significa mecânica correta.
python3 -m unittest test_motor_v17_blocked_pivots_mgba -v
python3 -m unittest \
  test_motor_v17_switch_pivot_hazards_mgba.MotorV17SwitchPivotHazardsTests.test_quatro_pivos_sobrevivem_preservando_aliado \
  test_motor_v17 test_treino_ev_mgba -v
```

## Correção recomendada e limites

**Próxima etapa: correção dirigida dos dois caminhos, em nova versão com base v17 exata.**

1. Vetar a troca dos pivôs de dano quando o golpe falhou/não afetou o alvo, preservando o encerramento nativo, PP e histórico do golpe tentado. Não confundir “sem reserva” com “sem efeito primário”.
2. Fazer Soundproof bloquear Parting Shot antes das quedas, usando encerramento/mensagem/PP coerentes com o bloqueio nativo. Não ampliar silenciosamente a promessa a todos os sons e todas as habilidades modernas.
3. Converter as reproduções atuais em testes de regressão positiva da saída nova, mantendo a caracterização negativa **somente na base v17**. Rerodar os controles de Protect, absorção, Clear Body, mínimos parciais, falta de reserva, pivôs bem-sucedidos, hazards/KO e histórico/PP.

Não se deve simplesmente vetar Parting Shot quando uma das quedas falha: os quatro controles de mínimo parcial exigem a troca se a outra redução teve efeito.

Não foram certificados misses aleatórios, Substitute, habilidades modernas completas, Mold Breaker/Mirror Armor, Soundproof em todos os golpes, pivôs do adversário, todas as velocidades/ordens/alvos, KO durante o pivô, derrota, campanha, link/multi, Teachy TV ou migração de saves. O alvo é sempre o primeiro adversário; as habilidades/tipos/atributos são configurações sintéticas iniciais.

Nenhum save pessoal utilizado. ROMs, saves, estados, capturas e fontes externas baixadas para consulta fora do Git. Drive não atualizado. A engine continua parcial.

## Referências fixadas

- [Auditoria anterior: trocas e pivôs com aliado ativo](AUDITORIA_V17_TROCAS_PIVOS_HAZARDS.md), [motor v17](MOTOR_V17.md).
- [Showdown: Volt Switch](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L20428-L20442), [Parting Shot](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L13162-L13184).
- [Showdown: imunidade de tipo](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/battle-actions.ts#L716-L727), [troca após efeito válido e reserva disponível](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/battle-actions.ts#L1345-L1370).
- [Showdown: Soundproof](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/abilities.ts#L4437-L4452).
- [pret/pokefirered: lista sonora](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_util.c#L29-L35), [consulta de Soundproof](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_util.c#L1874-L1889), [encerramento nativo do bloqueio](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/data/battle_scripts_1.s#L4121-L4127).
