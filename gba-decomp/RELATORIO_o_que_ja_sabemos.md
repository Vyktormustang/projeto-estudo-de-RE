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

## 9.5. O texto do jogo é legível (charset decifrado)

**[medido]** O texto usa o charset ocidental do Gen 3 e decodifica em português.
Testado por hipótese e **confirmado pelo contexto** (o texto ao redor sai
coerente, não aleatório):

| byte | carácter |
|---|---|
| `0xBB`–`0xD4` | `A`–`Z` |
| `0xD5`–`0xEE` | `a`–`z` |
| `0x00` | espaço |
| `0x1B` | `é` |
| `0x17` | `á` · `0x1C` `ê` · `0xF4` `ã` |
| `0xAD` `.` · `0xB8` `,` · `0xAB` `!` · `0xAC` `?` | pontuação |
| `0xFE` | quebra de linha · `0xFB` novo bloco · `0xFF` fim da string |

Exemplo real em `0x081B44A4`:

```
éMON selvagem escapa da<FE>POKé BALL, é porque ainda está<FE>muito forte…
```

E em `0x08176460`:

```
EQUIPE ROCKET está atrás da MASTER BOLA, é a melhor POKé BOLA.
```

Isto é o primeiro pedaço de **semântica** que o levantamento conseguiu: até
aqui só havia estrutura. Ele não diz nada sobre a bag, mas dá o instrumento para
chegar lá — achar a tabela de nomes de item e o código que a indexa.

**[medido] O que ainda falta para "onde mudar a quantidade de Poké Bolas":**
a bag não é constante de ROM. Ela vive na RAM (bloco de save), alcançada por
**ponteiro em RAM**, e o código só tem offsets relativos a esse ponteiro. Uma
anotação antiga dizia "bolsa = `0x020258B8`"; conferido agora, **esse literal
não aparece nenhuma vez na imagem** (0 ocorrências de `B8 58 02 02`) — está
descartado. Sem executar o jogo ou sem uma referência externa de símbolos, o
endereço absoluto não sai do estático.

## 9.6. A BAG: onde ficam os itens — **medido na ROM**

Esta seção responde "qual campo mudar para ter Poké Bolas". Ela existe porque a
cadeia toda foi **fechada dos dois lados**: o que a ROM faz (medido nos bytes) e
o que a decompilação pública `pret/pokefirered` diz (referência externa), sem
nenhum dos dois depender do outro.

### 9.6.1 A tabela de itens

**[medido]** Em `0x083DB028` há uma tabela de entradas de **44 bytes (0x2C)**, com
o nome inline nos primeiros 14 bytes (charset da seção 9.5, terminado em `0xFF`).
A base é referenciada por **15 literais** na imagem. Preços conferem com os
oficiais: Master 0, Ultra 1200, Great 600, Poké 200, Potion 300.

| offset | campo | accessor na ROM |
|---|---|---|
| +0x00 | `name[14]` | (inline) |
| +0x0E | `itemId` (u16) | `0x0809A8DC` |
| +0x10 | `price` (u16) | `0x0809A900` |
| +0x12 | `holdEffect` (u8) | `0x0809A924` |
| +0x13 | `holdEffectParam` (u8) | `0x0809A948` |
| +0x14 | `description` (ptr) | `0x0809A96C` |
| +0x18 | `importance` (u8) | `0x0809A990` |
| +0x19 | `registrability` (u8) | `0x0809A9B4` |
| **+0x1A** | **`pocket` (u8)** | `0x0809A9D8` |
| +0x1B | `type` (u8) | `0x0809A9FC` |
| +0x1C | `fieldUseFunc` (ptr) | `0x0809AA20` |
| +0x20 | `battleUsage` (u8) | `0x0809AA44` |
| +0x24 | `battleUseFunc` (ptr) | `0x0809AA68` |
| +0x28 | `secondaryId` (u8) | `0x0809AA8C` |

Os **14 campos batem um a um** com `struct Item` de `include/item.h` do
`pokefirered` — nenhum sobrando, nenhum faltando.

