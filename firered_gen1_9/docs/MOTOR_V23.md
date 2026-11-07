# Motor v23 — encontros por horário em 16 áreas

Expansão sobre a **v22 exata**, FireRed Gen1–9, 32 MiB. Acrescenta **Rotas 9, 10, 11 e 12**, preservando as 12 áreas anteriores. Não usa a variante FireRed BR/BAG_MOD.

## Novas distribuições

| Área | Grupo/mapa | Slot 2: dia → noite | Nível | Slot 3: dia → noite | Nível |
|---|---|---|---:|---|---:|
| Rota 9 | 3/27 | Gligar → **Sableye** | 11 | Vivillon → **Rockruff** | 15 |
| Rota 10 | 3/28 | Clodsire → **Chingling** | 11 | Wynaut → **Joltik** | 15 |
| Rota 11 | 3/29 | Emolga → **Rattata** | 12 | Linoone → **Scraggy** | 13 |
| Rota 12 | 3/30 | Magmortar → **Noctowl** | 22 | Tangrowth → **Ariados** | 23 |

Índices de slot zero-based. Cada substituição ocupa **10% nominal**, antes de Repel/filtros. Os outros **80%**, os níveis e a frequência nativa de tentativas permanecem iguais. As quatro áreas têm `mapType=3` e taxa terrestre nativa 21 nesta ROM.

São escolhas de distribuição do projeto, **não tabelas oficiais de Scarlet/Violet** nem afirmações universais sobre hábitos das espécies. Não há novos lendários, míticos, Ultra Beasts ou Paradox. Níveis iguais não garantem dificuldade igual: atributos, tipos e repertórios diferem; não foi simulada toda a campanha. Esta alteração não implementa novas evoluções por horário, habilidades ou formas de evolução de Rockruff.

### Protegidos e áreas anteriores

- **Poipole da Rota 9:** o slot 5 original permanece, nível **14**, chance nominal **10%**, de dia e de noite. Não é uma introdução da v23.
- O aplicador agora rejeita uma substituição se a espécie **original ou substituta** for classificada como protegida. Há testes negativos dirigidos para ambos os lados.
- Snorlax e outros eventos de história continuam fora dos intervalos alterados. Isso preserva seus scripts/objetos; **não significa que toda a sequência da Poké Flute/Snorlax foi percorrida nesta rodada**.
- Rotas **1–8, 22, 24 e 25**, mais a **Floresta de Viridian**, conservam seus 24 slots noturnos anteriores. As tabelas e o código v22 permanecem na ROM, permitindo comparação direta.

### Período e guia

- **Dia: 06:00–19:59:** todas as tabelas diurnas anteriores intactas.
- **Noite: 20:00–05:59:** duas substituições terrestres em cada uma das 16 áreas.
- Mesmo relógio herdado: **24 minutos jogados = um dia virtual**, sem RTC ou avanço offline.
- Sem novo HUD HH:MM. Em **999:59:59** jogados, o contador nativo ainda satura e a hora derivada para em **07:59**.

A [política](../data/encontros_horario_v23.csv) contém **32 substituições**, oito novas. O [guia completo](guia_encontros_horario_v23.csv) contém **384 linhas de slots**, além do cabeçalho: 16 áreas × dois períodos × 12 slots. As primeiras 288 linhas de dados coincidem com o guia v22.

A placa **Pallet–Viridian da Rota 1** mantém as direções e passa a listar as 16 áreas. O período é consultado ao abrir; não é um mostrador contínuo. Páginas nativas de duas linhas, até 32 caracteres por linha; textos diurno/noturno de **664/666 bytes**, incluindo terminadores.

## Exclusões e desenho técnico

Sem missões, recompensas, flags permanentes ou agendas de NPCs. Surf, pesca, Rock Smash, cavernas, outros mapas e encontros especiais não recebem novas regras. Não há exclusividade global das espécies noturnas. Gritos ambientes continuam com a seleção anterior.

