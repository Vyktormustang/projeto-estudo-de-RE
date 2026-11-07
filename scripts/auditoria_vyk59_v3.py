#!/usr/bin/env python3
"""VYK-59 (alvo real: BAG_MOD v3) — auditoria Capstone dos bytes do site/trampolim.

Confere, com decodificação real (nunca montagem "de cabeça"), o checklist da
issue v4 no caso **v3 sem correção** e numa variante **v3 corrigido** (veneer
`00 4b`, retorno `A41`, escrita em `0x020258B8`, máscara `0x3FF`/`0x0308`).

Os bytes do v3 vêm do ZIP histórico (`reports/site_v3.hex`, `tramp_v3.hex`,
`payload_bag_mod.hex`), que acompanha a issue. Nada é inventado.

    python3 scripts/auditoria_vyk59_v3.py --zip 'gba-re_project (1).zip'
    python3 scripts/auditoria_vyk59_v3.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import gba_modkit as mk  # noqa: E402

SITE = 0x08000A38
TRAMP = 0x08EB0C00
PAYLOAD_BASE = 0x08EB0C70
ORIGINAL = bytes.fromhex("30b50006040e0904")
COMBO_V3 = "L+R+START"
COMBO_NOVO = "START+SELECT"


def desasm(b: bytes, base: int) -> list:
    return list(mk._capstone_md().disasm(b, base))


def literal_addr(site: int, imm8: int) -> int:
    """`ldr rX,[pc,#imm8]` (Thumb): Align(PC,4) + imm8, com PC = site + 4.

    O imediato já está em BYTES (não em words) — multiplicar por 4 aqui foi um
    erro real cometido nesta auditoria e corrigido pelo self-test.
    """
    return ((site + 4) & ~3) + imm8


def auditar(site_bytes: bytes, tramp_bytes: bytes, payload_bytes: bytes,
            rotulo: str, combo: str = COMBO_V3) -> dict:
    itens: list[dict] = []

    def item(nome: str, ok: bool, detalhe: str) -> None:
        itens.append({"item": nome, "confere": bool(ok), "detalhe": detalhe})

    # 1) qual endereço o `ldr r3,[pc,#imm]` do site realmente lê
    ins = desasm(site_bytes[:2], SITE)[0]
    imm8 = int(ins.op_str.split("#")[1].rstrip("]"), 0)
    end_literal = literal_addr(SITE, imm8)
    item("ldr do site lê o literal pretendido (0x08000A3C)",
         end_literal == 0x08000A3C,
         f"`{ins.mnemonic} {ins.op_str}` → lê 0x{end_literal:08X}; "
         f"pretendido 0x08000A3C, portanto imediato correto = 0x00 "
         f"(gravado: '{site_bytes[0]:02x} {site_bytes[1]:02x}')")

    # 2) o literal gravado aponta para o trampolim?
    lit_real = int.from_bytes(site_bytes[4:8], "little")
    item("literal no site aponta para o trampolim (0x08EB0C01)",
         lit_real == (TRAMP | 1),
         f"literal = 0x{lit_real:08X}, esperado 0x{TRAMP | 1:08X}")

    # 3) retorno do replay: o v3 constrói o destino por aritmética e faz `bx r3`
    _, bx_tramp, _ = _simular(tramp_bytes, TRAMP)
    esperado_ret = (SITE + 8) | 1
    ret_ok = esperado_ret in bx_tramp
    item("retorno após o replay é 0x08000A41 (site+8|1)", ret_ok,
         f"destinos de `bx` simulados no trampolim: {sorted(hex(b) for b in bx_tramp)}; "
         f"correto 0x{esperado_ret:08X}, errado 0x{(SITE + 8 + 2) | 1:08X}")

    # 4) endereço de escrita construído pelo payload
    alvos = _constantes(payload_bytes, PAYLOAD_BASE)
    escrito = 0x020258B8 if 0x020258B8 in alvos else (0x022058B8 if 0x022058B8 in alvos else None)
    extra = ""
    if 0x022058B8 in alvos:
        extra = (" — 0x022058B8 está FORA da EWRAM (0x02000000–0x0203FFFF): "
                 "não é RAM, a escrita não pode cair na mochila")
    item("payload escreve em 0x020258B8 (não 0x022058B8)", escrito == 0x020258B8,
         f"constantes 0x02xxxxxx no payload: {sorted(hex(a) for a in alvos if 0x02000000 <= a < 0x03000000)}" + extra)

    # 4b) o `ldrh` do payload tem de ler REG_KEYINPUT = 0x04000130
    lido = _endereco_do_ldrh(payload_bytes, PAYLOAD_BASE, "r0")
    item("payload lê REG_KEYINPUT (0x04000130)", lido == 0x04000130,
         f"`ldrh` lê 0x{lido:08X}" + ("" if lido == 0x04000130
                                      else " — NÃO é o registro de teclas (é IWRAM)"))

    mask = mk.combo_mask(combo)
    mask_ok = mask in alvos
    item(f"máscara do combo presente (0x{mask:03X} = {combo})", mask_ok,
         f"constantes pequenas no payload: {sorted(hex(a) for a in alvos if a < 0x1000)}")

    # 6) POLARIDADE: REG_KEYINPUT é ativo em ZERO. Firing só com `(k & mask) == 0`.
    _, _, testes = _simular(payload_bytes, PAYLOAD_BASE)
    nomes = [t[0] for t in testes]
    invertido = ("ands" in nomes and "cmp" in nomes)
    item("teste do keypad compatível com registro ativo em zero", not invertido,
         f"testes encontrados: {testes or 'nenhum'} — "
         + ("`ands`+`cmp` com o próprio valor exige bits em 1, isto é botões SOLTOS: "
            "polaridade invertida" if invertido else
            "`ands`+`bne` (sai se algum bit do combo estiver alto) = correto"))

    # 7) o prólogo original é realocável e aparece no trampolim (replay)
    item("prólogo original reexecutado no trampolim",
         ORIGINAL in tramp_bytes,
         f"procurando {ORIGINAL.hex(' ')} no trampolim")

    return {"rotulo": rotulo, "confere_tudo": all(i["confere"] for i in itens),
            "itens": itens,
            "desasm_site": [f"0x{i.address:08X}  {i.bytes.hex(' '):<10} {i.mnemonic:<6} {i.op_str}"
                            for i in desasm(site_bytes, SITE)],
            "desasm_tramp": [f"0x{i.address:08X}  {i.bytes.hex(' '):<10} {i.mnemonic:<6} {i.op_str}"
                             for i in desasm(tramp_bytes, TRAMP)]}


def _simular(codigo: bytes, base: int) -> tuple[set[int], list[int], list[tuple[str, str]]]:
    """Simula os registradores Thumb e devolve (constantes, destinos de bx, testes).

    Thumb tem TRÊS formas para soma: `adds rXd, #imm` (2 ops), `adds rXd, rXs`
    (2 ops, low) e `adds rXd, rXs, rXt` (3 ops). Tratar só as duas primeiras
    produz falsos negativos — foi o que aconteceu nesta auditoria.
    """
    regs = {f"r{i}": 0 for i in range(8)}
    todos: set[int] = set()
    bx_alvos: list[int] = []
    testes: list[tuple[str, str]] = []
    for ins in desasm(codigo, base):
        p = [x.strip() for x in ins.op_str.split(",")]
        try:
            if ins.mnemonic == "movs" and len(p) == 2 and p[1].startswith("#"):
                regs[p[0]] = int(p[1][1:], 0) & 0xFF
            elif ins.mnemonic == "lsls" and len(p) == 3:
                regs[p[0]] = (regs.get(p[1], 0) << int(p[2][1:], 0)) & 0xFFFFFFFF
            elif ins.mnemonic in ("adds", "add") and len(p) == 2:
                if p[1].startswith("#"):
                    regs[p[0]] = (regs.get(p[0], 0) + int(p[1][1:], 0)) & 0xFFFFFFFF
                else:
                    regs[p[0]] = (regs.get(p[0], 0) + regs.get(p[1], 0)) & 0xFFFFFFFF
            elif ins.mnemonic in ("adds", "add") and len(p) >= 3:
                regs[p[0]] = (regs.get(p[1], 0) + regs.get(p[2], 0)) & 0xFFFFFFFF
            elif ins.mnemonic == "bx":
                bx_alvos.append(regs.get(p[0], -1))
            elif ins.mnemonic in ("ands", "cmp", "tst"):
                testes.append((ins.mnemonic, ins.op_str))
        except (ValueError, IndexError, KeyError):
            continue
        todos.update(regs.values())
    return todos, bx_alvos, testes


def _constantes(codigo: bytes, base: int) -> set[int]:
    return _simular(codigo, base)[0]


def _endereco_do_ldrh(codigo: bytes, base: int, registro: str = "r0") -> int:
    """Valor de `registro` no momento do primeiro `ldrh`."""
    regs = {f"r{i}": 0 for i in range(8)}
    for ins in desasm(codigo, base):
        p = [x.strip() for x in ins.op_str.split(",")]
        try:
            if ins.mnemonic == "ldrh":
                return regs.get(p[1].strip("[] "), -1)
            if ins.mnemonic == "movs" and len(p) == 2 and p[1].startswith("#"):
                regs[p[0]] = int(p[1][1:], 0) & 0xFF
            elif ins.mnemonic == "lsls" and len(p) == 3:
                regs[p[0]] = (regs.get(p[1], 0) << int(p[2][1:], 0)) & 0xFFFFFFFF
            elif ins.mnemonic in ("adds", "add") and len(p) == 2:
                if p[1].startswith("#"):
                    regs[p[0]] = (regs.get(p[0], 0) + int(p[1][1:], 0)) & 0xFFFFFFFF
                else:
                    regs[p[0]] = (regs.get(p[0], 0) + regs.get(p[1], 0)) & 0xFFFFFFFF
            elif ins.mnemonic in ("adds", "add") and len(p) >= 3:
                regs[p[0]] = (regs.get(p[1], 0) + regs.get(p[2], 0)) & 0xFFFFFFFF
        except (ValueError, IndexError, KeyError):
            continue
    return -1


def corrigir_v3(site_bytes: bytes, tramp_bytes: bytes, payload_bytes: bytes
                ) -> tuple[bytes, bytes, bytes]:
    """Aplica as quatro correções da issue sobre os MESMOS bytes do v3."""
    site = bytes.fromhex("004b1847") + site_bytes[4:8]          # 01 4b → 00 4b
    # retorno A43 → A41: o v3 CONSTRÓI o destino por aritmética
    # (`movs r2,#3; adds r3,r3,r2; bx r3`), não por literal. 0x08000A40+3 = A43;
    # para A41 o imediato tem de ser #1 → `03 22` vira `01 22`.
    tramp = tramp_bytes
    cauda = "03229b181847"
    if cauda not in tramp.hex():
        raise ValueError("cauda de retorno esperada não encontrada no trampolim v3")
    tramp = bytes.fromhex(tramp.hex().replace(cauda, "01229b181847"))
    # escrita 0x022058B8 → 0x020258B8 e máscara 0xFF00 → 0x3FF: reconstruídos do zero
    payload = mk.montar(mk.payload_mochila([(1, 99), (2, 99)], COMBO_NOVO,
                                          ptr_bolsa=0x020258B8), PAYLOAD_BASE)
    return site, tramp, payload


def carregar_zip(zip_path: Path) -> tuple[bytes, bytes, bytes]:
    with zipfile.ZipFile(zip_path) as z:
        site = bytes.fromhex(z.read("reports/site_v3.hex").decode().strip())
        tramp = bytes.fromhex(z.read("reports/tramp_v3.hex").decode().strip())
        payload = bytes.fromhex(z.read("reports/payload_bag_mod.hex").decode().strip())
    return site, tramp, payload


def self_test() -> int:
    """Sem o ZIP: valida a aritmética de literal e a simulação de constantes."""
    assert literal_addr(SITE, 4) == 0x08000A40      # `01 4b` → A40 (errado)
    assert literal_addr(SITE, 0) == 0x08000A3C      # `00 4b` → A3C (certo)
    assert mk.combo_mask("L+R+START") == 0x308
    assert mk.combo_mask("START+SELECT") == 0x00C
    c = _constantes(mk.montar(mk.payload_mochila([(1, 99)], "A+B+DOWN",
                                                ptr_bolsa=0x020258B8), PAYLOAD_BASE), PAYLOAD_BASE)
    assert 0x020258B8 in c, sorted(hex(x) for x in c)
    assert 0x083 in c
    print("self-test: PASSOU")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zip", default="gba-re_project (1).zip")
    ap.add_argument("--json-out")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    site, tramp, payload = carregar_zip(Path(a.zip))
    antes = auditar(site, tramp, payload, "v3 como entregue (sem correção)")
    s2, t2, p2 = corrigir_v3(site, tramp, payload)
    depois = auditar(s2, t2, p2, "v3 corrigido (combo trocado para START+SELECT)", COMBO_NOVO)
    for r in (antes, depois):
        print(f"\n### {r['rotulo']} — {'CONFERE TUDO' if r['confere_tudo'] else 'REPROVA'}")
        for i in r["itens"]:
            print(f"[{'OK ' if i['confere'] else 'NAO'}] {i['item']}: {i['detalhe']}")
    print("\n--- desasm do site v3 original ---")
    print("\n".join(antes["desasm_site"]))
    if a.json_out:
        Path(a.json_out).write_text(json.dumps({"antes": antes, "depois": depois,
                                                "corrigido_site": s2.hex(" "),
                                                "corrigido_tramp_len": len(t2),
                                                "corrigido_payload_len": len(p2)},
                                               ensure_ascii=False, indent=2))
    # o esperado desta auditoria: o v3 REPROVA e a versão corrigida PASSA
    ok = (not antes["confere_tudo"]) and depois["confere_tudo"]
    print("\nVEREDITO:", "v3 reprovado nos 4 defeitos; corrigido confere"
          if ok else "INESPERADO — revisar")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
