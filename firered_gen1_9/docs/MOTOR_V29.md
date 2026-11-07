# Motor parcial v29 — 24 áreas por horário, com guia navegável

2026-11-05. Base **FireRed Gen1–9 motor v28 exato**. Não misturar com FireRed BR/BAG_MOD.

## Novas áreas

À noite, **20:00–05:59**, dois slots de grama passam a usar:

| Área | Slot 2 (10% nominal) | Slot 3 (10% nominal) | Frequência terrestre nativa |
|---|---|---|---:|
| Rota 17 | Raticate, nível 22 | Mightyena, nível 26 | 21 |
| Rota 18 | Noctowl, nível 22 | Liepard, nível 26 | 21 |
| **Rota 21 Norte** | Shiinotic, nível 24 | Phantump, nível 21 | 14 |
| Rota 23 | Honchkrow, nível 34 | Houndoom, nível 34 | 21 |

Índices de slots começam em zero. Chance nominal de cada substituição: **10% antes de Repel e outros filtros**, não garantia por caminhada. O campo de frequência é um parâmetro nativo, não uma porcentagem de encontro por passo. Os outros slots, os níveis e a frequência de cada mapa ficam intactos.

**Rota 21 Sul não foi expandida.** Rotas 19 e 20 permanecem aquáticas e fora desta etapa. Água/pesca, cavernas e áreas não incluídas continuam sem política nova. De dia, **06:00–19:59**, todas as tabelas anteriores são mantidas.

Na Rota 23 permanecem **Raging Bolt (slot 4, nível 32, 10%)** e **Umbreon (slot 5, nível 34, 10%)**. Também permanecem Naganadel na Rota 13, Iron Valiant na Rota 14, Snorlax na Rota 15 e Poipole na Rota 9, além de todos os eventos e bloqueios de história. Não se alteram exigências de bicicleta, Surf, insígnias ou acesso à Liga para acomodar a expansão.

São **24 áreas**, mantendo a política das 20 anteriores. As 40 linhas anteriores da política e as primeiras 480 linhas do guia completo permanecem idênticas. O novo [guia CSV](guia_encontros_horario_v29.csv) possui **576 linhas** (24 × 2 períodos × 12 slots); `data/encontros_horario_v29.csv` possui 48 substituições. Distribuição de design deste projeto, não tabela oficial nem garantia de equilíbrio equivalente a Scarlet/Violet.

## Guia da placa da Rota 1

Mantida a navegação da v28, agora com o grupo **Rotas 17,18,21N,23**. Escolha **grupo → área**; cada consulta mostra seu par **NOTURNO**. As 20 consultas anteriores não mudam.

- **A:** selecionar; **A/B:** fechar a consulta e voltar à lista de áreas.
- **B/Voltar:** retornar ao menu de grupos.
- **B/Sair**, no menu principal: encerrar e devolver o controle ao jogador.
- **Horarios / regras:** faixas de horário, chance nominal, filtros e funcionamento do relógio.

As direções originais da placa continuam antes da introdução. O período da introdução é consultado ao entrar e ao terminar as regras; não é atualização contínua durante a leitura. As páginas de espécies sempre dizem NOITE, mesmo se consultadas de dia. O menu principal passa de sete para **oito opções**, dentro do suporte nativo; são sete listas de menu ao todo (principal + seis grupos).

Mantida a espera nativa de dois frames antes de cada menu. Nos testes, aguarda-se também a finalização da task nativa de mensagem, que ocorre depois do fim da impressão, antes de enviar a confirmação. Não se altera a lógica de impressão nem se reintroduz a sequência linear de todas as rotas.

## Relógio, HUD e saves

**MUNDO HH:MM**, **START → Opções → SELECT**, preferência persistente e continuidade após 999:59:59 permanecem byte a byte como na v28. Ocultar o HUD não pausa tempo, encontros ou paletas. Mantidos os aproximadamente 24 minutos jogados por dia virtual; sem RTC ou avanço offline.

