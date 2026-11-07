# Motor parcial v34 — 44 áreas e Icefall Cave

2026-11-06. Base **FireRed Gen1–9 motor v33 exato**, não FireRed BR/BAG_MOD. Expansão autorizada, preservando as 40 áreas anteriores e as seis regressões da auditoria da v32.

## Quatro mapas de Icefall Cave — Ilha 4

À noite (**20:00–05:59**), os slots terrestres 2 e 3 recebem:

| Área | Grupo/mapa | Slot 2 — 10% nominal | Slot 3 — 10% nominal |
|---|---|---|---|
| Entrada | 1/110 | Snorunt, nível **45** | Cryogonal, nível **47** |
| 1F | 1/111 | Sneasel, nível **45** | Froslass, nível **27** |
| B1F | 1/112 | Bergmite, nível **45** | Glalie, nível **27** |
| Fundos | 1/113 | Jynx, nível **45** | Frosmoth, nível **47** |

Índices começam em zero. Chances nominais antes de Repel e demais filtros. **Níveis variados da base mantidos**, sem normalização. Outros 80% dos slots e a frequência terrestre nativa **7** dos quatro mapas permanecem; frequência não significa porcentagem por passo. De dia (**06:00–19:59**) permanecem as tabelas originais.

**Sandy Shocks**, no slot 6 de B1F, nível 30 e chance nominal de 5%, permanece dia/noite. Também são mantidos Kingambit, Seel, Dewgong, Swinub, Eiscue e todos os demais slots não substituídos. As 40 áreas anteriores conservam suas tabelas noturnas e espécies protegidas.

As cavernas seguem o horário do mundo para os encontros, mas **mantêm a iluminação nativa**, sem escurecimento noturno adicional. Cabeçalhos continuam do tipo 4. Água, pesca e Rock Smash não mudam. Gelo, quedas, cachoeira, escadas, HMs, barcos, requisitos de acesso e scripts de Lorelei/Rocket permanecem byte a byte como na base. Não há desbloqueio, quest, recompensa ou warp na entrega.

Preservados os prefixos de **80 linhas de política**, **960 linhas de guia** e **40 textos de consulta**. O [CSV completo](guia_encontros_horario_v34.csv) tem **1.056 linhas** (44 × 2 períodos × 12 slots); a política tem **88 substituições**. Distribuição de design do projeto, não tabela oficial de Scarlet/Violet nem garantia de dificuldade equivalente.

## Guia da placa da Rota 1

**Mais areas / ilhas → Icefall - Ilha 4 → área**.

- Primeira página: seis grupos de Kanto, Mais areas / ilhas e Horarios / sair; oito opções.
- Segunda página: Ilhas 1,2,3; Ilhas 5,6; Bosques / Ilha 7; Grutas de Kanto; **Icefall - Ilha 4**; Voltar; Horarios / sair; sete opções.
- Grupo novo: Entrada, 1F, B1F, Fundos e Voltar.
- A seleciona; A/B fecha a consulta e retorna à lista de áreas.
- B/Voltar na lista retorna à página do grupo; na segunda página retorna à primeira. B na primeira encerra.
- Utilidades: regras, Voltar e Sair. B/Voltar retorna à página de origem; Sair encerra em ambas.

Direções originais preservadas. Após as regras, o período é consultado novamente e o guia volta à introdução/primeira página. A indicação é uma fotografia desse momento; páginas de espécies sempre dizem **NOITE**. Máximo de oito opções por menu, duas linhas por página e 32 caracteres por linha.

Sem campo persistente de navegação: retornos codificados no script e **VAR_RESULT (800D)** temporário. Mantida a espera nativa de dois frames antes do menu. O harness aguarda também a task da mensagem terminar antes de confirmar.

## Relógio e saves

MUNDO HH:MM, **START → Opções → SELECT**, preferência persistente, paletas e continuidade após 999:59:59 preservados byte a byte. Ocultar o HUD não pausa tempo ou encontros. Ciclo acelerado de aproximadamente 24 minutos jogados por dia virtual; sem RTC ou avanço offline.

Sem novo campo de save ou migração. Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. Somente saves/estados sintéticos nos testes, nunca dados pessoais.

## Integração e integridade

