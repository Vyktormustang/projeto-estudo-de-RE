# Motor v18 — veto de pivô sem efeito e Parting Shot/Soundproof

**04/11/2026 — FireRed Gen 1–9 / VYK-57.** Correção dirigida sobre a **v17 exata**, não o BAG_MOD histórico. Nenhum save pessoal utilizado. A engine continua parcial.

## Estado da entrega

**Correção concluída e validada: 41 métodos distintos, sem skips — 39 controles positivos/build e dois negativos exclusivamente na base v17.** A saída v18 impede a troca de Volt Switch contra Ground e bloqueia Parting Shot por Soundproof antes das quedas. Os testes negativos não representam defeitos aceitos na v18. A semântica nativa de histórico do Soundproof permanece explícita abaixo; não é uma modernização integral desse histórico.

## Defeitos da entrada e comportamento da saída

A [auditoria da v17](AUDITORIA_V17_PIVOS_BLOQUEADOS.md) demonstrou dois caminhos incorretos:

| Caso | Base v17 | Saída v18 exigida |
|---|---|---|
| Volt Switch contra Ground | Mensagem de imunidade e dano zero, mas abre a equipe e troca | Mantém o ocupante, sem tela de equipe ou hazards |
| Parting Shot contra Soundproof | Attack/Sp. Atk 6→5 e troca | Bloqueio nativo antes das quedas; estágios permanecem 6, sem troca/hazards |

Os negativos da v17 foram mantidos **somente na base**, em `test_motor_v18_base_mgba.py`, com fixtures próprias dessa ROM. Os testes positivos geram novas fixtures na saída v18. Nenhum estado é transferido entre versões.

## Implementação mínima

Arquivos: `scripts/motor_v18.py` e `patches/motor_v18/{motor_v18.c,entry.s,payload.ld,payload.bin}`.

- **Payload de 94 bytes**, Thumb/ARM7TDMI, em `0x090DC000..0x090DC05D`.
- Tabela sonora de **26 bytes**, em `0x090DC100..0x090DC119`.
- **Quatro intervalos de escrita**, 128 bytes no total das janelas; todos os demais bytes da ROM são preservados.
- **Nenhuma RAM adicional**, nenhum novo campo de save. Isso não certifica migração de saves ou save states.
- A reserva `0x10DC000..0x10DCFFF` precisa estar integralmente `FF` na entrada. O espaço entre payload/tabela e o restante da reserva permanecem intactos.

| Offset no arquivo | Antes | Depois |
|---|---|---|
| `0x10C0064` — literal do vetor de pivô v7 | `0x090C07B5` | `0x090DC001` |
| `0x6F840` — literal da busca Soundproof | `0x090D7002` | `0x090DC102` |
| `0x10DC000`, 94 bytes | `FF` | Novo wrapper Thumb |
| `0x10DC100`, 26 bytes | `FF` | Lista sonora estendida |

### Pivôs de dano: veto antes da seleção

O tail v7 já executou os estados 0..15 de moveend antes do helper de troca. O wrapper novo verifica **apenas U-turn 369, Volt Switch 517 e Flip Turn 708**, e apenas então os flags `0x29` (miss/falha/sem efeito). Havendo veto, redireciona para `0x081853FC`, o encerramento remanescente nativo, sem refazer PP/histórico/efeitos.

Nos demais casos chama diretamente a função original **`0x090C07B5`**, não o vetor regravado; não há recursão. Permanecem as verificações originais de HP, fim da batalha, contexto selvagem e adversários vivos, seguidas da elegibilidade nativa das reservas.

Parting Shot e Chilly Reception não passam por esse veto de pivô de dano. Não se deve impedir Parting Shot quando **só uma queda** falha por estágio mínimo: a outra redução válida deve continuar permitindo a troca. Os quatro controles de mínimos parciais verificam isso.

A reprodução de imunidade de tipo usa Volt Switch/Ground. Protect e absorção de Electric/Water são controles adicionais, mas não se afirma cobertura completa de todos os bits, imunidades, misses ou habilidades modernas só pela existência da máscara.

### Soundproof: preservar a lista ativa v12 e acrescentar 571

A lista ativa na base v17 **não é mais a tabela original em `0x0820F4E8`**. Desde a v12, o literal em offset `0x6F840` aponta para **`0x090D7002`**, isto é, tabela v12 + 2. Growl (45), o primeiro ID, é tratado separadamente pelo código compilado nativo.

A v18 conserva todos os IDs ativos e sua ordem, incluindo Eerie Spell 720, e acrescenta apenas Parting Shot 571:

```text
45, 46, 47, 48, 103, 173, 253, 319, 320, 304, 720, 571, FFFF
```

A busca nativa recebe o literal `0x090DC102` (nova tabela + 2). As tabelas antiga e v12 **não são alteradas**. O bloqueio usa o próprio caminho nativo de habilidade, mensagem, PP e moveend; não se cria um segundo tratamento de quedas/seleção e não se altera o catálogo sonoro usado por Throat Chop.

