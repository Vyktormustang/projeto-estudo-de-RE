# Motor v19 — horário acelerado, iluminação externa e evoluções

Implementação sobre **v18 exata** do FireRed Gen1–9 expandido. Não usa RTC, hora do computador ou tempo offline. Não utiliza offsets da ROM histórica FireRed BR/BAG_MOD.

## Comportamento

- Hora lógica inicial **08:00** quando o contador de jogo é zero.
- **Um segundo do contador nativo = um minuto virtual**; um ciclo completo leva **24 minutos jogados**. O contador nativo avança a cada 60 ticks de jogo; fast-forward acelera também o relógio.
- Continua em mapas, menus e batalhas enquanto o jogo roda. Emulador pausado/fechado não avança. Salvamento comum preserva o horário por meio do tempo de jogo; carregar um estado restaura também o tempo daquele estado.
- Saves anteriores **não reiniciam às 08:00**: a hora é calculada a partir do tempo já acumulado. Não há migração nem escrita em campos novos do save.
- **Não inclui mostrador HH:MM na tela.** A indicação visual desta etapa é a iluminação do cenário; o campo TEMPO existente continua mostrando tempo de jogo, não a hora virtual.

Fórmula: `minuto_do_dia = (480 + horas_jogadas*3600 + minutos_jogados*60 + segundos_jogados) % 1440`.

### Períodos e cores

| Período | Intervalo virtual | Ganhos RGB, denominador 32 |
|---|---|---|
| Noite | 20:00–05:59 | 18 / 20 / 28 |
| Amanhecer | 06:00–07:59 | 29 / 27 / 28 |
| Dia | 08:00–17:59 | 32 / 32 / 32 — sem alteração |
| Entardecer | 18:00–19:59 | 30 / 25 / 25 |

As transições são discretas, não interpoladas. Somente os terrenos externos de cidades, vilas, rotas e mar recebem a tonalidade. Cavernas, interiores, áreas subaquáticas e outros tipos permanecem nativos. Paletas de interface e sprites também permanecem nativas: **não é uma simulação de iluminação global de todos os objetos**.

O efeito opera nos slots BG 0–12 do hardware, depois da cópia nativa da paleta, sem modificar os buffers fonte. Slots BG 13–15 e todas as paletas OBJ ficam intactos. Não acumula escurecimento entre frames. Respeita transferência desabilitada e suspende a tonalidade durante fades ativos; durante uma transição pode aparecer brevemente a cor nativa. A paleta já processada pelo jogo/clima é a fonte, mas não foi auditada cada combinação meteorológica de cada mapa.

### Efeitos mecânicos implementados

Para evoluções por nível, **dia mecânico = 06:00–19:59; noite = 20:00–05:59**. Não é uma promessa de reproduzir calendários de todos os jogos oficiais.

| Pokémon | Regra desta versão |
|---|---|
| Eevee → Espeon | Subir nível, amizade ≥220, de dia, sem golpe classificado como Fairy na tabela ativa |
| Eevee → Umbreon | Subir nível, amizade ≥220, à noite, sem golpe classificado como Fairy na tabela ativa |
| Eevee → Sylveon | Amizade ≥220 e golpe Fairy conhecido têm prioridade sobre os dois caminhos acima |
| Budew → Roselia | Condição nativa de amizade por nível, agora apenas de dia |
| Riolu → Lucario | Condição nativa de amizade por nível, agora apenas de dia |

Everstone permanece bloqueando, inclusive o override nativo da Enigma Berry; ovos e bad eggs não entram nos novos caminhos. Trocas e uso/checagem de pedras passam pelo caminho original, sem restrição horária adicional. Outras espécies continuam no motor anterior.

**Por que tratar Eevee explicitamente:** na entrada v18 os métodos de amizade diurna/noturna existem na tabela, mas seu dispatcher os ignora. Além disso, há uma linha posterior de amizade genérica para Sylveon e uma evolução simplificada por nível para Glaceon, que poderiam sobrescrever o resultado. O wrapper resolve a prioridade do ramo de amizade alta. Com amizade baixa, preserva as simplificações nativas, inclusive Glaceon no nível 36; isso **não** é declarado como regra moderna correta.

