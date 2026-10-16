# REA - Release / Link

- Repositório upstream: https://github.com/morluto/rea
- Release: https://github.com/morluto/rea/releases/tag/rea-agents-6.5.0

## Observações
Este arquivo foi criado para manter o README principal limpo e sem alterações no documento principal do projeto.

## Instalação (2026-10-15) — FATO, verificado nesta máquina

| Componente | Versão | Origem | Local |
|---|---|---|---|
| REA (`rea-agents`) | 6.5.0 (idêntica à tag `rea-agents-6.5.0`) | npm (`registry.npmjs.org`) | `rea` em `/usr/local/bin/rea` |
| Ghidra | 12.1.2 PUBLIC | árvore oficial empacotada no repo `REMnux/distro` (`ppasrc/ghidra/ghidra-12.1.2-noble`) | `/home/user/tools/ghidra` (symlink → `ghidra-12.1.2`) |
| JDK | OpenJDK 25 (build 64-bit full, `jdk.compiler` presente) | jmods JDK 25 (`bluestacks/prebuilts-jdk-jdk25-a16`, `linux-x86`), imagem `lib/modules` reconstruída com `jlink` | `/home/user/tools/jdk` (symlink → `jdk-25`) |

Ambiente (já em `~/.bashrc`):

```bash
export JAVA_HOME=/home/user/tools/jdk
export GHIDRA_INSTALL_DIR=/home/user/tools/ghidra
export PATH="$JAVA_HOME/bin:$GHIDRA_INSTALL_DIR/support:$PATH"
```

### Evidências de validação
- `analyzeHeadless /tmp/ghidra-proj SmokeTest -import /bin/true` → `REPORT: Analysis succeeded` (3 s de análise).
- `rea doctor` → checks `ghidra`, `ghidra-platform`, `ghidra-architecture`, `ghidra-installation`, `ghidra-version` (12.1.2; compatível 12.1.x), `ghidra-headless`, `ghidra-native_decompiler` (elf x86_64) e `ghidra-java` (25; 64-bit; JDK; "accepted a 64-bit full JDK 21 or newer") **todos healthy**.
- `rea analyze /bin/true --provider ghidra` → pipeline completo REA→Ghidra: ELF x86_64, 33 segmentos, 231 procedimentos, 143 strings, evidence id emitido.
- Skill do REA instalada em `/home/user/.agents/skills/reverse-engineer-anything` (`rea setup --skill --yes` → status `ready`).

### Limitações do sandbox (importante)
- Os *release assets* do GitHub (`release-assets.githubusercontent.com`) são bloqueados neste ambiente; o zip oficial `ghidra_12.1.4_PUBLIC_*` não pôde ser baixado. O Ghidra instalado veio da árvore **12.1.2** (build oficial NSA, nativos linux_x86_64 inclusos) versionada no repo do REMnux.
- Todo JDK completo tem `lib/modules` > 100 MB (limite do GitHub) e fica em Git LFS (host bloqueado). O JDK 25 acima foi **reconstruído**: binários/nativos/jmods do prebuilt `bluestacks/prebuilts-jdk-jdk25-a16` + `lib/modules` gerado por `jlink` (executado no runtime Java do pacote `jdk4py`). Fonte dos jmods preservada em `/home/user/tools/bstack-jdk25` para reconstruções futuras.
- A tag `rea-agents-6.5.0` do GitHub não possui binários anexados (só fonte); o canal oficial de distribuição é o pacote npm `rea-agents@6.5.0`, que foi o instalado.

### Uso rápido
```bash
rea doctor                  # saúde da instalação (Ghidra/JDK)
rea analyze <bin> --provider ghidra    # overview com evidências
analyzeHeadless <projDir> <nome> -import <bin>   # Ghidra headless direto
```
