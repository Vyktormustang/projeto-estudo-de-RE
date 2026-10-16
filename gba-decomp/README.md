# gbadecomp — pipeline de engenharia reversa de ROM de GBA

Objetivo: sair do binário (ARM7TDMI, ARM/Thumb) e chegar a **código-fonte C
verificado**, não a um "achismo que parece código".

A regra que governa este diretório: **nada é afirmado sem execução**. Um
disassembler que produz uma listagem bonita e um decompilador que gera C que
compila não provam nada. O que prova é compilar o C gerado, empacotá-lo de volta
numa imagem de GBA e rodar a **mesma bateria de testes** contra as duas coisas:

```
binário  --disasm-->  funções + grafo de chamadas
         --decompile-->  C (uma instrução por linha, sem nomes inventados)
         --zig cc-->  objeto -> ELF linkado (endereços absolutos) -> blob
         --empacota-->  imagem de GBA
         --unicorn-->  mesma tabela de verdade contra o binário E contra o C
```

## Resultado medido (não estimado)

Última rodada, reproduzível com `python -m gbadecomp.cli rodada`:

| medida | valor |
|---|---|
| ROM sintética | 262 144 B, sha256 `5f9fe092e32780a1e7475c821e611a026ff6526523846ec1045f2208b3997135` |
| funções no binário | 25 (24 com caso de verdade-terreno; a 25ª é o próprio `main_teste`) |
| funções redescobertas **só a partir do vetor de boot** | 25/25, zero funções inventadas |
| instruções desmontadas | 379 |
| arestas de chamada | 27 (todas conferidas contra a verdade) |
| tabela de verdade no binário original | **60/60** |
| C levantado | 25/25 funções traduzidas, 0 não levantadas |
| tabela de verdade **no C levantado, recompilado e emulado** | **60/60** |
| C compilado (tamanho do modulo) | 1 096 bytes |
| testes automatizados | `56 passed` |

A ROM sintética é código **autoral** (funções triviais: soma, fatorial, laço
decrescente, classificação por faixas, leitura/escrita de memória, chamadas
internas). Ela serve para provar o *ferramental* em ARM/Thumb de verdade — não
diz nada sobre qualquer ROM de terceiros.

## ROM real (Pokemon - Fire Red BR): estado medido

Imagem de terceiros (modificada PT-BR), fora do repositorio:
sha256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`,
16 777 216 bytes, titulo `POKEMON FIRE`, codigo `BPRE`. O complemento do cabecalho
nao confere — esperado numa imagem modificada que nao recalculou o cabecalho, e
coerente com o `inventory.json` do censo, nao um problema do pipeline.

| medida | valor |
|---|---|
| descoberta partindo **so do vetor de reset** | 3 586 funcoes · 2 599 das 5 981 do censo (43,4%) |
| descoberta usando o **censo como sementes** | **8 172 funcoes**, 460 868 instrucoes listadas, 20 492 arestas |
| cobertura do censo | 5 981/5 981 (100%) · **2 191 funcoes que o censo nao tinha** |
| enderecos descartados | 164 (nenhuma instrucao valida do ARM7TDMI no inicio) |
| saltos que saem da funcao para tras | 241 · 148 trechos orfaos voltaram como janela propria |
| tabelas de casos | **377 reconhecidas**, 6 303 casos lidos da ROM → `switch` no C |
| funcoes com C para ler | **8 027 completas + 145 parciais = 100%** |
| C levantado | 1 056 638 linhas / 39,9 MB |
| conferencia byte a byte | **99,950%** das instrucoes remontam identicas ao binario |
| compilacao | **0 erros** com `zig cc -mcpu=arm7tdmi` (objeto de 2 164 988 bytes) |
| determinismo | C, JSON e objeto compilado **identicos** em duas rodadas (`ferramentas/checar_determinismo.py`) |
| o que uma mudanca mexe no objeto | medido por funcao, nao pelo sha256 (`ferramentas/conferir_objetos.py`): a r16 mudou o codigo de **2** funcoes de 8 172 |

### Achados que valem mais que os números

1. **Metade do que a varredura ingênua produzia era dado lido como código.** A
   primeira passada devolveu 675 389 "instruções"; rejeitando o que *não existe*
   no ARM7TDMI (`strd`, `cbnz`, `it`, `cdp2`, sufixos `.w`, NEON/VFP) sobraram
   **352 918**. Eram opcodes de Thumb-2/ARMv5 — impossíveis no GBA — vindos de
   tabelas percorridas como código. Sem esse filtro o levantamento teria gerado
   C bonito e falso.
2. **83 "funções" não tinham uma linha de C — e contavam como completas.** O
   resumo dizia 7 634 funções levantadas; as listas diziam 7 311 completas + 406
   parciais. A diferença passou uma rodada inteira porque a conta não estava
   escrita em lugar nenhum. Causa: endereços vindos de ponteiro de pool ou de
   `bl` decodificado de dado que não decodificam como instrução do ARM7TDMI.
   Efeito: viravam funções de corpo vazio **sem recusa registrada** — logo,
   "completas". Agora não são função: vão para `descartes`, com motivo e bytes, e
   a medição **falha** se alguém reintroduzir o caso (`analise._classificar`
   recusa publicar o número).
3. **As tabelas de casos estavam no binário e ninguém as seguia.** O
   levantamento parava em `mov pc, rN` e os corpos dos casos ficavam fora da
   desmontagem: o dispatcher `0x0803FBE8` tinha 19 dos 34 alvos desmontados.
   Agora o desmontador reconhece o idioma (`lsls` → `ldr rB,[pc,#N]` → `adds` →
   `ldr rI,[rI]` → `mov pc, rI`), lê a tabela da ROM e **segue os alvos**:
   +90 053 instruções (+25,5%) e **406 → 160 funções parciais**, com 375
   `switch` no C (número recalculado hoje pela própria descoberta: a contagem de
   `grep` daquela rodada dizia 377 e não era medição). O critério de aceitação é duplo e verificável: o guarda
   `cmp rN, #k` que o próprio compilador emitiu antes **tem de bater exatamente**
   com o número de entradas lidas da tabela, e cada alvo tem de começar com
   instrução que existe no ARM7TDMI. Se qualquer critério falhar, não se
   reconhece tabela nenhuma e a função continua marcada como parcial (teste
   `test_tabela_sem_guarda_que_bata_nao_vira_switch`). A sonda que mediu isso
   antes de implementar está em `ferramentas/estudo_switch.py`.

