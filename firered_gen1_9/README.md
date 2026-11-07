## Atualização — 07/11/2026 — publicação solicitada

Última ROM validada: **V42**, sem alterações após a auditoria das ilhas. [Publicação, Drive e verificação de integridade](docs/PUBLICACAO_V42.md). Fontes/progresso preservados na branch de trabalho, sem ROMs ou saves no GitHub. A [auditoria de Cosmog é parcial](docs/PROGRESSO_COSMOG_V42.md): cenas de evolução e obtenção de ovo observadas; eclosão, posse simultânea dos dois finais e suíte nativa consolidada ainda pendentes. As notas abaixo são históricas.

# gba-re 🔧 Engenharia Reversa de GBA + Mod Menu (item cheat)

## Auditoria dos trajetos V42 — ida, capturas e retorno concluídos

**6/6 testes aprovados; 98,001 s no runner. A ROM V42 permaneceu intacta.** Dois percursos independentes saem de Vermilion, recebem os bilhetes pelo marinheiro, visitam os locais dos eventos e voltam de barco: Navel Rock com Ho-Oh 70 e Lugia 70 na mesma viagem; Birth Island com o puzzle completo e Deoxys 30. Os Pokémon persistem após save/Continuar no retorno.

**24 mapas das ilhas, 549 passos manuais, 44 transições internas e quatro viagens de barco.** Sem warps de teste dentro das ilhas ou edição de contadores/inimigos/resultados durante os percursos. Chegada inicial a Vermilion, progresso, Rainbow Pass e Master Balls são preparação sintética; não é certificação de campanha completa desde o início.

[Relatório](docs/AUDITORIA_TRAJETOS_V42.md), [resultados](docs/trajetos_v42_resultados.json), [log](docs/trajetos_v42.log), [estrutura](docs/trajetos_v42_estrutura.json), [passos](docs/trajetos_v42_passos.csv), [transições](docs/trajetos_v42_transicoes.csv), [capturas](docs/trajetos_v42_capturas.csv) e [observações](docs/trajetos_v42_observacoes.json). Esta etapa complementa a limitação histórica de trajetos/retorno no relatório de criação da V42 abaixo. Sem nova ROM, commit, push ou publicação no Drive; as contagens não são cumulativas.

## Motor V42 — bilhetes das ilhas pelo marinheiro de Vermilion

**Mystic Ticket e Aurora Ticket agora são entregues ao conversar com o marinheiro após a progressão do Rainbow Pass, com o passe na bolsa.** Bilhetes já possuídos corrigem suas liberações ausentes; conversas repetidas não duplicam itens. Bolsa cheia não concede liberações indevidas; com uma vaga, entrega Mystic e deixa Aurora pendente. A falha de um item não impede reparar o outro já possuído.

**535 bytes alterados; 19/19 testes aprovados em 220,527 s**, sem falhas/erros/skips. Inclui aquisição nativa e duas viagens aos portos, duas matrizes de 16 combinações, capacidade/repetição, atualização de save V41 sem reentrar no mapa e retorno V42 → V41 → V42, as três capturas lendárias com persistência, puzzle inteiro de Deoxys e 2.200 sorteios de Altering Cave. Progresso e chegadas são sintéticos: não é certificação de campanha completa. Nenhum save pessoal foi usado.

[Relatório e instruções](docs/MOTOR_V42.md), [resultados](docs/motor_v42_resultados.json), [log](docs/motor_v42.log), [estrutura](docs/motor_v42_estrutura.json), [matriz de entrega](docs/motor_v42_matriz.csv), [capturas](docs/motor_v42_capturas.csv) e [observações](docs/motor_v42_observacoes.json). Preserva eventos/capturas, encontros, guia, relógio e formato de save. Sem publicação no Drive, commit ou push. A V42 resolve a pendência de bilhetes descrita na auditoria histórica abaixo; as contagens anteriores não são cumulativas.

## Auditoria das ilhas na V41 — eventos funcionam; obtenção dos bilhetes pendente

**Lugia (70), Ho-Oh (70) e Deoxys (30) capturados e preservados após save/Continuar em testes sintéticos.** O puzzle inteiro de Deoxys foi resolvido por botões, sem editar seus contadores: 11 interações e 52 passos. As flags de evento concluído/ocultação persistiram.

O marinheiro de Vermilion exige **bilhete + flag de liberação**, além da progressão: Mystic Ticket/`0x084A` para Navel Rock; Aurora Ticket/`0x084B` para Birth Island. Foram testadas as 16 combinações de itens/flags, dois controles de progresso e viagens nativas até ambos os portos. **Ainda não foi comprovada uma forma normal de receber os bilhetes e flags na campanha**; scripts de Mystery Gift presentes na ROM não bastam para essa conclusão.

**9/9 métodos aprovados em 144,618 s**, sem falhas/erros/skips. Transporte com requisitos sintéticos; capturas a partir de chegadas sintéticas independentes aos locais dos eventos. Isso não é uma viagem contínua desde o início da campanha até as três capturas; trajetos internos/retorno não certificados. Master Balls de teste, não ensaio de taxa de captura comum.

[Relatório](docs/AUDITORIA_ILHAS_V41.md), [matriz](docs/ilhas_v41_matriz.csv), [capturas](docs/ilhas_v41_capturas.csv), [evidência estrutural](docs/ilhas_v41_estrutura.json), [resultados](docs/ilhas_v41_resultados.json) e [log](docs/ilhas_v41.log). **Sem nova ROM, V42, Drive, commit ou push; V41 intacta.** Próxima proposta: entrega controlada dos bilhetes após Rainbow Pass, mantendo os eventos nativos. Os resultados abaixo permanecem históricos, não contagens cumulativas.

## Motor parcial V41 — Type: Null em todas as variantes de Altering Cave

**Type: Null, nível 20, 10% nominal, de dia e à noite, em Altering Cave (Ilha 6)** — não depende mais de selecionar a variante 7. Foram substituídos oito slots repetidos de espécies comuns; todas essas espécies continuam na própria caverna. A variante 7, os demais slots e o mecanismo de seleção ficam intactos. As chances das oito espécies comuns afetadas diminuem em 10 pontos percentuais nas respectivas variantes; nenhuma espécie é eliminada.

**30 bytes alterados**, em oito registros, sem código/flags/save novos. Preservados os eventos especiais, as 68 áreas noturnas, o guia, o relógio e os demais mapas. **15/15 testes aprovados em 84,083 s**, sem falhas/erros/skips: reconstrução exata, 2.200 sorteios determinísticos, Repel, seletores das 68 áreas, regressões de Tanoby/evolução, caminhada/captura diurna e noturna e flash **V41 → V40 → V41** com o Pokémon preservado.

A chegada à caverna foi sintética por cópia descartável + save normal; a caminhada e captura ocorreram na ROM exata. Uma Master Ball de teste tornou a captura determinística. Isso não certifica viagem natural até a Ilha 6, taxas de captura comuns ou campanha completa. Os 103 testes históricos da V40 não foram reexecutados nesta rodada.

[Relatório e reprodução](docs/MOTOR_V41.md), [108 slots das nove variantes](docs/encontros_altering_cave_v41.csv), [resultados](docs/validacao_v41_resultados.json) e [log](docs/validacao_v41.log). Builder `scripts/motor_v41.py`, base V40 exata; SHA-256 da V41: `662225325c50af5aeb568da97a10110cff300aff55e1a6ec87f0d11c1a5f5d50`.

Faça backup do save normal e use **Continuar**, não savestates de outra versão. Entrega local, sem Drive, commit ou push. **Lugia/Ho-Oh/Deoxys, cópias de Cosmog e demais pendências da auditoria continuam sem alteração.** A auditoria V40 abaixo é histórica: sua pendência de Type: Null foi tratada nesta V41.

## Auditoria dos 1.025 — V40 preservada, sem nova ROM

**1.025 referências de obtenção identificadas; não é certificação de 1.025 capturas/acessos normais.** As 931 espécies não lendárias/míticas constam nas tabelas. Os 94 lendários/míticos aparecem em tabelas, objetos adicionais, sete eventos nativos ou evoluções.

Pendências prioritárias: **Type: Null exige a variante 7 de Altering Cave (VAR 0x4024)**; comprovar acesso às ilhas de **Lugia, Ho-Oh e Deoxys**; verificar outra cópia/repetição de **Cosmog** para Solgaleo e Lunala no mesmo save. Cresselia foi gerada em sondagem nativa após ligar o desbloqueio de Tanoby, mas o puzzle/acesso natural não foi testado. Cosmog → Cosmoem no 43; Cosmoem → Solgaleo no 53 e Lunala a partir do 54, sem distinção dia/noite: regra simplificada da base, não fidelidade moderna.

**14/14 métodos aprovados em 23,245 s**, sem erros/falhas/skips (10 estruturais + 4 de sondagens em mGBA, 46 observações). ROM V40 inalterada; os 103 testes históricos da entrega abaixo não foram reexecutados nesta auditoria. Nenhuma expansão noturna, V41, publicação no Drive, commit ou push.

Veja o [relatório com limites e reprodução](docs/AUDITORIA_OBTENCAO_V40.md), a [planilha das 1.025 espécies](docs/cobertura_1025_v40.csv), [2.992 ocorrências de tabelas](docs/locais_obtencao_v40.csv), [117 referências de evento](docs/eventos_obtencao_v40.csv), [449 registros de evolução](docs/evolucoes_v40.csv) e [resultados](docs/validacao_obtencao_v40.json).

## Motor parcial v40 — 68 áreas, Rock Tunnel e escadas do Rubi

Expansão para **Rock Tunnel 1F/B1F e Mt. Ember Ruby Path B1F Stairs/B2F Stairs**, preservando as 64 áreas anteriores. As duas salas de escadas, antes excluídas, agora recebem tabelas noturnas, sem alteração das próprias escadas. À noite, **20:00–05:59**:

| Área | Novos encontros noturnos (níveis preservados) |
|---|---|
| Rock Tunnel — 1F | Woobat (16) / Noibat (17) |
| Rock Tunnel — B1F | Sableye (17) / Carbink (16) |
| Rubi — Escadas B1F | Houndoom (42) / Lampent (24) |
| Rubi — Escadas B2F | Litwick (34) / Magcargo (40) |

Dois slots de **10% nominal por área**, antes dos filtros, nos índices 2/3. Iron Thorns, Tyranitar, Charizard, Houndoom nativo e os demais slots mantidos preservados. Zubat, Geodude e Onix de Rock Tunnel intactos. Não mudam dia, níveis, frequências, Flash, iluminação nativa, acessos, puzzles ou eventos fixos.

Guia em **três páginas (8/8/8 opções)**. Na placa da Rota 1: **Mais areas / ilhas → Mais areas → Rock Tunnel / Rubi**. Os quatro andares principais do Rubi continuam no grupo anterior. A terceira página chegou ao limite de oito opções. O [CSV completo](docs/guia_encontros_horario_v40.csv) tem **1.632 linhas**.

**103/103 métodos aprovados**, sem falhas, erros ou skips: 13.600 casos determinísticos, 136 consultas ao guia, caminhada nas quatro áreas após chegada sintética/save na ROM exata, paleta/relógio, flash v39↔v40, seis regressões da auditoria v32 e testes dos limites de memória. Quinze capturas conferidas visualmente. Não certifica acesso normal, uso de Flash/todos os estados de iluminação, puzzles, travessia das escadas, evento do Rubi, campanha completa ou saves pessoais.

Tabelas: 4.624 B em reserva de 8.192 B. Menu: 1.584 B em reserva ampliada para **2.048 B**, sem sobreposição. Relógio, MUNDO, Opções/SELECT e save intactos. Builder `scripts/motor_v40.py`, base v39 exata, oito intervalos, saída exclusiva e reconstruções idênticas. SHA-256: `10214ba64a38a543d381db9d41eb37f46458a0926057d028dda2839b1f87e7e1`.

O ambiente foi restaurado: v18 arquivada → builders v19–v39, hashes conferidos; mGBA recompilado no mesmo commit, com novo hash registrado. Os resultados acima são da rodada nova, não reaproveitados.

Veja [MOTOR_V40.md](docs/MOTOR_V40.md), [resultados](docs/validacao_v40_resultados.json) e [log](docs/validacao_v40.log). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local, sem publicação no Drive, commit ou push.** As versões e auditorias abaixo são históricas, não contagens cumulativas.

## Motor parcial v39 — 64 áreas, Cerulean e Seafoam 1F

Expansão para **Cerulean Cave 1F, 2F, B1F e Seafoam Islands 1F**, preservando as 60 áreas anteriores. **Seafoam 1F agora recebe uma tabela noturna**, mantendo Pheromosa. À noite, **20:00–05:59**:

| Área | Novos encontros noturnos (níveis preservados) |
|---|---|
| Cerulean Cave — 1F | Umbreon (46) / Weavile (46) |
| Cerulean Cave — 2F | Gengar (52) / Spiritomb (52) |
| Cerulean Cave — B1F | Hydreigon (55) / Drapion (55) |
| Seafoam Islands — 1F | Delibird (22) / Swinub (22) |

Dois slots de **10% nominal por área**, antes dos filtros. **Kartana, Flutter Mane, Iron Jugulis e Pheromosa preservados**. Em Seafoam 1F usam-se slots 3/4, mantendo Pheromosa no 2; índices começam em zero. Exceções anteriores mantidas. Outros slots, níveis, frequências e tabelas diurnas intactos; sem mudar iluminação nativa, acessos, puzzles ou eventos fixos.

O guia continua em **três páginas (8/8/7 opções)**. Na placa da Rota 1: **Mais areas / ilhas → Mais areas → Cerulean / Seafoam**. Os quatro subsolos de Seafoam permanecem no grupo anterior, com textos e encontros intactos. B/Voltar retorna à página anterior; utilidades retornam à origem; Sair funciona nas três. O [CSV completo](docs/guia_encontros_horario_v39.csv) tem **1.536 linhas**.

