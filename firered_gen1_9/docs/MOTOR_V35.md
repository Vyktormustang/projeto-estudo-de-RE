# Motor parcial v35 — 48 áreas e Pokémon Mansion

2026-11-06. Base **FireRed Gen1–9 motor v34 exato**, não FireRed BR/BAG_MOD. Expansão autorizada, preservando as 44 áreas anteriores e as seis regressões da auditoria da v32.

## Quatro andares da Pokémon Mansion

À noite (**20:00–05:59**), dois slots terrestres por andar recebem:

| Área | Grupo/mapa | Slots substituídos | Primeiro encontro — 10% nominal | Segundo encontro — 10% nominal | Frequência nativa |
|---|---|---|---|---|---:|
| 1F | 1/59 | **3 e 4** | Shuppet, nível **36** | Litwick, nível **30** | 7 |
| 2F | 1/60 | **2 e 3** | Gastly, nível **30** | Misdreavus, nível **36** | 7 |
| 3F | 1/61 | **3 e 4** | Haunter, nível **36** | Banette, nível **30** | 7 |
| B1F | 1/62 | **2 e 4** | Yamask, nível **30** | Duskull, nível **30** | 5 |

Índices começam em zero. Chances nominais antes de Repel e demais filtros. Níveis da base mantidos, sem normalização. Outros 80% dos slots e as frequências nativas ficam intactos; frequência não significa porcentagem por passo. De dia (**06:00–19:59**) permanecem as tabelas originais.

### Slots preservados de propósito

- **Terapagos**: 1F, slot 1, nível 32, 20% nominais.
- **Metagross**: 1F, slot 2, nível 30, 10% nominais.
- **Dragonite**: 3F, slot 2, nível 30, 10% nominais.
- **Ditto**: B1F, slot 3, nível 30, 10% nominais.

Todos permanecem dia/noite. Por isso, a expansão **não aplica cegamente os slots 2/3**: usa 3/4 no 1F e 3F, e 2/4 no B1F. O builder exige esses conjuntos exatos e o teste adicional rejeita tentativas de atingir os slots mantidos. A exceção anterior da Rota 13 continua intacta. Todos os demais slots não substituídos, inclusive os especiais das 44 áreas anteriores, também são preservados.

A mansão usa o horário do mundo para selecionar encontros, mas **mantém a iluminação interna nativa**, sem escurecimento noturno adicional. Os quatro cabeçalhos continuam do **tipo 8**, sem conversão para mapa externo ou caverna. Portas, estátuas/interruptores, quedas, diários, itens/Secret Key, treinadores, scripts de história e requisitos de acesso permanecem byte a byte como na base. Água, pesca e Rock Smash não mudam. Não há desbloqueio, quest, recompensa ou warp na entrega.

Preservados os prefixos de **88 linhas de política**, **1.056 linhas de guia** e **44 textos de consulta**. O [CSV completo](guia_encontros_horario_v35.csv) tem **1.152 linhas** (48 × 2 períodos × 12 slots); a política tem **96 substituições**. Distribuição de design do projeto, não tabela oficial de Scarlet/Violet nem garantia de dificuldade equivalente.

## Guia da placa da Rota 1

**Mais areas / ilhas → Mansao Pokemon → andar**.

- Primeira página: seis grupos de Kanto, Mais areas / ilhas e Horarios / sair; oito opções.
- Segunda página: Ilhas 1,2,3; Ilhas 5,6; Bosques / Ilha 7; Grutas de Kanto; Icefall - Ilha 4; **Mansao Pokemon**; Voltar; Horarios / sair; oito opções.
- Grupo novo: 1F, 2F, 3F, B1F e Voltar.
- A seleciona; A/B fecha a consulta e retorna à lista de áreas.
- B/Voltar na lista retorna à página do grupo; na segunda página retorna à primeira. B na primeira encerra.
- Utilidades: regras, Voltar e Sair. B/Voltar retorna à página de origem; Sair encerra em ambas.

Direções originais preservadas. Após as regras, o período é consultado novamente e o guia volta à introdução/primeira página. A indicação é uma fotografia desse momento; as páginas de espécies sempre dizem **NOITE**. Máximo de oito opções por menu, duas linhas por página e 32 caracteres por linha. **Ambas as páginas atingem o limite de oito opções; nenhuma nona opção é criada.**

Sem campo persistente de navegação: retornos no script e **VAR_RESULT (800D)** temporário. Mantida a espera nativa de dois frames antes dos menus e a espera adicional do harness pela finalização da mensagem.

