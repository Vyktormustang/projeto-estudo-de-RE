"""Constantes e utilitarios dos wrappers (ferramentas reais compiladas para WASM)."""
import subprocess, sys, os

ZIG = "/usr/local/lib/python3.11/dist-packages/ziglang/zig"
PKG = "/tmp/pkg/package/wasm"
ARQ = "/tmp/pkg/package/share/gba/lib/arm-archives"
SYSINC = "/tmp/pkg/package/share/gba/lib/libgba/sysinclude"
AQUI = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(AQUI, "wtool.mjs")


def roda(tool, argv, stdin=None, cwd=None):
    """Executa uma ferramenta WASM via node, repassando stdin."""
    env = dict(os.environ)
    cmd = ["node", RUNNER, tool, cwd or os.getcwd()] + list(argv)
    if stdin is None:
        return subprocess.call(cmd, env=env)
    env["WT_STDIN"] = "1"
    p = subprocess.Popen(cmd, env=env, stdin=subprocess.PIPE)
    p.communicate(stdin)
    return p.returncode


def cc1(argv, stdin):
    """cc1 do GCC 14.2 real; escreve .s em stdout."""
    args, tmp = list(argv), None
    for i, a in enumerate(args):
        if a == "-o" and i + 1 < len(args) and args[i + 1] == "-":
            tmp = "/tmp/.cc1out.%d.s" % os.getpid()
            args[i + 1] = tmp
    args = ["-isystem", SYSINC] + [a for a in args if a != "-quiet"]
    rc = roda("cc1", args, stdin=stdin)
    if tmp:
        try:
            with open(tmp, "rb") as f:
                sys.stdout.buffer.write(f.read())
        finally:
            try: os.unlink(tmp)
            except OSError: pass
    return rc
