# Motor parcial v36 — 52 áreas e guia em três páginas

2026-11-06. Base **FireRed Gen1–9 motor v35 exato**, não FireRed BR/BAG_MOD. Expansão autorizada, preservando as 48 áreas anteriores e as seis regressões da auditoria da v32.

## Victory Road e Power Plant

À noite (**20:00–05:59**), dois slots terrestres por área recebem:

| Área | Grupo/mapa | Slots | Primeiro encontro — 10% nominal | Segundo encontro — 10% nominal |
|---|---|---|---|---|
| Victory Road — 1F | 1/39 | 2 e 3 | Golbat, nível **40** | Noivern, nível **43** |
| Victory Road — 2F | 1/40 | 2 e 3 | Sableye, nível **42** | Mawile, nível **45** |
| Victory Road — 3F | 1/41 | **3 e 4** | Zweilous, nível **43** | Absol, nível **46** |
| Power Plant | 1/95 | 2 e 3 | Joltik, nível **25** | Tynamo, nível **25** |

Índices começam em zero. Chances nominais antes de Repel e demais filtros. Níveis da base mantidos, sem normalização. Outros 80% dos slots e a frequência terrestre nativa **7** dos quatro mapas ficam intactos; frequência não significa porcentagem por passo. De dia (**06:00–19:59**) permanecem as tabelas originais.

### Preservação de encontros

| Espécie mantida dia/noite | Local e slot | Nível | Chance nominal |
|---|---|---:|---:|
| Iron Crown | Victory Road 1F, slot 5 | 32 | 10% |
| Guzzlord | Victory Road 2F, slot 5 | 34 | 10% |
| Roaring Moon | Victory Road 3F, slot 5 | 32 | 10% |
| Lucario | Victory Road 3F, slot 2 | 40 | 10% |
| Xurkitree | Power Plant, slot 6 | 31 | 5% |

A exceção **3/4 no 3F** preserva Lucario no slot 2. Mantidas as exceções de slots da Rota 13 e da Pokémon Mansion, incluindo Terapagos, Metagross, Dragonite e Ditto. O builder exige os conjuntos de slots definidos e o prefixo anterior imutável; rejeita modificações nos slots preservados cobertos pelo ensaio negativo.

Victory Road continua com cabeçalhos do **tipo 4**; Power Plant, **tipo 8**. Ambos usam o horário do mundo para encontros, mas **mantêm a iluminação nativa**, sem escurecimento noturno adicional. Pedras/Strength, interruptores, escadas, insígnias, acessos à Liga/Usina, itens, treinadores, eventos fixos e scripts de história permanecem byte a byte como na base. Água, pesca e Rock Smash não mudam. Não há desbloqueio, quest, recompensa ou warp na entrega.

Preservados os prefixos de **96 linhas de política**, **1.152 linhas de guia** e **48 textos de consulta**. O [CSV completo](guia_encontros_horario_v36.csv) tem **1.248 linhas** (52 × 2 períodos × 12 slots); a política tem **104 substituições**. Distribuição de design do projeto, não tabela oficial de Scarlet/Violet nem garantia de dificuldade equivalente.

## Guia da placa da Rota 1 — três páginas

Novo grupo: **Mais areas / ilhas → Mais areas → Liga / Usina → área**.

Pokémon Mansion passa para a mesma terceira página: **Mais areas / ilhas → Mais areas → Mansao Pokemon**. Seus quatro textos e encontros permanecem iguais.

| Página | Conteúdo | Opções |
|---|---|---:|
| Primeira | Seis grupos de Kanto; Mais areas / ilhas; Horarios / sair | 8 |
| Segunda | Ilhas 1,2,3; Ilhas 5,6; Bosques / Ilha 7; Grutas de Kanto; Icefall - Ilha 4; **Mais areas**; Voltar; Horarios / sair | 8 |
| Terceira | **Mansao Pokemon**; **Liga / Usina**; Voltar; Horarios / sair | 4 |

- A seleciona; A/B fecha a consulta individual e retorna à lista de áreas.
- B/Voltar na lista retorna à página que contém o grupo.
- B/Voltar na terceira página retorna à segunda; na segunda retorna à primeira.
- **B na primeira página encerra**.
- Horarios / sair está nas três páginas: regras, Voltar e Sair. B/Voltar retorna à página de origem; Sair encerra a partir de qualquer uma.
- Depois das regras, o período é consultado novamente e o guia sempre volta à introdução/primeira página, inclusive quando as regras foram abertas da terceira.

Direções originais preservadas. A indicação de período é uma fotografia do momento da consulta; páginas de espécies sempre dizem **NOITE**. Não se cria uma nona opção em nenhuma tela: máximos de oito opções por menu, duas linhas por página e 32 caracteres por linha.

