# Motor parcial v40 — 68 áreas, Rock Tunnel e escadas do Rubi

2026-11-06. Base **FireRed Gen1–9 motor v39 exato**, não FireRed BR/BAG_MOD. Expansão autorizada para **Rock Tunnel 1F/B1F e Mt. Ember Ruby Path B1F Stairs/B2F Stairs**, preservando as 64 áreas anteriores. As salas de escadas do Rubi, antes excluídas, agora recebem tabelas noturnas; isso não modifica as escadas ou seus destinos.

## Encontros noturnos

À noite (**20:00–05:59**):

| Área | Grupo/mapa | Slots | Primeiro encontro — 10% nominal | Segundo encontro — 10% nominal |
|---|---|---|---|---|
| Rock Tunnel — 1F | 1/81 | 2 e 3 | Woobat, nível **16** | Noibat, nível **17** |
| Rock Tunnel — B1F | 1/82 | 2 e 3 | Sableye, nível **17** | Carbink, nível **16** |
| Rubi — Escadas B1F | 1/107 | 2 e 3 | Houndoom, nível **42** | Lampent, nível **24** |
| Rubi — Escadas B2F | 1/108 | 2 e 3 | Litwick, nível **34** | Magcargo, nível **40** |

Índices começam em zero. Chances nominais antes de Repel e outros filtros. Níveis da base mantidos, sem normalização. Os demais 80% da distribuição e a frequência terrestre nativa **7** dos quatro mapas ficam intactos; frequência não significa porcentagem por passo. De dia (**06:00–19:59**) permanecem as tabelas originais.

Exemplos de encontros preservados dia/noite:

| Espécie | Local e slot | Nível | Chance nominal |
|---|---|---:|---:|
| Zubat | Rock Tunnel 1F, slot 0 | 15 | 20% |
| Onix | Rock Tunnel 1F, slot 11 | 15 | 1% |
| Zubat | Rock Tunnel B1F, slot 0 | 16 | 20% |
| Yamask | Rock Tunnel B1F, slot 9 | 15 | 4% |
| Onix | Rock Tunnel B1F, slot 11 | 17 | 1% |
| Tyranitar | Rubi Escadas B1F, slot 5 | 30 | 10% |
| Charizard | Rubi Escadas B2F, slot 4 | 24 | 10% |
| Houndoom | Rubi Escadas B2F, slot 7 | 28 | 5% |
| Iron Thorns | Rubi Escadas B2F, slot 9 | 30 | 4% |

Geodude no slot 10 dos dois mapas de Rock Tunnel também permanece intacto. Todos os slots não selecionados são copiados da base. Mantidas todas as exceções anteriores, incluindo Pheromosa em Seafoam 1F, Stakataka/Blacephalon no Rubi e os demais especiais.

Os quatro mapas são do **tipo 4**. Iluminação nativa mantida, sem escurecimento noturno adicional. Flash, água, pesca, Rock Smash, pedras/Strength, escadas, acessos, treinadores, itens, eventos fixos e scripts de história não mudam. Não há desbloqueio, recompensa ou warp de teste na entrega.

Prefixos preservados: **128 linhas de política**, **1.536 linhas de guia**, **64 textos** e todas as distribuições noturnas anteriores. O [CSV completo](guia_encontros_horario_v40.csv) tem **1.632 linhas** (68 × 2 × 12); a política tem **136 substituições**. São escolhas de design do projeto, não tabelas oficiais ou certificação de fidelidade a Scarlet/Violet.

## Guia — três páginas, oito opções em cada uma

Placa da Rota 1: **Mais areas / ilhas → Mais areas → Rock Tunnel / Rubi → área**.

Os quatro andares principais do Rubi continuam no grupo **Mt. Ember - Rubi**; apenas as duas salas de escadas estão no grupo novo. Nenhum texto ou grupo anterior é removido.

