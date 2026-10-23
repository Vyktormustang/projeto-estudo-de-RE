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

## 0.5 Ferramentas de RE (REA + Ghidra) — preparadas em 2026-10-22

- **Instalador:** `bash scripts/setup_re_tools.sh` — REA 6.7.0 (`rea-agents`) +
  Temurin **JDK 21.0.13+9** + **Ghidra 12.1.4** PUBLIC, tudo fora do repo
  (`~/.local/opt/re-tools`), com SHA-256 oficial e modo offline
  (`--ghidra-zip`, `--jdk-tarball`, `--jdk-home`, `--ghidra-dir`).
- **Ambiente:** `source scripts/re_env.sh` (exporta `JAVA_HOME`,
  `GHIDRA_INSTALL_DIR` e `PATH`).
- **Verificação:** `bash scripts/re_tools_check.sh` (exit 0 = pronto) e
  `bash scripts/rea_ghidra_smoke.sh` (imagem ARM **sintética** em `0x08000000`,
  sem a ROM; evidências em `reports/re_tools/`).
- **Guia + estado detalhado:** `docs/REA_GHIDRA.md`; notas: `REA.md`.
- **Estado no sandbox de preparação:** REA e Ghidra **OK** (doctor aprova
  versão/headless/decompilador nativo); **JDK 21 ausente** → o REA responde
  `provider_ghidra_available=false` com `runtime_missing`. Motivo: a CDN de
  assets do GitHub está bloqueada nesse sandbox. O smoke test só fecha depois de
  rodar o setup numa máquina com internet normal (ou `--jdk-home`).
- **Consequência para o roadmap:** a Fase 2 (Ghidra) segue bloqueada **apenas**
  por esse JDK; Ghidra e integração já estão instalados e validados.

### 0.6 Importador da ROM no Ghidra (EXECUTADO: motor pyghidra, sem JDK)

- **Comando único:** `bash scripts/ghidra_import_gba.sh rom/sua_rom.gba`
  (guia: `docs/GHIDRA_IMPORT.md`).
- Importa com `-processor ARM:LE:32:v4t` (ARMv4T, o certo para GBA; a lane raw
  do REA usa `ARM:LE:32:v7` fixo e não alterna para Thumb), `BinaryLoader` em
  `0x08000000`.
- Pré-script `scripts/ghidra_scripts/GbaPrepareProgram.java` cria EWRAM/IWRAM/IO/
  PALETTE/VRAM/OAM, valida o cabeçalho do cartucho, cria rótulos
  (`gBagSlots_slot0` em `0x020258B8`, `SetGpuReg` em `0x08000A38`, `REG_KEYINPUT`
  em `0x04000130`, `gKeysMirror_HIPOTESE` em `0x03003118`) e semeia entrada
  ARM (CONFIRMADO) + Thumb (HIPÓTESE via `ldr` literal).
- Pós-script grava `reports/ghidra/gba_prepare_{pre,post}.json`; o orquestrador
  faz **cross-check** do cabeçalho entre `scripts/gba_rom_header.py` (Python) e
  o Ghidra (11 campos + checagem de `v4t`).
- **Teste sem a ROM:** `bash scripts/ghidra_import_gba.sh --self-test` gerou uma
  ROM sintética de 32 KB com cabeçalho válido e roda o pipeline inteiro.
- **Status CONFIRMADO (2026-10-22):** o pipeline foi **executado de verdade**
  nesta máquina sobre a ROM sintética de 32 KB, pelo motor `pyghidra`
  (`scripts/ghidra_prepare_pyghidra.py`), com Java 25 **somente runtime**:
  import ARMv4T ✔, 6 blocos de memória ✔, 16 rótulos ✔, seed ARM + Thumb ✔,
  auto-análise ✔, **descompilação** ✔ (gerou C de `gba_entry_arm`) e
  cross-check Python×Ghidra em 11 campos ✔. `--self-test` → `TUDO OK`.