Sem campo persistente de navegação: retornos no script e **VAR_RESULT (800D)** temporário. Mantida a espera nativa de dois frames antes dos menus e a espera adicional do harness pela finalização da mensagem.

## Relógio e saves

MUNDO HH:MM, **START → Opções → SELECT**, preferência persistente, paletas e continuidade após 999:59:59 preservados byte a byte. Ocultar o HUD não pausa tempo ou encontros. Ciclo acelerado de aproximadamente 24 minutos jogados por dia virtual; sem RTC ou avanço offline.

Sem novo campo de save ou migração. Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. Somente saves/estados sintéticos nos testes, nunca dados pessoais.

## Integração e integridade

Builder `scripts/motor_v36.py`; núcleo `scripts/motor_v36_encontros.py`; payload `patches/motor_v36/`, compilado com **Zig 0.17.1**, `-Wall -Wextra -Werror`.

| Offset no arquivo | Tamanho | Conteúdo |
|---|---:|---|
| `1393B0` | 4 B | Literal da tabela do menu vertical |
| `164340` | 8 B | Hook do gerador terrestre |
| `7C20D8` | 4 B | Ponteiro do script da placa |
| `1116000` | 296 B | Payload Thumb |
| `1117000` | 3.536 B | 52 descritores/tabelas noturnas |
| `1118000` | 1.360 B | Descritores originais + 17 listas e ações |
| `1118600` | 1.834 B | Script do guia |
| `1119000` | 3.656 B | Textos e rótulos |

Somente **oito intervalos**; todos os bytes externos idênticos à base. Reservas exigidas `FF`: `1116000..1118000` e `1118000..111B000`. Mantidos tabelas nativas, payloads anteriores, hooks de relógio/HUD/Opções e scripts de história.

Vetores `09116001` seletor, `09116009` encontro, `09116011` noite e `09116019` helper. Trampoline `09116020`, retorno `08164349`. O seletor exige tipo terrestre, ponteiro original, grupo/mapa e ponteiro de save válido. Não sorteia RNG nem cria Pokémon: slot, nível, Repel e geração permanecem nativos.

Política anterior obrigatória como prefixo; substituições exigem os slots especificados, chances de 10%, espécies comuns e ausência de duplicação das novas espécies nos slots mantidos. Espécies protegidas e Snorlax são rejeitados.

65 descritores de `6CE39C` copiados integralmente. IDs **65–81**: primeira página 65, treze grupos 66–78, utilidades 79, segunda página 80 e terceira 81. A lista de utilidades é reutilizada em **três caminhos de retorno**. Referência de grade `139764` intacta; desenho, cursor, A/B e tasks nativos.

SHA-256:

- Base v35: `049ed92bfc9c6b1a7c96b8123bbe3066f84af33bdfbb8e216f56cb64cbdca8c9`.
- Payload, 296 B: `38bfc804ccf891c241051b44181dd436733a0e79098c5011fbf94f82991c2c2c`.
- ROM v36, 33.554.432 B: `88afd471b59e9b27dcd1e42e7b5cab6068975098b9a58361a3dd251e3b075ad0`.

Base, política, payload e saída verificados. Saída existente e reaplicação recusadas. Dados originais extraídos da base validada, não publicados como assets comerciais no fonte.

## Validação

**102/102 métodos aprovados em 767.769 s**, sem falhas, erros ou skips. Payload recompilado independentemente e ROM reconstruída com resultado idêntico. Onze capturas do guia geradas na ROM exata e conferidas visualmente. Também passaram os ensaios focados de encontros/paleta (**158.838 s**) e os 12 métodos do guia (**122.876 s**), sem somá-los à contagem consolidada. Seleção:

- **11 build/dados:** intervalos, hashes/vetores, rejeições, saída exclusiva, tabelas nativas, prefixos, slots preservados, layout, menus/script e exceções de slots.
- **8 encontros:** **10.400 casos determinísticos** (100 quantis × 52 áreas × dia/noite), níveis/checksums/ABI, equivalência às 48 anteriores, Repel, água/locais não abrangidos, helper sem flags salvas e encontros nas quatro novas áreas.
- **1.040 consultas pós-cap:** 52 áreas × 10 horários de fronteira × HUD visível/oculto, sem escritas no save.
- **12 guia:** **104 consultas** (52 áreas × dois períodos), A/B, três páginas, retorno à origem, saídas, regras/período, HUD oculto, relógio e menus antigos. Dois métodos adicionais cobrem retorno/Voltar/wrap/Sair da terceira página e regras abertas nela; os ensaios anteriores também incluem os novos caminhos e Mansion relocalizada.
- **11 HUD + 10 preferência + 10 relógio persistente + 11 relógio anterior + 5 estojo + 4 combate + 5 gameplay/flash + 9 EV.** Incluem 1.440 horários no oráculo de pixels, 172.800 frames vivos, 287 quantidades de TMs/HMs e saves normais sintéticos v35↔v36 antes/depois do cap.
- **6 regressões da auditoria da v32:** 12 capturas com save/reinicialização nas quatro áreas das ilhas adicionadas na v32; quatro trocas de período em Berry Forest; duas travessias locais de Sevault com save. Não são capturas nas novas áreas. Master Ball verifica o caminho de captura, não catch rate; controles com Poké Ball comum continuam no gameplay.

