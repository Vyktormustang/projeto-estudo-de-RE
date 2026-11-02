# Motor v12 — Soundproof e auditoria de Eerie Spell

**02/11/2026 — correção isolada concluída; engine ainda parcial.** Entrada v11 validada por SHA-256, saída em novo arquivo e testes exclusivamente sintéticos em mGBA 0.10.5. Nenhuma ROM, save ou asset comercial entra no Git.

## Resultado desta etapa

- **Corrigido:** Eerie Spell (ID interno **720**, API 826) agora é bloqueado por Soundproof (habilidade **43**) pelo fluxo nativo de FireRed: mensagem, consumo de PP próprio e término da ação.
- **Auditoria corrigida:** o antigo teste de Substitute do v11 parava numa mensagem aguardando confirmação, antes de aplicar o dano. O teste foi reforçado e renomeado para caracterizar explicitamente uma limitação, não fidelidade moderna.
- **Dois defeitos continuam abertos e reproduzidos:** Substitute intercepta Eerie Spell, e Shield Dust permite seu dreno de PP. Esta versão não tenta corrigi-los indiretamente por meio da lista de sons.
- Nenhum novo aprendizado, TM, habilidade ou reserva de RAM. Permanecem **15.008 registros / 708 das 729 omissões restauradas**; Simple Beam, Ally Switch, Instruct e Revival Blessing continuam adiados (21 registros).

## Defeito Soundproof e correção mínima

Fixture sintética: alvo adormecido, 480 HP, golpes `(33,150,45,39)`, PPs `(10,10,10,10)`, último golpe Growl (45, slot 2), habilidade Soundproof. Eerie Spell é executado pela interface normal; nenhuma chamada forçada ocorre durante a batalha.

| Caso | Resultado confirmado após o turno |
|---|---|
| v11 + Soundproof | HP abaixo de 480 e PP `(10,10,7,10)` — defeito |
| v12 + Soundproof | HP 480, PP `(10,10,10,10)` e mensagem SOUNDPROOF |
| v12 sem Soundproof | HP abaixo de 480 e PP `(10,10,7,10)` |
| v12, Tackle contra Soundproof | causa dano normalmente, sem dreno adicional |
| v12, Soundproof + Substitute de 1 ou 200 HP | HP/PP do alvo e HP do Substitute preservados |
| v12, turno após Eerie Spell bloqueado | Tackle funciona; não herda bloqueio |

No caso bloqueado, Eerie Spell gasta exatamente **1 PP próprio**. Os PPs criptografados da equipe do alvo permanecem iguais, com checksum válido. Growl e Hyper Voice continuam bloqueados por Soundproof.

### Causa e endereços

A lista nativa em offset `0x20F4E8` contém somente os dez golpes:

`45, 46, 47, 48, 103, 173, 253, 319, 320, 304`, seguidos por `0xFFFF`.

O código em `0x0806F7B2` verifica habilidade 43. Em `0x0806F7B8`, o primeiro ID (45) está embutido numa instrução; o literal em **offset `0x6F840`** aponta para **tabela + 2**, e não para seu início. A busca percorre o restante até `0xFFFF`. Isso foi verificado por disassembly da ROM exata, não por transferência de offsets de outra base.

O aplicador conserva a lista inteira e acrescenta somente 720 antes do terminador. O ponteiro passa de `0x0820F4EA` para `0x090D7002`.

| Offset de arquivo | Escrita |
|---|---|
| `0x6F840..0x6F843` | literal de 4 bytes, apontando à segunda entrada da nova lista |
| `0x10D7000..0x10D7017` | lista de 24 bytes: dez IDs anteriores + 720 + terminador |

São **28 bytes escritos em duas regiões**; nem todos diferem da base. Não há payload executável novo, compilação C/Thumb, hook novo ou RAM adicional. A tabela antiga permanece intacta. Os testes restauram exatamente essas regiões e exigem igualdade integral com v11. Tabelas de movimentos/aprendizados, estojo, TMs/HMs, encontros, eventos e treino permanecem byte a byte iguais.

## Auditoria: fatos que não devem ser confundidos com correções

### Substitute — defeito confirmado, não corrigido

Eerie Spell é um golpe sonoro com bypass de Substitute nas implementações modernas de referência. Entretanto, nos testes completos de v11 e v12 **sem Soundproof**:

- Substitute inicial de 200 HP perde HP; o alvo continua com 480 HP e todos os PPs em 10.
- Substitute inicial de 1 HP chega a zero e perde o bit de status; o alvo continua com 480 HP e todos os PPs em 10.
- O golpe deveria atingir o alvo através do Substitute, preservando o boneco e aplicando o dreno elegível. Isso **ainda não ocorre**.

O teste v11 original `test_substitute_nao_drena` parava em `O SUBSTITUTO recebeu o dano ... <fb>`. Naquele ponto, o HP do boneco ainda não tinha sido atualizado: suas asserções não provavam o resultado final do turno. Agora confirma mensagens com B e exige retorno ao texto `vai fazer?`, além de verificar a redução de HP do boneco. O nome novo é `test_limite_substitute_legado_nao_drena_apos_turno_completo`.