**103/103 métodos aprovados**, sem falhas, erros ou skips: 12.800 casos determinísticos, 128 consultas ao guia, caminhada nas quatro novas áreas após chegada sintética/save na ROM exata, iluminação/relógio, flash v38↔v39, seis regressões da auditoria da v32 e o novo teste de limites da reserva. Quatorze capturas conferidas visualmente. Não certifica acesso normal às cavernas, requisitos de pós-jogo, puzzles, eventos fixos, campanha completa ou saves pessoais.

A tabela de encontros cresceu para **4.352 B**, em reserva ampliada para **8.192 B**, sem sobreposição com o menu. Relógio, MUNDO, Opções/SELECT e formato de save intactos. Builder `scripts/motor_v39.py`, base v38 exata, oito intervalos e saída exclusiva; payload/ROM reconstruídos de forma idêntica. SHA-256: `a7d35f5f92b8aae0618d32b8dc0b822d086c0325c030f509f0aaac8f2a08bac5`.

Veja [MOTOR_V39.md](docs/MOTOR_V39.md), [resultados](docs/validacao_v39_resultados.json) e [log](docs/validacao_v39.log). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local, sem publicação no Drive, commit ou push.** As versões e auditorias abaixo são históricas, não contagens cumulativas.

## Motor parcial v38 — 60 áreas, caminho do Rubi

Expansão para **Mt. Ember Ruby Path 1F, B1F, B2F e B3F**, preservando as 56 áreas anteriores. As duas salas de escadas ficam fora da expansão. À noite, **20:00–05:59**:

| Andar do Rubi | Novos encontros noturnos (níveis preservados) |
|---|---|
| 1F | Camerupt (34) / Magcargo (34) |
| B1F | Numel (34) / Lampent (40) |
| B2F | Houndoom (42) / Salandit (24) |
| B3F | Litwick (30) / Sableye (24) |

Dois slots de **10% nominal por área**, antes dos filtros. **Stakataka, Iron Treads, Aerodactyl, Garchomp e Blacephalon preservados**. Slots alternativos no 1F (3/4) e B3F (2/4), com índices começando em zero; exceções anteriores mantidas. Outros slots, níveis, frequências e tabelas diurnas intactos; sem mudar iluminação nativa, pedras/Strength, escadas, acessos, evento do Rubi ou história.

O guia continua em **três páginas (8/8/6 opções)**. Na placa da Rota 1: **Mais areas / ilhas → Mais areas → Mt. Ember - Rubi**. Mansao Pokemon, Liga / Usina e Seafoam - Subsolos continuam na terceira página. B/Voltar retorna à página anterior; utilidades retornam à origem; Sair funciona nas três. O [CSV completo](docs/guia_encontros_horario_v38.csv) tem **1.440 linhas**.

**102/102 métodos aprovados**, sem falhas, erros ou skips: 12.000 casos determinísticos, 120 consultas ao guia, caminhada nos quatro novos andares após chegada sintética/save na ROM exata, iluminação/relógio, flash v37↔v38 e seis regressões da auditoria da v32. Treze capturas conferidas visualmente. Não certifica acesso normal ao caminho do Rubi, pós-jogo, solução de pedras, coleta/entrega do Rubi, campanha completa ou saves pessoais.

Relógio, MUNDO, Opções/SELECT e formato de save intactos. Builder `scripts/motor_v38.py`, base v37 exata, oito intervalos e saída exclusiva; payload/ROM reconstruídos de forma idêntica. SHA-256: `e22695512ef007fbeacd36f643440393528e9e43fc17224eac83ea04e63593c2`.

Veja [MOTOR_V38.md](docs/MOTOR_V38.md), [resultados](docs/validacao_v38_resultados.json) e [log](docs/validacao_v38.log). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local, sem publicação no Drive, commit ou push.** As versões e auditorias abaixo são históricas, não contagens cumulativas.

## Motor parcial v37 — 56 áreas, subsolos de Seafoam

Expansão para **Seafoam Islands B1F, B2F, B3F e B4F**, preservando as 52 áreas anteriores. O **1F fica fora da expansão**, com Pheromosa e seus demais encontros intactos. À noite, **20:00–05:59**:

| Área | Novos encontros noturnos (níveis preservados) |
|---|---|
| Seafoam — B1F | Sneasel (28) / Snorunt (22) |
| Seafoam — B2F | Bergmite (30) / Froslass (24) |
| Seafoam — B3F | Haunter (32) / Duskull (32) |
| Seafoam — B4F | Snover (34) / Beartic (32) |

Dois slots de **10% nominal por área**, antes dos filtros. **Great Tusk, Iron Hands, Baxcalibur, Eevee, Glaceon, Espeon e Flareon preservados**. Slots alternativos no B2F (2/5), B3F (2/4) e B4F (3/4), com índices começando em zero; exceções anteriores mantidas. Outros slots, níveis, frequências e tabelas diurnas intactos; sem mudar iluminação nativa, correntes, pedras/Strength, acessos, eventos fixos ou história.

O guia continua em **três páginas (8/8/5 opções)**. Na placa da Rota 1: **Mais areas / ilhas → Mais areas → Seafoam - Subsolos**. Mansao Pokemon e Liga / Usina permanecem nessa terceira página, com os mesmos textos e encontros. B/Voltar retorna à página anterior; utilidades retornam à origem; Sair funciona nas três. O [CSV completo](docs/guia_encontros_horario_v37.csv) tem **1.344 linhas**.

**102/102 métodos aprovados**, sem falhas, erros ou skips: 11.200 casos determinísticos, 112 consultas ao guia, caminhada nos quatro novos subsolos após chegada sintética/save na ROM exata, iluminação/relógio, flash v36↔v37 e seis regressões da auditoria da v32. Doze capturas conferidas visualmente. Não certifica acesso normal a Seafoam, solução de pedras/correntes, eventos fixos, campanha completa ou saves pessoais.

Relógio, MUNDO, Opções/SELECT e formato de save intactos. Builder `scripts/motor_v37.py`, base v36 exata, oito intervalos e saída exclusiva; payload/ROM reconstruídos de forma idêntica. SHA-256: `9ce2266b8a657f69c79cad8469ec25676dc5bf223c90b28360a5433b84b4b1a3`.

Veja [MOTOR_V37.md](docs/MOTOR_V37.md), [resultados](docs/validacao_v37_resultados.json) e [log](docs/validacao_v37.log). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local, sem publicação no Drive, commit ou push.** As versões e auditorias abaixo são históricas, não contagens cumulativas.

## Motor parcial v36 — 52 áreas e guia em três páginas

Expansão para **Victory Road 1F, 2F, 3F e Power Plant**, preservando as 48 áreas anteriores. À noite, **20:00–05:59**:

| Área | Novos encontros noturnos (níveis preservados) |
|---|---|
| Victory Road — 1F | Golbat (40) / Noivern (43) |
| Victory Road — 2F | Sableye (42) / Mawile (45) |
| Victory Road — 3F | Zweilous (43) / Absol (46) |
| Power Plant | Joltik (25) / Tynamo (25) |

Dois slots de **10% nominal por área**, antes dos filtros. **Iron Crown, Guzzlord, Roaring Moon, Xurkitree e Lucario preservados**; no 3F usam-se slots 3/4 para manter Lucario no 2. Mantidas também as exceções da Mansion e da Rota 13. Outros slots, níveis, frequências e tabelas diurnas intactos; sem mudar iluminação nativa, acessos, pedras/interruptores, eventos fixos ou história.

O guia agora tem **três páginas (8/8/4 opções)**. Na placa da Rota 1: **Mais areas / ilhas → Mais areas → Liga / Usina**. **Mansao Pokemon** fica nessa terceira página, com os mesmos textos e encontros. B/Voltar retorna à página anterior; utilidades retornam à origem; Sair funciona nas três. O [CSV completo](docs/guia_encontros_horario_v36.csv) tem **1.248 linhas**.

**102/102 métodos aprovados**, sem falhas, erros ou skips: 10.400 casos determinísticos, 104 consultas ao guia, caminhada nas quatro novas áreas após chegada sintética/save na ROM exata, iluminação/relógio, flash v35↔v36, seis regressões da auditoria da v32 e dois testes adicionais da terceira página. Onze capturas conferidas visualmente. Não certifica campanha completa, insígnias, Strength/puzzles, eventos fixos, acesso normal à Liga/Usina ou saves pessoais.

Relógio, MUNDO, Opções/SELECT e formato de save intactos. Builder `scripts/motor_v36.py`, base v35 exata, oito intervalos e saída exclusiva; payload/ROM reconstruídos de forma idêntica. SHA-256: `88afd471b59e9b27dcd1e42e7b5cab6068975098b9a58361a3dd251e3b075ad0`.

Veja [MOTOR_V36.md](docs/MOTOR_V36.md), [resultados](docs/validacao_v36_resultados.json) e [log](docs/validacao_v36.log). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local, sem publicação no Drive, commit ou push.** As versões e auditorias abaixo são históricas, não contagens cumulativas.

## Motor parcial v35 — 48 áreas e Pokémon Mansion

Expansão para os **quatro andares da Pokémon Mansion**, preservando as 44 áreas anteriores. À noite, **20:00–05:59**:

| Andar | Novos encontros noturnos (níveis preservados) |
|---|---|
| 1F | Shuppet (36) / Litwick (30) |
| 2F | Gastly (30) / Misdreavus (36) |
| 3F | Haunter (36) / Banette (30) |
| B1F | Yamask (30) / Duskull (30) |

Dois slots de **10% nominal por andar**, antes dos filtros. **Terapagos, Metagross, Dragonite e Ditto preservados**: slots substituídos são 3/4 no 1F e 3F, 2/3 no 2F e 2/4 no B1F. Outros slots, níveis, frequências e tabelas diurnas mantidos. Portas, estátuas, diários, Secret Key, treinadores e acessos não mudam. A iluminação interna continua nativa, sem escurecimento noturno extra.

Placa da Rota 1: **Mais areas / ilhas → Mansao Pokemon → andar**. [CSV completo](docs/guia_encontros_horario_v35.csv) com **1.152 linhas**. Ambas as páginas do guia têm oito opções; nenhuma nona opção é criada.

**100/100 métodos aprovados**, sem falhas, erros ou skips: 9.600 casos determinísticos, 96 consultas ao guia, caminhada nos quatro andares após chegada sintética/save na ROM exata, iluminação/relógio, flash v34↔v35, seis regressões da auditoria da v32 e teste novo das exceções de slots. Nove capturas conferidas visualmente. Não certifica campanha completa, puzzles/Secret Key, acesso normal à mansão ou saves pessoais.

Relógio, MUNDO, Opções/SELECT e formato de save intactos. Builder `scripts/motor_v35.py`, base v34 exata, oito intervalos e saída exclusiva; payload/ROM reconstruídos de forma idêntica. SHA-256: `049ed92bfc9c6b1a7c96b8123bbe3066f84af33bdfbb8e216f56cb64cbdca8c9`.

Veja [MOTOR_V35.md](docs/MOTOR_V35.md), [resultados](docs/validacao_v35_resultados.json) e [log](docs/validacao_v35.log). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local, sem publicação no Drive, commit ou push.** As versões e auditorias abaixo são históricas, não contagens cumulativas.

## Motor parcial v34 — 44 áreas e Icefall Cave

Expansão para os **quatro mapas de Icefall Cave, na Ilha 4**, preservando as 40 áreas anteriores. À noite, **20:00–05:59**:

| Área | Novos encontros noturnos (níveis preservados) |
|---|---|
| Entrada | Snorunt (45) / Cryogonal (47) |
| 1F | Sneasel (45) / Froslass (27) |
| B1F | Bergmite (45) / Glalie (27) |
| Fundos | Jynx (45) / Frosmoth (47) |

Dois slots de **10% nominal por área**, antes dos filtros. Outros slots, níveis variados, frequência 7 e tabelas diurnas mantidos. **Sandy Shocks preservado**, assim como os scripts de Lorelei/Rocket, gelo, cachoeira e requisitos de acesso. As cavernas **mantêm a iluminação nativa**, sem escurecimento noturno extra.

Na placa da Rota 1: **Mais areas / ilhas → Icefall - Ilha 4 → área**. O [CSV completo](docs/guia_encontros_horario_v34.csv) tem **1.056 linhas**. Guia com oito opções na primeira página e sete na segunda.

**99/99 métodos aprovados**, sem falhas, erros ou skips: 8.800 casos determinísticos, 88 consultas ao guia, caminhada nos quatro mapas de Icefall após chegada sintética/save carregado na ROM exata, iluminação/relógio, flash v33↔v34 e seis regressões da auditoria da v32. Nove capturas conferidas visualmente. Não certifica campanha completa, gelo/cachoeira, Lorelei/Rocket, acesso normal à Ilha 4 ou saves pessoais.

Relógio, MUNDO, Opções/SELECT e formato de save intactos. Builder `scripts/motor_v34.py`, base v33 exata, oito intervalos e saída exclusiva; payload/ROM reconstruídos de forma idêntica. SHA-256: `419212559dfb92054d2db024e8d0ef202ae601d3887f20a6c0d8f965cfb61655`.

Veja [MOTOR_V34.md](docs/MOTOR_V34.md), [resultados](docs/validacao_v34_resultados.json) e [log](docs/validacao_v34.log). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local, sem publicação no Drive, commit ou push.** As versões e auditorias abaixo são históricas, não contagens cumulativas.

## Motor parcial v33 — 40 áreas e grutas de Kanto

Expansão para **Mt. Moon 1F, B1F, B2F e Diglett's Cave B1F**, preservando as 36 áreas anteriores. À noite, **20:00–05:59**:

