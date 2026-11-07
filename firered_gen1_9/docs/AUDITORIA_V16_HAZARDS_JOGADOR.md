# Auditoria v16 — hazards no jogador e seleção após KO em duplas

**04/11/2026 — FireRed Gen 1–9 / VYK-57.** ROM v16 exata; equipes e estados exclusivamente sintéticos. **Sem alteração de ROM, payload ou aplicador; sem v17 nesta etapa.**

## Resultado

**26 verificações concluídas, sem skips**, incluindo **cinco métodos novos / 52 subcasos**. Nenhum novo defeito foi demonstrado neste recorte:

- Spikes e Stealth Rock são colocados por golpes adversários reais, no lado do jogador.
- Roar, Whirlwind, Dragon Tail e Circle Throw provocam entrada sobre esses hazards em singles e duplas.
- O entrante sobrevive com o dano esperado ou desmaia, abrindo a seleção real de equipe.
- A escolha válida devolve o membro retirado à batalha, com novo dano de hazard na própria entrada e histórico limpo.
- Em duplas, o aliado não é substituído nem recebe o dano de entrada do outro banco.
- A seleção rejeita tanto o aliado já ativo quanto um reserva desmaiado, com mensagens efetivas da interface, sem modificar a equipe.
- Após KO, um turno adicional é jogado: sem reserva elegível, não ocorre nova troca; o membro morto não gasta PP e a batalha continua.

O recorte novo é **hazards no lado do jogador**, incluindo duplas. Não certifica todos os hazards, efeitos de entrada, modos de batalha ou a campanha. A engine continua parcial.

## Matriz nova

Arquivo: `tests/test_motor_v16_player_hazards_mgba.py`.

IDs locais: Spikes **191**, Stealth Rock **445**, Roar **46**, Whirlwind **18**, Dragon Tail **521**, Circle Throw **508**. O ID local de Stealth Rock não é seu ID oficial.

| Método / cenário | Subcasos | Controles |
|---|---:|---|
| Singles, entrada sem KO | 2 hazards × 4 phazers = **8** | HP, PP, histórico e identidade |
| Singles, KO e seleção | 2 × 4 = **8** | Desmaio, escolha pela UI, novo dano e turno seguinte |
| Duplas, entrada sem KO | 2 hazards × 2 adversários × 4 phazers = **16** | Reserva correta, aliado preservado e PP dos quatro bancos |
| Duplas, KO e seleção | 2 × 2 × 4 = **16** | Seleção, reentrada, aliado e continuação sem reserva viva |
| Duplas, rejeições na seleção | 2 hazards × 2 adversários, usando Roar = **4** | Recusa do aliado ativo e reserva morto; depois escolha válida |
| **Total** | **52** | **Cinco métodos** |

Nos controles de seleção, a IA escolheu o banco **2** em três fixtures e o banco **0** com Stealth Rock / adversário no banco 3. A suíte exige que esses quatro subcasos, em conjunto, cubram **ambos os bancos do jogador**. Não força o alvo por memória nem afirma cobertura cartesiana de cada adversário contra cada alvo para todos os golpes.

## Preparação e observação

A fixture de singles deriva da auditoria anterior de hazards; a de duplas deriva da auditoria de phazing/reservas. Há contexto sintético de treinador, não link/multi.

- Singles: dois membros por lado. Duplas: dois ativos, um reserva vivo elegível, um reserva desmaiado, um ovo e um slot vazio. O phazing deve selecionar o único reserva elegível do jogador.
- Ativos têm máximo sintético de **4.000 HP**; a reserva Charmander tem máximo **400**. A reserva começa com 400 HP para sobreviver ou exatamente com o dano de entrada para desmaiar.
- Os adversários usam Splash, exceto o ator que coloca o hazard e depois usa o phazer. O hazard tem um único PP; após gastá-lo, só o phazer permanece disponível para esse ator.
- Na seleção inicial da IA da fixture de singles, o hazard ocupa o slot 0; em duplas, ocupa o slot 1. Isso é preparação prévia da fixture, não alteração entre turnos.
- PP, stats, HP, nível e identidades são sintéticos. Não é uma validação de legalidade das equipes de campanha.
- Os PIDs dos membros são distintos. No preparo de singles, a alteração de PID preserva a ordem dos sub-blocos e refaz a criptografia; em duplas, isso já vem do construtor anterior.
- Após iniciar as ações, não há escrita em hazards, histórico, índices de equipe, RNG, HP ou alvo. As ações são entradas de botões; restaurações só carregam o estado observado do cenário.

