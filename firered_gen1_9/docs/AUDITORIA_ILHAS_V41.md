# Lugia, Ho-Oh e Deoxys — auditoria na V41

**06/11/2026 · somente leitura · ROM V41 preservada · nenhuma V42 gerada**

## Conclusão

**Os três eventos funcionaram nos testes: Lugia e Ho-Oh no nível 70; Deoxys no nível 30, após resolver o puzzle completo do triângulo.** Os três Pokémon foram capturados, salvos e recuperados por Continuar. As flags de captura/ocultação persistiram, e os objetos dos Pokémon não estavam ativos após recarregar.

**O transporte também funciona quando seus requisitos estão presentes.** O teste embarcou em Vermilion e chegou aos portos de Navel Rock e Birth Island por botões normais.

**A pendência principal permanece a aquisição normal dos bilhetes e das liberações.** Foram localizados scripts de Mystery Gift que concedem esses itens e flags, mas não foi comprovado como receber esses eventos durante uma campanha normal desta base. Não foi feita uma alteração de acesso nesta etapa.

Estes resultados **não equivalem a uma campanha percorrida do início às capturas**: a progressão/bilhetes/flags do teste de transporte foram preparados sinteticamente. As capturas partiram de chegadas sintéticas independentes aos locais dos eventos. Não foi percorrido o trecho dos portos até todas as salas dos lendários, nem testada a viagem de retorno.

## Requisitos reais do transporte

Marinheiro de **VermilionCity**, grupo/mapa **3/5**, objeto **6**, posição **(24,33)**. Raiz de script real: offset de arquivo `0x18F32D`.

Antes das escolhas de ilhas especiais, a lógica consultada exige:

1. **VAR 0x407E = 3:** estado de Vermilion depois da partida do S.S. Anne.
2. **VAR 0x4076 ≥ 5:** estágio da progressão das ilhas que libera o ramo Rainbow Pass. Os valores 1 e 4 foram controles: mesmo com ambos os bilhetes e flags, aparece apenas o menu das ilhas 1–3.
3. **Bilhete na bolsa E flag de liberação correspondente:**

| Destino | Item | Flag exigida | Predicado real |
|---|---|---|---|
| Navel Rock — Lugia/Ho-Oh | Mystic Ticket, ID **370** | `0x084A` | `0x18F344` |
| Birth Island — Deoxys | Aurora Ticket, ID **371** | `0x084B` | `0x18F363` |

**Ter só o item não libera a viagem; ter só a flag também não.** Não se deve tratar “o item pode ser inserido na bolsa” como prova de acesso ao evento.

Foram exercitadas **16 combinações**: nenhuma/uma/ambas as passagens × nenhuma/uma/ambas as flags. O menu oferecido correspondeu à interseção entre os bilhetes presentes e as flags ligadas:

| Condição efetiva | Menu observado |
|---|---|
| Nenhuma ilha especial liberada | Menu dinâmico 255 das ilhas comuns, sem Navel/Birth |
| Apenas Mystic Ticket + flag 0x084A | Menu 54: Navel Rock |
| Apenas Aurora Ticket + flag 0x084B | Menu 55: Birth Island |
| Ambos os pares completos | Menu 56: Navel Rock e Birth Island |
| Progressão das ilhas em 1 ou 4, mesmo com os pares completos | Menu 57: apenas ilhas 1–3 |

A matriz usa um save sintético com a progressão requerida e as flags de bilhetes já mostrados ligadas para suprimir a saudação de primeira apresentação. Essa saudação não foi o objeto do teste. A ausência de Navel/Birth no menu regular foi conferida também visualmente.

No início de jogo sintético, foram observadas **zero unidades dos dois bilhetes e ambas as flags de liberação desligadas**. Isso descreve o início; **não demonstra que nenhum evento posterior possa concedê-los**.

### Entrega dos bilhetes encontrada na ROM

| Rotina de Mystery Event | Raiz relocável | Trecho que concede o item | Flag de recebimento |
|---|---|---|---|
| Mystic Ticket | `0x8797E1` | `0x87982A` | `0x02A8` |
| Aurora Ticket | `0x879611` | `0x879651` | `0x02A7` |

