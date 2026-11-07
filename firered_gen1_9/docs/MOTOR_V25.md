# Motor parcial v25 — horário do mundo visível

Data: 2026-11-05. Escopo: FireRed Gen1–9, sucessor **da v24 exata**. Não é o FireRed BR/BAG_MOD histórico.

## O que aparece no jogo

Um painel **HH:MM de 24 horas**, com zeros à esquerda, no canto superior direito do campo. Mede **o horário do mundo**, não a duração da partida. O dia continua tendo aproximadamente **24 minutos de jogo**; dia 06:00–19:59, noite 20:00–05:59. Não usa RTC nem avança com o emulador fechado.

O painel é de 32×16 pixels, em (204,4) na tela de 240×160. Fonte 5×7 e moldura desenhadas para este patch, sem extrair a fonte comercial. Nas transições de minuto, a atualização visual pode aparecer no próximo frame/VBlank.

Ele se oculta em diálogos, menus e batalhas nos fluxos validados. Na ajuda L/R, o próprio sistema nativo desativa a camada OBJ. O relógio do mundo continua seguindo a política de tempo da v24 enquanto sua representação está oculta. Não há botão/configuração nova.

**O tempo total jogado continua limitado a 999:59:59.** O HH:MM consulta o mesmo relógio persistente da v24 e continua mostrando os ciclos depois desse limite. Nenhuma ampliação do contador nativo ou novo campo no save.

Mantidos os encontros das **16 áreas**, guia da placa, evoluções por período, estojo/TMs, treino de EV e eventos existentes. Nenhuma área nova, recompensa ou alteração de história.

## Compatibilidade e uso

- Faça backup do save normal antes de experimentar.
- Use o menu **Continuar**, com o arquivo de save normal reconhecido pelo emulador. Não carregue savestates de outra versão.
- O HUD não grava configuração ou conteúdo próprio no save. Mantém o registro CK24 de oito bytes dentro da reserva T9X1, sem mudar formato, identificador ou CRC.
- A regra anterior de ativação segura, preservação de dados desconhecidos/corrompidos e impossibilidade de recuperar tempo já perdido continua valendo: consulte [v24](MOTOR_V24.md).
- Testes de compatibilidade usam somente flash sintética de 128 KiB, gerada pelo jogo: **v24 → v25 → v24 → v25**, abaixo e acima do limite, com equipe, mapa e itens conferidos. Isso não certifica um save pessoal nem mistura as bases BR/Gen1–9.

## Implementação e limites de recursos

Só três intervalos diferem da v24:

| Offset no arquivo | Tamanho | Finalidade |
|---|---:|---|
| `0x101664` | 8 B | Wrapper do update: chama `0x090E6009` da v24 exatamente uma vez, depois prepara/libera o HUD no thread principal |
| `0x0F1E20` | 8 B | VBlank de campo: chama `0x090DD019` da v19, preservando transferências e tintura, depois desenha o HUD |
| `0x10E8000` | 1.542 B | Código Thumb ARM7TDMI e arte original; reserva previamente `FF` até `0x10EA000` |

Vetores do payload: update `0x090E8001`, field `0x090E8009`, render `0x090E8011`, dígitos `0x090E8019`, prepare `0x090E8021`.

Alocação pelas APIs nativas: **8 tiles OBJ (256 bytes), um banco de 16 cores OBJ, tag `F925`**. Não há reserva fixa de RAM, sprite persistente em `gSprites`, janela de texto ou registro adicional no save. A alocação/liberação não ocorre no IRQ; renderização ocorre depois das seis operações do VBlank anterior.

APIs conferidas na ROM exata, não transplantadas de offsets vanilla: LoadSpriteSheet `08141FE1`, FreeSpriteTilesByTag `0814208D`, GetSpriteTileStartByTag `0814212D`, IndexOfSpriteTileTag `08142161`, LoadSpritePalette `08142231`, IndexOfSpritePaletteTag `08142331`, FreeSpritePaletteByTag `08142379`.

O carregador nativo de tiles não trata com segurança uma tabela de 64 tags lotada: o wrapper verifica espaço antes da chamada e consulta a tag depois, pois retorno zero também pode indicar tile zero válido. Falta de tiles ou paletas omite o painel; falha da paleta devolve os tiles. Reaquisição e resets separados de tiles/paleta foram exercitados.

Usa a entrada física OAM 127 somente se a entrada correspondente no buffer nativo estiver desativada ou contiver o dummy fora da tela (`00A0,0130,0C00`). **Nunca escreve o quarto halfword**, que pode pertencer à matriz afim 31. Não insere o HUD no buffer OAM nativo. Entrada ocupada: não desenha.

A transferência OAM nativa normalmente apaga a sobreposição anterior. Se ela estiver suspensa no VBlank de campo, a limpeza reconhece a geometria anterior do HUD e restaura somente os três atributos de um slot nativo ocioso. Callbacks de outras telas usam suas transferências OAM normais. Isso é uma integração com esta ROM, não um protocolo universal para plugins ou ROMs arbitrárias.