O observador acompanha por frame as transições dos índices de batalha e o HP da equipe **por identidade**, além dos textos. A confirmação é limitada a 64 ciclos de B, com saída antecipada e estabilização; não há espera infinita. Para KO, exige transição ao callback da tela de equipe; após escolha válida, exige retorno ao callback de batalha, flag em batalha e resultado ainda zero.

## Dano, PP, histórico e preservação

| Entrada da reserva Fire / máximo 400 | Spikes, uma camada | Stealth Rock |
|---|---:|---:|
| Sobrevivência | **400→350** | **400→300** |
| KO | **50→0** | **100→0** |
| Reentrada do membro de máximo 4.000 | **−500** | **−1.000** |

O dano de Dragon Tail/Circle Throw contra o membro que sai precede o dano de hazard da reentrada. O teste não trata esse dano anterior como parte do hazard. Os tipos da reserva e do substituto são carregados nativamente ao entrar.

Ao retornar ao menu de batalha, são conferidos:

- PP de batalha contra PP da equipe, com checksum válido; todos os slots de ambas as equipes têm o custo esperado das ações efetivamente escolhidas.
- HP de batalha contra HP persistente e PID do banco contra o membro ativo.
- PIDs, OT IDs, níveis e EXP persistentes preservados na matriz principal, inclusive após reordenar e restaurar a equipe pela UI. Não há EXP do jogador por desmaio de seu próprio membro.
- Histórico zero no banco cujo ocupante entrou, histórico de Splash nos demais e do phazer no ator.
- Índices distintos dos dois ativos de cada lado em duplas; aliado do alvo com mesmo índice e 4.000 HP.
- Marcador de não consumo de PP `0x800` limpo no menu.

Após KO, a matriz principal joga mais um turno. O único reserva antes elegível agora está desmaiado: os índices não mudam, o morto continua a zero HP e os custos de PP pertencem somente aos ativos. Os golpes de phazing com dano ainda podem causar seu dano próprio; a asserção não exige HP constante nesse turno.

## Seleção inválida e escolha válida

Os quatro subcasos adicionais usam a interface real para tentar enviar:

1. O parceiro que já está em batalha: a mensagem contém **“em batalha!”**.
2. Um reserva que já estava desmaiado antes do phazing: a mensagem contém **“para batalhar!”**.

As mensagens são verificadas na RAM de texto, incluindo ausência dessas sequências no estado inicial da tela. Não basta permanecer no menu para inferir uma rejeição. O callback da tela, os índices de batalha e todos os **600 bytes da equipe de cada lado** devem permanecer iguais aos de antes das tentativas.

Em seguida, a escolha do membro vivo retirado pelo phazing deve funcionar: a tela fecha, a ordem da equipe é restaurada, o banco retorna ao membro correto, o novo dano de hazard ocorre uma vez nessa sequência e o parceiro permanece intacto. A seleção de ovo pela UI não integra essa matriz automatizada; o ovo está presente como reserva inelegível ao phazing.

## Correções do observador — não da ROM

Duas suposições do teste foram corrigidas durante a investigação:

- **Posição física não equivale a identidade durante a tela de equipe.** Ao entrar no menu, os registros do jogador são temporariamente reordenados. Uma sonda baseada apenas em slots aparentava mostrar `4.000→0` no membro errado. A observação final acompanha PIDs únicos; ao voltar à batalha, confirma a identidade e a ordem persistentes. A leitura do código público de `UpdatePartyToBattleOrder` / `UpdatePartyToFieldOrder` explica essa ordenação.
- **O alvo da IA não é sempre o banco 2.** O primeiro teste adicional falhou em Stealth Rock / ator 3 porque exigia esse banco, mas a IA escolheu legalmente o banco 0. A navegação final depende do banco observado, exige a reserva correta e exige cobertura dos dois bancos. Não se alterou o RNG ou o alvo para satisfazer o teste.

A tentativa adicional inicial terminou com **uma falha em quatro subcasos, 103,403 s**. Não é contada como aprovação nem como defeito de engine. Sondas exploratórias e capturas de tela temporárias também ficam fora da contagem final e do Git.

## Execuções finais