Os trechos conferidos chamam a rotina padrão de entrega de item e, em seguida, ligam a flag de transporte e a flag de recebimento. Os offsets e operandos vieram da **V41 real**, não de offsets presumidos do FireRed original. A referência semântica foi `pret/pokefirered`, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`.

**Código de distribuição presente não significa distribuição normalmente acessível.** Esta auditoria não certificou recepção externa de Mystery Gift, liberação pós-Liga, entrega por outro NPC, todas as opções de menus de itens ou efeitos de outras revisões de FireRed. Também não concluiu uma impossibilidade absoluta de obtenção na base.

## Travessias executadas

Com os requisitos preparados antes da interação:

- Escolha **Navel Rock** no menu 56 → viagem nativa → **NavelRock_Harbor, grupo/mapa 2/59**.
- Escolha **Birth Island** no menu 56 → viagem nativa → **BirthIsland_Harbor, grupo/mapa 2/58**.

Após a escolha, não foram injetados destino, warp, flags, script ou resultado de transporte. A chegada foi verificada pelo mapa real, callback de campo, ausência de batalha e tela capturada. Os portos têm aparência semelhante; os IDs de mapa distinguem as duas chegadas.

Não foi certificado o caminho completo desses portos até as salas dos eventos. As capturas abaixo usaram fixtures independentes.

## Eventos, capturas e persistência

| Pokémon | Local do evento | Gatilho executado | Nível | Flag de evento concluído | Flag de ocultação |
|---|---|---|---:|---|---|
| Lugia #249 | NavelRock_Base, 2/38 | Interação com o objeto 1 | 70 | `0x02F2` | `0x009B` |
| Ho-Oh #250 | NavelRock_Summit, 2/37 | Passo sobre (9,12) | 70 | `0x02F3` | `0x009C` |
| Deoxys #386 | BirthIsland_Exterior, 2/56 | Puzzle completo do triângulo | 30 | `0x02E4` | `0x0099` |

O objeto visual de Ho-Oh não precisa ter um script de interação: o evento é disparado pela coordenada. Para Deoxys, o script parte do triângulo, não do objeto visual do Pokémon. A análise estrutural seguiu esses gatilhos até preparar a espécie e iniciar a batalha.

### Deoxys: puzzle sem pular etapas

Foram realizadas **11 interações e 52 passos entre elas**, conferindo as posições reais do triângulo e o avanço da variável de progresso após cada movimento do objeto. O contador nativo de passos foi verificado em cada etapa.

- **Não foram editadas VAR 0x4026, VAR 0x403E nem a flag de puzzle resolvido para completar a sequência.**
- Os deslocamentos, interações, animação final e início da batalha foram executados por botões normais.
- A chegada sintética ao mapa usa seu script normal de entrada; não substitui o puzzle por um combate direto.

### O que foi verificado em cada captura

- Espécie, nível, checksum válido, batalha selvagem e tela de batalha correspondente.
- Uma **Master Ball de teste**, preparada antes da interação, consumida normalmente. Isso não é ensaio de taxa de captura com bolas comuns.
- Pokémon capturado com a mesma personalidade do inimigo; metadado da bola; Pokémon inicial preservado.
- Flags de evento concluído e ocultação ligadas após o retorno ao campo.
- Save normal, core reiniciado e **Continuar** na mesma V41; Pokémon e flags preservados, bola consumida e objeto do lendário não ativo.

Fuga, derrota, blackout, reaparecimento após outras condições e todos os estados de eventos já consumidos não foram testados. Os saves foram sintéticos, nunca arquivos pessoais.

## Validação e preparação

**9/9 métodos aprovados em 144,618 s**, sem falhas, erros ou skips: **4 estruturais + 5 de emulador**.

- Estrutura: hash exato da V41, raízes do marinheiro, condições de progresso, predicados bilhete+flag, trechos de Mystery Gift e três eventos nativos.
- Segurança: rejeição de entrada divergente/truncada, saída exclusiva, repetibilidade do JSON e ROM inalterada.
- Emulador: matriz de 16 combinações, dois controles de progresso, duas travessias, início sem bilhetes/liberações, três capturas/persistências e puzzle de Deoxys.

A preparação utiliza uma cópia descartável com warp somente para chegar ao ponto de teste. Cada cópia parte de seu próprio jogo novo. O jogo salva **flash normal**, que é carregada por Continuar na **V41 exata**. **Nenhum savestate passou entre ROMs diferentes**, nenhum warp de teste foi entregue, e não houve edição de ROM durante as ações auditadas.

As leituras de variáveis/flags durante a inspeção são chamadas em cópias do estado, restaurando o estado original imediatamente depois; não publicam mutações no fluxo ao vivo. A progressão/bilhetes/flags do transporte e a Master Ball dos combates foram preparados antes das ações correspondentes.

Houve ajustes no harness durante o desenvolvimento: evitar uma interação acidental com o marinheiro ao chegar e aguardar a paginação dos diálogos do Tri-Pass/Rainbow Pass. O menu comum dinâmico usa ID 255; não deve ser confundido com ausência de menu durante o diálogo. Também foi testado cancelar esse menu e recuperar o movimento. A primeira tentativa falhou ao salvar durante diálogo; outras ainda não haviam chegado ao menu correto. Esses resultados não foram tratados como defeitos da ROM. A contagem acima corresponde à rodada final completa, não à soma das tentativas.

Os **15 testes da entrega V41** e os **103 históricos da V40** não foram reexecutados nem somados nesta rodada.

## Entregáveis

- [Evidência estrutural](ilhas_v41_estrutura.json): raízes, offsets, predicados e caminhos dos eventos.
- [Matriz do transporte](ilhas_v41_matriz.csv): 16 combinações de itens e flags.
- [Resumo das três capturas](ilhas_v41_capturas.csv).
- [Observações do emulador](ilhas_v41_observacoes.json).
- [Resultados](ilhas_v41_resultados.json) e [log final](ilhas_v41.log).
- Pasta `telas/`: três batalhas, menus/controles e chegadas aos dois portos. São telas do emulador, não imagens geradas.

### Reprodução

Da raiz do repositório, com saída inexistente:

```sh
python3 -B firered_gen1_9/scripts/auditar_ilhas_v41.py \
  --rom deliver/v41/FireRed_Gen1-9_motor_v41.gba \
  --saida deliver/auditoria_ilhas_nova/estrutura.json
