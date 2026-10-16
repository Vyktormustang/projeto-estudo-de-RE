> **ATENÇÃO (ciclo 35, 2026-10-16):** leia primeiro `RETOMADA.md`. Os valores de veneer e de retorno abaixo foram corrigidos; o restante do histórico está correto como registro.

# HANDOFF — Continue daqui (qualquer agente)

> Se você está pegando este projeto do zero, leia na ordem:
> **1) este arquivo → 2) `MEMORIA_CONSOLIDADA.md` → 3) `progress.md` (log por ciclo).**
> A ROM comercial NÃO está aqui: coloque uma cópia de Pokémon FireRed (mesma família
> PT-BR modificada descrita em `inventory.json`) em `rom/` antes de reproduzir.

---

## 0. Estado resumido (1 parágrafo)
Fases 0–6 rodadas: ROM identificada/censada, callgraph, decoder de texto, driver
headless mGBA, mochila mapeada (slot 0 @ `0x020258B8`, `{id:u16,qty:u16}`, 4 B/slot).
Objetivo atual: **mod menu = combo de botões preenche a mochila**. Hook v3 montado
(`rom_mod/BAG_MOD_v3.gba`) e estável no jogo, mas o **combo ainda não dispara** — o
bug aberto é onde ler as teclas naquele contexto tela (ou mudar a rotina-trampo).

## 1. O que NÃO refazer (causas-raiz já provadas)
- **BL Thumb alcança só ±4 MB.** Hookar `0x08000B08 → 0x08EB0C00` (~15,4 MB) é
  impossível por BL e trava a tela de copyright. Resolvido por **veneer** em
  `0x08000A38` (`00 4b 18 47 01 0c eb 08` (corrigido c35)). Não tente BL distante de novo.
- `scripts/gba_disasm.py::encode_bl_thumb` e `gba_hook_code.py` têm **bug de sinal**
  em bls negativos (bit-S nunca ligado). Trata qualquer trampo gerado por eles como
  suspeito. Patch a pendência mais valiosa do repo.
- Espelho de teclas `0x03003118` é **contexto-dependente** (zera na cena-bedroom —
  bug aberto). Não confiar sem validar no contexto.
- Artefatos `_DBG_pal.gba`, `_EMPTYPS.gba`, `BAG_MOD_cheat.gba`,
  `HOOK_VALIDADO_paleta_OK.gba` foram gerados pelo encoder bugado: descarte-os
  como evidência.

## 2. Próximos passos, em ordem, com comandos
0. `bash scripts/setup_env.sh` (python-capstone; já funciona aqui).
1. **Diagnosticar gating do combo (ciclo atual).**
   a. Rodar state_bedroom com um **payload sempre-escreve** (`str 0xAAAA` em
      `0x020258B8` sem checar teclas) → se **não** escrever : a rotina SetGpuReg não
      roda naquela tela → trocar rotina-trampo (candidatas: função per-frame do vblank
      / ReadKeys). Se **escrever**: gating é só o espelho de teclas.
      ```
      python3 scripts/gba_libretro_emu.py --rom rom_mod/<debug>.gba \
        --load-state emu/state_v3st1.bin --frames 900 --save-state out.bin
      python3 scripts/gba_state_dump.py out.bin --read 0x020258B8:0x04
      ```
   b. Fonte robusta de teclas: ler `0x04000130` (REG_KEYINPUT, ativo-baixo) == XOR;
      ou achar o "keys mirror" universal via diff-sweep com state durante hold.
2. **Unidades do mod**: combo final = L+R+START (`0x0308` ativo-alto) com nota de
   colisão L+R=help (documentado). Alternativa documentada: START+SELECT.
3. **Validação de aceitação** (só então chamar de "concluído"):
   boot → logo GAME FREAK → Nidorino → overworld com state → combo →
   botão START abre menu → **screenshot da mochila cheia** → estável ≥ 60 s.
4. Regenerar o mod quando precisar: `python3 scripts/apply_mod_v3.py` (montador
   one-shot, asserts de pré-condição inclusos, sha256 reportado; fonte de bytes:
   `reports/site_v3.hex` + `reports/tramp_v3.hex`). ROM modificada sha256 esperada:
   `348025c1...2215a3`.

## 3. Cheatsheet técnico (números já provados)
- SetGpuReg @ `0x08000A38`; site overwrite = 8 B: `00 4b 18 47 | .word TRAMP+1` (corrigido c35).
- Tramp @ `0x08EB0C00` (run 0xFF, ver `reports/freespace_map.tsv`), 158 B builder-
  revisado; salva/restore `{r0-r3}`, replay do prólogo, retorno `bx` pra 0x08000A41 (corrigido c35; o valor antigo pulava lsrs)
  (bit0=1 mantém Thumb).
- BL certo (replicado contra 6.000 BLs reais, ≡ capstone): S-bit + campo 23-bit
  H10:L11 — fórmula em `MEMORIA_CONSOLIDADA.md` §5.
- Save-state mGBA: IWRAM blob @ `0x19000`, EWRAM @ `0x21000`; slot-0 de bolsa no blob
  @ `0x468B8` (== VA `0x020258B8`).
- Emulador: `scripts/gba_libretro_emu.py` (input: `--input F:BTN:HOLD`; snaps md5 =
  detector de tela travada).
- Original ROM baseline: GAME FREAK logo @ ~480 f; Nidorino @ ~1380 f (timing-check).

## 4. Regras de convivência
- FATO/HIPÓTESE rotulados; nunca claim sem evidência; ROM/jogo nunca entra em git
  (`.gitignore` já pronto).
- Relatório enxuto por ciclo + ETA em toda resposta do agente.
