# notes_mods_codigo.md — Infraestrutura de mods de CÓDIGO (desenho Ciclo 15)

> Estado: **DESENHO validado estaticamente** — execução aplicada fica BLOQUEADA
> até mGBA (regra do projeto: nenhum hook "no escuro"). mGBA existe no apt do
> sandbox como `libretro-mgba` / `libmgba0.10t64` (pacote "mgba" não existe).

## 1. Mapa de espaço livre (`reports/freespace_map.tsv`, 171 runs ≥256 B)

- **Grande reserva in-file:** `0xEB0B20 + 1.373.408 B` de 0xFF (até ~0xFF BFFF)
  — a região "após o conteúdo útil" (cont. útil ≈ 0xEB0B20, coerente com Fase 1).
  → **corpo dos trampolins fica aqui** (sem alterar tamanho do arquivo).
- 5.242.425 B de 0xFF partindo de 0x8001C7 — região de dados expandida da tradução
  (NÃO é código; usar com cautela apenas para dados).
- Runs 0x00 (≥256 B): prováveis buffers/embeddings também presentes.

## 2. Modelo de hook (Thumb, BL-site)

Objetivo: substituir a chamada `bl #ALVO` em `site` pela chamada ao trampolim
`bl #TRAMP`, preservando todo o resto.

- BL Thumb = 4 bytes (hi `F000|immhi`; lo `F800|immlo`), encodável por
  `gba_disasm.encode_bl_thumb(site_va, tramp_va)` — já validada por self-test.
- Offset máximo ±16 MiB — cobre qualquer site → região 0xEB0B20+ ✓.

**Seqüência do trampolim no espaço livre (bytes Thumb):**
```
0xB468      push {r3, r4, r5, lr}     ; salvos (regs que o novo código pode usar)
<novo código aqui, usando r3-r5 ou stack>
0xBC30      pop  {r4, r5}
0xB501      push {r0, lr}             ; exec instrução original de sites?
...
BL de retorno p/ site+4
```
A forma concreta varia com a intenção: (a) hook "antes" (hum nos args),
(b) "depois" (pós `bl` com r0), (c) "substituição" (não volta). Ferramenta deve
oferecer os 3 modos.

## 3. Validações obrigatórias da ferramenta (spec p/ `gba_hook_code.py`)

1. `--expect-bytes`: ler os 4 bytes atuais do site (comparar EXATO antes de escrever).
2. `is_bl(site)` por capstone detail (não aceitar outra instrução) **e** alvo resolvido.
3. Trampolim cai sempre em run ≥ N B de 0xFF (de `freespace_map.tsv`; preencher
   somente dentro da run, sem overlap com residências anteriores — registrar
   "ocupação" em `logs/hook_occupancy.jsonl` para apps múltiplas).
4. Saída em cópia (mesma regra do gba_patch_text), relatório SHA-256 in/out e
   hexdump do site e do trampolim.
5. Desassembly final do trampolim impresso (verificável a olho).
6. **Corte duro de validação:** primeiro hook só é considerado funcional após
   boot + teste no emulador (mGBA). Ferramenta emite checklist de verificação.

## 4. Caminho de validação dinâmica (quando mGBA estiver disponível)

1. Hook de demonstração: site trivial em HUD/rotina repetitiva (alvo já
   conhecido por registry, ex.: SetGpuReg_like ×1238) incrementando um contador
   em 0x03008000 (RAM trabalho);
2. mGBA headless: watchpoint em 0x03008000 → arquivo de trace + esperado;
3. Se contador progride com FPS estável → trilha validada; senão: rollback
   automático (cópia anterior intacta) + revisão.

## 5. Pré-requisitos sendo cumpridos antes do spike

- [x] Mapa de espaço livre;
- [x] encoder BL;
- [ ] ferramenta gba_hook_code.py com as 6 validações;
- [ ] mGBA (pacote: libretro-mgba | retroarch | lib mgba + runner próprio).


## 6. Validação dinâmica — APRENDIZADO empírico (Ciclo 18)

- `gba_hook_code.py --payload-contador 0xADDR` (layout fixo 20 B, self-test 7/7).
- **FALSO NEGATIVO conhecido:** escrever em 0x0E000000 (save flash) NÃO aparece
  no region 0 do driver — a emulação de flash intercepta a escrita. Não usar
  save-payload p/ observação.
- **Canal observável que FUNCIONA:** paleta 0x05000000 — contador incrementado
  nesse byte corrige o frame (tela branca em segundos de chamadas recorrentes).
- Driver: restype obrigatório p/ retro_get_memory_data/size (ctypes truncaria
  o ponteiro 64-bit → segfault previsível — lição permanente).
- Status: **hooks de código FORMALMENTE funcionais** (aplicados com guardas +
  validados em emulação).


## 7. Observabilidade dinâmica — rotas testadas (Ciclo 22)

- `retro_get_memory_data/size`: só region 0 (SAVE 128 KiB) exposta. EWRAM,
  IWRAM, IO e paletas somente acessíveis indiretamente (vídeo/golpes via hook).
- SET_MEMORY_MAPS: o core não publica descritores (0 entradas) nesta build.
- **Alternativa proposta (não implementada):** "payload-sampler" — hook
  instrumentado copia N bytes da EWRAM p/ slots de paleta reservados e o
  host extrai do PNG. Alto custo; mantido ideia para futuras fases.
- Conclusão: validação dinâmica nesta plataforma abrange tela, SAVE e
  hooks visíveis — suficiente para os marcos fechados nos ciclos 17–21.


## 8. Subprojeto MOD MENU (combo-cheats in-ROM) — base técnica

- **Observabilidade total alcançada via save-state** (`scripts/gba_state_dump.py`):
  IWRAM no blob @0x19000 (32 KiB), EWRAM @0x21000 (256 KiB), SAVE @0x61000
  (128 KiB). Ground-truth: célula 0x03007FFC bate handler IRQ 0x08000248;
  pool 0x03005090 expõe ponteiros de código (ex.: slot0→0x0812F0B1).
- **Espelhos de input (empírico A/B):** RIGHT⇒0x03003118=0x0300311C=0x010
  → candidates held/new keys gMain-like; hook de combo lerá 0x03003118.
- Plano do mod: hook no vblank/per-frame → lê combo (L+R+A) → escreve slots
  da bolsa/party em EWRAM → valida abrindo mochila (screenshot) → persiste
  como rom_mod. Localização empírica da bolsa/party: diffs de states
  (antes/depois do starter) + offsets BPRE como referência cruzada.
- ESCOPO honesto: combo-cheat validável (bolsa/potions/balls) primeiro;
  "menu gráfico" UI-like só como fase posterior (muito maior).
