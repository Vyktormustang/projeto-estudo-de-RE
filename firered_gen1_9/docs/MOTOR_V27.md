# Motor parcial v27 — encontros por horário em 20 áreas

2026-11-05. Base: **FireRed Gen1–9 motor v26 exato**, não FireRed BR/BAG_MOD.

## Expansão

Adicionadas as **Rotas 13, 14, 15 e 16**, preservando integralmente a política das 16 áreas anteriores. Na grama, à noite (20:00–05:59), dois slots nominais de 10% passam a usar:

| Área | Slots (índices zero-based) | Espécies noturnas e níveis |
|---|---|---|
| Rota 13 | **3 e 4** | Drifloon 27 / Murkrow 25 |
| Rota 14 | 2 e 3 | Misdreavus 22 / Sneasel 23 |
| Rota 15 | 2 e 3 | Shuppet 22 / Duskull 27 |
| Rota 16 | 2 e 3 | Meowth 18 / Houndour 20 |

Cada espécie nova ocupa **10% nominal**, antes de Repel e demais filtros. Os outros 80%, os níveis e a frequência nativa de encontros são preservados. De dia (06:00–19:59), as tabelas anteriores continuam intactas. Trata-se de uma distribuição de design deste projeto, não de tabelas oficiais de Scarlet/Violet ou de garantia de equilíbrio equivalente.

### Exceção importante na Rota 13

O slot 2 já contém **Naganadel nível 22, 10%**. Ele **não foi substituído**: nessa rota foram escolhidos os slots 3 e 4, ambos comuns e de 10%. Também preservados:

- **Iron Valiant** na Rota 14: slot 7, nível 30, 5%;
- **Snorlax selvagem** na Rota 15: slot 4, nível 25, 10%;
- **Poipole** na Rota 9: slot 5, nível 14, 10%;
- eventos fixos e scripts de Snorlax e da história, incluindo os bloqueios de acesso das rotas.

O builder rejeita usar espécie protegida na origem ou no destino dos slots substituídos, incluindo Snorlax explicitamente. Não muda scripts de história para liberar áreas: eventuais warps são exclusivos de cópias descartáveis de teste.

## Relógio, painel e saves

O painel **MUNDO HH:MM**, o controle **START → Opções → SELECT**, a preferência persistente e o relógio pós-999:59:59 permanecem os da v26, byte a byte. **Ocultar o HUD não desativa os encontros por período.** Mantidos o ritmo acelerado de aproximadamente 24 minutos jogados/dia, as paletas e evoluções. Sem RTC ou avanço offline.

Não há novo campo no save, migração adicional, recompensa, quest ou flag permanente. CK24 e HUD6 mantêm seus formatos. Faça backup do save normal e use **Continuar**; não reutilize savestates de outra versão. Não misture esta base com o FireRed BR histórico.

A placa da Rota 1 conserva as direções originais e passa a listar as **20 áreas**. O período é consultado uma vez para a parte adicional do guia; se o horário mudar durante a leitura, fechar e reabrir atualiza a informação. O painel se oculta durante a mensagem.

Distribuição completa: [guia CSV](guia_encontros_horario_v27.csv), **480 linhas de slots**, 20 mapas × 2 períodos × 12 slots. Política: `data/encontros_horario_v27.csv`, 40 substituições noturnas. As 32 anteriores e as primeiras 384 linhas do guia são preservadas.

## Integração e integridade

Seis intervalos sobre a v26:

| Offset no arquivo | Tamanho | Conteúdo |
|---|---:|---|
| `164340` | 8 B | Hook do gerador terrestre nativo |
| `7C20D8` | 4 B | Ponteiro da placa da Rota 1 |
| `10EC000` | 300 B | Payload Thumb: seletor, wrapper nativo, período e helper da placa |
| `10ED000` | 1.360 B | 20 descritores e tabelas noturnas |
| `10ED600` | 42 B | Script da placa, preservando a mensagem original |
| `10ED700` | 1.554 B | Textos dia/noite do guia |

Reserva verificada `FF` até `10EF000`. Vetores `090EC001` seletor, `090EC009` encontro, `090EC011` noite e `090EC019` placa. O trampoline nativo continua em `090EC020` e retoma em `08164349`.

O seletor exige área terrestre, ponteiro original correspondente e grupo/mapa corrente corretos. Não sorteia números, cria Pokémon ou altera níveis: devolve o ponteiro da tabela adequada e chama o gerador original, preservando Repel, RNG, seleção de slot, criação e checksums. Água, pesca e áreas não abrangidas não recebem política nova.

