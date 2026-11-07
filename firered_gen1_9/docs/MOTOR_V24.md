# Motor parcial v24 — relógio do mundo após 999:59:59

Data: 2026-11-05. Escopo: FireRed Gen1–9, motor v23 exato como entrada. **Não é o projeto histórico FireRed BR/BAG_MOD.**

## Mudança e limites

O ciclo acelerado do mundo continua depois de o contador nativo atingir **999:59:59**. O indicador de tempo jogado permanece nesse máximo; não passa a exibir 1.000 horas e não contabiliza o total de horas excedentes. A continuidade vale para os consumidores do relógio do projeto: períodos, paletas de campo, encontros por horário, guia e evoluções dependentes de dia/noite.

- Antes do limite, preservada a fórmula `(480 + segundos jogados) mod 1440`.
- Depois dele, 60 quadros ativos avançam um minuto de mundo; 1.440 minutos completam um ciclo. São aproximadamente **24 minutos jogados por dia**, não tempo real do aparelho.
- Continua em campo, menus e batalhas enquanto o contador nativo está ativo. `Stop` pausa; `Start` retoma. Não há avanço offline, RTC, HUD HH:MM nem contador de dias acumulados.
- Dia 06:00–19:59, noite 20:00–05:59. As quatro fases de paleta permanecem iguais.
- **Nenhuma expansão de encontros nesta etapa.** Mantidas as 16 áreas, os 32 slots noturnos, níveis, probabilidades nominais, placa, eventos e exclusões da v23. O [guia v23](guia_encontros_horario_v23.csv) e a [política v23](../data/encontros_horario_v23.csv) continuam válidos.
- Não estende outros sistemas nativos que eventualmente consultem horas jogadas: eles continuam vendo o limite nativo. Não é uma correção universal de todos os temporizadores da ROM.

## Saves existentes e segurança

**Use backup e o save normal do jogo (`.sav`), não savestates entre versões.** Os testes usam exclusivamente jogos novos e dados sintéticos. Nenhum save pessoal foi aberto ou alterado.

1. **Save anterior abaixo do limite:** não muda o formato do horário; o novo registro só é necessário ao saturar. O mundo segue o horário já derivado do tempo jogado.
2. **Save v23 já saturado:** o horário anterior é 07:59. No primeiro tick ativo elegível da v24, a continuação inicia em **08:00**. Não é possível recuperar quanto tempo já havia transcorrido com o relógio antigo travado.
3. **Save v24 com registro válido:** conserva minuto e fração de minuto ao salvar/reabrir. O carregamento e o jogo ativo podem avançar quadros normalmente; não há progresso enquanto o emulador está fechado.
4. **Extensão de TMs ainda não inicializada:** o patch chama a rotina existente de consulta de quantidade do item 375, que já executa a migração validada do estojo. Só grava o relógio depois de reconhecer `T9X1`. **Essa ativação inicial aguarda um campo externo normal** (callback `0x080F172D`, tipos de mapa 1/2/3/6). Evita migrar a mochila temporária do Pokedude ou de contextos de link. Até então o relógio pode continuar em 07:59; o tempo dessa espera não é recuperado. Se `T9X1` já existe, essa restrição não se aplica. Nunca escreve o novo identificador antes da verificação de que os 400 bytes antigos estão livres.
5. **Dados desconhecidos, ponteiros inválidos, identificador alterado, CRC inválido ou campos fora da faixa:** recusa a gravação; não tenta reparar dados desconhecidos. No limite, o relógio pode permanecer em 07:59. Isso é uma limitação deliberada de segurança, não indicação de que o registro foi recuperado.
6. **Reset nativo do tempo:** o leitor ignora o registro quando o contador está abaixo do máximo. Um tick ativo abaixo do limite limpa somente um registro válido e reconhecido, evitando reutilizar uma época anterior. Dados desconhecidos não são apagados por esse mecanismo.

### Retornar à v23

A v23 ignora `CK24`: seu mundo volta a usar o horário nativo saturado, **07:59**, e não avança o novo registro. No ensaio sintético v24→v23→v24, os bytes e itens foram preservados pelo save nativo, e a v24 retomou o registro anterior. **O tempo passado na v23 não é recuperado.** Isso não constitui garantia para outras ROMs, editores, saves corrompidos ou savestates. Manter backups separados por versão continua necessário.

## Implementação