**Verificação independente:** lendo o campo `pocket` na tabela, os itens caem
exatamente nas cinco pockets: bolas (1–5) → **3**; poções (13, 20, 21) → **1**;
frutos (133, 134, 175) → **5**; TMs (290+) → **4**. Isso é consistência interna da
ROM, não confiança na referência.

### 9.6.2 Onde as pockets ficam

**[medido]** A rotina em `0x08099E44` inicializa o array `gBagPockets`
(`0x0203988C`, passo 8: ponteiro do pocket em +0, capacidade em +4):

```
08099E46  ldr r0, [pc, #0x40]   ; = 0x03005008   (gSaveBlock1Ptr)
08099E48  ldr r2, [r0]          ; r2 = *gSaveBlock1Ptr
08099E4A  movs r3, #0xc4
08099E4C  lsls r3, r3, #2       ; r3 = 0x310
08099E4E  adds r0, r2, r3        ; ITENS        +0x310
08099E52  movs r0, #0x2a        ; 42 slots
08099E56  adds r3, #0xa8        ; +0x3B8       ITENS-CHAVE
08099E5C  movs r0, #0x1e        ; 30 slots
08099E60  adds r3, #0x78        ; +0x430       POKé BOLAS
08099E66  movs r0, #0xd         ; 13 slots
08099E6A  adds r3, #0x34        ; +0x464       TM/HM
08099E70  movs r0, #0x3a        ; 58 slots
08099E74  ldr r0, [pc, #0x14]   ; = 0x54C     FRUTOS
08099E7C  movs r0, #0x2b        ; 43 slots
```

| pocket | offset em SaveBlock1 | slots |
|---|---|---|
| Itens | `+0x310` | 42 |
| Itens-chave | `+0x3B8` | 30 |
| **Poké Bolas** | **`+0x430`** | **13** |
| TM/HM | `+0x464` | 58 |
| Frutos | `+0x54C` | 43 |

A aritmética fecha com a tabela de estrutura (`0x310 + 42×4 = 0x3B8`,
`0x3B8 + 30×4 = 0x430`, `0x430 + 13×4 = 0x464`, `0x464 + 58×4 = 0x54C`,
`0x54C + 43×4 = 0x5F8` = `seen1`).

### 9.6.3 O slot, e o XOR na quantidade

**[medido]** `struct ItemSlot` = `{ u16 itemId; u16 quantity; }` — 4 bytes. A ROM
escreve `strh` no offset 0 (itemId) e no offset +2 (quantity).

**[medido]** A quantidade é guardada **cifrada**. `0x08099DBC`:

```
08099DC0  ldr r2, [pc, #0x10]   ; = 0x0300500C   (gSaveBlock2Ptr)
08099DC2  ldr r2, [r2]
08099DC4  movs r3, #0xf2
08099DC6  lsls r3, r3, #4       ; r3 = 0xF20
08099DC8  adds r2, r2, r3
08099DCA  ldr r2, [r2]          ; encryptionKey
08099DCC  eors r1, r2
08099DCE  strh r1, [r0]         ; guarda quantity ^ key
```

Bate com `src/item.c` do `pokefirered`
(`*ptr = value ^ gSaveBlock2Ptr->encryptionKey;`) e com `SaveBlock2`, que tem
`/*0xF20*/ u32 encryptionKey;`.

### 9.6.4 Resposta: qual campo

```
base = *(u32 *)0x03005008          # gSaveBlock1Ptr
slot = base + 0x430 + i * 4        # i = 0..12, pocket de Poké Bolas
*(u16 *)(slot + 0) = itemId        # 1=Master, 2=Ultra, 3=Super, 4=Poké, 5=Safari
*(u16 *)(slot + 2) = N ^ (encryptionKey & 0xFFFF)

encryptionKey = *(u32 *)(*(u32 *)0x0300500C + 0xF20)
```

**[medido] Endereços de referência:** `gSaveBlock1Ptr` = `0x03005008` (453
ocorrências na imagem), `gSaveBlock2Ptr` = `0x0300500C` (266). O endereço do
Emerald, `0x03005D8C`, aparece **0 vezes** — é linha FireRed, coerente com o
cabeçalho `BPRE`.