| Página | Conteúdo | Opções |
|---|---|---:|
| Primeira | Seis grupos de Kanto; Mais areas / ilhas; Horarios / sair | 8 |
| Segunda | Cinco grupos anteriores; Mais areas; Voltar; Horarios / sair | 8 |
| Terceira | Mansao Pokemon; Liga / Usina; Seafoam - Subsolos; Mt. Ember - Rubi; Cerulean / Seafoam; **Rock Tunnel / Rubi**; Voltar; Horarios / sair | 8 |

A seleciona. A/B fecha a consulta individual e retorna ao grupo; B/Voltar no grupo retorna à página de origem. B/Voltar na terceira página retorna à segunda, e na segunda à primeira. **B na primeira encerra**. Utilidades retornam à origem; Sair encerra de qualquer página. Após as regras, o período é consultado novamente e a navegação retorna à introdução/primeira página.

A indicação de período é uma fotografia da consulta; páginas de espécies dizem NOITE. Direções originais, duas linhas por página, limite de 32 caracteres por linha e menus nativos preservados. A terceira página chegou ao limite de oito opções: uma expansão futura terá de rever sua organização, não inserir uma nona opção.

Sem estado persistente de navegação: script e VAR_RESULT temporário (800D). Mantidas as esperas nativas e a espera do harness pela finalização da mensagem.

## Relógio e saves

MUNDO HH:MM, **START → Opções → SELECT**, preferência persistente, continuidade após 999:59:59 e formato do save preservados. Ocultar o HUD não pausa tempo ou encontros. Ciclo acelerado de aproximadamente 24 minutos jogados por dia virtual, sem RTC/avanço offline.

Faça backup do save normal e use **Continuar**, não savestates de outra ROM. Não misture com FireRed BR/BAG_MOD. Testes usam somente dados sintéticos, nunca saves pessoais. Nenhum campo novo ou migração de save.

## Integração e limites de espaço

Builder `scripts/motor_v40.py`; dados `scripts/motor_v40_encontros.py`; payload `patches/motor_v40/`, compilado com Zig **0.17.1**, `-Wall -Wextra -Werror`.

| Offset | Tamanho | Conteúdo |
|---|---:|---|
| `1393B0` | 4 B | Literal da tabela de menus verticais |
| `164340` | 8 B | Hook terrestre |
| `7C20D8` | 4 B | Ponteiro da placa |
| `112B000` | 296 B | Payload Thumb |
| `112C000` | 4.624 B | 68 descritores/tabelas noturnas |
| `112E000` | 1.584 B | Descritores originais + 21 listas e ações |
| `112E800` | 2.318 B | Script do guia |
| `1130000` | 4.762 B | Textos/rótulos |

Somente **oito intervalos** mudam. Todos os outros bytes são idênticos à base. Reservas exigidas FF: `112B000..112E000` e `112E000..1132000`.

A reserva das tabelas continua em **8.192 B**. O menu de **1.584 B** ultrapassa a antiga reserva de 1.536 B; agora dispõe de **2.048 B**, até `112E800`. O teste de limites verifica a rejeição de reserva de encontros reduzida a 4 KiB, retorno do menu à antiga reserva de 1.536 B e sobreposição entre menu e script.

Vetores: `0912B001` seletor; `0912B009` encontro; `0912B011` noite; `0912B019` helper. Trampoline `0912B020`, retorno `08164349`. O seletor exige área terrestre, ponteiro original, grupo/mapa e save válido. Não sorteia RNG nem cria Pokémon: slot, nível, Repel e geração permanecem nativos.

65 descritores originais de `6CE39C` preservados. IDs **65–85**: primeira página 65, dezessete grupos 66–82, utilidades 83, segunda página 84, terceira 85. Referência de grade `139764` intacta. A lista de utilidades é reutilizada em três caminhos de retorno.

Política anterior imutável como prefixo; slots/chances/espécies conferidos, sem novas espécies duplicadas nos slots mantidos. Espécies protegidas e Snorlax rejeitados como substituições. Entrada, política, payload e saída bloqueados por SHA-256; saída existente e reaplicação recusadas.

