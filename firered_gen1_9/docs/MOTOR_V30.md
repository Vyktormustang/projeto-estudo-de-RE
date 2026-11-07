# Motor parcial v30 — encontros por horário em 28 áreas

2026-11-06. Base **FireRed Gen1–9 motor v29 exato**, não FireRed BR/BAG_MOD.

## Expansão nas ilhas

Na grama, à noite (**20:00–05:59**), os slots 2 e 3 passam a usar:

| Área | Slot 2 | Slot 3 |
|---|---|---|
| Kindle Road — Ilha 1 | Lampent, nível 36 | Numel, nível 31 |
| Treasure Beach — Ilha 1 | Sandygast, nível 31 | Krabby, nível 35 |
| Cape Brink — Ilha 2 | Natu, nível 32 | Banette, nível 36 |
| Bond Bridge — Ilha 3 | Duskull, nível 29 | Greavard, nível 36 |

Índices começam em zero. Cada substituição ocupa **10% nominal**, antes de Repel e outros filtros. Os outros 80%, os níveis e a frequência terrestre nativa **21** de cada mapa permanecem. Esse valor de frequência é um parâmetro do motor, não uma porcentagem de encontro por passo.

De dia (**06:00–19:59**), as tabelas anteriores ficam intactas. As **24 áreas anteriores** não mudam: preservadas as primeiras 48 linhas da política, as 24 tabelas noturnas e as primeiras 576 linhas do guia completo. O novo [CSV](guia_encontros_horario_v30.csv) tem **672 linhas** (28 × 2 períodos × 12 slots), e a política tem 56 substituições.

**Berry Forest fica fora da expansão. Água, pesca e Rock Smash não mudam.** Não se altera acesso às ilhas, barcos, Surf, insígnias, tutores ou eventos de história. Os bloqueios continuam nativos; nenhum warp é incluído na ROM entregue.

Mantidos os slots especiais anteriores, como Raging Bolt, Naganadel, Iron Valiant, Snorlax e Poipole. Entre os outros slots das novas áreas continuam Gholdengo em Kindle Road, Dragapult em Treasure Beach, Archaludon em Cape Brink e Kommo-o em Bond Bridge. Isso não significa que toda espécie comum permaneça à noite: os dois slots escolhidos são substituídos somente nesse período, conforme a tabela acima.

A distribuição é de design do projeto, não uma tabela oficial de Scarlet/Violet nem certificação de equilíbrio equivalente.

## Guia: oito opções no menu principal

A placa da **Rota 1** preserva suas direções e a consulta **grupo → área**. O novo grupo **Ilhas 1,2,3** contém as quatro áreas acima. As 24 consultas anteriores permanecem idênticas.

Para não exceder oito opções no menu principal, **Horarios / sair** agora abre um submenu com:

1. **Horarios / regras** — faixas de horário, chance e filtros;
2. **Voltar** — retorno ao menu principal;
3. **Sair** — encerra o guia.

**B no menu principal continua saindo imediatamente.** Nos grupos ou no submenu de horários, B retorna ao menu principal. A escolhe; A/B fecha a consulta individual e retorna à lista de áreas.

São nove listas nativas: principal, sete grupos e horários/saída. Nenhuma lista supera oito opções. A espera de dois frames antes de abrir cada menu é mantida, inclusive no novo submenu, evitando reutilização da entrada. Os testes também respeitam a finalização da task nativa de mensagem após o fim da impressão.

O período da introdução é consultado ao entrar e após ler as regras, não atualizado continuamente. As páginas de espécies sempre dizem **NOITE**, mesmo quando consultadas de dia. Níveis e distribuição completa continuam no CSV.

## Relógio e saves

**MUNDO HH:MM**, **START → Opções → SELECT**, preferência persistente e continuidade após 999:59:59 permanecem byte a byte como na v29. Ocultar o HUD não pausa o mundo, os encontros ou as paletas. Mantido o ciclo acelerado de aproximadamente 24 minutos jogados por dia virtual; sem RTC ou avanço offline.

Sem novo campo de save, migração, recompensa ou quest. O guia utiliza apenas o temporário **VAR_RESULT (800D)**, não flags permanentes. Faça backup do save normal e carregue por **Continuar**; não reutilize savestates de outra versão. Não misture com FireRed BR/BAG_MOD. Nenhum save pessoal foi usado.

## Implementação e integridade

Builder completo: `scripts/motor_v30.py`; núcleo de encontros: `scripts/motor_v30_encontros.py`; payload em `patches/motor_v30/`, compilado com **Zig 0.17.1**.

| Offset no arquivo | Tamanho | Alteração |
|---|---:|---|
| `1393B0` | 4 B | Literal da tabela do menu vertical |
| `164340` | 8 B | Hook do gerador terrestre nativo |
| `7C20D8` | 4 B | Ponteiro do script da placa |
| `10F8000` | 296 B | Payload Thumb de seleção, wrapper e período |
| `10F9000` | 1.904 B | 28 descritores/tabelas noturnas |
| `10FA000` | 960 B | 65 descritores nativos preservados + nove listas do guia e ações |
| `10FA400` | 964 B | Script navegável |
| `10FB000` | 1.894 B | Textos e rótulos |

Somente **oito intervalos**. Reservas exigidas `FF` na base: `10F8000..10FA000` e `10FA000..10FD000`. Todos os demais bytes ficam idênticos, incluindo tabelas nativas, payloads anteriores, hooks de relógio/HUD/Opções e eventos de história.

Vetores `090F8001` seletor, `090F8009` encontro, `090F8011` noite e `090F8019` helper. O trampoline nativo fica em `090F8020` e retoma em `08164349`. O seletor exige tipo terrestre, ponteiro original correspondente, grupo/mapa corrente e ponteiro de save válido. Não sorteia RNG nem cria Pokémon: seleção do slot, nível, Repel e geração permanecem nativos.