| Área | Novos encontros noturnos (níveis preservados) |
|---|---|
| Mt. Moon — 1F | Cleffa (7) / Noibat (9) |
| Mt. Moon — B1F | Woobat (5) / Morelull (6) |
| Mt. Moon — B2F | Mawile (9) / Lunatone (10) |
| Diglett's Cave — B1F | Sandshrew (17) / Drilbur (15) |

Dois slots de **10% nominal por área**, antes dos filtros. Outros slots, níveis, frequência e tabelas diurnas mantidos. **Diglett/Dugtrio, Rotom, Clefairy, Poltchageist, Dreepy e Spiritomb preservados**. Fósseis, treinadores, acessos e demais scripts não mudam.

As cavernas usam o horário do mundo para os encontros, mas **mantêm a iluminação nativa**, sem escurecimento noturno extra. Na placa da Rota 1: **Mais areas / ilhas → Grutas de Kanto → área**. O [CSV completo](docs/guia_encontros_horario_v33.csv) tem **960 linhas**. Guia com oito opções na primeira página e seis na segunda.

**99/99 métodos aprovados**, sem falhas, erros ou skips: 8.000 casos determinísticos, 80 consultas ao guia, caminhada nas quatro cavernas após chegada sintética/save carregado na ROM exata, iluminação/relógio, flash v32↔v33 e as seis regressões da auditoria anterior. Nove capturas conferidas visualmente. Não certifica campanha completa, eventos dos fósseis, travessia integral das grutas ou saves pessoais.

Relógio, MUNDO, Opções/SELECT e formato de save intactos. Builder `scripts/motor_v33.py`, base v32 exata, oito intervalos e saída exclusiva; payload/ROM reconstruídos de forma idêntica. SHA-256: `dc3d076a9645b22e49f366c477929e50ee06e1df836c19b4f418fe7b2e44ddaf`.

Veja [MOTOR_V33.md](docs/MOTOR_V33.md), [resultados](docs/validacao_v33_resultados.json) e [log](docs/validacao_v33.log). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local, sem publicação no Drive, commit ou push.** As versões e auditorias abaixo são históricas, não contagens cumulativas.

## Auditoria ampliada da v32 — sem nova ROM

**99/99 métodos aprovados em 645.203 s**, sem falhas, erros ou skips. São seis testes novos e os 93 originais reexecutados, não uma soma de rodadas históricas.

- **12 capturas e recargas de save** nas quatro áreas novas: controles diurnos, pares noturnos, HUD oculto e relógio pós-cap. Identidade, níveis, IVs, HP, time e consumo da bola preservados.
- **Quatro trocas de período ao vivo** em Berry Forest, com HUD visível/oculto, seguidas de encontros naturais.
- **Duas travessias de ida e volta** pela conexão nativa entre entrada e Sevault Canyon, de dia/noite, com save e reinicialização.

As ações auditadas ocorrem na ROM exata após carregar um save sintético; apenas a chegada inicial é abreviada numa cópia descartável. Não certifica acesso normal às ilhas, Lostelle, puzzles ou campanha completa. Master Ball nos novos ensaios verifica o caminho de captura, não catch rate; Poké Ball comum continua no conjunto original.

**ROM v32 e distribuição inalteradas; não há v33.** SHA-256: `7c095be4d52eeb728600eafbe2f57b60a4a402c11fe9a84cc19a8bbf61aa6d13`.

Veja [auditoria e limites](docs/AUDITORIA_V32.md), [resultados](docs/auditoria_v32_resultados.json) e [log](docs/auditoria_v32.log). Runner: `scripts/validar_motor_v32_auditoria.py`. Sem saves pessoais, publicação no Drive, commit ou push.

## Motor parcial v32 — 36 áreas, bosques e Sevault

Expansão para mais quatro áreas de grama, preservando as 32 anteriores. À noite, **20:00–05:59**:

| Área | Novos encontros noturnos (níveis preservados) |
|---|---|
| Berry Forest — Ilha 3 | Phantump (32) / Shiinotic (30) |
| Pattern Bush — Ilha 6 | Venonat (14) / Ariados (6) |
| Entrada de Sevault Canyon — Ilha 7 | Houndour (10) / Murkrow (48) |
| Sevault Canyon — Ilha 7 | Houndoom (46) / Honchkrow (50) |

Dois slots de **10% nominal por área**, antes dos filtros. Demais slots, níveis variados, frequência e tabelas diurnas mantidos. **Celesteela e Buzzwole preservados**, assim como Drowzee/Hypno em Berry Forest, scripts de história, água/pesca/Rock Smash e requisitos de acesso às ilhas. Não foi validado o percurso completo de Lostelle ou dos puzzles.

Na placa da Rota 1: **Mais areas / ilhas → Bosques / Ilha 7 → área**. Mesmo guia em duas páginas: oito opções na primeira e cinco na segunda, B/Voltar para a página de origem e Sair disponível em ambas. O [CSV completo](docs/guia_encontros_horario_v32.csv) tem **864 linhas**.

MUNDO, Opções/SELECT, preferência persistente e relógio pós-cap intactos. Sem novo campo de save, RTC ou avanço offline.

**93/93 métodos aprovados**, sem falhas, erros ou skips: 7.200 casos determinísticos, 72 consultas ao guia, encontros nas novas áreas após warps somente de teste, flash v31↔v32 e regressões de relógio/HUD, combate, captura, estojo e EV. Nove capturas conferidas visualmente. Não equivale à campanha completa, progressão até as ilhas, hardware real ou certificação de saves pessoais.

Builder `scripts/motor_v32.py`, base v31 exata, oito intervalos e saída exclusiva. Payload/ROM reconstruídos de forma idêntica. SHA-256: `7c095be4d52eeb728600eafbe2f57b60a4a402c11fe9a84cc19a8bbf61aa6d13`.

Veja [MOTOR_V32.md](docs/MOTOR_V32.md), [resultados](docs/validacao_v32_resultados.json) e [log](docs/validacao_v32.log). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local, sem publicação no Drive, commit ou push.** As versões abaixo são históricas, não contagens cumulativas.

## Motor parcial v31 — 32 áreas e guia em duas páginas

Expansão noturna para mais quatro áreas de grama nas **ilhas 5 e 6**, preservando as 28 anteriores. À noite, **20:00–05:59**:

| Área | Novos encontros noturnos (níveis preservados) |
|---|---|
| Five Island Meadow | Liepard (48) / Purrloin (10) |
| Memorial Pillar | Gastly (8) / Litwick (14) |
| Water Path | Noctowl (44) / Misdreavus (48) |
| Ruin Valley | Golett (18) / Duskull (15) |

Dois slots de **10% nominal por área**, antes dos filtros. Demais slots, níveis variados, frequência e tabelas diurnas mantidos. **Slither Wing, Scream Tail e Brute Bonnet preservados**, assim como eventos, água/pesca/Rock Smash e requisitos de acesso às ilhas.

Na placa da Rota 1: **Mais areas / ilhas → Ilhas 5,6 → área**. O guia tem duas páginas, sem ultrapassar oito opções por tela. B/Voltar retorna à página de origem; B na primeira página sai. Horarios / sair está disponível nas duas. O [CSV completo](docs/guia_encontros_horario_v31.csv) tem **768 linhas**.

MUNDO, Opções/SELECT, preferência persistente e relógio pós-cap intactos. Sem novo campo de save, RTC ou avanço offline.

**93/93 métodos aprovados**, sem falhas, erros ou skips: 6.400 casos determinísticos, 64 consultas ao guia, paginação, encontros nas novas áreas após warps somente de teste, flash v30↔v31 e regressões de relógio/HUD, combate, captura, estojo e EV. Oito capturas conferidas visualmente. Não equivale à campanha completa, progressão até as ilhas, hardware real ou certificação de saves pessoais.

Builder `scripts/motor_v31.py`, base v30 exata, oito intervalos e saída exclusiva. Payload/ROM reconstruídos de forma idêntica. SHA-256: `fa25df630c902c7b7e155c9d8fca86f4a4674a76123b3541b68ab8eabcc84096`.

Veja [MOTOR_V31.md](docs/MOTOR_V31.md), [resultados](docs/validacao_v31_resultados.json) e [log](docs/validacao_v31.log). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local, sem publicação no Drive, commit ou push.** As versões abaixo são históricas, não contagens cumulativas.

## Motor parcial v30 — 28 áreas por horário, incluindo as ilhas

Novas áreas de grama nas ilhas. À noite, 20:00–05:59:

| Área | Encontros noturnos |
|---|---|
| Kindle Road — Ilha 1 | Lampent (36) / Numel (31) |
| Treasure Beach — Ilha 1 | Sandygast (31) / Krabby (35) |
| Cape Brink — Ilha 2 | Natu (32) / Banette (36) |
| Bond Bridge — Ilha 3 | Duskull (29) / Greavard (36) |

Dois slots de **10% nominal por área**, antes dos filtros; outros slots, níveis, frequência e dia preservados. As 24 áreas anteriores não mudam. **Berry Forest, água, pesca, Rock Smash, eventos e acesso às ilhas não foram alterados.**

Na placa da Rota 1, escolha **Ilhas 1,2,3 → área**. Para manter oito opções no menu principal, **Horarios / sair** agora abre um submenu com regras, Voltar e Sair. **B no menu principal continua encerrando imediatamente.** As consultas anteriores e o [CSV completo de 672 linhas](docs/guia_encontros_horario_v30.csv) continuam disponíveis.

MUNDO, Opções/SELECT, preferência e relógio pós-cap intactos; sem novo campo no save, RTC ou avanço offline.

**91 métodos aprovados, sem falhas, erros ou skips**, incluindo 5.600 casos determinísticos, encontros nas quatro novas áreas após warps somente de teste, 56 consultas ao guia, flash v29↔v30 e regressões de relógio/HUD, combate, captura, estojo e EV. Não equivale à campanha completa, progressão até as ilhas, hardware real ou certificação de saves pessoais.

Builder `scripts/motor_v30.py`, base v29 exata, oito intervalos e saída exclusiva. Payload/ROM reconstruídos de forma idêntica. SHA-256: `58e3a53b0bed5729e02d322569bcfe4bd11c7f0161f74ef1d1347050753dba21`.

Veja [MOTOR_V30.md](docs/MOTOR_V30.md), [resultados](docs/validacao_v30_resultados.json) e [log](docs/validacao_v30.log). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local, sem publicação no Drive, commit ou push.** As versões abaixo são históricas, não contagens cumulativas.

## Motor parcial v29 — 24 áreas por horário e guia atualizado

Novas **Rotas 17, 18, 21 Norte e 23**. À noite, 20:00–05:59:

| Área | Novos encontros noturnos |
|---|---|
| Rota 17 | Raticate (22) / Mightyena (26) |
| Rota 18 | Noctowl (22) / Liepard (26) |
| Rota 21 Norte | Shiinotic (24) / Phantump (21) |
| Rota 23 | Honchkrow (34) / Houndoom (34) |

Dois slots nominais de **10% por área**, antes dos filtros; outros slots, níveis, frequência e tabelas diurnas preservados. **Raging Bolt e Umbreon da Rota 23 mantidos**, assim como Naganadel, Iron Valiant, Snorlax, Poipole e eventos. Sem alterar bicicleta, Surf, insígnias ou acesso à Liga. **Rota 21 Sul, água/pesca e Rotas 19/20 não foram expandidas.**

As 20 áreas anteriores ficam intactas. A placa da Rota 1 mantém **grupo → área**, A/B e Voltar/Sair, com um novo grupo para as quatro áreas. O [CSV completo](docs/guia_encontros_horario_v29.csv) tem 576 linhas. MUNDO, Opções/SELECT, preferência persistente e relógio pós-cap permanecem os da v28; sem novo campo no save, RTC ou avanço offline.

**90 métodos aprovados, sem falhas, erros ou skips:** 4.800 casos determinísticos, encontros nas quatro novas áreas após warps somente de teste, 48 consultas ao guia, flash v28↔v29 e regressões de relógio, HUD, combate, captura, estojo e EV. Não é certificação da campanha inteira, requisitos de acesso, hardware real, saves pessoais ou fidelidade integral a Scarlet/Violet.

Builder `scripts/motor_v29.py`, base v28 exata, oito intervalos, saída exclusiva; payload e ROM reconstruídos de forma idêntica. SHA-256: `c8e9fd9e4269f31c462d3273c08b11996f8e229a5b20a2306e99f516bf5d2528`.

Veja [MOTOR_V29.md](docs/MOTOR_V29.md), [resultados](docs/validacao_v29_resultados.json) e [log](docs/validacao_v29.log). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local, sem publicação no Drive, commit ou push.** As versões abaixo são históricas, não contagens cumulativas.

## Motor parcial v28 — guia consultável por grupo e área

A placa da **Rota 1** agora oferece **grupo → área**, com uma página para cada par noturno. Consulte também **Horarios / regras**. **A** escolhe; **A/B** fecha a consulta; **B/Voltar** retorna ao grupo; **B/Sair** no menu principal encerra. Direções originais preservadas. O período indicado na introdução é consultado ao entrar e após ler as regras; as páginas de espécies são sempre identificadas como NOITE.

**Sem expandir ou alterar os encontros:** mesmas 20 áreas, espécies protegidas, chances, níveis e eventos da v27. Relógio, MUNDO, Opções/SELECT, preferência persistente, estojo e mecânicas intactos. Sem novo campo no save, RTC ou avanço offline.

**87 métodos aprovados, sem falhas, erros ou skips**, incluindo as 20 consultas nos dois períodos, retornos por A/B, menus nativos anteriores, 4.000 casos determinísticos de encontros e regressões de relógio, HUD, flash v27↔v28, combate, captura, TMs/HMs e EV. Não equivale à campanha completa, hardware real ou certificação de saves pessoais.

