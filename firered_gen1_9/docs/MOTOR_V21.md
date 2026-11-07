# Motor v21 — expansão dos encontros noturnos para oito áreas

Entrada: **v20 exata**, FireRed Gen1–9 expandido, 32 MiB. Acrescenta Rotas **3, 4, 24 e 25** ao piloto, mantendo Rotas 1, 2, 22 e Floresta de Viridian. Nenhuma ROM comercial, save ou estado é incluído no Git.

## Novas áreas

| Área | Slot 2: dia → noite | Nível | Slot 3: dia → noite | Nível |
|---|---|---:|---|---:|
| Rota 3 | Espurr → **Zubat** | 7 | Aipom → **Cleffa** | 7 |
| Rota 4 | Mareanie → **Woobat** | 6 | Doublade → **Noibat** | 10 |
| Rota 24 | Minior → **Purrloin** | 11 | Kecleon → **Drowzee** | 12 |
| Rota 25 | Pincurchin → **Shuppet** | 13 | Mothim → **Duskull** | 14 |

Cada substituição ocupa **um slot nominal de 10%**, antes de Repel/filtros. Os demais 80%, níveis e frequência nativa de tentativas de encontro permanecem iguais. Os índices de slot são zero-based.

Estas são escolhas de design para diversificar a noite, não tabelas oficiais de Scarlet/Violet nem afirmações de hábitos canônicos universais. As oito adições são espécies comuns em estágios iniciais, sem introduzir lendários, míticos, Ultra Beasts ou Paradox. **Níveis preservados não significam dificuldade idêntica:** atributos, tipos e repertórios das novas espécies diferem dos substituídos; não foi feita uma simulação completa de balanceamento da campanha.

### Piloto anterior preservado

| Área | Espécies noturnas mantidas |
|---|---|
| Rota 1 | Hoothoot / Nickit |
| Rota 2 | Poochyena / Houndour |
| Rota 22 | Murkrow / Greavard |
| Floresta de Viridian | Spinarak / Morelull |

A política anterior, os níveis, as chances e os outros dez slots de cada uma dessas quatro áreas são mantidos. Há comparação de dados e da criação nativa de Pokémon/RNG com o wrapper v20 que permanece intacto na ROM.

## Horário e guia

- **Dia: 06:00–19:59.** Todas as tabelas diurnas anteriores continuam intactas, preservando a cobertura anterior de espécies comuns.
- **Noite: 20:00–05:59.** Duas substituições terrestres por área nas oito áreas cadastradas.
- Mesmo relógio da v19: **24 minutos jogados = um dia virtual**, sem RTC ou avanço offline.
- A placa **Pallet–Viridian da Rota 1** mantém as direções originais e passa a listar as oito áreas no guia por período. Não há nova recompensa, NPC ou flag permanente.
- O período do guia é consultado quando ele abre; não é um mostrador HH:MM atualizado continuamente.

A política está em [`data/encontros_horario_v21.csv`](../data/encontros_horario_v21.csv): **16 substituições, das quais oito já existiam**. O [guia completo](guia_encontros_horario_v21.csv) tem **192 linhas de slots** (oito áreas × dois períodos × 12 slots), além do cabeçalho. As primeiras 96 linhas de dados coincidem com o guia v20.

## Fora do recorte

- Surf, pesca, Rock Smash, cavernas, outros mapas e encontros especiais não recebem novas regras.
- Os scripts de história, treinadores, roaming, objetos/eventos fixos e suas condições não foram alterados por esta expansão.
- Não há exclusividade global dessas espécies: elas podem aparecer em outros mapas/slots, inclusive de dia.
- Os gritos ambientes continuam usando a seleção local anterior, não tabelas noturnas próprias.
- Sem HUD HH:MM, alteração de velocidade ou migração de saves.
- **Limite herdado:** em 999:59:59 jogados, o contador nativo e o relógio derivado param; a hora fica em 07:59. A v21 não resolve esse limite.

As quatro novas rotas são `mapType=3` nesta ROM e usam a iluminação externa da v19. Paletas, evoluções e relógio não foram recompilados nem substituídos aqui.

## Implementação

Continua o desenho da [v20](MOTOR_V20.md): o seletor troca somente o ponteiro de informações de encontros terrestres quando **ponteiro original + grupo/mapa + período** correspondem a uma entrada cadastrada. Nenhuma chamada extra ao RNG, cache de período ou novo campo de save.