4. **A leitura de uma funcao andava para tras e engolia a funcao anterior.** Nao
   era um detalhe de estilo: a sonda (`ferramentas/onde_estao_as_lacunas.py`)
   mostrou que a "funcao" de `0x08018258` tinha 1 722 instrucoes e faixa
   `0x08017B92..0x08018C86` — **651 instrucoes antes da propria entrada**, o mesmo
   endereco aparecendo em tres funcoes. O estrago nao era so cosmetico: o `push`
   que guarda o endereco de retorno estava antes da entrada, entao o
   `pop {r1}; bx r1` do fim ficava sem marcador e virava recusa — **65 das 100
   recusas de `bx rN` vinham dai**. Agora um desvio para endereco ABAIXO da
   entrada e tratado como saida (o bloco comum pertence a outra rotina): a
   contagem de instrucoes caiu 3 102 (eram instrucoes fantasma, contadas duas
   vezes) e o numero de funcoes subiu, porque 154 trechos alcancados so por esses
   saltos voltaram como janela propria — com a origem marcada
   (`salto para tras em 0x...`), nao como se fossem entradas descobertas por
   chamada (testes `test_salto_para_tras_*`).
5. **Metade das recusas restantes de `bx rN` era o epilogo padrao.** Em Thumb o
   compilador volta por `pop {rN}; bx rN` (registrador baixo, para funcionar nos
   dois modos) em vez de `pop {pc}`. O lifter so aceitava o retorno quando o
   livro-caixa de slots da pilha tinha marcado aquele slot — e em 61 dos 96 casos
   a janela **comecava no meio do corpo** (endereco lido de tabela de dados),
   onde nao existe `push` nenhum no trecho lido. A condicao passou a ser mecanica
   (quem carrega o registrador e uma leitura da pilha na instrucao anterior):
   **96 → 35 `bx` recusados**, 146 parciais em vez de 205. E o que continua
   recusado ganhou motivo proprio, em vez de um rotulo so: 20 delas sao **thunks
   de 4 bytes `bx rN` + `mov r8, r8`** (nop de alinhamento) em `0x081E3BA8..`,
   chamados por `bl` de dezenas de sitios — ali o alvo e *parametro*, nao ha
   traducao literal a fazer; e ha a chamada indireta ARM→Thumb montada a mao
   (`stmdb sp!, {lr}` + `add lr, pc, #0` + `bx rN`).
6. **Um contador do proprio projeto mentia.** O relatorio de conferencia de bytes
   imprimia "25 divergencias" para 225 reais: o total era `len(exemplos)` e a
   lista de exemplos parava no limite de amostra. Achado ao *rodar* a medicao
   depois de mexer no codigo — nao por revisao. Agora o total e' contado sempre e
   agrupado por mnemonico (o que prova que as 225 sao so duas classes:
   `cmp` 219 escritos na outra codificacao valida, `bx` 6 repeticoes do mesmo
   endereco), com teste `test_conferencia_conta_todas_as_divergencias_...`.
7. **Dois numeros publicados nao vinham de medicao.** As "377 tabelas / 5 789
   casos" da rodada anterior saiam de `grep` no `.c` gerado — que nao distingue
   tabela reconhecida de `switch` emitido. Agora `analise._contar_tabelas` conta o
   que foi **lido da ROM** pela propria descoberta: **375 tabelas, 5 767 casos**.
   O numero mudou porque a fonte do numero mudou — o antigo nao era reproduzivel.
