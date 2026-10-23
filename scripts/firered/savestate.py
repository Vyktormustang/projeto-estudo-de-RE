#!/usr/bin/env python3
"""Lê e escreve campos do jogo direto no savestate do mGBA.

Motivo: testar telas do jogo (Pokédex, time, bolsa) pelo emulador é lento, e
depender de menus de debug não existe no pokefirered vanilla. Manipular o
savestate com **offsets corretos** é a forma rápida e determinística.

Os offsets vêm de `offsets.py` (compilador ARM real). **Nunca** use os
comentários do `global.h` nem o gcc do host: os dois dão valores errados.

Layout do savestate do mGBA (GBA):
    IWRAM em 0x19000, EWRAM em 0x21000 (ponteiros de 0x02000000/0x03000000).

Uso
---
    # estado atual
    savestate.py --map X.map --offsets o.json --in S.bin info

    # ler o time
    savestate.py --map X.map --offsets o.json --in S.bin party

    # marcar espécies como vistas+capturadas (contorna o anticheat da Pokédex)
    savestate.py --map X.map --offsets o.json --in S.bin --out T.bin dex --caught 1 4 7 1025

    # ligar uma flag
    savestate.py --map X.map --offsets o.json --in S.bin --out T.bin flag --set 0x829
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path

IWRAM = 0x19000
EWRAM = 0x21000
IWRAM_BASE = 0x03000000
EWRAM_BASE = 0x02000000


def simbolos_do_map(caminho: Path, nomes: list[str]) -> dict[str, int]:
    """Acha endereços de símbolos no .map do linker (offset dentro da região)."""
    alvo = set(nomes)
    achados: dict[str, int] = {}
    for linha in Path(caminho).read_text(errors="replace").splitlines():
        partes = linha.split()
        if len(partes) < 2 or partes[-1] not in alvo:
            continue
        try:
            achados[partes[-1]] = int(partes[0], 16)
        except ValueError:
            continue
    faltando = alvo - set(achados)
    if faltando:
        raise SystemExit(f"símbolos não achados no .map: {sorted(faltando)}")
    return achados


class Estado:
    def __init__(self, dados: bytes, mapa: Path):
        self.d = bytearray(dados)
        self.sym = simbolos_do_map(mapa, ["gSaveBlock1Ptr", "gSaveBlock2Ptr",
                                          "gPlayerParty", "gEnemyParty"])
        self.s1 = self._bloco("gSaveBlock1Ptr")
        self.s2 = self._bloco("gSaveBlock2Ptr")

    def _bloco(self, nome: str) -> int:
        """Devolve o offset (no savestate) do bloco apontado pelo ponteiro."""
        ptr_addr = self.sym[nome] - IWRAM_BASE
        ptr = struct.unpack_from("<I", self.d, IWRAM + ptr_addr)[0]
        if not (EWRAM_BASE <= ptr < EWRAM_BASE + 0x40000):
            raise SystemExit(f"{nome} aponta para 0x{ptr:08X} (fora da EWRAM)")
        return EWRAM + (ptr - EWRAM_BASE)

    def regiao(self, nome: str) -> int:
        """Offset, no savestate, de um símbolo de IWRAM/EWRAM."""
        addr = self.sym[nome]
        if IWRAM_BASE <= addr < IWRAM_BASE + 0x8000:
            return IWRAM + (addr - IWRAM_BASE)
        if EWRAM_BASE <= addr < EWRAM_BASE + 0x40000:
            return EWRAM + (addr - EWRAM_BASE)
        raise SystemExit(f"{nome} em 0x{addr:08X}: região não mapeada")

    # ---- leitura -----------------------------------------------------
    def posicao(self) -> tuple[int, int, int, int]:
        x, y = struct.unpack_from("<hh", self.d, self.s1)
        mg, mn, _ = struct.unpack_from("<bbB", self.d, self.s1 + 4)
        return x, y, mg, mn

    def contagem_time(self) -> int:
        return self.d[self.s1 + 52]

    def time(self, qtd: int) -> list[int]:
        base = self.regiao("gPlayerParty")
        return [struct.unpack_from("<H", self.d, base + i * 100 + 0x20)[0] for i in range(qtd)]

    # ---- escrita -----------------------------------------------------
    def marcar_dex(self, nums: list[int], visto: bool, capturado: bool, off: dict) -> None:
        dex = self.s2 + off["s2_pokedex"]
        for n in nums:
            if not 1 <= n <= 1025:
                raise SystemExit(f"#{n} fora da faixa 1..1025")
            idx, bit = (n - 1) // 8, (n - 1) % 8
            m = 1 << bit
            if visto:
                self.d[dex + off["dex_seen"] + idx] |= m
            if capturado:
                self.d[dex + off["dex_owned"] + idx] |= m
            # anticheat: SaveBlock1.seen1 e seen2 precisam concordar
            if visto or capturado:
                self.d[self.s1 + off["s1_seen1"] + idx] |= m
                self.d[self.s1 + off["s1_seen2"] + idx] |= m

    def set_flag(self, num: int, ligada: bool, off: dict) -> None:
        base = self.s1 + off["s1_flags"]
        byte, bit = num // 8, num % 8
        if ligada:
            self.d[base + byte] |= 1 << bit
        else:
            self.d[base + byte] &= ~(1 << bit)

    def get_flag(self, num: int, off: dict) -> bool:
        base = self.s1 + off["s1_flags"]
        return bool(self.d[base + num // 8] & (1 << (num % 8)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", required=True)
    ap.add_argument("--offsets", required=True, help="JSON gerado por offsets.py")
    ap.add_argument("--in", dest="entrada", required=True)
    ap.add_argument("--out", dest="saida", default="")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("info")
    sub.add_parser("party")
    p_dex = sub.add_parser("dex", help="marca espécies na Pokédex")
    p_dex.add_argument("nums", nargs="+", type=int)
    p_dex.add_argument("--no-caught", action="store_true")

    p_flag = sub.add_parser("flag")
    p_flag.add_argument("--set", dest="ligar", nargs="*", type=lambda s: int(s, 0))
    p_flag.add_argument("--clear", dest="desligar", nargs="*", type=lambda s: int(s, 0))

    a = ap.parse_args()
    off = json.loads(Path(a.offsets).read_text())
    est = Estado(Path(a.entrada).read_bytes(), Path(a.map))

    if a.cmd == "info":
        x, y, mg, mn = est.posicao()
        print(f"posicao   : ({x},{y})")
        print(f"mapa      : {mg}:{mn}")
        print(f"time      : {est.contagem_time()} mon(s)")
        print(f"SaveBlock1: 0x{est.s1:X}   SaveBlock2: 0x{est.s2:X}")
        for f, nome in ((0x829, "POKEDEX_GET"), (0x840, "NATIONAL_DEX")):
            print(f"flag {nome:<13}: {est.get_flag(f, off)}")
        return 0

    if a.cmd == "party":
        qtd = est.contagem_time()
        print(f"time: {qtd} mon(s)")
        for i, sp in enumerate(est.time(qtd)):
            print(f"  slot {i}: especie {sp}")
        return 0

    if a.cmd == "dex":
        est.set_flag(0x829, True, off)   # sem FLAG_SYS_POKEDEX_GET o item nem aparece no menu
        est.marcar_dex(a.nums, visto=True, capturado=not a.no_caught, off=off)
        print(f"{len(a.nums)} espécies marcadas na Pokédex: {a.nums[:8]}"
              f"{' ...' if len(a.nums) > 8 else ''}")
    elif a.cmd == "flag":
        est.set_flag(0x829, True, off)   # POKEDEX_GET
        for n in a.ligar or []:
            est.set_flag(n, True, off)
            print(f"flag 0x{n:03X} ligada")
        for n in a.desligar or []:
            est.set_flag(n, False, off)
            print(f"flag 0x{n:03X} desligada")

    if not a.saida:
        print("aviso: sem --out, nada foi gravado")
        return 0
    Path(a.saida).write_bytes(bytes(est.d))
    print(f"salvo: {a.saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