**Precisão documental sobre a auditoria anterior:** localizar a sequência original em `0x20F4E8` não demonstrava que ela ainda era a lista ativa. A conferência do literal e da etapa v12 nesta implementação corrige essa atribuição. O resultado negativo anterior permanece válido: nem a tabela original nem a ativa v12 continham 571.

## Histórico: preservar a semântica nativa, sem prometer lastMove moderno

A primeira sonda da correção bloqueou Parting Shot corretamente, mas o observador esperava histórico 571, como no golpe não bloqueado da v17. O encerramento **nativo** de Soundproof grava `FFFF` (`MOVE_UNAVAILABLE`), não 571: a habilidade cancela antes de `HITMARKER_OBEYS`, e `Cmd_moveend` usa esse flag para atualizar `gLastMoves`.

Isso foi conferido independentemente nas duas ROMs:

| Golpe contra Soundproof | Histórico v17 | Histórico v18 |
|---|---|---|
| Growl 45, Hyper Voice 304, Eerie Spell 720 | `FFFF` | `FFFF` |
| Parting Shot 571 | `571`, pois não era bloqueado | `FFFF`, bloqueio nativo |

A correção **não foi alterada para forçar um ID de histórico**. O oráculo passou a exigir a semântica nativa específica de Soundproof, fundamentada nesses controles e no código nativo, não a aceitar qualquer valor. As sondas exploratórias não entram nos totais finais.

Nos testes finais, o ator conserva índice, identidade, HP, atributos e estágios; seu histórico progride de Splash para **517** no Volt Switch imune ou **FFFF** no Parting Shot bloqueado, **nunca para zero como se fosse outro ocupante**. O aliado mantém sua progressão Court Change→Splash. A ação seguinte atualiza normalmente o histórico: Splash nas duplas e Tackle nos controles singles.

**Limite explícito:** isso preserva a regra legada de Soundproof; não certifica o `lastMove` moderno nem todas as interações posteriores com Eerie Spell, Spite, Encore ou Mimic. Modernizar esse histórico exigiria auditoria separada.

## Validação dirigida

### Correção e controles de pivô — 8 métodos / 36 cenários

Em `test_motor_v18_mgba.py`, seis cenários que reproduziam os defeitos passam a exigir ausência de troca e efeitos indevidos:

- Volt Switch/Ground: banco 0 rápido (SR→Spikes), banco 2 lento (Spikes→SR) e banco 0 com SR→TSpikes→Web→Spikes.
- Parting Shot/Soundproof: os dois bancos/ordens e banco 2 com TSpikes→Spikes→Web→SR.

Não há dano, status, redução de Speed ou gasto de PP nos reservas. O campo mantém suas condições/fila. O ator gasta exatamente um PP; aliado e adversários gastam seus próprios PP uma vez. Mais um turno completo não aplica hazards ou poison aos ocupantes que nunca saíram.

Os outros **30 cenários** conservam os controles da auditoria: Protect nos quatro pivôs; Volt Absorb/Water Absorb; Clear Body; mínimos totais/parciais; quatro pivôs sem reservas; Ground sem reserva. Banco, velocidade e ordem continuam acoplados, não cobrem todas as combinações.

### Regressões na saída exata

`test_motor_v18_regressions.py`:

- **Quatro métodos / 32 cenários** de trocas manuais, quatro pivôs bem-sucedidos, KO do entrante e segunda escolha no mesmo banco, absorção, Web e residual. HP/PP/histórico do aliado preservados.
- **Seis métodos de ciclo de vida:** limpeza no começo da batalha/guardas, Court Change, limpeza/recriação, Rapid/Mortal Spin, hazards indiretos, absorção e KO antes de Intimidate.
- **Seis métodos de Soundproof/histórico:** Eerie Spell ainda bloqueado; controles sem habilidade e não sonoros; Substitute forte/frágil protegido; Growl/Hyper Voice; ação seguinte e novo controle de histórico nativo para 45/304/720/571. Nenhum negativo antigo de Substitute/Shield Dust é importado como se fosse aprovação moderna.

`test_motor_v18.py`: seis métodos de build/integridade, rejeição de base/payload corrompidos e reaplicação, vetores/limites, lista sonora e saída exclusiva, inclusive symlink/hardlink. Reconstrução esperada byte a byte e restauração dos quatro intervalos confirmam preservação de todos os demais bytes.

`test_treino_ev_mgba.py`: nove métodos na **v18 identificada pelo novo SHA**, sem relaxar a verificação de ROM.

### Execuções finais

