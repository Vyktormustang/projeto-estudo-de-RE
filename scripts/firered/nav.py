#!/usr/bin/env python3
"""Driver mGBA libretro com savestate: permite continuar de um ponto sem re-rodar a intro.

Uso:
  python3 nav.py --rom R.gba --outdir DIR [--frames N] [--in S.bin] [--out S.bin]
                 [--script "1000-1600:RIGHT;1700:START"] [--shots 500,1000,...] [--every N]

--script: segmentos "inicio-fim:BOTAO" (segura) ou "frame:BOTAO" (aperta 8 frames).
BOTOES: A B UP DOWN LEFT RIGHT START SELECT L R
"""
import argparse, ctypes as C, os, struct, sys, zlib
from pathlib import Path

ENV_CB = C.CFUNCTYPE(None, C.c_uint, C.c_void_p)
VID_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUD_S = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUD_B = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL = C.CFUNCTYPE(None)
ISTATE = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)

BTN = dict(B=0, Y=1, SELECT=2, START=3, UP=4, DOWN=5, LEFT=6, RIGHT=7, A=8, L=10, R=11)


def png_write(path, w, h, rgb):
    raw = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))

    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    path.write_bytes(b"\x89PNG\r\n\x1a\n"
                     + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def parse_script(txt):
    """-> lista de (inicio, fim, conjunto_de_botoes)"""
    segs = []
    if not txt:
        return segs
    for parte in txt.split(";"):
        parte = parte.strip()
        if not parte:
            continue
        alvo, botoes = parte.split(":")
        st = {BTN[b.strip().upper()] for b in botoes.split("+")}
        if "-" in alvo:
            a, b = alvo.split("-")
            segs.append((int(a), int(b), st))
        else:
            i = int(alvo)
            segs.append((i, i + 7, st))
    return segs


def botoes_em(segs, f):
    s = set()
    for a, b, st in segs:
        if a <= f <= b:
            s |= st
    return s


def caixa_de_texto(rgb, w, h):
    """Heuristica: a caixa de dialogo do GBA e uma faixa quase branca no rodape.

    Amostra a faixa y=0.86h..0.96h entre x=0.10w..0.90w e devolve True se
    >=65% dos pixels sao claros nos tres canais.
    """
    if not rgb:
        return False
    y0, y1 = int(h * 0.86), int(h * 0.96)
    x0, x1 = int(w * 0.10), int(w * 0.90)
    claro = total = 0
    for y in range(y0, y1):
        base = y * w * 3
        for x in range(x0, x1, 2):
            o = base + x * 3
            r = rgb[o]; g = rgb[o + 1]; b = rgb[o + 2]
            total += 1
            if r > 205 and g > 205 and b > 205:
                claro += 1
    return total > 0 and claro * 100 // total >= 65


IWRAM_BASE = 0x19000
EWRAM_BASE = 0x21000


def ler_estado(lib):
    """Serializa o core e le gSaveBlock1Ptr (IWRAM) -> posicao e mapa do jogador."""
    tam = lib.retro_serialize_size()
    b = C.create_string_buffer(tam)
    if not lib.retro_serialize(C.cast(b, C.c_void_p), tam):
        return None
    d = b.raw[:tam]
    try:
        ptr = struct.unpack_from("<I", d, IWRAM_BASE + 0x52D8)[0]
        if not (0x02000000 <= ptr < 0x02040000):
            return None
        off = EWRAM_BASE + (ptr - 0x02000000)
        x, y = struct.unpack_from("<hh", d, off)
        mg, mn, _ = struct.unpack_from("<bbB", d, off + 4)
        return dict(x=x, y=y, grupo=mg, mapa=mn)
    except struct.error:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--core", default=os.environ.get(
        "MGBA_CORE", "/tmp/mgba/mgba-0.10.5/build/mgba_libretro.so"))
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--frames", type=int, default=0)
    ap.add_argument("--in", dest="entrada")
    ap.add_argument("--out", dest="saida")
    ap.add_argument("--script", default="")
    ap.add_argument("--shots", default="")
    ap.add_argument("--every", type=int, default=0)
    ap.add_argument("--auto-avancar", type=int, default=0,
                    help="aperta A sozinho ENQUANTO houver caixa de texto; limite de frames")
    ap.add_argument("--pos", type=int, default=0,
                    help="a cada N frames imprime posicao (x,y) e mapa lidos da RAM")
    ap.add_argument("--ir-ate", default="",
                    help="navegacao fechada ate um destino em linha reta: x,y,direcao(UP/DOWN/LEFT/RIGHT)")
    ap.add_argument("--andar-fugir", default="",
                    help="DIRECAO: anda nessa direcao; se a posicao nao mudar, aperta B (fuga) e segue")
    ap.add_argument("--parar-livre", action="store_true",
                    help="para assim que a caixa de texto desaparecer")
    a = ap.parse_args()

    lib = C.CDLL(a.core)
    for nome, tipos in (("retro_set_environment", [C.c_void_p]),
                        ("retro_set_video_refresh", [C.c_void_p]),
                        ("retro_set_audio_sample", [C.c_void_p]),
                        ("retro_set_audio_sample_batch", [C.c_void_p]),
                        ("retro_set_input_poll", [C.c_void_p]),
                        ("retro_set_input_state", [C.c_void_p]),
                        ("retro_init", []), ("retro_load_game", [C.c_void_p]),
                        ("retro_run", []), ("retro_serialize_size", []),
                        ("retro_serialize", [C.c_void_p, C.c_size_t]),
                        ("retro_unserialize", [C.c_void_p, C.c_size_t])):
        getattr(lib, nome).argtypes = tipos
    lib.retro_serialize_size.restype = C.c_size_t
    lib.retro_serialize.restype = C.c_bool
    lib.retro_unserialize.restype = C.c_bool

    estado = {"botoes": set(), "rgb": None, "w": 0, "h": 0}

    def video(data, w, h, pitch):
        if not data:
            return
        buf = C.string_at(data, pitch * h)
        rgb = bytearray(w * h * 3)
        for y in range(h):
            base = y * pitch
            for x in range(w):
                v = buf[base + x * 2] | (buf[base + x * 2 + 1] << 8)
                o = (y * w + x) * 3
                rgb[o] = ((v >> 11) & 31) * 255 // 31
                rgb[o + 1] = ((v >> 5) & 63) * 255 // 63
                rgb[o + 2] = (v & 31) * 255 // 31
        estado["rgb"] = bytes(rgb)
        estado["w"], estado["h"] = w, h

    def istate(port, device, index, bid):
        return 1 if bid in estado["botoes"] else 0

    cbs = [ENV_CB(lambda c, d: None), VID_CB(video), AUD_S(lambda l, r: None),
           AUD_B(lambda d, f: f), POLL(lambda: None), ISTATE(istate)]
    lib.retro_set_environment(C.cast(cbs[0], C.c_void_p))
    lib.retro_set_video_refresh(C.cast(cbs[1], C.c_void_p))
    lib.retro_set_audio_sample(C.cast(cbs[2], C.c_void_p))
    lib.retro_set_audio_sample_batch(C.cast(cbs[3], C.c_void_p))
    lib.retro_set_input_poll(C.cast(cbs[4], C.c_void_p))
    lib.retro_set_input_state(C.cast(cbs[5], C.c_void_p))

    dados = Path(a.rom).read_bytes()

    class GameInfo(C.Structure):
        _fields_ = [("path", C.c_char_p), ("data", C.c_void_p),
                    ("size", C.c_size_t), ("meta", C.c_char_p)]

    buf = C.create_string_buffer(dados)
    gi = GameInfo(str(a.rom).encode(), C.cast(buf, C.c_void_p), len(dados), None)
    lib.retro_init()
    if not lib.retro_load_game(C.byref(gi)):
        print("falha ao carregar a ROM")
        return 1

    outdir = Path(a.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if a.entrada:
        blob = Path(a.entrada).read_bytes()
        b = C.create_string_buffer(blob, len(blob))
        ok = lib.retro_unserialize(C.cast(b, C.c_void_p), len(blob))
        print(f"unserialize({a.entrada}) = {ok} ({len(blob)} B)")
        if not ok:
            return 1

    segs = parse_script(a.script)
    marcos = {int(x) for x in a.shots.split(",") if x.strip()}

    # navegacao fechada: anda na direcao dada ate alcancar (x,y) ou acabar os frames
    destino = None
    if a.ir_ate:
        px, py, direcao = a.ir_ate.split(",")
        destino = dict(x=int(px), y=int(py), dir=direcao.strip().upper())
        print(f"navegando ate ({destino['x']},{destino['y']}) por {destino['dir']}")

    # modo andar-fugir: usa a posicao para saber se entrou em batalha
    modo_af = None
    if a.andar_fugir:
        modo_af = dict(dir=a.andar_fugir.strip().upper())
        print(f"andar-fugir na direcao {modo_af['dir']}")

    livre_ha = 0          # frames consecutivos sem caixa de texto
    ciclo = 0
    for f in range(1, a.frames + 1):
        bot = botoes_em(segs, f)
        if destino:
            est = ler_estado(lib)
            if est:
                if (est["x"], est["y"]) == (destino["x"], destino["y"]):
                    print(f"chegou em ({est['x']},{est['y']}) mapa {est['grupo']}:{est['mapa']} "
                          f"no frame {f}")
                    break
                # so anda em linha reta: se ja passou do alvo nesse eixo, para
                ok = ((destino["dir"] == "RIGHT" and est["x"] < destino["x"]) or
                      (destino["dir"] == "LEFT" and est["x"] > destino["x"]) or
                      (destino["dir"] == "UP" and est["y"] > destino["y"]) or
                      (destino["dir"] == "DOWN" and est["y"] < destino["y"]))
                bot = bot | ({BTN[destino["dir"]]} if ok else set())
                if f % 20 == 0:
                    print(f"  frame {f:5d}: ({est['x']},{est['y']}) mapa {est['grupo']}:{est['mapa']}")
        if modo_af:
            est = ler_estado(lib)
            if est:
                ult = modo_af.get("ult")
                if ult and (est["x"], est["y"]) == ult:
                    modo_af["parado"] = modo_af.get("parado", 0) + 1
                else:
                    modo_af["parado"] = 0
                modo_af["ult"] = (est["x"], est["y"])
                if modo_af["parado"] > 70:
                    # travado: provavelmente batalha/menu -> B para fugir/voltar
                    if modo_af["parado"] % 12 < 6:
                        bot = bot | {BTN["B"]}
                    if modo_af["parado"] % 40 == 0:
                        print(f"  travado em ({est['x']},{est['y']}) ha {modo_af['parado']} f -> B")
                    if modo_af["parado"] > 400:
                        print("  travado demais, encerrando")
                        break
                    modo_af["batalhas"] = modo_af.get("batalhas", 0) + (1 if modo_af["parado"] == 71 else 0)
                else:
                    bot = bot | {BTN[modo_af["dir"]]}
                    if f % 200 == 0:
                        print(f"  f{f:5d} ({est['x']},{est['y']}) mapa {est['grupo']}:{est['mapa']}")
        if a.auto_avancar:
            # A em pulsos de 6 frames a cada 26, mas so quando ha caixa aberta
            tem_caixa = caixa_de_texto(estado["rgb"], estado["w"], estado["h"])
            if tem_caixa:
                ciclo += 1
                if ciclo % 26 < 6:
                    bot = bot | {BTN["A"]}
                livre_ha = 0
            else:
                livre_ha += 1
                if a.parar_livre and livre_ha >= 45:
                    print(f"campo livre detectado no frame {f}")
                    break
        estado["botoes"] = bot
        lib.retro_run()
        if a.pos and f % a.pos == 0:
            est = ler_estado(lib)
            if est:
                print(f"f{f:5d} pos=({est['x']},{est['y']}) mapa={est['grupo']}:{est['mapa']}")
        if estado["rgb"] and (f in marcos or (a.every and f % a.every == 0)):
            cx = "TXT" if caixa_de_texto(estado["rgb"], estado["w"], estado["h"]) else "---"
            png_write(outdir / f"{f:06d}.png", estado["w"], estado["h"], estado["rgb"])
            if a.every:
                print(f"frame {f:6d} {cx}")

    if a.saida:
        tam = lib.retro_serialize_size()
        b = C.create_string_buffer(tam)
        ok = lib.retro_serialize(C.cast(b, C.c_void_p), tam)
        if ok:
            Path(a.saida).write_bytes(b.raw[:tam])
            print(f"state salvo: {a.saida} ({tam} B)")
        else:
            print("falha ao serializar")

    if estado["rgb"]:
        png_write(outdir / "final.png", estado["w"], estado["h"], estado["rgb"])
    print("PNGs em", outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