Todas as tabelas nativas, os payloads anteriores, os hooks do relógio/HUD/Opções e todos os demais bytes fora desses seis intervalos são preservados. A análise das tabelas nativas antes/depois é idêntica, mantendo a cobertura diurna anterior. Não se reescrevem as localizações da Pokédex para refletir o horário.

Hashes SHA-256:

- Base v26: `ffba283f8d01885f9a8a3d5300135adeae008e6434a7c5c80ec7f695c1445ba7`.
- Payload: `7833d1441ed13cf9e5ba30fdd738e23eda5a4ea64392d7643889c5dcb97f3c66` (300 B).
- ROM v27: `f48ce3b2b4328637d47004722907ca9bfb5b6e523f1ed8a6b1bfbe93fd266673` (33.554.432 B).

## Validação

**85 métodos únicos aprovados: 415.032 s de parede, três processos isolados, zero falhas, erros ou skips.** Veja [resultados](validacao_v27_resultados.json) e [log integral](validacao_v27.log). A seleção inclui:

- 10 contratos de build/dados: seis intervalos, slots protegidos, política anterior, tabelas nativas, guia e saída exclusiva;
- 9 de encontros/guia: **4.000 casos determinísticos** (100 quantis × 20 mapas × dia/noite), níveis/checksums/ABI, equivalência às 16 áreas anteriores, Repel, água/caverna fora da política, placa e encontros nas quatro rotas novas;
- fronteiras nas 20 áreas após saturação, com HUD visível e oculto, sem escritas no save pelo seletor;
- 12 de HUD, incluindo os 1.440 horários no formatador e no oráculo de pixels;
- 10 de preferência e flash, 10 do relógio persistente, 11 do relógio/paletas/evoluções anterior;
- 5 de estojo com relógio e preferência oculta ativos, 4 de combate/EXP/Soundproof, 5 de captura/fuga/jornada/flash e 9 de EV.

Os encontros nas novas rotas são exercitados após **warps somente de teste**: uma cópia temporária muda exclusivamente o ponteiro da placa e dez bytes de script de transporte. Terreno e coordenadas são derivados desta ROM e conferidos pela API nativa; em seguida há caminhada normal, sem escrever RNG/espécie/nível durante a ação. Isso não prova a jornada da campanha até essas rotas ou o desbloqueio de todos os portões/HMs.

As provas determinísticas percorrem os 100 quantis nativos, não estimam frequências de 100 caminhadas aleatórias. Os testes de captura comum aceitam falhas naturais e procuram um controle positivo variando somente a espera antes de lançar a bola. O controle de vitória seleciona por caminhada um adversário de nível até 3, sem resistência/imunidade a Tackle; não exige que um inicial vença qualquer inimigo. Nenhuma regra do jogo foi alterada para acomodar esses ensaios.

Somente partidas, estados iniciais e flash sintéticos. Testes de flash cruzam versões por save normal, não por savestate. As rotinas isoladas de relógio usam o vetor v24 preservado; a execução viva usa os hooks atuais. Dois dias do mundo/172.800 frames, TMs/HMs, opções e preferência continuam na seleção, mas não equivalem a campanha completa.

Sem certificação de hardware físico, todos os emuladores, link real, saves pessoais ou fidelidade integral a Scarlet/Violet. Nenhum save pessoal utilizado.

## Reprodução

Zig 0.17.0; mGBA libretro 0.10.5, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`, core SHA-256 `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`.

Na raiz do repositório:

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v27/payload.ld \
  firered_gen1_9/patches/motor_v27/entry.s \
  firered_gen1_9/patches/motor_v27/motor_v27.c -o /tmp/v27.elf
python -m ziglang objcopy -O binary /tmp/v27.elf /tmp/v27.bin
cmp /tmp/v27.bin firered_gen1_9/patches/motor_v27/payload.bin
python firered_gen1_9/scripts/motor_v27.py --rom /caminho/v26.gba --saida /novo/caminho/v27.gba

MOTOR_V27_ROM=/novo/caminho/v27.gba MOTOR_V27_BASE=/caminho/v26.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v27.gba \
python firered_gen1_9/scripts/validar_motor_v27.py --jobs 3 --log /tmp/v27-final.log
```

O runner exige 85 IDs únicos, cores/partidas isolados e nenhuma falha ou skip. O tempo consolidado é de parede. ROM, screenshots e saves/estados ficam fora do Git. Entrega local, sem publicação no Drive, commit ou push.
