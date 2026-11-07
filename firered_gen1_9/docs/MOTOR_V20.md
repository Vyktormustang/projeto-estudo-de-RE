# Motor v20 — piloto de encontros noturnos e placa informativa

Base: **motor v19 exato**, FireRed Gen1–9 expandido. Escopo confirmado: Rotas 1, 2 e 22, Floresta de Viridian e informações por período em um ponto do piloto. Nenhum save pessoal usado.

## O que muda no jogo

Usa o mesmo relógio acelerado da v19:

- **Dia: 06:00–19:59** — todas as tabelas anteriores continuam intactas.
- **Noite: 20:00–05:59** — dois slots terrestres de cada área recebem outras espécies.
- **24 minutos jogados = um dia virtual**. Não utiliza RTC ou passagem de tempo offline.
- As duas substituições usam slots nativos de **10% cada**. Os demais **80% da tabela** permanecem iguais, inclusive os slots raros de 1%.

| Área | Slot 2: dia → noite | Slot 3: dia → noite | Nível dos dois slots |
|---|---|---|---:|
| Rota 1 | Magby → **Hoothoot** | Elekid → **Nickit** | 3 |
| Rota 2 | Starly → **Poochyena** | Spinda → **Houndour** | 4 |
| Rota 22 | Pidove → **Murkrow** | Amaura → **Greavard** | 4 |
| Floresta de Viridian | Larvesta → **Spinarak** | Lileep → **Morelull** | 5 |

Índices de slot são zero-based. São escolhas de design deste piloto, **não uma reprodução das tabelas oficiais de Scarlet/Violet ou dos hábitos de todas as espécies**. Uma espécie ainda pode aparecer em outro mapa ou slot fora do recorte; não é exclusividade global de dia/noite.

Níveis, distribuição dos slots e frequência total nativa de tentativas de encontro não são modificados. As porcentagens são **nominais, antes de Repel e outros filtros nativos**; Repel pode impedir um encontro de nível baixo. O wrapper não ignora esses filtros. Os encontros diurnos mantêm a cobertura anterior de espécies comuns; não se eliminam permanentemente os oito Pokémon substituídos à noite.

Política auditável: [`data/encontros_horario_v20.csv`](../data/encontros_horario_v20.csv). Guia completo, **96 linhas de slots** diurnos/noturnos: [`guia_encontros_horario_v20.csv`](guia_encontros_horario_v20.csv). O guia é gerado da entrada exata e comparado em teste; não foi preenchido manualmente.

### Ponto informativo

A **placa existente da Rota 1 com as direções Pallet Town–Viridian City** mantém a mensagem original. Depois, abre o **GUIA DE HORARIOS**, informando:

- se é DIA ou NOITE, calculado quando o guia é aberto;
- os horários de cada período;
- as oito espécies noturnas e suas áreas;
- a chance nominal de cada novo slot e a preservação dos níveis/frequência.

O guia tem páginas de duas linhas e usa a caixa nativa de placas. Pode ser consultado repetidamente. Não concede itens, dinheiro ou recompensas; não cria NPCs, flags permanentes ou mudanças na história. Durante a leitura, o período mostrado é uma fotografia do instante em que o guia abriu; não se atualiza a cada minuto.

## O que permanece fora do recorte

- Surf, pesca, Rock Smash, cavernas e todos os outros mapas permanecem com suas tabelas anteriores.
- Pokémon fixos, lendários, míticos, Ultra Beasts, Paradox e o caminho de roaming não recebem novas restrições horárias.
- Não há missões, lojas, treinadores ou NPCs com agenda nesta etapa: o evento adicionado é **informativo**.
- Os gritos ambientes consultam a seleção local nativa; não receberam uma tabela noturna própria. Não confundir um grito ambiente com um encontro possível no slot substituído.
- Não há mostrador HH:MM permanente ou ajuste de velocidade. O limite da v19 continua: **em 999:59:59 jogados o contador satura e a hora fica em 07:59**. A v20 não remove esse limite nem migra saves.

As quatro áreas têm `mapType=3` nesta ROM e usam a iluminação externa já implementada na v19. A v20 não altera seus hooks de paleta, relógio ou evolução.

## Implementação e endereços confirmados

Reconhecimento por leitura da **ROM expandida exata**, auxiliado por fontes pret fixadas; offsets vanilla não foram transplantados.