O ensaio negativo de slots da Mansion agora deve falhar já na proteção do **prefixo da política anterior**; o caso novo de Victory Road 3F alcança a verificação explícita de slots. A expectativa da mensagem do teste foi adaptada a essa ordem de validação, sem relaxar o builder ou alterar a ROM.

### Chegada sintética, caminhada e paleta

Terreno lido desta ROM: tipos 4/8, atributo terrestre 1, piso comum de comportamento 8 e sem colisão, com vizinhos para caminhar e distância de NPCs. Não se usam escadas, pedras, interruptores ou quedas como percurso. O atributo é conferido pela API nativa após carregar.

A chegada é abreviada por warp em **cópia descartável**, iniciada do próprio boot. Apenas dois intervalos da cópia diferem; restaurá-los deve reproduzir integralmente a ROM. A espera limitada exige destino e callback de campo corretos antes de salvar.

Depois da chegada: save normal, fechamento do core e carregamento desse flash por Continuar na **ROM exata v36**. Nenhum savestate atravessa da cópia para a entrega. Mapa, coordenadas, inicial e callback são conferidos.

Na ROM exata, **120 frames parados em cada período por área** devem avançar dois segundos jogados (dois minutos do mundo) e manter iguais as primeiras **208 cores de terreno** da paleta entre dia/noite. Caminhada nativa noturna deve encontrar os dois novos alvos, com espécie, nível e checksum válidos. Não se editam RNG, espécie, nível ou HP durante a ação; frequências não são elevadas para facilitar o teste.

A chegada usa Repel sintético com inicial inferior aos novos alvos. O controle separado de Repel usa líder sintético de nível 100, acima dos slots abrangidos. Nenhum nível da ROM muda para acomodar ensaio.

### Limites

Não se certificam insígnias/acesso à Liga, Surf/acesso à Usina, Strength, pedras/interruptores, itens disfarçados, eventos fixos, treinadores ou travessia completa. Preservação byte a byte não substitui jogar esses eventos.

Quantis não são frequências medidas em caminhada aleatória. Menus antigos são abertos/cancelados nos IDs 0, 15, 31, 39 e 64, não seus serviços completos; os 65 descritores são comparados. Guia repetido em 12 ensaios de quatro consultas consecutivas, não teste prolongado de todos os recursos.

Saves entre versões usam flash normal, nunca savestate. O ensaio longo usa HUD visível; controles de preferência oculta usam 120 frames. Rotinas isoladas de relógio usam o vetor v24 preservado; fluxos vivos usam os hooks atuais.

Sem certificação de campanha completa, hardware real, todos os emuladores, link real, saves pessoais ou fidelidade integral a Scarlet/Violet. Localizações da Pokédex não são reescritas por período.

## Reprodução

mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; core SHA-256 `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`.

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v36/payload.ld \
  firered_gen1_9/patches/motor_v36/entry.s \
  firered_gen1_9/patches/motor_v36/motor_v36.c -o /tmp/v36.elf
python -m ziglang objcopy -O binary /tmp/v36.elf /tmp/v36.bin
cmp /tmp/v36.bin firered_gen1_9/patches/motor_v36/payload.bin
python firered_gen1_9/scripts/motor_v36.py --rom /caminho/v35.gba --saida /novo/caminho/v36.gba

MOTOR_V36_ROM=/novo/caminho/v36.gba MOTOR_V36_BASE=/caminho/v35.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v36.gba \
python firered_gen1_9/scripts/validar_motor_v36.py --jobs 3 --log /tmp/v36-final.log
```

Runner exige **102 IDs únicos**, nenhum skip/falha/erro, cores/partidas isolados; tempo consolidado de parede. `--jobs 1` executa serialmente. Capturas opcionais exigem Pillow e diretório novo:

```sh
MOTOR_V36_ROM=/novo/caminho/v36.gba MGBA_CORE=/caminho/mgba_libretro.so \
python firered_gen1_9/scripts/capturar_guia_v36.py --saida /novo/diretorio/telas
```

Capturas do guia na ROM exata, por controles nativos em partida sintética, sem warps. ROM, saves, estados e screenshots fora do Git. **Entrega local, sem publicação no Drive, commit ou push.**
