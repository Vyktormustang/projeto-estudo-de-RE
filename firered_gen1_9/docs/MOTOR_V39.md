# Motor parcial v39 — 64 áreas, Cerulean e Seafoam 1F

2026-11-06. Base **FireRed Gen1–9 motor v38 exato**, não FireRed BR/BAG_MOD. Expansão autorizada, preservando as 60 áreas anteriores e o guia em três páginas. Adicionados **Cerulean Cave 1F, 2F, B1F e Seafoam Islands 1F**. Diferentemente da v38, o 1F de Seafoam agora recebe uma tabela noturna; Pheromosa permanece intacta.

## Novos encontros noturnos

À noite (**20:00–05:59**), dois slots terrestres por área recebem:

| Área | Grupo/mapa | Slots | Primeiro encontro — 10% nominal | Segundo encontro — 10% nominal |
|---|---|---|---|---|
| Cerulean Cave — 1F | 1/72 | 2 e 3 | Umbreon, nível **46** | Weavile, nível **46** |
| Cerulean Cave — 2F | 1/73 | 2 e 3 | Gengar, nível **52** | Spiritomb, nível **52** |
| Cerulean Cave — B1F | 1/74 | 2 e 3 | Hydreigon, nível **55** | Drapion, nível **55** |
| Seafoam Islands — 1F | 1/83 | **3 e 4** | Delibird, nível **22** | Swinub, nível **22** |

Índices começam em zero. Chances nominais antes de Repel e demais filtros. Níveis da base mantidos, sem normalização. Os demais 80% da distribuição e a frequência terrestre nativa **7** dos quatro mapas ficam intactos; frequência não significa porcentagem por passo. De dia (**06:00–19:59**) permanecem as tabelas originais.

### Encontros preservados

| Espécie mantida dia/noite | Local e slot | Nível | Chance nominal |
|---|---|---:|---:|
| Kartana | Cerulean Cave 1F, slot 5 | 52 | 10% |
| Flutter Mane | Cerulean Cave 2F, slot 5 | 55 | 10% |
| Iron Jugulis | Cerulean Cave B1F, slot 4 | 52 | 10% |
| Pheromosa | Seafoam 1F, slot 2 | 31 | 10% |

A exceção **3/4 em Seafoam 1F** evita substituir Pheromosa. Todos os demais slots não selecionados permanecem idênticos à base. Mantidas também todas as exceções anteriores da Rota 13, Pokémon Mansion, Victory Road, subsolos de Seafoam e caminho do Rubi.

Os quatro mapas são do **tipo 4**, com piso comum elegível para encontros. **Iluminação nativa preservada**, sem escurecimento noturno adicional. Água, pesca, Rock Smash, pedras/Strength, correntes, escadas, buracos, acessos, itens, eventos fixos e scripts de história não mudam. Não há desbloqueio, quest, recompensa ou warp na entrega.

Os quatro subsolos de Seafoam mantêm as distribuições anteriores. As salas de escadas do Rubi e os demais mapas não incluídos continuam sem novas tabelas noturnas nesta etapa.

Preservados os prefixos de **120 linhas de política**, **1.440 linhas de guia**, **60 textos de consulta** e todas as distribuições noturnas anteriores. O [CSV completo](guia_encontros_horario_v39.csv) tem **1.536 linhas** (64 × 2 períodos × 12 slots); a política tem **128 substituições**. Distribuição de design do projeto, não tabela oficial de Scarlet/Violet nem garantia de dificuldade equivalente.

## Guia da placa da Rota 1 — três páginas

Novo caminho: **Mais areas / ilhas → Mais areas → Cerulean / Seafoam → área**.

Mansao Pokemon, Liga / Usina, Seafoam - Subsolos e Mt. Ember - Rubi continuam na terceira página, com os mesmos textos e encontros. **Seafoam 1F está no novo grupo Cerulean / Seafoam**, não na lista dos quatro subsolos. Nenhum grupo anterior é removido.

| Página | Conteúdo | Opções |
|---|---|---:|
| Primeira | Seis grupos de Kanto; Mais areas / ilhas; Horarios / sair | 8 |
| Segunda | Ilhas 1,2,3; Ilhas 5,6; Bosques / Ilha 7; Grutas de Kanto; Icefall - Ilha 4; Mais areas; Voltar; Horarios / sair | 8 |
| Terceira | Mansao Pokemon; Liga / Usina; Seafoam - Subsolos; Mt. Ember - Rubi; **Cerulean / Seafoam**; Voltar; Horarios / sair | 7 |

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

Builder `scripts/motor_v39.py`; núcleo `scripts/motor_v39_encontros.py`; payload `patches/motor_v39/`, compilado com **Zig 0.17.1**, `-Wall -Wextra -Werror`.