## Relógio e saves

MUNDO HH:MM, **START → Opções → SELECT**, preferência persistente, paletas e continuidade após 999:59:59 preservados byte a byte. Ocultar o HUD não pausa tempo ou encontros. Ciclo acelerado de aproximadamente 24 minutos jogados por dia virtual; sem RTC ou avanço offline.

Sem novo campo de save ou migração. Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. Somente saves/estados sintéticos nos testes, nunca dados pessoais.

## Integração e integridade

Builder `scripts/motor_v35.py`; núcleo `scripts/motor_v35_encontros.py`; payload `patches/motor_v35/`, compilado com **Zig 0.17.1**, `-Wall -Wextra -Werror`.

| Offset no arquivo | Tamanho | Conteúdo |
|---|---:|---|
| `1393B0` | 4 B | Literal da tabela do menu vertical |
| `164340` | 8 B | Hook do gerador terrestre |
| `7C20D8` | 4 B | Ponteiro do script da placa |
| `1111000` | 296 B | Payload Thumb |
| `1112000` | 3.264 B | 48 descritores/tabelas noturnas |
| `1113000` | 1.272 B | Descritores originais + 15 listas e ações |
| `1113600` | 1.641 B | Script do guia |
| `1114000` | 3.367 B | Textos e rótulos |

Somente **oito intervalos**; todos os bytes externos idênticos à base. Reservas exigidas `FF`: `1111000..1113000` e `1113000..1116000`. Mantidos tabelas nativas, payloads anteriores, hooks de relógio/HUD/Opções e scripts de história.

Vetores `09111001` seletor, `09111009` encontro, `09111011` noite e `09111019` helper. Trampoline `09111020`, retorno `08164349`. O seletor exige tipo terrestre, ponteiro original, grupo/mapa e ponteiro de save válido. Não sorteia RNG nem cria Pokémon: slot, nível, Repel e geração permanecem nativos.

Política anterior obrigatória como prefixo; substituições exigem os slots especificados, chances de 10%, espécies comuns e ausência de duplicação das novas espécies nos slots mantidos. Espécies protegidas e Snorlax são rejeitados.

65 descritores de `6CE39C` copiados integralmente. IDs **65–79**: primeira página 65, doze grupos 66–77, utilidades 78 e segunda página 79. Utilidades com dois caminhos de retorno. Referência de grade `139764` intacta; desenho, cursor, A/B e tasks nativos.

SHA-256:

- Base v34: `419212559dfb92054d2db024e8d0ef202ae601d3887f20a6c0d8f965cfb61655`.
- Payload, 296 B: `c77bb446c485eb786d8db5e138b87c0e4f4fc0036cc89f2d74d7821758742db6`.
- ROM v35, 33.554.432 B: `049ed92bfc9c6b1a7c96b8123bbe3066f84af33bdfbb8e216f56cb64cbdca8c9`.

Base, política, payload e saída verificados. Saída existente e reaplicação recusadas. Dados originais extraídos da base validada, não publicados como assets comerciais no fonte.

## Validação

**100/100 métodos aprovados em 776.395 s**, sem falhas, erros ou skips. Payload recompilado independentemente e ROM reconstruída com resultado idêntico. Nove capturas do guia geradas na ROM exata e conferidas visualmente. O ensaio focado dos quatro andares também passou em **152.721 s**, sem somá-lo à contagem consolidada. Seleção:

- **11 build/dados:** intervalos, hashes/vetores, rejeições, saída exclusiva, tabelas nativas, prefixos, slots preservados, layout, menus/script e novo teste de rejeição das substituições que atingiriam Metagross, Dragonite ou Ditto.
- **8 encontros:** **9.600 casos determinísticos** (100 quantis × 48 áreas × dia/noite), níveis/checksums/ABI, equivalência às 44 anteriores, Repel, água/locais não abrangidos, helper sem flags salvas e encontros nos quatro andares.
- **960 consultas pós-cap:** 48 áreas × 10 horários de fronteira × HUD visível/oculto, sem escritas no save.
- **10 guia:** **96 consultas** (48 áreas × dois períodos), A/B, paginação, retorno à origem, saída, regras/período, HUD oculto, relógio e menus antigos.
- **11 HUD + 10 preferência + 10 relógio persistente + 11 relógio anterior + 5 estojo + 4 combate + 5 gameplay/flash + 9 EV.** Incluem 1.440 horários no oráculo de pixels, 172.800 frames vivos, 287 quantidades de TMs/HMs e saves normais sintéticos v34↔v35 antes/depois do cap.
- **6 regressões da auditoria da v32:** 12 capturas com save/reinicialização nas quatro áreas das ilhas adicionadas na v32; quatro trocas de período em Berry Forest; duas travessias locais de Sevault com save. Não são capturas na mansão. Master Ball verifica o caminho de captura, não catch rate; controles com Poké Ball comum continuam no gameplay.

