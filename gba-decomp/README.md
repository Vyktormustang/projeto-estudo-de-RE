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

Com a ROM no disco (`/home/user/gba-re/rom/pokemon_firered_bpre_trabalho.gba`,
sha256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae` — bate
exatamente com o `inventory.json` do projeto):

| medida | valor |
|---|---|
| censo do projeto | 5 981 funções (5 980 Thumb, 1 ARM) |
| descoberta **só a partir do vetor de reset** | 1 876 funções, 73 792 instruções, 3 432 arestas |
| …das quais confirmadas no censo | 1 382 · e **494 que o censo não tinha** |
| descoberta com o censo como semente | **7 717 funções, 352 918 instruções, 16 387 arestas** |
| censo coberto | 5 981/5 981 (100%) · **1 736 funções fora do censo** |
| funções **com C para ler** | **7 634 de 7 717 (98,9%)** — 7 311 completas + 406 parciais marcadas |
| C gerado | 832 192 linhas / 31 MB — **compila sem erros** (`zig cc -mcpu=arm7tdmi`, objeto de 1,76 MB) |
| condições fundidas nos desvios | 15 541 (`if (r0 >= 0x64)` em vez de `if ((n == v))`) |
| conferência byte a byte | **352 888/352 918 (99,991%)** remontam idênticas ao binário |

### Três descobertas que valem mais que os números

1. **Metade do que a varredura ingênua produzia era dado lido como código.** A
   primeira passada devolveu 675 389 "instruções"; rejeitando o que *não existe*
   no ARM7TDMI (`strd`, `cbnz`, `it`, `cdp2`, sufixos `.w`, NEON/VFP) sobraram
   **352 918**. Eram opcodes de Thumb-2/ARMv5 — impossíveis no GBA — vindos de
   tabelas percorridas como código. Sem esse filtro o levantamento teria gerado
   C bonito e falso.
2. **`salto calculado` ≠ variável.** 306 instruções `mov pc, rN` são tabelas de
   casos (dispatchers). Traduzi-las como atribuição seria mentira silenciosa:
   agora a função sai **PARCIAL**, com o motivo no cabeçalho e `g_erro |= 2` no
   ponto exato — legível, e detectável por quem executar.
3. **Função sem corpo nenhum: 0.** Antes as 448 incompletas viravam só um
   protótipo; agora todas as 7 717 têm algo para ler (406 com lacuna marcada).

O que esses números **não** dizem: que o C esteja semanticamente certo. Num
binário de terceiros não existe verdade-terreno, então o que se prova é
fidelidade de bytes e compilabilidade — **não comportamento**. O único lugar
onde comportamento está provado é o corpus sintético (59/59 por emulação, no
binário e no C rele_vantado e recompilado).

## O que está provado e o que não está## O que está provado e o que não está

**Provado:** o ciclo completo funciona em código Thumb real. As armadilhas que
quebraram o pipeline durante o desenvolvimento e que os testes agora travam
(regressões reais, cada uma produzia resultado plausível e errado):

1. **Modo de execução do destino de `bl`.** O alvo vem **par**; escolher o modo
   pela paridade desmonta a função inteira em ARM e gera lixo que parece código.
   O modo correto é herdado de quem chama.
2. **Semântica de PUSH/POP.** O push desce o `sp` e grava em endereços
   crescentes; um `pop {r1}` posterior recupera o **primeiro** item empilhado.
   Tratar a pilha como LIFO clássico entrega o endereço de retorno ao
   registrador errado.
3. **Deslocamento por registrador** (`lsls r3, r2`): quantidade nos 8 bits
   baixos, com regras próprias para n = 0, 32 e > 32.
4. **`mvns Rd, Rm`**: a fonte é o **segundo** operando (`mvns r3, r3` esconde o
   erro; `mvns r2, r0` não).
5. **Writeback do `stm r0!, {…}`**: a string termina em `}`, não em `!` — testar
   o fim da string perde a atualização do registrador base.
6. **`PC + 4` no pool de literais do Thumb** (bit1 zerado): errar desloca a
   constante em 4 bytes.
7. **Símbolos somem** se as funções geradas não forem `noinline, used`: o
   compilador embute tudo e a verificação por endereço deixa de existir.

Evidências gravadas em `evidencias/`: listagem legível, desmontagem em JSON,
o C levantado e o resumo numérico da rodada.

**NÃO provado (e não será sem a ROM):** nada sobre o FireRed/BPRE do projeto
`../gba-re`. Sem o arquivo da ROM no disco, o melhor que este pipeline pode
fazer com ele é: nada. Não existe verdade-terreno, não existe byte para ler.

Para ROM de terceiros sem verdade-terreno, o caminho `rodada_binario` /
`cli levantar` grava explicitamente no relatório:

> ROM de terceiros: não existe verdade-terreno conhecida, então NÃO foi possível
> afirmar se o C levantado está correto — só foi possível compilá-lo e registrar
> o que ele executa.

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
