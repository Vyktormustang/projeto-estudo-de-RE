# Auditoria ampliada da v32 — gameplay, captura e continuidade local

Data: 2026-11-06. Escopo escolhido: **aprofundar a validação**, sem expandir encontros ou modificar a ROM.

## Estado

**99/99 métodos aprovados em 645.203 s**, sem falhas, erros ou skips: seis métodos novos e os 93 da validação original da v32, executados novamente. A ROM e todos os arquivos cobertos pelos manifestos anteriores foram conferidos antes da atualização documental; estavam inalterados.

Detalhes verificáveis: [resultados JSON](auditoria_v32_resultados.json) e [log consolidado](auditoria_v32.log).

A ROM continua sendo **FireRed_Gen1-9_motor_v32.gba**, 33.554.432 bytes, SHA-256:

`7c095be4d52eeb728600eafbe2f57b60a4a402c11fe9a84cc19a8bbf61aa6d13`

**Não existe v33 nesta etapa.** Permanecem as 36 áreas, a distribuição, o guia, o relógio acelerado, MUNDO, Opções e o formato de save da v32. Nenhum builder, política, payload ou tabela de encontros é alterado nesta auditoria.

## Novos ensaios

### 1. Captura e persistência nas quatro novas áreas

Um método por área, com três cenários cada: espécie diurna do slot 2, primeira substituição noturna e segunda substituição noturna.

| Área | Controle diurno | Noturno, HUD oculto | Noturno, relógio pós-cap |
|---|---|---|---|
| Berry Forest | Hatterene, 32 | Phantump, 32 | Shiinotic, 30 |
| Pattern Bush | Nymble, 14 | Venonat, 14 | Ariados, 6 |
| Entrada de Sevault Canyon | Golett, 10 | Houndour, 10 | Murkrow, 48 |
| Sevault Canyon | Ceruledge, 46 | Houndoom, 46 | Honchkrow, 50 |

Total aprovado: **12 capturas naturais seguidas de save/reinicialização/Continuar**. Cada cenário começa com um único Pokémon no time e uma Master Ball sintética. A caminhada sorteia os encontros nativamente; varia-se apenas a espera inicial para obter o alvo. Após iniciar a caminhada não se editam RNG, espécie, nível, HP, atributos, movimentos ou experiência.

São conferidos:

- Encontro selvagem, não batalha de treinador, com espécie, nível e checksum válidos.
- HUD ausente durante a batalha.
- Resultado nativo de captura (`B_OUTCOME_CAUGHT = 7`), retorno ao mapa e time com dois membros.
- Identidade/PID, espécie, nível, IVs, HP e HP máximo do capturado iguais aos do encontro; metadado da bola igual a Master Ball.
- Pokémon inicial inteiro preservado, incluindo seus 100 bytes; consumo da única bola.
- Save flash nativo de 128 KiB, core encerrado e novo core carregando **a mesma ROM exata** por Continuar, sem usar savestate nessa recarga.
- Os 100 bytes do capturado, inicial, local, preferência de HUD e consumo da bola persistem.
- Relógio avança, incluindo o registro pós-999:59:59; HUD volta ou permanece oculto conforme a preferência.
- Movimento por botão após carregar, sem travamento no retorno.

A Master Ball é um controle determinístico do caminho de captura, **não uma medição de catch rate**. Os testes existentes com Poké Ball comum e falhas de captura são reexecutados no conjunto original. Estes novos cenários não certificam PC cheio, envio ao PC, todas as bolas ou todas as espécies.

### 2. Amanhecer e anoitecer com o jogo rodando

Em Berry Forest, quatro cenários pós-cap: **05:59 → 06:01** e **19:59 → 20:01**, com HUD visível e oculto.

O tempo/preferência são preparados somente no início. Depois, o jogo executa **120 frames sem input**: o registro deve avançar exatamente 120 ticks, e a visibilidade deve respeitar a preferência. Em seguida, caminhada e sorteio nativos produzem Hatterene no controle diurno ou Phantump no noturno. O período também é conferido no estado real da batalha, não apenas em chamada isolada do seletor.

Não é um teste de transição no meio da batalha, RTC, tempo offline ou travessia do cap nesta ação; o registro pós-cap é uma condição inicial sintética. A travessia do cap e os dois dias virtuais completos continuam cobertos pelos métodos originais reexecutados.

### 3. Travessia local de Sevault e save

Dois cenários, de dia/HUD visível e à noite/HUD oculto:

1. Carregar um checkpoint sintético da entrada de Sevault na ROM exata.
2. Caminhar pela **conexão leste nativa** para Sevault Canyon.
3. Retornar pela **conexão oeste nativa** para a entrada.
4. Salvar, encerrar o core e carregar por Continuar.

