# Motor parcial v37 — 56 áreas, subsolos de Seafoam

2026-11-06. Base **FireRed Gen1–9 motor v36 exato**, não FireRed BR/BAG_MOD. Expansão autorizada, preservando as 52 áreas anteriores e o guia em três páginas. Somente os quatro subsolos de Seafoam Islands são adicionados; o 1F fica fora da expansão.

## Novos encontros noturnos

À noite (**20:00–05:59**), dois slots terrestres por área recebem:

| Área | Grupo/mapa | Slots | Primeiro encontro — 10% nominal | Segundo encontro — 10% nominal |
|---|---|---|---|---|
| Seafoam — B1F | 1/84 | 2 e 3 | Sneasel, nível **28** | Snorunt, nível **22** |
| Seafoam — B2F | 1/85 | **2 e 5** | Bergmite, nível **30** | Froslass, nível **24** |
| Seafoam — B3F | 1/86 | **2 e 4** | Haunter, nível **32** | Duskull, nível **32** |
| Seafoam — B4F | 1/87 | **3 e 4** | Snover, nível **34** | Beartic, nível **32** |

Índices começam em zero. Chances nominais antes de Repel e demais filtros. Níveis da base mantidos, sem normalização. Os demais 80% da distribuição e a frequência terrestre nativa **7** dos quatro mapas ficam intactos; frequência não significa porcentagem por passo. De dia (**06:00–19:59**) permanecem as tabelas originais.

### Preservação de encontros

| Espécie mantida dia/noite | Local e slot | Nível | Chance nominal |
|---|---|---:|---:|
| Eevee | Seafoam B1F, slot 7 | 28 | 5% |
| Great Tusk | Seafoam B2F, slot 3 | 32 | 10% |
| Glaceon | Seafoam B2F, slot 4 | 22 | 10% |
| Baxcalibur | Seafoam B3F, slot 3 | 30 | 10% |
| Espeon | Seafoam B3F, slot 5 | 24 | 10% |
| Iron Hands | Seafoam B4F, slot 2 | 32 | 10% |
| Flareon | Seafoam B4F, slot 5 | 26 | 10% |

Os conjuntos alternativos de slots evitam atingir esses encontros. Mantidas também as exceções anteriores da Rota 13, Pokémon Mansion e Victory Road 3F. **Pheromosa no 1F, slot 2, nível 31, permanece intacta**, assim como toda a distribuição do andar, que não recebe tabela noturna nova. Outros slots retidos, inclusive Frigibax e Bagon no B4F, não mudam.

Os quatro subsolos mantêm cabeçalhos do **tipo 4**. Usam o horário do mundo para encontros, mas **mantêm a iluminação nativa**, sem escurecimento noturno adicional. Água, pesca, Rock Smash, correntes, pedras/Strength, buracos, escadas, acessos, itens, eventos fixos e scripts de história permanecem como na base. Não há desbloqueio, quest, recompensa ou warp na entrega.

Preservados os prefixos de **104 linhas de política**, **1.248 linhas de guia**, **52 textos de consulta** e as distribuições noturnas anteriores. O [CSV completo](guia_encontros_horario_v37.csv) tem **1.344 linhas** (56 × 2 períodos × 12 slots); a política tem **112 substituições**. Distribuição de design do projeto, não tabela oficial de Scarlet/Violet nem garantia de dificuldade equivalente.

## Guia da placa da Rota 1 — três páginas

Novo caminho: **Mais areas / ilhas → Mais areas → Seafoam - Subsolos → área**.

Mansao Pokemon e Liga / Usina continuam na terceira página, com os mesmos textos e encontros. Nenhum grupo anterior é removido.

| Página | Conteúdo | Opções |
|---|---|---:|
| Primeira | Seis grupos de Kanto; Mais areas / ilhas; Horarios / sair | 8 |
| Segunda | Ilhas 1,2,3; Ilhas 5,6; Bosques / Ilha 7; Grutas de Kanto; Icefall - Ilha 4; Mais areas; Voltar; Horarios / sair | 8 |
| Terceira | Mansao Pokemon; Liga / Usina; **Seafoam - Subsolos**; Voltar; Horarios / sair | 5 |

- A seleciona; A/B fecha a consulta individual e retorna à lista de áreas.
- B/Voltar na lista retorna à página que contém o grupo.
- B/Voltar na terceira página retorna à segunda; na segunda retorna à primeira.
- **B na primeira página encerra**.
- Horarios / sair está nas três páginas: regras, Voltar e Sair. B/Voltar retorna à origem; Sair encerra de qualquer uma.
- Depois das regras, o período é consultado novamente e o guia volta à introdução/primeira página.

Direções originais preservadas. A indicação de período é uma fotografia do momento da consulta; páginas de espécies sempre dizem **NOITE**. Máximo de oito opções por menu, duas linhas por página e 32 caracteres por linha.