Builder `scripts/motor_v28.py`, base v27 exata, saída exclusiva e cinco intervalos. Nenhum código ARM/Thumb novo; menus e scripts nativos. SHA-256: `e7d11016a5c17f226ce05bc89142d52daeeee46b90c87b4b0fba29085e50cd16`.

Veja [MOTOR_V28.md](docs/MOTOR_V28.md), [resultados](docs/validacao_v28_resultados.json) e [guia CSV completo](docs/guia_encontros_horario_v27.csv). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local, sem publicação no Drive, commit ou push.** As seções abaixo são históricas, com contagens não cumulativas.

## Motor parcial v27 — encontros por horário em 20 áreas

Adicionadas **Rotas 13, 14, 15 e 16**, preservando as 16 áreas anteriores. À noite (20:00–05:59):

| Nova área | Espécies noturnas e níveis |
|---|---|
| Rota 13 | Drifloon (27) / Murkrow (25) |
| Rota 14 | Misdreavus (22) / Sneasel (23) |
| Rota 15 | Shuppet (22) / Duskull (27) |
| Rota 16 | Meowth (18) / Houndour (20) |

Cada nova espécie ocupa um slot nominal de **10%**, antes dos filtros. Na Rota 13 usamos **slots 3 e 4**, preservando Naganadel no slot 2. Iron Valiant, Snorlax e Poipole mantidos. Os outros 80%, níveis, frequência, tabelas diurnas, água/pesca e eventos de história não mudam. Placa da Rota 1 e [guia completo](docs/guia_encontros_horario_v27.csv) atualizados para 20 áreas/480 linhas.

**MUNDO, START → Opções → SELECT, persistência e relógio pós-999:59:59 permanecem os da v26.** Ocultar o painel não pausa o relógio nem os encontros. Sem novo campo no save, RTC ou avanço offline.

**85 métodos aprovados, zero falhas, erros ou skips**, incluindo 4.000 casos determinísticos, caminhadas nas novas rotas após warps somente de teste, save v26↔v27, relógio, HUD, preferência, batalhas, estojo e EV. Não é certificação da campanha inteira, acesso às rotas, saves pessoais ou fidelidade completa a Scarlet/Violet.

Builder `scripts/motor_v27.py`, base v26 exata e seis intervalos; reconstrução independente idêntica. SHA-256: `f48ce3b2b4328637d47004722907ca9bfb5b6e523f1ed8a6b1bfbe93fd266673`.

Veja [MOTOR_V27.md](docs/MOTOR_V27.md), [resultados](docs/validacao_v27_resultados.json) e [log](docs/validacao_v27.log). Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. **Entrega local; sem publicação no Drive, commit ou push.** As seções abaixo são históricas, não contagens cumulativas.

## Motor parcial v26 — MUNDO e visibilidade configurável

O painel agora identifica **MUNDO** acima do HH:MM. Em **START → Opções → SELECT**, alterne a exibição entre **MUNDO SIM/NAO**; saia com B e **salve normalmente** para conservar a escolha. SELECT no campo continua com a função nativa do item registrado.

**Ocultar não pausa o relógio**, os encontros ou o ciclo visual. Mantidos os 24 minutos jogados/dia, a continuidade após 999:59:59, as 16 áreas, TMs/estojo, EV e mecânicas anteriores. Sem RTC ou avanço offline.

A preferência ocupa oito bytes finais da reserva T9X1 já existente, sem aumentar a flash nem mudar CK24. Registros desconhecidos/corrompidos são preservados; nesse caso o controle pode mostrar BLOQ. Saves anteriores começam com o painel visível. Use uma cópia do save normal e o menu **Continuar**, não savestates de outra versão.

**80 métodos aprovados na rodada final, sem falhas, erros ou skips**, incluindo os 1.440 horários no oráculo de pixels, Opções/SELECT, dados corrompidos, save/downgrade, relógio, encontros, batalhas, estojo e EV. Não é certificação de toda a campanha ou de saves pessoais.

Builder `scripts/motor_v26.py`, base v25 exata, saída exclusiva, cinco intervalos. SHA-256: `ffba283f8d01885f9a8a3d5300135adeae008e6434a7c5c80ec7f695c1445ba7`.

Veja [MOTOR_V26.md](docs/MOTOR_V26.md) e os [resultados](docs/validacao_v26_resultados.json). Entrega local, sem publicação no Drive, commit ou push. As versões abaixo são históricas e suas contagens não são cumulativas.

## Motor parcial v25 — HH:MM do mundo na tela

O **horário do mundo** aparece no canto superior direito do campo, em formato **HH:MM de 24 horas**. Não é o tempo total jogado: esse contador nativo continua em 999:59:59, enquanto o mundo e o painel continuam seus ciclos. Preservados o ritmo acelerado de 24 minutos jogados/dia, o save da v24, as **16 áreas**, as paletas, evoluções e demais mecânicas. Sem RTC ou avanço offline.

Painel de 32×16 pixels com arte original. Oculto nos fluxos validados de menus, diálogos, ajuda e batalhas; omite a exibição quando faltam recursos próprios ou o slot OAM está ocupado. Nenhum campo novo no save.

**69 métodos únicos aprovados na rodada final, sem falhas, erros ou skips**, com testes gráficos, recursos esgotados, viradas antes/depois do cap, saves sintéticos **v24→v25→v24→v25**, encontros, estojo, EV e batalhas. Não é validação da campanha inteira.

Builder `scripts/motor_v25.py`, **base v24 exata**, saída exclusiva e três intervalos. SHA-256 da ROM: `1ef4e7235a95d20b12c7f281284febbf5ff8f0b59a8886968e46c225aa43a01d`.

Veja [MOTOR_V25.md](docs/MOTOR_V25.md) e os [resultados](docs/validacao_v25_resultados.json). O [guia das 16 áreas](docs/guia_encontros_horario_v23.csv) continua inalterado. Faça backup do save normal e use **Continuar**, não savestates de outra versão. **Entrega local, sem publicação no Drive ou commit/push.** As versões abaixo são históricas; suas contagens não são cumulativas.

## Motor parcial v24 — relógio além do limite nativo

O **mundo continua seu ciclo acelerado depois de 999:59:59**; o indicador nativo de tempo jogado permanece nesse máximo. Mantidos os 24 minutos jogados/dia, as **16 áreas da v23**, as paletas e evoluções por período. Sem RTC, avanço offline, HUD ou expansão de encontros.

Registro persistente de **8 bytes** dentro da reserva existente do estojo, com identificador e CRC. Saves anteriores já saturados iniciam a continuação em 08:00 no primeiro tick elegível; tempo já perdido não pode ser recuperado. **Se o estojo nunca inicializou sua extensão, a ativação automática aguarda um campo externo normal**, protegendo mochilas temporárias do Pokedude/link. Dados desconhecidos/corrompidos são preservados, não reparados.

**60 métodos selecionados aprovados, sem skips**, incluindo dois ciclos completos consecutivos, saves sintéticos v23→v24 e roundtrip, downgrade limitado, proteção do Pokedude, 287 quantidades de TMs/HMs, 3.200 casos de encontros e regressões de UI/batalha/EV. Não é validação da campanha inteira.

Builder `scripts/motor_v24.py`, **base v23 exata**, saída nova e três intervalos. SHA-256: `5fe26a76ee13a85a8dbccecc61ce3f89ed7f44a49d221b8621acb4a0966e36d2`.

Veja [MOTOR_V24.md](docs/MOTOR_V24.md) e os [resultados](docs/validacao_v24_resultados.json). O [guia de 16 áreas](docs/guia_encontros_horario_v23.csv) permanece o da v23. Faça backup do save normal; não reutilize savestates entre versões. **V24 local; sem publicação no Drive ou commit/push.** As seções seguintes são históricas, não resultados cumulativos.

## Motor parcial v23 — encontros por horário em 16 áreas

**Novas Rotas 9, 10, 11 e 12**, preservando as 12 áreas da v22. Noite 20:00–05:59: dois slots nominais de 10% por área, antes de Repel/filtros. Outros 80%, níveis e frequência nativa mantidos. De dia (06:00–19:59), tabelas anteriores intactas.

| Nova área | Espécies noturnas e níveis |
|---|---|
| Rota 9 | Sableye (11) / Rockruff (15) |
| Rota 10 | Chingling (11) / Joltik (15) |
| Rota 11 | Rattata (12) / Scraggy (13) |
| Rota 12 | Noctowl (22) / Ariados (23) |

**Poipole da Rota 9 preservado:** slot original de 10%, nível 14, nos dois períodos. O builder rejeita substituir espécies protegidas na origem ou no destino. A placa da Rota 1 lista as 16 áreas; sem recompensas, novas flags ou alterações nos eventos de história, incluindo Snorlax. Distribuições de design, não tabelas oficiais nem garantia de dificuldade equivalente.

**47 métodos selecionados aprovados, sem skips:** 3.200 casos determinísticos, preservação das 12 áreas anteriores, encontros nas novas rotas após warps somente de teste, leitura da placa, relógio/evoluções/paletas, EV/IV, captura/save/fuga, migração de flash sintética v22→v23 e quatro regressões de batalha. Não equivale à auditoria de 68 métodos da v21 ou à campanha completa.

Builder `scripts/motor_v23.py`, **base v22 exata**, saída nova e seis intervalos. SHA-256: `e7de31338f37b22995734d2f855aef82d965c348a83609606f8f2f08d42ba361`.

Veja [MOTOR_V23.md](docs/MOTOR_V23.md), a [política de 32 slots](data/encontros_horario_v23.csv), o [guia de 384 linhas](docs/guia_encontros_horario_v23.csv) e os [resultados](docs/validacao_v23_resultados.json). Mantidos os 24 minutos jogados/dia, a ausência de HUD HH:MM e a saturação em 999:59:59. **V23 local; não enviada ao Drive.** As seções abaixo são históricas, não resultados cumulativos da v23.

## Motor parcial v22 — encontros por horário em 12 áreas

**Novas Rotas 5, 6, 7 e 8**, preservando as oito áreas da v21. Noite 20:00–05:59: dois slots de 10% por área; demais 80%, níveis e frequência nativa iguais. De dia (06:00–19:59), tabelas anteriores intactas. Chances nominais antes de Repel/filtros.

| Nova área | Espécies noturnas e níveis |
|---|---|
| Rota 5 | Skitty (13) / Munna (12) |
| Rota 6 | Poliwag (13) / Volbeat (12) |
| Rota 7 | Misdreavus (19) / Stunky (18) |
| Rota 8 | Illumise (16) / Dedenne (20) |

A placa da Rota 1 lista as 12 áreas, sem recompensas ou flags permanentes. Surf, pesca, Rock Smash, cavernas, eventos especiais e outros mapas ficam fora da expansão. Escolhas do projeto, não tabelas oficiais nem promessa de dificuldade equivalente.

**46 métodos selecionados aprovados, sem skips:** 2.400 casos determinísticos, preservação das oito áreas anteriores, encontros por movimentação nas quatro novas rotas após warps apenas de teste, leitura completa da placa, relógio/evoluções/paletas, EV/IV, captura/save/fuga, migração de flash sintética v21→v22 e quatro regressões pontuais de batalha. Não são os 68 métodos da auditoria v21 nem a campanha completa.

Builder `scripts/motor_v22.py`, **base v21 exata**, saída nova e seis intervalos. SHA-256: `0e9f9d901d6d411a02d992e5b9f483f5729880dd07d169c868d5d4862309f90f`.

Veja [MOTOR_V22.md](docs/MOTOR_V22.md), a [política de 24 slots](data/encontros_horario_v22.csv), o [guia de 288 linhas](docs/guia_encontros_horario_v22.csv) e os [resultados](docs/validacao_v22_resultados.json). Mantidos os 24 minutos jogados/dia, a ausência de HUD HH:MM e o limite em 999:59:59. **V22 local; não enviada ao Drive.** As seções abaixo descrevem versões/rodadas históricas, não resultados cumulativos da v22.

## Motor parcial v21 — encontros noturnos em oito áreas

**Validação ampliada (2026-11-05): 68 métodos distintos aprovados, sem skips**, incluindo 27 regressões de batalha e quatro fluxos de captura/persistência, fuga e transição inicial. Mesma ROM v21, sem novas mecânicas. Veja [VALIDACAO_V21.md](docs/VALIDACAO_V21.md) para evidências e limites; não é validação da campanha inteira.

**Acrescentadas Rotas 3, 4, 24 e 25**, mantendo o piloto das Rotas 1, 2, 22 e Floresta de Viridian. Dia 06:00–19:59 intacto; noite 20:00–05:59 com duas substituições de 10% por área. Os demais 80%, níveis e frequência nativa são preservados; chances nominais antes de Repel/filtros.

| Nova área | Espécies noturnas e níveis |
|---|---|
| Rota 3 | Zubat (7) / Cleffa (7) |
| Rota 4 | Woobat (6) / Noibat (10) |
| Rota 24 | Purrloin (11) / Drowzee (12) |
| Rota 25 | Shuppet (13) / Duskull (14) |

A placa da Rota 1 agora lista as oito áreas, preservando as direções e sem recompensas ou flags permanentes. Surf, pesca, Rock Smash, cavernas, especiais e outros mapas ficam fora desta expansão. Escolhas de design, não tabelas oficiais nem promessa de dificuldade equivalente.

**Rodada de implementação: 37 métodos selecionados aprovados, sem skips.** Inclui 1.600 casos determinísticos de geração, preservação do piloto v20, encontros por movimentação nas quatro novas rotas após warps somente de teste, placa real, horário/evoluções/save/paletas e EV/IV. Não é a suíte histórica completa.

Aplicador `scripts/motor_v21.py`, **base v20 exata**, saída nova, payload de **300 bytes**, seis intervalos e nenhuma reserva persistente nova. SHA-256: `cfbcebd0bf3ab0c1cbcb9872bc400f62d9c807fbd67dd99b4b89ffb16c92a10f`.