Os descritores reais desta ROM são conferidos: entrada → Canyon, direção 4 e deslocamento +20; retorno, direção 3 e deslocamento −20. Não se transplanta coordenada/offset de uma ROM vanilla. O ponto inicial `(22, 28)` está junto à conexão da entrada; o mapa e a coordenada são verificados antes e após o primeiro carregamento.

São conferidos mapas de destino, callback de campo, ausência de batalha nessa pequena passagem, time/identidade, preferência e HUD. O save final deve voltar à entrada de Sevault com o mesmo Pokémon inicial.

**Isso prova apenas essa travessia local**, não o percurso completo de Sevault, a chegada às ilhas, barcos, insígnias, HMs, puzzles ou requisitos de história.

## Preparação sintética e limites de evidência

O começo do jogo/inicial/rival é produzido pelo harness por botões. Para chegar às áreas distantes, uma **cópia descartável** da ROM recebe somente um script de warp na placa da Rota 1 e seu ponteiro. O teste restaura esses dois intervalos em memória e exige igualdade integral com a ROM exata, para verificar que nenhuma outra instrumentação foi aplicada.

Após chegar, o jogo grava um save normal. O core da cópia é encerrado. Um novo core carrega **a ROM de SHA-256 acima** e esse flash por Continuar; mapa, coordenada e Pokémon são conferidos. **Nenhum savestate atravessa ROMs.** Captura, conexão, mudanças de período e saves auditados acontecem somente depois desse carregamento na ROM exata.

Tempo, preferência e uma bola são condições iniciais de ensaio, não conquistas legítimas de campanha. O trajeto até a placa usa Repel sintético; ele não força espécie e o inicial é inferior aos níveis dos novos encontros. Não são concedidas insígnias, HMs ou flags de conclusão de história para alegar progressão normal.

Restaurações de estado para variar a espera inicial ocorrem apenas dentro da mesma ROM exata. Consultas isoladas de inventário usam ABI nativa; antes de qualquer botão, restaura-se o estado vivo observado, não o estado da CPU parado no sentinel do harness.

Não se usou save pessoal. Não há certificação de Lostelle, de campanha completa, hardware real, todos os emuladores, link real ou fidelidade integral a Scarlet/Violet. A preservação byte a byte dos scripts de história, já testada na v32, não substitui jogar esses eventos completos.

## Regressões reexecutadas

Os **93 métodos originais** permanecem com a mesma seleção:

- 10 build/dados; 8 encontros, incluindo 7.200 casos determinísticos e 720 consultas pós-cap.
- 10 guia, com 72 consultas e navegação paginada.
- 11 HUD; 10 preferências; 10 relógio persistente; 11 relógio anterior.
- 5 estojo/TMs; 4 combate; 5 gameplay/flash; 9 EV.

Entre os controles: 1.440 horários no oráculo de pixels, 172.800 frames vivos, 287 quantidades de TMs/HMs, captura com Poké Ball, fuga, combate/evolução e saves sintéticos v31↔v32. As contagens são da seleção, não soma das rodadas focadas com a consolidada. Quantis não são frequências medidas em caminhada aleatória.

## Reprodução

- Testes novos: `tests/test_motor_v32_audit_mgba.py`.
- Runner ampliado: `scripts/validar_motor_v32_auditoria.py`.
- Runner original de 93 métodos preservado: `scripts/validar_motor_v32.py`.
- mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`.
- Core SHA-256: `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`.
- Base v31 exigida para os controles de downgrade: `fa25df630c902c7b7e155c9d8fca86f4a4674a76123b3541b68ab8eabcc84096`.

```sh
MOTOR_V32_ROM=/caminho/FireRed_Gen1-9_motor_v32.gba \
MOTOR_V32_BASE=/caminho/FireRed_Gen1-9_motor_v31.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
TREINO_TEST_ROM=/caminho/FireRed_Gen1-9_motor_v32.gba \
python firered_gen1_9/scripts/validar_motor_v32_auditoria.py \
  --jobs 3 --log /tmp/v32-audit-final.log
```

Runner exige **99 IDs únicos**, nenhum skip/falha/erro e cores/partidas isolados. O tempo consolidado é de parede. `--jobs 1` executa serialmente. As cópias de teste e saves são temporários e não entram no Git.

Entrega de **relatório**, não de nova ROM. Sem publicação no Drive, commit ou push. Para uso normal da v32, mantenha backup e carregue por Continuar; não reaproveite savestates de outras versões nem misture com FireRed BR/BAG_MOD.