| Processo final | Métodos | Tempo | Resultado |
|---|---:|---:|---|
| Build (6), Soundproof/histórico (6), EV/IV (9) | **21** | **111,446 s** | OK, sem skips |
| Correção e controles de pivô (36 cenários) | **8** | **1.756,313 s** | OK, sem skips |
| Trocas/pivôs/KO com hazards (32 cenários) | **4** | **1.759,873 s** | OK, sem skips |
| Negativos na base (2) e ciclo de vida na saída (6) | **8** | **1.507,712 s** | Base reproduz os defeitos; saída passa, sem skips |

**Total: 21 + 8 + 4 + 8 = 41 métodos distintos.** A descoberta dirigida confirma 6 de build + 8 de pivôs + 2 negativos da base + 16 regressões + 9 EV/IV. Os grupos foram chamados sem sobreposição. São 39 controles positivos/build e dois negativos exclusivamente na entrada v17, com seis subcasos negativos. Os resultados históricos 23/22/46 não foram somados.

As sondas iniciais, inclusive a falha do primeiro oráculo de histórico, foram excluídas dos totais finais. Os processos de batalha rodaram em paralelo compartilhando CPU; os tempos não medem desempenho relativo da engine. Não foi reexecutada toda a suíte histórica.

Payload recompilado independentemente e comparado byte a byte; hashes da entrada, payload e saída reconferidos após os testes. **Manifesto: 267/267 entradas verificadas**, excluindo o próprio manifesto.

## Hashes e aplicação

| Artefato | SHA-256 |
|---|---|
| Entrada v17, 33.554.432 bytes | `5db05cbb54add61a6c50e08d3e392ba610e87ca3ef462095de168de5d3e32957` |
| Payload v18, 94 bytes | `6dd0dc125fe321e4775a587ae494140d611a70061f97e8f28e94e53cf8916147` |
| Saída v18, 33.554.432 bytes | `f9a96edec0f070578dfec3d134dcb6decd5b4a5f7c296fef2c8346d7b9f504b2` |

```sh
python3 firered_gen1_9/scripts/motor_v18.py \
  --rom /privado/motor_v17.gba --saida /privado/motor_v18.gba
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V18_BASE=/privado/motor_v17.gba
export MOTOR_V18_ROM=/privado/motor_v18.gba
export MGBA_CORE=/privado/mgba_libretro.so
export TREINO_TEST_ROM="$MOTOR_V18_ROM"
python3 -m unittest test_motor_v18 test_motor_v18_mgba \
  test_motor_v18_base_mgba test_motor_v18_regressions test_treino_ev_mgba -v
```

Recompilação independente com Zig **0.17.0**, comparada byte a byte:

```sh
python3 -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi \
  -mthumb -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_pivot_v18 \
  -Wl,-T,firered_gen1_9/patches/motor_v18/payload.ld \
  firered_gen1_9/patches/motor_v18/entry.s \
  firered_gen1_9/patches/motor_v18/motor_v18.c -o /tmp/v18-rebuilt.elf
python3 -m ziglang objcopy -O binary /tmp/v18-rebuilt.elf /tmp/v18-rebuilt.bin
cmp /tmp/v18-rebuilt.bin firered_gen1_9/patches/motor_v18/payload.bin
```

## Limites e continuidade

Correção dos dois caminhos demonstrados, não implementação completa dos pivôs/sons modernos. Não acrescenta todos os sons à lista, não moderniza Substitute/Shield Dust, Mold Breaker/Mirror Armor, interações de itens/saída forçada, todas as imunidades, redirecionamento, campanha, link/multi, Teachy TV ou migração de saves. Os atributos/tipos/habilidades e o gate de Disable dos controles Protect são configurações sintéticas iniciais.

Os hazards são colocados por golpes reais e Court Change; não há escrita de RAM durante as ações. O funcionamento desse recorte não prova a legalidade das equipes nem fidelidade integral a Scarlet/Violet. Não foi reexecutada toda a suíte histórica.

Próximo recorte sugerido: **histórico e consumo de PP após bloqueio por habilidade**, incluindo consumidores de histórico e controles que distingam `FFFF` nativo do comportamento moderno, antes de ampliar a promessa de fidelidade.

ROMs, saves e estados fora do Git. Drive não atualizado; o pacote antigo lá armazenado não passa automaticamente a ser v18.

## Referências

- [Auditoria negativa da v17](AUDITORIA_V17_PIVOS_BLOQUEADOS.md), [Soundproof/Eerie Spell v12](MOTOR_V12.md), [motor v17](MOTOR_V17.md).
- [Showdown fixado: Parting Shot](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L13162-L13184), [Soundproof](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/abilities.ts#L4437-L4452), [imunidade de tipo](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/battle-actions.ts#L716-L727).
- [pret/pokefirered: cancelamento nativo antes de OBEYS](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c#L819-L864), [atualização de histórico](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c#L4235-L4260), [script Soundproof](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/data/battle_scripts_1.s#L4121-L4127). Endereços aplicados são os conferidos na ROM expandida exata.
