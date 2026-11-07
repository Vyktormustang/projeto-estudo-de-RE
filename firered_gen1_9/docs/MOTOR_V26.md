# Motor parcial v26 — MUNDO HH:MM e controle de visibilidade

2026-11-05. Base: **FireRed Gen1–9 motor v25 exato**, não o FireRed BR/BAG_MOD histórico.

## Uso

O painel continua no canto superior direito, com **MUNDO** acima do **HH:MM**. Mantém os mesmos 32×16 pixels e os mesmos recursos gráficos da v25. A legenda distingue o horário virtual da duração total da partida.

Para mostrar/ocultar:

1. Durante a partida, abra **START → Opções**.
2. Pressione **SELECT**: o cabeçalho alterna entre **MUNDO SIM** e **MUNDO NAO**.
3. Saia com B. A escolha já vale na sessão.
4. Use **SALVAR** normalmente para conservar a escolha após fechar o jogo.

Segurar SELECT não alterna repetidamente. O controle é exclusivo dessa tela: SELECT no campo continua sendo a ação nativa do item registrado. Direcionais, A/B, ajuda L/R e modos de botão continuam com suas funções anteriores. Não há novo atalho de campo.

**Ocultar o painel não pausa o relógio.** Mantidos os aproximadamente 24 minutos jogados/dia, os períodos 06:00–19:59 / 20:00–05:59 e a continuidade depois de 999:59:59. O contador nativo de tempo jogado permanece nesse limite. Sem RTC ou avanço offline.

Saves anteriores começam com o painel visível. O controle só é habilitado nas Opções abertas pela partida normal; na tela de título ou diante de dados desconhecidos/corrompidos pode aparecer **SELECT: BLOQ.** Nenhum dado é reparado ou sobrescrito para forçar a preferência. Uma preferência inválida usa exibição visível como fallback, sem regravar o registro.

Faça backup do save normal. Carregue pelo menu **Continuar**, não por savestate de outra versão. Nenhum save pessoal foi usado na validação.

## Escopo preservado

Não foram ampliados encontros, áreas, história, recompensas ou mecanismos de combate. Mantidas as 16 áreas, guia, TMs/estojo, EV, paletas e evoluções por horário. As regras do relógio persistente da [v24](MOTOR_V24.md) continuam valendo.

A v25 ignora a nova preferência e exibe seu HUD antigo. Em flash sintética v26→v25→v26, a preferência é preservada e volta a ser respeitada ao retornar à v26. Isso não é recomendação para reutilizar savestates entre versões.

## Registro persistente

A preferência usa **os oito bytes finais da reserva T9X1 já existente**, sem aumentar SaveBlock1 nem o arquivo flash:

| Conteúdo | Offset relativo ao SaveBlock1 |
|---|---|
| Quantidades T9X1 e reserva anterior | `+34D8` em diante |
| Relógio CK24, inalterado | `+3658..365F` |
| Preferência HUD6 | `+3660..3667` |
| Fim da reserva de 400 bytes | `+3668` exclusivo |

Registro HUD6: magic `36445548` (`HUD6`, little-endian), seguido por `26A5FF00` (visível) ou `26A5FE01` (oculto). O byte de valor tem complemento; todos os 64 erros de um bit do registro são rejeitados. **Não é autenticação criptográfica** nem prova de detectar toda corrupção multibit.

O getter não inicializa, migra nem repara dados. A primeira alteração explícita de preferência pode inicializar T9X1 por meio da migração existente do estojo: ela valida todos os 400 bytes e as pilhas legadas antes de mover qualquer quantidade. Isso ocorre somente nas Opções da partida normal, com ponteiros válidos, estado ativo, sem fade e sem link ocupado. Não ocorre automaticamente ao andar, abrir o cabeçalho ou visitar uma mochila temporária. CK24 e quantidades não são usados para guardar a preferência.

Magic é publicada por último; alternâncias de um registro válido mudam apenas a palavra de valor. No caso já inicializado, o teste compara todo o save e admite mudanças exclusivamente nesses oito bytes. O arquivo flash permanece com **131.072 bytes**.

## Integração binária

Cinco intervalos alterados sobre a v25:

| Offset no arquivo | Bytes | Função |
|---|---:|---|
| `101664` | 8 | Update: chama o relógio v24 uma vez e prepara/libera o painel |
| `0F1E20` | 8 | VBlank de campo, preservando a cadeia nativa/v19 |
| `0EFB1C` | 8 | Cabeçalho de Opções: mantém OPÇÕES e acrescenta o estado/controle |
| `0EF890` | 8 | Input de Opções: SELECT isolado; demais entradas seguem o código original |
| `10EA000` | 2.509 | Payload Thumb/arte original; reserva FF até `10EC000` |

Vetores a partir de `090EA001`, em passos de oito bytes: update, field, render, digits, prepare, header, input, preference, toggle. Nenhuma tabela de encontros ou rotina de batalha é substituída.

O trampoline de input reproduz as quatro instruções deslocadas. Reloca o literal de `gMain`, conserva os flags de LSLS para o BPL nativo e restaura R4 pelo epílogo original. Testes percorrem os ramos de direita/esquerda/cima/baixo/A/B, incluindo o item Moldura e combinações com SELECT.

Endereços auditados na ROM exata: Options callback `080EF379`, saved callback de retorno ao campo `080F1B99`, ponteiro da estrutura `020399B0`, IsActiveOverworldLinkBusy `080E164D`, FillWindowPixelBuffer `081658B5`, AddTextPrinterParameterized `08147991`, AddTextPrinterParameterized3 `080E0DAD`, PutWindowTilemap `08165461`, CopyWindowToVram `08165411`. Os nomes da referência não serviram para transplantar endereços vanilla.