8. **A mensagem da lacuna mandava procurar defeito onde nao tinha.** Nos 146
   parciais, desvio recusado saia como "desvio para 0x…, que nao foi desmontado
   (rotulo inexistente)". `ferramentas/onde_estao_as_lacunas.py` passou a
   classificar o **destino** de cada desvio recusado lendo a propria descoberta —
   e o que se mediu foi: dos **130**, **48** caem em buraco de OUTRA janela,
   **29** caem em **instrucao** de outra janela (o endereco esta desmontado, so
   nao esta nesta rotina), **29** em buraco dentro da propria faixa e **24** em
   endereco que leitura nenhuma alcancou. Em 77 dos 130 a frase antiga era
   **falsa sobre o proprio levantamento**. O lifter agora tem um indice de janelas
   (`decompile.IndiceDeJanelas`) e escreve onde o alvo esta — "a leitura continua
   em INSTRUCAO da janela 0x…", "dentro da faixa da janela 0x…, em trecho nao
   desmontado (buraco: la a leitura parou em dado)" ou "fora de qualquer janela
   desmontada". Nenhuma dessas classes e' instrucao faltando implementar: sao
   todas "a leitura sai desta janela" (o bloco comum pertence a outra rotina).
   Testes `test_desvio_recusado_diz_onde_o_destino_foi_desmontado` e
   `test_desvio_para_endereco_que_ninguem_desmontou_diz_isso`. O objeto compilado
   **nao mudou um byte** (o motivo vive em comentario): sha256 do objeto identico
   antes e depois da correcao — a prosa mudou, o codigo gerado nao.