A tag não aparece nos outros patches do projeto. A busca de descritores nativos alinhados não encontrou sheet/paleta com essa tag; um candidato de template era código, com demais ponteiros inválidos. Essa inspeção estática não é prova exaustiva de todas as tags calculadas em tempo de execução.

Há custo real de VRAM, paleta e CPU. Não se promete ausência de disputa em toda cena possível da campanha. Sob os cenários de esgotamento testados, o HUD falha fechado em vez de sobrescrever recursos alheios.

## Validação

**69 métodos únicos aprovados em uma rodada final: 542.473 s, zero falhas, erros ou skips.** Veja [resultados](validacao_v25_resultados.json). Contagens não incluem tentativas anteriores de diagnóstico.

Seleção final de 69 métodos únicos:

| Grupo | Métodos |
|---|---:|
| Builder, integridade e saída exclusiva | 5 |
| HUD: dígitos, pixels, isolamento, recursos, ABI e UI | 11 |
| Relógio persistente/cap/CRC/Pokedude | 11 |
| Relógio anterior, paletas e evoluções | 11 |
| Encontros e guia das 16 áreas | 8 |
| Estojo/TMs com relógio saturado | 5 |
| Batalha, EXP e Soundproof | 4 |
| Captura/fuga/jornada e flash v24/v25 | 5 |
| Treino de EV | 9 |

Pontos verificados pela seleção: todos os 1.440 valores HH:MM no formatador; 13 horários no oráculo independente de pixels; alterações restritas aos tiles/paleta/atributos próprios; matriz afim e buffer OAM intactos; 64 tags cheias, bitmap cheio e 16 paletas ocupadas; 20 liberações/reaquisições; menus, ajuda, placa e guia; viradas 05:59→06:00, 19:59→20:00, 23:59→00:00 depois do cap; dois dias completos/172.800 frames; 3.200 casos determinísticos de encontros; 287 quantidades de TMs/HMs e flash nativa.

Probes de ABI exclusivos do relógio usam o vetor preservado da v24, para não confundir manutenção de recursos gráficos com escritas do relógio. Fluxos vivos continuam passando pelo hook novo; um teste separado compara bytes de save entre wrapper e vetor antigo e confere a ABI dos cinco vetores.

### Ajustes do ensaio, sem alterar a ROM para satisfazer testes

- O OAM nativo usa um dummy fora da tela, não apenas o bit de desativação. O primeiro protótipo conservador não aparecia; o payload final reconhece os dois casos e foi capturado visualmente.
- O libretro serializa no limite do frame antes do IRQ pendente. O teste exige o minuto novo até o frame seguinte, sem antecipar a atualização visual.
- A primeira tela de boas-vindas da ajuda exige **A**; B sozinho não a fecha. A placa extensa exige terminar sua impressão antes de fechar.
- O novo percurso determinístico selecionou **Sableye**, imune a Tackle. O ensaio natural não altera HP, stats, nível, EXP ou inimigo: escolhe **Vine Whip já aprendido** por botões. Fixtures de evolução são explicitamente sintéticas e usam **Bite**, tipo Dark, para atingir Fantasma sem ativar a prioridade Fairy de Sylveon. Não é uma alegação de legalidade da learnset desse Eevee de teste.

Não é campanha completa, teste em hardware físico, teste de todos os emuladores, link real ou certificação de fidelidade integral a Scarlet/Violet. Nenhum save pessoal usado.

## Reprodução

ROM base SHA-256: `5fe26a76ee13a85a8dbccecc61ce3f89ed7f44a49d221b8621acb4a0966e36d2`.

Payload SHA-256: `6e3bb325c44681b743550185d477ba3a1d8179c9c9fb440ac3b729b98a10582c` (1.542 B).

Saída SHA-256: `1ef4e7235a95d20b12c7f281284febbf5ff8f0b59a8886968e46c225aa43a01d` (33.554.432 B).

Na raiz do repositório, com Python e Zig 0.17.0 instalados no ambiente escolhido:

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_update \
  -Wl,-T,firered_gen1_9/patches/motor_v25/payload.ld \
  firered_gen1_9/patches/motor_v25/entry.s \
  firered_gen1_9/patches/motor_v25/motor_v25.c -o /tmp/v25.elf
python -m ziglang objcopy -O binary /tmp/v25.elf /tmp/v25.bin
cmp /tmp/v25.bin firered_gen1_9/patches/motor_v25/payload.bin
python firered_gen1_9/scripts/motor_v25.py --rom /caminho/v24.gba --saida /novo/caminho/v25.gba

MOTOR_V25_ROM=/novo/caminho/v25.gba MOTOR_V25_BASE=/caminho/v24.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v25.gba \
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
python -m unittest -v test_motor_v25 test_motor_v25_mgba \
  test_motor_v25_regressions test_motor_v25_gameplay_mgba test_treino_ev_mgba
```

A recompilação independente do payload e a reconstrução completa da ROM produziram bytes idênticos. mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`, core SHA-256 `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`. Referência pret/pokefirered `ce6406d8c2eaf46d543c8a2606de0c3cb1951982` para compreensão, não como base binária.

ROM, screenshots de jogo, flash e estados de teste ficam fora do Git. Entrega local; sem upload ao Drive, commit ou push nesta etapa.
