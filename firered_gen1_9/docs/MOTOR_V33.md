# Motor parcial v33 — 40 áreas e grutas de Kanto

2026-11-06. Base **FireRed Gen1–9 motor v32 exato**, não FireRed BR/BAG_MOD. Etapa autorizada: expansão dos encontros, preservando a distribuição anterior e a cobertura da auditoria.

## Quatro novas áreas

À noite (**20:00–05:59**), dois slots terrestres, índices 2 e 3, recebem:

| Área | Grupo/mapa | Slot 2 — 10% nominal | Slot 3 — 10% nominal | Frequência nativa |
|---|---|---|---|---:|
| Mt. Moon — 1F | 1/1 | Cleffa, nível **7** | Noibat, nível **9** | 7 |
| Mt. Moon — B1F | 1/2 | Woobat, nível **5** | Morelull, nível **6** | 5 |
| Mt. Moon — B2F | 1/3 | Mawile, nível **9** | Lunatone, nível **10** | 7 |
| Diglett's Cave — B1F | 1/37 | Sandshrew, nível **17** | Drilbur, nível **15** | 5 |

Índices começam em zero. Chances nominais antes de Repel e demais filtros. Os níveis são os da base e não foram normalizados. A frequência é um parâmetro do motor, não uma porcentagem por passo. Outros 80% dos slots ficam intactos. De dia (**06:00–19:59**) permanecem as tabelas originais.

Mantidos, entre outros, **Rotom e Clefairy** em Mt. Moon 1F, **Poltchageist** em B1F, **Dreepy** em B2F e **Diglett, Dugtrio e Spiritomb** em Diglett's Cave. Os 36 mapas anteriores conservam tabelas noturnas, níveis, eventos e slots protegidos, incluindo os lendários/Paradox e Snorlax já preservados.

As cavernas usam o **horário do mundo** para selecionar encontros, mas **não recebem escurecimento noturno adicional**: continuam com a iluminação nativa. Os quatro cabeçalhos são do tipo 4; não são convertidos para mapa externo. Água, pesca, Rock Smash e áreas não abrangidas ficam intactos. Sem alterar fósseis, treinadores, scripts de história, escadas, acessos, HMs, insígnias ou puzzles. O teste não equivale a jogar integralmente os eventos dos fósseis ou a travessia das cavernas.

As primeiras **72 linhas de política**, **864 linhas de guia** e **36 textos de consulta** permanecem iguais à v32. O [CSV completo](guia_encontros_horario_v33.csv) tem **960 linhas** (40 × 2 períodos × 12 slots); a política tem **80 substituições**. Esta distribuição é de design do projeto, não tabela oficial de Scarlet/Violet nem garantia de dificuldade equivalente.

## Guia na placa da Rota 1

**Mais areas / ilhas → Grutas de Kanto → área**.

- Primeira página: seis grupos de Kanto, Mais areas / ilhas e Horarios / sair, total oito opções.
- Segunda página: Ilhas 1,2,3; Ilhas 5,6; Bosques / Ilha 7; **Grutas de Kanto**; Voltar; Horarios / sair, total seis opções.
- Grupo novo: Mt. Moon 1F, B1F, B2F, Digletts Cave B1F e Voltar.
- A seleciona; A/B fecha a consulta individual e retorna à lista de áreas.
- B/Voltar na lista retorna à página do grupo; na segunda página retorna à primeira. B na primeira encerra.
- Horarios / sair oferece regras, Voltar e Sair. B/Voltar retorna à página de origem; Sair encerra em ambas.

As direções originais são mantidas. Depois das regras, o período é consultado novamente e o guia retorna à introdução/primeira página. A indicação de período é uma fotografia desse momento; as páginas de espécies sempre dizem **NOITE**. Nenhuma tela ultrapassa oito opções ou duas linhas de texto por página, com até 32 caracteres por linha.

Navegação sem campo persistente: caminhos de retorno no script, resultado temporário **VAR_RESULT (800D)**. Mantida a espera nativa de dois frames antes dos menus. O harness aguarda também a task de mensagem terminar após a impressão, antes de confirmar.

## Relógio e saves

MUNDO HH:MM, **START → Opções → SELECT**, preferência persistente, paletas existentes e continuidade após 999:59:59 são preservados byte a byte. Ocultar o HUD não pausa relógio nem encontros. Mantido o ciclo acelerado de aproximadamente 24 minutos jogados por dia virtual, sem RTC ou avanço offline.

