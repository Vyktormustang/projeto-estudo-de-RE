# Motor parcial v31 — 32 áreas e guia em duas páginas

2026-11-06. Base **FireRed Gen1–9 motor v30 exato**, não FireRed BR/BAG_MOD.

## Novas áreas: ilhas 5 e 6

Na grama, à noite (**20:00–05:59**), os slots 2 e 3 passam a usar:

| Área | Slot 2 — 10% nominal | Slot 3 — 10% nominal |
|---|---|---|
| Five Island Meadow — Ilha 5 | Liepard, nível **48** | Purrloin, nível **10** |
| Memorial Pillar — Ilha 5 | Gastly, nível **8** | Litwick, nível **14** |
| Water Path — Ilha 6 | Noctowl, nível **44** | Misdreavus, nível **48** |
| Ruin Valley — Ilha 6 | Golett, nível **18** | Duskull, nível **15** |

Índices começam em zero. Chances nominais antes de Repel e demais filtros. Os níveis variados são os da base, **não foram normalizados**. Outros 80% dos slots e frequência terrestre nativa **21** de cada mapa permanecem. Esse valor de frequência é um parâmetro do motor, não uma porcentagem por passo.

**Slither Wing** em Five Island Meadow (slot 5, nível 41), **Scream Tail** em Water Path (slot 5, nível 41) e **Brute Bonnet** em Ruin Valley (slot 5, nível 43) são preservados, com seus 10% nominais em ambos os períodos. Mantidos também todos os slots especiais protegidos das áreas anteriores.

De dia (**06:00–19:59**) permanecem as tabelas originais. As **28 áreas anteriores** não mudam: mesmas 56 linhas iniciais da política, mesmas tabelas noturnas e mesmas primeiras 672 linhas do guia completo. O novo [CSV](guia_encontros_horario_v31.csv) tem **768 linhas** (32 × 2 períodos × 12 slots); a política tem 64 substituições.

Água, pesca, Rock Smash e áreas não abrangidas não recebem mudanças. Eventos, armazém Rocket, acessos, barcos, HMs, insígnias e requisitos de progressão continuam nativos. Não há warp na ROM entregue. Esta distribuição é de design do projeto, não tabela oficial de Scarlet/Violet nem garantia de dificuldade equivalente.

## Guia da placa da Rota 1

As direções originais e a consulta **grupo → área** são preservadas. Para manter no máximo oito opções por tela:

- **Primeira página:** seis grupos de Kanto, **Mais areas / ilhas** e **Horarios / sair**.
- **Segunda página:** **Ilhas 1,2,3**, **Ilhas 5,6**, **Voltar** e **Horarios / sair**.
- **A:** selecionar. **A/B:** fechar a consulta individual e retornar à lista de áreas.
- **B/Voltar** em uma lista de áreas: retornar à página que contém seu grupo.
- **B/Voltar** na segunda página: retornar à primeira.
- **B na primeira página:** sair imediatamente.
- **Horarios / sair:** regras, Voltar ou Sair. Voltar/B retorna à página de origem; Sair encerra a partir de qualquer página.

Após ler as regras, o período é consultado novamente e o guia retorna à introdução/primeira página. O período exibido é uma fotografia desse momento, não uma atualização contínua. As páginas de espécies sempre dizem **NOITE**, mesmo quando consultadas de dia. Os 28 textos de consulta anteriores não mudam.

A navegação não grava página ou seleção no save: os caminhos de retorno são codificados no script, reutilizando apenas **VAR_RESULT (800D)**, temporário. A espera nativa de dois frames antes de cada menu permanece. Os testes aguardam também a finalização da task de mensagem após o fim da impressão, antes de confirmar a caixa.

## Relógio e saves

**MUNDO HH:MM**, **START → Opções → SELECT**, preferência persistente e continuidade após 999:59:59 permanecem byte a byte como na v30. Ocultar o HUD não pausa tempo, encontros ou paletas. Mantido o ciclo acelerado de aproximadamente 24 minutos jogados por dia virtual; sem RTC ou avanço offline.

