#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gba_poketext.py — decodificador do charset custom Pokémon (Gen 3) + extrator de texto
=====================================================================================

OBJETIVO
    Decodificar o sistema de codificação de caracteres dos jogos Pokémon GBA
    (RSE/FRLG), extrair candidatos a texto e VALIDAR EMPIRICAmente o charset
    contra a ROM real usando âncoras de conteúdo conhecido (nomes de espécies,
    itens, golpes). Também executa sondas de idioma (PT-BR × EN) para
    classificar a variante da ROM.

POR QUE ISSO É CONFIÁVEL
    O charset NÃO é presumido: âncoras como "BULBASAUR" (bytes BC CF C6 BC BB CD
    BB CF CC) são buscadas na ROM. Encontrá-las — vizinhas de "IVYSAUR",
    "VENUSAUR" e do slot 0 "??????????" — valida a decodificação com evidência
    interna reproduzível. Cada sotaque (é, ç, á…) é reportado como confirmado ou
    não por sondas, nunca presumido.

ENTRADAS     ROM bruta (.gba). Opcional: JSON com remapeamentos do charset.
SAÍDAS (-o)  <rom>_poketext_anchors.json   (âncoras: achou/não achou, offsets, vizinhança)
             <rom>_poketext_dump.tsv       (strings candidatas: offset, score, texto)
             <rom>_poketext_markers.json   (marcadores PT-BR/EN: contagens e contextos)
             logs/gba_poketext_runs.jsonl

USO
    python3 gba_poketext.py ROM.gba all              # anchors + dump + markers
    python3 gba_poketext.py ROM.gba anchors          # só validação por âncoras
    python3 gba_poketext.py ROM.gba dump             # extração em massa (TSV)
    python3 gba_poketext.py ROM.gba markers          # sondas PT-BR/EN
    python3 gba_poketext.py ROM.gba probe 0xOFF [-n 64]   # decodifica N bytes de um offset (HIPÓTESE testável)
    python3 gba_poketext.py --self-test

LIMITAÇÕES DECLARADAS
    1. O dump é GERADOR DE CANDIDATOS: dados gráficos/comprimidos podem imitar
       texto; use o score e verifique contexto antes de confiar.
    2. Strings contendo 0xFF dentro de códigos de controle raros podem truncar.
    3. ROMs traduzidas podem REMAPEAR o charset (assentos viram [NN]); use
       --charset-override para aplicar remapeamentos descobertos.
    4. PT-BR é inferido por marcadores linguísticos específicos, não por estatística
       vaga — ver seção "markers" do relatório.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

VERSAO = "1.0.0"
GBA_ROM_BASE = 0x08000000

# --------------------------------------------------------------------------- #
# Charset Gen 3 — dois níveis de confiança declarados
# --------------------------------------------------------------------------- #
# NÚCLEO (alta confiança): padrão universal documentado (Bulbapedia/pokefirered).
def _montar_nucleo() -> dict[int, str]:
    t: dict[int, str] = {0x00: " "}
    for i in range(26):
        t[0xBB + i] = chr(ord("A") + i)   # 0xBB..0xD4 = A..Z
        t[0xD5 + i] = chr(ord("a") + i)   # 0xD5..0xEE = a..z
    for i in range(10):
        t[0xA1 + i] = str(i)              # 0xA1..0xAA = 0..9
    t.update({0xAB: "!", 0xAC: "?", 0xAD: ".", 0xAE: "-"})
    return t

# EXTENSÃO (confiança moderada até sonda empírica): acentos e símbolos variam
# por localização; validados aqui via âncora POKéMON (é) e sondas PT-BR (ç, á).
_EXTENSAO_PADRAO = {
    0x01: "À", 0x02: "Á", 0x03: "Â", 0x04: "Ç", 0x05: "È", 0x06: "É",
    0x07: "Ê", 0x08: "Ë", 0x09: "Ì", 0x0A: "Î", 0x0B: "Ï", 0x0C: "Ò",
    0x0D: "Ó", 0x0E: "Ô", 0x10: "Ù", 0x11: "Ú", 0x12: "Û", 0x13: "Ñ",
    0x15: "à", 0x16: "á", 0x17: "â", 0x18: "ç", 0x19: "è", 0x1A: "é",
    0x1B: "ê", 0x1C: "ë", 0x1D: "ì", 0x1E: "î", 0x1F: "ï", 0x20: "ò",
    0x21: "ó", 0x22: "ô", 0x24: "ù", 0x25: "ú", 0x26: "û", 0x27: "ñ",
    0xB0: "…", 0xB4: "'", 0xB5: "♂", 0xB6: "♀", 0xB8: ",", 0xBA: "/",
}

