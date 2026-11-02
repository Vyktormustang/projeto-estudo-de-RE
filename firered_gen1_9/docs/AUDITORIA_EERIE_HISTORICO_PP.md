# Eerie Spell — histórico após trocas e sequências com PP zero

**02/11/2026 — auditoria dirigida concluída no motor v13, sem patch de ROM.** Foram acrescentados oito testes (dois de preparação de dados e seis de integração) e reexecutadas regressões v13/EV-IV. Somente estados sintéticos, mGBA 0.10.5 e ROM identificada por SHA-256; nenhum save pessoal.

> **Adendo posterior (02/11/2026):** a [auditoria dedicada de potência](AUDITORIA_ROLLOUT_POTENCIA.md) confirmou a progressão de Rollout/Ice Ball e o bônus de Defense Curl, mas encontrou um desvio separado: Protect interrompendo uma sequência ativa desconta um PP extra. Esse caso não estava coberto pela presente suíte. O defeito segue aberto, sem mudança no v13; a conclusão abaixo permanece restrita aos cenários originais.

## Resultado e decisão

**Não foi demonstrado defeito que exija uma nova ROM nos cenários testados.** O v13:

- Limpa o histórico na troca normal, inclusive quando um Pokémon retorna ao campo.
- Não apaga histórico nem gasta PP quando o menu de troca é cancelado.
- Mantém sequências já iniciadas de Thrash, Rollout e SolarBeam mesmo após Eerie Spell zerar seus PPs.
- Encerra essas sequências normalmente nos casos testados, sem underflow de PP; depois usa Struggle quando nenhum golpe tem PP e a ação pode ocorrer.

A continuação a PP zero é compatível com a referência moderna consultada. **Não foi adicionado `CancelMultiTurnMoves` a Eerie Spell.** A chamada existente no Spite nativo de Gen 3, apontada como hipótese de investigação nas etapas anteriores, não basta para justificar copiar esse comportamento para Eerie Spell.

Isso não é uma certificação integral de mecânicas Scarlet/Violet; as conclusões têm o escopo abaixo.

## 1. Sequências de múltiplos turnos

Preparação: alvo com moveset de IDs distintos `(golpe testado,150,45,39)`, PPs `(4,0,0,0)` e histórico inicialmente zero. Não se escreve um histórico fictício nem se injeta uma trava já ativa: o adversário executa o golpe pelo fluxo normal. Os PPs são coerentes entre estrutura de batalha e equipe criptografada. Atributos/HP são sintéticos para manter os participantes vivos.

### Eerie Spell age depois do alvo

O adversário usa um PP (4 → 3); Eerie Spell drena os três restantes. Nas continuações os PPs permanecem **zero tanto na batalha quanto na equipe**, com checksum válido.

| Golpe | Observação automatizada |
|---|---|
| **Thrash (37)** | Continua no turno seguinte com PP zero, causa dano e termina a trava. A fixture determinística produz uma sequência de dois turnos seguida de confusão. O teste não limpa a confusão artificialmente: espera uma ação válida até observar Struggle. |
| **Rollout (205)** | Completa cinco turnos, com a trava ativa até o quarto e limpa após o quinto. No sexto usa Struggle. |
| **SolarBeam (76)** | Carrega no primeiro turno, tem seus PPs zerados, dispara no segundo e encerra a trava. No terceiro usa Struggle. |

**Não se afirma a fidelidade da progressão de potência/dano de Rollout.** Aqui foram medidos continuidade, dano presente, contagem de turnos, histórico e PPs. Também não foram cobertas todas as possíveis durações/RNG de Thrash.

### Eerie Spell age antes do alvo

Em três subcasos (Thrash, Rollout e SolarBeam):

1. No primeiro turno não existe histórico do alvo. Eerie Spell causa seu dano, mas não drena um slot arbitrário; o golpe próprio do adversário deixa **3 PP**.
2. No segundo turno Eerie Spell age primeiro, encontra o histórico registrado naturalmente e reduz 3 → 0.
3. A continuação do adversário ainda ocorre naquele turno e causa dano. A ordem das mensagens é verificada: Eerie Spell antes do golpe adversário.

Assim, a cobertura não depende apenas de esgotar PP depois que o alvo já agiu.

## 2. Troca manual, retorno e novo histórico

Dois Pokémon sintéticos do jogador, ambos com EXP coerente com o nível 10, enfrentam um oponente que usa Eerie Spell. Toda a sequência abaixo usa botões da interface; não se força a troca alterando índices de equipe.

| Fase | Histórico do jogador | PPs verificados na equipe |
|---|---|---|
| Pokémon A usa Splash (150) | 150 | `(10,10,10,10) → (6,10,10,10)` — um PP próprio e três drenados |
| Troca para B; Eerie Spell acerta o entrante | **0** | B mantém `(12,11,13,14)`; A permanece `(6,10,10,10)` |
| B usa Growl (45) e recebe Eerie Spell | 45 | B passa a `(8,11,13,14)` |
| Troca de volta para A; Eerie Spell acerta | **0** | A mantém `(6,10,10,10)`; B permanece `(8,11,13,14)` |
| A usa Splash novamente | 150 | A passa a `(2,10,10,10)` |

B também conhece Splash, mas em outro slot. Mesmo assim, não herda o histórico de A e não perde os PPs desse golpe ao entrar. O teste confere os índices físicos 0 → 1 → 0, os PPs em batalha e na equipe, e os checksums. A tela de equipe apresenta o ativo à frente; DOWN seleciona o reserva visual tanto na ida quanto na volta.