```

Configure `ILHAS_V41_ROM` e `MGBA_CORE` com caminhos absolutos. Opcionalmente, `ILHAS_V41_OBSERVATIONS` aponta para um arquivo novo e `MOTOR_V41_SCREENS` para uma pasta de capturas. No ambiente com as dependências do harness/mGBA/Pillow:

```sh
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests python3 -B -m unittest -v \
  test_ilhas_v41.IslandStructureTests \
  test_ilhas_v41_mgba.IslandNativeTests
```

ROM: **33.554.432 bytes**, SHA-256 **`662225325c50af5aeb568da97a10110cff300aff55e1a6ec87f0d11c1a5f5d50`**.

mGBA 0.10.5, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; core SHA-256 `07ab56ae80ed30486eff67ab4907b345f46ebb5e60f47f98869dc534df18dad9`.

## Próxima etapa recomendada

**Propor uma V42 com obtenção normal dos bilhetes pelo marinheiro de Vermilion, somente após a progressão do Rainbow Pass**, mantendo os três eventos nativos intactos. A proposta deve tratar bilhetes já possuídos, flags ausentes, bolsa cheia, repetição e saves existentes; não deve resetar flags de captura nem liberar ilhas antes da hora. Essa mudança **não foi implementada nesta auditoria**.

Continuam separados os pontos de Cosmog/Solgaleo/Lunala, Tanoby e outros acessos da auditoria dos 1.025. Nenhuma conclusão aqui certifica todas as espécies, campanha completa, link, hardware ou saves pessoais.

**Entrega local, sem ROM nova, publicação no Drive, commit ou push. A V41 e suas entregas anteriores permanecem intactas.**