Sem novo campo de save, migração, quest ou recompensa. Faça backup do save normal e use **Continuar**, não savestates de outra versão. Não misture com FireRed BR/BAG_MOD. Somente saves/estados sintéticos nos ensaios, nunca dados pessoais.

## Integração e integridade

Builder completo `scripts/motor_v33.py`; núcleo de encontros `scripts/motor_v33_encontros.py`; payload `patches/motor_v33/`, compilado com **Zig 0.17.1**, `-Wall -Wextra -Werror`.

| Offset no arquivo | Tamanho | Conteúdo |
|---|---:|---|
| `1393B0` | 4 B | Literal da tabela do menu vertical |
| `164340` | 8 B | Hook do gerador terrestre |
| `7C20D8` | 4 B | Ponteiro do script da placa |
| `1107000` | 296 B | Payload Thumb |
| `1108000` | 2.720 B | 40 descritores/tabelas noturnas |
| `1109000` | 1.160 B | Descritores originais + 13 listas e ações |
| `1109600` | 1.399 B | Script do guia |
| `110A000` | 2.817 B | Textos e rótulos |

Somente **oito intervalos**, todos os bytes externos idênticos à base. Reservas exigidas `FF`: `1107000..1109000` e `1109000..110C000`. Preservados tabelas nativas, payloads anteriores, hooks de relógio/HUD/Opções e scripts de história.

Vetores `09107001` seletor, `09107009` encontro, `09107011` noite e `09107019` helper da placa. Trampoline `09107020`, retorno `08164349`. O seletor exige tipo terrestre, ponteiro original, grupo/mapa e ponteiro de save válido. Não sorteia RNG nem cria Pokémon; slot, nível, Repel e geração ficam nativos.

Política anterior obrigatória como prefixo. Slots substituídos precisam ter 10%, espécies comuns e nenhuma duplicação das novas espécies nos slots mantidos. Espécies protegidas e Snorlax são rejeitados. Mantida a exceção da Rota 13, slots 3/4 para preservar Naganadel no 2.

65 descritores nativos de `6CE39C` copiados integralmente. IDs **65–77**: primeira página 65, dez grupos 66–75, utilidades 76 e segunda página 77. Utilidades com dois caminhos de retorno. Referência de grade `139764` intacta; desenho, cursor, A/B e tasks permanecem nativos.

SHA-256:

- Base v32: `7c095be4d52eeb728600eafbe2f57b60a4a402c11fe9a84cc19a8bbf61aa6d13`.
- Payload, 296 B: `e3c58aa877b5d98ebfd6f0f054961d871dba6ee16dea4cd6a7acd273169cd54c`.
- ROM v33, 33.554.432 B: `dc3d076a9645b22e49f366c477929e50ee06e1df836c19b4f418fe7b2e44ddaf`.

Entrada, política, payload e saída verificados. Saída existente e reaplicação recusadas. Dados originais extraídos da base validada, não publicados como assets comerciais no fonte.

## Validação

**99/99 métodos aprovados em 676.638 s**, sem falhas, erros ou skips. Payload recompilado independentemente e ROM reconstruída com resultado idêntico. Nove capturas do guia geradas na ROM exata e conferidas visualmente. Seleção:

- **10 build/dados:** intervalos, hashes/vetores, rejeições, saída exclusiva, tabelas nativas, prefixos, slots mantidos, layout, menus e fluxo de script.
- **8 encontros:** **8.000 casos determinísticos** (100 quantis × 40 áreas × dia/noite), níveis/checksums/ABI, equivalência às 36 anteriores, Repel, água/locais não abrangidos, helper sem flags salvas e encontros nativos nas quatro cavernas.
- **800 consultas pós-cap:** 40 áreas × 10 horários de fronteira × HUD visível/oculto, sem escritas no save.
- **10 guia:** **80 consultas** (40 áreas × dois períodos), A/B, paginação, retorno à origem, saída, regras/período, HUD oculto, relógio e menus antigos.
- **11 HUD + 10 preferência + 10 relógio persistente + 11 relógio anterior + 5 estojo + 4 combate + 5 gameplay/flash + 9 EV.** Incluem 1.440 horários no oráculo de pixels, 172.800 frames vivos, 287 quantidades de TMs/HMs e saves normais sintéticos v32↔v33 antes/depois do cap.
- **6 regressões da auditoria anterior:** 12 capturas seguidas de save/reinicialização nas quatro áreas das ilhas adicionadas na v32; quatro trocas de período ao vivo em Berry Forest; duas travessias locais de ida e volta da conexão de Sevault com save. Não são capturas nas novas cavernas nem prova da campanha inteira. Novos ensaios de captura da auditoria usam Master Ball para verificar o caminho, não catch rate; Poké Ball comum continua nos cinco métodos de gameplay.

