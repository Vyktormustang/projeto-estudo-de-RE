# V42 — Ida, eventos e retorno das ilhas especiais

**Concluída em 06/11/2026: 6/6 testes aprovados, sem falhas, erros ou skips.** Tempo total do runner: **98,001 s** (97,980 s no unittest).

**A ROM V42 não foi alterada. Não há V43 e não é necessário baixar outra ROM.** Esta auditoria complementa os testes de criação da V42: os caminhos internos e as viagens de retorno, antes não certificados, foram agora percorridos nativamente nos cenários abaixo.

## Resultado dos dois percursos

| Percurso independente | Mapas das ilhas visitados | Passos manuais registrados | Transições nativas entre mapas | Viagens de barco | Capturas |
|---|---:|---:|---:|---:|---|
| Navel Rock, do porto ao topo e à base, de volta a Vermilion | 22 | 465 | 42 | 2 | Ho-Oh 70 e Lugia 70, na mesma viagem |
| Birth Island, do porto ao puzzle, de volta a Vermilion | 2 | 84 | 2 | 2 | Deoxys 30 |
| **Total** | **24** | **549** | **44** | **4** | **3 capturas nativas** |

Os passos são movimentos manuais observados, não todos os deslocamentos automáticos de embarque/desembarque. São **duas jornadas independentes**, cada uma contínua desde Vermilion até o retorno; não um único save contendo as três capturas.

### Navel Rock

1. Em Vermilion, conversa com o marinheiro e recebimento dos dois bilhetes pela rotina da V42 — sem injetar bilhetes ou suas flags.
2. Balsa até Navel Rock Harbor; caminhada pelo exterior, 1F, B1F e Fork.
3. Subida por SummitPath 2F–5F até o Summit. Gatilho de coordenada e **captura real de Ho-Oh nível 70**.
4. Save normal e “Continuar” em um core novo da V42, preservando Ho-Oh e suas flags.
5. Descida até Fork e percurso por BasePath B1F–B11F até Base. Interação com Lugia e **captura real de Lugia nível 70**, mantendo Ho-Oh no grupo.
6. Novo save/Continuar; caminhada de volta pelos andares, Fork, B1F, 1F e exterior até o porto.
7. Menu nativo de retorno: cancelar com B, recuperar movimento, reabrir e escolher **Vermilion**.
8. Retorno, movimento livre, 3.600 frames adicionais no campo (60 segundos emulados), save e “Continuar” em Vermilion com ambos os lendários preservados.

Foram visitados todos os **22 mapas de Navel Rock identificados na ROM**, sem warp de teste entre eles. Não se afirma que cada tile ou item opcional foi explorado.

### Birth Island

1. Conversa com o marinheiro de Vermilion e recebimento nativo dos bilhetes; balsa até Birth Island Harbor.
2. Caminhada do porto até o triângulo. A primeira interação encontra o contador nativo em **11**, resultado da aproximação real, e não artificialmente zerado.
3. Puzzle completo: **11 interações e 52 passos entre a primeira interação e a batalha**. Os dez contadores subsequentes são `4, 8, 8, 8, 4, 4, 4, 6, 3, 3`. Não são forçados contadores, resultados ou posições do triângulo.
4. **Captura real de Deoxys nível 30** e save/Continuar com o Pokémon e as flags preservados.
5. Caminhada de volta ao porto, teste de cancelamento do menu, embarque para Vermilion, controle livre, 60 segundos emulados no campo e novo save/Continuar com Deoxys preservado.

## O que foi verificado

**4 testes estruturais/algorítmicos + 2 testes nativos de jornada completa.** As contagens históricas de 19 testes da entrega V42 e das versões anteriores não são somadas a estas seis.