- `TryGenerateWildMon`, em **08164340**, agora aponta para o wrapper v21.
- O array de descritores passa de quatro para **oito entradas**, em **090E1000**.
- O wrapper chama a criação nativa, mantendo sorteio do slot/nível, flags e Repel.
- O relógio é consultado em **090DD001**, mesma entrada v19.
- A placa continua usando apenas a variável temporária **800D / 02021AAC**, pelo `VarSet` nativo em `0808EA15`.
- O código, tabelas e textos v20 na antiga reserva permanecem intactos; o hook e o ponteiro da placa passam a apontar para a nova reserva.

**Importante para o trampoline:** ele repete o prólogo **nativo** `f0b54746ce460906` e retoma em `08164349`. Não repete o veneer v20 presente na entrada, o que poderia causar reentrada/recursão. Testes verificam os bytes e preservação de SP/registradores callee-saved.

### Novos endereços de tabelas diurnas verificados

| Área | Grupo/mapa | Informações originais, offset ROM |
|---|---|---|
| Rota 3 | 3/21 | `7B6A94` |
| Rota 4 | 3/22 | `7B6ACC` |
| Rota 24 | 3/43 | `7B7284` |
| Rota 25 | 3/44 | `7B7308` |

Não foram importados offsets de FireRed vanilla ou da variante FireRed BR/BAG_MOD. As cópias noturnas são construídas a partir da entrada identificada; os cabeçalhos/arrays selvagens originais permanecem iguais.

### Seis intervalos de escrita

| Offset ROM | Bytes | Finalidade |
|---|---:|---|
| `164340` | 8 | Redirecionar hook v20 → v21 |
| `7C20D8` | 4 | Redirecionar placa |
| `10E0000` | 300 | Payload próprio |
| `10E1000` | 544 | Oito descritores e oito tabelas noturnas |
| `10E1300` | 42 | Script informativo |
| `10E1400` | 878 | Textos próprios diurno/noturno |

Reserva validada até **10E2000**. O teste restaura esses seis intervalos e exige igualdade integral com a v20. Sem nova reserva global de RAM ou bytes persistentes; apenas pilha e estruturas transitórias nativas.

## Hashes e aplicação

| Artefato | SHA-256 |
|---|---|
| Entrada v20, 33.554.432 B | `6f22c85769de8fc083b72edd491e185c2baee9ef0fc23f174c25f31d3200ee23` |
| Payload v21, 300 B | `de85b79a1ffd6aab10ae23448fd1805033b49d4416ba02290048720303d75457` |
| Política CSV | `f1e6bda06ebc3beb451c758865ad1a2ac641e460067926236852de266fc00ddc` |
| Saída v21, 33.554.432 B | `cfbcebd0bf3ab0c1cbcb9872bc400f62d9c807fbd67dd99b4b89ffb16c92a10f` |

```sh
python3 firered_gen1_9/scripts/motor_v21.py \
  --rom /privado/motor_v20.gba --saida /privado/motor_v21.gba
```

Entrada, política e payload identificados por SHA-256; verificação dos hooks anteriores, espaço livre, preservação da política v20 e hash de saída. Recusa reaplicação/corrupção e não sobrescreve arquivos existentes, inclusive aliases por symlink/hardlink. Não se trata de um editor genérico de CSV: mudar a política exige nova build identificada e testes.

Recompilação com Zig **0.17.0**:

```sh
python3 -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi \
  -mthumb -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v21/payload.ld \
  firered_gen1_9/patches/motor_v21/entry.s \
  firered_gen1_9/patches/motor_v21/motor_v21.c -o /tmp/v21-rebuilt.elf
python3 -m ziglang objcopy -O binary /tmp/v21-rebuilt.elf /tmp/v21-rebuilt.bin
cmp /tmp/v21-rebuilt.bin firered_gen1_9/patches/motor_v21/payload.bin
```

