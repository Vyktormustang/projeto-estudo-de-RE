# Auditoria KO/EXP — causa identificada na preparação dos testes

**02/11/2026 — investigação concluída para o cenário relatado no motor v13.** Não foi necessário alterar o motor: a ROM continua **v13, com o mesmo SHA-256**. Foram corrigidos os estados sintéticos e acrescentados testes causais, de subida de nível e de batalha natural. Nenhuma ROM, save pessoal ou asset comercial foi incluído no Git.

## Conclusão demonstrada

A espera em `A ganhou 21 pontos de EXP.!` era provocada, nesse cenário, pela preparação de um **Bulbasaur de nível 10 com EXP total 1**. A fábrica fazia:

```python
seed_mon(fixture, 1, 10, moves)       # espécie 1, nível 10
set_exp_and_test_stats(state, 1, 10) # EXP total 1, atributo 10!
```

A assinatura da segunda função é `(state, experience, stat=135)`, não `(state, species, level)`. Nível e EXP são campos separados; a função não tornava esses campos coerentes. Havia sete chamadas semelhantes nas fábricas compartilhadas, usando EXP 1, 4 ou 6 para Pokémon de nível 10.

Para Bulbasaur, Charmander e Charizard, todos da curva **medium-slow**, o nível 10 começa em **560 EXP**, e o nível 11 em **742 EXP**. Os limites também foram conferidos nas ROMs exatas: tabela em offset `0x69C8E4`, nível 10 em `0x69C90C` e nível 11 em `0x69C910`.

**Intervenção causal:** conservando todos os demais bytes do cenário de batalha, mudar somente EXP criptografada e checksum de `1` para `560` faz o ganho de 21 pontos terminar, registra vitória e retorna ao callback do mapa. Isso foi executado tanto no v12 quanto no v13, sem patch na ROM.

## Experimentos e limites da interpretação

| Experimento, em v12 e v13 | Resultado confirmado |
|---|---|
| Nível 10, EXP 1, alvo a 1 HP | reproduz a espera em getexp após 20 confirmações B; EXP permanece 1, batalha ainda ativa |
| Mesmo cenário, somente EXP 560 | EXP `560 → 581`, nível 10 mantido, vitória e retorno ao mapa |
| EXP 741, um ponto antes do nível 11 | EXP `741 → 762`, nível `10 → 11`, IVs preservados, vitória e retorno ao mapa |
| Starter e encontro naturais, sem alterar HP/atributos/nível/EXP | batalha termina por vitória, EXP aumenta e o mapa é retomado |
| Fábricas singles, reservas, segundo inimigo e duplas | Pokémon sintéticos de nível 10 passam a ter EXP 560 e checksum válido |

Foi testado também **EXP 559**: apesar de incoerente com o nível 10, esse valor **não reproduziu a espera** e terminou com EXP 580. A hipótese inicial de que *todo* valor abaixo de 560 bloquearia a barra foi refutada pelo teste. Não extrapolar o comportamento do caso EXP 1 para todos os dados inválidos.

O código de referência de `Task_PrepareToGiveExpWithExpBar` subtrai o limite do nível da EXP total antes de preparar a barra. `1 - 560` produz um valor negativo/underflow nesse estado contraditório. Isso explica o tipo de inconsistência que chega à barra; não foi feita uma auditoria exaustiva de todos os valores inválidos ou caminhos internos da animação. A conclusão causal sobre **o cenário relatado** não depende dessa generalização: o teste altera somente EXP/checksum e compara o resultado.

A reprodução negativa mede uma janela limitada de frames/confirmações; não pretende provar uma espera infinita. Tampouco comprova ausência de qualquer outro defeito de EXP no motor inteiro.

## Como o retorno ao mapa é verificado

O texto de EXP continua na RAM depois da vitória; por isso **não é um indicador suficiente** de que a batalha continua ativa. O helper novo exige simultaneamente:

- `gBattleOutcome` em `0x020216C8` igual a **1** (vitória);
- `gMain.inBattle`, bit `0x02` de `0x03004A45`, **limpo**;
- `gMain.callback2` em `0x03004610` igual ao callback de campo capturado antes da batalha, **`0x080F172D`** nesta base.

O cursor do caso negativo permanece em `0x08187142`, comando getexp `0x23`. Os endereços IWRAM são lidos no bloco `0x19000` do formato de estado mGBA 0.10.5; não são offsets de save GBA. Não foram forçados callbacks, registradores ou funções durante batalhas.

O cenário natural reutiliza a introdução jogada por botões e o encontro selvagem normal. Não chama `seed_mon`, `_duel_state` ou setters de Pokémon para vencer essa batalha. Continua sendo uma sessão sintética descartável, nunca um save pessoal.

## Correções no repositório

### `tests/battle_fixture_helpers.py`