mGBA **0.10.5**, ROM v16 conferida antes/depois. Todos os processos finais terminaram com código zero:

| Processo final | Métodos | Tempo | Resultado |
|---|---:|---:|---|
| Matriz principal nova, ainda com quatro métodos ao iniciar | **4** | **660,539 s** | OK, sem skips |
| Controle adicional de seleção, versão corrigida, executado separadamente | **1** | **109,474 s** | OK, sem skips |
| Hazards adversários anteriores (7) + build/estrutura v16 (5) + treino EV/IV (9) | **21** | **501,316 s** | OK, sem skips |
| **Total desta etapa** | **26** | | **26/26, sem skips** |

São **4 + 1 + 21**, não uma execução única de cinco métodos novos. Os quatro métodos principais não mudaram funcionalmente depois que seu processo começou. A contagem de 52 subcasos refere-se apenas aos cinco métodos novos. Os resultados históricos de 41, 29 e 85 verificações não são somados como execuções novas; tampouco foi reexecutada a totalidade das suítes históricas ou das regressões de Eerie nesta etapa.

O ambiente temporário havia sido reiniciado. A base privada foi baixada em leitura do Drive; a cadeia parcial→estojo v2→motor v5…v16 foi reconstruída com hash de entrada verificado antes de cada aplicação e arquivos novos. mGBA foi recompilado a partir da tag 0.10.5. O checkout local foi realinhado ao commit já publicado `4c919bd` somente após confirmar igualdade integral dos arquivos com o remoto; nenhum arquivo divergente foi descartado.

## Reprodução e hashes

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V16_ROM=/privado/motor_v16.gba
export MOTOR_V16_BASE=/privado/motor_v15.gba
export MGBA_CORE=/privado/mgba_libretro.so
export TREINO_TEST_ROM="$MOTOR_V16_ROM"
python3 -m unittest test_motor_v16_player_hazards_mgba -v
python3 -m unittest test_motor_v16_hazards_ko_mgba test_motor_v16 test_treino_ev_mgba -v
```

A reprodução integral do arquivo novo hoje executa seus cinco métodos; a tabela acima registra a divisão efetivamente utilizada nesta etapa.

| Artefato inalterado | SHA-256 |
|---|---|
| ROM v16, 33.554.432 bytes | `644b140dc4fd1f4fab4c7ed9304fb266865d3e81825140c01c2c275564dc0fcc` |
| Base v15 | `a6b454f7cbafad8c05e1b8aa2028087a596bbeff4f0184c826a92ebb7e554147` |
| Payload v16, 300 bytes | `f1946a84a7932215b83e6d01e4d6794e4b1dbab334fb49c2236b48ad185c0ceb` |

## Limites e próximos controles

Continuam fora deste recorte: KO por hazards **no lado adversário em duplas**, dois desmaios simultâneos e seleção de dois substitutos; derrota/whiteout do jogador; entrada voluntária e pivôs; hazards combinados no jogador; múltiplas camadas de Spikes; Toxic Spikes/Sticky Web; Flying no lado do jogador; interações com habilidades/itens pós-Gen 3, Gravity, Levitate ou efeitos simultâneos. As regressões anteriores de combinação/Flying/vitória são do lado adversário em singles.

Próximo recorte recomendado: **KO e reposição adversária em duplas**, seguido de dois desmaios e seleção de dois substitutos. Link/multi, campanha, Teachy TV e migração de saves pessoais seguem sem certificação.

**ROMs, saves, estados e capturas de jogo não foram incluídos no Git. Nenhum save pessoal foi utilizado. Drive não atualizado; o pacote armazenado lá não passa automaticamente a ser v16.**

## Referências

- [pret/pokefirered, `party_menu.c`, ce6406d](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/party_menu.c): `TrySwitchInPokemon`, validações de HP/ativos/ovo, ações da tela e conversões entre ordem de batalha/campo. Código público como referência; os offsets da ROM expandida não são transplantados da versão original.
- [Auditoria anterior de hazards/KO](AUDITORIA_V16_HAZARDS_KO.md): fórmulas de dano, referências fixadas e os sete testes de regressão reexecutados.
- [Auditoria de phazing em duplas](AUDITORIA_V16_DUPLAS_PHAZING.md): origem da fixture, identidades e reservas inelegíveis.
- [Especificação da v16](MOTOR_V16.md): correção original, hashes e limites da engine.
