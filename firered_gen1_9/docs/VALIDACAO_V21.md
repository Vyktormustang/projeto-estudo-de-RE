# Validação ampliada da v21 — 2026-11-05

## Objetivo e identidade

Rodada de regressão solicitada após a expansão dos encontros por horário. **Sem v22 e sem novas mecânicas.** A ROM v21 não recebe nenhuma alteração nesta rodada.

- ROM: `FireRed_Gen1-9_motor_v21.gba`, **33.554.432 bytes**.
- SHA-256: `cfbcebd0bf3ab0c1cbcb9872bc400f62d9c807fbd67dd99b4b89ffb16c92a10f`.
- Emulador: **mGBA libretro 0.10.5**, código upstream no commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`.
- Ambiente: Python 3.11.2 e GCC 12.2.0, Linux; core compilado em Release.
- SHA-256 do core usado nesta execução: `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`.
- Exclusivamente jogos, Pokémon, flash e estados sintéticos. Nenhum save pessoal.

A ROM e o core não estavam no checkout reaberto. A v18 previamente entregue foi recuperada do Drive privado e aplicada à cadeia de builders **v19 → v20 → v21**, sem editar os checksums esperados. Todos os hashes de entrada/saída coincidiram. O manifesto anterior de fontes foi conferido: **296/296 entradas iguais** antes desta rodada. Os testes não dependem da presença dos commits locais citados no histórico da conversa.

Os adaptadores em `tests/test_motor_v21_regressions.py` verificam a **v21 exata** ao abrir e fechar o core. Não afrouxam os hashes das suítes antigas nem importam suas classes negativas específicas de outras ROMs. Os novos fluxos estão em `tests/test_motor_v21_gameplay_mgba.py`.

## Resultado

**Rodada concluída: 68 métodos distintos aprovados, sem failures, errors ou skips**, em três execuções finais. A v21 permanece byte a byte identificada pelo mesmo SHA-256. Nenhuma alteração de ROM foi necessária.

| Grupo | Métodos | Resultado |
|---|---:|---|
| Build/dados, encontros, horário/evoluções/paletas e EV/IV | 37 | Aprovados, sem skips — 157,641 s |
| Captura/persistência, fuga e transição entre mapas | 4 | Aprovados, sem skips — 77,188 s |
| Regressões ampliadas de batalha | 27 | Aprovados, sem skips — 2785.865 s |

Os processos podem executar em paralelo: suas durações não representam um único tempo total decorrido. Sondas preliminares não entram nos totais finais.

## Fluxos novos efetivamente verificados

### Captura e persistência — três casos dentro de um método

Na **Rota 1**, por caminhada normal, sem warp ou Pokémon injetado:

| Período virtual inicial | Espécie | Nível |
|---|---|---:|
| Dia, 10:00 | Magby | 3 |
| Noite, 22:00 | Hoothoot | 3 |
| Noite, 22:00 | Nickit | 3 |

Preparação explícita: uma **Master Ball** é adicionada pelo `AddBagItem` nativo à fixture sintética, antes da caminhada; o contador de tempo também é preparado antes da ação. O item não é uma recompensa adicionada à ROM. A partir daí, encontro, escolha da bolsa, lançamento, recusa de apelido e retorno usam botões normais.

Cada caso exige:

1. Batalha selvagem, não treinador; espécie/nível/checksum válidos.
2. Resultado nativo **7 / capturado**, flag de batalha desligada e callback de campo restaurado. Texto remanescente em RAM sozinho não é suficiente.
3. Equipe passa de um para dois membros; inicial não muda durante a captura.
4. Pokémon recebido conserva personalidade, espécie, nível, IVs e HP observados no selvagem; checksum válido.
5. Master Ball consumida: quantidade final zero.
6. Save feito pelo menu do jogo, flash de **131.072 bytes**.
7. Core fechado e reiniciado; apenas a flash sintética é carregada, **sem importar savestate**.
8. Pokémon capturado preservado byte a byte no slot da equipe e item continua consumido, no mesmo mapa e fora da batalha.

**Controle adicional com Poké Ball comum:** um quarto método encontra Nickit naturalmente, usa a Poké Ball (item 4), verifica captura/retorno, consumo e preservação de identidade/IVs/nível/HP. O campo nativo de bola utilizada é conferido: 4 para Poké Ball, 1 nos casos de Master Ball.

**Não mede taxa de captura.** O caso de Poké Ball é um resultado determinístico de um sorteio nativo, não uma estimativa de probabilidades nem teste de todas as falhas possíveis. Os três casos com Master Ball isolam a integridade do fluxo e da persistência. Não testa caixa cheia, envio ao PC, capturas nos outros sete mapas, todas as espécies ou persistência de todos os bits da Pokédex.

### Fuga à noite

Encontro natural com Nickit, sem alterar HP, velocidade ou RNG. A opção Run é escolhida pela interface; tentativas nativas podem falhar e ser repetidas. Exige resultado **4 / fuga**, retorno ao campo, equipe ainda com um membro, checksum válido e movimento do jogador novamente possível.

### Progressão curta: Pallet ↔ Rota 1

A fixture joga a introdução, escolha do inicial e passagem pela batalha obrigatória do rival usando botões. O teste exige a chegada ao ponto esperado de Pallet e verifica o trajeto **Pallet → Rota 1 → Pallet**, de dia e de noite, sem warp.

Conferidos grupo/mapa, presença do NPC regular da rota, callback de campo, quantidade de membros e identidade/dados criptografados do inicial. Encontros aleatórios durante a volta são tratados por fuga nativa. HP não é obrigado a permanecer idêntico, pois uma tentativa de fuga malsucedida pode permitir um ataque adversário.

Isso é cobertura de uma **conexão inicial e retorno de batalha**, não prova da campanha inteira, da entrega do Parcel, dos ginásios, da Liga ou de todas as flags de história.

## Escopo das regressões de batalha selecionadas

Os 27 métodos selecionados abrangem:

- **8 de bloqueios de pivôs:** Protect, absorções elétrica/água, imunidade Ground, Soundproof, Clear Body, estágios mínimos e falta de reservas. Incluem as correções v18 de Volt Switch e Parting Shot.
- **4 de trocas/pivôs com hazards:** ordem de entrada, sobrevivência, KO e segunda seleção, preservação do aliado, absorção de Toxic Spikes, status e Sticky Web.
- **6 de ciclo de vida de hazards:** nova batalha, Court Change, limpeza e recriação, Rapid/Mortal Spin, Stone Axe/Ceaseless Edge, ordem e KO antes de habilidade.
- **6 de Soundproof em singles:** golpes nativos e modernos, dano/dreno/PP, Substitute, histórico e ação seguinte.
- **3 de experiência/encerramento:** vitória natural sem editar atributos/HP/EXP, subida 10 → 11 com retorno ao campo e coerência das fábricas sintéticas.

Os cenários de batalha preparados podem ajustar tipos, habilidades, HP, movimentos e reservas **antes** da ação. Não são equipes obtidas por uma campanha natural. Durante as ações usam o motor e controles normais; as observações quadro a quadro verificam HP, PP, histórico, identidade, trocas e encerramento conforme cada método.

O negativo histórico com nível 10 e EXP=1 incoerente não foi usado como critério de aceitação de gameplay. Continua disponível em sua suíte histórica, sem ser apagado ou alterado.

## Sondagem que exigiu correção do teste

A primeira versão do teste de retorno segurava DOWN por 280 frames e supunha que nenhum encontro aconteceria. Houve encontros nativos nos dois períodos, portanto o teste falhou **antes de completar o trajeto**, e não demonstrou um defeito na ROM.

O teste foi corrigido para observar a batalha, usar Run e prosseguir até Pallet dentro de um limite de passos. Permanecem as exigências de mapa, retorno ao campo e identidade da equipe. A ROM não foi modificada. A execução final de quatro métodos passou, incluindo o controle adicional de Poké Ball; a sondagem e a execução intermediária de três métodos não são somadas aos resultados finais.

## Reprodução

Pré-requisitos: Python com NumPy/Pillow, core mGBA 0.10.5 e ROMs privadas identificadas. Não usar saves pessoais ou estados de outra versão.

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V21_ROM=/privado/FireRed_Gen1-9_motor_v21.gba
export MOTOR_V21_BASE=/privado/FireRed_Gen1-9_motor_v20.gba
export TREINO_TEST_ROM="$MOTOR_V21_ROM"
export MGBA_CORE=/privado/mgba_libretro.so

python3 -m unittest test_motor_v21 test_motor_v21_mgba test_treino_ev_mgba -v
python3 -m unittest test_motor_v21_gameplay_mgba -v
python3 -m unittest test_motor_v21_regressions -v
```