CTRL_2BYTES = {0xFC: "{FC}", 0xFD: "{BUF}"}   # consomem 1 byte de parâmetro
CTRL_1BYTE = {0xFB: "{FB}", 0xF9: "{F9}"}
EOS, NEWLINE = 0xFF, 0xFE


def montar_charset(override_path: Path | None) -> tuple[dict, dict, dict, set]:
    """Retorna (núcleo, extensão, tabela_unificada, bytes_prioritarios_override).

    `prioritarios` = bytes que vieram do override: usado para desempatar o
    mapeamento inverso char→byte (o mesmo char pode existir no estoque E no
    override; nesse caso o byte do override VENCE, pois reflete a ROM real).
    """
    nucleo = _montar_nucleo()
    ext = dict(_EXTENSAO_PADRAO)
    prio: set[int] = set()
    if override_path:
        dados = json.loads(override_path.read_text(encoding="utf-8"))
        for k, v in dados.items():
            if k.startswith("_"):          # metadados/documentação: ignorar
                continue
            b = int(k, 0)
            ext[b] = v
            prio.add(b)
    tab = dict(ext)
    tab.update(nucleo)  # núcleo prevalece
    return nucleo, ext, tab, prio


def inversa_prioritaria(tab: dict, prio: set) -> dict:
    """Mapa char→byte. Em empates (char mapeado por >1 byte), vence byte ∈ prio."""
    inv: dict[str, int] = {}
    for b, c in tab.items():
        cur = inv.get(c)
        if cur is None or (b in prio and cur not in prio):
            inv[c] = b
    return inv


# --------------------------------------------------------------------------- #
# Decodificação
# --------------------------------------------------------------------------- #

def decodificar(data: bytes, inicio: int, max_len: int, tab: dict,
                nucleo: dict) -> dict:
    """Decodifica a partir de `inicio` até EOS (0xFF) ou max_len bytes.

    Retorna texto (quebras \n como '¶', desconhecidos como [NN]) + métricas.
    """
    texto: list[str] = []
    i, consumidos = inicio, 0
    n_nucleo = n_ext = n_desc = n_ctrl = 0
    terminou_limpo = False
    while consumidos < max_len and i < len(data):
        b = data[i]
        if b == EOS:
            terminou_limpo = True
            i += 1
            break
        if b == NEWLINE:
            texto.append("¶"); n_ctrl += 1; i += 1; consumidos += 1; continue
        if b in CTRL_2BYTES:
            if i + 1 < len(data):
                texto.append(f"{CTRL_2BYTES[b]}{data[i+1]:02X}")
            n_ctrl += 1; i += 2; consumidos += 2; continue
        if b in CTRL_1BYTE:
            texto.append(CTRL_1BYTE[b]); n_ctrl += 1; i += 1; consumidos += 1; continue
        ch = tab.get(b)
        if ch is None:
            texto.append(f"[{b:02X}]"); n_desc += 1
        else:
            texto.append(ch)
            if b in nucleo:
                n_nucleo += 1
            else:
                n_ext += 1
        i += 1; consumidos += 1
    return {
        "texto": "".join(texto),
        "fim_exclusivo": i,
        "payload_chars": n_nucleo + n_ext + n_desc,
        "n_nucleo": n_nucleo, "n_ext": n_ext, "n_desconhecidos": n_desc,
        "n_controles": n_ctrl,
        "terminador_ff": terminou_limpo,
    }


def encode(texto: str, tab_inv: dict) -> bytes:
    """Inverso (para self-test e sondas). Levanta KeyError em char desconhecido."""
    return bytes(tab_inv[c] for c in texto)