9. **"Mnemônico nao implementado" tambem mandava procurar defeito onde nao tem.**
   Das lacunas, 20 diziam isso. Medindo uma por uma: 16 nao sao instrucao que
   falte implementar — **nao existem no ARM7TDMI**. `orn`/`orns` sao ARMv6,
   `smlawt` e' ARMv5TE, `hint` e' Thumb-2, `ldcl`/`stcl` sao coprocessador (o
   Thumb-1 nao tem nenhum) e `stmdb r0, {...}` so' existe no ARM -- todas lidas
   em janelas **Thumb**, ou seja, ali a leitura passou por **dado**. O filtro
   `disasm.impossivel_no_arm7tdmi` existia, mas nao pegava as formas com letra
   colada (`ldcl` nao e' `ldc` na comparacao por igualdade) nem essa familia;
   agora pega, e o desmontador **para** no ponto (registrando a terminacao) em vez
   de continuar lendo dado como codigo. **189 → 173 lacunas, 146 → 134 parciais**,
   336 instrucoes a menos (eram bytes de dado escritos como instrucao). Testes
   `test_instrucao_que_nao_existe_no_thumb1_e_marcada_como_tal` e
   `test_lifter_distingue_instrucao_que_nao_existe_de_falta_implementar` — os
   bytes vem da ROM (com o que capstone le neles assertado antes do veredito), e
   o mesmo `stmdb sp!, {lr}` do ARM continua passando pelo filtro.
10. **Um numero do JSON que dava para citar errado.** `recusas_motivo` era o
   histograma de motivos cortado em 12 grupos e truncado em 90 caracteres: a soma
   dele dava **67** para **189** lacunas. Nao era erro de calculo, era um numero
   sem definicao publicada — quem citasse o JSON escreveria "67 recusas". Agora o
   JSON traz `recusas_total` (o total, com o nome dizendo o que e'), o histograma
   por motivo **completo** e com os enderecos trocados por `0x...` (senao cada
   motivo com endereco vira um grupo de 1) e o relatorio diz na tela que a soma
   dos motivos e' o total. Teste
   `test_histograma_de_recusas_fecha_com_o_total_e_agrupa_endereco`.
11. **Uma regra escrita pelo TEXTO que o capstone imprime errou duas vezes — e a
   segunda vez quebrou o C.** A pergunta era boa (o `adc` existe no ARMv4T, mas
   `adc r4, r4, #0xd000` não existe no Thumb-1), a resposta não: a regra olhava o
   nome e os operandos *impressos*. Primeiro `lsls`/`lsrs`/`asrs` com imediato,
   que **existem** no Thumb-1 (formatos 1 e 3): 11 testes caíram. Depois
   `rsbs r0, r1, #0` — que é o `neg` do Thumb-1 escrito em **dois bytes**
   (`48 42`); o `#0` que o capstone **mostra** ali não está codificado em lugar
   nenhum. A regra marcou **1 750 instruções válidas** como inexistentes e o C
   levantado **não compilou** (rodada r12 — o defeito era do filtro, não da ROM;
   a rodada inteira foi descartada, nada dela foi publicado). A versão que ficou
   pergunta pela **codificação**: instrução Thumb do ARM7TDMI tem 16 bits, e a
   codificação de 32 bits começa com prefixos que no Thumb-1 são indefinidos —
   se a leitura chegou num deles, ela passou por dado. A exceção é medida e
   estreita: o **`bl` do Thumb-1 também tem 32 bits** (é assim que o Thumb chama
   sub-rotina) e continua válido — o corpus tem 29 dessas chamadas e sem a
   exceção o levantado parava de reproduzir a verdade-terreno.
12. **O que essa regra consertou era C silenciosamente errado.** Nos 17 sítios de
   codificação de 32 bits que sobraram, o lifter **traduzia dado como código** e
   acertava a conta errada: `orr r2, r0, #0x810000` saía como `r2 = r2 | 0x810000;`
   (o `r0` sumia) e `and sl, r1, #0x690069` como `r10 = r10 & 0x690069;` — o
   registrador de origem era o **destino**, e do imediato ninguém via nada de
   errado. **8 funções** estavam nesse estado e viraram parciais: hoje o sítio sai
   como `/* NAO LEVANTADO: orr r2, r0, #0x810000 */`, com o motivo verdadeiro.
   Detalhe que vale registrar: a conferência byte a byte **não pega** isso — ela
   confere o texto contra os bytes, e o texto remonta certo (keystone monta a
   forma de 32 bits). Conferência de bytes não é conferência de semântica; por
   isso a verdade-terreno existe só no corpus, onde a emulação decide (teste
   `test_forma_inexistente_no_thumb1_e_julgado_pelo_tamanho_da_codificacao`).

13. **O guarda do `switch` nem sempre e' `cmp rX, #k` — e a recusa dizia so' a
   metade.** Duas tabelas da ROM (`0x0805234C` e `0x08050F5C`, **268 casos
   cada**) eram recusadas com "nao existe `cmp rX, #k` nas 18 instrucoes
   anteriores". Verdade incompleta: o limite estava na ROM. O codigo e'

   ```
   0x08052338  ldr r1, [pc, #0x18]   ; r1 = 0x0000010B -- o LIMITE, vindo do pool
   0x0805233C  cmp r5, r1            ; compara com REGISTRADOR, nao com imediato
   0x0805233E  bls 0x08052344        ; dentro da faixa
   0x08052340  bl  0x08053774        ; fora da faixa: tratamento
   ```

   O numero de casos continua saindo de medicao (e nao de suposicao): o limite
   lido do pool **tem de fechar** com as entradas lidas da tabela. Medido nos
   dois sitios: **268 entradas, todas enderecos de codigo do alvo**, e o word
   seguinte (`0x68384B1A`) **nao** e' endereco de codigo — a tabela acaba
   exatamente onde o guarda diz, confirmacao dupla. Antes disto a sonda
   (`ferramentas/diagnosticar_tabela.py`) tambem nao existia: as quatro recusas
   pareciam a mesma coisa de longe e nao sao (**2** sao este idioma, **2** nao
   sao — em `0x083F62EC` e `0x081DBEBA` a instrucao anterior e' um `cmp`/`bhs`,
   e o motivo agora diz isso com a instrucao medida). Efeito: **375 → 377
   tabelas, 5 767 → 6 303 casos**, 8 153 → **8 172 funcoes** (os corpos dos casos
   passaram a entrar na desmontagem), 456 822 → **460 868 instrucoes**. As
   recusas cairam de 193 para **192** naquela rodada (191 hoje, item 15) — e o
   motivo das duas que sairam, o das
   que ficaram e o das que apareceram (uma janela nova que termina em desvio para
   trecho nao desmontado) esta' no JSON, item a item.

14. **"Buraco" nao era codigo faltando — era dado, e agora esta' medido.** As
   **99** recusas de desvio cujo motivo era "trecho nao desmontado" (47 buraco de
   outra janela, 29 buraco dentro da propria faixa, 23 endereco que leitura
   nenhuma alcancou) pareciam a maior lacuna do levantamento, e a correcao
   parecia obvia: semear esses enderecos "para recuperar o trecho". Antes de
   escrever isso, o que HA' em cada alvo foi lido da ROM: dos **65 911** alvos de
   desvio imediato da desmontagem, **65 801** sao instrucao de alguma janela
   (99,83 %); dos **110** restantes, **2** caem fora da imagem, **53** ja' tinham
   sido tentados como semente e descartados (nao decodificam) e **55** nunca
   foram tentados — e os **55 param na PRIMEIRA instrucao**: nenhum chega a um
   retorno. Nao ha' codigo perdido em nenhum deles; semear ali seria ler dado
   como codigo, exatamente o defeito que a rodada r13 desfez (item 12). O
   veredito pergunta pelos **dois** motivos que o levantador usa — o mnemonico
   (`mrc2`, `ldrd`, `udf`: instrucoes que nao existem no ARM7TDMI) e a **forma
   por tamanho de codificacao** (`44 f5 50 44` = `adc r4, r4, #0xd000`, que o
   capstone mostra com cara de instrucao valida e nao existe no Thumb-1) — e sem
   o segundo o buraco voltaria a parecer codigo faltando. Medido pela secao
   "alvos de desvio imediato" de `ferramentas/onde_estao_as_lacunas.py`; o
   teste `test_alvo_de_desvio_que_ninguem_cobriu_e_medido_nos_bytes` monta os
   tres casos (coberto, nunca tentado, ja' descartado) num binario sintetico e
   cai se a leitura dos bytes deixar de ser feita.

15. **O C levantado nao guarda o endereco da instrucao — e tres instrucoes liam
   `pc`.** O modelo tem `pc` como variavel que so' serve para RECEBER desvio (vale
   0), entao `add lr, pc, #0` saia como `lr = pc + 0`: C que compila e conta
   errado, sem marca de lacuna nenhuma — o pior tipo de defeito deste projeto
   (item 12). Medido o universo inteiro: **392 instrucoes** citam `pc` na ROM, das
   quais 388 sao `mov pc, rX` (retorno/tabela, ja' tratados) e **3 LEEM `pc`** —
   `add lr, pc, #0` em 0x0800036C (a chamada ARM→Thumb montada a mao), `add r8, pc`
   em 0x0839FEB8 e `mov r2, pc` em 0x0800C280. As tres formas viraram **constante
   dobrada em tempo de traducao**, com a conta no comentario
   (`lr = 0x08000374u;  /* pc desta instrucao (0x0800036C) */`), pela mesma regra
   que o `adr` ja' usava (endereco + 8 no ARM; endereco + 4 alinhado no Thumb — o
   `mov r2, pc` de 0x0800C280 e o `add r8, pc` de 0x0839FEB8 leem o MESMO valor,
   0x08000024 no caso do teste, porque o segundo cai em endereco nao alinhado). As
   formas sem valor constante (`cmp rD, pc`, `add rD, rM, pc`, `str` em `[pc, ...]`)
   sao **recusadas**, com o motivo dizendo exatamente isso. Na mesma passada, duas
   fronteiras do modelo ficaram ditas com o motivo certo: no ARM, PUSH e POP **sao**
   `stmdb sp!` / `ldmia sp!` — a unica ocorrencia da ROM (0x08000368, no
   IRQ_HANDLER) era recusada e agora entra pelo caminho da pilha (o mesmo do `push`
   do Thumb, que mantem o modelo usado para reconhecer o epilogo `pop {rN}; bx rN`);
   e o PSR **nao existe** no modelo, entao ler `mrs r0, spsr` / `mrs r3, apsr` e
   escrever o campo de CONTROLE (`msr cpsr_fc, r3`, o que mexe na mascara de IRQ)
   ficam recusados — mas o texto agora diz **limite do modelo**, no lugar do
   "mnemonico nao implementado / falta traduzir" que mandava procurar trabalho
   inexistente. Efeito medido: **192 → 191 recusas**, 1 056 640 → 1 056 638 linhas
   de C, objeto 2 164 980 → 2 164 988 B (`sha256` 82b93d74…); **todo o resto
   identico** (8 172 funcoes, 460 868 instrucoes, 20 492 arestas, 377 tabelas /
   6 303 casos, 8 027 + 145 completas/parciais, 460 639 identicas em 460 868).
   O objeto mudou **onde tinha de mudar**, e isso foi medido funcao por funcao e
   nao pelo sha256: das 8 172 funcoes, **2** mudaram de tamanho
   (`IRQ_HANDLER_arm_boot`, 80 → 84 bytes, porque o `stmdb sp!, {lr}` passou a sair
   pelo caminho da pilha; e `fn_0800C280`, 22 → 28, porque o `mov r2, pc` virou
   constante) e 20 so' deslocaram, de mesmo tamanho. Testes:
   `test_pc_lido_como_operando_vira_constante_e_nao_a_variavel_pc`,
   `test_mov_e_add_com_pc_no_thumb1_usam_o_pc_alinhado`,
   `test_leitura_de_pc_em_forma_sem_valor_constante_e_recusada` e
   `test_stmdb_sp_do_arm_e_o_push_da_pilha_do_modelo` (bytes montados com keystone,
   conferidos pelo capstone e conferidos contra os bytes da ROM).

16. **A regra de coprocessador so' valia no Thumb.** `ldc`/`stc`/`cdp`/`mcr`/
   `mrc` sao dado nos DOIS modos -- o ARM7TDMI decodifica essas instrucoes e as
   deixa indefinidas quando nao ha coprocessador ligado, e o GBA nao liga nenhum
   --, mas a checagem estava **dentro do ramo do Thumb**. Em ARM, uma delas sairia
   como "mnemonico nao implementado (a instrucao existe no ARMv4T; falta
   traduzir)", que e' afirmacao falsa. Medido ANTES de mexer (varredura r17): nas
   janelas da ROM ha' **75 instrucoes ARM, e zero delas e' de coprocessador** (as
   6 que aparecem -- `ldcl` 3 vezes, `stcl` 3 vezes -- estao em janelas Thumb, ja'
   cobertas pela regra antiga). Ou seja: a mudanca nao tinha como alterar leitura
   nenhuma; o que ela conserta e' o **texto**, e isso aparece em 50 entradas de
   `descartes` reescritas (`ldc2l` 45, `stc2` 2, `stc2l` 1, `mcr` 1, `ldc2` 1) --
   `ldc2l` dizia "coprocessador 2 nao existe no ARM7TDMI" quando a razao e' nao
   existir coprocessador **nenhum**. A pergunta passou a ser por PREFIXO (a forma
   vem colada no nome: `ldcl`, `stcl`, `ldc2l`) e vale nos dois modos. Efeito
   medido na rodada r17: **tudo identico a r16** -- 8 172 funcoes, 460 868
   instrucoes, 191 recusas, 8 027 + 145 completas/parciais, 460 639/460 868 na
   conferencia, 1 056 638 linhas de C (2 692 bytes a mais, so' texto de recusa) e
   **objeto byte a byte identico** (`sha256` 82b93d74… igual): a prosa mudou, o
   codigo gerado nao. Teste
   `test_coprocessador_e_dado_nos_dois_modos_nao_so_no_thumb`: 8 formas montadas
   com keystone e conferidas pelo capstone antes do veredito, 3 negativos que
   EXISTEM no ARMv4T (`stmdb sp!` = push do ARM, `mrs`, `mov`) e o caso em que a
   leitura **para** no ponto (vira `descarte`, com 0 instrucoes lidas). Conferido
   quebrando de proposito: com a regra de volta so' no Thumb, o teste cai.

17. **A recusa do `mov pc, rX` mandava procurar tabela onde nao tem.** Ela dizia
   "salto calculado (tabela de casos) nao modelado" -- o que sugere um `switch`
   que quase fechou. As **2** que sobram na ROM **nao sao tabela**, e isso foi
   medido antes de mexer (`ferramentas/diagnosticar_tabela.py`, rodada r17):
   * `0x081DBEBA` (janela `0x081DBEA6`, descoberta por um `bl` em `0x080EC620`):
     o que esta' antes e' `ldr r2, [r0, #0x28]` + `cmp r2, #0` + `beq` + `bhs` --
     o destino do salto e' **ponteiro lido da memoria** (chamada indireta), nao
     tabela; e o pool da janela (`0x081DC000`) carrega `0x04000120`,
     registrador de I/O do GBA, **fora da imagem**: mesmo que o idioma fechasse,
     nao ha' tabela de codigo ali;
   * `0x083F62EC` (janela `0x083F61FA`, descoberta por um ponteiro de pool em
     `0x080CCA84`): antes dele ha' `asrs r5, r1, #2` e `cmp r1, #0x53` no meio de
     um trecho de `00 00` (o decodificador ve `movs r0, r0`) -- **dado** lido como
     codigo.
   O que faltava era o texto dizer o **criterio que falhou**, e nao um rotulo. O
   motivo medido pelo desmontador por site ja' existia
   (`FuncaoDesmontada.tabelas_recusadas`, item 13); agora ele viaja com a recusa
   ate' o C:

   ```
   /* PC calculado em r2: o destino so' existe em tempo de execucao (vem de
      registrador); o idioma de tabela de casos nao fechou -- a instrucao anterior a
      0x081DBEBA nao e' `ldr rI, [rI]` (medido: `bhs #0x81dbeca` em 0x081DBEB8) */
   ```

   Efeito medido na r18: recusas continuam **191** (as 2 continuam recusadas --
   recusa correta, e' dado/ponteiro, nao tabela), **377** tabelas, **6 303**
   casos, 1 056 638 linhas de C (658 bytes a mais, so' texto de recusa) e
   **objeto byte a byte identico** ao da r17 (`sha256` 82b93d74… igual): de novo,
   a prosa mudou e o codigo gerado nao. Teste
   `test_salto_calculado_marca_funcao_como_parcial` (estendido): o criterio medido
   tem de aparecer no motivo **e** no comentario do C; o outro teste
   (`test_tabela_sem_guarda_que_bata_nao_vira_switch`) passou a exigir a medicao
   no lugar do rotulo ("a entrada 3 da tabela ... nao e' endereco de codigo").

### O que isso prova e o que nao prova

Prova: a listagem **nao esta deslocada, nao pulou bytes e nao inventou instrucao**
(99,950% remontam byte a byte; as 226 divergencias sao `cmp`/`bx` escritos com a
outra codificacao valida da mesma instrucao), e o C gerado e **C valido para o
alvo** (nenhum rotulo inexistente, nenhuma chamada sem declaracao, em 1 056 638
linhas). Nao prova **semantica** -- foi exatamente esse tipo de defeito (item 12)
que a conferencia de bytes deixou passar por uma rodada inteira.

Nao prova: **semantica**. Nesta ROM nao existe verdade-terreno, entao nao se pode
afirmar que uma funcao levantada faz o que a original faz. O unico lugar onde
comportamento esta provado e o corpus sintetico — 60 casos (em 24 das 25
funcoes; a 25ª e' o proprio `main_teste`), por emulacao, no binario e no C
levantado e recompilado.

### As lacunas que ficam (todas marcadas dentro do C)

| lacuna | ocorrencias |
|---|---|
| `bx rN` com origem nao rastreada | 39 (11 sao `bx rN`+nop *thunk*, 1 e' chamada indireta ARM→Thumb, 27 sao salto calculado) |
| desvio que sai da funcao (bloco comum de outra rotina) | 98 |
| desvio condicional para endereco sem rotulo nesta janela | 32 — mesmas 4 classes de destino |
| instrucao que **nao existe** no ARM7TDMI (dado lido como codigo) | 17 (codificacao de 32 bits do Thumb-2; ARMv5+/coprocessador nem chega aqui: **para** a leitura e vira `descarte`, 162 deles) |
| o PSR nao existe no MODELO (`mrs` lendo, `msr` escrevendo o campo de controle) | 3 — o valor lido no ARMv4T carrega modo e mascara de IRQ, que o C levantado nao tem (so' z/n/c/v) |
| `mov pc, rN` com o destino em registrador (nao e' o idioma de tabela de casos) | 2 — o motivo diz QUAL criterio faltou, medido: `bhs` antes de 0x081DBEBA e `cmp r1, #0x53` antes de 0x083F62EC |
| **total** | **191** (13 em funcao do censo, 178 fora dele) |
| destino de cada desvio recusado (relatorio separado) | 130: 47 buraco de outra janela, 31 instrucao de outra janela, 29 buraco da propria faixa, 23 ninguem desmontou |
| o que HA' nos alvos que nenhuma janela cobriu | 110 de 65 911: 53 ja' tentados como semente e descartados, 55 nunca tentados (**os 55 param na primeira instrucao**), 2 fora da imagem — **0 sao codigo** |

Cada uma aparece no ponto exato do C como `/* NAO LEVANTADO: ... */`, com o
endereco e o motivo. A funcao continua legivel ate ali — e o que faltou esta
declarado, nao escondido.

Comando que produz a evidencia (duas execucoes seguidas dao JSON identico e o
mesmo `.c` byte a byte), com os arquivos que ficam versionados em `evidencias/`:

```bash
# corpus sintetico: rodada, desmontagem e o C levantado (tudo gerado)
python -m gbadecomp.cli rodada --saida /tmp/corpus --json evidencias/rodada_corpus.json
python -m gbadecomp.cli disasm /tmp/corpus/corpus.gba \
        --json evidencias/desmontagem_corpus.json \
        --listagem evidencias/desmontagem_corpus.txt
cp /tmp/corpus/levantado.c evidencias/levantado_corpus.c

# ROM de terceiros: sem verdade-terreno, so' o que foi medido
python -m gbadecomp.cli analisar ROM.gba --censo censo/functions.csv \
        --json evidencias/rom_bpre_analise.json -o levantado_rom.c
python -m gbadecomp.conferir_bytes ROM.gba --censo censo/functions.csv
python ferramentas/estudo_switch.py ROM.gba --censo censo/functions.csv
python ferramentas/onde_estao_as_lacunas.py ROM.gba --censo censo/functions.csv
python ferramentas/diagnosticar_tabela.py ROM.gba --censo censo/functions.csv
python ferramentas/checar_determinismo.py ROM.gba --censo censo/functions.csv
# "o objeto mudou" quase nunca quer dizer "o CODIGO mudou": esta ferramenta separa
python ferramentas/conferir_objetos.py objeto_da_rodada_antiga.o objeto_da_rodada_nova.o

# a amostra versionada (evidencias/rom_bpre_amostra_levantada.c) sai daqui: o
# cabecalho vem do JSON acima e os trechos, do .c da mesma rodada
python ferramentas/recortar_amostra.py levantado_rom.c \
        --analise evidencias/rom_bpre_analise.json \
        --caso 0x080011E4 "tabela de casos lida da ROM virou switch" \
        --caso 0x08014040 "desvio para tras: a leitura continua em OUTRA janela" \
        --caso 0x081DC45A "bx rN recusado, com o motivo dito por inteiro" \
        --caso 0x08000248 "no ARM, stmdb sp! E' o push da pilha, e add lr, pc virou constante" \
        --orcamento 150 --saida evidencias/rom_bpre_amostra_levantada.c
```

Os arquivos de `evidencias/` **nao sao retratos antigos**: dois testes comparam
cada um com o que o pipeline produz agora — `test_readme_conta_a_mesma_rodada_
da_evidencia` (tabelas do README contra `rom_bpre_analise.json`) e
`test_evidencia_do_corpus_e_a_rodada_de_agora` (rodada do corpus, campo a campo,
e o `.c` byte a byte). Se a medicao mudar e a evidencia nao, os testes caem; se o
README citar numero de outra rodada, tambem. Conferido quebrando de proposito:
trocar `"funcoes": 25` por `24` no JSON, ou um unico caractere no `.c` versionado,
faz o teste falhar.

`diagnosticar_tabela.py` responde "por que este `mov pc, rX` nao virou
`switch`?" — e ele existe porque a resposta antiga ("salto calculado nao
reconhecido", 4 ocorrencias) juntava quatro situacoes diferentes: **2** sao o
idioma com o limite vindo do pool e **2** nao sao o idioma (a instrucao anterior
e' um `cmp`/`bhs`). A classificacao vem da MESMA funcao que o desmontador usa
(`disasm._tabela_de_casos_ou_motivo`) — sonda que reimplementa a regra mede a
regra da sonda, nao a do programa — e o veredito sai com os numeros medidos: o
guarda, o pool, cada entrada lida e qual delas nao existe no alvo.
(`--site 0x...` detalha um sitio; `--censo`/`--entrada` dao as sementes.)

`conferir_objetos.py` responde "o objeto mudou **no codigo** ou so' em rotulo?".
Ele existe porque esta rodada produziu os **dois** casos e eles se parecem: um
polimento de legibilidade que tirou `+ 0x0u` de uma linha de C (7 bytes menos de
C) deu objeto com o **mesmo sha256**; e o conserto do `pc`/`stmdb`, que na mesma
passada mudou uma linha de CODIGO, deu objeto diferente. A ferramenta compara
secao por secao (`.text`, `.rodata`, tabelas do ELF) e, quando o `.text` muda, diz
**qual funcao** mudou de tamanho pelo nome: na r16, de 8 172 funcoes, exatamente
**2** -- `IRQ_HANDLER_arm_boot` (80 → 84 bytes: o `stmdb sp!, {lr}` passou a sair
pela pilha) e `fn_0800C280` (22 → 28: o `mov r2, pc` virou constante) -- com 20
outras so' deslocadas, de mesmo tamanho. Ela tambem mede a armadilha do proprio
instrumento: o **caminho da fonte entra no `.symtab`** (simbolo `STT_FILE`), entao
o MESMO C compilado noutro diretorio nao da objeto byte a byte igual -- e' por
isso que o objeto de 2 164 988 B da rodada publicada nao bate com um build local
em outro caminho, e nao por causa de codigo.

A amostra versionada (`evidencias/rom_bpre_amostra_levantada.c`) existe para o
item 15 poder ser **lido**, e nao acreditado: o ultimo caso e' o
`IRQ_HANDLER_arm_boot` inteiro (0x08000248), onde dao para ver as duas coisas que
mudaram -- `sp -= 4; guarda32(sp + 0, lr);` no lugar do `/* NAO LEVANTADO: stmdb
sp!, {lr} */` (que era a unica ocorrencia de push em ARM da ROM) e
`lr = 0x08000374u;  /* pc desta instrucao (0x0800036C) */` no lugar de um
`lr = pc + 0` que compilava e devolvia 0. Na r14, as duas linhas estavam ali do
lado: `{ u32 a_ = pc, b_ = 0x0 + 0; ... }`.

 onde as lacunas
se concentram (por pagina de 4 KB), se cairam em funcao do censo ou fora dele,
**de onde vem o registrador de cada `bx rN`** e **para onde vai cada desvio
recusado** (buraco de outra janela, instrucao de outra janela, buraco na propria
faixa ou endereco que leitura nenhuma alcancou) — foi ele que separou "falta
implementar" de "a leitura saiu desta janela" — e **o que existe em cada alvo que
nenhuma janela cobriu**, lendo os bytes dos 110 alvos: nenhum tem codigo (item 14). Com `--regiao 0x...-0x...` ele
lista o desmonte de uma faixa mostrando **todas** as funcoes donas de cada
endereco (o caso que mais confunde).

## Como usar

```bash
# prova o pipeline inteiro no corpus sintético (não precisa de ROM nenhuma)
python -m gbadecomp.cli rodada

# descoberta recursiva a partir do vetor de boot, com listagem e JSON
python -m gbadecomp.cli disasm ROM.gba --listagem lista.txt --json dados.json

# levantar o binário para C
python -m gbadecomp.cli decompilar ROM.gba -o levantado.c

# cabeçalho, espaço livre e cruzamento com o censo de funções
python -m gbadecomp.cli relatorio ROM.gba --censo functions.csv

# conferencia independente: remontar cada instrucao e comparar byte a byte
python -m gbadecomp.conferir_bytes ROM.gba --censo censo/functions.csv

# medir a rodada inteira e gravar a evidencia (numeros do README saem daqui)
python -m gbadecomp.cli analisar ROM.gba --censo functions.csv \
        --json evidencias/rom_bpre_analise.json -o levantado_rom.c

# ROM de verdade, usando o censo como sementes (endereços + nomes)
python -m gbadecomp.cli levantar ROM.gba --censo functions.csv -o levantado_rom.c
```

Testes: `python -m pytest tests/ -q`

## Módulos

| arquivo | o que faz |
|---|---|
| `rom.py` | acesso à ROM por endereço do espaço GBA, cabeçalho, espaço livre, leitura do `functions.csv` |
| `corpus.py` | compila e empacota a ROM sintética (zig cc → Thumb), com a tabela de verdade de 60 casos |
| `disasm.py` | descoberta recursiva (bl, desvios, pools de literais) com modo herdado da chamada |
| `decompile.py` | tradução instrução-a-instrução para C, com pilha em memória real e conferência de balanceamento |
| `verificador.py` | emulador unicorn + comparação com a verdade-terreno, caso a caso, sem maquiagem |
| `analise.py` | mede a rodada inteira e grava a evidência; categorias exaustivas conferidas por asserção |
| `conferir_bytes.py` | remonta cada instrução e compara com o binário (fidelidade de bytes, não semântica) |
| `reconstruir.py` | junta tudo: disasm → C → compilação → imagem → verificação |
| `cli.py` | linha de comando (inclui `analisar`: mede e grava a evidência) |

## Limites técnicos declarados

- **Subconjunto de instruções.** O levantador cobre o que aparece no corpus
  (Thumb-1: aritmética, deslocamentos, comparações, memória, `push`/`pop`,
  `bl`/`bx`, desvios condicionais, `stm`). Instrução não coberta **aparece na
  lista de não levantadas** — nunca é ignorada em silêncio.
- **ARM**: o desmontador entende ARM e começa por ele (o vetor de boot de um GBA
  executa em ARM), mas o levantamento para C foi exercitado apenas em Thumb.
- **Desvio indireto por registrador** sem origem conhecida (`bx rN` que não veio
  de um `pop`) interrompe o levantamento daquela função, com o motivo registrado.
- **Flags imprevisíveis**: onde o ARM não define o resultado (ex.: flag C após
  `MUL`), o C gerado não inventa valor — o comportamento fica anotado.
- **Sem nomes, sem estruturas.** O C gerado tem `fn_08000258` e `goto`; a
  reescrita para `if`/`while`/nomes significativos é trabalho humano posterior.
- **Não é um emulador de GBA completo.** O verificador mapeia ROM, EWRAM e
  IWRAM; não há PPU, DMA, timers nem interrupções. Código que dependa disso
  (a maior parte de um jogo) exige um emulador completo, não este verificador.

## Requisitos

`python3` e, no `.venv` do repositório: `capstone`, `unicorn`, `pyelftools`,
`ziglang` (traz o `zig cc`, que faz o papel de `arm-none-eabi-gcc` — este último
não pôde ser instalado neste ambiente). Nada além disso é necessário.
