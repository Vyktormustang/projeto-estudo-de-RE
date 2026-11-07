# Motor v22 — encontros por horário em 12 áreas

Expansão sobre a **v21 exata**, FireRed Gen1–9, 32 MiB. Acrescenta **Rotas 5, 6, 7 e 8**, sem modificar as oito áreas anteriores. Não é a variante FireRed BR/BAG_MOD.

## Novas distribuições

| Área | Grupo/mapa | Slot 2: dia → noite | Nível | Slot 3: dia → noite | Nível |
|---|---|---|---:|---|---:|
| Rota 5 | 3/23 | Smoliv → **Skitty** | 13 | Swoobat → **Munna** | 12 |
| Rota 6 | 3/24 | Metang → **Poliwag** | 13 | Sunflora → **Volbeat** | 12 |
| Rota 7 | 3/25 | Exploud → **Misdreavus** | 19 | Altaria → **Stunky** | 18 |
| Rota 8 | 3/26 | Charcadet → **Illumise** | 16 | Alcremie → **Dedenne** | 20 |

Índices de slot zero-based. Cada substituição ocupa **10% nominal**, antes de Repel/filtros. Os outros **80%**, os níveis e a frequência nativa de tentativas são preservados. As quatro áreas têm `mapType=3` e taxa terrestre nativa 21 nesta ROM.

São escolhas de design, **não tabelas oficiais de Scarlet/Violet** nem declarações universais sobre hábitos das espécies. Foram escolhidas espécies comuns, sem lendários, míticos, Ultra Beasts ou Paradox. Preservar níveis não significa manter dificuldade idêntica: os atributos, tipos e repertórios diferem. Não houve simulação completa do balanceamento da campanha.

### Áreas anteriores preservadas

Rotas **1, 2, 22, 3, 4, 24 e 25**, mais a **Floresta de Viridian**. Os 16 slots noturnos da v21, seus níveis e chances permanecem iguais; o teste também compara as criações/RNG contra o wrapper v21 preservado.

### Regras de período

- **Dia: 06:00–19:59:** tabelas anteriores intactas em todos os mapas.
- **Noite: 20:00–05:59:** duas substituições terrestres por área nas 12 áreas.
- Relógio herdado: **24 minutos jogados = um dia virtual**, sem RTC nem tempo offline.
- Não foi criado um HUD HH:MM.
- **Limite herdado:** em 999:59:59 jogados, o contador nativo satura e a hora derivada para em **07:59**. Esta expansão não corrige esse limite.

A [política](../data/encontros_horario_v22.csv) contém **24 substituições**, oito novas. O [guia completo](guia_encontros_horario_v22.csv) contém **288 linhas de slots**, além do cabeçalho: 12 áreas × dois períodos × 12 slots. As primeiras 192 linhas de dados são idênticas às da v21.

## Placa e exclusões

A placa **Pallet–Viridian da Rota 1** mantém as direções originais e lista as 12 áreas. O período é consultado quando o guia abre; não é atualizado continuamente enquanto se lê. O texto usa páginas nativas de duas linhas, até 32 caracteres por linha.

Sem novas recompensas, flags permanentes, missões ou agendas de NPCs. Surf, pesca, Rock Smash, cavernas, encontros especiais e outros mapas não recebem novas regras. Eventos fixos, scripts de história e treinadores permanecem fora dos intervalos alterados. Não há exclusividade global das espécies noturnas: elas podem aparecer em outros mapas e de dia. Gritos ambientes continuam com o seletor anterior.

## Implementação e segurança

Mesmo desenho da v21: o hook antes do sorteio troca somente o ponteiro de informações terrestres quando **ponteiro original + grupo/mapa + noite** correspondem a uma entrada cadastrada. A criação, níveis, flags e Repel permanecem nativos. Sem chamada extra ao RNG, novo campo de save ou reserva global de RAM.

O array agora tem **12 descritores**, em `090E3000`. O código e todas as tabelas/textos antigos permanecem intactos na ROM. O trampoline repete o prólogo **nativo** `f0b54746ce460906` e retorna em `08164349`; não repete o veneer v21.