**O que isto NÃO é:** não é um offset de ROM que se possa patchear. É RAM: o
valor vale para a sessão e é o que o jogo grava no save quando você salva. Um
patch de ROM que "dê Poké Bolas" tem de mexer na rotina que entrega item ou no
script que a chama — não numa constante.

**[medido] As funções da bag, agora separadas por comportamento** (a versão
anterior desta seção dizia que `AddBagItem` e `RemoveBagItem` não tinham sido
separadas — foram, lendo a aritmética):

| função | endereço | o que faz, medido nos bytes |
|---|---|---|
| `GetBagItemQuantity` | `0x08099DA0` | `*ptr ^ encryptionKey` (lê e trunca em u16) |
| `SetBagItemQuantity` | `0x08099DBC` | `*ptr = value ^ encryptionKey` |
| `GetPcItemQuantity` | `0x08099DD8` | `ldrh r0,[r0]` — PC **não** é cifrado |
| `SetPcItemQuantity` | `0x08099DDC` | `strh r1,[r0]` |
| `ClearItemSlots` | `0x0809A274` | zera `capacidade` slots de uma pocket |
| `ResetBag` | `0x0809A2DC` | laço nas 5 pockets → `ClearItemSlots` |
| **`AddBagItem`** | **`0x0809A084`** | `ItemId_GetPocket` → `pocket-1` em `gBagPockets` → procura o item; se existe, `GetBagItemQuantity`, **soma** `count` e recusa acima de **999** (`0x3E7`); se não existe, acha slot livre com `0x08099ECC` e grava `strh itemId` + `SetBagItemQuantity` |
| **`RemoveBagItem`** | **`0x0809A1D8`** | mesmo caminho, mas **subtrai**; se a quantidade chega a zero, grava `itemId = 0` |
| `AddPCItem` | `0x0809A3C8` | **não é bag**: usa `pcItems` (`SaveBlock1+0x298`) e as versões de PC, sem cifra |

A distinção `Add`/`Remove` está medida: `0x0809A084` tem `adds r1,r0,r2` seguido
de `cmp r1, 0x3E7` e `ble` para o `SetBagItemQuantity`; `0x0809A1D8` tem
`subs r0,r0,r7` e, em `0x0809A238`, `cmp r4,#0` + `strh r4,[r0]` para limpar o
`itemId` quando a quantidade zera.

Essa separação é o que permite o patch da seção 11: em vez de reimplementar o
slot e o XOR, o patch chama `AddBagItem(4, 99)` — a mesma função que o jogo usa
ao pegar um item.

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

## 11. Como modificar o jogo (patch binário verificado)

**O que não é:** não é recompilar o jogo a partir do C levantado. Esse C cobre
2,76% dos bytes e **não tem os dados** (mapas, gráficos, texto, tabelas de
encontro); recompilar a partir dele produziria um binário que não é o jogo.

**O que é:** trocar bytes na imagem, com quatro guardas, e executar o resultado
no emulador antes de afirmar que funcionou.

1. **Montar para o endereço certo.** `bl` e pool de literais são relativos;
   montar para um endereço e injetar em outro desvia para o lugar errado. O
   `patch.montar_thumb(codigo, endereco)` exige o destino.
2. **Exigir o byte esperado.** Todo patch carrega o que espera encontrar.
   Aplicar num endereço com outro conteúdo (ROM diferente, patch já aplicado) é
   erro, não aviso. O `esperado` tem de ser uma **constante** — ler da própria
   imagem torna a conferência tautológica e deixa a segunda aplicação passar
   (foi um defeito real, corrigido durante este trabalho).
3. **Injetar só em espaço livre de verdade.** Nesta ROM há **66** sequências de
   `0xFF` maiores que 32 bytes, e a maioria é padding entre funções ou trecho de
   gráfico comprimido. O primeiro trecho de 81 bytes fica em `0x081BA4E6`, no
   meio de dados. Exigindo pelo menos **4 KiB** sobram três: `0x088001C7`
   (5 242 425 B), `0x08EB0B20` (1 373 408 B) e `0x0871A905` (939 771 B).
4. **Verificar por emulação.** O stub é executado no unicorn sobre a ROM já
   patcheada, com `SaveBlock1`, `SaveBlock2` e `gBagPockets` montados à mão, e o
   efeito é lido **pelas funções do jogo**, não por uma reimplementação.

