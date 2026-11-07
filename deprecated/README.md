# deprecated/

Ferramentas e binários aposentados — mantidos só como registro histórico.
Nada aqui é usado pela bateria de testes.

## `gba_libretro_emu.py` (driver libretro headless, 2026-10-14 → 2026-11-07)

Substituído por `scripts/gba_emu.py` + `tools/gba_shim/`. Duas causas-raiz:

1. **Binário incompatível**: o `mgba_libretro.so` do pacote Debian 13 exige
   `GLIBC_2.38`; o sandbox roda Debian 12 (2.36) → `GLIBC_2.38 not found` no
   `--self-test`. O core e os `.deb` que ficavam em `emu/` foram removidos
   (4,6 MB de binário que não carrega).
2. **Sem observabilidade**: o core libretro publica **zero** descritores de
   memória (`SET_MEMORY_MAPS` vazio — já registrado no ciclo 22), então EWRAM,
   IWRAM, IO, CPU e registradores ficavam inacessíveis. Todo save-state e
   leitura de mochila era feito "de fora", por arquivo.

O substituto compila a libmgba a partir do fonte (tag 0.10.5, sha256 no
`tools/gba_shim/mgba_tree.sha256`) e conversa direto com o barramento do
emulador: `read/write` em qualquer região, `pc()`, `reg()`, breakpoints,
`keys_held()`, save-state binário — tudo dentro do processo Python.
