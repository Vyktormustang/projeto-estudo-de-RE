# O que já entendemos do código da ROM

**Imagem:** `pokemon_firered_bpre_trabalho.gba` — 16 777 216 bytes,
sha256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
Imagem de terceiros (modificação PT-BR), fora do repositório.

**De onde saem os números deste relatório:** da rodada **sem censo** (descoberta
partindo só do vetor de reset), que é a reproduzível daqui — ver
`evidencias/rom_bpre_boot_sem_censo.json`. Onde aparece número da rodada com
censo (r19), está dito. Cada afirmação abaixo é marcada como:

- **[medido]** — sai dos bytes: listagem, contagem, endereço verificado;
- **[inferido]** — sai de uma convenção documentada do GBA (mapa de memória,
  ABI do BIOS), não de execução;
- **[não provado]** — o que o levantamento **não** estabelece.

Este relatório não diz que as funções *fazem* o que as originais fazem. Nesta
ROM não existe verdade-terreno; o único lugar onde comportamento foi provado é o
corpus sintético, por emulação (60/60 casos no binário e no recompilado).

---

## 0. O tamanho do que se sabe

| medida | valor |
|---|---|
| janelas de código descobertas | **3 587** |
| instruções lidas | **208 458** |
| chamadas (`bl`) mapeadas | **8 588 arestas** |
| bytes distintos cobertos por essas janelas | **462 736 de 16 777 216 (2,76%)** |
| tabelas de `switch` reconhecidas | **166** (3 066 casos lidos da ROM) |
| instruções conferidas byte a byte | **208 249 / 208 458 (99,9%)** remontam idênticas |
| objeto compilado | **956 768 B, 0 erros** com `zig cc -mcpu=arm7tdmi` |

**97,2% da imagem não é código alcançável a partir do reset** — é gráfico,
áudio, texto, tabela de dados e código que só é alcançado por ponteiro em RAM.
E **janela não é sinônimo de função**: 540 das 3 587 (15,1%) não têm `bl` nem
prólogo `push {..., lr}`, e 52 dessas têm 100 instruções ou mais — são fortes
candidatas a dado lido como código (seção 9). O número de funções de verdade é
**menor que 3 587**; o de janelas é exatamente 3 587.

---

## 1. A imagem

- **[medido]** Cabeçalho: `POKEMON FIRE` / `BPRE` / versão `01` em `0x080000A0`.
  O complemento do cabeçalho **não confere** — esperado numa imagem modificada
  que não o recalculou.
- **[medido]** Em `0x08000108` há a string `pokemon red version`.
- **[medido]** 24 732 sequências ASCII de 6+ caracteres, concentradas em
  `0x084E0000` (1 131), `0x086A0000` (938), `0x084D0000` (672) — as regiões de
  texto/dados, não de código.
- **[medido]** A ROM carrega **strings de depuração do build original**, lado a
  lado com asserts: em `0x0843EDE4` está
  `== NULL` · `size<=252` · `PokemonSioInfo` · `LINK LOSS DISCONNECT!`.
  Ou seja: sobrou no binário o texto de um subsistema de **SIO (cabo de
  link)** com checagem de tamanho e mensagem de perda de conexão.

---

## 2. O começo: 14 instruções que ligam a máquina

**[medido]** A tabela de vetores do GBA é só o `b` inicial
(`0x08000000: b 0x08000204`). O código de boot é **ARM** e faz, em ordem:

```
0x08000204  mov  r0, #0x12        ; modo IRQ
0x08000208  msr  cpsr_fc, r0
0x0800020C  ldr  sp, [pc, #0x28]  ; sp = 0x03007E40   (pilha de IRQ)
0x08000210  mov  r0, #0x1F        ; modo SYS
0x08000214  msr  cpsr_fc, r0
0x08000218  ldr  sp, [pc, #0x18]  ; sp = 0x03007FA0   (pilha de usuário)
0x0800021C  ldr  r1, [pc, #0x1C]  ; r1 = 0x03007FFC
0x08000220  add  r0, pc, #0x20    ; r0 = 0x08000248
0x08000224  str  r0, [r1]         ; INSTALA o handler de IRQ no vetor do BIOS
0x08000228  ldr  r1, [pc, #0x14]  ; r1 = 0x080003A5  (entrada Thumb, bit0 = 1)
0x0800022C  mov  lr, pc           ; retorno = 0x08000234, montado à mão
0x08000230  bx   r1               ; chamada ARM -> Thumb
0x08000234  b    0x08000204       ; se main voltar, recomeça o boot
```

