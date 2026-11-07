# Motor parcial v28 — guia consultável por grupo e área

2026-11-05. Base **FireRed Gen1–9 motor v27 exato**. Não usar FireRed BR/BAG_MOD.

## Como consultar

Na **placa da Rota 1**, leia as direções originais e a introdução do guia. Depois:

1. Escolha um grupo: **Rotas 1/2/22 e Floresta**, **3/4/24/25**, **5–8**, **9–12** ou **13–16**.
2. Escolha a área. Uma única página mostra seu par de encontros **NOTURNOS**.
3. **A ou B** fecha essa consulta e retorna à lista de áreas.
4. **B** ou **Voltar** retorna ao menu de grupos; **B** ou **Sair** no menu principal fecha o guia.

Há também **Horarios / regras**, com as faixas dia/noite, chance nominal, filtros e comportamento do relógio. O período da introdução é uma fotografia do momento em que foi consultado, não um indicador em tempo real; é recalculado ao entrar no guia e ao terminar a leitura das regras. As páginas de espécies estão sempre identificadas como **NOITE**, mesmo se consultadas de dia.

Isso substitui a sequência obrigatória da lista inteira por uma escolha de grupo e área. Não transforma a placa em Pokédex: a distribuição completa de dia/noite, com níveis e todos os slots, continua no [CSV de 480 linhas da v27](guia_encontros_horario_v27.csv).

## O que não muda

- **20 áreas**, mesmos pares noturnos, chances, níveis, frequência e filtros da v27; nenhuma área nova.
- Naganadel, Iron Valiant, Snorlax, Poipole, eventos e bloqueios de história preservados.
- Tabelas diurnas, água/pesca, evoluções, TMs/HMs, estojo, EV e combate inalterados.
- **MUNDO HH:MM**, controle **START → Opções → SELECT**, preferência persistente e continuidade após 999:59:59 mantidos byte a byte.
- Ocultar o HUD não pausa o relógio nem os encontros. Sem RTC ou avanço offline.
- Nenhum campo novo no save, recompensa, quest ou flag permanente. O único resultado de script utilizado é o temporário **VAR_RESULT (800D)**, compartilhado com os menus nativos.

Faça backup do **save normal** e carregue por **Continuar**. Não reutilize savestates de outra versão nem misture com FireRed BR/BAG_MOD. Os ensaios usam somente dados sintéticos, nunca saves pessoais.

## Implementação e auditoria

**Sem código ARM/Thumb novo.** O builder gera dados de menu, textos e script nativo e altera apenas cinco intervalos:

| Offset no arquivo | Tamanho | Alteração |
|---|---:|---|
| `1393B0` | 4 B | Literal da tabela usado pelo menu vertical nativo |
| `7C20D8` | 4 B | Ponteiro do script da placa da Rota 1 |
| `10F0000` | 824 B | Cópia dos 65 descritores originais + seis novos menus e suas ações |
| `10F0400` | 686 B | Script navegável |
| `10F1000` | 1.356 B | Introdução, regras, consultas e rótulos |

Reserva `10F0000..10F3000` exigida inteiramente `FF` na base. Todos os demais bytes permanecem idênticos, inclusive payloads e hooks de encontros, relógio, HUD e Opções.

A tabela real da ROM foi localizada em `6CE39C`, **65 entradas de 8 bytes**. Seus contadores não são simplesmente os da fonte vanilla: por exemplo, o menu de prêmios de Pokémon tem seis entradas nesta ROM. Os 520 bytes originais são copiados sem alterar ponteiros, contadores ou padding. Os IDs **65–70** são acrescentados, sem substituir um menu existente. Seus callbacks de ação são nulos, como esperado pelo seletor de scripts.

A desmontagem da ROM exata confirma `08139296: ldr r3, [pc, #0x118]`, que lê o literal em `1393B0`; em seguida o índice é multiplicado por oito e são lidos contador/lista. Somente esse literal é redirecionado. A segunda referência, `139764`, usada pelo menu em grade, continua apontando à tabela original. Não se amplia a grade nem se usa um ID novo nela.

Menus de até sete opções reutilizam desenho, cursor, wrap, A/B, tasks e liberação de janela nativos. O script congela os objetos enquanto está aberto e libera o controle ao sair. **Antes de abrir cada menu há uma espera nativa de dois frames**, evitando que o A/B usado para fechar a mensagem também selecione/cancele o menu recém-criado. É uma proteção contra reaproveitamento da entrada. Separadamente, o diagnóstico mostrou que a task nativa da mensagem termina um frame após o fim da impressão: o teste espera dois frames sem botões antes de confirmar a caixa, em vez de confundir texto completo com entrada já pronta. A lógica nativa de impressão não foi alterada.

Referência de semântica: `pret/pokefirered`, `script_menu.c`, `scrcmd.c` e macros de eventos. Offsets e contagens foram obtidos da ROM expandida, não transplantados da referência. O resultado é um guia de design deste projeto, não uma afirmação de fidelidade integral a Scarlet/Violet.

### Integridade

