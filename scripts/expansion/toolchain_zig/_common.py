"""Funções comuns dos wrappers arm-none-eabi-* (backend: zig cc + lld)."""
ZIG = "/tmp/tc/bin/_zig"
ALVO = "--target=arm-linux-musleabi"   # headers libc + ABI EABI; sem linkar libc
CPU = "-mcpu=arm7tdmi"
LIXO = {"-mthumb-interwork", "-mabi=apcs-gnu", "-meabi=5", "-fno-toplevel-reorder",
        "-mno-thumb-interwork", "-mword-relocations"}
LIXO |= {"-fno-diagnostics-show-caret", "-fno-show-column", "-fno-tree-loop-distribute-patterns",
         "-fno-aggressive-loop-optimizations", "-fno-ipa-cp-clone", "-fno-inline-functions-called-once",
         "-fira-algorithm=priority", "-fno-toplevel-reorder", "-fno-var-tracking-assignments",
         "-fno-stack-protector", "-mno-unaligned-access"}


def normaliza(argv):
    """Remove flags do gcc-ARM que o clang nao conhece e fixa a CPU."""
    out, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a in LIXO:
            i += 1; continue
        if a.startswith(("-mabi=", "-meabi=", "-march=", "-mtune=", "-mcpu=")):
            i += 1; continue
        if a in ("-march", "-mtune", "-mcpu"):
            i += 2; continue
        out.append(a); i += 1
    # o driver do zig injeta -c internamente; com -Werror isso vira erro
    return [CPU, "-fpack-struct=4", "-fshort-enums"] + out + [  # APCS-GNU: agregados e u64 alinhados a 4
             "-Wno-error=unused-command-line-argument",
             "-Wno-error=incompatible-function-pointer-types",
             "-Wno-error=incompatible-pointer-types",
             "-Wno-error=return-mismatch",
             "-Wno-error=int-conversion",
             "-Wno-error=implicit-function-declaration",
             "-Wno-error=implicit-int",
             "-Wno-error"]

def cc(argv, extra=()):
    import subprocess
    return subprocess.call([ZIG, "cc", ALVO] + normaliza(list(argv)) + list(extra))