Sem novo campo de save, migração, recompensa, quest ou flag permanente. O guia utiliza somente **VAR_RESULT (800D)**, temporário. Faça backup do save normal e carregue por **Continuar**; não reutilize savestates de outra versão. Apenas dados sintéticos são usados nos testes, nunca saves pessoais.

## Integração técnica

Builder completo: `scripts/motor_v29.py`. Núcleo de dados/patch de encontros: `scripts/motor_v29_encontros.py`. Payload próprio em `patches/motor_v29/`, compilado com **Zig 0.17.1**.

| Offset no arquivo | Tamanho | Conteúdo |
|---|---:|---|
| `1393B0` | 4 B | Literal do menu vertical, apontando para a lista ampliada |
| `164340` | 8 B | Hook do gerador terrestre nativo |
| `7C20D8` | 4 B | Ponteiro do script da placa |
| `10F3000` | 296 B | Payload Thumb de seleção, wrapper, período e helper da placa |
| `10F4000` | 1.632 B | 24 descritores e tabelas noturnas |
| `10F5000` | 880 B | 65 descritores nativos preservados + sete listas novas e ações |
| `10F5400` | 807 B | Script navegável |
| `10F6000` | 1.575 B | Textos e rótulos |

Somente **oito intervalos**. Reservas exigidas `FF` na base: encontros `10F3000..10F4800`, guia `10F5000..10F8000`. Dados são gerados a partir da base SHA-verificada. Todos os payloads anteriores, os hooks de relógio/HUD/Opções, as tabelas nativas e os bytes fora desses intervalos permanecem intactos.

Vetores: `090F3001` seletor, `090F3009` encontro, `090F3011` noite e `090F3019` helper da placa. O trampoline do gerador original continua a partir de `090F3020` e retoma em `08164349`. O seletor verifica tipo terrestre, ponteiro original, grupo/mapa corrente e ponteiro válido do save; não chama RNG nem cria Pokémon. Seleção do slot, nível, Repel e geração permanecem nativos.

Política: dois slots comuns de 10%, sem duplicar a espécie nova entre slots retidos; a exceção anterior da Rota 13 (slots **3 e 4**, protegendo Naganadel no 2) permanece. Rejeitam-se espécies protegidas na origem/destino e Snorlax explicitamente. O prefixo da política anterior é obrigatório.

Menu: os primeiros **65 descritores** de `6CE39C` são preservados byte a byte. IDs **65–71** são usados pelo guia; não há substituição de IDs nativos. A referência da grade em `139764` não muda. Nenhum código nativo de desenho, cursor, A/B, tasks ou liberação de janela é substituído.

### SHA-256

- Base v28: `e7d11016a5c17f226ce05bc89142d52daeeee46b90c87b4b0fba29085e50cd16`.
- Payload (296 bytes): `9c2e9d8aa929662b1cb566e6ac781995efbf0fb386c11d051f3bbc4e57996ca0`.
- ROM v29 (33.554.432 bytes): `c8e9fd9e4269f31c462d3273c08b11996f8e229a5b20a2306e99f516bf5d2528`.

## Validação

**90 métodos únicos aprovados: 544.231 s de parede, três processos isolados, zero falhas, erros ou skips.** [Resultados](validacao_v29_resultados.json) e [log integral](validacao_v29.log). Seleção:

- **10 build/dados:** oito intervalos, vetores e hashes, corrupção/reaplicação recusadas, saída exclusiva, tabelas nativas, preservação da política/20 tabelas noturnas/guia anterior, espécies protegidas e menus/scripts.
- **8 encontros:** 4.800 casos determinísticos (100 quantis × 24 áreas × dia/noite), níveis/checksums/ABI, equivalência às 20 áreas anteriores, Repel, água e áreas não abrangidas, helper sem flags permanentes e encontros nas quatro áreas novas.
- **480 consultas pós-cap ao seletor**: 24 áreas × 10 horários de fronteira × HUD visível/oculto. O seletor não escreve no save.
- **7 navegação:** 24 áreas nos dois períodos (**48 consultas**), A/B, Voltar/Sair, wrap, regras, período, HUD oculto, relógio, menus existentes e controle devolvido ao jogador.
- **11 HUD + 10 preferência + 10 relógio persistente + 11 relógio anterior + 5 estojo + 4 combate + 5 gameplay/flash + 9 EV.** Incluem os 1.440 horários no oráculo de pixels, 172.800 frames vivos/dois dias virtuais, 287 quantidades de TMs/HMs e saves normais sintéticos v28↔v29 antes/depois do cap, com HUD visível/oculto.