Veja [MOTOR_V21.md](docs/MOTOR_V21.md), a [política de 16 slots](data/encontros_horario_v21.csv) e o [guia de 192 linhas](docs/guia_encontros_horario_v21.csv). Herda 24 minutos jogados/dia, o limite de 999:59:59 e a ausência de HUD HH:MM da v19. **V21 local; não enviada ao Drive nesta etapa.** Resultados abaixo são históricos, não cumulativos.

## Motor parcial v20 — encontros noturnos e guia na Rota 1

**Piloto nas Rotas 1, 2 e 22 e na Floresta de Viridian.** De dia (06:00–19:59), tabelas anteriores intactas. À noite (20:00–05:59), dois slots de 10% mudam em cada área; níveis, frequência nativa e os demais 80% são preservados.

- Rota 1: Hoothoot e Nickit; Rota 2: Poochyena e Houndour.
- Floresta: Spinarak e Morelull; Rota 22: Murkrow e Greavard.
- A placa Pallet–Viridian da Rota 1 mantém as direções e acrescenta um guia que informa o período e as espécies noturnas. Sem recompensas ou flags de história novas.
- Surf, pesca, Rock Smash, cavernas, outros mapas e encontros especiais permanecem fora do recorte. Chances nominais, antes de Repel/filtros nativos.

**35 métodos selecionados aprovados, sem skips.** Inclui criação nativa para os 100 resultados do sorteio de slots nas quatro áreas e nos dois períodos, Repel, placa real e encontros reais na Rota 1, além das regressões de horário/evolução/save/paletas e EV/IV. Não é a suíte histórica completa.

Aplicador `scripts/motor_v20.py`, entrada **v19 exata**, saída nova, payload próprio de **300 bytes**, seis intervalos e nenhuma reserva persistente nova. SHA-256 da saída: `6f22c85769de8fc083b72edd491e185c2baee9ef0fc23f174c25f31d3200ee23`.

Veja [MOTOR_V20.md](docs/MOTOR_V20.md), a [política de oito slots](data/encontros_horario_v20.csv) e o [guia completo diurno/noturno](docs/guia_encontros_horario_v20.csv). Herda o relógio de 24 minutos/dia e o limite de 999:59:59 da v19; não adiciona HUD HH:MM. **V20 local, não enviada ao Drive nesta etapa.** Resultados abaixo são históricos, não cumulativos.

## Motor parcial v19 — horário acelerado e dia/noite

**24 minutos jogados = um dia; início lógico às 08:00.** Tempo preservado pelo contador salvo, sem RTC, sem progresso offline e sem alterar o formato do save. Saves antigos usam seu tempo acumulado. Campo, menus e batalhas contam.

- Iluminação do terreno externo: noite, amanhecer, dia e entardecer; interfaces, sprites, batalhas e interiores preservam suas paletas nativas.
- Eevee: Espeon de dia / Umbreon à noite, com amizade ≥220; Sylveon tem prioridade se conhecer golpe Fairy da tabela ativa. Budew e Riolu: amizade por nível somente de dia. Everstone preservada.
- Sem encontros/eventos por horário e sem mostrador HH:MM. **Limite herdado: contador satura em 999:59:59; o relógio então para em 07:59.** Outras simplificações de evolução da base não foram modernizadas.

Aplicador `scripts/motor_v19.py`, base **v18 exata**, saída nova, payload próprio de **776 bytes**, três intervalos e nenhuma nova reserva de RAM/save. SHA-256: `b7b8b5636e522e1e3502aa59d1f714d36d955a028d9b988b1fe3f97219fffad1`.

**28 métodos selecionados aprovados, sem skips:** 5 de build, 12 de horário/integração, 9 de EV/IV e 2 regressões centrais da v18 (seis cenários). Não é a suíte histórica completa. Evidências, reprodução e limitações em [MOTOR_V19.md](docs/MOTOR_V19.md). Evoluções reais diurna/noturna, save/reload sintético e paletas testados em mGBA 0.10.5; resultados finais discriminados no relatório. **V19 local, não enviada ao Drive nesta etapa.** As seções abaixo são históricas, não resultados cumulativos.

## Motor parcial v18 — pivô sem efeito e Parting Shot/Soundproof

**Corrigidos os dois caminhos demonstrados na v17:** Volt Switch contra Ground não troca nem aplica hazards; Parting Shot é bloqueado por Soundproof antes das quedas de atributos. Eerie Spell e os sons nativos da lista permanecem preservados.

**41 métodos distintos concluídos, sem skips:** 39 controles positivos/build e dois negativos exclusivamente na base v17. Inclui 36 cenários de correção/controle de pivôs, 32 de trocas/KO sob hazards, ciclo de vida, histórico/PP, Soundproof legado e EV/IV. Não são 41 testes de fidelidade integral.

Aplicador `scripts/motor_v18.py`: base v17 exata, saída nova, payload de **94 bytes**, tabela de **26 bytes**, quatro intervalos de escrita e nenhuma RAM adicional. SHA-256 da saída: `f9a96edec0f070578dfec3d134dcb6decd5b4a5f7c296fef2c8346d7b9f504b2`. Veja [MOTOR_V18.md](docs/MOTOR_V18.md) para hashes, reprodução, evidências e limites.

**Histórico Soundproof mantém a semântica nativa `FFFF`, não o zero de uma troca; não certifica lastMove moderno.** Próximo recorte sugerido: histórico/consumo de PP após bloqueio por habilidade e seus consumidores. Engine parcial; nenhum save pessoal utilizado. A entrega posterior da v18 no Drive foi confirmada; isso não publica automaticamente a v19. As seções abaixo preservam o histórico, sem somar seus resultados aos atuais.

## Auditoria v17 — divergências em pivôs bloqueados

**Confirmado:** Volt Switch troca contra Ground mesmo reconhecendo a imunidade; Parting Shot ignora Soundproof, reduz atributos e troca. A segunda lacuna já era declarada nas fontes v7 e foi reproduzida na v17. As trocas indevidas aplicam hazards ao reserva.

**23 métodos distintos concluídos, sem skips: 21 controles positivos e dois negativos que reproduzem os problemas.** Oito métodos novos / **36 cenários (30 positivos + seis negativos)**. Protect, absorção, Clear Body, mínimos parciais/totais, reservas inelegíveis, PP/histórico e continuidade do aliado conferidos no recorte. **OK nos testes negativos não significa conformidade moderna.**

**Naquela auditoria, os problemas ainda não estavam corrigidos e a ROM v17 permaneceu inalterada. A correção posterior foi entregue na v18 acima**, mantendo os controles de efeitos parciais e falta de reservas. Veja [AUDITORIA_V17_PIVOS_BLOQUEADOS.md](docs/AUDITORIA_V17_PIVOS_BLOQUEADOS.md). Engine parcial; Drive não atualizado. Resultados anteriores abaixo são históricos, não cumulativos.

## Auditoria v17 — trocas e pivôs com aliado ativo

**22/22 métodos distintos aprovados, sem skips**, incluindo quatro métodos novos / **32 cenários**. Trocas voluntárias nos dois bancos, U-turn, Volt Switch, Flip Turn e Parting Shot sob hazards combinados, com sobrevivência ou KO do entrante e segunda seleção. HP/atributos/histórico do aliado acompanhados por frame, PP e continuidade do turno conferidos; quatro controles incluem absorção, Web e veneno residual.

**ROM/payload/aplicador inalterados, sem v18; nenhum novo defeito de engine demonstrado neste recorte.** Uma camada de Spikes na matriz nova; nos pivôs, velocidade e ordem estão acopladas ao banco, não cobrem todas as combinações. Veja [AUDITORIA_V17_TROCAS_PIVOS_HAZARDS.md](docs/AUDITORIA_V17_TROCAS_PIVOS_HAZARDS.md) para a matriz, execução e limites.

O recorte então sugerido — pivôs impedidos/falhos e reservas inelegíveis — foi auditado acima e revelou divergências fora da matriz desta etapa anterior. Engine parcial; **Drive não atualizado**. Os números das auditorias anteriores abaixo são históricos e não foram somados aos desta etapa.

## Auditoria v17 — hazards combinados nas reposições do jogador

**23/23 métodos distintos aprovados, sem skips**, incluindo cinco métodos novos / **30 cenários**. Escolhas reais pela tela de equipe, três quantidades de camadas, ordem de dano/mensagens, KO durante a entrada, rejeição de candidatos inválidos, absorção de Toxic Spikes nos dois bancos e histórico/PP dos entrantes. O veneno residual é separado de uma reaplicação indevida de hazard.

Os hazards são colocados por golpes reais e levados ao jogador por Court Change; a fixture inicial controla quando a IA pode usar Rock Slide. Não é auditoria de colocação adversária direta nem da duração moderna de Disable. **ROM/payload/aplicador inalterados, sem v18; nenhum novo defeito de engine demonstrado neste recorte.** Veja [AUDITORIA_V17_HAZARDS_COMBINADOS_JOGADOR.md](docs/AUDITORIA_V17_HAZARDS_COMBINADOS_JOGADOR.md).

O recorte então recomendado — trocas voluntárias e pivôs com aliado ativo — foi auditado na seção acima. Engine parcial; **Drive não atualizado**. Os resultados de entrega da v17 abaixo são históricos, não somados aos desta auditoria.

## Motor parcial v17 — hazards na ordem de criação

A correção dirigida substitui a prioridade fixa Spikes→Stealth Rock por uma fila de criação por lado. Camadas adicionais preservam a posição; limpeza/recolocação e Court Change atualizam a fila. O entrante já desmaiado não recebe os hazards seguintes nem executa Intimidate no controle dirigido.

Aplicador `scripts/motor_v17.py`, **base v16 exata e saída nova**. Payload de **3.148 bytes**, nove intervalos de escrita e oito bytes efêmeros dentro da reserva v8, sem mudança no formato de save. SHA-256 da saída: `5db05cbb54add61a6c50e08d3e392ba610e87ca3ef462095de168de5d3e32957`. Veja [MOTOR_V17.md](docs/MOTOR_V17.md) para testes, implementação, hashes e limites.

**46/46 métodos distintos concluídos, sem skips**, incluindo um negativo na base v16. Os dez métodos positivos novos de batalha cobrem **33 subcasos**; mais dois subcasos reproduzem o defeito na base. Build, treino EV/IV e 21 regressões foram reexecutados. A validação separa a reprodução negativa na v16 das expectativas modernas na v17. Não é certificação integral de Scarlet/Violet, campanha, link/multi ou migração de saves pessoais. **Drive não atualizado.**

## Auditoria v16 — defeito na ordem de hazards combinados

**Defeito confirmado na v16, tratado pela v17 acima:** a v16 executa Spikes antes de Stealth Rock mesmo quando Stealth Rock foi colocado primeiro. A regra moderna de referência exige ordem de criação. O dano final pode coincidir; eventos intermediários de HP e mensagens expõem a diferença, inclusive no hazard que causa o KO.

**20 métodos distintos concluídos, sem skips:** 16 regressões reexecutadas e quatro novos. A matriz nova cobre três quantidades de camadas e reposições adversárias em duplas: **10 controles positivos e 10 reproduções negativas**, em quatro métodos. Um `ok` nos negativos confirma o defeito, **não conformidade moderna**. Relatório: [AUDITORIA_V16_HAZARDS_COMBINADOS_DUPLAS.md](docs/AUDITORIA_V16_HAZARDS_COMBINADOS_DUPLAS.md).

**Na etapa de auditoria abaixo, ROM/payload permaneceram inalterados, ainda sem v17 e sem atualização do Drive.** Próximo trabalho então recomendado: correção dirigida da ordem de criação e do ciclo de vida dos hazards, não simplesmente inverter sua prioridade fixa. As seções abaixo conservam os resultados e escopos das auditorias anteriores.

## Auditoria v16 — reservas insuficientes e fim da batalha em duplas

**21/21 verificações aprovadas, sem skips**, incluindo cinco métodos novos com **44 subcasos**. Uma reserva sobrevivente mantém a batalha com o outro banco ausente; KOs em cadeia pelos hazards levam a vitória/derrota, com EXP concluída, retorno ao campo e cura de HP/PP após derrota. Inclui controle de whiteout em dupla selvagem sintética, sem escolher fuga.

**ROM v16 inalterada, sem v17 e sem novo defeito de engine demonstrado nesse recorte.** Relatório: [AUDITORIA_V16_DUPLAS_RESERVAS_FIM.md](docs/AUDITORIA_V16_DUPLAS_RESERVAS_FIM.md). Corrigida uma suposição do observador sobre a ordem dos alvos de Rock Slide; matriz inteira reexecutada. Próximo recorte: hazards combinados e múltiplas camadas na reposição em duplas. Drive não atualizado.

## Auditoria v16 — KO e duas reposições em duplas

**23/23 verificações distintas aprovadas, sem skips**, incluindo quatro métodos novos com **52 subcasos**. KO adversário por hazard, duas reposições pela IA, dois desmaios do jogador por um golpe de área e duas escolhas pela UI: dano de entrada, EXP, PP, histórico, recusa de duplicata e continuidade da batalha conferidos.

**ROM v16 inalterada, sem v17 e sem novo defeito demonstrado nesse recorte.** Relatório: [AUDITORIA_V16_DUPLAS_KO_REPOSICAO.md](docs/AUDITORIA_V16_DUPLAS_KO_REPOSICAO.md). A contagem desconta cinco repetições acidentais de descoberta do unittest (corrigida). Próximo recorte: reservas insuficientes, KO durante reposição e encerramento da batalha em duplas. Drive não atualizado.

## Auditoria v16 — hazards no jogador e seleção após KO