O limiar 220 é o nativo preservado, não uma modernização geral para 160. Os tipos de golpes vêm da tabela ativa desta ROM. Baby-Doll Eyes é o ID interno **601** e tem Fairy; Moonblast é **581**, não o número externo 585. Charm ainda aparece como Normal nessa tabela e não foi modernizado aqui. Não foram implementadas todas as evoluções por horário de Gen1–9 (itens noturnos, formas, condições especiais etc.).

## Limite conhecido do contador

**O contador nativo satura em 999:59:59 e para. O relógio derivado também para, em 07:59.** O teste reproduz esse limite; não o mascara nem altera silenciosamente o tempo de jogo. A escolha evita reservar bytes de save sem comprovação de que estejam livres. Uma evolução futura para contador independente precisa de análise do layout persistente e de compatibilidade/migração.

Não há encontros, lojas, NPCs, missões, eventos ou tabelas de encontros por período nesta entrega. Não há configuração de velocidade ou ajuste manual de hora.

## Endereços verificados nesta ROM expandida

Referências de pret foram usadas para reconhecer comportamento, **não para importar offsets vanilla**.

| Elemento | Endereço/offset |
|---|---|
| Ponteiro de SaveBlock2 | `03006F98` |
| Horas/minutos/segundos/ticks | SaveBlock2 `+0E/+10/+11/+12` |
| Estado do contador nativo | `030021D6` |
| Update nativo do contador | `08101664` |
| VBlank de campo, seis chamadas | `080F1E20` |
| TransferPlttBuffer nativo | `080F4264` |
| Paleta unfaded/faded | `020399FC` / `02039DFC` |
| Controle de fade | `0203A2BC` |
| gMapHeader / mapType | `0202750C` / `02027523` |
| GetEvolutionTargetSpecies nativo | `0810DB44` |
| GetMonData / GetItemHoldEffect | `0810A96D` / `080C725D` (Thumb) |
| Tabela ativa de golpes | `09000000`, registros de 12 bytes |
| Tabela de evolução | ROM `6AB6A8`, oito registros de oito bytes por espécie |

O hook do campo reproduz, em ordem, LoadOam, ProcessSpriteCopyRequests, ScanlineEffect_InitHBlankDmaTransfer, FieldUpdateBgTilemapScroll, TransferPlttBuffer e TransferTilesetAnimsBuffer. A tonalidade entra entre as duas últimas chamadas. Não substitui callbacks de batalha/resumo/equipe.

O trampoline de evolução repete os oito bytes substituídos do prólogo, retoma em `0810DB4D` e preserva o frame nativo. O wrapper chama o original antes de aplicar o recorte de horário e preserva qualquer retorno nativo zero, inclusive o hold-effect configurável da Enigma Berry. Testes verificam retorno, SP, registradores callee-saved e integridade do Pokémon.

**Apenas três intervalos de escrita:** ROM `F1E20` (8 bytes), `10DB44` (8 bytes), `10DD000` (776 bytes). Reserva termina em `10DE000`. Nenhum byte fora desses intervalos muda; tabelas de encontros/evolução e payloads de batalha v18 permanecem intactos. Nenhuma nova reserva global de RAM ou save; apenas uso normal da pilha.

## Build e reprodução

| Artefato | SHA-256 |
|---|---|
| Entrada v18, 33.554.432 B | `f9a96edec0f070578dfec3d134dcb6decd5b4a5f7c296fef2c8346d7b9f504b2` |
| Payload v19, 776 B | `6ed02470ba01143bea8f2cf759b0ea8e05a43960db02dc119d8cf5078d38d10f` |
| Saída v19, 33.554.432 B | `b7b8b5636e522e1e3502aa59d1f714d36d955a028d9b988b1fe3f97219fffad1` |

```sh
python3 firered_gen1_9/scripts/motor_v19.py \
  --rom /privado/motor_v18.gba --saida /privado/motor_v19.gba
```

Aplicador verifica tamanho/SHA-256 de entrada e payload, bytes dos hooks, espaço reservado e hash final. Recusa reaplicação, corrupção e sobrescrita, inclusive aliases por symlink/hardlink.

Compilação com Zig **0.17.0**:

```sh
python3 -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi \
  -mthumb -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_minutes \
  -Wl,-T,firered_gen1_9/patches/motor_v19/payload.ld \
  firered_gen1_9/patches/motor_v19/entry.s \
  firered_gen1_9/patches/motor_v19/motor_v19.c -o /tmp/v19-rebuilt.elf
python3 -m ziglang objcopy -O binary /tmp/v19-rebuilt.elf /tmp/v19-rebuilt.bin
cmp /tmp/v19-rebuilt.bin firered_gen1_9/patches/motor_v19/payload.bin
```

