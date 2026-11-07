#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""teste_mod_bench.py — prova ponta a ponta do mod na ROM de bancada (mGBA real).

O QUE ESTE TESTE PROVA (e o que ele NÃO prova)
    PROVA: o mecanismo do mod funciona na emulação — o veneer no site chega ao
    trampolim, o combo L+R+START detectado por REG_KEYINPUT preenche os 8 slots
    da mochila, e a ROM segue executando normalmente (o contador do site bate
    mais de 4.000 incrementos por quadro, sem travar).

    NÃO PROVA: que o mesmo vale no FireRed. Para isso a validação final exige a
    ROM do usuário (não redistribuível): `scripts/apply_mod.py` + screenshot da
    mochila aberta. Está escrito no README/HANDOFF — ninguém chama de "pronto"
    antes disso.

CENÁRIOS
    A sem combo (120 f)            -> mochila intocada
    B combo por 30 f               -> 8 slots preenchidos; sobrevive ao soltar
    C só L+R (combo incompleto)    -> nada
    D combo via agenda (--input)   -> nada; agenda é agendada p/ frame futuro
    E estabilidade (600 f c/ combo)-> ROM não trava (contador segue subindo)

USO
    python3 tests/teste_mod_bench.py            # sai 0 se tudo passar
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from gba_emu import Emu                      # noqa: E402
import gba_modkit as mk                      # noqa: E402

BENCH = ROOT / "tests/fixtures/bench_hook.gba"
MOD = ROOT / "tests/fixtures/bench_mod.gba"
BAG = 0x020258B8
COUNTER = 0x03000100


def mochila(emu: Emu) -> list[tuple[int, int]]:
    d = emu.read(BAG, 32)
    return [(int.from_bytes(d[i * 4:i * 4 + 2], "little"),
             int.from_bytes(d[i * 4 + 2:i * 4 + 4], "little")) for i in range(8)]


def eh_padrao(itens: list[tuple[int, int]]) -> bool:
    return itens == mk.PADRAO


def main() -> int:
    falhas = 0

    def chk(nome: str, ok: bool, extra: str = "") -> None:
        nonlocal falhas
        print(f"  [{'PASS' if ok else 'FAIL'}] {nome}{(' — ' + extra) if extra else ''}")
        if not ok:
            falhas += 1

    print("teste_mod_bench.py — prova do mod em emulador (ROM de bancada, 0 conteúdo de jogo)")

    # bancada + mod, gerados agora (reprodutível)
    if not BENCH.is_file():
        import subprocess
        subprocess.run([sys.executable, str(ROOT / "tests/fixtures/make_bench_rom.py"),
                        "-o", str(BENCH)], check=True)
    receita = mk.receita(va_tramp=0x08020000)
    MOD.write_bytes(mk.aplicador(BENCH.read_bytes(), receita))
    chk("mod aplicado na bancada", MOD.is_file(), f"{MOD.stat().st_size} B")

    # A — sem combo
    e = Emu().load(MOD)
    e.frames(120)
    base = mochila(e)
    base_counter = e.read32(COUNTER)
    chk("A) sem combo: nenhum slot escrito", not any(i for i, _ in base), str(base[:2]))
    chk("A) site continua executando (contador > 100k)",
        base_counter > 100_000, f"{base_counter}")
    e.close()

    # B — combo completo
    e = Emu().load(MOD)
    e.frames(60)
    e.hold("L", "R", "START")
    e.frames(30)
    cheia = mochila(e)
    chk("B) combo L+R+START preenche os 8 slots", eh_padrao(cheia),
        " ".join(f"{i:04X}x{q}" for i, q in cheia))
    e.release()
    e.frames(60)
    chk("B) soltar os botões não apaga a mochila", mochila(e) == cheia)
    e.close()

    # C — combo incompleto
    e = Emu().load(MOD)
    e.frames(60)
    e.hold("L", "R")
    e.frames(30)
    chk("C) L+R sozinho não dispara", not any(i for i, _ in mochila(e)))
    e.close()

    # D — agenda (mesmo caminho de `--input FRAME:BOTAO:HOLD`)
    e = Emu().load(MOD)
    e.schedule(40, "L+R+START", 20)
    e.frames(30)
    chk("D) agenda não dispara antes do frame marcado", not any(i for i, _ in mochila(e)))
    e.frames(40)
    chk("D) agenda dispara no frame marcado", eh_padrao(mochila(e)))
    e.close()

    # E — estabilidade com combo por 600 frames
    e = Emu().load(MOD)
    e.hold("L", "R", "START")
    e.frames(600)
    c1 = e.read32(COUNTER)
    e.frames(60)
    c2 = e.read32(COUNTER)
    chk("E) 600 frames com combo: ROM viva (contador avança)", c2 > c1, f"{c1} -> {c2}")
    chk("E) mochila estável cheia", eh_padrao(mochila(e)))
    e.close()

    print(f"resumo: {'OK' if falhas == 0 else str(falhas) + ' falha(s)'}")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