Sem as variáveis, as suítes opcionais podem ser ignoradas: **skips não validam nada**. A última execução é mais demorada por acompanhar diversos cenários quadro a quadro. Os hashes rígidos devem ser mantidos.

## Limites mantidos

Não é uma execução de toda a suíte histórica ou um certificado de fidelidade integral a Scarlet/Violet. Permanecem fora do recorte: campanha completa, link/multi, hardware real, todas as bolas e probabilidades, todas as espécies/habilidades/movimentos, PC cheio e migração de saves pessoais. A limitação do relógio em **999:59:59** continua presente; não foi corrigida nesta rodada.

Nenhum arquivo foi publicado ou alterado no Drive. A recuperação da ROM foi somente leitura. Nenhum `.gba`, `.sav`, savestate ou asset protegido faz parte das alterações de código.

## Evidências e arquivos

`validacao_v21_resultados.json` registra os 68 IDs de método, durações, SHA-256 dos logs e das duas novas suítes. Em `deliver/v21/validacao/`: relatório, JSON, `TESTES_BASE.log`, `TESTES_GAMEPLAY.log`, `TESTES_BATALHAS.log` e a sondagem inicial `SONDAGEM_TRANSICAO.log`. O manifesto atual de fontes foi atualizado e conferido: **300/300 entradas**, excluindo o próprio manifesto.