Três coisas que só apareceram ao ler os bytes:

1. **As duas pilhas** são montadas antes de qualquer código C: IRQ em
   `0x03007E40`, usuário em `0x03007FA0`.
2. **O handler de IRQ é instalado como dado**, escrito em `0x03007FFC` — e não
   por chamada. É por isso que a descoberta recursiva não o encontra (seção 3).
3. **A chamada para o `main` é uma chamada de verdade**: `mov lr, pc` + `bx r1`
   com o destino vindo do pool (`0x080003A5`). O desmontador antigo tratava esse
   `bx` como fim de fluxo e **perdia a instrução de retorno** em `0x08000234`.

**[inferido]** `0x03007FFC` é o ponteiro de IRQ na BIOS RAM (mapa do GBA);
`0x03007E40`/`0x03007FA0` são as pilhas padrão do console.

---

## 3. O handler de IRQ existe — e o levantamento recursivo não o vê

**[medido]** O endereço instalado, `0x08000248`, é código ARM válido:

```
0x08000248  mov  r3, #0x4000000
0x0800024C  add  r3, r3, #0x200    ; r3 = 0x04000200
0x08000250  ldr  r2, [r3]          ; lê REG_IE
0x08000254  ldrh r1, [r3, #8]      ; lê REG_IF (0x04000208)
0x08000258  mrs  r0, spsr          ; salva o CPSR do modo interrompido
0x0800025C  push {r0, r1, r2, r3, lr}
```

**[inferido]** `0x04000200` = `REG_IE`, `0x04000208` = `REG_IF`: é o prólogo
clássico de um dispatcher de interrupção.

**[medido]** Esse endereço **não está** nas 3 587 janelas da rodada sem censo,
nem entre os 45 descartes. Ele só existe na rodada com censo (r19), porque o
censo o informa como semente. **É a explicação concreta de boa parte da
diferença 3 587 × 8 172**: funções alcançadas apenas por *ponteiro guardado em
RAM* (IRQ, callbacks, tabelas de script) não são alcançáveis por recursão a
partir do vetor de reset. Das 8 172 funções do censo, **2 191 não estavam no
censo** e foram descobertas pelo grafo; das 3 587 do boot, **655 não têm nenhum
chamador** — 628 nasceram de ponteiro de pool, 25 de salto para trás, 1 é o
vetor de reset e 1 é o veneer ARM. Ou seja: o grafo tem muitas raízes que não são
"chamadas".

---

## 4. Todo o BIOS passa por uma tabela de thunks

**[medido]** Em `0x081E3B58`–`0x081E3BA6` há uma sequência de stubs de 4 bytes,
`svc #n; bx lr`, um por serviço do BIOS:

| endereço | `svc` | serviço (ABI do GBA) | quem usa |
|---|---|---|---|
| `0x081E3B58` | `0x0A` | ArcTan2 | não descoberto como janela |
| `0x081E3B5C` | `0x0E` | BgAffineSet | — |
| `0x081E3B60` | `0x0C` | CpuFastSet | — |
| `0x081E3B64` | `0x0B` | CpuSet | **129 chamadas** |
| `0x081E3B68` | `0x06` | Div | — |
| `0x081E3B6C` | `0x12` | LZ77UnCompVram | — |
| `0x081E3B70` | `0x11` | LZ77UnCompWram | — |
| `0x081E3B74` | `0x25` | SoundDriverVSyncOff (`r1 = 1`) | — |
| `0x081E3B7C` | `0x0F` | ObjAffineSet | — |
| `0x081E3B80` | `0x01` | RegisterRamReset | **primeira chamada do main** |
| `0x081E3B9C` | `0x08` | Sqrt | — |
| `0x081E3BA2` | `0x05` | VBlankIntrWait | — |

O mais chamado deles é o `CpuSet` (129 sítios) — é o `memcpy`/`memset` da ROM.
Em `0x081E3B84` há um stub maior que faz `sp = 0x03007FA0`, `svc #1`
(RegisterRamReset) e `svc #0` (SoftReset): é o **reset de software**.

Logo depois, em `0x081E3BA8`, começa a tabela de thunks `bx rN` + nop
(`bx r0`, `bx r1`, … `bx r5`) — 9 sítios, os "chame pelo registrador N" que o
levantador recusa de propósito (traduzir exigiria inventar a assinatura).

