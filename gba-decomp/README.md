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
| testes automatizados | `14 passed` |

A ROM sintética é código **autoral** (funções triviais: soma, fatorial, laço
decrescente, classificação por faixas, leitura/escrita de memória, chamadas
internas). Ela serve para provar o *ferramental* em ARM/Thumb de verdade — não
diz nada sobre qualquer ROM de terceiros.

## ROM real (Pokemon - Fire Red BR): números medidos

Tudo nesta seção sai de **um comando**, que grava a evidência em JSON:

```bash
python -m gbadecomp.cli analisar ROM.gba --censo functions.csv \
       --json evidencias/rom_bpre_analise.json -o levantado_rom.c
```

ROM: `pokemon_firered_bpre_trabalho.gba`, sha256
`6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae` — bate
exatamente com o `inventory.json` do projeto. Duas execuções seguidas produzem
**JSON idêntico e o mesmo `.c` byte a byte**.

| medida | valor |
|---|---|
| censo do projeto | 5 981 funções |
| descoberta **só a partir do vetor de reset** | 1 866 funções, 73 321 instruções, 3 432 arestas, 10 descartes |
| descoberta com o censo como semente | **7 634 funções, 352 918 instruções, 16 387 arestas** |
| censo coberto | 5 981/5 981 (100%) · **1 653 funções fora do censo** |
| funções **com C para ler** | **7 634 de 7 634 (100%)** — 7 228 completas + 406 parciais marcadas |
| funções sem corpo nenhum | **0** |
| C gerado | 831 870 linhas / 31,2 MB — **compila sem erro** (`zig cc -mcpu=arm7tdmi`, objeto de 1 761 916 B) |
| condições fundidas nos desvios | 15 541 (`if (r0 >= 0x64)` em vez de `if ((n == v))`) |
| conferência byte a byte | **352 888/352 918 (99,991%)** remontam idênticas ao binário |
| endereços tentados como função e **descartados** | 83 (73 de ponteiro de pool, 10 de `bl`) — não são código |

### As descobertas que valem mais que os números

1. **Metade do que a varredura ingênua produzia era dado lido como código.** A
   primeira passada devolveu 675 389 "instruções"; rejeitando o que *não existe*
   no ARM7TDMI (`strd`, `cbnz`, `it`, `cdp2`, sufixos `.w`, NEON/VFP) sobraram
   **352 918**. Eram opcodes de Thumb-2/ARMv5 — impossíveis no GBA — vindos de
   tabelas percorridas como código. Sem esse filtro o levantamento teria gerado
   C bonito e falso.
2. **83 "funções" não tinham uma linha de C — e contavam como completas.** O
   resumo dizia 7 634 funções levantadas; as listas diziam 7 311 completas + 406
   parciais. A diferença passou uma rodada inteira porque a conta não estava
   escrita em lugar nenhum. Causa: endereços vindos de ponteiro de pool (73) ou
   de `bl` decodificado de dado (10) que não decodificam como instrução do
   ARM7TDMI. Efeito: viravam funções de corpo vazio **sem nenhuma recusa
   registrada** — logo, "completas". Agora não são função: vão para `descartes`,
   com motivo e bytes, e a medição **falha** se alguém reintroduzir o caso
   (`analise._classificar` recusa publicar o número).
3. **`salto calculado` ≠ variável.** 306 instruções `mov pc, rN` são tabelas de
   casos. Traduzi-las como atribuição seria mentira silenciosa: a função sai
   **PARCIAL**, com o motivo no cabeçalho e `g_erro |= 2` no ponto exato.
   (Estudadas em `ferramentas/estudo_switch.py`: 309 dos 320 sítios seguem o
   mesmo idioma `lsls` → `ldr r1,[pc,#N]` → `adds r0,r0,r1` → `ldr r0,[r0]` →
   `mov pc, r0`, e em **todos** os casos o guarda `cmp rN, #k` confere com o
   número de entradas lido da tabela — mas os alvos ainda não estão todos
   desmontados, então um `switch` hoje só trocaria o texto.)

O que esses números **não** dizem: que o C esteja semanticamente certo. Num
binário de terceiros não existe verdade-terreno, então o que se prova é
fidelidade de bytes e compilabilidade — **não comportamento**. Comportamento
está provado no corpus sintético (59/59 por emulação, no binário e no C
levantado e recompilado).

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
| `cli.py` | linha de comando |

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