### 11.1 O exemplo medido: 99 Poké Bolas ao começar o jogo

`ferramentas/aplicar_patch_pokebolas.py`. O hook é `0x08054B06`, o
`bl ResetBag` dentro de `NewGameInitData` (função `0x08054A60`). O stub chama
`ResetBag` e depois `AddBagItem(4, 99)`:

```
10 b5              push {r4, lr}
7f f5 e8 f4        bl   0x0809A2DC      ; ResetBag
04 20              movs r0, #4         ; ITEM_POKE_BALL
63 21              movs r1, #99
7f f5 b8 f3        bl   0x0809A084      ; AddBagItem
10 bd              pop  {r4, pc}
```

| medida | valor |
|---|---|
| stub | **16 bytes** em `0x0871A906` |
| bytes alterados na ROM | **20** (4 no hook + 16 no stub) |
| sha256 da ROM patcheada | `b2f9f0fa0294f050cf6213b9c1082f68b06637fb59f541d3cf869ad0e4db3945` |
| complemento do cabeçalho | `0xBD = 0x68`, inalterado e conferido |
| `itemId` no slot 0 | **4** |
| quantidade lida por `GetBagItemQuantity` (`0x08099DA0`) | **99** (cifrada `0x561B` com chave `0x12345678`) |
| `ItemId_GetPocket(4)` | **3** (pocket de Poké Bolas) |
| outras quatro pockets | nenhum slot com item |
| segunda aplicação | recusada com "ROM diferente ou patch já aplicado" |

A escolha do ponto importa e está medida: `SetSaveBlocksPointers`
(`0x0804C058`) roda no **boot**, antes de o save existir, e `ResetBag` zera as
cinco pockets — escrever antes dele seria sobrescrito. O hook é o **único**
chamador real de `ResetBag` (o outro candidato, `0x08111374`, é **dado**, não
código).

### 11.2 O que fica provado — e o que não fica

**Provado por execução:** o stub, rodando sobre a ROM patcheada, zera as cinco
pockets e grava item 4 / quantidade 99 na pocket de Poké Bolas; a leitura feita
pela função do jogo devolve 99; `ItemId_GetPocket` classifica o item 4 na pocket
3; nenhuma outra pocket recebe item; o `bl` do hook aponta para o stub; o
cabeçalho continua válido; a ROM continua reconhecida como `POKEMON FIRE` /
`BPRE`.

**Não provado:** (a) que o boot real chegue a `0x08054B06` com
`gBagPockets[2].itemSlots` apontando para `SaveBlock1+0x430` — é **inferência**
a partir de `SetBagPocketsPointers`, que roda no boot, mas não foi observada;
(b) que a tela da bag exiba 99 — a leitura usa a função do jogo, mas não houve
execução num emulador de console; (c) **nada foi jogado**, nem em emulador de
GBA, nem no aparelho.

### 11.3 Para fazer outro patch

O ferramental é `gbadecomp/patch.py` (`montar_thumb`, `achar_espaco_livre`,
`Patch`, `aplicar`, `corrigir_cabecalho`) e o exemplo acima é o molde: achar o
ponto certo no fluxo, montar um stub que chame funções do jogo, trocar uma
instrução por um `bl`, verificar por emulação. O que muda de um patch para outro
é **qual função chamar** e **onde pendurar o salto** — por isso o mapa de
endereços da seção 9.6.

## 12. O que ainda não sabemos

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

## 15. Mochila: qual campo da' poke bolas (2026-10-17, MEDIDO EM JOGO)

Esta secao responde a pergunta "qual campo mudar para conseguir poke bolas" com
prova dentro do jogo, e nao por inferencia de estrutura.

**MEDIDO**:

- `gBagPockets` e' o ARRAY em `0x0203988C` (nao um ponteiro para ele). Cada
  entrada tem 8 bytes: `{ u32 itemSlots; u8 capacity; u8 pad[3] }`.