| Offset no arquivo | Tamanho | Conteúdo |
|---|---:|---|
| `1393B0` | 4 B | Literal da tabela do menu vertical |
| `164340` | 8 B | Hook do gerador terrestre |
| `7C20D8` | 4 B | Ponteiro do script da placa |
| `1125000` | 296 B | Payload Thumb |
| `1126000` | 4.352 B | 64 descritores/tabelas noturnas |
| `1128000` | 1.528 B | Descritores originais + 20 listas e ações |
| `1128600` | 2.197 B | Script do guia |
| `1129000` | 4.482 B | Textos e rótulos |

Somente **oito intervalos**; todos os bytes externos idênticos à base. Reservas exigidas `FF`: `1125000..1128000` e `1128000..112B000`. Mantidos tabelas nativas, payloads anteriores, hooks de relógio/HUD/Opções e scripts de história.

### Reserva ampliada

64 × 68 = **4.352 B** ultrapassa a antiga capacidade de 4.096 B. A reserva das tabelas agora é de **8.192 B**, de `1126000` até `1128000`, sem avançar sobre o menu. O ensaio novo verifica todos os limites e exige rejeição ao reduzir essa reserva novamente para 4 KiB ou provocar sobreposição entre menu e script. O menu ocupa 1.528 dos 1.536 B reservados antes do script; uma futura expansão também deverá revisar esse limite.

Vetores `09125001` seletor, `09125009` encontro, `09125011` noite e `09125019` helper. Trampoline `09125020`, retorno `08164349`. O seletor exige tipo terrestre, ponteiro original, grupo/mapa e ponteiro de save válido. Não sorteia RNG nem cria Pokémon: slot, nível, Repel e geração permanecem nativos.

Política anterior obrigatória como prefixo; substituições exigem os slots especificados, chances de 10%, espécies comuns e ausência de duplicação das novas espécies nos slots mantidos. Espécies protegidas e Snorlax são rejeitados.

65 descritores de `6CE39C` copiados integralmente. IDs **65–84**: primeira página 65, dezesseis grupos 66–81, utilidades 82, segunda página 83 e terceira 84. A lista de utilidades é reutilizada em **três caminhos de retorno**. Referência de grade `139764` intacta; desenho, cursor, A/B e tasks nativos.

SHA-256:

- Base v38: `e22695512ef007fbeacd36f643440393528e9e43fc17224eac83ea04e63593c2`.
- Payload, 296 B: `3be6658a6340b27a7b2070dedf61f75e8fa85bce131ec63a9a9b0d449e2de327`.
- ROM v39, 33.554.432 B: `a7d35f5f92b8aae0618d32b8dc0b822d086c0325c030f509f0aaac8f2a08bac5`.

Base, política, payload e saída verificados. Saída existente e reaplicação recusadas. Dados originais extraídos da base validada, não publicados como assets comerciais no fonte.

## Validação

**103/103 métodos aprovados em 875.707 s**, sem falhas, erros ou skips. Payload recompilado independentemente e ROM reconstruída com resultado idêntico. Quatorze capturas do guia geradas na ROM exata e conferidas visualmente. Também passaram os ensaios focados de encontros/paleta (**1 método, 175.752 s**) e navegação da terceira página (**3 métodos, 53.414 s**), sem somá-los à contagem consolidada. Seleção:

- **12 build/dados:** intervalos, hashes/vetores, rejeições, saída exclusiva, tabelas nativas, prefixos, slots preservados, layout, menus/script, exceções de slots e o novo teste da reserva ampliada.
- **8 encontros:** **12.800 casos determinísticos** (100 quantis × 64 áreas × dia/noite), níveis/checksums/ABI, equivalência às 60 anteriores, Repel, água/locais não abrangidos, helper sem flags salvas e encontros nas quatro novas áreas.
- **1.280 consultas pós-cap:** 64 áreas × 10 horários de fronteira × HUD visível/oculto, sem escritas no save.
- **12 guia:** **128 consultas** (64 áreas × dois períodos), A/B, três páginas, retorno à origem, saídas, regras/período, HUD oculto, relógio e menus antigos. Os testes da terceira página contemplam os novos índices de Voltar/utilidades e o grupo Cerulean / Seafoam.
- **11 HUD + 10 preferência + 10 relógio persistente + 11 relógio anterior + 5 estojo + 4 combate + 5 gameplay/flash + 9 EV.** Incluem 1.440 horários no oráculo de pixels, 172.800 frames vivos, 287 quantidades de TMs/HMs e saves normais sintéticos v38↔v39 antes/depois do cap.
- **6 regressões da auditoria da v32:** 12 capturas com save/reinicialização nas quatro áreas das ilhas adicionadas na v32; quatro trocas de período em Berry Forest; duas travessias locais de Sevault com save. Não são capturas nas quatro áreas novas. Master Ball verifica o caminho de captura, não catch rate; controles com Poké Ball comum continuam no gameplay.

