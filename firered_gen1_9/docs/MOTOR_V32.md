# Motor parcial v32 — 36 áreas, bosques e Sevault

2026-11-06. Base **FireRed Gen1–9 motor v31 exato**, não FireRed BR/BAG_MOD.

## Expansão noturna

Na grama, à noite (**20:00–05:59**), os slots 2 e 3 recebem:

| Área | Grupo/mapa | Slot 2 — 10% nominal | Slot 3 — 10% nominal |
|---|---|---|---|
| Berry Forest — Ilha 3 | 1/109 | Phantump, nível **32** | Shiinotic, nível **30** |
| Pattern Bush — Ilha 6 | 1/121 | Venonat, nível **14** | Ariados, nível **6** |
| Entrada de Sevault Canyon — Ilha 7 | 3/63 | Houndour, nível **10** | Murkrow, nível **48** |
| Sevault Canyon — Ilha 7 | 3/64 | Houndoom, nível **46** | Honchkrow, nível **50** |

Índices começam em zero. Chances nominais antes de Repel e demais filtros. Os níveis variados são os da base, **não foram normalizados**. Outros 80% dos slots e a frequência terrestre nativa **21** de cada mapa permanecem; esse parâmetro do motor não é uma porcentagem por passo. De dia (**06:00–19:59**), as tabelas originais são usadas.

**Celesteela** na entrada de Sevault (slot 5, nível 41) e **Buzzwole** em Sevault Canyon (slot 5, nível 43) permanecem com seus 10% nominais em ambos os períodos. Em Berry Forest, **Drowzee** (slot 5, nível 34) e **Hypno** (slot 9, nível 37) ficam intactos. O evento de Lostelle e todos os demais scripts de história são byte a byte os da base; não se afirma ter percorrido esse evento na validação.

As **32 áreas anteriores** não mudam: mesmas 64 linhas iniciais da política, tabelas noturnas e primeiras 768 linhas do guia completo. Inclui a preservação dos slots de Slither Wing, Scream Tail, Brute Bonnet, Naganadel, Iron Valiant, Poipole, Raging Bolt e Snorlax. O novo [CSV](guia_encontros_horario_v32.csv) tem **864 linhas** (36 × 2 períodos × 12 slots); a política tem 72 substituições.

Água, pesca, Rock Smash, locais não abrangidos, barcos, HMs, insígnias, puzzles e requisitos de acesso continuam nativos. Não há warp, quest ou recompensa nova na entrega. A distribuição é de design do projeto, não tabela oficial de Scarlet/Violet nem garantia de dificuldade equivalente.

## Guia da placa da Rota 1

Mantidas as direções originais, os 32 textos anteriores e a navegação por grupo/área:

- Primeira página: seis grupos de Kanto, **Mais areas / ilhas** e **Horarios / sair** (oito opções).
- Segunda página: **Ilhas 1,2,3**, **Ilhas 5,6**, **Bosques / Ilha 7**, **Voltar** e **Horarios / sair** (cinco opções).
- Novo grupo: Berry Forest, Pattern Bush, Entrada Sevault, Sevault Canyon e Voltar.
- **A** seleciona; **A/B** fecha a consulta individual, retornando à lista de áreas.
- **B/Voltar** na lista de áreas retorna à página que contém seu grupo.
- **B/Voltar** na segunda página retorna à primeira; **B na primeira página** encerra.
- Utilidades: regras, Voltar e Sair. B/Voltar retorna à página de origem; Sair encerra em ambas.

Depois das regras, o período é consultado novamente e o guia retorna à introdução/primeira página. O período exibido é uma fotografia desse momento. As páginas de espécies sempre dizem **NOITE**, inclusive quando consultadas de dia. Nenhuma tela ultrapassa oito opções; nenhum texto ultrapassa duas linhas por página ou 32 caracteres por linha.

Sem estado de navegação persistente: os retornos estão no script e apenas **VAR_RESULT (800D)** é usado como resultado temporário. Mantida a espera nativa de dois frames antes dos menus. No harness, há também uma espera de dois frames para a task de mensagem terminar após a impressão, antes da confirmação.