**26/26 verificações concluídas, sem skips**, incluindo cinco métodos novos com **52 subcasos** de Spikes/Stealth Rock no lado do jogador, em singles e duplas. A seleção após desmaio foi exercitada nos dois bancos do jogador: rejeita aliado ativo e reserva morto, aceita o substituto vivo e aplica o dano da nova entrada. PP, identidade, histórico, aliado e continuação da batalha são conferidos.

**ROM v16 inalterada, sem v17 e sem novo defeito demonstrado nesse recorte.** Relatório: [AUDITORIA_V16_HAZARDS_JOGADOR.md](docs/AUDITORIA_V16_HAZARDS_JOGADOR.md). A UI reordena a equipe temporariamente; o observador acompanha HP por PID. Próximo recorte: KO/reposição adversária em duplas e, depois, dois desmaios com seleção de dois substitutos. Drive não atualizado.

## Auditoria v16 — Spikes, Stealth Rock e KO na entrada

**41/41 verificações concluídas, sem skips**, incluindo sete testes novos com **27 subcasos**. Hazards são colocados por golpes reais: dano de entrada, KO, reposição, histórico/PP e EXP são conferidos. Também passaram dois desmaios em cadeia com vitória e retorno ao mapa, o KO pelo próprio golpe de phazing e a interrupção dos hazards quando Spikes já derruba o entrante.

**ROM v16 inalterada, sem v17 e sem novo defeito demonstrado nesse recorte.** Veja [AUDITORIA_V16_HAZARDS_KO.md](docs/AUDITORIA_V16_HAZARDS_KO.md). A matriz nova é singles, no lado adversário, com uma camada de Spikes e/ou Stealth Rock; não certifica todos os hazards nem a fórmula moderna de EXP. Próximos controles: entrada/KO no lado do jogador e em duplas. Drive não atualizado.

## Auditoria v16 — phazing em duplas e múltiplas reservas

**29/29 verificações concluídas, sem skips**, incluindo cinco testes novos com **60 subcasos**. Roar, Whirlwind, Dragon Tail e Circle Throw foram testados nos quatro bancos, com três reservas, uma única elegível e nenhuma elegível. A seleção exclui os dois membros ativos, desmaiados, ovos e vazios nos cenários auditados. PP, níveis, EXP e identidade permanecem coerentes; Eerie Spell respeita o histórico do entrante.

**ROM v16 mantida, sem v17 e sem novo defeito demonstrado nesta matriz.** Veja [AUDITORIA_V16_DUPLAS_PHAZING.md](docs/AUDITORIA_V16_DUPLAS_PHAZING.md) para as combinações, a escolha de alvos da IA e os limites. Próximo recorte: KO e hazards durante a troca/entrada. Link/multi e phazing simultâneo continuam pendentes. Drive não atualizado.

## Motor parcial `v16` — corrigida a falha de phazing por nível em treinador

Roar, Whirlwind, Dragon Tail e Circle Throw deixam de falhar **apenas pela chance legada de nível** em batalhas de treinador. A rotina nativa continua verificando a reserva e escolhendo o substituto. Níveis não ficam alterados; ausência de reserva, Suction Cups, Ingrain e os controles de Protect/imunidade testados são preservados. Oito cenários selvagens mantêm os resultados da v15.

**85/85 verificações concluídas, sem skips:** dez dirigidas (incluindo a reprodução do defeito na base v15), 61 regressões positivas e 14 de build/treino EV/IV. Payload de **300 bytes**, dois intervalos escritos, sem nova RAM persistente ou catálogo. Aplicador `scripts/motor_v16.py`, base v15 exata e saída nova. SHA-256 v16: `644b140dc4fd1f4fab4c7ed9304fb266865d3e81825140c01c2c275564dc0fcc`.

Veja [MOTOR_V16.md — correção, hashes, testes e limites](docs/MOTOR_V16.md). **Engine parcial:** matriz inicial de phazing em singles, posteriormente ampliada pela auditoria de duplas acima; demais interações continuam exigindo controles específicos. Drive não atualizado. As seções seguintes conservam o histórico das entregas anteriores.

## Auditoria anterior v15 — pivôs, trocas forçadas e diagnóstico do defeito

O histórico de Eerie Spell é limpo nas trocas efetivamente realizadas por U-turn, Volt Switch, Flip Turn, Parting Shot, Roar, Whirlwind, Dragon Tail e Circle Throw, nos cenários descritos. Entrada, nova ação e retorno preservam os PPs; Suction Cups bloqueia a troca sem apagar o histórico.

**Defeito confirmado na v15 e corrigido pela v16 acima:** Dragon Tail/Circle Throw podem causar dano, mas falhar em trocar um alvo de nível superior por causa da probabilidade legada nativa, inclusive no contexto de treinador. **25 verificações concluídas, sem skips, incluindo uma caracterização negativa em dois subcasos** — esse `ok` não significa conformidade moderna do phazing. Naquela auditoria não houve mudança na ROM. Veja [AUDITORIA_V15_PIVOS_PHAZING.md](docs/AUDITORIA_V15_PIVOS_PHAZING.md); a correção subsequente e seus controles estão no relatório v16 acima. Drive não atualizado.

## Motor parcial `v15` — duração de Disable e Encore

**Disable por quatro ações do alvo; Encore por três**, incluindo a ação ainda pendente no turno de aplicação. Corrige os contadores aleatórios legados, demonstrados separadamente na v14. Preserva verificações nativas, PP e travas: Disable interrompe Rollout/Ice Ball sem PP extra; a expiração de Encore não cancela a sequência própria desses golpes.

**76/76 verificações concluídas, sem skips:** nove testes dirigidos, 53 regressões positivas e 14 verificações de build/treino EV/IV. Payload de **304 bytes**, dois intervalos físicos escritos, sem RAM persistente ou catálogo novos. Aplicador `scripts/motor_v15.py`, entrada v14 exata, sempre saída nova. SHA-256 v15: `a6b454f7cbafad8c05e1b8aa2028087a596bbeff4f0184c826a92ebb7e554147`.

Veja [MOTOR_V15.md — evidências, hashes, reprodução e limites](docs/MOTOR_V15.md). **Correção de duração, não implementação integral de Encore/Disable modernos.** A auditoria posterior de pivôs/trocas forçadas está registrada acima; cobertura completa de duração em duplas continua pendente. Drive não atualizado. As seções abaixo conservam os registros históricos das etapas anteriores.

## Auditoria ampliada do v14 — duplas e interrupções naturais

**21/21 verificações concluídas, sem skips**, incluindo sete testes novos com 22 subcasos. Rollout/Ice Ball foram testados com usuários nos quatro bancos: o bloqueio por Protect não desconta PP da continuação nem isenta os outros participantes. Flinch por Stomp, autoataque por Confuse Ray e imobilidade por Thunder Wave encerram a sequência sem PP extra; o próximo impacto reinicia a potência em 30. **Nenhuma mudança na ROM; v14 mantido, sem v15.** Veja [AUDITORIA_V14_DUPLAS_INTERRUPCOES.md](docs/AUDITORIA_V14_DUPLAS_INTERRUPCOES.md) para a matriz exata, a correção da fixture e as limitações. Não se validaram probabilidades modernas de status nem todas as combinações de alvos/AI.

## Motor parcial `v14` — PP correto após Protect/Detect interromper Rollout/Ice Ball

**Corrigido o desconto extra de PP de uma continuação bloqueada.** Protect/Detect continuam encerrando a sequência; primeiro uso e reinício continuam gastando PP. Mantidas potência progressiva, Defense Curl, Pressure e sequências a PP zero. Testes incluem os dois lados em singles, miss por Sand Attack, sono por Hypnosis e Tackle posterior sem herdar isenção.

**61/61 verificações concluídas, sem skips**: build/controles dirigidos, regressões de batalha/estojo/save/histórico e treino EV/IV. Payload de **210 bytes**, dois intervalos escritos, sem RAM ou catálogo novos. Aplicador `scripts/motor_v14.py`, entrada v13 exata, sempre saída nova. SHA-256 v14: `2302ba1c88194fec190d0da062f91380ba062ee06e5a4a626902767412a9682c`.

Veja [MOTOR_V14.md — correção, hashes, testes, reprodução e limites](docs/MOTOR_V14.md). A engine continua parcial; os novos cenários Rollout/Protect não equivalem à validação de todas as interrupções ou de todos os alvos em duplas. **Drive não atualizado nesta etapa.**

## Auditoria anterior de Rollout/Ice Ball — registro do defeito no v13

A potência foi medida em cada impacto: **30→60→120→240→480**, ou **60→120→240→480→960** após Defense Curl, inclusive com PP zerado por Eerie Spell. Entretanto, **Protect interrompendo uma sequência ativa desconta um PP extra no v13**, reproduzido em Rollout e Ice Ball, com/sem Defense Curl. O reset de potência funciona; o desconto extra **permanece no v13 e foi corrigido no v14 acima**.

Foram executadas **27 verificações, incluindo uma caracterização desse defeito em quatro subcasos**, sem testes pulados. Esse `ok` não significa conformidade moderna no caso de Protect. Naquela etapa a **ROM v13 permaneceu inalterada**; a correção e seus controles foram entregues posteriormente no v14. Veja [AUDITORIA_ROLLOUT_POTENCIA.md — medições, diagnóstico, reprodução e critérios de correção](docs/AUDITORIA_ROLLOUT_POTENCIA.md).

## Auditoria anterior de histórico e PP — v13 mantido

**Trocas manuais, cancelamento e retorno** preservam os PPs corretamente e limpam o histórico apenas quando há troca. **Thrash, Rollout e SolarBeam continuam suas sequências já iniciadas após Eerie Spell zerar os PPs**, compatível com a referência moderna consultada; não foi adicionado o cancelamento legado de Spite. Oito testes novos e regressões reexecutadas: **50/50 nesta etapa, nenhum pulado**. Não há mudança na ROM nem motor v14. Veja [AUDITORIA_EERIE_HISTORICO_PP.md — evidências, reprodução e limites](docs/AUDITORIA_EERIE_HISTORICO_PP.md). Isso não valida toda a potência de Rollout, todas as travas ou todos os tipos de troca.

## Motor parcial `v13` — Eerie Spell atravessa Substitute e respeita Shield Dust

Corrige os dois desvios confirmados no v12: **Eerie Spell atinge o alvo através de Substitute sem consumir o boneco**, e **Shield Dust bloqueia somente o dreno de PP**. Preserva Soundproof, Endure, proteção dos PPs de Transform/Mimic e comportamento dos outros golpes. Testes dedicados incluem Substitute criado durante o turno e seleção de alvos em duplas. Payload de 454 bytes, sem RAM nova ou mudanças no catálogo.

**Auditoria KO/EXP concluída, sem nova ROM:** o teste criava um Pokémon nível 10 com apenas 1 EXP total. Corrigindo as fábricas para EXP 560, o ganho de experiência, a subida de nível e o retorno ao mapa passam em v12/v13. **54/54 verificações**, incluindo regressões v13 e EV/IV; reproduções negativas de EXP inválida ficam separadas. Veja [AUDITORIA_EXP_FIXTURES.md — causa, controles e reprodução](docs/AUDITORIA_EXP_FIXTURES.md).

SHA-256 v13 permanece `71756c820ebb71c0c64735b0e8f36cf420da29ac419f8ee09a39109d9cb4951c`, gerado em arquivo novo por `scripts/motor_v13.py`; **não há v14** nesta auditoria. Veja também [MOTOR_V13.md — correções, hashes e registro histórico](docs/MOTOR_V13.md). A engine continua parcial; 15.008 aprendizados e 708/729 omissões restauradas, sem novas inclusões.

## Motor parcial `v12` — Eerie Spell e Soundproof

Corrige o bloqueio de **Eerie Spell (720) por Soundproof**, estendendo somente a lista nativa: um literal de 4 bytes e uma tabela de 24 bytes, sem código executável ou RAM novos. **34 verificações aprovadas**, incluindo **duas caracterizações de defeitos ainda abertos**: Substitute intercepta o golpe e Shield Dust permite o dreno de PP. O teste histórico de Substitute do v11 foi reforçado para exigir término do turno; o resultado antigo não provava conformidade moderna.

Saída SHA-256 `fb28ad767a11add187d0fa69dec0164b3de73a9887a0c5834c5feccc675725c1`, gerada por `scripts/motor_v12.py` sobre v11, em arquivo novo. Catálogo inalterado: 15.008 linhas, 708/729 omissões restauradas. Veja [MOTOR_V12.md — correção, defeitos abertos, reprodução e testes](docs/MOTOR_V12.md). Continua parcial; esta correção **não** moderniza todos os golpes sonoros.

## Motor parcial `v11` — correção de Eerie Spell

Corrige a redução de PP de **Eerie Spell (720)**: agora consulta o último golpe usado pelo alvo, sem drenar indevidamente o primeiro slot disponível. Protege os PPs originais durante Transform/Mimic e preserva todos os bytes fora de três pequenas regiões. **28/28 testes** nesta etapa (5 estruturais, 8 dirigidos, 6 regressões de batalha/estojo/save e 9 de treino EV/IV). Mighty Cleave já atravessava Protect no v10; a hipótese de defeito foi descartada por teste.

Saída SHA-256 `1a147ee909183cc2e3bbba0599a4d70f0b0185b01d3e4941a1f27e6c4a9eee5b`, gerada por `scripts/motor_v11.py` sobre v10, sempre em arquivo novo. **Não habilita novos aprendizados**: permanecem 15.008 linhas, 708/729 omissões restauradas e quatro golpes adiados (21 linhas). Veja [MOTOR_V11.md — evidências, reprodução e limites](docs/MOTOR_V11.md). Não é uma engine SV completa; ROMs e saves continuam fora do Git.

## Motor parcial `v10` (Motor de Berries, +3 aprendizados → 15.008 = 708/729 [97,1%], 200 golpes consolidados e correção de `acc=0`, preservando 229/229 TMs SV)