- **Sem JDK:** o motor `--engine pyghidra` usa a API oficial PyGhidra e pula o
  `LaunchSupport -jdk_home` (que é o que exige `javac`). Basta
  `python3 -m pip install pyghidra` + um Java 21+ runtime. O motor `--engine java`
  (script `.java` via `analyzeHeadless`) segue exigindo JDK e ainda **não** foi
  executado aqui.

## 1. O que NÃO refazer (causas-raiz já provadas)
- **BL Thumb alcança só ±4 MB.** Hookar `0x08000B08 → 0x08EB0C00` (~15,4 MB) é
  impossível por BL e trava a tela de copyright. Resolvido por **veneer** em
  `0x08000A38` (`01 4b 18 47 01 0c eb 08`). Não tente BL distante de novo.
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

### 0.7 Windows (quando `bash` não existe)

- Guia: `docs/WINDOWS.md`. Três caminhos: GUI do Ghidra (mais simples),
  `scripts/win/setup_re_tools.ps1` + `scripts/win/ghidra_import_gba.ps1`
  (automação) e WSL (fluxo completo).
- **Limite do Windows nativo:** o provider Ghidra do REA é P0 somente-leitura e
  **recusa `raw-binary`** → REA→Ghidra **não funciona** para GBA ali. Ghidra
  sozinho funciona. Para os dois juntos: WSL.
- Os `.ps1` foram escritos/revisados mas **não executados** no ambiente Linux de
  desenvolvimento; a validação de cabeçalho chama o `gba_rom_header.py`
  (testado com `--self-test`) e há fallback em PowerShell puro.

### 0.8 Mod da mochila v4 — **VALIDADO NO JOGO** (2026-10-22)

- **Causa-raiz encontrada (CONFIRMADO):** o veneer em `0x08000A38` cobre
  `A38..A3F`; a continuação é **`0x08000A40`**, mas o trampolim v3 fazia `bx`
  para **`0x08000A42`** (resíduo do site antigo `0x08000A3A`) — pulava **uma
  instrução Thumb** a cada chamada de `SetGpuReg` (1.200+ callsites). É a
  explicação das telas brancas do v3.
- **Segunda correção:** gate por **`REG_KEYINPUT` (0x04000130)** ativo-baixo,
  em vez do espelho `0x03003118` (contexto-dependente).
- **Ferramenta:** `scripts/gba_bag_payload.py` (`--build`, `--emulate`,
  `--self-test`, `--apply ROM -o SAIDA --variante regkey|sanity`).
- **Evidência na ROM real** (save-state Viridian, mGBA 0.10.5 compilado do fonte):
  - sanity (`AAAA` sem gate) → `aa aa aa aa` no slot 0 ⇒ **hook executa**;
  - **L+R+START** → `01 00 63 00 02 00 63 00 …` ⇒ **mochila cheia**;
  - **START+SELECT** → idem (combo recomendado: L+R abre a ajuda nativa);
  - sem nada / L+R só / START só → mochila intacta (controles negativos).
  - Print da tela ITENS: `reports/mod_v4/BAG_CHEIA_contraste.png`
    (MASTER BOLA, ULTRA BOLA, POKÉ BOLA, POÇÃO, LIMONADA, CINZA SAGRADA).
- **Detalhes:** `docs/MOD_BAG_V4.md`. Nota: o core mGBA do zip exige glibc 2.38
  e falha na Debian 12 (glibc 2.36); compilar o mGBA 0.10.5 do fonte resolve
  (cmake + ninja, `-DBUILD_LIBRETRO=ON -DUSE_ZLIB=OFF ...`).

## 3. Cheatsheet técnico (números já provados)
- SetGpuReg @ `0x08000A38`; site overwrite = 8 B: `01 4b 18 47 | .word TRAMP+1`.
- Tramp @ `0x08EB0C00` (run 0xFF, ver `reports/freespace_map.tsv`), 158 B builder-
  revisado; salva/restore `{r0-r3}`, replay do prólogo, retorno `bx` pra `0x08000A43`
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
