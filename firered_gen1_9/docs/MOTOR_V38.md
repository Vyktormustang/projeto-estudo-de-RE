# Motor parcial v38 — 60 áreas, caminho do Rubi

2026-11-06. Base **FireRed Gen1–9 motor v37 exato**, não FireRed BR/BAG_MOD. Expansão autorizada, preservando as 56 áreas anteriores e o guia em três páginas. Adicionados **Mt. Ember Ruby Path 1F, B1F, B2F e B3F**; as duas salas de escadas não recebem tabelas noturnas novas.

## Novos encontros noturnos

À noite (**20:00–05:59**), dois slots terrestres por área recebem:

| Área do caminho do Rubi | Grupo/mapa | Slots | Primeiro encontro — 10% nominal | Segundo encontro — 10% nominal |
|---|---|---|---|---|
| 1F | 1/103 | **3 e 4** | Camerupt, nível **34** | Magcargo, nível **34** |
| B1F | 1/104 | 2 e 3 | Numel, nível **34** | Lampent, nível **40** |
| B2F | 1/105 | 2 e 3 | Houndoom, nível **42** | Salandit, nível **24** |
| B3F | 1/106 | **2 e 4** | Litwick, nível **30** | Sableye, nível **24** |

Índices começam em zero. Chances nominais antes de Repel e demais filtros. Níveis da base mantidos, sem normalização. Os demais 80% da distribuição e a frequência terrestre nativa **7** dos quatro mapas ficam intactos; frequência não significa porcentagem por passo. De dia (**06:00–19:59**) permanecem as tabelas originais.

### Encontros preservados

| Espécie mantida dia/noite | Local e slot | Nível | Chance nominal |
|---|---|---:|---:|
| Stakataka | Rubi 1F, slot 2 | 32 | 10% |
| Iron Treads | Rubi B1F, slot 9 | 30 | 4% |
| Aerodactyl | Rubi B1F, slot 5 | 26 | 10% |
| Garchomp | Rubi B2F, slot 5 | 30 | 10% |
| Blacephalon | Rubi B3F, slot 3 | 32 | 10% |

As exceções **3/4 no 1F** e **2/4 no B3F** evitam substituir Stakataka e Blacephalon. Mantidas também todas as exceções anteriores da Rota 13, Pokémon Mansion, Victory Road e Seafoam. Iron Treads, Aerodactyl, Garchomp e todos os demais slots não selecionados permanecem idênticos à base.

Os quatro mapas são do **tipo 4**, com piso comum elegível para encontros. **Iluminação nativa preservada**, sem escurecimento noturno adicional. Água, pesca, Rock Smash, pedras/Strength, escadas, buracos, acessos, itens, eventos fixos e scripts de história não mudam. Não há desbloqueio, quest, recompensa ou warp na entrega.

As salas **Ruby Path B1F Stairs (1/107)** e **B2F Stairs (1/108)** continuam com a geração nativa. Exterior, caminho do cume e demais mapas ficam fora desta expansão; o evento do Rubi não muda. Seafoam 1F também continua fora, com Pheromosa preservada; os quatro subsolos já cobertos mantêm suas distribuições da v37.

Preservados os prefixos de **112 linhas de política**, **1.344 linhas de guia**, **56 textos de consulta** e todas as distribuições noturnas anteriores. O [CSV completo](guia_encontros_horario_v38.csv) tem **1.440 linhas** (60 × 2 períodos × 12 slots); a política tem **120 substituições**. Distribuição de design do projeto, não tabela oficial de Scarlet/Violet nem garantia de dificuldade equivalente.

## Guia da placa da Rota 1 — três páginas

Novo caminho: **Mais areas / ilhas → Mais areas → Mt. Ember - Rubi → andar**.

Mansao Pokemon, Liga / Usina e Seafoam - Subsolos continuam na terceira página, com os mesmos textos e encontros. Nenhum grupo anterior é removido.

| Página | Conteúdo | Opções |
|---|---|---:|
| Primeira | Seis grupos de Kanto; Mais areas / ilhas; Horarios / sair | 8 |
| Segunda | Ilhas 1,2,3; Ilhas 5,6; Bosques / Ilha 7; Grutas de Kanto; Icefall - Ilha 4; Mais areas; Voltar; Horarios / sair | 8 |
| Terceira | Mansao Pokemon; Liga / Usina; Seafoam - Subsolos; **Mt. Ember - Rubi**; Voltar; Horarios / sair | 6 |

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