Foi preservado o limite visual porque leitores nativos usam campos e formatação de três dígitos, incluindo caminhos que constroem os dígitos diretamente. Aumentar horas exigiria outra auditoria de interfaces e consumidores não relacionados ao relógio do mundo.

### Reserva persistente compartilhada

A v24 não cria seção de flash nem aumenta o save: usa **8 bytes** dentro da reserva de **400 bytes** do estojo expandido, já salva pelo jogo.

| Região relativa a SaveBlock1 | Uso |
|---|---|
| `+0x34D8`, 4 bytes | Identificador existente `T9X1` |
| `+0x34DC`, 287 bytes | Quantidades compactadas dos 229 IDs modernos; intocadas pelo relógio |
| `+0x3658`, 4 bytes | Identificador do relógio `CK24` (`0x34324B43`) |
| `+0x365C`, 4 bytes | Minuto, quadro e verificação de integridade |
| Fim exclusivo `+0x3668` | Limite da reserva existente |

Palavra de dados: bits 0–10 = minuto 0–1439; 11–16 = quadro 0–59; 17–31 = CRC de 15 bits. Polinômio `0x4599`, semente `0x1D0F`, 17 bits de entrada em ordem MSB-first, sem reflexão ou XOR final. É **verificação de integridade, não autenticação criptográfica**. Minuto/quadro/CRC são publicados em uma única escrita alinhada de 32 bits; na inicialização o identificador é publicado depois dos dados.

O update foi localizado no loop principal, não na IRQ de VBlank. Além disso, a migração a frio é restrita ao campo externo normal. Uma demonstração real do Pokedude confirmou o risco de consultar a mochila temporária; a versão entregue adia a ativação e preserva as TMs legadas após cancelar a demonstração. O leitor não grava nem migra o save. A fonte pret foi usada para entender o fluxo; os endereços foram conferidos por desassemblagem desta ROM expandida, não transplantados da ROM vanilla.

### Alterações na ROM

Somente três intervalos:

| Offset de arquivo | Tamanho | Destino |
|---|---:|---|
| `0x101664` | 8 | Update nativo → `0x090E6009` |
| `0x10DD038` | 8 | Corpo efetivo de `clock_minutes` v19 → `0x090E6001` |
| `0x10E6000` | 870 | Payload próprio, dentro da reserva livre até `0x10E8000` |

Interceptar apenas o vetor público antigo não bastaria: consumidores internos chamam o corpo diretamente. A função nativa de update é retomada em `0x0810166F` por um trampoline que reconstrói o acesso PC-relative e a condição; seus bytes não foram copiados cegamente. `Start`, `Stop`, `Reset` e o retorno nativo em `0x0810166C` não são substituídos.

Todo o restante da ROM é idêntico à v23: tabelas, scripts, payloads anteriores, distribuição e dados de batalha/itens. Não foram incluídas imagens, saves ou assets comerciais no manifesto de código.

## Identidades e reprodução

- Base v23, 33.554.432 bytes: `e7de31338f37b22995734d2f855aef82d965c348a83609606f8f2f08d42ba361`.
- Saída v24, 33.554.432 bytes: `5fe26a76ee13a85a8dbccecc61ce3f89ed7f44a49d221b8621acb4a0966e36d2`.
- Payload, 870 bytes: `d13a59fe1ba0a04b24a344d8f0f185033ea9ca3e06052b6d3435d8db007610fc`.

```sh
python3 firered_gen1_9/scripts/motor_v24.py \
  --rom /privado/motor_v23.gba --saida /privado/motor_v24.gba
```

O builder rejeita entrada diferente, corrupção do payload, reaplicação e destinos existentes, inclusive aliases por symlink/hardlink. Só escreve arquivo novo. Recompilação independente com Zig **0.17.0**, comparada byte a byte:

```sh
python3 -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi \
  -mthumb -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_minutes \
  -Wl,-T,firered_gen1_9/patches/motor_v24/payload.ld \
  firered_gen1_9/patches/motor_v24/entry.s \
  firered_gen1_9/patches/motor_v24/motor_v24.c -o /tmp/v24-rebuilt.elf
python3 -m ziglang objcopy -O binary /tmp/v24-rebuilt.elf /tmp/v24-rebuilt.bin
cmp /tmp/v24-rebuilt.bin firered_gen1_9/patches/motor_v24/payload.bin
```

## Validação