- Extração dos headers, dimensões, colisão, elevação, comportamento das passagens e destinos a partir da **ROM real**, não apenas da referência de decompilação.
- Grafo dos 24 mapas com destinos recíprocos; rotas estruturais de 9, 17 e 16 transições para os três trechos de Navel Rock, e uma em cada sentido de Birth Island.
- Caminhos entre as saídas respeitam colisões, elevação e passagens que não foram escolhidas. A geometria é idêntica à V41.
- Cada passo manual executado por botões muda a posição por exatamente um tile no mesmo mapa. Cada transição alcança o mapa esperado e retorna ao callback nativo de campo, sem batalha inesperada.
- Os quatro trajetos de barco usam as opções normais da balsa. O menu de retorno é o nativo **61**, contendo Vermilion/Sair; B cancela e devolve o controle antes do novo embarque.
- Os inimigos são criados pelos eventos nativos. Captura com resultado 7, checksum válido, espécie/nível esperados e a mesma personalidade do inimigo. Consumo efetivo da Master Ball e metadados da bola são conferidos.
- O grupo anterior é preservado durante cada captura. Depois das caminhadas, são comparados identidade, espécie, nível, IVs, EVs e bola; mudanças legítimas de amizade por passos não são confundidas com corrupção.
- Após cada captura e após cada retorno, há save normal e “Continuar” em **um core novo da mesma V42**. As flags de captura/ocultação e os Pokémon persistem; o objeto do Pokémon capturado não reaparece no carregamento do local do evento.
- Os bilhetes e suas liberações permanecem após as viagens. As três Master Balls preparadas são consumidas nas três capturas.

A evidência final contém **68 observações**, um rastro de **549 passos + 44 transições**, e **18 capturas de tela**. O CSV de transições acrescenta as quatro viagens de barco, totalizando 48 linhas de deslocamentos entre mapas/portos.

## Preparação e limites

- Somente saves/estados sintéticos. Nenhum save pessoal foi aberto ou alterado.
- Antes de cada jornada, são preparados chegada a Vermilion, progressão, Rainbow Pass e Master Balls. A preparação inicial de chegada usa uma cópia temporária com um letreiro de warp, seguida de save normal e carga na **V42 exata**; essa cópia não é distribuída.
- **Nenhum warp de teste dentro das ilhas.** Após o início, não há edição de posição, progresso, contador do puzzle, inimigo ou resultado de batalha. A movimentação usa botões; sondas de leitura executam consultas isoladas e restauram o mesmo estado, sem avançar ou reescrever a jornada. Gravação e carregamento usam o save normal.
- O início da campanha até obter legitimamente Rainbow Pass/progressão não foi percorrido nesta rodada. O teste não certifica campanha completa, taxa de captura com bolas comuns, todos os itens opcionais, hardware real, link ou fidelidade integral a Scarlet/Violet.
- Não foram reexecutadas aqui todas as suítes históricas. A ROM e os artefatos anteriores foram conferidos por hash e permaneceram intactos.

## Identificação e reprodução

- **V42:** `6997366bea7056778e3183595d2e2f84c62a98576430db71b9459962e5bbd99a`
- V41 usada somente como comparação estrutural: `662225325c50af5aeb568da97a10110cff300aff55e1a6ec87f0d11c1a5f5d50`
- mGBA libretro 0.10.5: `07ab56ae80ed30486eff67ab4907b345f46ebb5e60f47f98869dc534df18dad9`
- Fonte do core: commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`. Construção documentada em `MOTOR_V40.md`.

Com Python, Pillow, o core indicado e cópias próprias das ROMs, a partir da raiz do repositório:

```sh
python3 -B firered_gen1_9/scripts/validar_trajetos_v42.py \
  --rom /caminho/FireRed_Gen1-9_motor_v42.gba \
  --base /caminho/FireRed_Gen1-9_motor_v41.gba \
  --core /caminho/mgba_libretro.so \
  --saida /caminho/resultados-trajetos-novos
```

O diretório de saída precisa ser novo. O runner recusa hashes divergentes, falhas e skips. A auditoria estrutural isolada também pode ser reproduzida com `scripts/auditar_trajetos_v42.py --rom ... --saida novo.json`; ela não substitui os testes nativos.

Arquivos complementares: `trajetos_v42_resultados.json`, `trajetos_v42.log`, `trajetos_v42_estrutura.json`, `trajetos_v42_observacoes.json`, `trajetos_v42_passos.csv`, `trajetos_v42_transicoes.csv` e `trajetos_v42_capturas.csv`.

**Sem nova ROM, commit, push ou publicação no Drive.** ROMs, saves, estados e capturas de tela do jogo ficam fora do Git; o pacote de evidências não contém ROM/save/state.