Endereços relevantes: `BattlePokemon.status2` em `0x02021410 + 0x5C*b + 0x54`; bit Substitute `0x01000000`; HP do boneco em **`0x02021648 + 28*b + 0x0A`**. Não usar a definição incorreta de DisableStructs encontrada em fontes antigas. Os comandos nativos `healthbarupdate`/`datahpupdate` consultam `HITMARKER_IGNORE_SUBSTITUTE` (bit `0x100` de `0x0202160C`); qualquer correção futura precisa cobrir animação, dano e pós-impacto, inclusive limpeza do bit. Não há alteração desse mecanismo nesta versão.

### Shield Dust — defeito confirmado, não corrigido

Alvo adormecido com habilidade **19**, último golpe Growl e PP 10: recebe dano de Eerie Spell e fica com PP `(10,10,7,10)`. A habilidade deveria impedir o efeito adicional de redução de PP, sem bloquear o dano. O wrapper v11 em `patches/motor_v11/motor_v11.c` não verifica Shield Dust. O v12 preserva esse código.

Os testes `test_limite_substitute_*` e `test_limite_shield_dust_*` passam quando reproduzem esses defeitos conhecidos. **Não são testes de conformidade moderna e não devem ser apresentados como funcionalidades corrigidas.**

### Ainda não demonstrado nesta etapa

- Eerie Spell especificamente em duplas, histórico após troca e esgotamento de PP de golpes com trava multi-turno.
- Soundproof para os demais golpes sonoros pós-Gen 3: somente Eerie Spell foi acrescentado à lista. Não generalizar este resultado para Snarl, Boomburst, Psychic Noise etc.
- Covert Cloak, habilidades modernas, IA moderna, campanha inteira, link e Teachy TV completa.
- O código nativo de Spite chama `CancelMultiTurnMoves` (`0x0806C934`) quando o PP chega a zero. Isso é um ponto de investigação para Eerie Spell, **não demonstração de defeito de travas nem correção entregue**.

## Hashes e reprodução

| Artefato | SHA-256 |
|---|---|
| Entrada `motor_v11.gba` | `1a147ee909183cc2e3bbba0599a4d70f0b0185b01d3e4941a1f27e6c4a9eee5b` |
| Saída `motor_v12.gba`, 33.554.432 B | `fb28ad767a11add187d0fa69dec0164b3de73a9887a0c5834c5feccc675725c1` |

```sh
# Saída deve ser inexistente; nunca usar saves pessoais nos testes.
python3 firered_gen1_9/scripts/motor_v12.py \
  --rom /caminho/motor_v11.gba --saida /caminho/nova_motor_v12.gba

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V12_BASE=/caminho/motor_v11.gba \
MOTOR_V12_ROM=/caminho/nova_motor_v12.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_motor_v12*.py' -v
# 25/25, 307,612 s, zero pulados

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
TREINO_TEST_ROM=/caminho/nova_motor_v12.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_treino_ev_mgba.py' -v
# 9/9, 22,658 s, zero pulados
```

**34 verificações aprovadas:** 5 estruturais, 14 dirigidas (incluindo as **duas caracterizações de defeitos abertos**), 6 regressões herdadas de batalha/estojo/save e 9 EV/IV. As seis herdadas incluem cenários em duplas, mas não Eerie Spell em duplas. As 14 dirigidas exigem retorno ao menu ao final do turno, inclusive após as mensagens de Substitute. Fixtures de v11 e v12 são geradas separadamente nas respectivas ROMs.

Adicionalmente, o teste histórico de Substitute corrigido foi reexecutado **na v11**: 1/1, 61,165 s. Não se trata de uma nova execução completa da suíte v11, nem de teste adicional na v12. Também não houve execução integral de todos os testes de todas as versões do repositório nesta etapa.

## Referências técnicas fixadas

Consultadas via GitHub; são referências de código aberto, não prova de execução na ROM:

- [pret/pokefirered — battle_util.c, commit ce6406d8](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_util.c): lista nativa, ABILITYEFFECT_MOVES_BLOCK e CancelMultiTurnMoves.
- [pret/pokefirered — battle_script_commands.c](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c): healthbarupdate/datahpupdate e Spite. Endereços locais foram conferidos na ROM v11 separadamente.
- [Pokémon Showdown — moves.ts, Eerie Spell, commit 035c1a1f](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L4461-L4485): flags `sound` e `bypasssub`, dreno de até três PPs como efeito adicional.
- [pokeemerald-expansion — teste Eerie Spell, commit c460a866](https://github.com/rh-hideout/pokeemerald-expansion/blob/c460a8661dfa0598ae25d42a968c690ecbf489c6/test/battle/move_effect_secondary/eerie_spell.c): Shield Dust impede a redução de PP.
- [pokeemerald-expansion — teste Soundproof](https://github.com/rh-hideout/pokeemerald-expansion/blob/c460a8661dfa0598ae25d42a968c690ecbf489c6/test/battle/ability/soundproof.c): bloqueio de golpe sonoro.

Próxima prioridade recomendada: corrigir o caminho completo de Eerie Spell através de Substitute e o bloqueio do efeito adicional por Shield Dust, com testes que cheguem ao fim do turno. Depois, ampliar o teste dedicado a duplas, troca e travas. Não ampliar o catálogo antes disso.

O pacote do Drive **não foi atualizado** nesta etapa. O registro atual fica no repositório e no comentário de VYK-57. Não reutilizar save states antigos em v12; manter backups separados dos saves normais. O histórico BAG_MOD pertence a outra ROM.