def score_legibilidade(d: dict) -> float:
    total = d["payload_chars"]
    if total == 0:
        return 0.0
    # núcleo pesa 1.0, extensão pesa 0.6, desconhecido pesa 0
    return (d["n_nucleo"] + 0.6 * d["n_ext"]) / total


def parece_texto(d: dict, min_chars: int, min_score: float) -> bool:
    if d["payload_chars"] < min_chars or not d["terminador_ff"]:
        return False
    if score_legibilidade(d) < min_score:
        return False
    letras = sum(1 for c in d["texto"] if c.isalpha())
    vogais = sum(1 for c in d["texto"].lower() if c in "aeiouáéíóúâêôãõ")
    tem_minuscula_ou_espaco = any(c.islower() or c == " " for c in d["texto"])
    if tem_minuscula_ou_espaco:
        return letras >= 3 and vogais >= 2
    # caso tudo-maiúsculo (nomes próprios como BULBASAUR): exige mais letras
    return letras >= 6 and vogais >= 2


# --------------------------------------------------------------------------- #
# Âncoras de validação (conteúdo conhecido → validação empírica do charset)
# --------------------------------------------------------------------------- #

# "??" = curinga de 1 byte (usado p/ descobrir empiricamente o código do 'é')
ANCORAS = {
    "BULBASAUR":  "BC CF C6 BC BB CD BB CF CC",
    "IVYSAUR":    "C3 D0 D3 CD BB CF CC",
    "VENUSAUR":   "D0 BF C8 CF CD BB CF CC",
    "CHARMANDER": "BD C2 BB CC C7 BB C8 BE BF CC",
    "POTION":     "CA C9 CE C3 C9 C8",
    "POUND":      "CA C9 CF C8 BE",
    "POK[e]MON":  "CA C9 C5 ?? C7 C9 C8",   # byte-3 desconhecido → descoberta do 'é'
}
SONDA_ESPECIE = 11  # Gen 3: 10 chars + 0xFF por slot de nome de espécie


def _regex_hex(hexstr: str) -> bytes:
    partes = []
    for tok in hexstr.split():
        partes.append(b"." if tok == "??" else re.escape(bytes([int(tok, 16)])))
    return b"".join(partes)


def buscar_padrao(data: bytes, hexstr: str) -> list[int]:
    rx = re.compile(_regex_hex(hexstr), re.DOTALL)
    return [m.start() for m in rx.finditer(data)]


def relatorio_ancoras(data: bytes, tab: dict, nucleo: dict) -> dict:
    res = {"ancoras": {}, "byte_e_empirico": None, "tabela_especies": None}
    for nome, hexstr in ANCORAS.items():
        offs = buscar_padrao(data, hexstr)
        entrada = {"hex": hexstr, "encontradas": len(offs),
                   "offsets_hex": [f"0x{o:08x}" for o in offs[:8]]}
        if nome == "POK[e]MON" and offs:
            b = data[offs[0] + 3]
            entrada["byte_pos3_hex"] = f"0x{b:02X}"
            entrada["mapeado_como"] = tab.get(b, "(fora do charset)")
            res["byte_e_empirico"] = {"byte": f"0x{b:02X}",
                                      "mapeado_como": entrada["mapeado_como"]}
        res["ancoras"][nome] = entrada

    # estrutura da tabela de espécies ao redor de BULBASAUR (se achada)
    offs_b = buscar_padrao(data, ANCORAS["BULBASAUR"])
    if offs_b:
        base = offs_b[0]
        viz = []
        for j in (-2, -1, 0, 1, 2, 3):
            off = base + j * SONDA_ESPECIE
            if off < 0:
                continue
            slot = data[off:off + SONDA_ESPECIE]
            dec = decodificar(slot, 0, SONDA_ESPECIE, tab, nucleo)
            viz.append({"idx_relativo": j, "offset_hex": f"0x{off:08x}",
                        "raw_hex": slot.hex(), "decodificado": dec["texto"]})
        res["tabela_especies"] = {"base_bulbasaur_hex": f"0x{base:08x}",
                                  "addr_gba_hex": f"0x{GBA_ROM_BASE + base:08x}",
                                  "vizinhanca_slot_11B": viz}
    return res


