# MEMÓRIA CONSOLIDADA — gba-re (ciclo 34)

> Leia isto primeiro em sessões futuras. Regras do briefing do usuário permanecem ativas:
> ROM original intocável (trabalhar só em cópias); nunca redistribuir ROM; separar
> CONFIRMADO/PROVÁVEL/HIPÓTESE; ETAs em toda resposta; relatório enxuto.

---

## 1. MISSÃO ATUAL (pós-c24)
Mod = **"mod menu" (cheat) para pegar Pokéballs, Potions, itens e tudo mais**:
hook no jogo + combo de botões → preencher a mochila. Validar visualmente em emulador.
Nota de colisão: L+R abre a ajuda nativa do jogo — combo escolhido L+R+START convive com isso
(documentar); alternativa START+SELECT se virar problema.

## 2. RESULTADOS DURAIS (provados)
- **BOLSA (CONFIRMADO)**: array @ **0x020258B8**, 4 B/slot `{id:u16 LE, qty:u16 LE}`;
  vazio = `00 00 37 dd` (fill DMA). UI cacheia na abertura → patch/dump no overworld.
  Offset no save-state mGBA = **0x468B8**.
- **Item-teste provado (c33)**: poção id=1 qty=99 exibida na BAG após escritas via hook?
  (ver §3 status v3) — registros c32: formato clássico {id@+0, qty@+2} CORRIGIDO.
- **Input espelho (empírico 0x03003118 inválido em alguns contextos)**:
  bits ativos-alto L=0x0200 R=0x0100 START=0x0008 → combo 0x0308. **0x03003118 zera
  no overworld de bedroom v3st1 — endereço é contexto-dependente; NÃO confiar.**
- **Thumb BL ±4MB!** — queda definitiva: site→tramp distante é IMPOSSÍVEL com BL;
  a faixa ±4 MB ao redor de 0x08000B08 não tem freespace ≥256 B (freespace_map.tsv).
  Solução pra frete distante = **veneer ldr-pc+bx** (byte-eb0c00 literal).
- **Encoder/decoder BL reescritos (c33) e homologados vs 6000 BLs reais** (≡capstone,
  re-encode byte-idêntico). Fórmula (23-bit S:H10:L11) permanece nos regs (§5).
- **SetGpuReg** @ **0x08000A38** = rotina tiny chamada a partir de 0x08000B08 etc;
  primeiros 8 bytes = `30 b5 00 06 04 0e 09 04` (push{r4,r5,lr}, lsls, lsrs, lsls —
  relocável, sem pc-relative).
- **v3 state não-responde a START solo** em bedroom state_v3st1 (e state_bt7 c/ start
  sozinho tbm falhou no c34-repro; antes funcionava). **Estado "congelável"/input-mudo
  — investigar (BUG no state??).** Combo+seq A,A,B,START gera md5 diferente (reação).
- Emulador: `--input f:BOTÃO:hold` multi-janela; snaps md5 = detector de tela travada.

## 3. ESTADO DO MOD (c33→c34)
- **`rom_mod/BAG_MOD_v2.gba` (BL-fix manual)**: TRAVA na tela ©2004 (@480→@2550 md5 igual).
  Causa-raiz: site 0x08000B08→tramp 0x08EB0C00 = ~15,4MB → FORA do alcance BL ±4MB.
  O "back-bl certo" de c33 não existia de fato — contas validaram campo, não alcance.