O wrapper troca somente o ponteiro das informações terrestres quando **ponteiro original + grupo/mapa + noite** correspondem a uma das 16 entradas. Sorteio do slot, nível, flags, Repel e criação do Pokémon continuam nativos. Nenhuma chamada extra ao RNG, reserva global de RAM ou novo campo de save.

O trampoline repete o prólogo nativo `f0b54746ce460906` e retoma em `08164349`, sem executar novamente o veneer anterior. O relógio continua em `090DD001`; o guia usa somente o `VAR_RESULT` temporário 800D, pelo `VarSet` nativo.

### Seis intervalos de escrita

| Offset ROM | Bytes | Finalidade |
|---|---:|---|
| `164340` | 8 | Hook para wrapper v23 |
| `7C20D8` | 4 | Ponteiro da placa |
| `10E4000` | 300 | Payload próprio |
| `10E5000` | 1088 | 16 descritores e 16 tabelas noturnas |
| `10E5500` | 42 | Script informativo |
| `10E5600` | 1330 | Textos próprios |

Reserva livre conferida até `10E6000`. Entradas Thumb: seletor `090E4001`, encontro `090E4009`, período `090E4011`, placa `090E4019`; trampoline `090E4021`.

Informações terrestres originais, offsets ROM: Rota 9 `7B6C7C`, Rota 10 `7B6CB4`, Rota 11 `7B6D38`, Rota 12 `7B6DBC`. Os endereços são desta ROM identificada, não transplantados de vanilla.

O teste restaura os seis intervalos e exige igualdade integral com a entrada. O builder verifica hashes, preimagens, reserva livre e tamanho dos blocos; preserva a política anterior e impede duplicação de substitutos em slots mantidos do mesmo mapa. Não é um editor genérico de CSV. A gravação de saída é exclusiva, incluindo proteção contra aliases por symlink/hardlink.

## Identidade e reprodução

| Artefato | SHA-256 |
|---|---|
| Entrada v22, 33.554.432 B | `0e9f9d901d6d411a02d992e5b9f483f5729880dd07d169c868d5d4862309f90f` |
| Payload, 300 B | `7fc67b5ac6e1167d1fe22358e39727c08cc7696bb8b83f77bd8fa8fb6ffc1176` |
| Política CSV | `3f9f693276da415f70697d0e09aef6a5f0d2a028f57d27a9aed2a1e6dc8602c0` |
| Saída v23, 33.554.432 B | `e7de31338f37b22995734d2f855aef82d965c348a83609606f8f2f08d42ba361` |

```sh
python3 firered_gen1_9/scripts/motor_v23.py \
  --rom /privado/motor_v22.gba --saida /privado/motor_v23.gba
```

Payload compilado com Zig **0.17.0**, recompilado independentemente e comparado byte a byte. A ROM também foi reproduzida integralmente pelo builder.

```sh
python3 -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi \
  -mthumb -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v23/payload.ld \
  firered_gen1_9/patches/motor_v23/entry.s \
  firered_gen1_9/patches/motor_v23/motor_v23.c -o /tmp/v23-rebuilt.elf
python3 -m ziglang objcopy -O binary /tmp/v23-rebuilt.elf /tmp/v23-rebuilt.bin
cmp /tmp/v23-rebuilt.bin firered_gen1_9/patches/motor_v23/payload.bin
```

## Validação

**47 métodos selecionados aprovados em 346.658 s, sem failures, errors ou skips**, na v23 exata. **Manifesto: 326/326 entradas verificadas**, excluindo o próprio manifesto. IDs dos métodos, hashes e identificação do ambiente estão em `validacao_v23_resultados.json`.

Seleção de **47 métodos**, sem somar sondas ou rodadas históricas:

- **9 build/dados:** identidade, corrupção/reaplicação, saída exclusiva, seis intervalos, tabelas/guia, preservação das 12 áreas anteriores e proteção de Poipole/espécies protegidas.
- **8 encontros/placa:** mapas, métodos, limites de horário, ponteiros, RNG, ABI, Repel, exclusões, leitura completa do guia e encontros por caminhada.
- **12 horário/evoluções/paletas:** recorte herdado, incluindo save/reload, saturação, evoluções reais de Espeon/Umbreon e paletas de campo/UI/interiores.
- **9 EV/IV:** edição, limites, cancelamento, integridade e contextos inseguros na saída identificada.
- **5 gameplay:** captura/persistência, Poké Ball comum, fuga, trajeto Pallet↔Rota 1 e migração de flash sintética **v22→v23**.
- **4 regressões de batalha:** vitória natural, subida 10→11, bloqueios sonoros nativos, histórico Soundproof e ação seguinte.