### Cancelamento

Depois de A registrar Splash, o teste abre Pokémon e cancela com B antes de escolher um substituto. Confirma que índice, histórico, PPs de A e PPs do oponente não mudaram. A próxima ação Splash/Eerie Spell reduz corretamente 6 → 2. Cancelar o menu não foi confundido com executar uma troca ou consumir um turno.

## 3. Por que não copiar o cancelamento de Spite antigo

Referência consultada: **Pokémon Showdown, revisão fixa `035c1a1f3c2ed286cda4c0d8623800699cd2c1c0`**:

- Eerie Spell chama `target.deductPP(move.id, 3)` sobre o último golpe; essa rotina reduz PP com piso zero e não remove travas.
- `runMove` não exige um novo desconto de PP quando já existe um `lockedMove`.
- `lockedmove` e `twoturnmove` fornecem o golpe que deve continuar; Rollout tem sua própria condição de trava.
- `clearVolatile` limpa `lastMove`, coerentemente com os resultados de troca medidos nesta ROM.

Essa é uma referência de implementação moderna, **não um teste em cartucho de Scarlet/Violet**. Os testes mGBA constituem a evidência sobre esta ROM. A ausência de uma chamada a CancelMultiTurnMoves no helper de Eerie Spell não é, por si só, um bug.

Fontes:

- [moves.ts — Eerie Spell](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L4461-L4485)
- [moves.ts — Rollout](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/moves.ts#L15360-L15420)
- [conditions.ts — lockedmove/twoturnmove](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/data/conditions.ts#L253-L322)
- [pokemon.ts — deductPP](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/pokemon.ts#L909-L923) e [limpeza de histórico](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/pokemon.ts#L1553-L1573)
- [battle-actions.ts — execução de golpe já travado](https://github.com/smogon/pokemon-showdown/blob/035c1a1f3c2ed286cda4c0d8623800699cd2c1c0/sim/battle-actions.ts#L335-L349)

## 4. Endereços observados nesta base

- `gLastMoves`: **`0x020215D4`**, um u16 por banco.
- `gBattlerPartyIndexes`: **`0x020213F8`**, um u16 por banco.
- `gBattleMons`: **`0x02021410`**, stride `0x5C`.
- PPs de batalha: `gBattleMons + 0x5C*b + 0x25..0x28`.
- `status2`: `gBattleMons + 0x5C*b + 0x54`; trava múltiplos turnos `0x1000`, confusão nos três bits inferiores.
- Equipe do jogador: **`0x0203A98C`**; equipe inimiga: **`0x0203A734`**, stride 100 bytes, subestruturas criptografadas e checksum conferidos.

Os testes usam as fábricas corrigidas pela [auditoria EXP](AUDITORIA_EXP_FIXTURES.md). Não há chamadas forçadas de rotinas durante a batalha; após cada turno, mensagens são confirmadas e exige-se o retorno ao menu `vai fazer?` antes das asserções.

## 5. Execução — 50/50 nesta etapa, nenhum pulado

| Suíte | Resultado | Tempo |
|---|---:|---:|
| Nova `test_eerie_history_mgba.py` | **8/8**: dois testes de dados + seis integrações | 106,314 s |
| Regressões `test_motor_v13*.py` | **33/33** | 345,430 s |
| Treino EV/IV sobre v13 | **9/9** | 22,149 s |

As regressões incluem Substitute/Shield Dust/Soundproof, Endure, duplas, estojo/save e KO com EXP/retorno ao mapa. A suíte específica de auditoria EXP (12 testes) não foi reexecutada nesta etapa; seus resultados anteriores não foram somados aos 50 atuais. Não houve execução completa de todas as suítes históricas.

```sh
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
EERIE_HISTORY_ROM=/caminho/motor_v13.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_eerie_history_mgba.py' -v

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

A ROM é validada antes e depois da nova suíte. SHA-256 v13 permanece:

`71756c820ebb71c0c64735b0e8f36cf420da29ac419f8ee09a39109d9cb4951c`

**Não há motor v14, payload novo, escrita na ROM ou alteração de saves.** Nenhum aplicador, catálogo ou código de motor foi alterado. Continuam 15.008 aprendizados / 708 de 729 omissões restauradas e quatro golpes/21 registros adiados.

## Limites e próximos passos

- Trocas testadas: manuais, singles, lado do jogador contra Eerie Spell. Ainda não se generaliza para trocas forçadas, pivôs, Baton Pass, retorno após desmaio ou todas as disposições de duplas.
- Sequências testadas: Thrash, Rollout e SolarBeam nas condições descritas. Encore, Disable, Torment, Pressure, condições meteorológicas, habilidades/itens especiais e outras travas ainda exigem testes próprios.
- A contagem de turnos de Rollout passou; sua progressão de potência não foi validada por esta suíte e deve ser auditada separadamente antes de alegar fidelidade do golpe inteiro.
- Próxima prioridade recomendada: interações com Encore/Disable e trocas por pivô/forçadas, ou auditoria dedicada de potência de movimentos consecutivos. Não aumentar o catálogo com base apenas nestes testes.
- IA moderna, campanha completa, link e Teachy TV continuam sem validação integral. Não reutilizar offsets da ROM histórica BAG_MOD.

Documentação e VYK-57 atualizados; pacote Drive **não atualizado** nesta etapa.
