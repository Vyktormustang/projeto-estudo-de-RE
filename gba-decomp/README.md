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
| ROM sintética | 262 144 B, sha256 `5dfd55fb1c6d8ad93dd55aa4730908d0711427fa8395154c65c9382eeff7459a` |
| funções no binário | 24 (todas com resultado conhecido) |
| funções redescobertas **só a partir do vetor de boot** | 24/24, zero funções inventadas |
| instruções desmontadas | 370 |
| arestas de chamada | 26 (todas conferidas contra a verdade) |
| tabela de verdade no binário original | **59/59** |
| C levantado | 24/24 funções traduzidas, 0 não levantadas |
| tabela de verdade **no C levantado, recompilado e emulado** | **59/59** |
| C compilado (tamanho do modulo) | 1 092 bytes |
| testes automatizados | `32 passed` |

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
| descoberta partindo **so do vetor de reset** | 3 544 funcoes · 2 590 das 5 981 do censo (43,3%) |
| descoberta usando o **censo como sementes** | **8 151 funcoes**, 439 869 instrucoes listadas, 20 379 arestas |
| cobertura do censo | 5 981/5 981 (100%) · **2 170 funcoes que o censo nao tinha** |
| enderecos descartados | 170 (nenhuma instrucao valida do ARM7TDMI no inicio) |
| saltos que saem da funcao para tras | 245 · 154 trechos orfaos voltaram como janela propria |
| tabelas de casos | **375 reconhecidas**, 5 767 casos lidos da ROM → `switch` no C |
| funcoes com C para ler | **8 005 completas + 146 parciais = 100%** |
| C levantado | 1 020 566 linhas / 38,4 MB |
| conferencia byte a byte | **99,948%** das instrucoes remontam identicas ao binario |
| compilacao | **0 erros** com `zig cc -mcpu=arm7tdmi` (objeto de 2 124 636 bytes) |
| determinismo | C, JSON e objeto compilado **identicos** em duas rodadas (`ferramentas/checar_determinismo.py`) |

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

### O que isso prova e o que nao prova

Prova: a listagem **nao esta deslocada, nao pulou bytes e nao inventou instrucao**
(99,948% remontam byte a byte; as 225 divergencias sao `cmp`/`bx` escritos com a
outra codificacao valida da mesma instrucao), e o C gerado e **C valido para o
alvo** (nenhum rotulo inexistente, nenhuma chamada sem declaracao, em 1 020 566
linhas).

Nao prova: **semantica**. Nesta ROM nao existe verdade-terreno, entao nao se pode
afirmar que uma funcao levantada faz o que a original faz. O unico lugar onde
comportamento esta provado e o corpus sintetico — 59 casos, por emulacao, no
binario e no C levantado e recompilado.

### As lacunas que ficam (todas marcadas dentro do C)

| lacuna | ocorrencias |
|---|---|
| `bx rN` com origem nao rastreada | 35 (20 sao `bx rN`+nop *thunk*; o resto, salto calculado) |
| desvio que sai da funcao (bloco comum de outra rotina) | 130 · 71 para tras, 28 para fora, 31 para endereco nao desmontado |
| instrucao de ARM v4T ainda nao implementada (`mrs`, `stmdb`, `ldcl`...) | 20 |
| salto calculado por tabela que nao passou nos criterios | 4 |
| **total** | **189** (14 em funcao do censo, 175 fora dele) |

Cada uma aparece no ponto exato do C como `/* NAO LEVANTADO: ... */`, com o
endereco e o motivo. A funcao continua legivel ate ali — e o que faltou esta
declarado, nao escondido.

Comando que produz a evidencia (duas execucoes seguidas dao JSON identico e o
mesmo `.c` byte a byte):

```bash
python -m gbadecomp.cli analisar ROM.gba --censo censo/functions.csv \
        --json evidencias/rom_bpre_analise.json -o levantado_rom.c
python -m gbadecomp.conferir_bytes ROM.gba --censo censo/functions.csv
python ferramentas/estudo_switch.py ROM.gba --censo censo/functions.csv
python ferramentas/onde_estao_as_lacunas.py ROM.gba --censo censo/functions.csv
python ferramentas/checar_determinismo.py ROM.gba --censo censo/functions.csv
```

`onde_estao_as_lacunas.py` responde o que o resumo nao responde: onde as lacunas
se concentram (por pagina de 4 KB), se cairam em funcao do censo ou fora dele, e
**de onde vem o registrador de cada `bx rN`** — foi ele que separou "falta
implementar" de "a leitura estava engolindo a funcao anterior". Com
`--regiao 0x...-0x...` ele lista o desmonte de uma faixa mostrando **todas** as
funcoes donas de cada endereco (o caso que mais confunde).

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
| `corpus.py` | compila e empacota a ROM sintética (zig cc → Thumb), com a tabela de verdade de 59 casos |
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