Sem novo campo de save, migração, recompensa ou quest. Faça backup do save normal e carregue por **Continuar**; não reutilize savestates de outra versão nem misture com FireRed BR/BAG_MOD. Somente dados sintéticos são usados nos ensaios; nenhum save pessoal.

## Integração e integridade

Builder completo: `scripts/motor_v31.py`. Núcleo de encontros: `scripts/motor_v31_encontros.py`. Payload em `patches/motor_v31/`, compilado com **Zig 0.17.1**.

| Offset no arquivo | Tamanho | Conteúdo |
|---|---:|---|
| `1393B0` | 4 B | Literal da tabela do menu vertical |
| `164340` | 8 B | Hook do gerador terrestre nativo |
| `7C20D8` | 4 B | Ponteiro do script da placa |
| `10FD000` | 296 B | Payload Thumb de seleção, wrapper e período |
| `10FE000` | 2.176 B | 32 descritores/tabelas noturnas |
| `10FF000` | 1.048 B | 65 descritores originais + 11 listas do guia e ações |
| `10FF600` | 1.157 B | Script paginado |
| `1100000` | 2.233 B | Textos e rótulos |

Somente **oito intervalos**. Reservas exigidas `FF`: `10FD000..10FF000` e `10FF000..1102000`. Todos os bytes fora desses intervalos ficam idênticos, inclusive tabelas nativas, payloads anteriores, hooks de relógio/HUD/Opções e scripts de história.

Vetores `090FD001` seletor, `090FD009` encontro, `090FD011` noite e `090FD019` helper. Trampoline em `090FD020`, retomando em `08164349`. O seletor exige tipo terrestre, ponteiro original, grupo/mapa corrente e ponteiro de save válido. Não sorteia RNG nem cria Pokémon: slot, nível, Repel e geração permanecem nativos.

O prefixo da política anterior é obrigatório. Slots substituídos devem ter 10%, espécies comuns e nenhuma duplicação da espécie nova nos slots mantidos; espécies protegidas e Snorlax são rejeitados. A exceção da Rota 13 (slots 3/4 para preservar Naganadel no 2) permanece.

Os 65 descritores originais de `6CE39C` são copiados byte a byte. O guia usa IDs **65–75**: primeira página 65, grupos 66–73, utilidades 74 e segunda página 75. A mesma lista de utilidades possui dois caminhos de script, com retornos distintos, sem variável persistente adicional. A referência da grade em `139764` não muda; nenhum código nativo de desenho/cursor/A/B/tasks é substituído.

SHA-256:

- Base v30: `58e3a53b0bed5729e02d322569bcfe4bd11c7f0161f74ef1d1347050753dba21`.
- Payload, 296 B: `e5acc441c227fe299e6b8d4d8589dd85028491e53822f676c6d47c62f53449d4`.
- ROM v31, 33.554.432 B: `fa25df630c902c7b7e155c9d8fca86f4a4674a76123b3541b68ab8eabcc84096`.

Base, política, payload e saída são verificados. Saída existente e reaplicação são recusadas. Dados originais são extraídos da base validada, não publicados como asset comercial no fonte.

## Validação

**93/93 métodos aprovados em 551.953 s**, sem falhas, erros ou skips. Payload recompilado independentemente e ROM reconstruída com resultado idêntico. Oito capturas do guia geradas na ROM exata e conferidas visualmente. Seleção:

- **10 build/dados:** oito intervalos, vetores/hashes, rejeições, saída exclusiva, tabelas nativas, prefixo anterior, slots protegidos, textos, menus e fluxo de script.
- **8 encontros:** **6.400 casos determinísticos** (100 quantis × 32 áreas × dia/noite), níveis/checksums/ABI, equivalência às 28 anteriores, Repel, água e áreas não abrangidas, helper sem flags salvas e encontros nas quatro novas áreas.
- **640 consultas pós-cap ao seletor:** 32 áreas × 10 horários de fronteira × HUD visível/oculto, sem escritas no save.
- **10 navegação:** **64 consultas** (32 áreas nos dois períodos), A/B, paginação, retornos à origem, saída em ambas as páginas, regras/período, HUD oculto, relógio e menus anteriores.
- **11 HUD + 10 preferência + 10 relógio persistente + 11 relógio anterior + 5 estojo + 4 combate + 5 gameplay/flash + 9 EV.** Incluem 1.440 horários no oráculo de pixels, 172.800 frames vivos/dois dias virtuais, 287 quantidades de TMs/HMs e saves normais sintéticos v30↔v31 antes/depois do cap, com HUD visível/oculto.

**Repel:** o controle sintético usa um líder de nível 100, acima do máximo dos slots abrangidos. Isso substitui a hipótese antiga de que todos fossem inferiores a 50, já que Ruin Valley possui um slot nativo de nível 52. Não se altera nenhum nível da ROM para acomodar o ensaio.

Novas áreas: acesso por **warps apenas em cópias de teste**, com terreno/coordenadas derivados desta ROM e conferidos pela API nativa; depois, movimento e encontros nativos. Não se escrevem RNG, espécie, nível ou HP durante a ação. Não é prova da campanha até as ilhas ou dos requisitos de acesso. Esses warps não estão na entrega.

Menus: identidade dos 65 descritores e abertura/cancelamento dos IDs 0, 15, 31, 39 e 64 em scripts temporários, não seus serviços completos. Repetição: 12 ensaios de quatro consultas consecutivas, não certificação prolongada de todos os recursos. Quantis não são frequências medidas em caminhadas aleatórias.

Captura comum admite falhas e varia apenas a espera antes do lançamento. O controle de vitória usa encontro natural adequado ao inicial, não presume vitória contra qualquer inimigo. Flash cruza versões pelo save normal, não por savestate. O teste longo usa HUD visível; controles dedicados de preferência oculta usam 120 frames. Rotinas isoladas de relógio usam o vetor v24 preservado; fluxos vivos usam os hooks atuais.

Sem certificação de campanha completa, hardware real, todos os emuladores, link real, saves pessoais ou fidelidade integral a Scarlet/Violet. Localizações da Pokédex não são reescritas por período.

## Reprodução

mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; core SHA-256 `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`. Zig **0.17.1**.

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v31/payload.ld \
  firered_gen1_9/patches/motor_v31/entry.s \
  firered_gen1_9/patches/motor_v31/motor_v31.c -o /tmp/v31.elf
python -m ziglang objcopy -O binary /tmp/v31.elf /tmp/v31.bin
cmp /tmp/v31.bin firered_gen1_9/patches/motor_v31/payload.bin
python firered_gen1_9/scripts/motor_v31.py --rom /caminho/v30.gba --saida /novo/caminho/v31.gba

MOTOR_V31_ROM=/novo/caminho/v31.gba MOTOR_V31_BASE=/caminho/v30.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v31.gba \
python firered_gen1_9/scripts/validar_motor_v31.py --jobs 3 --log /tmp/v31-final.log
```

Runner exige **93 IDs únicos**, cores/partidas isolados e nenhum skip/falha/erro; tempo consolidado de parede. `--jobs 1` executa serialmente. Capturas opcionais exigem Pillow e diretório novo:

```sh
MOTOR_V31_ROM=/novo/caminho/v31.gba MGBA_CORE=/caminho/mgba_libretro.so \
python firered_gen1_9/scripts/capturar_guia_v31.py --saida /novo/diretorio/telas
```

Capturas da ROM exata, por controles nativos em partida sintética, sem warps. ROM, saves, estados e screenshots ficam fora do Git. **Entrega local, sem publicação no Drive, commit ou push.** O arquivo v18 já existente no Drive foi apenas lido para reconstruir e conferir a cadeia até a base v30; nada novo foi enviado.