Builder `scripts/motor_v34.py`; núcleo `scripts/motor_v34_encontros.py`; payload `patches/motor_v34/`, compilado com **Zig 0.17.1**, `-Wall -Wextra -Werror`.

| Offset no arquivo | Tamanho | Conteúdo |
|---|---:|---|
| `1393B0` | 4 B | Literal da tabela do menu vertical |
| `164340` | 8 B | Hook do gerador terrestre |
| `7C20D8` | 4 B | Ponteiro do script da placa |
| `110C000` | 296 B | Payload Thumb |
| `110D000` | 2.992 B | 44 descritores/tabelas noturnas |
| `110E000` | 1.216 B | Descritores originais + 14 listas e ações |
| `110E600` | 1.520 B | Script do guia |
| `110F000` | 3.074 B | Textos e rótulos |

Somente **oito intervalos**; todos os bytes externos idênticos à base. Reservas exigidas `FF`: `110C000..110E000` e `110E000..1111000`. Mantidos tabelas nativas, payloads anteriores, hooks de relógio/HUD/Opções e scripts de história.

Vetores `0910C001` seletor, `0910C009` encontro, `0910C011` noite e `0910C019` helper. Trampoline `0910C020`, retorno `08164349`. O seletor exige tipo terrestre, ponteiro original, grupo/mapa e ponteiro de save válido. Não sorteia RNG nem cria Pokémon: slot, nível, Repel e geração permanecem nativos.

Política anterior obrigatória como prefixo; substituições exigem slots de 10%, espécies comuns e ausência de duplicação das novas espécies nos slots mantidos. Espécies protegidas e Snorlax são rejeitados. Mantida a exceção da Rota 13, slots 3/4 para preservar Naganadel no 2.

65 descritores de `6CE39C` copiados integralmente. IDs **65–78**: primeira página 65, onze grupos 66–76, utilidades 77 e segunda página 78. Utilidades com dois caminhos de retorno. Referência de grade `139764` intacta; desenho, cursor, A/B e tasks nativos.

SHA-256:

- Base v33: `dc3d076a9645b22e49f366c477929e50ee06e1df836c19b4f418fe7b2e44ddaf`.
- Payload, 296 B: `8db19ad888758ada2f5ffb99bbf503d307596176e7e764cbd011c3a1b769dd1b`.
- ROM v34, 33.554.432 B: `419212559dfb92054d2db024e8d0ef202ae601d3887f20a6c0d8f965cfb61655`.

Base, política, payload e saída verificados. Saída existente e reaplicação recusadas. Dados originais extraídos da base validada, não publicados como assets comerciais no fonte.

## Validação

**99/99 métodos aprovados em 707.664 s**, sem falhas, erros ou skips. Payload recompilado independentemente e ROM reconstruída com resultado idêntico. Nove capturas do guia geradas na ROM exata e conferidas visualmente. O teste focado das quatro áreas também passou, em **140.256 s**; não é somado à contagem consolidada. Seleção:

- **10 build/dados:** intervalos, hashes/vetores, rejeições, saída exclusiva, tabelas nativas, prefixos, slots preservados, layout, menus e script.
- **8 encontros:** **8.800 casos determinísticos** (100 quantis × 44 áreas × dia/noite), níveis/checksums/ABI, equivalência às 40 anteriores, Repel, água/locais não abrangidos, helper sem flags salvas e encontros nas quatro áreas de Icefall.
- **880 consultas pós-cap:** 44 áreas × 10 horários de fronteira × HUD visível/oculto, sem escritas no save.
- **10 guia:** **88 consultas** (44 áreas × dois períodos), A/B, paginação, retorno à origem, saída, regras/período, HUD oculto, relógio e menus antigos.
- **11 HUD + 10 preferência + 10 relógio persistente + 11 relógio anterior + 5 estojo + 4 combate + 5 gameplay/flash + 9 EV.** Incluem 1.440 horários no oráculo de pixels, 172.800 frames vivos, 287 quantidades de TMs/HMs e saves normais sintéticos v33↔v34 antes/depois do cap.
- **6 regressões da auditoria da v32:** 12 capturas com save/reinicialização nas quatro áreas das ilhas adicionadas na v32; quatro trocas de período em Berry Forest; duas travessias locais de Sevault com save. Não são capturas em Icefall. Master Ball verifica o caminho de captura, não catch rate; controles com Poké Ball comum continuam no gameplay.