## Validação

```sh
export PYTHONPATH=firered_gen1_9:firered_gen1_9/tests
export MOTOR_V19_BASE=/privado/motor_v18.gba
export MOTOR_V19_ROM=/privado/motor_v19.gba
export MGBA_CORE=/privado/mgba_libretro.so  # mGBA 0.10.5
export TREINO_TEST_ROM="$MOTOR_V19_ROM"
python3 -m unittest test_motor_v19 test_motor_v19_mgba test_treino_ev_mgba -v
python3 -m unittest \
  test_motor_v19_regressions.MotorV19BlockedPivotsTests.test_volt_switch_ground_nao_troca_nem_aplica_hazards \
  test_motor_v19_regressions.MotorV19BlockedPivotsTests.test_soundproof_bloqueia_parting_antes_dos_atributos -v
```

**28 métodos selecionados aprovados, sem skips, contra o SHA-256 final:**

| Grupo | Métodos |
|---|---:|
| Build, hashes, intervalos e saída exclusiva | 5 |
| Relógio, paletas, evoluções e fluxos de save/menu/batalha | 12 |
| Treino EV/IV | 9 |
| Volt Switch/Ground e Parting Shot/Soundproof — seis cenários | 2 |
| **Total executado** | **28** |

Execuções separadas de 26 e 2 métodos, sem sobreposição. Os seis outros métodos herdados no módulo de regressão estão disponíveis, mas não foram reexecutados contra a build final e não são contados. Não somar sondas preliminares nem os totais históricos da v18. Payload recompilado independentemente e comparado byte a byte; hashes de entrada, payload e saída reconferidos. Manifesto do pacote: **276/276 arquivos verificados**, excluindo o próprio manifesto.

Cobertura nova: cálculo/viradas/horário de saves antigos; tick nativo de 59→60; saturação; quatro períodos e seus limites; ponteiros/campos inválidos; paletas/fontes/UI/OBJ, repetição e transferência desabilitada; interiores/cavernas/subaquático por tipo; condições de evolução e pedras; progressão real em campo/menu/batalha; ida à equipe e retorno noturno; flash sintético salvo e carregado em core novo; duas evoluções reais por vitória/nível, Espeon e Umbreon, com retorno ao mapa. A execução final de regressão seleciona os dois métodos positivos que cobrem as correções centrais da v18: Volt Switch contra Ground e Parting Shot contra Soundproof, três cenários cada. O módulo disponibiliza também os outros seis métodos herdados, mas eles não integram o total final executado. Treino EV/IV usa somente a saída v19 identificada.

Chamadas diretas a rotinas são testes de contrato, não prova de fluxo inteiro. As duas cenas reais são distinguidas dos testes diretos das outras espécies. Não foi reexecutada toda a campanha, suíte histórica, link/multi ou cada mapa/clima. Não houve teste em hardware físico nem medição de margem de VBlank. Boot isolado não é prova de fidelidade integral a Scarlet/Violet.

As primeiras sondas detectaram erros no teste (ID externo de Moonblast em lugar do interno e bytearray passado ao wrapper ctypes), corrigidos sem alterar o motor para satisfazer um oráculo incorreto. Uma revisão posterior identificou e reproduziu um defeito real na candidata inicial: Eevee ainda evoluía com a Enigma Berry configurada com hold-effect 38 (bloqueio de evolução). A versão final preserva todo retorno nativo zero; o teste cobre esse bloqueio de dia e de noite. A regressão ampla da candidata anterior foi interrompida e descartada do total; somente execuções contra o hash final contam nesta seção.

ROMs, saves e estados fora do Git; apenas fontes, payload próprio, aplicador, testes e documentação versionados. Nenhum save pessoal foi aberto. **V19 gerada localmente; não enviada ao Drive nesta etapa.** Ao usar, faça backup do save comum e reinicie o emulador com a nova ROM; não reutilize savestate de outra versão.

## Referências de reconhecimento

- [pret/pokefirered, play_time.c fixado](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/play_time.c)
- [SaveBlock2](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/include/global.h)
- [Transferência de paletas](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/palette.c)
- [VBlank e mapas](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/overworld.c)
- [Evoluções nativas](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/pokemon.c)