Sem campo persistente de navegação: retornos no script e **VAR_RESULT (800D)** temporário. Mantida a espera nativa de dois frames antes dos menus e a espera adicional do harness pela finalização da mensagem.

## Relógio e saves

MUNDO HH:MM, **START → Opções → SELECT**, preferência persistente, paletas e continuidade após 999:59:59 preservados. Ocultar o HUD não pausa tempo ou encontros. Ciclo acelerado de aproximadamente 24 minutos jogados por dia virtual; sem RTC ou avanço offline.

Sem novo campo de save ou migração. Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. Somente saves/estados sintéticos nos testes, nunca dados pessoais.

## Integração e integridade

Builder `scripts/motor_v37.py`; núcleo `scripts/motor_v37_encontros.py`; payload `patches/motor_v37/`, compilado com **Zig 0.17.1**, `-Wall -Wextra -Werror`.

| Offset no arquivo | Tamanho | Conteúdo |
|---|---:|---|
| `1393B0` | 4 B | Literal da tabela do menu vertical |
| `164340` | 8 B | Hook do gerador terrestre |
| `7C20D8` | 4 B | Ponteiro do script da placa |
| `111B000` | 296 B | Payload Thumb |
| `111C000` | 3.808 B | 56 descritores/tabelas noturnas |
| `111D000` | 1.416 B | Descritores originais + 18 listas e ações |
| `111D600` | 1.955 B | Script do guia |
| `111E000` | 3.903 B | Textos e rótulos |

Somente **oito intervalos**; todos os bytes externos idênticos à base. Reservas exigidas `FF`: `111B000..111D000` e `111D000..1120000`. Mantidos tabelas nativas, payloads anteriores, hooks de relógio/HUD/Opções e scripts de história.

Vetores `0911B001` seletor, `0911B009` encontro, `0911B011` noite e `0911B019` helper. Trampoline `0911B020`, retorno `08164349`. O seletor exige tipo terrestre, ponteiro original, grupo/mapa e ponteiro de save válido. Não sorteia RNG nem cria Pokémon: slot, nível, Repel e geração permanecem nativos.

Política anterior obrigatória como prefixo; substituições exigem os slots especificados, chances de 10%, espécies comuns e ausência de duplicação das novas espécies nos slots mantidos. Espécies protegidas e Snorlax são rejeitados.

65 descritores de `6CE39C` copiados integralmente. IDs **65–82**: primeira página 65, quatorze grupos 66–79, utilidades 80, segunda página 81 e terceira 82. A lista de utilidades é reutilizada em **três caminhos de retorno**. Referência de grade `139764` intacta; desenho, cursor, A/B e tasks nativos.

SHA-256:

- Base v36: `88afd471b59e9b27dcd1e42e7b5cab6068975098b9a58361a3dd251e3b075ad0`.
- Payload, 296 B: `2cdd0f26a1449a395694498faf91e38adafd4d1f4ed36f3724ed45da4e73ff0b`.
- ROM v37, 33.554.432 B: `9ce2266b8a657f69c79cad8469ec25676dc5bf223c90b28360a5433b84b4b1a3`.

Base, política, payload e saída verificados. Saída existente e reaplicação recusadas. Dados originais extraídos da base validada, não publicados como assets comerciais no fonte.

## Validação

**102/102 métodos aprovados em 761.895 s**, sem falhas, erros ou skips. Payload recompilado independentemente e ROM reconstruída com resultado idêntico. Doze capturas do guia geradas na ROM exata e conferidas visualmente. Também passaram os ensaios focados de encontros/paleta (**1 método, 147.670 s**) e navegação da terceira página (**3 métodos, 35.747 s**), sem somá-los à contagem consolidada. Seleção:

- **11 build/dados:** intervalos, hashes/vetores, rejeições, saída exclusiva, tabelas nativas, prefixos, slots preservados, layout, menus/script e exceções de slots.
- **8 encontros:** **11.200 casos determinísticos** (100 quantis × 56 áreas × dia/noite), níveis/checksums/ABI, equivalência às 52 anteriores, Repel, água/locais não abrangidos, helper sem flags salvas e encontros nas quatro novas áreas.
- **1.120 consultas pós-cap:** 56 áreas × 10 horários de fronteira × HUD visível/oculto, sem escritas no save.
- **12 guia:** **112 consultas** (56 áreas × dois períodos), A/B, três páginas, retorno à origem, saídas, regras/período, HUD oculto, relógio e menus antigos. Os testes da terceira página contemplam os novos índices de Voltar/utilidades e o grupo Seafoam.
- **11 HUD + 10 preferência + 10 relógio persistente + 11 relógio anterior + 5 estojo + 4 combate + 5 gameplay/flash + 9 EV.** Incluem 1.440 horários no oráculo de pixels, 172.800 frames vivos, 287 quantidades de TMs/HMs e saves normais sintéticos v36↔v37 antes/depois do cap.
- **6 regressões da auditoria da v32:** 12 capturas com save/reinicialização nas quatro áreas das ilhas adicionadas na v32; quatro trocas de período em Berry Forest; duas travessias locais de Sevault com save. Não são capturas nos subsolos de Seafoam. Master Ball verifica o caminho de captura, não catch rate; controles com Poké Ball comum continuam no gameplay.