Builder `scripts/motor_v38.py`; núcleo `scripts/motor_v38_encontros.py`; payload `patches/motor_v38/`, compilado com **Zig 0.17.1**, `-Wall -Wextra -Werror`.

| Offset no arquivo | Tamanho | Conteúdo |
|---|---:|---|
| `1393B0` | 4 B | Literal da tabela do menu vertical |
| `164340` | 8 B | Hook do gerador terrestre |
| `7C20D8` | 4 B | Ponteiro do script da placa |
| `1120000` | 296 B | Payload Thumb |
| `1121000` | 4.080 B | 60 descritores/tabelas noturnas |
| `1122000` | 1.472 B | Descritores originais + 19 listas e ações |
| `1122600` | 2.076 B | Script do guia |
| `1123000` | 4.203 B | Textos e rótulos |

Somente **oito intervalos**; todos os bytes externos idênticos à base. Reservas exigidas `FF`: `1120000..1122000` e `1122000..1125000`. Mantidos tabelas nativas, payloads anteriores, hooks de relógio/HUD/Opções e scripts de história. A tabela de 4.080 B cabe na reserva de 4.096 B; o builder rejeita excesso, não avança silenciosamente para o menu.

Vetores `09120001` seletor, `09120009` encontro, `09120011` noite e `09120019` helper. Trampoline `09120020`, retorno `08164349`. O seletor exige tipo terrestre, ponteiro original, grupo/mapa e ponteiro de save válido. Não sorteia RNG nem cria Pokémon: slot, nível, Repel e geração permanecem nativos.

Política anterior obrigatória como prefixo; substituições exigem os slots especificados, chances de 10%, espécies comuns e ausência de duplicação das novas espécies nos slots mantidos. Espécies protegidas e Snorlax são rejeitados.

65 descritores de `6CE39C` copiados integralmente. IDs **65–83**: primeira página 65, quinze grupos 66–80, utilidades 81, segunda página 82 e terceira 83. A lista de utilidades é reutilizada em **três caminhos de retorno**. Referência de grade `139764` intacta; desenho, cursor, A/B e tasks nativos.

SHA-256:

- Base v37: `9ce2266b8a657f69c79cad8469ec25676dc5bf223c90b28360a5433b84b4b1a3`.
- Payload, 296 B: `b201e9d0bb2b7f86631793cfa59651801ad300a81d74dd2c91f6c739d79a3b61`.
- ROM v38, 33.554.432 B: `e22695512ef007fbeacd36f643440393528e9e43fc17224eac83ea04e63593c2`.

Base, política, payload e saída verificados. Saída existente e reaplicação recusadas. Dados originais extraídos da base validada, não publicados como assets comerciais no fonte.

## Validação

**102/102 métodos aprovados em 856.674 s**, sem falhas, erros ou skips. Payload recompilado independentemente e ROM reconstruída com resultado idêntico. Treze capturas do guia geradas na ROM exata e conferidas visualmente. Também passaram os ensaios focados de encontros/paleta (**1 método, 156.648 s**) e navegação da terceira página (**3 métodos, 41.519 s**), sem somá-los à contagem consolidada. Seleção:

- **11 build/dados:** intervalos, hashes/vetores, rejeições, saída exclusiva, tabelas nativas, prefixos, slots preservados, layout, menus/script e exceções de slots.
- **8 encontros:** **12.000 casos determinísticos** (100 quantis × 60 áreas × dia/noite), níveis/checksums/ABI, equivalência às 56 anteriores, Repel, água/locais não abrangidos, helper sem flags salvas e encontros nas quatro novas áreas.
- **1.200 consultas pós-cap:** 60 áreas × 10 horários de fronteira × HUD visível/oculto, sem escritas no save.
- **12 guia:** **120 consultas** (60 áreas × dois períodos), A/B, três páginas, retorno à origem, saídas, regras/período, HUD oculto, relógio e menus antigos. Os testes da terceira página contemplam os novos índices de Voltar/utilidades e o grupo Rubi.
- **11 HUD + 10 preferência + 10 relógio persistente + 11 relógio anterior + 5 estojo + 4 combate + 5 gameplay/flash + 9 EV.** Incluem 1.440 horários no oráculo de pixels, 172.800 frames vivos, 287 quantidades de TMs/HMs e saves normais sintéticos v37↔v38 antes/depois do cap.
- **6 regressões da auditoria da v32:** 12 capturas com save/reinicialização nas quatro áreas das ilhas adicionadas na v32; quatro trocas de período em Berry Forest; duas travessias locais de Sevault com save. Não são capturas no caminho do Rubi. Master Ball verifica o caminho de captura, não catch rate; controles com Poké Ball comum continuam no gameplay.

