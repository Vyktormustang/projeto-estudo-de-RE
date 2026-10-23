# Mod da mochila — v4: retorno corrigido + teclas por `REG_KEYINPUT`

> **TL;DR.** O trampolim v3 faz `bx` para **0x08000A42**, mas o prólogo que ele
> substitui termina em **0x08000A3F** — ou seja, **pula uma instrução Thumb a cada
> chamada de `SetGpuReg`**. A v4 corrige o retorno (0x08000A40) e troca a fonte de
> teclas do espelho de IWRAM (`0x03003118`, contexto-dependente) pelo registrador
> de hardware **`REG_KEYINPUT` (0x04000130)**, que é ativo-baixo e sempre válido.
> Tudo validado em emulação de CPU (Unicorn), **sem precisar da ROM**.

---

## 1. O bug do retorno (CONFIRMADO por aritmética + emulação)

O hook v3 é um *veneer* de 8 bytes em `0x08000A38`:

```
08000A38  01 4b        ldr  r3, [pc, #4]      ; PC = A3C, +4 = A40 -> literal em A3C
08000A3A  18 47        bx   r3
08000A3C  01 0c eb 08  .word 0x08EB0C01       ; tramp | Thumb-bit
```

Ele **substitui 8 bytes**: `0x08000A38..0x08000A3F`. O trampolim reexecuta o
prólogo (4 instruções, 8 bytes) e precisa continuar **em 0x08000A40**.

O v3 monta o retorno assim:

```
movs r3, #8 ; lsls r3, #24     -> 0x08000000
movs r2, #0xA4 ; lsls r2, #4   -> 0x00000A40
adds r3, r3, r2                -> 0x08000A40
movs r2, #3 ; adds r3, r3, r2  -> 0x08000A43   <-- +3
bx r3                          -> 0x08000A42   (bx limpa o bit 0)
```

**0x08000A42 ≠ 0x08000A40.** É a assinatura de um endereço calculado para o site
antigo (`0x08000A3A`, quando o veneer acabava em `0x08000A41`) e não atualizado
quando o site passou para `0x08000A38`.

Consequência: toda chamada de `SetGpuReg` (há **mais de 1.200** callsites — veja
`functions.csv`) executa uma instrução a menos. Se a instrução pulada for a que
carrega o índice/valor do registrador de vídeo, o jogo escreve lixo em
`0x04000000+idx` — o que é compatível com as **telas brancas** observadas nos
testes do v3 (`reports/v3_480.png`, `reports/v3_2900.png`).

Prova em emulador (mesmo payload, só o retorno muda):

```
v3 (retorno 0x08000A42): parou_em=0x08000A42 motivo=pulou_1_instrucao
v4 (retorno 0x08000A40): parou_em=0x08000A40 motivo=continuacao_correta
```

---

## 2. A fonte de teclas (HIPÓTESE → correção estrutural)

O v3 lê `0x03003118`, um espelho em IWRAM que **zera em algumas cenas**
(`MEMORIA_CONSOLIDADA.md` §2: "endereço é contexto-dependente; NÃO confiar").

| Fonte | Endereço | Semântica | Depende da cena? |
|---|---|---|---|
| espelho v3 | `0x03003118` | ativo-alto (bit 1 = pressionado) | **sim** |
| `REG_KEYINPUT` | `0x04000130` | **ativo-baixo** (bit 0 = pressionado) | **não** |

`REG_KEYINPUT` é o registrador de hardware do GBA (GBATEK §"Keypad Input"):
os bits 0-9 são as teclas, `0` = pressionada; os bits 10-15 não são usados.
Ler dele é imune a estado de cena, menu ou interrupção.

Máscara usada (mesma convenção de bits do v3): `L=0x0200`, `R=0x0100`,
`START=0x0008` → combo `0x0308`. Como o registrador é ativo-baixo, a condição é

```
(REG_KEYINPUT & 0x0308) == 0        # as três pressionadas
```

---

## 3. O que o script gera

`scripts/gba_bag_payload.py` encoda o Thumb **à mão** (sem montador externo),
valida cada instrução com capstone e emula o resultado:

```bash
python3 scripts/gba_bag_payload.py --build       # reports/bag_v4/*.hex + report.json
python3 scripts/gba_bag_payload.py --emulate     # matriz de cenários (Unicorn)
python3 scripts/gba_bag_payload.py --self-test   # encoders + applier + emulação
python3 scripts/gba_bag_payload.py --apply rom_mod/BAG_MOD_v3.gba -o rom_mod/BAG_MOD_v4.gba \
        --variante regkey
```

| Artefato | Tamanho | Conteúdo |
|---|---|---|
| `site.hex` | 8 B | `ldr r3,[pc,#0] ; bx r3 ; .word 0x08EB0C01` |
| `payload_regkey.hex` | 128 B | gate por `REG_KEYINPUT` + 8 slots |
| `tramp_regkey.hex` | 156 B | `push {r0-r3}` + payload + `pop` + replay + `bx` |
| `payload_sanity.hex` | 30 B | grava `0xAAAA` em id e qty do slot 0, **sem gate** |
| `tramp_sanity.hex` | 58 B | idem + replay + `bx` correto |