- As cinco entradas, lidas com o jogo em execucao no overworld:

  | indice | itemSlots | offset em SaveBlock1 | capacity |
  |---|---|---|---|
  | 0 | `S1+0x310` | +0x310 | 42 |
  | 1 | `S1+0x3B8` | +0x3B8 | 30 |
  | 2 | `S1+0x430` | +0x430 | 13 |
  | 3 | `S1+0x464` | +0x464 | 58 |
  | 4 | `S1+0x54C` | +0x54C | 43 |

  Bate exatamente com `include/global.h` do pret/pokefirered. Medido, nao
  suposto: os cinco ponteiros foram lidos de `0x0203988C` em tempo de execucao.

- Cada slot tem 4 bytes: `u16 itemId` e `u16 quantidade`.
- **A quantidade e' cifrada**: slot vazio NAO e' zero. Com a mochila vazia os
  slots liam `00 00 04 85` (itemId 0, quantidade `0x8504`) e a chave em
  `SaveBlock2+0xF20` era `0x0E078504`. A metade baixa da chave e' `0x8504`:
  a quantidade gravada e' `qtd ^ (chave & 0xFFFF)`.
- **Prova visual**: gravando `itemId=4` e `99 ^ 0x8504` em `S1+0x430`, abrindo
  o menu e a BOLSA, a tela mostra "POKe BOLA x 99" na pocket POKe BOLAS
  (`evidencias/mochila_pokebola_99.png`).

**NAO PROVADO**:

- Que exista um ponto unico no codigo que inicialize a bag e que possa ser
  patchado para ja' nascer com bolas. Sete conjuntos de call-sites foram
  instrumentados (NewGameInitData, ResetBag, ClearItemSlots, GetBagItemQuantity,
  modulo da mochila, UI da bolsa, handlers de IRQ) e **nenhum** disparou no
  fluxo de jogo novo / abertura de bolsa -- ver `NOTAS_DE_TRABALHO.md` secao 14.
- Portanto o patch de ROM que da' bolas automaticamente continua **aberto**. O
  que existe e' (a) o campo e a codificacao, provados em jogo, e (b) a prova de
  que codigo injetado em espaco livre executa (stub ARM no reset, contador = 1).

**Efeito colateral medido**: o keystone 0.9.2 resolve `ldr rX, =VALOR` com
deslocamento errado a partir do segundo literal do bloco. Isso ja' foi corrigido
(`patch.montar_thumb_literais`, 5 testes). Era a causa de varios "o hook nao
roda" anteriores.

## 16. Injeção de código: o que passou a estar **medido** (2026-10-17)

**Medido:**

- O `bl` do Thumb no ARM7TDMI alcanca **so' ±4 MiB**. Keystone e capstone o
  tratam como o `bl` do Thumb-2 (±16 MiB) e **nao avisam**. Todo codigo injetado
  em `0x0871A906` a partir de um hook em `0x0800xxxx` estava saltando para
  `0x0831A906` -- lixo. Isso invalida os testes anteriores de hook que ficaram
  a mais de 4 MiB (`rom_bolas_v3`, `rom_bagmap`, `rom_marca_c/a2`, `rom_bolas_c`,
  entre outros): eles nao provavam "o codigo nao executa", provavam que o salto
  estava errado.
- Com o stub perto do hook (padding `0x080000C0`, 64 bytes livres) e a chamada
  longa feita por um thunk (`ldr r3,=alvo|1; bl thunk; ... thunk: bx r3`), o
  codigo roda: `rom_marca_c3.gba` incrementa `0x02037F00` ~1 vez por quadro
  desde o boot (570 em 600 quadros; 11 588 em 12 000).
- O hook `0x080004A6` e' o `bl 0x08000890` do `AgbMain`, e `0x08000890` e' uma
  **espera de VBlank** (gira em `0x080008AA..B2` ate' o bit 0 de
  `0x0300310C`). O PC amostrado por save state fica nesse laco a maior parte
  do tempo -- o jogo nao esta' travado, esta' esperando o VBlank.

**Nao provado / bloqueio aberto:**

- Nesta ROM (traducao BR), o jogo **nao sai da tela de titulo** no emulador
  mGBA: as teclas chegam (`KEYINPUT` = `f703` com START; `gMain.heldKeys`
  0x03003118 e `newKeys` 0x0300311C = `0x0008`), mas START/A/B/direcional nao
  abrem o menu, e forcar essas variaveis por codigo injetado tambem nao.
  Os callbacks vistos no ciclo sao `0x08078BB5` (intro/titulo), `0x080EC9ED` e
  `0x080EC5A5`. A causa (hack de traducao x core libretro) **nao foi
  determinada**.