| Offset ROM | Bytes | Finalidade |
|---|---:|---|
| `164340` | 8 | Hook para wrapper v22 |
| `7C20D8` | 4 | Ponteiro da placa |
| `10E2000` | 300 | Payload próprio |
| `10E3000` | 816 | 12 descritores e 12 tabelas noturnas |
| `10E3400` | 42 | Script informativo |
| `10E3500` | 1094 | Textos próprios dos dois períodos |

Reserva validada até `10E4000`. Entradas Thumb: seletor `090E2001`, encontro `090E2009`, período `090E2011`, placa `090E2019`; trampoline `090E2021`. Relógio em `090DD001`, inalterado. A placa escreve somente o `VAR_RESULT` temporário 800D pelo `VarSet` nativo.

Informações terrestres originais verificadas nesta ROM: Rota 5 em `7B6B50`, Rota 6 em `7B6B88`, Rota 7 em `7B6C0C`, Rota 8 em `7B6C44` (offsets ROM). Não foram transplantados offsets de vanilla ou BAG_MOD.

O builder rejeita versão errada, política/payload divergentes, reserva ocupada e preimagens incompatíveis. Exige os 16 slots anteriores inalterados; impede duplicar a espécie substituta nos slots mantidos do mesmo mapa, para não transformar uma entrada de 10% em uma chance agregada maior. A saída é exclusiva e o hash final é obrigatório. Não é um editor genérico de CSV.

## Identidade e aplicação

| Artefato | SHA-256 |
|---|---|
| Entrada v21, 33.554.432 B | `cfbcebd0bf3ab0c1cbcb9872bc400f62d9c807fbd67dd99b4b89ffb16c92a10f` |
| Payload, 300 B | `40218172b834b8aa6e453f98b007b8c299ba0aa4a793e144c616a2fa62fd28a4` |
| Política CSV | `a58be95bd5122e40f0ac5dedeaa0ac14ba25720a7f8699ecb8df6f61b47ce61a` |
| Saída v22, 33.554.432 B | `0e9f9d901d6d411a02d992e5b9f483f5729880dd07d169c868d5d4862309f90f` |

```sh
python3 firered_gen1_9/scripts/motor_v22.py \
  --rom /privado/motor_v21.gba --saida /privado/motor_v22.gba
```

Recompilação do payload com Zig 0.17.0:

```sh
python3 -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi \
  -mthumb -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v22/payload.ld \
  firered_gen1_9/patches/motor_v22/entry.s \
  firered_gen1_9/patches/motor_v22/motor_v22.c -o /tmp/v22-rebuilt.elf
python3 -m ziglang objcopy -O binary /tmp/v22-rebuilt.elf /tmp/v22-rebuilt.bin
cmp /tmp/v22-rebuilt.bin firered_gen1_9/patches/motor_v22/payload.bin
```

## Validação

**46 métodos selecionados aprovados em 317.741 s, sem failures, errors ou skips**, na v22 exata. Payload recompilado independentemente e comparado byte a byte; ROM reproduzida integralmente pelo builder. **Manifesto atual: 313/313 entradas verificadas**, excluindo o próprio manifesto. Os IDs e hashes dos logs estão em `validacao_v22_resultados.json`.

Seleção final de **46 métodos**, não somada aos resultados históricos:

- **8 build/dados:** SHA, saída exclusiva, corrupção/reaplicação, seis intervalos, tabelas originais/guia reproduzíveis e preservação das oito áreas anteriores.
- **8 encontros/placa:** limites de horário, mapas/métodos, ponteiros, RNG, ABI, Repel, exclusões, leitura completa da placa e encontros por movimentação.
- **12 horário/evoluções/paletas:** limites e saturação, save/reload, evolução real Espeon/Umbreon e preservação de UI/interiores/batalhas, conforme o recorte herdado.
- **9 EV/IV:** edição, limites, cancelamento, integridade e contextos inseguros na v22 identificada.
- **5 gameplay:** os quatro métodos de captura/persistência, Poké Ball, fuga e percurso Pallet↔Rota 1, mais **migração de flash sintética v21 → v22**.
- **4 batalhas selecionadas:** vitória natural, subida 10→11, bloqueios sonoros nativos, histórico Soundproof e ação seguinte.