- Base v27: `f48ce3b2b4328637d47004722907ca9bfb5b6e523f1ed8a6b1bfbe93fd266673`.
- Saída v28, 33.554.432 bytes: `e7d11016a5c17f226ce05bc89142d52daeeee46b90c87b4b0fba29085e50cd16`.
- Sem payload binário adicional. Dados de menu antigos são extraídos somente da base SHA-verificada; não são armazenados como asset comercial no código-fonte.
- Builder recusa base diferente, reaplicação, reserva ocupada e saída já existente.

## Validação

**87 métodos únicos aprovados: 621.929 s de parede, três processos isolados, zero falhas, erros ou skips.** [Resultados](validacao_v28_resultados.json) e [log integral](validacao_v28.log). Seleção:

- **7 contratos de build/dados:** cinco intervalos, 65 menus preservados, seis listas novas válidas, fluxo de script com destinos internos e comandos restritos, texto/política, saída exclusiva e reconstrução determinística.
- **7 de navegação nativa:** 20 áreas nos dois períodos (**40 consultas**), retornos por A/B, Voltar/Sair, wrap, regras completas e atualização do período, preferência oculta/clock pós-cap, repetições e controle devolvido ao jogador.
- Os testes de consulta comparam o SaveBlock1 inteiro durante a leitura em condição pré-cap, sem escritas em flags salvas. O relógio nativo de tempo jogado continua a avançar no SaveBlock2.
- Compatibilidade de menus existentes: prova binária dos **65 descritores** e ensaios de abrir/cancelar os IDs **0, 15, 31, 39 e 64** em scripts temporários somente de teste. Não é teste funcional completo das respectivas lojas/link/torre.
- Repetição: 12 ensaios sintéticos, cada um com quatro consultas seguidas antes de sair, sem task presa; não se afirma teste de longa duração de todos os recursos.
- **11 HUD + 10 preferência + 10 relógio persistente + 11 regressões de relógio + 8 encontros + 5 estojo + 4 combate + 5 gameplay/flash + 9 EV.** Incluem 1.440 horários no oráculo de pixels, 172.800 frames vivos/dois dias do mundo, 4.000 casos determinísticos de encontros, 287 quantidades de TMs/HMs e saves normais sintéticos v27↔v28, com HUD visível/oculto e antes/depois do cap.

Na rodada inicial, dois métodos exigiram correções no harness: aguardar a prontidão nativa após o fim da impressão e conferir o novo ponteiro da placa antes do warp temporário. Ambos foram reexecutados com sucesso em conjunto (228,812 s), sem alterar a ROM final; a seleção integral foi então repetida.

Os testes antigos da leitura linear da placa foram **substituídos**, não executados contra a placa obsoleta. Os encontros usam o payload v27, que é de fato o ativo e está intacto nesta versão. Rotinas isoladas de relógio usam o vetor v24 preservado; fluxos vivos passam pelos hooks atuais.

Nos controles de encontro das Rotas 13–16, o acesso começa após warps exclusivamente em cópias de teste. Não há warp na ROM entregue, nem prova de toda a progressão/HMs até essas áreas. Os 4.000 casos cobrem quantis, não frequências medidas de caminhadas aleatórias. Captura comum pode falhar naturalmente; seu controle positivo varia apenas a espera antes do lançamento.

Sem certificação de campanha completa, hardware real, todos os emuladores, link real ou saves pessoais. O ensaio de dois dias usa preferência visível; a preferência oculta possui controles dedicados de 120 frames. ROMs comerciais, saves, estados e screenshots ficam fora do Git.

## Reprodução

mGBA libretro **0.10.5**, commit `26b7884bc25a5933960f3cdcd98bac1ae14d42e2`; SHA-256 do core `574d504a8b49338ee883f1461a92460a21c239f5620b47cea87d83ff848b0429`.

```sh
python firered_gen1_9/scripts/motor_v28.py \
  --rom /caminho/v27.gba --saida /novo/caminho/v28.gba

MOTOR_V28_ROM=/novo/caminho/v28.gba MOTOR_V28_BASE=/caminho/v27.gba \
MGBA_CORE=/caminho/mgba_libretro.so TREINO_TEST_ROM=/novo/caminho/v28.gba \
python firered_gen1_9/scripts/validar_motor_v28.py --jobs 3 --log /tmp/v28-final.log
```

O runner exige 87 IDs únicos e nenhuma falha, erro ou skip. Cada processo usa seu próprio core e partida; `--jobs 1` executa serialmente. Tempo consolidado é de parede.

Capturas opcionais exigem Pillow e diretório novo:

```sh
MOTOR_V28_ROM=/novo/caminho/v28.gba MGBA_CORE=/caminho/mgba_libretro.so \
python firered_gen1_9/scripts/capturar_guia_v28.py --saida /novo/diretorio/telas
```

As capturas são da ROM exata, por controles nativos em partida sintética, sem warps. Entrega local, **sem publicação no Drive, commit ou push**. A leitura do arquivo v18 já existente no Drive foi usada apenas para reconstruir e conferir a cadeia até a base v27; não foi enviado arquivo novo.