Os encontros das novas áreas são exercitados por **warps somente em cópias de teste**, seguidos de movimento e encontros nativos. Terreno/coordenadas são obtidos desta ROM e conferidos pela API nativa. Não se escrevem RNG, espécie, nível ou HP durante a ação. Isso não prova a progressão, bicicleta, Surf ou coleta das insígnias até essas áreas. A ROM entregue não contém esses warps.

Compatibilidade dos menus nativos: identidade dos 65 descritores e abertura/cancelamento dos IDs 0, 15, 31, 39 e 64 usando scripts temporários de teste. Não é teste funcional completo das lojas, torre ou link. Repetição do guia: 12 ensaios com quatro consultas consecutivas, não certificação de longa duração de todos os recursos.

Quantis não são frequências medidas em caminhadas aleatórias. Captura comum admite falhas e procura controle positivo variando apenas a espera antes do lançamento. O controle de vitória usa encontro natural adequado ao inicial, sem presumir que ele vença qualquer inimigo. Os testes de flash cruzam versões pelo save normal, não por savestate; estados sintéticos são usados apenas nos ensaios controlados.

Sem certificação de campanha completa, hardware físico, todos os emuladores, link real, saves pessoais ou fidelidade integral a Scarlet/Violet. O teste longo de dois dias usa preferência visível; os controles dedicados de HUD oculto usam 120 frames. Rotinas isoladas de relógio usam o vetor v24 preservado; fluxos vivos passam pelos hooks atuais. Não se reescrevem localizações da Pokédex por período.

## Reprodução

mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; core SHA-256 `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`. Zig **0.17.1** para reconstruir o payload idêntico.

```sh
python -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -mthumb \
  -Os -ffunction-sections -fdata-sections -fno-builtin -nostdlib \
  -Wall -Wextra -Werror -Wl,--gc-sections -Wl,--nmagic -Wl,-e,entry_select \
  -Wl,-T,firered_gen1_9/patches/motor_v29/payload.ld \
  firered_gen1_9/patches/motor_v29/entry.s \
  firered_gen1_9/patches/motor_v29/motor_v29.c -o /tmp/v29.elf
python -m ziglang objcopy -O binary /tmp/v29.elf /tmp/v29.bin
cmp /tmp/v29.bin firered_gen1_9/patches/motor_v29/payload.bin
python firered_gen1_9/scripts/motor_v29.py --rom /caminho/v28.gba --saida /novo/caminho/v29.gba

MOTOR_V29_ROM=/novo/caminho/v29.gba MOTOR_V29_BASE=/caminho/v28.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v29.gba \
python firered_gen1_9/scripts/validar_motor_v29.py --jobs 3 --log /tmp/v29-final.log
```

O runner exige **90 IDs únicos**, cores/partidas isolados e nenhum skip/falha/erro. Tempo consolidado é de parede; `--jobs 1` executa serialmente. Capturas opcionais exigem Pillow e um diretório novo:

```sh
MOTOR_V29_ROM=/novo/caminho/v29.gba MGBA_CORE=/caminho/mgba_libretro.so \
python firered_gen1_9/scripts/capturar_guia_v29.py --saida /novo/diretorio/telas
```

Capturas da ROM exata, por controles nativos em partida sintética, sem warps. ROM, saves, estados e imagens ficam fora do Git. **Entrega local, sem publicação no Drive, commit ou push.** O arquivo v18 existente no Drive foi somente lido para reconstruir a cadeia até a base v28 e conferir todos os hashes; nada novo foi enviado.