## Validação

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V21_BASE=/privado/motor_v20.gba
export MOTOR_V21_ROM=/privado/motor_v21.gba
export TREINO_TEST_ROM="$MOTOR_V21_ROM"
export MGBA_CORE=/privado/mgba_libretro.so  # mGBA 0.10.5
python3 -m unittest test_motor_v21 test_motor_v21_mgba test_treino_ev_mgba -v
```

**37 métodos selecionados aprovados, sem skips:** 8 de build/dados + 8 de encontros/guia + 12 regressões de horário/evolução/paletas + 9 de EV/IV. Uma execução final contra a v21 exata; sondas preliminares e totais históricos não foram somados. Payload recompilado independentemente e comparado byte a byte; entrada, política, payload e saída reconferidos. **Manifesto: 296/296 arquivos verificados**, excluindo o próprio manifesto.

Cobertura da execução final:

- **8 métodos de build/dados:** identidade, seis intervalos, exclusividade de saída, tabelas originais, guia reproduzível, política/slots/antiga reserva v20 preservados.
- **8 métodos de encontros/guia:** limites de horário e mapa/método, guardas de ponteiros, ausência de consumo de RNG pelo seletor, **100 resultados do sorteio × oito áreas × dois períodos = 1.600 criações verificadas**, níveis/checksums/ABI, Repel, água das rotas novas e caverna fora do recorte, placa/controle real, encontros na Rota 1 e nas quatro novas rotas.
- Comparação adicional dos **400 casos noturnos do piloto** com o wrapper v20 preservado; não são contados como 400 métodos adicionais.
- **12 regressões de horário/evolução/paletas** herdadas da v19, executadas na v21 exata, incluindo save/reload e evoluções reais de Espeon/Umbreon, além do bloqueio da Enigma Berry.
- **9 regressões de treino EV/IV**, exclusivamente na saída identificada.

### Encontros nas novas rotas: o que foi instrumentado

Para evitar percorrer novamente toda a campanha, o teste cria uma **cópia descartável** da v21 e muda somente o ponteiro da placa e um script de dez bytes para efetuar um warp. É verificada igualdade com a ROM de produção fora desses dois pequenos intervalos. Isso **não faz parte da ROM entregue**.

O ponto de chegada é obtido do terreno da própria ROM, com vizinhos transitáveis e distância de NPCs. O tipo terrestre é confirmado pela rotina nativa `MapGridGetMetatileAttributeAt` em `080BB808`: atributo 4, máscara `07000000`, deslocamento 24, **LAND=1**. O grupo/mapa e as coordenadas após o warp também são conferidos.

Depois da chegada, cada tentativa usa somente espera e botões de movimento; nenhum Pokémon é injetado e não se edita RAM durante a ação. Os oito novos Pokémon devem ser encontrados, com níveis e checksum válidos. A flag de batalha é verificada para rejeitar um encontro de treinador acidental. Isso comprova a integração dos encontros nos mapas carregados, **não uma caminhada completa pela história até eles**.

Os 1.600 casos de sorteio são contratos determinísticos, não uma medição de frequência em 1.600 caminhadas. O orçamento das chamadas diretas continua em até 33 frames. A comparação de Pokémon normaliza somente bytes não especificados após o terminador do apelido, como na v20; nome visível, personalidade, OT, dados criptografados, checksum e demais campos continuam comparados.

Não foi reexecutada toda a suíte histórica de batalhas, campanha, captura, link/multi, Teachy TV ou todas as combinações de eventos. Boot, preservação de bytes e testes sintéticos não certificam fidelidade integral a Scarlet/Violet. Os procedimentos herdados de Sweet Scent continuam sendo testes da entrada nativa, não uma sequência completa do menu do golpe.

**V21 local; não enviada ao Drive nesta etapa.** Faça backup do save comum e reinicie o emulador com a ROM nova. Não reutilize savestates de outra versão. Nenhum save pessoal foi aberto.

Referências: [v20 e reconhecimento das rotinas nativas](MOTOR_V20.md), [v19 e limites do relógio](MOTOR_V19.md), [política v21](../data/encontros_horario_v21.csv), [guia completo](guia_encontros_horario_v21.csv).

### Rodada posterior de validação

A [validação ampliada de 2026-11-05](VALIDACAO_V21.md) reexecutou os 37 métodos e acrescentou 31, totalizando **68 métodos distintos aprovados sem skips**, sem modificar esta ROM. Os resultados de implementação descritos acima permanecem históricos; o relatório posterior discrimina captura, persistência, progressão curta e regressões de batalha.
