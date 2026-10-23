# Toolchain ARM experimental (Zig) — incompleto

Alternativa ao `arm-none-eabi-*` oficial, para ambientes onde só há acesso a
GitHub/PyPI/npm (foi o caso do sandbox do projeto). **Não fecha o build.**

## Como era usado

```bash
pip install ziglang
export PATH="$(pwd):$PATH"      # estes wrappers
cd pokeemerald-expansion
make modern -j2
```

Os wrappers chamam `zig cc --target=arm-linux-musleabi` (clang + lld) e
normalizam as diferenças:

| Problema | Solução no wrapper |
|---|---|
| `-march/-mtune/-mcpu` viram CPU inválida | força `-mcpu=arm7tdmi` |
| `-mthumb-interwork`, `-mabi=apcs-gnu` | removidos (clang não conhece) |
| `-mabi=apcs-gnu` alinha agregados/u64 a 4 | `-fpack-struct=4` |
| enums do ARM EABI são curtos | `-fshort-enums` |
| `-Werror` + avisos novos do clang | `-Wno-error=...` seletivo |
| `.include` resolvido pelo CWD (e não pelo arquivo) | roda com `cwd` = dir do fonte |
| `--defsym` | injetado como `.equ` no topo |
| `mov r1, #1` (GNU aceita em Thumb) | reescreve só as linhas rejeitadas (`movs`) |
| `[r0, SYM]` sem `#` | `[r0, #(SYM)]` |
| `.struct` (contador de offsets do m4a) | emulado com `.set`/`.equiv` |
| `.syntax divided` no `global.h` | removido do fonte |

## Onde parou

~95% dos objetos compilam (todo o C, gráficos, mapas, som). O build trava em
arquivos `.s` que dependem de macros do GNU `as` — por exemplo `Call` /
`CreatePinkHearts` em `data/battle_anim_scripts.s`. O assembler do LLVM não
expande essas macros do mesmo jeito, e não há ajuste de flag que resolva.

**Use o toolchain oficial (devkitPro) no Windows/WSL.** Ver `docs/EXPANSION.md`.
