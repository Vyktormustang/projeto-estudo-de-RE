# REA - Release / Link

- Repositório upstream: https://github.com/morluto/rea
- Release: https://github.com/morluto/rea/releases/tag/rea-agents-6.5.0

## Observações
Este arquivo foi criado para manter o README principal limpo e sem alterações no documento principal do projeto.

---

# Ferramentas de RE — REA + Ghidra (atualizado 2026-10-22)

Guia completo: **[`docs/REA_GHIDRA.md`](docs/REA_GHIDRA.md)**.
Scripts: `scripts/setup_re_tools.sh`, `scripts/re_env.sh`,
`scripts/re_tools_check.sh`, `scripts/rea_ghidra_smoke.sh`.

## Versões fixadas (não são “latest”)

| Ferramenta | Versão | Motivo do pin |
|---|---|---|
| REA (`rea-agents`) | **6.7.0** | release atual do upstream (tag `rea-agents-6.7.0`) |
| Ghidra | **12.1.4 PUBLIC** | o REA 6.7.0 só aceita a série **12.1.x**; a 12.2 é rejeitada |
| JDK (Temurin) | **21.0.13+9** | Ghidra 12.1.4 exige `java.min=21` e um **JDK completo** (com `javac`), não JRE |

Checksums usados pelo instalador:
- Ghidra `ghidra_12.1.4_PUBLIC_20260921.zip`:
  `ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db`
- JDK: SHA-256 lido do `.sha256.txt` oficial publicado junto do asset.

## Instalação

**No Windows não existe `bash`** — use `docs/WINDOWS.md` (GUI do Ghidra, scripts
`.ps1` ou WSL). Os comandos abaixo são para Linux/macOS/WSL.

```bash
bash scripts/setup_re_tools.sh          # REA + JDK 21 + Ghidra 12.1.4 (~800 MB de download)
source scripts/re_env.sh                # exporta JAVA_HOME, GHIDRA_INSTALL_DIR e PATH
bash scripts/re_tools_check.sh          # diagnóstico (exit 0 = pronto)
bash scripts/rea_ghidra_smoke.sh        # teste ponta-a-ponta com imagem ARM sintética
```

Opções úteis: `--dry-run`, `--verify-only`, `--jdk-home DIR`, `--ghidra-dir DIR`,
`--ghidra-zip ARQ`, `--jdk-tarball ARQ` (offline), `--strict`.

## Estado verificado (rótulos do projeto)

| Item | Estado | Evidência |
|---|---|---|
| REA 6.7.0 instalado (`~/.local/bin/rea`) | **CONFIRMADO** | `rea --version` → `6.7.0` |
| Ghidra 12.1.4 PUBLIC extraído | **CONFIRMADO** | `application.version=12.1.4`, `release.name=PUBLIC` |
| Ghidra conferido pelo REA | **CONFIRMADO** | `rea doctor`: `ghidra`, `ghidra-version`, `ghidra-headless`, `ghidra-native_decompiler` OK |
| Proveniência do Ghidra | **CONFIRMADO** | `application.revision.ghidra=8b6bbb857accdfa20dc5b2f5dea471178c2e9fbc` = commit da tag oficial `Ghidra_12.1.4_build` (via `api.github.com`) |
| Decompilador nativo | **CONFIRMADO** | `…/os/linux_x86_64/decompile` = ELF 64-bit x86-64 (“matches linux/x64” no doctor) |
| JDK 21 completo | **PENDENTE no sandbox** | ambiente sem `javac`; nenhuma fonte acessível forneceu um JDK completo |
| `provider_ghidra_available` | **PENDENTE no sandbox** | depende do JDK: doctor acusa `runtime only` |
| Smoke test REA→Ghidra | **PENDENTE no sandbox** | script pronto; sai com código 3 enquanto faltar JDK |

Motivo da pendência local: o sandbox só tem acesso a `github.com`,
`codeload.github.com`, `api.github.com`, `registry.npmjs.org` e `pypi.org`; a CDN
de assets (`release-assets.githubusercontent.com`) é bloqueada, então os
downloads oficiais de 208 MB (JDK) e 570 MB (Ghidra) não completam. O Ghidra
local veio de um espelho do **mesmo build oficial** (validado pelo `revision`
oficial) e o instalador do repositório usa **somente URLs oficiais + SHA-256**.

## Próximo passo (na máquina do usuário, com internet normal)

1. `bash scripts/setup_re_tools.sh` (o script instala o JDK e valida tudo).
2. `bash scripts/re_tools_check.sh` → esperado `RESULTADO: stack RE pronto`.
3. `bash scripts/rea_ghidra_smoke.sh` → esperado exit 0 + JSONs em `reports/re_tools/`.
4. Depois disso a Fase 2 (refinação de nomes no Ghidra) deixa de estar bloqueada.

## Importar a ROM no Ghidra (ARMv4T)

```bash
bash scripts/ghidra_import_gba.sh rom/sua_rom.gba   # guia: docs/GHIDRA_IMPORT.md
bash scripts/ghidra_import_gba.sh --self-test       # sem ROM: usa ROM sintética de 32 KB
```

Usa `-processor ARM:LE:32:v4t` (não a lane raw do REA, que fixa ARMv7), cria o
mapa de memória do GBA, valida o cabeçalho do cartucho, rotula
`gBagSlots_slot0`/`SetGpuReg`/`REG_KEYINPUT` e semeia entradas ARM (CONFIRMADO)
e Thumb (HIPÓTESE). Evidências em `reports/ghidra/` (ignorado pelo git).