- Base v39: `a7d35f5f92b8aae0618d32b8dc0b822d086c0325c030f509f0aaac8f2a08bac5`.
- Payload: `cb1dd98b91b8d9812b894ae1e0b085239e828454047f7dd3af28e529e97555f2`.
- ROM v40, 33.554.432 B: `10214ba64a38a543d381db9d41eb37f46458a0926057d028dda2839b1f87e7e1`.

## Validação

**103/103 métodos aprovados em 748.087 s**, sem falhas, erros ou skips. Payload recompilado independentemente e ROM reconstruída com resultado idêntico. Quinze capturas do guia geradas na ROM exata e conferidas visualmente. Passaram também os ensaios focados de encontros/paleta (**1 método, 152.223 s**) e navegação da terceira página (**3 métodos, 33.229 s**), sem somá-los à contagem consolidada. Seleção:

- **12 build/dados:** hashes, oito intervalos, saída exclusiva, tabelas nativas, prefixos, espécies preservadas, rejeições, menus/script e reservas ampliadas.
- **8 encontros:** **13.600 casos determinísticos** (100 quantis × 68 áreas × dois períodos), níveis/checksums/ABI, equivalência às 64 anteriores, Repel, água/locais não abrangidos, helper e caminhada nas quatro áreas novas.
- **1.360 consultas pós-cap:** 68 áreas × 10 fronteiras de horário × HUD visível/oculto, sem escritas no save.
- **12 guia:** **136 consultas** (68 × dois períodos), retornos/saídas, regras, período, três páginas, HUD oculto, menus antigos e consultas repetidas.
- **11 HUD + 10 preferência + 10 relógio persistente + 11 relógio anterior + 5 estojo + 4 combate + 5 gameplay/flash + 9 EV**. Incluem 1.440 horários no oráculo de pixels, 172.800 frames vivos, 287 quantidades de TMs/HMs e flash normal sintético v39↔v40 antes/depois do cap.
- **6 regressões da auditoria v32:** 12 capturas nas quatro áreas das ilhas daquela versão, com identidade completa/save/reinicialização; quatro trocas de período em Berry Forest; duas travessias locais de Sevault. Não são capturas nas áreas novas. Master Ball testa o caminho de captura, não catch rate; controles com Poké Ball comum permanecem no gameplay.

Negativos de slots das áreas antigas falham pelo prefixo imutável. Novos casos rejeitam tentativas de substituir Zubat, Tyranitar e Iron Thorns. Rock Tunnel 1F e as duas salas de escadas saíram dos controles de caverna não abrangida e entraram nos controles positivos. **Mt. Ember Summit Path 1F** é agora controle de caverna não abrangida. Controles de água de Cerulean e Seafoam permanecem.

### Chegada sintética e caminhada

Terreno extraído da ROM exata: mapa tipo 4, atributo terrestre 1, piso comum de comportamento 8, sem colisão, com vizinhos para caminhar e distância de NPCs. A API nativa confirma o atributo após carregar. Os passos de teste não usam escadas, pedras ou quedas.

Chegada abreviada por warp em **cópia descartável iniciada do próprio boot**, com apenas dois intervalos alterados; restaurá-los deve reproduzir integralmente a ROM. Espera limitada pelo destino e callback de campo antes do save. Depois: save normal, fechamento do core e Continuar na **ROM exata v40**. Nenhum savestate atravessa ROMs. Mapa, coordenadas, inicial e callback são conferidos.

Em cada mapa, 120 frames parados por período devem avançar dois segundos jogados/dois minutos do mundo e manter iguais as primeiras 208 cores de terreno entre dia/noite. Caminhada nativa noturna deve encontrar os dois novos alvos com espécie, nível e checksum válidos. Sem editar RNG, espécie, nível ou HP durante a ação, nem elevar a frequência para o teste.

A chegada usa Repel sintético com inicial inferior aos novos alvos; o controle separado usa líder sintético de nível 100, acima de todos os encontros. Nenhum nível da ROM é alterado.

### Limites