### Cavernas: caminho vivo e iluminação

Na primeira rodada, 98/99 métodos passaram; o roteiro de chegada falhou nas quatro cavernas por exigir o callback de campo enquanto a transição nativa ainda estava ativa. Foi corrigido somente o harness: aproximação por botões, espera limitada e exigência simultânea de destino correto e callback de campo antes de salvar. O ensaio focado das quatro cavernas passou em **133.791 s**. Nenhum byte da ROM foi alterado por essa correção.

O terreno é lido desta ROM: cabeçalho tipo 4, atributo de encontro terrestre 1, piso comum de comportamento 8 e sem colisão. São evitadas escadas/warps e escolhidos pontos com vizinhos para caminhar, afastados de NPCs. A classificação do terreno é conferida pela API nativa após o carregamento.

A chegada é abreviada por um warp em **cópia descartável**, iniciada do próprio boot. Apenas dois intervalos da cópia diferem; restaurá-los deve reproduzir integralmente a ROM exata. Depois da chegada, save normal, fechamento do core e carregamento desse flash por Continuar na **ROM exata v33**. Nenhum savestate atravessa dessa cópia para a entrega. Mapa, coordenadas, inicial e callback são conferidos.

Na ROM exata, dois ensaios de **120 frames parados por caverna**, dia/noite, devem avançar dois segundos jogados (dois minutos do mundo) e manter iguais as primeiras **208 cores de terreno** da paleta. Depois, caminhada nativa noturna encontra ambos os novos alvos com espécie, nível e checksum válidos. Durante a ação não se editam RNG, mon, nível ou HP. O orçamento de espera/caminhada é maior que nas áreas externas, por causa das frequências nativas 5/7, sem aumentá-las na ROM.

A preparação da jornada usa Repel sintético; o inicial não é superior aos níveis dos alvos novos. O controle separado de Repel usa líder sintético de nível 100, acima de todos os slots abrangidos. Nenhum nível da ROM muda para acomodar o teste.

### Limites

Quantis não são frequências medidas em caminhadas aleatórias. Menus antigos são abertos/cancelados nos IDs 0, 15, 31, 39 e 64, não seus serviços completos; os 65 descritores são comparados. Guia repetido em 12 ensaios de quatro consultas consecutivas, não um teste prolongado de todos os recursos.

Saves entre versões passam por flash normal, nunca por savestate. O ensaio longo usa HUD visível; controles dedicados de preferência oculta usam 120 frames. Rotinas isoladas de relógio usam o vetor v24 preservado; fluxos vivos usam os hooks atuais.

Sem certificação de campanha completa, fósseis, treinadores, travessia integral das grutas, Lostelle, acesso normal às ilhas, hardware real, todos os emuladores, link real, saves pessoais ou fidelidade integral a Scarlet/Violet. Localizações da Pokédex não são reescritas por período.

## Reprodução

mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; core SHA-256 `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`.

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v33/payload.ld \
  firered_gen1_9/patches/motor_v33/entry.s \
  firered_gen1_9/patches/motor_v33/motor_v33.c -o /tmp/v33.elf
python -m ziglang objcopy -O binary /tmp/v33.elf /tmp/v33.bin
cmp /tmp/v33.bin firered_gen1_9/patches/motor_v33/payload.bin
python firered_gen1_9/scripts/motor_v33.py --rom /caminho/v32.gba --saida /novo/caminho/v33.gba

MOTOR_V33_ROM=/novo/caminho/v33.gba MOTOR_V33_BASE=/caminho/v32.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v33.gba \
python firered_gen1_9/scripts/validar_motor_v33.py --jobs 3 --log /tmp/v33-final.log
```

Runner exige **99 IDs únicos**, nenhum skip/falha/erro, cores/partidas isolados; tempo consolidado de parede. `--jobs 1` executa serialmente. Capturas opcionais exigem Pillow e diretório novo:

```sh
MOTOR_V33_ROM=/novo/caminho/v33.gba MGBA_CORE=/caminho/mgba_libretro.so \
python firered_gen1_9/scripts/capturar_guia_v33.py --saida /novo/diretorio/telas
```

Capturas do guia na ROM exata, por controles nativos em partida sintética, sem warps. ROM, saves, estados e screenshots fora do Git. **Entrega local, sem publicação no Drive, commit ou push.**