### Seleção de encontros

Hook em **`08164340` — TryGenerateWildMon**. Antes do código nativo:

1. Aceita apenas `area == 0` (terrestre).
2. Confere ponteiro de informações original **e** grupo/número do mapa atual em SaveBlock1 `+4/+5`.
3. Consulta `090DD001`, o relógio da v19, sem consumir RNG.
4. Se for noite e uma das quatro combinações cadastradas, usa a cópia noturna em ROM; caso contrário, mantém o ponteiro original.
5. Executa o caminho nativo, preservando argumentos, sorteio do slot/nível, Repel e criação do Pokémon.

O trampoline repete exatamente os oito bytes substituídos (`f0b54746ce460906`) e retoma em **`08164349`**. Registradores callee-saved e SP são verificados nos testes de criação.

Cinco callsites nativos confirmados para essa rotina: ROM `16466C` (terra normal), `1646EE` (água normal), `164786` (Rock Smash), `164810` (Sweet Scent/água), `164838` (Sweet Scent/terra). Água e pedras continuam caindo no caminho original. Pesca usa outro caminho, não interceptado.

| Área | Grupo/mapa | Informações diurnas em ROM | Array original |
|---|---|---|---|
| Rota 1 | 3/19 | `7B6A24` | `7B69F4` |
| Rota 2 | 3/20 | `7B6A5C` | `7B6A2C` |
| Rota 22 | 3/41 | `7B717C` | `7B714C` |
| Floresta | 1/0 | `7B50EC` | `7B50BC` |

Os cabeçalhos selvagens originais em `7B784C` e **todos os seus arrays permanecem intactos**. As cópias noturnas são construídas pelo aplicador a partir da ROM fornecida: não se distribui um dump comercial de tabelas no Git. Nenhuma reserva global de RAM ou campo persistente novo; apenas uso normal da pilha e das estruturas nativas.

### Script informativo

- Apenas o ponteiro da placa em ROM **`7C20D8`** é redirecionado.
- O script original `08190947` continua intacto. O novo script reutiliza sua mensagem original por ponteiro, sem copiá-la para o repositório.
- `callnative` (`23`) consulta o período; `VarSet` nativo em `0808EA15` grava somente **VAR_RESULT `800D`**, temporária em `02021AAC`.
- `compare`/`goto_if` selecionam um de dois textos próprios; `callstd 3` mantém a caixa de placa nativa.
- Nenhuma variável permanente ou flag de missão é reservada para essa consulta.

### Intervalos de escrita

| Offset ROM | Bytes | Conteúdo |
|---|---:|---|
| `164340` | 8 | Hook de geração |
| `7C20D8` | 4 | Ponteiro da placa |
| `10DE000` | 300 | Payload próprio |
| `10DF000` | 272 | Quatro descritores e quatro tabelas noturnas |
| `10DF200` | 42 | Script da placa |
| `10DF400` | 670 | Textos próprios diurno/noturno |

**Seis intervalos, reserva até `10E0000`.** O teste restaura esses intervalos e exige igualdade byte a byte com a entrada. Todo o código/dados de batalha, evolução e horário anterior fora do hook específico permanece igual.

## Hashes e reprodução

| Artefato | SHA-256 |
|---|---|
| Entrada v19, 33.554.432 B | `b7b8b5636e522e1e3502aa59d1f714d36d955a028d9b988b1fe3f97219fffad1` |
| Payload v20, 300 B | `2ca3afe13ff00cb601727ea8a6c83091cec8d6a7a324689edee8cfdb44a639e1` |
| CSV de política | `dda1acd41ce3a2c4c6dae418205e1970c0e524f856eb93962d90d3b3ed15bd7d` |
| Saída v20, 33.554.432 B | `6f22c85769de8fc083b72edd491e185c2baee9ef0fc23f174c25f31d3200ee23` |

```sh
python3 firered_gen1_9/scripts/motor_v20.py \
  --rom /privado/motor_v19.gba --saida /privado/motor_v20.gba
```

O aplicador exige entrada e payload exatos, política CSV identificada, bytes esperados dos hooks, espaço livre e hash final. Recusa corrupção, reaplicação e sobrescrita, incluindo symlinks/hardlinks. Alterar a política exige uma nova build identificada e nova validação; não basta editar o CSV e ignorar os hashes.

Recompilação com Zig **0.17.0**:

```sh
python3 -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi \
  -mthumb -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v20/payload.ld \
  firered_gen1_9/patches/motor_v20/entry.s \
  firered_gen1_9/patches/motor_v20/motor_v20.c -o /tmp/v20-rebuilt.elf
python3 -m ziglang objcopy -O binary /tmp/v20-rebuilt.elf /tmp/v20-rebuilt.bin
cmp /tmp/v20-rebuilt.bin firered_gen1_9/patches/motor_v20/payload.bin
```

## Testes e alcance da evidência

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V20_BASE=/privado/motor_v19.gba
export MOTOR_V20_ROM=/privado/motor_v20.gba
export TREINO_TEST_ROM="$MOTOR_V20_ROM"
export MGBA_CORE=/privado/mgba_libretro.so  # mGBA 0.10.5
python3 -m unittest test_motor_v20 test_motor_v20_mgba test_treino_ev_mgba -v
```

**35 métodos selecionados aprovados, sem skips, contra a v20 exata:** 7 de build/dados + 7 novos de encontros/placa + 12 de horário/evolução/paletas + 9 de EV/IV. Uma execução final, sem somar sondas nem resultados históricos. Payload recompilado independentemente e comparado byte a byte; entrada, política, payload e saída reconferidos. **Manifesto: 286/286 arquivos verificados**, excluindo o próprio manifesto.

Cobertura:

- Sete testes de build/dados: identidade dos artefatos, seis intervalos, proteção de saídas, todas as tabelas originais/cobertura de espécies, layout do script e guia de 96 linhas reproduzível.
- Sete métodos novos no mGBA: limites de horário; seleção por mapa/método; ausência de consumo extra de RNG no seletor; criação nativa para os **100 resultados possíveis do sorteio do slot × quatro mapas × dois períodos**; níveis/checksums/ABI; Repel; água e caverna fora do piloto; variável transitória da placa; placa real em ambos os períodos com retorno ao controle; Hoothoot e Nickit encontrados andando normalmente; entrada nativa de Sweet Scent.
- Doze métodos herdados de horário/evolução/paletas da v19, executados na **v20 exata**: incluem save/reload em core novo e evoluções reais de Espeon/Umbreon, além do bloqueio da Enigma Berry.
- Nove regressões de treino EV/IV na saída v20 identificada.

Os 800 sorteios são **testes determinísticos de contrato**, escolhendo uma semente inicial para cada resultado 0–99. Não equivalem a medir frequências em 800 caminhadas naturais. Nas caminhadas reais foi validada a Rota 1; não se afirma uma campanha completa percorrendo as quatro áreas. Sweet Scent foi testado pela entrada nativa sobre estados de campo/grama alcançados por movimentação, **não por uma sequência completa do menu do golpe**.

A comparação com a criação nativa normaliza somente o preenchimento não especificado **depois do terminador do apelido**. Personalidade, OT, nome visível, dados criptografados, checksum, IVs/EVs/nível/HP e resto da equipe inimiga continuam sendo comparados. O orçamento das chamadas diretas permite até 33 frames: algumas criações nativas de níveis maiores excedem os três frames do helper histórico. Nenhuma expectativa de espécie, nível, Repel ou integridade foi relaxada para ajustar o motor.

As sondas preliminares identificaram limitações dos testes (padding após o nome, orçamento curto, tentativa de Sweet Scent em piso sem grama e fechamento/reabertura da placa). Os oráculos foram corrigidos; não houve mudança de payload para contornar uma falha. Não somar sondas ou totais históricos aos resultados finais.

Não foi reexecutada a suíte histórica completa de batalhas, link/multi, campanha, todos os especiais ou todas as interações de captura. Preservação de bytes e boot não certificam fidelidade integral a Scarlet/Violet.

ROM, saves e estados ficam fora do Git. **V20 gerada localmente, não enviada ao Drive nesta etapa.** Faça backup do save comum antes de usar e reinicie o emulador com a nova ROM; não carregue savestates de outra versão.

## Referências de reconhecimento

- [pret/pokefirered: wild_encounter.c fixado](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/wild_encounter.c)
- [Comandos de script](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/scrcmd.c)
- [Macros de eventos](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/asm/macros/event.inc)
- [Variáveis normais/especiais](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/event_data.c)
- [Relógio e limitações herdadas da v19](MOTOR_V19.md)