### 3.1 Variante `sanity` (teste de "o hook roda nesta cena?")

Esta era a próxima pergunta da lista do projeto. A variante **ignora as teclas**
e grava `id = qty = 0xAAAA` no slot 0. Se a mochila mostrar item `AAAA` depois de
alguns frames, o trampolim **está executando** e o problema é só o gate; se não
mostrar nada, `SetGpuReg` **não é chamado** naquela cena (e o site precisa mudar).

---

## 4. Evidência (emulação, sem ROM)

`python3 scripts/gba_bag_payload.py --emulate` mapeia ROM/EWRAM/IWRAM/IO como no
GBA, escreve `REG_KEYINPUT` com o valor do cenário, roda do site até a
continuação e confere a mochila:

| Variante | `REG_KEYINPUT` | Teclas | Mochila preenchida? | Esperado | Resultado |
|---|---|---|---|---|---|
| regkey | `0x03FF` | nenhuma | não | não | ✅ |
| regkey | `0x00FF` | L+R | não | não | ✅ |
| regkey | `0x03F7` | START | não | não | ✅ |
| regkey | `0x00F7` | **L+R+START** | **sim** | sim | ✅ |
| sanity | `0x03FF` | nenhuma | sim (`AAAA/AAAA`) | sim | ✅ |

Além do conteúdo da mochila, cada caso verifica:

* `PC` final = `0x08000A40` (continuação correta, **não** `0x08000A42`);
* bit **T** do CPSR ligado (permaneceu em Thumb);
* `SP` final = `SP` inicial − 12 (o `push {r4,r5,lr}` do prólogo reexecutado
  ficou na pilha, como no original);
* `push`/`pop` do payload balanceados (`r0-r3` preservados).

`--self-test` fecha com:

```
[self-test] OK  encoders + payload + trampolim + emulação
```

---

## 5. O que **não** está provado (rotulado)

| Afirmação | Nível | Como provar |
|---|---|---|
| O retorno do v3 pula 1 instrução | **CONFIRMADO** | aritmética acima + emulação (`pulou_1_instrucao`) |
| A v4 executa o fill só com L+R+START | **CONFIRMADO (emulação)** | matriz §4 |
| A v4 funciona **no jogo** | **PENDENTE** | aplicar numa cópia da ROM e testar no mGBA (§6) |
| `SetGpuReg` é chamada a cada frame no overworld | **PROVÁVEL** | README/diagrama do projeto; a variante `sanity` responde definitivamente |
| A instrução pulada era a causa das telas brancas | **HIPÓTESE** | comparar frames do v3 × v4 com a ROM na mão |

Nenhuma linha acima usa a ROM: os bytes gerados são código do próprio projeto.

---

## 6. Como testar na sua cópia da ROM

```bash
# 1) aplicar na CÓPIA (a original nunca é tocada)
python3 scripts/gba_bag_payload.py --apply rom/pokemon_firered_bpre_trabalho.gba \
        -o rom_mod/BAG_MOD_v4_sanity.gba --variante sanity

# 2) rodar 3 s no emulador headless e ler a mochila
python3 scripts/gba_libretro_emu.py --rom rom_mod/BAG_MOD_v4_sanity.gba \
        --frames 600 --snap 590=sanity.png --save-state out_sanity.bin
python3 scripts/gba_state_dump.py out_sanity.bin --read 0x020258B8:0x10
#    esperado: aa aa aa aa ...   -> hook executa
#    esperado: 00 00 37 dd ...   -> hook NÃO executa nesta cena

# 3) se o sanity escrever, testar o combo de verdade
python3 scripts/gba_bag_payload.py --apply rom/pokemon_firered_bpre_trabalho.gba \
        -o rom_mod/BAG_MOD_v4.gba --variante regkey
python3 scripts/gba_libretro_emu.py --rom rom_mod/BAG_MOD_v4.gba --frames 900 \
        --input 100:L:250 --input 100:R:250 --input 100:START:250 \
        --snap 890=bag.png --save-state out_v4.bin
python3 scripts/gba_state_dump.py out_v4.bin --read 0x020258B8:0x20
#    esperado: 01 00 63 00 02 00 63 00 04 00 63 00 0d 00 63 00 ...
```

> `--apply` valida antes de escrever: prólogo original em `0x08000A38`
> (`30 b5 00 06 04 0e 09 04`) e destino `0x08EB0C00` todo `0xFF`. Se a ROM for
> outra versão, ele **recusa** em vez de corromper.

---

## 7. Arquivos

| Arquivo | Papel |
|---|---|
| `scripts/gba_bag_payload.py` | encoders Thumb, payloads, trampolim, applier, emulação e testes |
| `reports/bag_v4/*.hex` | bytes prontos para auditoria (gerados por `--build`) |
| `reports/bag_v4/bag_v4_report.json` | tamanhos, SHA-256 e tabela de itens |
| `apply_mod_v3.py` (no pacote do projeto) | applier antigo — **não** corrige o retorno |