**[inferido]** A numeração e os nomes dos serviços vêm da ABI do BIOS do GBA.
**[medido]** O `main` (`0x080003A4`) começa com `r0 = 0xFF; bl 0x081E3B80`, e
`0x081E3B80` é `svc #1` — ou seja, a primeira coisa que o jogo faz é
**limpar toda a RAM** (`RegisterRamReset(0xFF)`).

**Anomalia aberta:** há **12 sítios de `svc` com número que não existe no BIOS**
(`0xAB` ×7, `0x2E` ×4, `0xFF` ×1). O `0xFF` está dentro de uma palavra de pool
lida (`0xFFFFDFFF`), logo é dado. Os outros **não** estão em pool e aparecem em
janelas que parecem código normal (prólogo, chamada, epílogo) — por exemplo
`0x081E9A54`: `push {r4,r5,lr}; sub sp,#0xC; bl 0x081E9958; str r0,[sp];
r0 = 6; r1 = sp; svc #0xAB`. Não sei o que é. Fica registrado como pergunta, não
como conclusão.

---

## 5. O hub de 653 chamadas: ler um campo pelo número

**[medido]** `0x0803FBE8` é a rotina mais chamada do grafo (653 sítios). Ela
recebe `(ponteiro, id)` e faz `id - 0x37`; se `<= 0x21` (33), salta por uma
**tabela de 34 entradas em `0x0803FC08`**. Os casos leem campos fixos da
estrutura:

| casos | o que fazem |
|---|---|
| 0 | `u32` em `+0x50` |
| 1 | `u8` em `+0x54` |
| 9 | `u8` em `+0x55` |
| 2, 3 | `u16` em `+0x56`, `+0x58` |
| 29–33 | `u16` em `+0x5A`, `+0x5C`, `+0x5E`, `+0x60`, `+0x62` |
| 4–8 | chamam `0x08044674(struct, 1..5)`; se o `u16` de retorno for ≠ 0, devolvem; se 0, caem no `u16` correspondente (`+0x5A`…`+0x62`) |
| padrão (`id` fora de 0x37–0x59) | chama `0x0803FD44(struct, id)` |

**Leitura:** é um **acessador de campo por número** (`get_field(struct, id)`)
sobre uma estrutura com pelo menos 0x63 bytes, com uma faixa "virtual" (4–8) que
consulta uma tabela externa antes. 653 chamadas fazem dela o ponto de leitura
mais usado do código alcançável.

---

## 6. `0x08000A38`: uma tabela de 96 `u16` em IWRAM, com guarda de VCOUNT

**[medido]** 350 chamadores, e o corpo começa assim:

```
r4 = r0 & 0xFF
r1 = r1 & 0xFFFF
if (r4 > 0x5F) goto 0x08000AB4      ; índice válido: 0..95
*(u16 *)(0x03000000 + r4*2) = r1    ; grava na tabela em IWRAM
r0 = REG_VCOUNT (0x04000006) & 0xFF
if ((r0 - 0xA1) <= 0x40) ...        ; VCOUNT em 161..225
```

**Leitura:** grava um parâmetro indexado (0–95) numa tabela de 192 bytes no
início da IWRAM e tem uma condição de tempo ligada ao `VCOUNT` — escrita
sincronizada com o feixe, típica de registro de vídeo/som cujo efeito só vale
na janela certa.

---

## 7. Tabelas de `switch`: 166 reconhecidas, 3 066 casos lidos

**[medido]** Cada tabela é lida da própria ROM (o guarda `cmp` e o `ldr` do
pool), e o C sai como `switch`. As maiores:

| salto | casos | guarda |
|---|---|---|
| `0x0805234C` | **268** | por registrador; limite `0x10B` (267) lido do pool |
| `0x08050F5C` | **268** | idem |
| `0x08053EAA` | 102 | imediato |
| `0x081E6214` | 89 | imediato (duas janelas compartilham) |
| `0x0803FDD2` | 84 | imediato |
| `0x08040560` | 81 | imediato |

**[medido]** As duas tabelas de 268 casos **não são a mesma**: 59 e 57 alvos
distintos, e em ambas **210 dos 268 casos apontam para o mesmo endereço**
(`0x08053774`). É um `switch` esparso — a maioria dos índices cai no tratamento
padrão.

---

## 8. Idiomas do compilador que aparecem em todo lugar