- `set_level10_starter_test_stats`: aceita somente as três espécies realmente usadas nas fábricas, no nível 10; grava EXP 560 por argumento nomeado. Espécie/nível inesperado é rejeitado, em vez de assumir uma curva universal.
- `set_party_experience`: intervenção de teste que altera somente EXP e checksum, sem tocar nível, HP, atributos ou ROM. Permite valores incoerentes **deliberadamente** para reproduções negativas.
- `party_experience`, `main_callback2`, `in_battle` e `finish_victory`: verificam a progressão e o término real, sem depender de texto residual.

### Fábricas compartilhadas v10–v13

Sete chamadas em `tests/test_motor_v10_mgba.py` foram corrigidas, cobrindo singles, dois Pokémon do jogador, segundo inimigo e duplas. Os HPs/atributos de estresse continuam como antes; **a correção é a coerência da EXP**, não uma conversão dessas fixtures em Pokémon naturais. Outras preparações históricas voltadas somente a aprendizado/menu não foram auditadas integralmente.

### Teste KO do v13

A antiga observação intermediária foi substituída por:

`test_ko_atras_de_substitute_sem_dreno_com_exp_e_retorno_ao_mapa`

Agora exige: alvo desmaiado, PPs da equipe do alvo preservados, EXP do atacante `560 → 581`, marcador de bypass limpo, vitória e retorno ao mapa. O defeito da preparação antiga continua reproduzido separadamente no teste causal, por injeção explícita de EXP 1; não se mantém um dado inválido como padrão de todas as batalhas.

## Verificação executada — 54/54, nenhum teste pulado

| Suíte | Resultado | Tempo |
|---|---:|---:|
| `test_battle_experience_fixture.py` | **12/12**: 4 estruturais + 4 integrações em cada ROM v12/v13 | 114,696 s |
| `test_motor_v13*.py`, após correção das fábricas | **33/33**: 5 estruturais + 21 singles + 1 duplas + 6 regressões herdadas | 354,454 s |
| `test_treino_ev_mgba.py` sobre v13 | **9/9** | 33,804 s |

O teste causal inclui a reprodução **negativa deliberada** com EXP inválida. Ela não é uma funcionalidade correta do motor e não é usada para afirmar que todos os cenários terminam. Diferentemente do registro anterior, o teste KO do v13 agora comprova os critérios positivos de encerramento.

As regressões de Eerie Spell/Substitute/Shield Dust, Soundproof, Endure, Transform/Mimic, duplas, estojo/save e treino passaram novamente com as fábricas corrigidas. Não foi executada a totalidade das suítes de todas as versões históricas.

```sh
# Na raiz do repositório. Os caminhos apontam a cópias privadas verificadas.
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
EXPERIENCE_BASE=/caminho/motor_v12.gba \
EXPERIENCE_ROM=/caminho/motor_v13.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_battle_experience_fixture.py' -v

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V13_BASE=/caminho/motor_v12.gba \
MOTOR_V13_ROM=/caminho/motor_v13.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_motor_v13*.py' -v

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
TREINO_TEST_ROM=/caminho/motor_v13.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_treino_ev_mgba.py' -v
```

O ambiente temporário foi reconstruído nesta etapa: mGBA 0.10.5 e cadeia parcial → estojo_v2 → motores v5–v13. Todos os aplicadores exigiram os hashes esperados. Para compilar mGBA 0.10.5 com CMake recente, foi necessário `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`.

## ROM e escopo permanecem inalterados

| Artefato | SHA-256 antes/depois, sem alteração |
|---|---|
| v12 | `fb28ad767a11add187d0fa69dec0164b3de73a9887a0c5834c5feccc675725c1` |
| v13 | `71756c820ebb71c0c64735b0e8f36cf420da29ac419f8ee09a39109d9cb4951c` |

**Não há motor v14 nesta etapa.** Não se deve instalar um patch novo nem alterar saves por causa desta correção de teste. Catálogo continua em 15.008 aprendizados / 708 das 729 omissões restauradas; quatro golpes/21 registros adiados.

Continuam pendentes: histórico após trocas, esgotamento de PP de golpes com trava multi-turno, auditoria geral de habilidades/sons/IA, campanha completa, link e Teachy TV. A próxima prioridade pode voltar aos testes de histórico e travas de Eerie Spell, sem ampliar o catálogo ainda.

Referências fixadas:

- [pret/pokefirered — controller do jogador, revisão ce6406d8](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_controller_player.c): preparação da barra de EXP e progressão de nível.
- [pret/pokefirered — Main](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/include/main.h): offsets callback2/inBattle dentro da estrutura; endereços desta ROM conferidos separadamente.
- [mGBA 0.10.5 — serialize.h](https://github.com/mgba-emu/mgba/blob/0.10.5/include/mgba/internal/gba/serialize.h): layout IWRAM/EWRAM do estado do core.

Documentação e VYK-57 atualizados. O Drive foi usado para recuperar a base privada de reconstrução; **o pacote no Drive não foi atualizado**. Não misturar offsets ou estados com a ROM histórica BAG_MOD.