**60 métodos distintos aprovados em 579.422 s, sem failures, errors ou skips**, na build final identificada acima. A seleção completa foi reexecutada após os ajustes; sondagens e execuções interrompidas não entram nessa contagem. IDs, hashes, ambiente e limites estão nos [resultados estruturados](validacao_v24_resultados.json).

A seleção separa contratos diretos da CPU e fluxos reais por quadros/botões. Foram usados mGBA libretro 0.10.5 e estados/saves exclusivamente sintéticos. O teste histórico que exigia congelamento no máximo foi substituído por testes de continuação, não contado como sucesso com a asserção removida.

- Build: entrada/saída exatas, somente três intervalos, tabelas/guia v23 intactos, corrupção/reaplicação e saída exclusiva.
- Transições de quadros/segundos/horas e passagem exata pelo limite; ciclos à meia-noite, pausa/retomada/reset, estados desconhecidos e ponteiros inválidos.
- **Dois ciclos completos consecutivos de mundo**, 172.800 quadros em campo, além dos testes de fronteira. Isso demonstra repetição e coerência do contador modular; não simula todos os futuros estados possíveis do jogo.
- Inversão individual dos 64 bits do registro, minuto/quadro fora da faixa e dados estrangeiros recusados sem sobrescrita.
- Migração preguiçosa da extensão com TMs modernas ainda em slots legados, adiamento fora do campo externo e proteção diante da mochila temporária real do Pokedude; preservação de itens/equipe e bytes fora das regiões permitidas.
- Flash nativa v23→v24 abaixo do limite e no limite, roundtrip v24, e comportamento limitado do downgrade v24→v23→v24. Somente flash de 131.072 bytes cruza versões, nunca savestates.
- Depois do limite: dez fronteiras de horário nas 16 áreas, paleta noturna em campo e exclusão do menu da equipe, tempo em menus/batalhas e evoluções reais de Eevee para Espeon/Umbreon.
- Regressões anteriores: 3.200 sorteios determinísticos de slots, encontros e placa, 11 métodos de relógio/paleta/evoluções, EV/IV, captura/save/fuga/progressão inicial e quatro métodos selecionados de batalha.
- Estojo com relógio pós-limite ativo: capacidade 58+229, operações de quantidade, páginas/ensino com consumo de uma TM (política SV vigente), backup nativo e persistência das 287 quantidades junto ao relógio.

Foi corrigido um defeito do **harness de teste**, não da ROM: a caminhada de entrada já podia iniciar a batalha antes de o helper começar a procurar outra espécie. Agora ele observa o estado nativo de batalha, sem editar RAM durante a ação. Também foram corrigidas premissas dos testes de trajeto (encontros e fade-in podem ocorrer antes da placa e na ida à rota), do valor de EXP fixado para uma espécie sorteada da leitura automática da placa ao caminhar contra ela, e das expectativas de ensino/retorno e consumo de TM. A política vigente consome uma TM, ao contrário da antiga versão isolada do estojo. O teste de subida de nível usa um braço de controle com o mesmo inimigo e outra EXP inicial; o ensino continua pela interface real, incluindo a substituição de golpe e a saída normal do estojo. O acesso à placa usa Repel como condição sintética inicial; nenhum encontro é injetado e nada é editado durante a caminhada. Os níveis das Rotas 9–12 excedem o do inicial, portanto esse Repel não bloqueia os encontros testados nessas áreas. Essas sondagens não são somadas aos resultados finais. Tabelas e regras preservadas não significam uma sequência de RNG idêntica para uma gravação fixa de botões.

**Não comprovado:** campanha inteira, todos os estados de corrupção, periféricos/link reais, comportamento de emuladores diferentes, todos os temporizadores nativos nem fidelidade integral a Scarlet/Violet. Os números não se somam às rodadas v21/v22/v23.

### Executar a seleção

A partir da raiz do repositório, com as duas ROMs privadas e o core instalado:

```sh
MOTOR_V24_BASE=/privado/motor_v23.gba \
MOTOR_V24_ROM=/privado/motor_v24.gba \
TREINO_TEST_ROM=/privado/motor_v24.gba \
MGBA_CORE=/privado/mgba_libretro.so \
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
python3 -m unittest test_motor_v24 test_motor_v24_mgba \
  test_treino_ev_mgba test_motor_v24_gameplay_mgba \
  test_motor_v24_regressions test_motor_v24_estojo_mgba -v
```

V24 local. Sem commit/push, publicação no Drive, acesso a saves pessoais ou alteração de encontros além do escopo preservado.