Os ensaios negativos de slots das áreas anteriores são rejeitados pelo **prefixo anterior imutável**. Os novos casos alcançam a verificação explícita de slots: tentativas de atingir Kartana, Flutter Mane, Iron Jugulis e Pheromosa devem falhar. Controles negativos do seletor incluem água de Cerulean 1F/B1F, água de Seafoam B3F/B4F e as duas salas de escadas do Rubi.

Seafoam 1F foi removido do controle de caverna não abrangida: agora participa dos controles positivos, dos 100 quantis por período, das fronteiras de horário e da caminhada nativa. Rock Tunnel 1F continua como controle de caverna não abrangida.

### Chegada sintética, caminhada e paleta

Terreno lido desta ROM: tipo 4, atributo terrestre 1, piso comum de comportamento 8 e sem colisão, com vizinhos para caminhar e distância de NPCs. Não se usam escadas, pedras, correntes ou quedas como percurso. O atributo é conferido pela API nativa após carregar.

A chegada é abreviada por warp em **cópia descartável**, iniciada do próprio boot. Apenas dois intervalos da cópia diferem; restaurá-los deve reproduzir integralmente a ROM. A espera limitada exige destino e callback de campo corretos antes de salvar.

Depois da chegada: save normal, fechamento do core e carregamento desse flash por Continuar na **ROM exata v39**. Nenhum savestate atravessa da cópia para a entrega. Mapa, coordenadas, inicial e callback são conferidos.

Na ROM exata, **120 frames parados em cada período por área** devem avançar dois segundos jogados (dois minutos do mundo) e manter iguais as primeiras **208 cores de terreno** da paleta entre dia/noite. Caminhada nativa noturna deve encontrar os dois novos alvos, com espécie, nível e checksum válidos. Não se editam RNG, espécie, nível ou HP durante a ação; frequências não são elevadas para facilitar o teste.

A chegada usa Repel sintético com inicial inferior aos novos alvos. O controle separado de Repel usa líder sintético de nível 100, acima dos slots abrangidos. Nenhum nível da ROM muda para acomodar ensaio.

### Limites

Não se certificam acesso normal a Cerulean Cave/Seafoam, requisitos de pós-jogo, Surf, Strength, solução de pedras/correntes, travessia dos andares, Mewtwo/Articuno/outros eventos fixos ou campanha completa. Preservação byte a byte não substitui jogar esses eventos.

Quantis não são frequências medidas em caminhada aleatória. Menus antigos são abertos/cancelados nos IDs 0, 15, 31, 39 e 64, não seus serviços completos; os 65 descritores são comparados. Guia repetido em 12 ensaios de quatro consultas consecutivas, não teste prolongado de todos os recursos.

Saves entre versões usam flash normal, nunca savestate. O ensaio longo usa HUD visível; controles de preferência oculta usam 120 frames. Rotinas isoladas de relógio usam o vetor v24 preservado; fluxos vivos usam os hooks atuais.

Sem certificação de hardware real, todos os emuladores, link real, saves pessoais ou fidelidade integral a Scarlet/Violet. Localizações da Pokédex não são reescritas por período.

## Reprodução

mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; core SHA-256 `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`.

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v39/payload.ld \
  firered_gen1_9/patches/motor_v39/entry.s \
  firered_gen1_9/patches/motor_v39/motor_v39.c -o /tmp/v39.elf
python -m ziglang objcopy -O binary /tmp/v39.elf /tmp/v39.bin
cmp /tmp/v39.bin firered_gen1_9/patches/motor_v39/payload.bin
python firered_gen1_9/scripts/motor_v39.py --rom /caminho/v38.gba --saida /novo/caminho/v39.gba

MOTOR_V39_ROM=/novo/caminho/v39.gba MOTOR_V39_BASE=/caminho/v38.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v39.gba \
python firered_gen1_9/scripts/validar_motor_v39.py --jobs 3 --log /tmp/v39-final.log
```

Runner exige **103 IDs únicos**, nenhum skip/falha/erro, cores/partidas isolados; tempo consolidado de parede. `--jobs 1` executa serialmente. Capturas opcionais exigem Pillow e diretório novo:

```sh
MOTOR_V39_ROM=/novo/caminho/v39.gba MGBA_CORE=/caminho/mgba_libretro.so \
python firered_gen1_9/scripts/capturar_guia_v39.py --saida /novo/diretorio/telas
```

Capturas do guia na ROM exata, por controles nativos em partida sintética, sem warps. ROM, saves, estados e screenshots fora do Git. **Entrega local, sem publicação no Drive, commit ou push.**
