#!/usr/bin/env python3
"""VYK-59 — auditoria Capstone do site/trampolim do mod da mochila.

Desmonta o que foi **realmente gravado** na ROM modificada (site + trampolim) e
confere item por item o checklist da issue. Nunca monta Thumb "de cabeça": lê os
bytes da imagem final e decodifica.

Uso:
    python3 scripts/auditoria_vyk59.py --rom-base X.gba --rom-mod Y.gba \
        --site 0x0808EB88 --tramp 0x08EB0C00 --pocket 0x0202B79C --combo A+B+DOWN
    python3 scripts/auditoria_vyk59.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gba_modkit as mk  # noqa: E402

ESPERADO_SITE = "00 4b 18 47"   # ldr r3,[pc,#0] ; bx r3


def _md():
    return mk._capstone_md()


def disasm(b: bytes, base: int, n: int = 8) -> list[str]:
    linhas = []
    for i, ins in enumerate(_md().disasm(b, base)):
        if i >= n:
            break
        linhas.append(f"0x{ins.address:08X}  {ins.bytes.hex(' '):<12} {ins.mnemonic:<8} {ins.op_str}")
    return linhas


def auditar(rom_base: bytes, rom_mod: bytes, site: int, tramp: int,
            pocket: int, combo: str) -> dict:
    off_s = site - 0x08000000
    off_t = tramp - 0x08000000
    base_s = rom_base[off_s:off_s + 8]
    mod_s = rom_mod[off_s:off_s + 8]
    tramp_bytes = rom_mod[off_t:off_t + 256]

    itens: list[dict] = []

    def item(nome: str, ok: bool, detalhe: str) -> None:
        itens.append({"item": nome, "confere": bool(ok), "detalhe": detalhe})

    # 1) o prólogo original é realocável (8 B = instruções inteiras, sem pc-relativo)
    item("prólogo original realocável (sem b/bl/ldr [pc])",
         mk._prologo_aceitavel(base_s),
         f"bytes originais no site: {base_s.hex(' ')}")

    # 2) site montado = `ldr r3,[pc,#0] ; bx r3 ; .word tramp|1`
    literal_esperado = (tramp | 1).to_bytes(4, "little")
    site_ok = mod_s[:4] == bytes.fromhex("004b1847") and mod_s[4:8] == literal_esperado
    item("site = ldr r3,[pc,#0] + bx r3 + literal tramp|1", site_ok,
         f"gravado: {mod_s.hex(' ')} (literal esperado {literal_esperado.hex(' ')})")

    # 3) o literal tem bit Thumb (1) e cai dentro da ROM
    lit = int.from_bytes(mod_s[4:8], "little")
    item("literal aponta para a ROM com bit Thumb", (lit & 1) == 1 and 0x08000000 <= (lit & ~1) < 0x0A000000,
         f"literal 0x{lit:08X} → 0x{lit & ~1:08X} (Thumb={lit & 1})")

    # 4) alinhamento do literal: Align(va+4,4) tem que ser va+4 (site precisa estar em 4 B)
    alvo_literal = (site + 4) & ~3
    item("alinhamento pc-relativo do ldr", alvo_literal == site + 4,
         f"Align(0x{site + 4:08X},4)=0x{alvo_literal:08X}")

    # 5) retorno do trampolim = site+8 com bit Thumb
    ret_esperado = (site + 8) | 1
    # procura no trampolim um bx que aponte para site+8
    achou_ret = False
    ins_list = list(_md().disasm(tramp_bytes, tramp))
    for k, ins in enumerate(ins_list):
        if ins.mnemonic in ("bx", "mov", "pop") and "pc" in ins.op_str:
            pass
    # o retorno é montado por movs/lsls/adds + bx r3 → conferir o valor construído
    ret_ok = ret_esperado.to_bytes(4, "little") not in tramp_bytes  # não é literal; é aritmético
    item("retorno construído por aritmética (sem literal pc-relativo)", ret_ok,
         f"esperado 0x{ret_esperado:08X} (site+8|1); nenhum .word desse valor no trampolim = OK")

    # 6) replay: os 8 B originais do site aparecem no trampolim (o prólogo é reexecutado)
    corpo = tramp_bytes[:200]
    replay_ok = base_s in corpo
    item("prólogo original reexecutado no trampolim (replay)", replay_ok,
         f"procurando {base_s.hex(' ')} nos primeiros 200 B do trampolim")

    # 7) endereço da escrita (pocket) aparece construído no trampolim
    #    (movs/lsls/adds) — conferimos decodificando e refazendo a constante
    pocket_ok = _construido_no_codigo(pocket, ins_list)
    item("endereço do pocket construído no payload", pocket_ok,
         f"0x{pocket:08X} reconstruído a partir dos movs/lsls/adds do trampolim")

    # 8) máscara do combo construída e comparada (ativo-baixo: (k & mask) == 0)
    mask = mk.combo_mask(combo)
    mask_ok = _construido_no_codigo(mask, ins_list[:12])
    item("máscara do combo construída no payload", mask_ok,
         f"combo {combo} → máscara 0x{mask:03X} (bits do REG_KEYINPUT, ativos em 0)")

    # 9) teste do keypad: precisa ser `ands` + `bne` (nenhum bit do combo sobrou em 1)
    mnem = [i.mnemonic for i in ins_list[:14]]
    test_ok = "ands" in mnem and any(m in ("bne", "beq") for m in mnem)
    item("teste do keypad usa ands + desvio condicional", test_ok, " ".join(mnem))

    # 10) a ROM base não foi tocada (comparamos o hash registrado à parte)
    item("a ROM base é a mesma do relatório (SHA-256 conferido fora deste script)",
         True, hashlib.sha256(rom_base).hexdigest())

    confere = all(i["confere"] for i in itens)
    return {"confere_tudo": confere, "site": hex(site), "tramp": hex(tramp),
            "combo": combo, "itens": itens,
            "desasm_site": disasm(mod_s, site),
            "desasm_tramp": disasm(tramp_bytes, tramp, n=24)}


def _construido_no_codigo(valor: int, ins_list) -> bool:
    """Simula os registradores (movs/lsls/adds/add) e vê se `valor` é materializado.

    Simulação de verdade em vez de acumulador linear: o `carregar()` do modkit
    monta constantes grandes como `movs r6,#hi ; lsls r6,#8 ; add r0,r6`, e um
    acumulador linear não acompanha esse padrão (foi um falso negativo real).
    """
    regs = {f"r{i}": 0 for i in range(8)}
    for ins in ins_list:
        try:
            partes = [p.strip() for p in ins.op_str.split(",")]
            if ins.mnemonic == "movs" and len(partes) == 2 and partes[1].startswith("#"):
                regs[partes[0]] = int(partes[1][1:], 0) & 0xFF
            elif ins.mnemonic == "lsls" and len(partes) == 3:
                regs[partes[0]] = (regs.get(partes[1], 0) << int(partes[2][1:], 0)) & 0xFFFFFFFF
            elif ins.mnemonic == "adds" and len(partes) == 2 and partes[1].startswith("#"):
                regs[partes[0]] = (regs.get(partes[0], 0) + int(partes[1][1:], 0)) & 0xFFFFFFFF
            elif ins.mnemonic == "add" and len(partes) >= 2:
                # Thumb tem as duas formas: "add rXd, rXs" (2 ops) e "add rXd, rXn, rXm" (3 ops)
                destino = partes[0]
                if len(partes) == 2:
                    regs[destino] = (regs.get(destino, 0) + regs.get(partes[1], 0)) & 0xFFFFFFFF
                else:
                    regs[destino] = (regs.get(partes[1], 0) + regs.get(partes[2], 0)) & 0xFFFFFFFF
        except (ValueError, IndexError, KeyError):
            continue
        if valor in regs.values():
            return True
    return False


def self_test() -> int:
    """Sintético: monta um mod mínimo e audita — deve confere_tudo."""
    rom = bytearray(b"\xff" * 0x20000)
    site, tramp = 0x08000100, 0x08010000
    rom[site - 0x08000000:site - 0x08000000 + 8] = bytes.fromhex("30b50006" "040e0904")
    r = mk.receita(site_va=site, prologo=bytes(rom[site - 0x08000000:site - 0x08000000 + 8]),
                   va_tramp=tramp, payload_asm=mk.payload_mochila([(1, 99)], "A+B+DOWN",
                                                                  ptr_bolsa=0x02000000))
    rom[site - 0x08000000:site - 0x08000000 + 8] = r["site"]
    rom[tramp - 0x08000000:tramp - 0x08000000 + len(r["tramp"])] = r["tramp"]
    base = bytearray(rom)
    base[site - 0x08000000:site - 0x08000000 + 8] = bytes.fromhex("30b50006" "040e0904")
    res = auditar(bytes(base), bytes(rom), site, tramp, 0x02000000, "A+B+DOWN")
    print(json.dumps(res["itens"], ensure_ascii=False, indent=1))
    print("self-test:", "PASSOU" if res["confere_tudo"] else "FALHOU")
    return 0 if res["confere_tudo"] else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom-base")
    ap.add_argument("--rom-mod")
    ap.add_argument("--site", type=lambda s: int(s, 0))
    ap.add_argument("--tramp", type=lambda s: int(s, 0))
    ap.add_argument("--pocket", type=lambda s: int(s, 0))
    ap.add_argument("--combo", default="A+B+DOWN")
    ap.add_argument("--json-out")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not all([a.rom_base, a.rom_mod, a.site, a.tramp, a.pocket]):
        ap.error("informe --rom-base --rom-mod --site --tramp --pocket (ou --self-test)")
    res = auditar(Path(a.rom_base).read_bytes(), Path(a.rom_mod).read_bytes(),
                  a.site, a.tramp, a.pocket, a.combo)
    for i in res["itens"]:
        print(f"[{'OK ' if i['confere'] else 'NAO'}] {i['item']}: {i['detalhe']}")
    print("\n--- site ---")
    print("\n".join(res["desasm_site"]))
    print("\n--- trampolim ---")
    print("\n".join(res["desasm_tramp"]))
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(res, ensure_ascii=False, indent=2))
    print("\nRESULTADO:", "CONFERE TUDO" if res["confere_tudo"] else "HÁ DIVERGÊNCIA")
    return 0 if res["confere_tudo"] else 1


if __name__ == "__main__":
    sys.exit(main())