- Estados salvos do mGBA (`salvar_estado`) carregaram **inertes** em pelo menos
  dois casos: o jogo nao responde a botao nenhum depois de carregar, nem na ROM
  sem patch. Nao usar estado salvo como banco de teste sem validar a resposta a
  um botao.
- A rotina `0x08056644` chama `NewGameInitData` e parece ser o inicio de um
  jogo novo, mas chama-la pelo hook (aos 1 600 quadros) zerou
  `gMain.callback2` e deixou a tela parada. Nao serve como atalho sem entender
  o estado esperado.

## 17. Título destravado (2026-10-17): o bloqueio era de medição, não do jogo nem do core

**MEDIDO (nesta ROM, no nosso harness, repetido com os mesmos quadros):**

- O campo que líamos como `callback2` (`0x030030FC`) é o `vblankCallback`
  (+0x0C do `gMain`); o `callback2` de verdade fica em `0x030030F4` (+0x04),
  e o `newKeys` que o jogo testa (`JOY_NEW`) fica em `0x0300311E` (+0x2E) —
  layout do `include/main.h` do pret/pokefirered, confirmado pelo
  comportamento. Os testes antigos que forçavam "teclas" e "menu"
  escreviam nos campos vizinhos; as conclusões tiradas deles estão anuladas.
- A máquina de estados do título é saudável: sem aperto, ela faz o ciclo
  completo (título → cena RUN/"PRESS START" ~1730 quadros → 2700 quadros de
  espera → RESTART ~4200 → copyright/intro → título de novo). A tarefa do
  título é `0x08078C25` (data[0]=cena), o timer é `0x08078BED` e o
  `callback2` do título é `0x08078B9D`.
- Apertando A **na cena RUN**, o jogo sai do título: no mesmo quadro do
  `newKeys=1` (quadro 1733) a cena vira CRY, e aos 1870 a tarefa do título
  morre e o `callback2` troca. Com pulsos periódicos de A, o jogo chega à
  tela de nomear o jogador (~6500 quadros). Evidências:
  `evidencias/titulo_press_start.png`, `apos_titulo_controle.png`,
  `intro_nome_jogador.png`; ferramenta: `ferramentas/ir_ao_menu.py`.
- Teste de controle com uma ROM homebrew de terceiros (projeto
  gba-harness, código revisado antes de rodar): no nosso harness, o pixel
  do START acende ao segurar START e fica preto sem botão — a cadeia de
  entrada sempre entregou as teclas.
- Um aperto nas cenas de abertura (0–2) só pula a animação para a cena
  RUN; é preciso um **segundo** aperto, já na RUN, para sair do título.
  Isso, mais julgar a tela por hash de VRAM (que não muda na RUN nem em
  fades de paleta), explica todas as observações anteriores de "travado".
- Dois defeitos reais do nosso harness foram encontrados na revisão e
  corrigidos (com 4 testes novos; suíte em 104 testes verdes), sem serem
  a causa do bloqueio: escrita de 4 bytes onde a ABI libretro pede um
  `bool` de 1 byte, e tratamento da `struct retro_variable` como texto.

**NÃO PROVADO:**

- Se a lista do menu principal ("NOVO JOGO") é exibida entre os quadros
  1860–1875 (a primeira tela capturada depois da transição é a página
  CONTROLE da sequência de novo jogo) — falta amostragem quadro a quadro.
- Os nomes dos callbacks pós-título (`0x0800C301` transitório e
  `0x0812EB11`): são inferidos do fluxo do pret, ainda sem desmontagem
  confirmando nesta ROM.
- O harness do gba-harness **não foi executado** (exige Python 3.12; o
  sandbox tem 3.11.2) — foi apenas lido. O libretro.py também não foi
  executado; deixou de ser necessário depois do teste de controle.

## §18 — Overworld: do boot ao quarto, com estado validado (2026-10-20)