Uma nova etapa determinística (`scripts/motor_v10.py`, sobre `motor_v9.gba`, saída SHA-256 `a533d1812812e2348bbe62a95a8c3817dd9d8372a89ff283f0e747c6c7ddeb09`) ocupa o último slot livre `255` de `gBattleScriptsForMoveEffects` em conjunto com `CMD_TABLE_V10` (`0x00, 0x01, 0x04, 0x05, 0x06, 0x0C, 0x88, 0xDD`) para consolidar **200 golpes** (`162` atualizações na tabela de golpes + `38` golpes `eff=0` enriquecidos nos hooks de cálculo): motor unificado de consumo de Berries `133..175` (`Stuff Cheeks`, `Teatime`, `Bug Bite / TM182`, `Pluck`, `Incinerate` e `Belch` rastreado por slot da equipe), dreno `75%` (`Draining Kiss / TM037`, `Oblivion Wing`) e `Matcha Gotcha`, `Knock Off / TM181` `1.5x` com item, multi-hit especializados (`Scale Shot / TM200`, `Population Bomb`, `Surging Strikes`, `Triple Dive`, `Double Iron Bash`), críticos garantidos (`Flower Trick`, `Wicked Blow`, `Surging Strikes`, `Storm Throw`, `Frost Breath`) e **correção do defeito Gen 3 de `acc == 0` em 11 golpes infalíveis Gen 4–9** (incluindo `TM032 Disarming Voice` e `TM053 Smart Strike`), aterramento sem colaterais de `Ingrain` (`Smack Down`, `Thousand Arrows`), limpeza de terrenos (`Ice Spinner`, `Steel Roller`), tipos/categorias adaptativos e quebra-telas (`Raging Bull`, `Freeze-Dry`, `Flying Press`, `Photon Geyser`, `Secret Sword`, `Tera Blast`, `Pollen Puff` em aliado), prioridade/resíduos/travas (`Sucker Punch`, `Thunderclap`, `Grassy Glide`, `Spectral Thief`, `Salt Cure`, `Syrup Bomb`, `Throat Chop`, `Gigaton Hammer`, `Blood Moon`, `Dragon Tail`, `Circle Throw`) e potências dinâmicas / peso (`Rage Fist`, `Last Respects`, `Bolt Beak`, `Fishious Rend`, `Collision Course`, `Electro Drift`, `Autotomize` + `Heavy Slam`/`Heat Crash`/`Low Kick`). Restaura mais **+3 aprendizados por nível** (`15.005` → **15.008** linhas em `data/learnsets_motor_v10.csv`, **708 / 729 = 97,1%**), preservando byte a byte as **229/229 TMs de Scarlet/Violet**, as 8 HMs infinitas, o `estojo_v2` e o `treino_ev`. **Continua parcial quanto ao motor geral de SV:** exatamente **4 golpes (`21` entradas = `2,9%`)** dependentes de habilidades/UI ausentes na base Gen 3 (`Simple Beam`, `Ally Switch`, `Instruct`, `Revival Blessing`), além de itens/habilidades pós-Gen 3 e Terastalização, permanecem fora de escopo e documentados. Veja a [especificação técnica, hashes, limitações e testes de `motor_v10`](docs/MOTOR_V10.md) e o [catálogo atualizado de aprendizados por nível](data/learnsets_motor_v10.csv). ROMs e saves permanecem fora do Git.

## Motor parcial `v9` (+51 golpes não-TM de subida de nível e +378 aprendizados → 15.005; 705/729 = 96,7% restaurados, preservando 229/229 TMs SV)

Uma nova etapa determinística (`scripts/motor_v9.py`, sobre `motor_v8.gba`, saída SHA-256 `2936a08fc95f40c7788b6136f209ab5cab31aec062d615f2a458f45b123e0e6f`) ocupa **12 slots livres (`243..254`, mantendo `255` livre)** de `gBattleScriptsForMoveEffects` para implementar **51 golpes não-TM** em 6 famílias mecânicas — alteração de tipos, 3º tipo efêmero e eletrificação (`Soak`, `Magic Powder`, `Reflect Type`, `Trick-or-Treat`, `Forest's Curse`, `Electrify`), trocas/divisões/inversão de atributos e impulsos compostos (`Power Trick`, `Speed Swap`, `Power/Guard Split`, `Power/Guard/Heart Swap`, `Topsy-Turvy`, `Acupressure`, `Decorate`, `Spicy Extract`, `No Retreat`, `Clangorous Soul`, `Fillet Away`, `Take Heart`, `Venom Drench`, `Toxic Thread`, `Tar Shot`, `Rototiller`, `Flower Shield`, `Magnetic Flux`, `Gear Up`), regeneração/drenagem por Atk/sacrifício/pivot com `Substitute` e purificação (`Aqua Ring`, `Strength Sap`, `Healing Wish`, `Lunar Dance`, `Shed Tail`, `Psycho Shift`, `Purify`, `Jungle Healing`, `Lunar Blessing`, `Dark Void` restrito a Darkrai `#491`), manipulação de habilidades Gen 3 (`Gastro Acid`, `Worry Seed`, `Entrainment`, `Doodle`), cópia/ordem de turno/foco crítico/dano por HP e `Natural Gift` com consumo real de Berry (`Copycat`, `After You`, `Quash`, `Laser Focus`, `Final Gambit`, `Natural Gift`) e sala de itens/prisão (`Magic Room` com supressão segura em `GetHoldEffect`, `Octolock`, `Fairy Lock`) — restaurando **+378 aprendizados por nível** (`14.627` → **15.005** registros em `data/learnsets_motor_v9.csv`, alcançando **705 / 729 = 96,7%** das entradas originalmente omitidas) e preservando byte a byte as **229/229 TMs de Scarlet/Violet**, as 8 HMs infinitas, o `estojo_v2` e o `treino_ev`. **Continua parcial quanto ao motor geral de SV:** exatamente **6 golpes (`24` entradas = `3,3%`)** dependentes de habilidades/UI inexistentes na base Gen 3 (`Simple Beam`, `Ally Switch`, `Instruct`, `Stuff Cheeks`, `Teatime`, `Revival Blessing`) seguem retidos e documentados. Veja a [especificação técnica, hashes, limitações e testes de `motor_v9`](docs/MOTOR_V9.md) e o [catálogo atualizado de aprendizados por nível](data/learnsets_motor_v9.csv). ROMs e saves permanecem fora do Git.

## Motor parcial `v8` (229/229 TMs SV habilitadas — 100% do catálogo, Clima Snow, 4 Terrenos, Salas, Gravidade, Hazards e +245 aprendizados por nível)

Uma nova etapa determinística (`scripts/motor_v8.py`, sobre `motor_v7.gba`, saída SHA-256 `32fd47c87b581952f54f05656f590c5f7da55d5cc3d186d81951508899ec54f0`) habilita as **10 TMs finais de Scarlet/Violet** (`TM052 Snowscape`, `TM091 Toxic Spikes`, `TM113 Tailwind`, `TM116 Stealth Rock`, `TM136 Electric Terrain`, `TM137 Grassy Terrain`, `TM138 Psychic Terrain`, `TM139 Misty Terrain`, `TM161 Trick Room` e `TM178 Gravity`, completando **229/229 TMs SV disponíveis = 100% do catálogo** sem nenhuma TM pendente), integra os golpes e sinergias das mesmas famílias (`Wonder Room`, `Magnet Rise`, `Aurora Veil`, `Chilly Reception`, `Shore Up`, `Sticky Web`, `Stone Axe`, `Ceaseless Edge`, `Mortal Spin`, `Rapid Spin`, `Defog`, `Tidy Up`, `Court Change`, `Blizzard`, `Weather Ball`, `Brick Break`, `Psychic Fangs`, `Floral Healing`, `Expanding Force`, `Rising Voltage`, `Terrain Pulse`, `Psyblade`, `Grassy Glide`, `Steel Roller` e `Misty Explosion`) e restaura mais **245 aprendizados por nível** em 18 golpes (elevando `learnsets_motor_v8.csv` para **14.627** registros, preservando 100% dos anteriores). **Continua parcial quanto ao motor geral de SV:** itens e habilidades modernos inexistentes na base Gen 3 (`Heavy-Duty Boots`, `Terrain Extender`, `Light Clay`, `Surge` abilities etc.) não existem, `Expanding Force` mantém cursor de alvo único em duplas, e `402` registros de nível (`57` golpes não-TM) seguem documentados. Veja a [especificação técnica, hashes, limitações e testes de `motor_v8`](docs/MOTOR_V8.md) e o [catálogo completo de 229 TMs](data/tms_motor_v8.csv). ROMs e saves permanecem fora do Git.

## Motor parcial `v7` (219/229 TMs SV, trocas automáticas e +59 aprendizados por nível)

Uma nova etapa determinística (`scripts/motor_v7.py`, sobre `motor_v6.gba`, saída SHA-256 `6321d8e2900cc44dcaefb2dedfbaf5b0952b2796ca27a4cb9d8dc0875827de09`) habilita mais **9 TMs de Scarlet/Violet** (`TM195 Burning Jealousy`, `TM199 Lash Out`, `TM207 Temper Flare`, `TM213 Coaching`, `TM220 Meteor Beam`, `TM226 Dragon Cheer`, `TM227 Alluring Voice`, `TM228 Psychic Noise` e `TM229 Upper Hand`, elevando o total para **219/229 TMs SV**), implementa as **trocas automáticas pós-golpe** (`TM048 Volt Switch`, `TM060 U-turn`, `TM196 Flip Turn` e `Parting Shot`, sem herdar estágios/Substitute de `Baton Pass`), atualiza `Stomping Tantrum` (`TM179`) após falha anterior e restaura **59 aprendizados por nível** em 5 golpes (`Heal Pulse`, `Parting Shot`, `Geomancy`, `Floral Healing` e `Life Dew`, totalizando **14.382** registros). **Continua parcial:** 10 TMs SV de campo/clima/terreno/hazards (`TM052, TM091, TM113, TM116, TM136..139, TM161, TM178`) e 647 registros de nível (75 golpes) seguem adiados e documentados. Veja a [especificação técnica, hashes, limitações e testes de `motor_v7`](docs/MOTOR_V7.md) e o [catálogo atualizado de TMs](data/tms_motor_v7.csv). ROMs e saves permanecem fora do Git.

## Auditoria (`estojo_v2` / `motor_v5`) e Motor parcial `v6`

Uma nova etapa determinística (`scripts/motor_v6.py`, sobre a saída de `scripts/motor_ampliado.py` e `scripts/estojo_expandido.py`) corrige três defeitos reais identificados na auditoria — teto `796` de nomes de golpes em batalha (`797..812`), overflow de 1 byte em `gBattleTextBuff2` (`0x020202F0`) e ícones de itens `375..603` / seta `RETURN_TO_FIELD` (`604`) — e habilita mais **6 TMs de Scarlet/Violet** (`TM043 Fling`, `TM170 Steel Beam`, `TM198 Poltergeist`, `TM201 Misty Explosion`, `TM210 Supercell Slam` e `TM212 Triple Axel`, elevando o total para **210/229 TMs SV**) mais **23 aprendizados por nível** de `Fling`. **Continua parcial:** 19 TMs SV, as trocas automáticas (`U-turn`/`Volt Switch`/`Flip Turn`) e 706 registros de nível seguem pendentes. Veja [auditoria completa, hashes, testes e pendências](docs/AUDITORIA_E_MOTOR_V6.md) e o [catálogo atualizado de TMs](data/tms_motor_v6.csv). ROMs e saves permanecem fora do Git.

## Complemento expandido de TMs e golpes — parcial

Uma cópia de 32 MiB acrescenta 14 TMs à variante anterior, reintroduz 116 aprendizados por nível e adapta cálculos e efeitos selecionados. **Continua incompleta:** há 26 TMs e 729 registros de nível omitidos, e o estojo permanece com 58 espaços. Consulte [instruções, backups, limitações e testes](docs/COMPLEMENTO_GEN9.md), as [TMs](data/tms_gen9_complemento.csv) e as [omissões restantes](docs/golpes_pendentes_complemento.csv). O aplicador é `scripts/complemento_gen9.py`; ROMs e saves continuam fora do Git.

## Variante anterior: TMs modernas e golpes

Uma nova cópia **acrescenta 189 TMs de Scarlet/Violet sem substituir as antigas ou as HMs**, amplia algumas listas por nível e corrige efeitos e poderes selecionados. As novas TMs são reutilizáveis, compartilham os 58 espaços do estojo com as antigas e podem facilitar a campanha: a loja abre desde cedo. **A atualização de batalha não é completa**; há 40 TMs indisponíveis e outros golpes disponíveis ainda têm mecânicas legadas ou incompletas. Veja [local da loja, backups, diferenças e testes](docs/ATUALIZACOES_GEN9.md), a [lista de TMs](data/tms_gen9.csv) e as [omissões por nível](docs/golpes_ainda_nao_incluidos.csv). O instalador é `scripts/atualizacoes_gen9.py`; ROMs e saves continuam fora do Git.

## Variante anterior: golpes aprendidos por nível

A variante anterior atualiza os aprendizados por nível usando Scarlet/Violet quando disponível e corrige o truncamento dos IDs acima de 511. Nela, **efeitos/animações e TMs/HMs ainda não haviam sido atualizados**. Veja [uso, backups, limitações e testes dessa variante](docs/GOLPES_POR_NIVEL.md), o [catálogo anterior](data/learnsets_gen1_9.csv) e as [omissões anteriores](docs/golpes_por_nivel_nao_incluidos.csv). O instalador é `scripts/golpes_gen9.py`.

## Correção dos Pokémon fixos comuns

