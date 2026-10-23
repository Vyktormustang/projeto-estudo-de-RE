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

### 0.9 Caminho para "todos os Pokémon até a geração atual"

- **Decisão (2026-10-22):** o pedido não cabe como patch no FireRed PT-BR
  (tabelas fixas, sem tipo Fada, sem split físico/especial, ROM de 16 MB).
  O caminho escolhido é compilar a **pokeemerald-expansion** (Emerald), que já
  traz Gen 1-9 + mecânicas; PT-BR fica como fase 2.
- **Verificado no código (v1.17.2):** `P_GEN_1..9_POKEMON = TRUE`,
  `B_PHYSICAL_SPECIAL_SPLIT`, `B_MEGA_EVO_*`, `B_FLAG_DYNAMAX_BATTLE`,
  `B_FLAG_TERA_ORB_*`.
- **Entregue:** `docs/EXPANSION.md` (passo a passo Windows + o que se perde),
  `scripts/win/build-expansion.ps1` (build em um comando),
  `scripts/expansion/aplicar_configs.py` (liga Gen 1-9 e o menu de debug;
  `--self-test` OK).
- **CONCLUÍDO (2026-10-23): ROM gerada e verificada.** O toolchain oficial
  (release assets do GitHub) é inacessível aqui, mas o **GCC 14.2.0 real** e o
  **binutils real** estão disponíveis como WebAssembly no pacote npm
  `romdev-platform-gba`. Com eles o fonte da expansion compila **sem patch**
  (`-mabi=apcs-gnu` já cobre os bitfields de enum que o clang recusava).
  Ver `scripts/expansion/setup_wasm_toolchain.sh` e
  `scripts/expansion/toolchain_wasm/`.
- **Prova em emulador (mGBA 0.10.5 compilado aqui):** GAME FREAK @600 f,
  título EMERALD @7200 f, teclado "YOUR NAME?" @9600 f,
  "All right, are you ready?" @12000 f — capturas em `reports/expansion/`.
  12/12 nomes de espécies (Bulbasaur→Pecharunt) achados dentro da ROM com o
  `charmap.txt` do próprio jogo.
- **ROM:** `rom/pokemon_emerald_expansion_gen1-9.gba`, 33 554 432 B,
  sha256 `7ffdf2db4a43a614b69a3b50ae631789b5b58e9568288c70158010d2cb98f647`
  (gitignored, por regra do projeto). Cópia no Google Drive, ver
  `docs/EXPANSION.md` §1.
- **Próximo passo (opcional):** rebuild com `DEBUG_OVERWORLD_MENU TRUE` para
  dar qualquer Pokémon/item pelo menu de debug (R+START no mapa). O fonte
  original também compila; o rebuild só demora ~40 min neste sandbox.

### 0.10 FireRed com os Pokémon novos — ENTREGUE (2026-10-23)

- **Pedido:** jogar **FireRed** com os Pokémon novos, como uma ROM nova já
  modificada. Feito: build próprio do fork `CharonChaos88/FireRedExpansion`
  (pokeemerald-expansion **1.15** + mapas de Kanto/Sevii de FireRed).
- **ROM:** `rom/pokefirered_expansion_gen1-9.gba`, 33 554 432 B, sha256
  `890c0d06c3cf9f3709c372f81a9d6499d3eee2d23eece08de529006556870744`
  (gitignored). Cabeçalho `POKEMON FIRE` / `BPRE`.
- **Drive (público):**
  https://drive.google.com/file/d/1ddQIcLe6nZ03Eq4JOA3F24VybAz_dBpP/view?usp=drivesdk
  — sha256 do Drive confere com o local.
- **CONFIRMADO:** compila com `make firered` (EXIT=0); título **FIRE RED**
  (frame 8400); novo jogo abre no **quarto em Pallet Town** (frame 42000);
  encontros Gen 2–9 **presentes no binário** (li `sRoute1_FireRed_LandMons`
  no ELF → Pidgey, Starly, Stufful, Pidove; Rota 22 → Pancham, Tandemaus,
  Clobbopus).
- **PROVÁVEL (falta captura):** batalha selvagem real com um Pokémon novo na
  grama da Rota 1. O driver de input não venceu os diálogos do prólogo.
- **Receita reproduzível:** `scripts/firered/buildar_firered_expansion.sh`
  (`--self-test` 5/5) + `scripts/firered/misturar_encontros.py`
  (`--self-test` 18/18) + `scripts/firered/patches/000{1,2}-*.patch`.
  Documento completo: `docs/FIRERED.md`; capturas: `reports/firered/`.
- **Dois bugs do fork que o build expôs (corrigidos por patch):**
  (a) `asm/macros/map.inc` abortava com flag de item escondido 0 — o fork zera
  as flags de Hoenn no modo FireRed; (b) `map_data_rules.mk` fixava
  `mapjson map emerald`, gerando `.inc` em modo Emerald e quebrando o link com
  `undefined reference to gTileset_Building`.
- **Limites:** inglês; engine do Emerald (menus/sons); enredo de Kanto não
  testado de ponta a ponta; sem compatibilidade com saves oficiais.

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