**MEDIDO** (3 execuções com quadros e hashes idênticos;
`ferramentas/ir_ao_overworld.py` + `validar_estado_overworld.py`):

- A navegação completa é determinística: sai do título no q.1870
  (transitório `0x0800C2D5`), q.1885 `0x0812EB11` (diálogos, 96 pulsos de
  A no total), telas de nomear `0x0809FB71` nos q.4540 (jogador) e q.5365
  (rival), e q.6595 `0x080565B5` estável = overworld; chegou no q.6955
  com `pos=(6,6)`, grupo 4, mapa 1 — o quarto do jogador (PNG em
  `evidencias/overworld_quarto.png`).
- Na tela de nomear, **START só move o cursor ao botão OK; quem confirma
  é o A** (pret `naming_screen.c` + medido: a 1ª versão, só com START,
  travou até o limite).
- **Correção sobre §§ anteriores**: o endereço do SaveBlock1 **não é
  fixo**. No overworld, `gSaveBlock1Ptr` (`0x03005008`) vale
  `0x0202557C` (+0x38 sobre o `0x02025544` de sessões anteriores, que
  aqui está zerado). Ler sempre pelo ponteiro.
- O estado salvo no overworld (528.448 B, fora do Git) carrega **vivo**
  num processo novo: BAIXO (6,6)→(6,8), DIREITA →(9,8), START abre o
  menu (BOLSA/SALVAR/OPÇÕES/SAIR) e B fecha com o framebuffer voltando
  byte-idêntico (hash `890d5737`). Diferente dos estados inertes da
  §16.3, este é ponto de partida reutilizável (e regenerável em ~1 min).

**NÃO PROVADO**:

- Os nomes dos três callbacks (`0x0812EB11`, `0x0809FB71`, `0x080565B5`)
  continuam inferidos do comportamento/pret, sem desmontagem nesta ROM.
- A causa da variação de +0x38 no buffer do SaveBlock1 não foi
  investigada (hipótese: contextos de Quest Log) — só o efeito foi
  medido.

## §19 — Do quarto ao inicial: casa, Pallet, laboratório, batalha (2026-10-20)

**MEDIDO** (`ferramentas/ir_ao_inicial.py`, execução completa do boot em
199 s; evidências `inicial_*.png`):

- Movimento confiável tile a tile: segurar a direção até `pos` mudar
  (segurar 20q anda 2 tiles); bloqueio por NPC resolve esperando.
  Warps têm **atraso** (a escada só troca o mapa no passo seguinte) e a
  **porta da casa só dispara descendo a partir do tapete** — andar na
  horizontal sobre ele não sai.
- Rota validada: escada (10,2) → porta (4,8)→sul → Pallet (6,8) →
  frente das casas até x=11 → (11,2) → (12,2) → gatilho **(12,1)** → o
  Oak escolta ao lab (4,3) → diálogo → bola em (8,4) de (8,5) → apelido
  na tela `0x0809FB71` → gatilhos (5..7,8) → batalha (callback2
  `0x08011101`) → fora do lab em Pallet (16,14). As coordenadas
  coincidem com os `map.json` do pret.
- **O time durante o jogo não está no SaveBlock1**: SB1+0x34 ficou 0 o
  tempo todo, com o menu POKéMON funcionando. O endereço real medido:
  contagem em `0x02024029`, estrutura do 1º Pokémon em `0x02024284`
  (apelido@+8, nível@+84, HP@+86). As bases dos SaveBlocks variaram
  juntas (SB1−SB2 sempre `0xFA4`; SB1 medido entre `02025538` e
  `02025580`).
- Desfecho da batalha com A repetido varia com o RNG: uma execução
  terminou nv5 19/19, a do boot **nv6 22/22** (subiu de nível ⇒ venceu
  essa). Nas duas, o progresso continuou e o time saiu com HP cheio.

**NÃO PROVADO**:

- Quem venceu a 1ª execução da batalha do rival (não registramos o
  desfecho frame a frame).
- Quando os campos SB1+0x34/+0x38 (party no SaveBlock1 do pret) são
  preenchidos — hipótese: ao salvar no cartucho.
- A espécie lida da estrutura (dados de caixa são cifrados; a
  confirmação do Bulbasaur é pela foto da tela do time).