- **`rom_mod/BAG_MOD_v3.gba` (design veneer)**: site em **0x08000A38** (prologo SetGpuReg):
  `00 4b 18 47 01 0c eb 08` = ldr r3,[pc,#0]; bx r3; .word 0x08EB0C01 (corrigido c35: `01 4b` lia literal em 0xA40 = código).
  Tramp @ 0x08EB0C00 (158 B): push{r0-r3} + payload(130 B) + pop + replay 4 instr +
  retorno bx-stay-Thumb → **0x08000A41** (corrigido c35; o valor 0x08000A42/A43 original estava ERRADO e pulava `lsrs r1,r1,#0x10`@0xA40). Header: `reports/site_v3.hex`,
  `reports/tramp_v3.hex`. **STATUS: boot OK BRANCO (?! frames iguais 480/2900 AMBOS
  de tela branca — provável pré-GBI 'fade to white' do boot? Deletado: precisa validar
  o conteúdo das imagens, pois 4-byte-white pode ser boot legítimo)**. Testes no
  jogo: overworld estável; combo L+R+START **NÃO preencheu bolsa** (slot00 intacto);
  START solo no state_v3st1 não abre menu (state-input-mudo??? — mesmo md5 em 3 runs).
- **Última pista c34**: `reports/c_seq.png md5 6e7db1...` ≠ c_v3_bt7 — sequência A,A,B,START
  reage no jogo: **input funciona; o problema é o TRAMP gating (combinação/espelho errado).
- Próximo passo isolador: **payload DEBUG com tramp capaz de gravar 0xAAAA em slot-0**
  quando vê QUALQUER flag (ou sempre) — se nem sempre-escreve → trap nunca roda nessa cena
  (SetGpuReg não é chamada em bedroom overworld!). Re-testar com a rotina per-frame certa.

## 4. ENCOLHEDORES DEFINITIVOS DE NÃO-USO-BL (restrições reais)
- **RESOLVIDO (c35, FATO)**: encode_bl_thumb (gba_disasm.py; gba_hook_code.py importa
  dele) está CORRETO e homologado — 88.782 callsites reais re-encodados → capstone:
  0 divergências nos 51.041 pares dentro da faixa; os 37.741 fora de ±4 MB são
  REJEITADOS com ValueError (patch c35: guarda de faixa/alinhamento; o wrap
  silencioso em exatamente +0x400000 gerava 1.579 falsos "válidos"). Base do PC =
  site+4 **não alinhada** (hipótese Align(site+4,4) TESTADA e DESCARTADA c35:
  piorava 26.118 pares). Self-test 14/14 cobre bordas de faixa.
- `_DBG_pal.gba`, `_EMPTYPS.gba`, `BAG_MOD_cheat.gba`, `HOOK_VALIDADO_paleta_OK.gba` = **artefatos
  gerados pelo encode errado → descartá-los como evidência mecânica** (só histórico).

## 5. FÓRMULAS & BYTES DURAIS
- **Thumb BL (certo)**: enc: S=1 se off<0; raw23=off&0x7FFFFF; w0=F000|(S<<10)|H; w1=F800|L
  (H=(raw23>>12)&3FF, L=(raw23>>1)&7FF). dec espelha. Off>±0x400000 → FORA DE ALCANCE.
- Site v3: bytes `00 4b 18 47 01 0c eb 08` @0x08000A38 (c35). Tramp jump-back: bx sobre
  **0x08000A41** (0xA40|1 = thumb-bit). Literal do veneer em 0x08000A3C = 0x08EB0C01.
- Push/pop const-range certos: `0xB40F` push{r0-r3} / `0xBC0F` pop{r0-r3} (AUDITADOS c34 —
  anteriores 0xB0/0xB8-famílias misturadas no c33 histórico; versão c34 no tramp_v3 e
  dump capstone 1:1).

## 6. AMBIENTE
- Linux sandbox (briefing disse Windows; artifacts multiplataforma). mGBA ctypes-core
  OK (input-polling + libretro-IDs padrão funcionam — ver c34 prova A,A,B,START).
- State IWRAM 0x19000-0x20FFF; EWRAM 0x21000-0x60FFF; IO arquivado em dominio separado(?)
  — REG_KEYINPUT 0x04000130 ativo-baixo NÃO aparece nas diffs de blob checado (mid-hold).

## 7. LOG DE EXECUÇÃO RECENTE (não refazer)
- c35 (2026-10-15): encoder homologado 88k + guarda de faixa (§4 RESOLVIDO); core
  mGBA 0.10.5 RECONSTRUÍDO do fonte (glibc 2.38 do .deb Ubuntu quebrava no
  Debian 12; novo `emu/.../mgba_libretro.so` build local — self-test 5/5);
  trampos de diagnóstico montados+auditados (`reports/tramp_always.hex`,
  `reports/tramp_regkey.hex` + `scripts/apply_mod_dbg.py`) — 3 bugs de
  hand-assembly pegos pela auditoria capstone (muls≠mvns; bne pulava o pop;
  strh≠str). Pendente: ROM para aplicar/validar.
- 205-213 (c33): encoder fix + v2; 214-223 (c34): freespace-busca ±4MB (), SetGpuReg site-veneer,
  v3 build+boot+state+sem-fill; INVESTIGAÇÃO combo-zero (2 diffs cruzados errados → corrigido
  mesma-rom → AINDA zerado IWRAM/EWRAM??); START solo não abre (state-input-mudo?!);
  seq A,A,B,START muda md5 ✓;
- RESTA VALIDAR as PNGs v3_480/v3_2900 (brancas — boot ≠ boot?): procurar primeiro frame
  com texto real vs branco puro.