# --------------------------------------------------------------------------- #
# Dump em massa
# --------------------------------------------------------------------------- #

def extrair_candidatas(data: bytes, tab: dict, nucleo: dict,
                       min_chars: int, min_score: float) -> list[dict]:
    """Varre segmentos delimitados por 0xFF e mantém os que parecem texto."""
    achadas: list[dict] = []
    inicio_seg = 0
    n = len(data)
    i = data.find(b"\xff")
    while i != -1:
        seg_ini, seg_fim = inicio_seg, i  # segmento [ini, fim)
        if seg_fim - seg_ini >= min_chars:
            d = decodificar(data[seg_ini:seg_fim + 1], 0, seg_fim - seg_ini + 1,
                            tab, nucleo)
            if parece_texto(d, min_chars, min_score):
                achadas.append({
                    "offset_hex": f"0x{seg_ini:08x}",
                    "addr_gba_hex": f"0x{GBA_ROM_BASE + seg_ini:08x}",
                    "bytes": seg_fim - seg_ini,
                    "score": round(score_legibilidade(d), 3),
                    "desconhecidos": d["n_desconhecidos"],
                    "texto": d["texto"],
                })
        inicio_seg = i + 1
        i = data.find(b"\xff", inicio_seg)
    # dedupe: remove candidatas totalmente contidas em outra já aceita
    achadas.sort(key=lambda s: int(s["offset_hex"], 16))
    final, ultimo_fim = [], -1
    for s in achadas:
        ini = int(s["offset_hex"], 16)
        if ini >= ultimo_fim:
            final.append(s)
            ultimo_fim = ini + s["bytes"]
    return final


# --------------------------------------------------------------------------- #
# Sondas PT-BR × EN (evidência linguística específica, não estatística vaga)
# --------------------------------------------------------------------------- #

def relatorio_marcadores(data: bytes, tab: dict, nucleo: dict,
                         prio: set | None = None) -> dict:
    tab_inv = inversa_prioritaria(tab, prio or set())

    def enc_ou_none(palavra: str):
        try:
            return encode(palavra, tab_inv)
        except KeyError:
            return None

    sondas_pt = ["ção", "você", "Você", "Olá", "olá", "está", "Está",
                 "Parabéns", "obrigad", "Poké"]
    sondas_en = [" the ", "You", "Hello", "Thank", "POKé", "PLAYER"]

    def sondar(palavras, tab_inv_local):
        out = {}
        for p in palavras:
            enc = enc_ou_none(p)
            if enc is None:
                out[p] = {"status": "nao_codificavel_neste_charset"}
                continue
            ocorr = [m.start() for m in re.finditer(re.escape(enc), data)]
            ctx = []
            for o in ocorr[:3]:
                ini = max(data.rfind(b"\xff", 0, o), 0) + 1
                fim = data.find(b"\xff", o)
                fim = fim if fim != -1 else min(len(data), o + 80)
                dec = decodificar(data[ini:fim + 1], 0, fim - ini + 1, tab, nucleo)
                ctx.append({"offset_hex": f"0x{ini:08x}", "texto": dec["texto"][:120]})
            out[p] = {"hex": enc.hex(), "ocorrencias": len(ocorr), "contextos": ctx}
        return out

    return {
        "nota_metodo": ("'ocorrencias' = hits do byte-pattern exato; contextos "
                        "mostram a string 0xFF-delimitada que contém o hit. "
                        "PT-BR exige múltiplos marcadores com contexto legível."),
        "pt_br": sondar(sondas_pt, tab_inv),
        "en": sondar(sondas_en, tab_inv),
    }


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #

