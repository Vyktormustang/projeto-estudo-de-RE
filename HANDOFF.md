# HANDOFF — continue daqui (qualquer agente)

> Ordem de leitura: **1) este arquivo → 2) `MEMORIA_CONSOLIDADA.md` →
> 3) `progress.md`** (log por ciclo).
> A ROM comercial NÃO está aqui: coloque uma cópia em `rom/` (ou aponte com
> `--rom`) antes de reproduzir a validação final.

---

> ⚠ **ATUALIZAÇÃO 2026-11-07 (fim do ciclo): o mod FOI validado na ROM real do
> usuário** — que é outra base (`pokefirered_gen1-9_ptbr.gba`, sha256 `e96d1a53…`),
> não a de `inventory.json`. Resumo do que mudou:
> - site do hook **descoberto automaticamente** nesta base: `0x08095F88`
>   (1 chamada por frame, vive em overworld **e** com o menu aberto);
> - mochila: pocket em `0x0202B718` → `{ItemSlot* slots; u8 cap}` → slots em
>   `0x0202D31C` (items, cap 42) — o payload agora **lê o ponteiro em runtime**;
> - **L+R+START não serve nesta base**: L+R abre a ajuda nativa e o site deixa de
>   rodar. O combo que funciona é **START+SELECT**;
> - evidência: `reports/ptbr_bolsa_cheia_prova.png` (ITENS — MASTER BALL ×?14,
>   ULTRA BALL, GREAT BALL, POKé BALL, POTION, FULL RESTORE…).

## 0. Estado resumido (1 parágrafo)

O mod está **mecanicamente pronto e provado em emulador**. O motivo de o v3 não
disparar **não era o combo de teclas**: era o `ldr` do veneer apontando 4 bytes
adiante do literal (`bx` para lixo em 1238 callsites de `SetGpuReg`) — mais o
keypad ser ativo-baixo. O toolkit agora monta o mod a partir de mnemônicos,
**simula** antes de gravar e o emulador é próprio (libmgba compilada aqui),
com CPU, memória e breakpoints. Falta **uma** coisa: rodar na ROM do usuário e
tirar o print da mochila cheia.

## 1. Números que agora são FATO (não repita a investigação)

- Site `0x08000A38` = prólogo de `SetGpuReg` (`30 b5 00 06 04 0e 09 04`),
  **1238 callsites** (`reports/..._callsites.tsv`).
- Veneer correto **8 B**: `00 4b | 18 47 | 01 0c eb 08`
  — `ldr r3,[pc,#0]` lê `Align(0x08000A3C,4)+0 = 0x08000A3C`.
  ⚠ O v3 usava `#4` (lê `0x08000A40`) com o literal em `0x08000A3C` → **lixo**.
- `REG_KEYINPUT` `0x04000130` = **ativo-baixo** (solto = `0x3FF`).
  Combo L+R+START = `0x308`. Teste correto: `(k & 0x308) == 0`.
- Mochila `0x020258B8`, slot `{id:u16, qty:u16}` → escrever como **um** `u32`
  `(qty<<16)|id` (duas stores deixam estado meio-escrito visível).
- Trampolim `0x08EB0C00` é run 0xFF e cabe numa ROM de 16 MiB (`0xEB0C00`),
  **não** numa de 8 MiB → `apply_mod.py` checa e recusa/estica.
- Save-state mGBA: **0x61000 B**; IWRAM @ `0x19000`, EWRAM @ `0x21000`;
  mochila no blob @ `0x21000 + 0x258B8 = 0x468B8`.
- ARM7TDMI **não tem Thumb-2**: `adds rX, rY` monta 32 bits e vira lixo —
  usar `add rX, rY`. O montador (`gba_modkit.montar`) recusa 4 B fora de BL.

## 2. Próximos passos, em ordem

0. Ambiente (uma vez por sessão):
   ```bash
   bash scripts/setup_env.sh
   make -C tools/gba_shim -j$(nproc)      # ~2 min; gera build/gba_shim.so (1,3 MB)
   bash scripts/run_all_tests.sh          # 14 verificações, todas devem passar
   ```
1. **Validação no FireRed** (única pendência real):
   ```bash
   python3 scripts/apply_mod.py --rom rom/<sua_copia>.gba -o rom_mod/MOD_BAG.gba
   # confira no relatório: sha256, site, trampolim e a simulação (off/on)
   ```
   No emulador: chegar ao overworld, segurar **L+R+START** por ~2 s (o hook roda
   milhares de vezes por quadro — não precisa de timing), abrir o menu START →
   MOCHILA → screenshot. Se o combo colidir com a ajuda nativa do jogo, refaça
   com `--combo START+SELECT`.
   Se a mochila não mudar: rode `python3 scripts/gba_emu.py --rom rom_mod/MOD_BAG.gba
   --load-state <state do overworld> --input 10:L:90 --input 10:R:90 --input 10:START:90
   --read 0x020258B8:32` e compare. (A ROM continua em `0x020258B8`? O save-state
   é de uma versão da ROM sem o mod? Anote o que mudou.)
2. **Se precisar mexer no payload**: edite `gba_modkit.PADRAO` (lista de
   `(id, qtd)`); `--payload tudo` injeta os 8 primeiros da tabela Gen 3.
3. **Regenerar a prova de bancada** (não precisa de ROM comercial):
   ```bash
   python3 tests/fixtures/make_bench_rom.py     # ROM própria, 0 conteúdo de jogo
   python3 tests/teste_mod_bench.py             # 10 checks no mGBA real
   ```
4. **Escopo maior (opcional)**: menu in-game de escolha de itens. Exige achar o
   handler do menu de mochila e uma tabela de itens; hoje o mod só preenche os
   slots. Não comece sem a validação do passo 1.

## 3. Ferramentas (o que usar em vez do quê)

| Preciso de… | Use | NÃO use |
|---|---|---|
| rodar a ROM | `scripts/gba_emu.py` | `deprecated/gba_libretro_emu.py` (GLIBC 2.38) |
| montar/alterar o mod | `scripts/gba_modkit.py` | hex na mão, `apply_mod_v3.py` (apagado) |
| aplicar na ROM | `scripts/apply_mod.py` | — |
| ler o save-state | `scripts/gba_state_dump.py` | — |
| ler memória AO VIVO | `Emu.read/write` (`gba_emu.py`) | `retro_get_memory_data` (não publica) |
| teclas | `Emu.keys_held()` / `REG_KEYINPUT` | o espelho `0x03003118` (contexto-dependente) |

## 4. Regras de convivência

- FATO/HIPÓTESE rotulados; nunca claim sem evidência; ROM/jogo nunca entra em git
  (`.gitignore` já pronto, com exceção só para `tests/fixtures/*.gba`, que é ROM
  de bancada **nossa**).
- Relatório enxuto por ciclo + ETA em toda resposta do agente.