Mantidos da v25: tag privada `F925`, oito tiles OBJ/256 bytes, um banco de paleta, OAM 127 somente quando desativado/dummy, preservação do quarto halfword da matriz afim, ausência de sprite persistente ou RAM fixa própria. A legenda é arte original 5×5; dígitos 5×7. Campo em modo gráfico incompatível, slot ocupado ou recursos esgotados: não desenha. Os limites de integração/recurso descritos na [v25](MOTOR_V25.md) continuam aplicáveis.

## Validação

**80 métodos únicos aprovados na rodada final paralela (3 processos isolados): 383.336 s, zero falhas, erros ou skips.** Veja [resultados](validacao_v26_resultados.json). Seleção:

- 5 de builder, integridade, vetores e saída exclusiva;
- 12 de HUD/ABI/recursos/contextos, com **1.440 horários no formatador e no oráculo independente de pixels**, incluindo a legenda;
- 10 de preferência: SELECT, hold, navegação/modos, escrita restrita, 64 corrupções, dados estrangeiros, migração, contextos bloqueados, tempo oculto e flash;
- 11 do relógio persistente e 11 do relógio anterior/paletas/evoluções;
- 8 de encontros/guia, com 3.200 casos nas 16 áreas;
- 5 do estojo/TMs, agora com **CK24 ativo e preferência oculta simultaneamente**;
- 4 de combate/EXP/Soundproof, 5 de captura/fuga/jornada/compatibilidade e 9 de EV.

Flash sintética: v25→v26→v25→v26 para o padrão visível e v26→v26→v25→v26 para a preferência oculta; abaixo e acima do cap. Conferidos equipe, itens, preferência, progressão e retorno ao campo. Na v25 intermediária, o HUD fica visível por design, sem apagar HUD6.

Dois dias completos do mundo (172.800 frames) fazem parte da seleção anterior. Os testes específicos de ocultação exigem continuidade por 120 frames antes/depois do cap e nas recargas de flash. Não se confunde esse ensaio curto oculto com dois dias inteiros ocultos.

Probes isolados de relógio usam o vetor preservado v24; fluxos vivos usam o wrapper novo. O controle de vitória natural varia somente a espera inicial para encontrar um inimigo de nível até 3, sem resistência/imunidade a Tackle, e usa o golpe já aprendido. Não edita RNG, espécie, HP, nível, stats, golpes ou EXP. Não exige que o inicial vença qualquer adversário: o primeiro ensaio escolheu Pidgey nível 5 e tentou Vine Whip resistido; isso não era um controle confiável de vitória. Eevee de evolução é uma fixture sintética com Bite, para não confundir a imunidade Fantasma a Tackle com falha de evolução.

Poké Ball comum pode falhar: o controle de captura varia somente a espera antes do lançamento na mesma batalha sintética, confere consumo também nas falhas e exige um sucesso com identidade/metadados corretos. Não é estimativa de probabilidade e não modifica RNG ou HP.

Capturas reais de mGBA mostram MUNDO 10:00, Opções SIM/NAO, campo oculto e retorno do painel. Não há certificação da campanha inteira, hardware físico, todo emulador, link real ou saves pessoais. Nenhuma promessa de fidelidade integral a Scarlet/Violet.

## Integridade e reprodução

- Base v25: `1ef4e7235a95d20b12c7f281284febbf5ff8f0b59a8886968e46c225aa43a01d`.
- Payload: `cca07e6aed6e1c5e0f383ba025d4cbcba9b450e5b46ca25559eb5b8a76e09617`, 2.509 B.
- ROM v26: `ffba283f8d01885f9a8a3d5300135adeae008e6434a7c5c80ec7f695c1445ba7`, 33.554.432 B.
- Zig 0.17.0, Thumb ARM7TDMI, `-Os`, sem libc. Recompilação independente do payload e da ROM: bytes idênticos.
- mGBA libretro 0.10.5, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`, SHA-256 do core `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`.

Na raiz do repositório:

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_update \
  -Wl,-T,firered_gen1_9/patches/motor_v26/payload.ld \
  firered_gen1_9/patches/motor_v26/entry.s \
  firered_gen1_9/patches/motor_v26/motor_v26.c -o /tmp/v26.elf
python -m ziglang objcopy -O binary /tmp/v26.elf /tmp/v26.bin
cmp /tmp/v26.bin firered_gen1_9/patches/motor_v26/payload.bin
python firered_gen1_9/scripts/motor_v26.py --rom /caminho/v25.gba --saida /novo/caminho/v26.gba

MOTOR_V26_ROM=/novo/caminho/v26.gba MOTOR_V26_BASE=/caminho/v25.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v26.gba \
PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
python -m unittest -v test_motor_v26 test_motor_v26_mgba \
  test_motor_v26_preferences_mgba test_motor_v26_regressions \
  test_motor_v26_gameplay_mgba test_treino_ev_mgba
```

A rodada final também pode ser reproduzida em processos isolados, com as mesmas variáveis de ambiente: `python firered_gen1_9/scripts/validar_motor_v26.py --jobs 3 --log /tmp/v26-parallel-final.log`. O runner exige exatamente 80 IDs únicos, não aceita skips como aprovação e reúne os resultados em um log. O tempo consolidado é de parede; cada grupo inicializa seu próprio core e sua própria partida sintética.

ROM, screenshots comerciais e estados/flash sintéticos ficam fora do Git. Entrega local, sem publicação no Drive, commit ou push.