def self_test(verbose: bool) -> int:
    import tempfile
    nucleo, ext, tab, prio = montar_charset(None)
    tab_inv = {c: b for b, c in tab.items()}
    checks = []

    # 1) núcleo codifica/decodifica âncoras
    buf = encode("BULBASAUR", tab_inv) + b"\xff"
    checks.append(("encode('BULBASAUR') == âncora",
                   buf[:-1] == bytes.fromhex(ANCORAS["BULBASAUR"])))
    d = decodificar(buf, 0, 16, tab, nucleo)
    checks.append(("decode(âncora) == 'BULBASAUR'", d["texto"] == "BULBASAUR"))
    checks.append(("EOS reconhecido", d["terminador_ff"] is True))

    # 2) controles: FC/FD consomem 1 parâmetro; FE vira ¶
    d2 = decodificar(encode("AB", tab_inv) + bytes([0xFC, 0x06]) +
                     encode("CD", tab_inv) + bytes([0xFE]) +
                     encode("EF", tab_inv) + b"\xff", 0, 32, tab, nucleo)
    checks.append(("controles FC/FE", d2["texto"] == "AB{FC}06CD¶EF"))

    # 3) bytes desconhecidos viram [NN] e derrubam score
    d3 = decodificar(bytes([0x9C, 0x9D]) + b"\xff", 0, 8, tab, nucleo)
    checks.append(("desconhecido -> [NN]", d3["texto"] == "[9C][9D]"))
    checks.append(("score p/ lixo == 0", score_legibilidade(d3) == 0.0))

    # 4) varredura acha strings e rejeita lixo
    rom_falsa = (encode("HELLO WORLD", tab_inv) + b"\xff" + b"\x9c\x9d\xff" * 3 +
                 bytes(16) + encode("BULBASAUR", tab_inv) + b"\xff")
    res = extrair_candidatas(rom_falsa, tab, nucleo, min_chars=5, min_score=0.75)
    textos = [r["texto"] for r in res]
    checks.append(("dump acha 'HELLO WORLD'", any("HELLO WORLD" in t for t in textos)))
    checks.append(("dump acha 'BULBASAUR'", any("BULBASAUR" in t for t in textos)))
    checks.append(("dump rejeita lixo 9C9D", not any("[9C]" in t for t in textos)))

    # 5) wildcard: CA C9 C5 ?? C7 C9 C8 casa POK?MON com qualquer byte-3
    alvo = encode("POK", tab_inv) + b"\x1a" + encode("MON", tab_inv)
    checks.append(("wildcard POK[e]MON", buscar_padrao(b"xx" + alvo + b"yy",
                   ANCORAS["POK[e]MON"]) == [2]))

    # 6) override vence no mapa inverso (regressão: sondas com 'é'/'ç' usavam
    #    o byte do estoque, gerando falsos zeros nos marcadores)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as tf:
        json.dump({"0x1B": "é", "0x1C": "ê", "0x19": "ç"}, tf)
        tmp = tf.name
    try:
        _, _, tab2, prio2 = montar_charset(Path(tmp))
        inv2 = inversa_prioritaria(tab2, prio2)
        checks.append(("override vence inverso ('é'→0x1B)", inv2["é"] == 0x1B))
        checks.append(("override vence inverso ('ê'→0x1C)", inv2["ê"] == 0x1C))
        checks.append(("override vence inverso ('ç'→0x19)", inv2["ç"] == 0x19))
    finally:
        Path(tmp).unlink()

    falhas = 0
    for nome, ok in checks:
        if verbose or not ok:
            print(f"  [{'PASS' if ok else 'FAIL'}] {nome}")
        falhas += 0 if ok else 1
    print(f"self-test: {len(checks) - falhas}/{len(checks)} verificações OK")
    return 1 if falhas else 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _log(logs_dir: Path, entrada: dict) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    with (logs_dir / "gba_poketext_runs.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")