Uma nova cópia da ROM com treino retira 224 objetos comuns do sistema adicional de encontros fixos; lendários, míticos, Ultra Beasts e Paradox são preservados. Eventos originais de história, incluindo Snorlax, continuam. Veja [instruções, saves, critérios e testes](docs/EVENTOS_FIXOS.md) e o [inventário dos objetos](docs/eventos_fixos_inventario.csv). A ROM e os saves continuam fora do Git.

## Treinamento EV/IV estilo RPG

A ROM de encontros tem uma variante separada com visualização de EVs e IVs no resumo da equipe e redistribuição dos EVs já conquistados. **Nenhum ponto extra é criado; IVs são apenas exibidos.** Veja os [controles, testes e cuidados com saves](docs/TREINAMENTO_EV_IV.md) e a [pesquisa](docs/PESQUISA_TREINAMENTO_EV_IV.md). O instalador é `scripts/treino_ev.py`; o código Thumb e o payload estão em `patches/treino_ev/`. A ROM e saves privados não estão no repositório.

## Trabalho atual: encontros selvagens Gen 1–9

A edição PT-BR mais recente tem uma variante com encontros selvagens adicionais.
O [guia de encontros](docs/guia_encontros.csv), as [instruções e os limites da
validação](docs/ENCONTROS_SELVAGENS.md), o gerador reproduzível
`scripts/encontros_selvagens.py` e seus testes estão neste repositório. A ROM e
os saves privados ficam fora do Git.

A verificação estrutural cobre 931 espécies não lendárias/míticas pela PokéAPI;
alguns encontros e capturas foram testados no mGBA, mas **não todas as espécies
ou rotas**. Lendários e míticos existentes não foram alterados. Ultra Beasts e
Paradoxo seguem a classificação e as ressalvas explicadas na documentação.

> O restante deste README é um registro **histórico** do projeto anterior de
> mochila/mod menu, não das implementações atuais de encontros e treino. Não use os
> endereços e conclusões antigas como se fossem desta ROM Gen 1–9.
> **Atenção:** o veneer e o retorno do BAG_MOD_v3 descritos abaixo estão errados;
> veja [os bytes e testes](docs/DIAGNOSTICO_HOOK_V3.md). O v3 não é uma solução validada.

![plataforma](https://img.shields.io/badge/plataforma-Game%20Boy%20Advance-blue)
![linguagem](https://img.shields.io/badge/scripts-Python%203.13-informational)
![id-stage](https://img.shields.io/badge/fase-6%20(Mod%20ROM)-brightgreen)
![status-mod](https://img.shields.io/badge/mod%20menu-em%20valida%C3%A7%C3%A3o-orange)

Reconstrução técnica **verificável e automatizada** do código interno de *Pokémon
FireRed* (GBA, ARM7TDMI, Thumb), com **objetivo prático**: um **mod menu** acionado
por combo de botões que entrega **Poké Balls, Potions, itens e mais direto na mochila**,
rodando em cópia da ROM no emulador — **sem jeito-feito**: toda alegação passa
por prova em frames/screenshots/dumps de RAM.

> **Legal:** este repositório **não contém a ROM** nem qualquer asset protegido.
> Tudo é código automático, documentação, hashes e screenshots geradas em sessão.
> Você precisa da sua própria cópia do jogo para reproduzir os resultados.

---

## TL;DR do que já está de pé

| Entrega | Status | Onde |
|---|---|---|
| ROM identificada (BPRE, imagem PT-BR modificada ⚠ não-confere No-Intro) | ✅ CONFIRMADO | `inventory.json` |
| Censo de funções + grafo de chamadas (BL direto, milhares de callsites) | ✅ | `functions.csv`, `callgraph/` |
| Decodificador de texto Gen 3 + charset PT-BR remapeado | ✅ | `scripts/gba_poketext.py` |
| Emulador headless **completo** (frames, input agendado, snaps PNG, save-state, mem-dumps) | ✅ | `scripts/gba_libretro_emu.py` |
| **Mapa da mochila**: array @ `0x020258B8`, 4 B/slot `{id:u16, qty:u16}` | ✅ CONFIRMADO | este README ↓ |
| Formatos/offsets no save-state (EWRAM/IWRAM) p/ inspeção offline | ✅ | `notes_mods_codigo.md` |
| **Mod v3** (hook-veneer + combo L+R+START → preencher 8 slots) | 🛠 em validação | `rom_mod/BAG_MOD_v3.gba` |
| Patch de texto demo (safe-text-slot) — primeiro modificador de ROM | ✅ | `rom_mod/PATCH_TEXTO_DEMO_PIDGEY.gba` |

---

## O Mod (o que você vai usar)

**Como dispara:** pressione **L + R + START** juntos no overworld.

**O que acontece:** o trampolim varre o espelho de teclado a cada chamada do
`SetGpuReg` (rotina tiny per-frame) e, ao ver o combo, escreve na mochila:

| Slot | Item | Qtd |
|---|---|---|
| 0 | `0x0001` Master Ball | 99 |
| 1 | `0x0002` Ultra Ball | 99 |
| 2 | `0x0004` Great Ball | 99 |
| 3 | `0x000D` Potion | 99 |
| 4 | `0x001C` Antidote | 50 |
| 5 | `0x002D` — | 30 |
| 6 | `0x0032` — | 30 |
| 7 | `0x0013` Repel | 99 |

> ℹ Lista trivialmente editável no payload (`reports/payload_bag_mod.hex` /
> tabela de pares `(id, qty)` no builder).
> ⚠ L+R sozinho abre a **ajuda nativa** do jogo — o combo completo convive com isso
> (START+SELECT é o alternativo documentado).

### Design técnico do hook (v3 — o estável)

- **Site** em `0x08000A38` — prólogo de `SetGpuReg` (8 B relocáveis, sem pc-relative):
  ```
  01 4b              ldr  r3, [pc, #4]
  18 47              bx   r3
  01 0c eb 08        .word 0x08EB0C01   ; = tramp | Thumb-bit
  ```
- **Trampolim** em `0x08EB0C00` (run 0xFF livre do `freespace_map.tsv`), 158 B:
  ```
  push {r0-r3} ; payload 130 B (combo-gate → writes) ; pop {r0-r3}
  replay do prólogo original ; constrói 0x08000A43 ; bx r3  (Thumb mantido)
  ```
- **Por que veneer e não BL:** BL Thumb só alcança **±4 MB**; o peso-árido fica
  a ~15,4 MB do site. Não existe freespace ≥256 B na janela ±4 MB
  (`reports/freespace_map.tsv` — verificado). Foi essa a causa-raiz de *todas* as
  travas anteriores (v1/v2). Encoder/decoder de BL foram reescritos e homologados
  contra **6.000 BLs reais** da ROM (decode ≡ capstone, re-encode byte-idêntico).

### Status de validação (honesto)

- Boot v3: **estável no jogo** (overworld ok; sem preenchimento sem combo ✓).
- Combo: **ainda não escreveu** no state de teste — diagnóstico aponta o
  espelho `0x03003118` ser **contexto-dependente** (zera na cena-bedroom).
  Próximo passo da lista: espelho-fonte de teclas robusto + payload sempre-escreve
  de sanidade. *(Ninguém aqui chama de 'feito' antes do print da mochila cheia.)*

---

## Diagrama-mestre (sempre-útil)

```
Cenário: overworld → SetGpuReg chamado a cada frame
────────────   original   ────────────        ─────  hokeado (v3)  ─────────────
0x08000B08  bl  #0x08000A38          |  0x08000B08  bl  #0x08000A38
...                                  |
0x08000A38  push {r4,r5,lr}          |  0x08000A38  ldr r3,[pc,#4] ; bx r3 ; .word TRAMP+1
... function body ...                |             ──────────────────────────────► 0x08EB0C00
                                     |                                              tramp:
                                     |                                                push {r0-r3}
                                     |                                                if (keys & 0x0308)==0x0308:
                                     |                                                    bag[0..7] = ITEMS   # 0x020258B8
                                     |                                                pop {r0-r3}
                                     |                                                push {r4,r5,lr}; lsls..; lsrs..; lsls..
                                     |                                                bx → 0x08000A43 (Thumb ☑)
```

---

## Estrutura do repositório

```
gba-re/
├── README.md                ← você está aqui
├── MEMORIA_CONSOLIDADA.md   ← estado-canônico entre sessões (comece por aqui)
├── inventory.json           ← manifesto da ROM (hashes, header, entropia)
├── functions.csv            ← censo de funções (endereço / confiança)
├── hypotheses.md            ← hipóteses x evidências x testes pendentes
├── progress.md              ← log de execução por ciclo (fonte primária)
├── notes_*.md|json          ← notas verificadas (estrutura, charset, mods)
├── callgraph/               ← grafo de chamadas (DOT, edges, métricas)
├── reports/                 ← relatórios gerados (hex dumps, freespace, PNGs)
├── logs/                    ← logs reproduzíveis de cada run
├── scripts/                 ← toda a automação (tabela abaixo)
├── tests/                   ← fixtures sintéticas rotuladas (NUNCA a ROM real)
├── rom/                     ← sua cópia da ROM (não commitar!)
└── rom_mod/                 ← ROMs modificadas (cópias de trabalho apenas)
```

## Scripts (automação completa, `--self-test` em todos)

| Script | O que faz |
|---|---|
| `gba_ident.py` | Triagem: hashes, header GBATEK, entropia, strings, padrões Thumb/ARM. |
| `gba_poketext.py` | Decodifica charset Gen 3 + remap PT-BR; dump de texto. |
| `gba_disasm.py` | Boot-trace ARM → Thumb, censo de BL → `functions.csv` + callsites. ⚠ `encode_bl_thumb` legado com bug de sinal (fórmula correta no §docs). |
| `gba_callgraph.py` | Gera DOT/edges/métricas do grafo de chamadas. |
| `gba_table_probe.py` | Sonda jump-tables e hubs de handlers. |
| `gba_patch_text.py` | Patch safe de slot de texto (0xFF) + relatório hexdump/SHA-256. |
| `gba_hook_code.py` | Instalador de trampolim (site bl → run 0xFF); 6 validações. |
| `gba_libretro_emu.py` | **Driver libretro headless** (mGBA cores via ctypes): frames, `--input f:BTN:hold` multi-janela, `--snap n=arq.png`, save/load-state, mem-read/dump. |
| `gba_state_dump.py` | Parser de save-state mGBA (IWRAM/EWRAM mapeados, `--read VA:len`). |
| `run_all_tests.sh` | Roda todos os `--self-test` e agrega exit-code. |

---

## Reprodução rápida

```bash
git clone <voce>/gba-re && cd gba-re
bash scripts/setup_env.sh                 # dependências mínimas (capstone)

# 1) identificar SUA cópia da ROM (não incluída por motivos legais!)
python3 scripts/gba_ident.py rom/seu_jogo.gba -o reports --update-inventory inventory.json

# 2) bateria de testes (fixtures sintéticas — serve sem ROM)
bash scripts/run_all_tests.sh

# 3) aplicar o mod (gera rom_mod/BAG_MOD_v3.gba a partir dos .hex em reports/)
python3 scripts/apply_mod_v3.py           # mounter/verificador em construção
# or manual: python3 - <<'PY' ... (ver docs/apply_mod_manual.py)

# 4) testar no emulador headless
python3 scripts/gba_libretro_emu.py --rom rom_mod/BAG_MOD_v3.gba \
    --frames 900 --input 100:L:250 --input 100:R:250 --input 100:START:250 \
    --save-state out.bin --snap 890=bag.png
python3 scripts/gba_state_dump.py out.bin --read 0x020258B8:0x10
# esperado (quando validado): 01 00 63 00 02 00 63 00 ...
```

---

## Regras do projeto (contrato de verdade)

1. ROM original intocada; **sempre** trabalhar em cópia.
2. **Nunca inventar** funções, endereços, nomes ou resultados;
   fatos ≠ inferências ≠ hipóteses — níveis: **CONFIRMADO / PROVÁVEL / HIPÓTESE / DESCONHECIDO**.
3. Nada de redistribuir a ROM nem assets (sprites/textos/áudio).
4. Todo script tem `--self-test`, logs reproduzíveis e IO validado.
5. Antes de qualquer claim "FUNCIONA": boot → alvo chamado → comportamento
   esperado → sem crash por 60 s — tudo com evidência visual/dump.

## Stack

Python 3.13 · Capstone Engine · mGBA (libretro core, ctypes headless) ·
Git · (Ghidra mapeado p/ Fase 2) · zero dependências pagas.

## Roadmap (ETA viva — atualizada por ciclo)

- [x] Fase 0/1: ambiente + identificação + inventário.
- [x] Fase 3: callgraph + sondas.
- [x] Emulador headless com input/snap/state/dump.
- [x] Mapa da mochila + formatos de slot (provado por escrita+leitura).
- [x] Fix/homologação do encoder BL (±4 MB, 6.000 amostras reais).
- [x] Veneer hábil p/ payload distante (v3).
- [ ] **Fonte robusta de teclas** (espelho contexto-independente) — *ciclo atual*.
- [ ] **Validação final**: print da mochila cheia + frame-frame stable ≥ 60 s.
- [ ] Expansão: itens infinitos selector / party-pokemon (dados party já mapeados?).
- [ ] Fase 2 Ghidra (rafinação de nomes) — *deferida*.

**ETA (ciclo 34):** diagnóstico do gating de teclas = **1 ciclo** · mod validado
com prova = **+2 ciclos**.

---

## Referências confiáveis

- GBATEK (Martin Korth) — header/mem-map/registradores.
- Capstone — desassembly homologação BL.
- mGBA + docs de scripting — estados/regiões de memória.
- No-Intro — hashes de referência (uso consultivo apenas).

<sub>Projeto pessoal de estudo de engenharia reversa. Não afiliado a Nintendo/
GAME FREAK/The Pokémon Company. **A ROM comercial NÃO faz parte deste repositório.**</sub>