## Relógio e saves

**MUNDO HH:MM**, **START → Opções → SELECT**, preferência persistente e continuidade após 999:59:59 permanecem byte a byte como na v31. Ocultar o HUD não pausa tempo, encontros ou paletas. Ciclo acelerado de aproximadamente 24 minutos jogados por dia virtual, sem RTC ou avanço offline.

Sem novo campo de save ou migração. Faça backup do save normal e carregue por **Continuar**; não reutilize savestates de outra versão nem misture com FireRed BR/BAG_MOD. Somente dados sintéticos são usados nos ensaios, nunca saves pessoais.

## Integração e integridade

Builder completo: `scripts/motor_v32.py`. Núcleo de encontros: `scripts/motor_v32_encontros.py`. Payload em `patches/motor_v32/`, compilado com **Zig 0.17.1** e `-Wall -Wextra -Werror`.

| Offset no arquivo | Tamanho | Conteúdo |
|---|---:|---|
| `1393B0` | 4 B | Literal da tabela do menu vertical |
| `164340` | 8 B | Hook do gerador terrestre nativo |
| `7C20D8` | 4 B | Ponteiro do script da placa |
| `1102000` | 296 B | Payload Thumb |
| `1103000` | 2.448 B | 36 descritores/tabelas noturnas |
| `1104000` | 1.104 B | Descritores originais + 12 listas do guia e ações |
| `1104600` | 1.278 B | Script paginado |
| `1105000` | 2.558 B | Textos e rótulos |

Somente **oito intervalos**, com todos os bytes fora deles idênticos à base. Reservas exigidas `FF`: `1102000..1104000` e `1104000..1107000`. Tabelas nativas, hooks de relógio/HUD/Opções, payloads anteriores e scripts de história não são modificados.

Vetores `09102001` seletor, `09102009` encontro, `09102011` noite e `09102019` helper da placa. Trampoline em `09102020`, retomando em `08164349`. O seletor exige tipo terrestre, ponteiro original, grupo/mapa corrente e ponteiro de save válido. Não sorteia RNG nem cria Pokémon; slot, nível, Repel e geração permanecem nativos.

O prefixo da política anterior é obrigatório. Slots substituídos devem ter 10%, espécies comuns e nenhuma duplicação das novas espécies nos slots mantidos. Espécies protegidas e Snorlax são rejeitados. Mantida a exceção da Rota 13, slots 3/4 para preservar Naganadel no 2.

Os 65 descritores originais de `6CE39C` são copiados integralmente. IDs **65–76**: primeira página 65, nove grupos 66–74, utilidades 75 e segunda página 76. As utilidades têm dois caminhos de retorno no script. A referência da grade em `139764` fica intacta; desenho, cursor, A/B e tasks são nativos.

SHA-256:

- Base v31: `fa25df630c902c7b7e155c9d8fca86f4a4674a76123b3541b68ab8eabcc84096`.
- Payload, 296 B: `796a60da7d06878fd31f01083e7e50532f94c39200c383a0733621ebd9c495c0`.
- ROM v32, 33.554.432 B: `7c095be4d52eeb728600eafbe2f57b60a4a402c11fe9a84cc19a8bbf61aa6d13`.

Base, política, payload e saída são verificados. Saída existente e reaplicação são recusadas. Dados originais são extraídos da base validada, não publicados como asset comercial no fonte.

## Validação

**Auditoria adicional concluída:** [99/99 métodos, captura/flash e continuidade local](AUDITORIA_V32.md), incluindo os 93 abaixo reexecutados. A ROM permanece inalterada; a rodada original abaixo é mantida como registro histórico.

**93/93 métodos aprovados em 551.650 s**, sem falhas, erros ou skips. Payload recompilado independentemente e ROM reconstruída com resultado idêntico. Nove capturas do guia geradas na ROM exata e conferidas visualmente. Seleção:

- **10 build/dados:** oito intervalos, hashes/vetores, rejeições, saída exclusiva, tabelas nativas, prefixo anterior, slots preservados, layout, menus e fluxo de script.
- **8 encontros:** **7.200 casos determinísticos** (100 quantis × 36 áreas × dia/noite), níveis/checksums/ABI, equivalência às 32 anteriores, Repel, água/locais não abrangidos, helper sem flags salvas e encontros nas quatro novas áreas.
- **720 consultas pós-cap ao seletor:** 36 áreas × 10 horários de fronteira × HUD visível/oculto, sem escritas no save.
- **10 navegação:** **72 consultas** (36 áreas nos dois períodos), A/B, paginação, retornos à origem, saída em ambas as páginas, regras/período, HUD oculto, relógio e menus anteriores.
- **11 HUD + 10 preferência + 10 relógio persistente + 11 relógio anterior + 5 estojo + 4 combate + 5 gameplay/flash + 9 EV.** Incluem 1.440 horários no oráculo de pixels, 172.800 frames vivos/dois dias virtuais, 287 quantidades de TMs/HMs e saves normais sintéticos v31↔v32 antes/depois do cap, com HUD visível/oculto.

Repel: líder sintético de nível 100, acima de todos os slots abrangidos, incluindo níveis 52/54 nativos. Nenhum nível da ROM é ajustado para acomodar o ensaio.

Novas áreas: acesso por **warps apenas em cópias de teste**. Terreno/coordenadas são lidos desta ROM e conferidos pela API nativa; depois, movimento e encontros nativos. Não se escrevem RNG, espécie, nível ou HP durante a ação. Não é prova de progressão até as ilhas, Lostelle, puzzles ou acesso a Sevault. Os warps não estão na ROM entregue.

Menus antigos: abertura/cancelamento dos IDs 0, 15, 31, 39 e 64 em scripts temporários, além da identidade dos 65 descritores; não seus serviços completos. Repetição do guia: 12 ensaios de quatro consultas consecutivas. Quantis são casos determinísticos, não frequências medidas em caminhadas aleatórias.

Captura comum admite falhas e varia apenas a espera antes do lançamento. A vitória usa encontro natural adequado ao inicial, não presume vitória contra qualquer inimigo. Flash cruza versões pelo save normal, nunca savestate. O ensaio longo usa HUD visível; controles dedicados de preferência oculta usam 120 frames. Rotinas isoladas de relógio usam o vetor v24 preservado; fluxos vivos usam os hooks atuais.

Sem certificação de campanha completa, hardware real, todos os emuladores, link real, saves pessoais ou fidelidade integral a Scarlet/Violet. Localizações da Pokédex não são reescritas por período.

## Reprodução

mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; core SHA-256 `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`. Zig **0.17.1**.

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v32/payload.ld \
  firered_gen1_9/patches/motor_v32/entry.s \
  firered_gen1_9/patches/motor_v32/motor_v32.c -o /tmp/v32.elf
python -m ziglang objcopy -O binary /tmp/v32.elf /tmp/v32.bin
cmp /tmp/v32.bin firered_gen1_9/patches/motor_v32/payload.bin
python firered_gen1_9/scripts/motor_v32.py --rom /caminho/v31.gba --saida /novo/caminho/v32.gba

MOTOR_V32_ROM=/novo/caminho/v32.gba MOTOR_V32_BASE=/caminho/v31.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v32.gba \
python firered_gen1_9/scripts/validar_motor_v32.py --jobs 3 --log /tmp/v32-final.log
```

Runner exige **93 IDs únicos**, cores/partidas isolados e nenhum skip/falha/erro; tempo consolidado de parede. `--jobs 1` executa serialmente. Capturas opcionais exigem Pillow e diretório novo:

```sh
MOTOR_V32_ROM=/novo/caminho/v32.gba MGBA_CORE=/caminho/mgba_libretro.so \
python firered_gen1_9/scripts/capturar_guia_v32.py --saida /novo/diretorio/telas
```

Capturas da ROM exata, por controles nativos em partida sintética, sem warps. ROM, saves, estados e screenshots ficam fora do Git. **Entrega local, sem publicação no Drive, commit ou push.**