### Cobertura dos encontros

**100 resultados do sorteio × 12 áreas × dois períodos = 2.400 casos determinísticos**, verificando espécies, níveis, checksums e SP/registradores. Comparação diurna com o caminho nativo e dos **800 casos noturnos anteriores** com o wrapper v21 preservado. Isso não é medição de frequência em caminhadas aleatórias.

O controle fora do recorte inclui água das Rotas 22, 4, 24, 25 e **6**, além da terra da **Rota 9** e da caverna Mt. Moon. Pesca e outros scripts continuam preservados por bytes/escopo, sem prometer que toda a interação de cada método foi percorrida pela UI.

Nas Rotas 5–8, cópias descartáveis da ROM alteram somente o ponteiro da placa e dez bytes de script para transportar o jogador. O terreno é derivado da ROM e confirmado pela rotina nativa (`LAND=1`); os encontros depois da chegada usam apenas espera e botões. As oito novas espécies precisam aparecer, com níveis/checksums corretos e flag de batalha selvagem. **Esse warp não está na ROM entregue**, e não comprova a travessia da campanha até as rotas.

### Placa: teste corrigido e fortalecido

A primeira rodada de 45 métodos teve uma falha no teste de devolução do controle: 60 pulsos cegos de A terminavam o guia e reabriam a placa; o orçamento posterior de B era insuficiente para encerrar outra leitura. A sondagem encontrou o cursor nativo avançando normalmente, não um travamento do jogo. A ROM não foi alterada para resolver essa falha do teste.

O teste final observa o `TextPrinter` efetivo desta ROM, em **0203EAF0** (`currentChar` em +0, `active` em +27), lendo o texto em **0203E6C4**. Para no terminador, exige avanço além da última linha nova, fecha uma vez e prova movimento do jogador. Portanto, não basta encontrar o texto completo copiado na RAM. Os endereços foram observados no emulador; o layout foi confrontado com `include/text.h`/`src/text.c` do pret/pokefirered, commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`.

### Save e limites das regressões

A migração cria um jogo novo na v21 exata, prepara sete Poké Balls e horário noturno, salva pelo jogo, fecha o core e carrega somente a **flash nativa de 131.072 B** em uma instância v22. Confere equipe, item, mapa, callback e continuidade do horário. **Não carrega savestate v21 na v22** e não usa save pessoal. Isso é um caso sintético dirigido, não garantia sobre todo save externo/corrompido.

As capturas desta rodada usam Magby, Hoothoot e Nickit na Rota 1, incluindo Master Ball, Poké Ball, campo de bola utilizada e persistência após reinício. Não são testes estatísticos de captura nem cobrem caixa cheia/todas as espécies. A progressão testada é inicial, não a campanha inteira.

**Não foram reexecutados os 68 métodos da auditoria v21**, nem toda a suíte histórica de trocas/hazards em duplas. Os testes de batalha escolhidos e os bytes preservados não certificam fidelidade integral a Scarlet/Violet, link/multi ou hardware real.

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V22_BASE=/privado/motor_v21.gba
export MOTOR_V22_ROM=/privado/motor_v22.gba
export TREINO_TEST_ROM="$MOTOR_V22_ROM"
export MGBA_CORE=/privado/mgba_libretro.so  # mGBA 0.10.5
python3 -m unittest test_motor_v22 test_motor_v22_mgba test_treino_ev_mgba \
  test_motor_v22_gameplay_mgba test_motor_v22_regressions -v
```

## Uso e entrega

Faça backup do `.sav` comum. Reinicie o emulador com a ROM nova e, se necessário, use uma **cópia** do save com o mesmo nome-base. Não importe savestate de outra versão. Nenhum save pessoal foi aberto, alterado ou convertido.

ROM e saves não entram no Git. **V22 local; não enviada ao Drive nesta etapa.** O guia e o relatório acompanham a entrega em `deliver/v22/`.