| idioma | ocorrências [medido] | o que significa |
|---|---|---|
| `pop {rN}` + `bx rN` | **2 973** | o retorno padrão deste binário (em vez de `pop {pc}`) |
| `ldr rX, [pc, #N]` (pool) | **11 787 pools** lidos | constantes e endereços vêm de pool, não de imediato |
| `adr` + `bx` | 3 pares | troca ARM↔Thumb por veneer |
| `mov r8, r8` | nops de alinhamento | preenchimento entre thunks |
| funções ARM | **2** (`0x08000000`, `0x081DC014`) | só o boot e uma rotina de 3 instruções (`umull; add; bx lr`) |

**[medido]** O modo ARM praticamente não aparece: **16 instruções ARM em
208 458** (0,008%). A ROM é Thumb de ponta a ponta, com o boot e um veneer em ARM.

---

## 9. O que é código e o que é dado — a parte que impede ler os números errado

O levantamento **não** afirma que toda janela é função. As evidências de que uma
parte é dado lido como código:

- **[medido] 540 janelas (15,1%) sem `bl` e sem prólogo**; 52 delas com ≥100
  instruções.
- **[medido] A maior "função" da ROM, `0x08262054`, tem 5 880 instruções,
  zero `bl` e zero tabelas**, nasceu de um ponteiro de pool (`0x0804EE1C`) e
  começa com `ff 04 03 13 03 00 00 00 — ff 7f 10 00`: valores pequenos em
  little-endian, não código. É quase certamente **dado**.
- **[medido] 1 037 instruções (0,50%) ficam dentro de palavras de pool** que o
  próprio código lê: os mesmos bytes são dado e "instrução".
- **[medido] 45 endereços** foram tentados como semente e **descartados** por não
  terem instrução válida do ARM7TDMI — os bytes são do tipo `ff bb`, `ff f8`,
  `ff ef`, típicos de dado comprimido/gráfico.
- **[medido] 12 `svc` com número impossível** (seção 4).
- **[medido] 159 janelas têm a leitura interrompida por dado** (95 param numa
  instrução que o alvo não tem — `add.w`, `cbnz`, `udf`, bloco IT — e 64 em bytes
  que não decodificam). Estão marcadas no C como lacuna, não escondidas.

Nada disso é falha silenciosa: cada janela carrega a semente no cabeçalho do C
(`/* origem: 0x... semente: ... */`) e cada parada está escrita no ponto.

---

## 10. Números da rodada (sem censo — a reproduzível daqui)

| medida | valor |
|---|---|
| janelas / instruções / arestas | 3 587 / 208 458 / 8 588 |
| completas / parciais | 3 391 / 196 |
| recusas de instrução | 63 (17 desvio indireto sem origem, 11 desvio para trás fora da função, 9 Thumb-2 = dado, 9 thunks, 2 PSR, 2 ILHA ARM, …) |
| janelas que param em dado | 159 |
| descartes de semente | 45 |
| tabelas de casos / casos | 166 / 3 066 |
| conferência byte a byte | 208 249 / 208 458 = 99,9% |
| C levantado | 483 244 linhas / 18 292 786 bytes |
| objeto compilado | 956 768 B, 0 erros |

Rodada **com censo (r19, histórica — o `functions.csv` não existe mais)**:
8 172 funções, 460 868 instruções, 20 492 arestas, 377 tabelas / 6 303 casos,
191 recusas, objeto de 2 164 988 B, 1 056 638 linhas de C. **Não é reproduzível
a partir deste repositório** e não se soma aos números acima: são escopos
diferentes da mesma imagem.

---

## 11. O que ainda não sabemos

- **Semântica.** Nenhuma afirmação de que uma função levantada *faz* o que a
  original faz. Só o corpus sintético prova comportamento, e ele é sintético.
- **Os `svc #0xAB`.** Sete sítios em código que parece normal, com um número que
  o BIOS do GBA não tem.
- **O que `0x0803FBE8` acessa.** Sabemos *como* lê (campo por índice) e *onde*
  (offsets fixos), não *o que* a estrutura representa.
- **As 655 raízes sem chamador.** 628 vêm de ponteiro de pool: são alvo de
  tabela, mas qual tabela e quem a percorre ainda não foi levantado.
- **97,2% da imagem.** O que não é alcançável a partir do reset — gráficos,
  áudio, texto, dados — não foi tocado por este pipeline.
- **A ordem de execução.** O C levantado é uma tradução instrução-por-instrução
  com `goto` e flags explícitas; ele é *legível*, não é o programa reconstruído.

---

*Gerado a partir de `evidencias/rom_bpre_boot_sem_censo.json`,
`evidencias/rom_bpre_analise.json` e das medições descritas no `README.md`
(itens 1–22). Todo número aqui pode ser refeito com os comandos do README.*