Não se certificam acesso normal a Rock Tunnel/Rubi, utilização de Flash, estados possíveis de iluminação após Flash, requisitos de pós-jogo, Strength, puzzles, travessia das escadas, coleta/entrega do Rubi, treinadores/eventos fixos ou campanha completa. Preservação de bytes não substitui jogar esses eventos. A igualdade de paletas testada não é uma auditoria completa do sistema de Flash.

Quantis não são frequências medidas por caminhada aleatória. Menus antigos 0/15/31/39/64 são abertos/cancelados, não auditados em todos os serviços; os 65 descritores são comparados. Guia repetido em 12 ensaios de quatro consultas, não teste de longa duração. Ensaio longo com HUD visível; controles ocultos de 120 frames. Rotinas isoladas de relógio usam o vetor v24 preservado; fluxos vivos usam hooks atuais.

Sem certificação de hardware real, todos os emuladores, link real, saves pessoais ou fidelidade integral a Scarlet/Violet. Pokédex não é reescrita por período.

## Ambiente restaurado e reprodução

As ROMs ignoradas pelo Git e o ambiente de testes não estavam disponíveis ao retomar esta etapa. Recuperou-se somente a **v18 arquivada**, SHA-256 `f9a96edec0f070578dfec3d134dcb6decd5b4a5f7c296fef2c8346d7b9f504b2`, e reconstruíram-se v19–v39 pelos respectivos builders, todos com hashes exatos. Não se restauraram saves pessoais nem se publicaram arquivos no Drive. Os relatórios históricos não foram reescritos para representar novos testes.

mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`, recompilado nesta sessão com GCC **12.2.0** e CMake **4.4.4**. Core usado nesta validação: **`07ab56ae80ed30486eff67ab4907b345f46ebb5e60f47f98869dc534df18dad9`**. É um binário diferente do usado nos relatórios anteriores; a rodada desta versão é nova, não transferência de resultados antigos.

Comando de construção do core (os avisos de compilação upstream não impediram a conclusão):

```sh
git clone --depth 1 --branch 0.10.5 https://github.com/mgba-emu/mgba.git /caminho/mgba-source
cmake -S /caminho/mgba-source -B /caminho/mgba-build \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_LIBRETRO=ON -DBUILD_QT=OFF -DBUILD_SDL=OFF -DBUILD_GL=OFF \
  -DUSE_FFMPEG=OFF -DUSE_LIBZIP=OFF -DUSE_PNG=OFF -DUSE_ELF=OFF \
  -DUSE_SQLITE3=OFF -DUSE_LZMA=OFF -DUSE_ZLIB=OFF \
  -DENABLE_DEBUGGERS=OFF -DBUILD_TEST=OFF
cmake --build /caminho/mgba-build --target mgba_libretro -j 4
```

Payload e validação:

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v40/payload.ld \
  firered_gen1_9/patches/motor_v40/entry.s \
  firered_gen1_9/patches/motor_v40/motor_v40.c -o /tmp/v40.elf
python -m ziglang objcopy -O binary /tmp/v40.elf /tmp/v40.bin
cmp /tmp/v40.bin firered_gen1_9/patches/motor_v40/payload.bin
python firered_gen1_9/scripts/motor_v40.py --rom /caminho/v39.gba --saida /novo/caminho/v40.gba

MOTOR_V40_ROM=/novo/caminho/v40.gba MOTOR_V40_BASE=/caminho/v39.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v40.gba \
python firered_gen1_9/scripts/validar_motor_v40.py --jobs 3 --log /tmp/v40-final.log

MOTOR_V40_ROM=/novo/caminho/v40.gba MGBA_CORE=/caminho/mgba_libretro.so \
python firered_gen1_9/scripts/capturar_guia_v40.py --saida /novo/diretorio/telas
```

Runner exige 103 IDs únicos e nenhum skip/falha/erro; processos/cores isolados, tempo consolidado de parede. `--jobs 1` executa serialmente. Capturas exigem Pillow, diretório novo e partida sintética na ROM exata, por controles nativos, sem warp.

ROM, saves, estados e screenshots fora do Git. **Entrega local, sem publicação no Drive, commit ou push.**