def main(argv=None) -> int:
    script_dir = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(
        description="Decodificador do charset Pokémon Gen 3 com validação por âncoras.")
    ap.add_argument("rom", nargs="?", type=Path)
    ap.add_argument("cmd", nargs="?", default="all",
                    choices=["all", "anchors", "dump", "markers", "probe"])
    ap.add_argument("offset", type=lambda s: int(s, 0), nargs="?", default=None,
                    help="offset para cmd=probe (aceita 0x...)")
    ap.add_argument("-n", "--length", type=lambda s: int(s, 0), default=64)
    ap.add_argument("-o", "--outdir", type=Path,
                    default=script_dir.parent / "reports")
    ap.add_argument("--min-chars", type=int, default=5)
    ap.add_argument("--min-score", type=float, default=0.75)
    ap.add_argument("--charset-override", type=Path, default=None,
                    help="JSON com remapeamentos {\"0xNN\": \"char\"}")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test(args.verbose)
    if not args.rom or not args.rom.is_file():
        print("erro: informe uma ROM válida (ou --self-test).", file=sys.stderr)
        return 2
    if args.cmd == "probe" and args.offset is None:
        print("erro: cmd=probe requer offset.", file=sys.stderr)
        return 2

    t0 = time.perf_counter()
    data = args.rom.read_bytes()
    nucleo, ext, tab, prio = montar_charset(args.charset_override)
    args.outdir.mkdir(parents=True, exist_ok=True)
    stem = args.rom.stem
    feitos: dict[str, str] = {}

    if args.cmd in ("all", "anchors"):
        rep = relatorio_ancoras(data, tab, nucleo)
        p = args.outdir / f"{stem}_poketext_anchors.json"
        p.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
        feitos["anchors"] = str(p)
        print("== ÂNCORAS (validação empírica do charset) ==")
        for nome, e in rep["ancoras"].items():
            print(f"  {nome:<12} {e['encontradas']:>4} hit(s) {e.get('offsets_hex', [])[:3]}")
        if rep["byte_e_empirico"]:
            be = rep["byte_e_empirico"]
            print(f"  >> byte do 'é' em POKéMON: {be['byte']} → {be['mapeado_como']!r}")
        if rep["tabela_especies"]:
            te = rep["tabela_especies"]
            print(f"  >> tabela de espécies: base {te['base_bulbasaur_hex']} "
                  f"(GBA {te['addr_gba_hex']})")
            for v in te["vizinhanca_slot_11B"]:
                print(f"     slot[{v['idx_relativo']:+d}] {v['offset_hex']}: "
                      f"{v['decodificado']!r}")

    if args.cmd in ("all", "dump"):
        cands = extrair_candidatas(data, tab, nucleo, args.min_chars, args.min_score)
        p = args.outdir / f"{stem}_poketext_dump.tsv"
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(["offset_hex", "addr_gba_hex", "bytes", "score",
                        "desconhecidos", "texto"])
            for c in cands:
                w.writerow([c["offset_hex"], c["addr_gba_hex"], c["bytes"],
                            c["score"], c["desconhecidos"], c["texto"]])
        feitos["dump"] = str(p)
        print(f"\n== DUMP == {len(cands)} strings candidatas "
              f"(min_chars={args.min_chars}, min_score={args.min_score}) → {p}")
        for c in cands[:8]:
            print(f"  {c['offset_hex']} score={c['score']:<5} {c['texto'][:72]!r}")

    if args.cmd in ("all", "markers"):
        rep = relatorio_marcadores(data, tab, nucleo, prio)
        p = args.outdir / f"{stem}_poketext_markers.json"
        p.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
        feitos["markers"] = str(p)
        print("\n== MARCADORES DE IDIOMA ==")
        for grupo in ("pt_br", "en"):
            print(f"  [{grupo}]")
            for pal, e in rep[grupo].items():
                oc = e.get("ocorrencias", "—")
                print(f"    {pal!r:<12} {oc}")
        alvos = [k for k in ("ção", "você", "Você", "Olá", "olá")
                 if rep["pt_br"].get(k, {}).get("ocorrencias", 0) > 0]
        print(f"\n  PT-BR marcadores com hits: {alvos or 'nenhum'}")

    if args.cmd == "probe":
        d = decodificar(data, args.offset, args.length, tab, nucleo)
        raw = data[args.offset: args.offset + args.length]
        print(f"== PROBE @0x{args.offset:08x} (GBA 0x{GBA_ROM_BASE + args.offset:08x}) ==")
        print(f"raw    : {raw.hex(' ')}")
        print(f"decode : {d['texto']}")
        print(f"stats  : núcleo={d['n_nucleo']} ext={d['n_ext']} "
              f"desc={d['n_desconhecidos']} terminou_FF={d['terminador_ff']}")

    _log(script_dir.parent / "logs", {
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ferramenta": "gba_poketext.py", "versao": VERSAO,
        "rom_sha256": hashlib.sha256(data).hexdigest(),
        "cmd": args.cmd, "duracao_s": round(time.perf_counter() - t0, 3),
        "saidas": feitos})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