### Chegada sintética, caminhada e paleta

Terreno lido desta ROM: cabeçalho tipo 4, atributo terrestre 1, piso comum de comportamento 8 e sem colisão, com vizinhos para caminhar e distância de NPCs. **Piso comum**, não gelo quebrável, escadas, cachoeira ou Surf. O atributo é conferido pela API nativa após carregar.

A chegada é abreviada por warp em **cópia descartável**, iniciada do próprio boot. Apenas dois intervalos da cópia diferem; restaurá-los deve reproduzir integralmente a ROM. A espera limitada exige destino e callback de campo corretos antes do save, mantendo a correção de transição introduzida no harness da v33.

Depois da chegada: save normal, fechamento do core e carregamento desse flash por Continuar na **ROM exata v34**. Nenhum savestate atravessa da cópia para a entrega. Mapa, coordenadas, inicial e callback são conferidos.

Na ROM exata, **120 frames parados em cada período por área** devem avançar dois segundos jogados (dois minutos do mundo) e manter iguais as primeiras **208 cores de terreno** da paleta entre dia/noite. Caminhada nativa noturna deve encontrar os dois novos alvos, com espécie, nível e checksum válidos. Não se editam RNG, espécie, nível ou HP durante a ação. Frequência 7 da ROM não é elevada para facilitar o teste.

A chegada usa Repel sintético com inicial inferior aos novos alvos. O controle separado de Repel usa líder sintético de nível 100, acima dos slots abrangidos. Nenhum nível da ROM muda para acomodar ensaio.

### Limites

Não se certificam gelo, quedas, cachoeira, HM Waterfall, evento de Lorelei/Rocket, acesso normal à Ilha 4 ou travessia completa de Icefall. Preservação byte a byte não substitui jogar esses eventos.

Quantis não são frequências medidas em caminhada aleatória. Menus antigos são abertos/cancelados nos IDs 0, 15, 31, 39 e 64, não seus serviços completos; os 65 descritores são comparados. Guia repetido em 12 ensaios de quatro consultas consecutivas, não teste prolongado de todos os recursos.

Saves entre versões usam flash normal, nunca savestate. O ensaio longo usa HUD visível; controles de preferência oculta usam 120 frames. Rotinas isoladas de relógio usam o vetor v24 preservado; fluxos vivos usam os hooks atuais.

Sem certificação de campanha completa, hardware real, todos os emuladores, link real, saves pessoais ou fidelidade integral a Scarlet/Violet. Localizações da Pokédex não são reescritas por período.

## Reprodução

mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; core SHA-256 `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`.

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v34/payload.ld \
  firered_gen1_9/patches/motor_v34/entry.s \
  firered_gen1_9/patches/motor_v34/motor_v34.c -o /tmp/v34.elf
python -m ziglang objcopy -O binary /tmp/v34.elf /tmp/v34.bin
cmp /tmp/v34.bin firered_gen1_9/patches/motor_v34/payload.bin
python firered_gen1_9/scripts/motor_v34.py --rom /caminho/v33.gba --saida /novo/caminho/v34.gba

MOTOR_V34_ROM=/novo/caminho/v34.gba MOTOR_V34_BASE=/caminho/v33.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v34.gba \
python firered_gen1_9/scripts/validar_motor_v34.py --jobs 3 --log /tmp/v34-final.log
```

Runner exige **99 IDs únicos**, nenhum skip/falha/erro, cores/partidas isolados; tempo consolidado de parede. `--jobs 1` executa serialmente. Capturas opcionais exigem Pillow e diretório novo:

```sh
MOTOR_V34_ROM=/novo/caminho/v34.gba MGBA_CORE=/caminho/mgba_libretro.so \
python firered_gen1_9/scripts/capturar_guia_v34.py --saida /novo/diretorio/telas
```

Capturas do guia na ROM exata, por controles nativos em partida sintética, sem warps. ROM, saves, estados e screenshots fora do Git. **Entrega local, sem publicação no Drive, commit ou push.**