Os ensaios negativos da Mansion e de Victory Road são rejeitados pelo **prefixo anterior imutável**. Os novos casos de Seafoam B2F/B3F/B4F alcançam a verificação explícita de slots: tentativas de atingir Great Tusk, Glaceon, Baxcalibur e Iron Hands devem falhar. Controles negativos do seletor incluem Seafoam 1F terrestre e água dos B3F/B4F.

### Chegada sintética, caminhada e paleta

Terreno lido desta ROM: tipo 4, atributo terrestre 1, piso comum de comportamento 8 e sem colisão, com vizinhos para caminhar e distância de NPCs. Não se usam escadas, pedras, correntes ou quedas como percurso. O atributo é conferido pela API nativa após carregar.

A chegada é abreviada por warp em **cópia descartável**, iniciada do próprio boot. Apenas dois intervalos da cópia diferem; restaurá-los deve reproduzir integralmente a ROM. A espera limitada exige destino e callback de campo corretos antes de salvar.

Depois da chegada: save normal, fechamento do core e carregamento desse flash por Continuar na **ROM exata v37**. Nenhum savestate atravessa da cópia para a entrega. Mapa, coordenadas, inicial e callback são conferidos.

Na ROM exata, **120 frames parados em cada período por área** devem avançar dois segundos jogados (dois minutos do mundo) e manter iguais as primeiras **208 cores de terreno** da paleta entre dia/noite. Caminhada nativa noturna deve encontrar os dois novos alvos, com espécie, nível e checksum válidos. Não se editam RNG, espécie, nível ou HP durante a ação; frequências não são elevadas para facilitar o teste.

A chegada usa Repel sintético com inicial inferior aos novos alvos. O controle separado de Repel usa líder sintético de nível 100, acima dos slots abrangidos. Nenhum nível da ROM muda para acomodar ensaio.

### Limites

Não se certificam acesso normal a Seafoam, Surf, Strength, solução de pedras/correntes, travessia dos andares, itens, Articuno/outros eventos fixos ou campanha completa. Preservação byte a byte não substitui jogar esses eventos.

Quantis não são frequências medidas em caminhada aleatória. Menus antigos são abertos/cancelados nos IDs 0, 15, 31, 39 e 64, não seus serviços completos; os 65 descritores são comparados. Guia repetido em 12 ensaios de quatro consultas consecutivas, não teste prolongado de todos os recursos.

Saves entre versões usam flash normal, nunca savestate. O ensaio longo usa HUD visível; controles de preferência oculta usam 120 frames. Rotinas isoladas de relógio usam o vetor v24 preservado; fluxos vivos usam os hooks atuais.

Sem certificação de hardware real, todos os emuladores, link real, saves pessoais ou fidelidade integral a Scarlet/Violet. Localizações da Pokédex não são reescritas por período.

## Reprodução

mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; core SHA-256 `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`.

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v37/payload.ld \
  firered_gen1_9/patches/motor_v37/entry.s \
  firered_gen1_9/patches/motor_v37/motor_v37.c -o /tmp/v37.elf
python -m ziglang objcopy -O binary /tmp/v37.elf /tmp/v37.bin
cmp /tmp/v37.bin firered_gen1_9/patches/motor_v37/payload.bin
python firered_gen1_9/scripts/motor_v37.py --rom /caminho/v36.gba --saida /novo/caminho/v37.gba

MOTOR_V37_ROM=/novo/caminho/v37.gba MOTOR_V37_BASE=/caminho/v36.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v37.gba \
python firered_gen1_9/scripts/validar_motor_v37.py --jobs 3 --log /tmp/v37-final.log
```

Runner exige **102 IDs únicos**, nenhum skip/falha/erro, cores/partidas isolados; tempo consolidado de parede. `--jobs 1` executa serialmente. Capturas opcionais exigem Pillow e diretório novo:

```sh
MOTOR_V37_ROM=/novo/caminho/v37.gba MGBA_CORE=/caminho/mgba_libretro.so \
python firered_gen1_9/scripts/capturar_guia_v37.py --saida /novo/diretorio/telas
```

Capturas do guia na ROM exata, por controles nativos em partida sintética, sem warps. ROM, saves, estados e screenshots fora do Git. **Entrega local, sem publicação no Drive, commit ou push.**