### Encontros e proteção

**100 resultados do sorteio × 16 áreas × dois períodos = 3.200 casos determinísticos.** Verificação de espécies, níveis, checksums e SP/registradores; comparação diurna com o caminho nativo e de **1.200 casos noturnos das 12 áreas anteriores** com o wrapper v22 intacto. O Poipole preservado também aparece nas verificações por slot. Isso não estima frequências de caminhadas aleatórias.

Controles fora do recorte: água das Rotas 22, 4, 24, 25, 6, **10, 11 e 12**, terra da **Rota 13** e caverna Mt. Moon. Pesca e outros scripts permanecem por preservação de bytes/escopo, sem afirmar que todos seus fluxos de UI foram percorridos.

Para alcançar as Rotas 9–12, o teste altera somente o ponteiro da placa e dez bytes de script em **cópias descartáveis**. O terreno é derivado desta ROM e conferido pela rotina nativa (`LAND=1`); depois do warp, os encontros usam apenas espera e botões. As oito novas espécies devem aparecer, com níveis/checksums corretos e flag de batalha selvagem. **O warp não está na ROM entregue**. Isso não valida a travessia de obstáculos nem a progressão até essas rotas.

### Placa e saves

A leitura da placa acompanha o cursor real do `TextPrinter` em `0203EAF0` (`currentChar` +0, `active` +27), com texto em `0203E6C4`, endereços observados e validados na ROM expandida. Exige chegar ao terminador e passar pela linha da Rota 12; fecha uma única vez e verifica movimento do jogador. Encontrar a string inteira na RAM, por si só, não seria prova de leitura. Mantém a correção de teste introduzida na v22 para não reabrir a placa com pulsos cegos de A.

A migração cria um jogo novo na v22 exata, prepara sete Poké Balls e horário noturno, salva pelo menu e carrega somente a flash nativa de **131.072 bytes** em um core v23 novo. Confere equipe, item, mapa, callback e continuidade do horário. Não importa savestate entre versões nem usa save pessoal; não garante recuperação de saves externos/corrompidos.

Capturas e persistência desta rodada usam Magby, Hoothoot e Nickit na Rota 1, com Master Ball e um controle de Poké Ball comum, incluindo metadado de bola. Não são estatísticas de captura nem testes de todas as espécies ou PC cheio. A progressão coberta é inicial, não a campanha inteira.

### Comando

mGBA libretro **0.10.5** (upstream `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`), Python com NumPy/Pillow:

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V23_BASE=/privado/motor_v22.gba
export MOTOR_V23_ROM=/privado/motor_v23.gba
export TREINO_TEST_ROM="$MOTOR_V23_ROM"
export MGBA_CORE=/privado/mgba_libretro.so
python3 -m unittest test_motor_v23 test_motor_v23_mgba test_treino_ev_mgba \
  test_motor_v23_gameplay_mgba test_motor_v23_regressions -v
```

Não foram reexecutados os 68 métodos da auditoria v21 nem toda a suíte histórica de trocas/hazards em duplas. Testes sintéticos e preservação de bytes não certificam fidelidade integral a Scarlet/Violet, campanha completa, link/multi ou hardware real.

## Uso e entrega

Faça backup do save comum. Reinicie com a ROM nova e, se o emulador exigir, use uma **cópia** do save com o mesmo nome-base. Não carregue savestate de outra versão. Nenhum save pessoal foi aberto ou modificado.

ROMs/saves não entram no Git. **V23 local; não enviada ao Drive nesta etapa.** Relatório, política, guia, resultados e log acompanham a entrega em `deliver/v23/`.