### Chegada sintética, caminhada e paleta

Terreno lido desta ROM: cabeçalho interno **tipo 8**, atributo terrestre 1, piso comum de comportamento 8 e sem colisão, com vizinhos para caminhar e distância de NPCs. Não são escolhidos interruptores, escadas ou quedas para o percurso. O atributo é conferido pela API nativa após carregar. O helper de terreno admite tipos 3/4/8 para manter a preparação dos controles anteriores.

A chegada é abreviada por warp em **cópia descartável**, iniciada do próprio boot. Apenas dois intervalos da cópia diferem; restaurá-los deve reproduzir integralmente a ROM. A espera limitada exige destino e callback de campo corretos antes de salvar.

Depois da chegada: save normal, fechamento do core e carregamento desse flash por Continuar na **ROM exata v35**. Nenhum savestate atravessa da cópia para a entrega. Mapa, coordenadas, inicial e callback são conferidos.

Na ROM exata, **120 frames parados em cada período por andar** devem avançar dois segundos jogados (dois minutos do mundo) e manter iguais as primeiras **208 cores de terreno** da paleta entre dia/noite. Caminhada nativa noturna deve encontrar os dois novos alvos, com espécie, nível e checksum válidos. Não se editam RNG, espécie, nível ou HP durante a ação. As frequências da ROM não são elevadas para facilitar o teste.

A chegada usa Repel sintético com inicial inferior aos novos alvos. O controle separado de Repel usa líder sintético de nível 100, acima dos slots abrangidos. Nenhum nível da ROM muda para acomodar ensaio.

### Limites

Não se certificam acesso normal à mansão, interruptores/portas, diários, Secret Key, quedas, treinadores ou travessia completa. Preservação byte a byte não substitui jogar esses eventos.

Quantis não são frequências medidas em caminhada aleatória. Menus antigos são abertos/cancelados nos IDs 0, 15, 31, 39 e 64, não seus serviços completos; os 65 descritores são comparados. Guia repetido em 12 ensaios de quatro consultas consecutivas, não teste prolongado de todos os recursos.

Saves entre versões usam flash normal, nunca savestate. O ensaio longo usa HUD visível; controles de preferência oculta usam 120 frames. Rotinas isoladas de relógio usam o vetor v24 preservado; fluxos vivos usam os hooks atuais.

Sem certificação de campanha completa, hardware real, todos os emuladores, link real, saves pessoais ou fidelidade integral a Scarlet/Violet. Localizações da Pokédex não são reescritas por período.

## Reprodução

mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; core SHA-256 `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`.

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v35/payload.ld \
  firered_gen1_9/patches/motor_v35/entry.s \
  firered_gen1_9/patches/motor_v35/motor_v35.c -o /tmp/v35.elf
python -m ziglang objcopy -O binary /tmp/v35.elf /tmp/v35.bin
cmp /tmp/v35.bin firered_gen1_9/patches/motor_v35/payload.bin
python firered_gen1_9/scripts/motor_v35.py --rom /caminho/v34.gba --saida /novo/caminho/v35.gba

MOTOR_V35_ROM=/novo/caminho/v35.gba MOTOR_V35_BASE=/caminho/v34.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v35.gba \
python firered_gen1_9/scripts/validar_motor_v35.py --jobs 3 --log /tmp/v35-final.log
```

Runner exige **100 IDs únicos**, nenhum skip/falha/erro, cores/partidas isolados; tempo consolidado de parede. `--jobs 1` executa serialmente. Capturas opcionais exigem Pillow e diretório novo:

```sh
MOTOR_V35_ROM=/novo/caminho/v35.gba MGBA_CORE=/caminho/mgba_libretro.so \
python firered_gen1_9/scripts/capturar_guia_v35.py --saida /novo/diretorio/telas
```

Capturas do guia na ROM exata, por controles nativos em partida sintética, sem warps. ROM, saves, estados e screenshots fora do Git. **Entrega local, sem publicação no Drive, commit ou push.**