O prefixo da política anterior é obrigatório. Slots devem ter 10% e espécies comuns, sem duplicar substituições entre slots mantidos; espécies protegidas e Snorlax são rejeitados. A exceção da Rota 13 (slots 3/4, preservando Naganadel no 2) continua.

Os primeiros 65 descritores de menu de `6CE39C` são copiados byte a byte. IDs **65–73** pertencem ao guia; nenhum ID nativo é substituído. A referência do menu em grade em `139764` permanece original. Desenho, cursor, A/B, tasks e liberação de janela são nativos.

SHA-256:

- Base v29: `c8e9fd9e4269f31c462d3273c08b11996f8e229a5b20a2306e99f516bf5d2528`.
- Payload, 296 B: `bf6f11c1a6eff93b4136d141f713696075b2346aeed730820e8fda226407a24b`.
- ROM v30, 33.554.432 B: `58e3a53b0bed5729e02d322569bcfe4bd11c7f0161f74ef1d1347050753dba21`.

Base, política, payload e hash final são verificados; saída existente e reaplicação são recusadas. Dados originais de menu são extraídos somente da base validada, não publicados como asset comercial no fonte.

## Validação

**91 métodos únicos aprovados: 577.728 s de parede, três processos isolados, zero falhas, erros ou skips.** [Resultados](validacao_v30_resultados.json) e [log integral](validacao_v30.log). Seleção:

- **10 build/dados:** oito intervalos, vetores/hashes, corrupção/reaplicação, saída exclusiva, tabelas nativas, prefixo anterior, slots preservados, menus/scripts e layout de texto.
- **8 encontros:** **5.600 casos determinísticos** (100 quantis × 28 áreas × dia/noite), níveis/checksums/ABI, equivalência às 24 anteriores, Repel, água e áreas não abrangidas, helper sem flags salvas e encontros nas quatro áreas novas.
- **560 consultas pós-cap ao seletor:** 28 áreas × 10 horários de fronteira × HUD visível/oculto, sem escritas no save pelo seletor.
- **8 navegação:** **56 consultas** (28 áreas nos dois períodos), A/B, Voltar, saída pelo submenu e por B, wrap, regras, atualização do período, HUD oculto, relógio e menus nativos anteriores.
- **11 HUD + 10 preferência + 10 relógio persistente + 11 relógio anterior + 5 estojo + 4 combate + 5 gameplay/flash + 9 EV.** Incluem 1.440 horários no oráculo de pixels, 172.800 frames vivos/dois dias virtuais, 287 quantidades de TMs/HMs e saves normais sintéticos v29↔v30, antes/depois do cap e com HUD visível/oculto.

Os encontros nas novas áreas começam após **warps exclusivos de cópias de teste**, com terreno/coordenadas derivados desta ROM e conferidos pela API nativa. Depois há movimento e encontro nativos, sem escrever RNG, espécie, nível ou HP durante a ação. Não é prova de toda a progressão até as ilhas. A ROM entregue não contém esses warps.

Compatibilidade de menus: identidade dos 65 descritores e abertura/cancelamento dos IDs 0, 15, 31, 39 e 64 em scripts temporários de teste, não seus serviços completos. Repetição: 12 ensaios de quatro consultas consecutivas, não certificação de longa duração de todos os recursos.

Quantis não são frequências medidas em caminhadas aleatórias. O controle de Poké Ball admite falhas e varia somente a espera antes do lançamento. O controle de vitória usa encontro natural adequado ao inicial, sem presumir vitória contra qualquer inimigo. A flash cruza versões pelo save normal, não por savestate. O teste longo usa HUD visível; controles dedicados de preferência oculta usam 120 frames. Rotinas isoladas de relógio usam o vetor v24 preservado; fluxos vivos usam os hooks atuais.

Sem certificação de campanha completa, hardware real, todos os emuladores, link real, saves pessoais ou fidelidade integral a Scarlet/Violet. Localizações da Pokédex não são reescritas por período.

## Reprodução

mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; core SHA-256 `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`. Zig **0.17.1** para payload idêntico.

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v30/payload.ld \
  firered_gen1_9/patches/motor_v30/entry.s \
  firered_gen1_9/patches/motor_v30/motor_v30.c -o /tmp/v30.elf
python -m ziglang objcopy -O binary /tmp/v30.elf /tmp/v30.bin
cmp /tmp/v30.bin firered_gen1_9/patches/motor_v30/payload.bin
python firered_gen1_9/scripts/motor_v30.py --rom /caminho/v29.gba --saida /novo/caminho/v30.gba

MOTOR_V30_ROM=/novo/caminho/v30.gba MOTOR_V30_BASE=/caminho/v29.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v30.gba \
python firered_gen1_9/scripts/validar_motor_v30.py --jobs 3 --log /tmp/v30-final.log
```

O runner exige **91 IDs únicos**, cores/partidas isolados e nenhum skip/falha/erro. Tempo consolidado de parede; `--jobs 1` executa serialmente. Capturas opcionais exigem Pillow e diretório novo:

```sh
MOTOR_V30_ROM=/novo/caminho/v30.gba MGBA_CORE=/caminho/mgba_libretro.so \
python firered_gen1_9/scripts/capturar_guia_v30.py --saida /novo/diretorio/telas
```

Capturas da ROM exata, por controles nativos em partida sintética, sem warps. ROM, saves, estados e screenshots ficam fora do Git. **Entrega local, sem publicação no Drive, commit ou push.** O arquivo v18 já existente no Drive foi somente lido para reconstruir e conferir a cadeia até a base v29; nada novo foi enviado.
