#!/usr/bin/env python3
"""VYK-60 — teste "sempre escreve": payload que NÃO checa teclas.

Decisão da issue:
  * escreveu     → hook e endereço corretos; o que resta é a leitura das teclas;
  * não escreveu → a rotina hookada não cobre esta cena; trocar de função.

Roda em ROM **cópia** e state sintético, e registra valor lido + frame + SHA da
ROM de teste (exigência de aceite). Controle negativo: a ROM limpa, no mesmo
state, não pode ter o alvo alterado.

    python3 scripts/teste_vyk60_sempre_escreve.py --rom X.gba --state S.bin \
        --site 0x0808EB88 --tramp 0x08EB0C00 --alvo 0x0202B79C --fechar-a 200
    python3 scripts/teste_vyk60_sempre_escreve.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gba_modkit as mk  # noqa: E402
from gba_emu import Emu  # noqa: E402

SENTINELA = 0xA5A55A5A
TMP_MOD = Path("/tmp/_vyk60_mod.gba")


def payload_sentinela(endereco: int) -> str:
    """`[endereco] = 0xA5A55A5A` sem ler REG_KEYINPUT (nenhum ands/bne)."""
    linhas = ["push {r0, r1, r2, r3, r6}"]
    linhas += mk.carregar("r0", endereco)
    linhas += mk.carregar("r2", SENTINELA)
    linhas += ["str r2, [r0]", "pop {r0, r1, r2, r3, r6}"]
    return "\n".join(linhas)


def montar(rom: bytes, site: int, tramp: int, alvo: int) -> bytes:
    r = mk.receita(site_va=site, prologo=rom[site - 0x08000000:site - 0x08000000 + 8],
                   va_tramp=tramp, payload_asm=payload_sentinela(alvo))
    img = bytearray(rom)
    img[site - 0x08000000:site - 0x08000000 + 8] = r["site"]
    img[tramp - 0x08000000:tramp - 0x08000000 + len(r["tramp"])] = r["tramp"]
    return bytes(img)


def _ler(rom_path: str, state: str, alvo: int, fechar_a: int) -> tuple[int, int]:
    e = Emu().load(rom_path)
    try:
        e.load_state(state)
        e.frames(120)
        if fechar_a:
            e.schedule(e.frames_total, "A", 4)
            e.frames(fechar_a)
        frame = e.frames_total
        valor = e.read32(alvo)
        return valor, frame
    finally:
        e.close()


def rodar(rom_path: str, state: str, site: int, tramp: int, alvo: int,
          fechar_a: int) -> dict:
    rom = Path(rom_path).read_bytes()
    mod = montar(rom, site, tramp, alvo)
    TMP_MOD.write_bytes(mod)

    v_limpa, f_limpa = _ler(rom_path, state, alvo, fechar_a)
    v_mod, f_mod = _ler(str(TMP_MOD), state, alvo, fechar_a)
    escreveu = v_mod == SENTINELA

    return {
        "escreveu": escreveu,
        "decisao": ("hook e endereço corretos; resta a leitura das teclas"
                    if escreveu else
                    "a rotina hookada não cobre esta cena; trocar por função por frame"),
        "valor_lido_mod": f"0x{v_mod:08X}",
        "valor_lido_limpa": f"0x{v_limpa:08X}",
        "controle_limpa_intacto": v_limpa != SENTINELA,
        "frame_mod": f_mod,
        "frame_controle": f_limpa,
        "alvo": f"0x{alvo:08X}",
        "site": f"0x{site:08X}",
        "tramp": f"0x{tramp:08X}",
        "sha256_rom_base": hashlib.sha256(rom).hexdigest(),
        "sha256_rom_teste": hashlib.sha256(mod).hexdigest(),
        "sha256_state": hashlib.sha256(Path(state).read_bytes()).hexdigest(),
    }


def self_test() -> int:
    """Sintético: `_ler` não é exercitável sem ROM; testa o payload e a decisão."""
    asm = payload_sentinela(0x0202B79C)
    assert "ands" not in asm and "bne" not in asm, "o payload não pode checar teclas"
    assert "str r2, [r0]" in asm
    codigo = mk.montar(asm, 0x08010000)
    assert isinstance(codigo, (bytes, bytearray)) and len(codigo) > 0
    assert codigo[:2] == b"\x4f\xb4", "deve começar com push {r0,r1,r2,r3,r6}"
    desasm = [(i.mnemonic, i.op_str) for i in mk._capstone_md().disasm(bytes(codigo), 0x08010000)]
    assert ("str", "r2, [r0]") in desasm, "deve conter o str da sentinela"
    assert not any(m == "ands" for m, _ in desasm), "não pode ler REG_KEYINPUT"
    print("payload sem checagem de teclas:", asm.replace("\n", " ; "))
    print("bytes:", bytes(codigo).hex(" "))
    print("self-test: PASSOU")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom")
    ap.add_argument("--state")
    ap.add_argument("--site", type=lambda s: int(s, 0))
    ap.add_argument("--tramp", type=lambda s: int(s, 0))
    ap.add_argument("--alvo", type=lambda s: int(s, 0))
    ap.add_argument("--fechar-a", type=int, default=200, help="frames após tapar A (0 = nenhum)")
    ap.add_argument("--json-out")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not all([a.rom, a.state, a.site, a.tramp, a.alvo]):
        ap.error("informe --rom --state --site --tramp --alvo (ou --self-test)")
    res = rodar(a.rom, a.state, a.site, a.tramp, a.alvo, a.fechar_a)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(res, ensure_ascii=False, indent=2))
    ok = res["escreveu"] and res["controle_limpa_intacto"]
    print("RESULTADO:", "ESCREVEU SEM TECLAS" if ok else "NÃO ESCREVEU / CONTROLE SUJO")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
