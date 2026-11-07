# Motor parcial V41 — Type: Null sem depender da variante 7

**06/11/2026 · base V40 exata · correção pontual de obtenção**

## Como encontrar

**Type: Null (#772), nível 20, em Altering Cave, na Ilha 6.** Está disponível **de dia e à noite**, com **10% nominal dos encontros terrestres**, em todas as nove variantes da caverna e também quando um valor inválido faz o jogo usar a tabela padrão.

A chance é condicional a um encontro terrestre e anterior a Repel/outros filtros. **Não significa 10% por passo.** A frequência geral da caverna permanece a mesma. Não é necessário obter Mystery Gift nem selecionar a variante 7 para esse Pokémon na V41.

O acesso normal à Ilha 6/caverna e os requisitos de campanha **não foram alterados** nem percorridos integralmente nos testes. A V41 não libera ilhas, bilhetes, flags de progresso ou transporte.

## Por que foi necessário

Na V40, Type: Null ocupava apenas o slot 2 da variante 7. A rotina nativa escolhe entre nove tabelas de Altering Cave usando **VAR 0x4024**. A tabela padrão é a variante 0; valores acima de 8 também caem na padrão.

Foi conferido na ROM real o script relocável de Mystery Event em **offset `0x8799BA`**: estabelece o endereço virtual, incrementa VAR 0x4024, compara com 10 e retorna a zero ao atingir esse valor. A presença desse código **não comprova um meio normalmente utilizável de receber o evento**. Não foi encontrada interação local para selecionar a variante: a caverna tem zero objetos, zero eventos de coordenada/fundo e um warp. Seu script de entrada em `0x18D090` apenas marca a visita no mapa-múndi (flag `0x08BE`).

Não se afirma que a obtenção original fosse impossível em todas as circunstâncias. A correção evita depender desse mecanismo para Type: Null, sem removê-lo ou forçar a variável do jogador.

## Alteração exata

Foram substituídos **oito slots redundantes de espécies comuns**, um por variante sem Type: Null. Cada slot novo contém nível mínimo 20, máximo 20 e espécie 772. A variante 7, que já tinha o encontro correto, fica **integralmente intacta**.

| Variante / header | Slot alterado (base zero) | Antes | Depois | Offset do registro |
|---|---:|---|---|---|
| 0 / 123 | 3 | Zubat, nível 14 | Type: Null, nível 20 | `0x7B7660` |
| 1 / 124 | 3 | Mareep, nível 11 | Type: Null, nível 20 | `0x7B7698` |
| 2 / 125 | 3 | Pineco, nível 27 | Type: Null, nível 20 | `0x7B76D0` |
| 3 / 126 | 3 | Houndour, nível 20 | Type: Null, nível 20 | `0x7B7708` |
| 4 / 127 | 3 | Teddiursa, nível 26 | Type: Null, nível 20 | `0x7B7740` |
| 5 / 128 | 3 | Aipom, nível 26 | Type: Null, nível 20 | `0x7B7778` |
| 6 / 129 | 3 | Shuckle, nível 26 | Type: Null, nível 20 | `0x7B77B0` |
| 7 / 130 | Nenhum | Type: Null, nível 20, slot 2 | Preservado | `0x7B77E4` |
| 8 / 131 | 3 | Smeargle, nível 26 | Type: Null, nível 20 | `0x7B7820` |

Cada slot alterado tem **10% nominal**. As oito espécies substituídas continuam em outros slots da própria variante: sua chance nominal agregada passa de 70% para 60%, enquanto Type: Null recebe 10%. **Nenhuma espécie anterior foi eliminada da caverna.** Shroodle, Trubbish, Buzzwole, Munchlax e todos os demais slots não selecionados permanecem idênticos.

São **oito registros de quatro bytes**, com **30 bytes efetivamente diferentes**: no registro de Houndour, os dois bytes de nível já eram 20. Não há código executável, hook, payload ou reserva nova. Ao restaurar esses oito registros com os bytes da V40, a ROM inteira volta a ser idêntica à V40.

### Preservado

- As nove escolhas de variante e a própria VAR 0x4024; nenhuma migração/reescrita de save.
- Frequência de encontro da caverna, todos os outros slots e todos os outros mapas.
- As **931 espécies não lendárias/míticas** da cobertura anterior.
- Objetos fixos adicionais, objetos estacionados, sete eventos lendários nativos e tabelas de evolução.
- As **68 áreas noturnas**, política e tabelas noturnas, guia completo, menus, relógio, MUNDO e preferências. Esta não é uma expansão para 69 áreas.
- Flags, bilhetes, puzzles, NPCs, mapa, colisões, gráficos e código de captura/save.

## Validação: 15/15 métodos aprovados

**84,083 s**, sem falhas, erros ou skips: **8 testes estruturais + 7 testes no mGBA**.

### Estrutura e reconstrução

- SHA-256 exato da entrada e saída; reconstrução byte a byte idêntica.
- Rejeição de ROM truncada, alterada, V41 como entrada, destino existente e aliases por link simbólico.
- Diferenças confinadas a oito registros, 30 bytes modificados, nenhum byte adicional.
- Todas as espécies de cada variante preservadas; um único slot de Type: Null por variante, sempre nível 20 e 10% nominal.
- Variante 7, demais mapas, eventos nativos/adicionais, evolução, tabelas noturnas e guia inalterados.
- [CSV completo da caverna](encontros_altering_cave_v41.csv), **108 linhas**: nove variantes × doze slots.

### Contratos nativos no emulador

- **2.200 sorteios determinísticos**: 100 quantis × dia/noite × nove variantes, mais os valores inválidos 9 e 65535. Cada grupo de 100 gerou Type: Null exatamente dez vezes, com espécie/nível/checksum corretos. Isso testa a seleção de slots, **não mede frequência de encontros em caminhadas aleatórias**.
- Repel bloqueia Type: Null de nível 20 diante do Pokémon sintético de nível 100; geração sem o filtro continua correta, nas nove variantes e nos dois períodos.
- **272 consultas** aos seletores das 68 áreas anteriores, nos limites 05:59/06:00 e 19:59/20:00, preservando RNG e save nesses contratos.
- Regressões de Cosmog/Cosmoem: níveis 43, 53 e 54, prioridade das evoluções e Everstone, de dia/noite; regras simplificadas da base preservadas.
- Regressão de Tanoby: Cresselia continua bloqueada pelo header com flag 0x849 desligada e é gerada como Cresselia quando ligada.

### Caminhada, captura e save — na ROM exata

Foi criado um jogo **sintético** numa cópia descartável com um warp de preparação. A chegada à caverna foi salva pelo jogo; apenas a **flash normal** foi carregada na V41 exata por Continuar. **O warp não existe na ROM entregue. Nenhum savestate atravessou versões.**

Após essa chegada, na variante padrão 0:

1. Hora, Repel desligado e uma Master Ball de teste foram preparados no estado sintético, antes da caminhada.
2. A partir daí, a caminhada, encontro e captura usaram botões normais, **sem injetar Pokémon, sorteio ou resultado de captura**.
3. Type: Null nível 20 apareceu e foi capturado tanto de dia quanto à noite.
4. Foram verificados personalidade, checksum, nível, metadado da bola, consumo da bola e preservação do Pokémon inicial.
5. O save normal foi carregado em um core novo com V40, salvo novamente e carregado em outro core com V41: **V41 → V40 → V41**, preservando o Pokémon capturado, a equipe, o local e o consumo da bola. O contador dos setores de save foi verificado: avançou de 2 para 3 na V40, comprovando uma nova gravação, não apenas releitura da mesma flash.

A Master Ball torna a captura determinística; não é certificação da taxa de captura com Poké Balls comuns. A caminhada/captura foi testada na variante padrão, enquanto todas as variantes passaram pelas chamadas de geração. Não foi percorrido o caminho natural desde o início da campanha até a Ilha 6.

Duas telas da batalha foram conferidas visualmente: `telas/TYPE_NULL_600_BATALHA.png` e `telas/TYPE_NULL_1320_BATALHA.png`. Ambas mostram Type: Null no nível 20. A aparência diurna/noturna igual da batalha em caverna é esperada; o período também foi controlado/verificado nos testes.

Os 103 métodos históricos da V40 **não foram reexecutados nem somados** a esses 15. A auditoria estrutural de preservação e as regressões focadas acima são o escopo desta rodada.

## O que continua pendente entre os 1.025

A dependência exclusiva da variante 7 para **Type: Null está resolvida na V41**. A auditoria V40 (`docs/AUDITORIA_OBTENCAO_V40.md`) permanece um registro histórico, não uma descrição atualizada desse encontro na V41.

Continuam pendentes: acesso normal/bilhetes e captura dos eventos de **Lugia, Ho-Oh e Deoxys**; cenas de evolução e segunda cópia/repetição de **Cosmog** para Solgaleo e Lunala no mesmo save; desbloqueio natural de Tanoby e validação de outros acessos/capturas. Esta correção **não transforma o levantamento estrutural de 1.025 espécies em certificação de campanha completa**.

## Arquivos e reprodução

- `scripts/motor_v41.py`: builder estrito, sem sobrescrever a entrada/saída existente.
- `tests/test_motor_v41.py`: oito testes estruturais.
- `tests/test_motor_v41_mgba.py`: sete métodos de contratos/fluxo real, apenas dados sintéticos.
- [Resultados](validacao_v41_resultados.json), [log](validacao_v41.log), [observações](sondagens_v41.json) e [CSV](encontros_altering_cave_v41.csv).

Da raiz do repositório:

```sh
python3 -B firered_gen1_9/scripts/motor_v41.py \
  --rom deliver/v40/FireRed_Gen1-9_motor_v40.gba \
  --saida deliver/v41-nova/FireRed_Gen1-9_motor_v41.gba
```

Para testes, exporte `MOTOR_V41_BASE`, `MOTOR_V41_ROM` e `MGBA_CORE` com caminhos absolutos. Opcionalmente, `MOTOR_V41_OBSERVATIONS` aponta para um arquivo novo e `MOTOR_V41_SCREENS` para a pasta de capturas. Use o ambiente com as dependências do harness/mGBA/Pillow:

```sh
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests python3 -B -m unittest -v \
  test_motor_v41.MotorV41BuildTests \
  test_motor_v41_mgba.MotorV41NativeTests
```

ROM de saída: **33.554.432 bytes**.

- V40 / entrada: `10214ba64a38a543d381db9d41eb37f46458a0926057d028dda2839b1f87e7e1`.
- **V41 / saída:** `662225325c50af5aeb568da97a10110cff300aff55e1a6ec87f0d11c1a5f5d50`.
- mGBA 0.10.5, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`, core SHA-256 `07ab56ae80ed30486eff67ab4907b345f46ebb5e60f47f98869dc534df18dad9`.

**Faça backup do save normal e use Continuar. Não use savestates de outra versão.** Os testes sintéticos não garantem todos os saves pessoais/emuladores. Não misture este projeto Gen1–9 com FireRed BR/BAG_MOD. Entrega local, sem publicação no Drive, commit ou push; ROMs, saves e telas ficam fora do Git.