Os ensaios negativos de slots das áreas anteriores são rejeitados pelo **prefixo anterior imutável**. Os novos casos do Rubi alcançam a verificação explícita de slots: tentativas de atingir Stakataka, Iron Treads, Garchomp e Blacephalon devem falhar. Controles negativos do seletor incluem as duas salas de escadas do Rubi, Seafoam 1F terrestre e água dos B3F/B4F de Seafoam.

### Chegada sintética, caminhada e paleta

Terreno lido desta ROM: tipo 4, atributo terrestre 1, piso comum de comportamento 8 e sem colisão, com vizinhos para caminhar e distância de NPCs. Não se usam escadas, pedras ou quedas como percurso. O atributo é conferido pela API nativa após carregar.

A chegada é abreviada por warp em **cópia descartável**, iniciada do próprio boot. Apenas dois intervalos da cópia diferem; restaurá-los deve reproduzir integralmente a ROM. A espera limitada exige destino e callback de campo corretos antes de salvar.

Depois da chegada: save normal, fechamento do core e carregamento desse flash por Continuar na **ROM exata v38**. Nenhum savestate atravessa da cópia para a entrega. Mapa, coordenadas, inicial e callback são conferidos.

Na ROM exata, **120 frames parados em cada período por área** devem avançar dois segundos jogados (dois minutos do mundo) e manter iguais as primeiras **208 cores de terreno** da paleta entre dia/noite. Caminhada nativa noturna deve encontrar os dois novos alvos, com espécie, nível e checksum válidos. Não se editam RNG, espécie, nível ou HP durante a ação; frequências não são elevadas para facilitar o teste.

A chegada usa Repel sintético com inicial inferior aos novos alvos. O controle separado de Repel usa líder sintético de nível 100, acima dos slots abrangidos. Nenhum nível da ROM muda para acomodar ensaio.

### Limites

Não se certificam acesso normal ao caminho do Rubi, requisitos de pós-jogo, Strength, solução de pedras, travessia dos andares, coleta/entrega do Rubi, eventos fixos ou campanha completa. Preservação byte a byte não substitui jogar esses eventos.

Quantis não são frequências medidas em caminhada aleatória. Menus antigos são abertos/cancelados nos IDs 0, 15, 31, 39 e 64, não seus serviços completos; os 65 descritores são comparados. Guia repetido em 12 ensaios de quatro consultas consecutivas, não teste prolongado de todos os recursos.

Saves entre versões usam flash normal, nunca savestate. O ensaio longo usa HUD visível; controles de preferência oculta usam 120 frames. Rotinas isoladas de relógio usam o vetor v24 preservado; fluxos vivos usam os hooks atuais.

Sem certificação de hardware real, todos os emuladores, link real, saves pessoais ou fidelidade integral a Scarlet/Violet. Localizações da Pokédex não são reescritas por período.

## Reprodução

mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; core SHA-256 `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`.

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v38/payload.ld \
  firered_gen1_9/patches/motor_v38/entry.s \
  firered_gen1_9/patches/motor_v38/motor_v38.c -o /tmp/v38.elf
python -m ziglang objcopy -O binary /tmp/v38.elf /tmp/v38.bin
cmp /tmp/v38.bin firered_gen1_9/patches/motor_v38/payload.bin
python firered_gen1_9/scripts/motor_v38.py --rom /caminho/v37.gba --saida /novo/caminho/v38.gba

MOTOR_V38_ROM=/novo/caminho/v38.gba MOTOR_V38_BASE=/caminho/v37.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v38.gba \
python firered_gen1_9/scripts/validar_motor_v38.py --jobs 3 --log /tmp/v38-final.log
```

Runner exige **102 IDs únicos**, nenhum skip/falha/erro, cores/partidas isolados; tempo consolidado de parede. `--jobs 1` executa serialmente. Capturas opcionais exigem Pillow e diretório novo:

```sh
MOTOR_V38_ROM=/novo/caminho/v38.gba MGBA_CORE=/caminho/mgba_libretro.so \
python firered_gen1_9/scripts/capturar_guia_v38.py --saida /novo/diretorio/telas
```

Capturas do guia na ROM exata, por controles nativos em partida sintética, sem warps. ROM, saves, estados e screenshots fora do Git. **Entrega local, sem publicação no Drive, commit ou push.**
