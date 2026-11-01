#!/usr/bin/env python3
"""gba_state_dump.py — leitor/editor de save-states blob do gba_libretro_emu.py.

Descoberto empiricamente (ciclo "mod menu", evidência: célula 0x03007FFC do
IWRAM contém o handler IRQ 0x08000248 quando base=0x19000; pool 0x03005090
mostra ponteiros de código — ver logs/tests e notes_mods_codigo.md):

  layout do blob (528 448 B observado, mGBA 0.10.5 via retro_serialize):
    IWRAM  0x19000..0x21000  (32 KiB, endereços 0x03000000–0x03008000)
    EWRAM  0x21000..0x61000 (256 KiB, endereços 0x02000000–0x02040000)
    SAVE   0x61000..0x81000 (128 KiB, flash1M: conteúdo vivo do cartucho)
    demais offsets: CPU/IO/GPU/VRAM (verificar quando necessário)

Uso:
  python3 gba_state_dump.py state.bin --read 0xADDR:0xN [--read ...]
  python3 gba_state_dump.py state.bin --patch 0xADDR=HEXSTR -o saida.bin
  python3 gba_state_dump.py stateA.bin --diff stateB.bin 0xSTART 0xFIM
Saída: hexdump JSON no stdout; --patch escreve arquivo novo (nunca in-place)."""
import argparse, json, sys
from pathlib import Path

REGIOES = [("IWRAM", 0x03000000, 0x03008000, 0x19000),
           ("EWRAM", 0x02000000, 0x02040000, 0x21000),
           ("SAVE",  0x0E000000, 0x0E020000, 0x61000)]


def trad(addr, reg=None):
    for nome, a, b, base in REGIOES:
        if (reg in (None, nome)) and a <= addr < b:
            return nome, base + (addr - a)
    return None, None


def hexdump(dado, addr, max_w=8):
    out = []
    for i in range(0, len(dado), 16):
        w = dado[i:i+16]
        out.append({"end": hex(addr + i), "hex": w.hex(" ")})
        if len(out) > max_w * 64:
            out.append({"...": "truncado", "em": i})
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("state", type=Path, nargs="?", default=None)
    ap.add_argument("--read", action="append", default=[], help="0xADDR:0xN")
    ap.add_argument("--patch", action="append", default=[], help="0xADDR=hexbytes")
    ap.add_argument("-o", type=Path, help="saída (necessário c/ --patch)")
    ap.add_argument("--diff", nargs=3, metavar=("STATE_B", "0xINI", "0xFIM"),
                    help="compara janela de memória entre dois states (mesma região)")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        import tempfile
        falhas = 0

        def chk(nome, ok, verboso=False):
            nonlocal falhas
            if verboso or not ok:
                print(f"  [{'PASS' if ok else 'FAIL'}] {nome}")
            falhas += 0 if ok else 1

        # fixture sintética com o tamanho real observado
        buf = bytearray(528448)
        buf[0x19000:0x19004] = b"\xaa\xbb\xcc\xdd"     # IWRAM base
        buf[0x21000 + 0x100:0x21004 + 0x100] = b"\x01\x02\x03\x04"
        fixture = Path(tempfile.mkstemp(suffix=".bin")[1])
        fixture.write_bytes(buf)
        chk("trad IWRAM boundary", trad(0x03008000 - 1)[0] == "IWRAM"
            and trad(0x03008000)[0] != "IWRAM")
        chk("trad EWRAM/SAVE", trad(0x02000000)[0] == "EWRAM"
            and trad(0x0E000000)[0] == "SAVE")
        chk("SAVE translation offset",
            trad(0x0E000000)[1] == 0x61000)
        # fluxo read
        import subprocess, sys as _s
        r = subprocess.run([_s.executable, __file__, str(fixture),
                            "--read", "0x03000000:0x04", "--read", "0x02000100:0x04"],
                           capture_output=True, text=True)
        j = json.loads(r.stdout)
        chk("read EWRAM+0x100 sintético",
            j["reads"][1]["dump"][0]["hex"] == "01 02 03 04")
        # fluxo patch + re-leitura
        out = fixture.with_suffix(".out.bin")
        r = subprocess.run([_s.executable, __file__, str(fixture),
                            "--patch", "0x0E000000=beef", "-o", str(out)],
                           capture_output=True, text=True)
        back = out.read_bytes()
        chk("patch SAVE é aplicado e arquivo preserva tamanho",
            back[0x61000:0x61002] == b"\xbe\xef" and len(back) == len(buf))
        chk("nunca in-place (fixture intacta)",
            fixture.read_bytes()[0x61000] == 0)
        fixture.unlink(); out.unlink(missing_ok=True)
        print(f"self-test: {5 - falhas}/5 verificações OK")
        return 1 if falhas else 0
    if a.state is None:
        ap.error("o argumento state é obrigatório (exceto com --self-test)")

    raw = a.state.read_bytes()
    res = {"state": str(a.state), "size": len(raw), "reads": [], "patches": []}

    for spec in a.read:
        addr_s, n_s = spec.split(":")
        addr, n = int(addr_s, 16), int(n_s, 16)
        nome, so = trad(addr)
        if nome is None or so + n > len(raw):
            res["reads"].append({"erro": f"fora de faixa: {spec}"})
            continue
        res["reads"].append({"regiao": nome, "addr": addr_s, "n": n,
                             "dump": hexdump(raw[so:so+n], addr)})

    if a.patch:
        if not a.o:
            sys.exit("erro: --patch exige -o (nunca in-place)")
        buf = bytearray(raw)
        for spec in a.patch:
            addr_s, hexs = spec.split("=")
            addr = int(addr_s, 16)
            payload = bytes.fromhex(hexs.replace(" ", ""))
            nome, so = trad(addr)
            if nome is None or so + len(payload) > len(buf):
                sys.exit(f"erro: patch fora de faixa: {spec}")
            buf[so:so+len(payload)] = payload
            res["patches"].append({"regiao": nome, "addr": addr_s,
                                   "n": len(payload)})
        a.o.write_bytes(buf)
        res["escrito"] = str(a.o)

    if a.diff:
        outro, ini_s, fim_s = a.diff
        ra = Path(outro).read_bytes()
        ini, fim = int(ini_s, 16), int(fim_s, 16)
        nome, sof1 = trad(ini)
        mud = []
        for addr in range(ini, fim - 3, 4):
            _, sA = trad(addr)
            vA = int.from_bytes(raw[sA:sA+4], "little")
            vB = int.from_bytes(ra[sA:sA+4], "little")
            if vA != vB:
                mud.append({"addr": hex(addr), "a": vA, "b": vB,
                            "verbo": f"0x{vA:08x}→0x{vB:08x}"})
        res["diff"] = {"regiao": nome, "janela": f"{ini_s}..{fim_s}",
                       "mudancas": len(mud), "primeiras": mud[:48]}

    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
