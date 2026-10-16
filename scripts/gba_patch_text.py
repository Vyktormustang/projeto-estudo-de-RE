#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gba_patch_text.py — FASE 6: primeiro MODIFICADOR seguro de texto da ROM
=======================================================================

OBJETIVO
    Substituir o conteúdo de UM slot de texto (terminado em 0xFF) por um
    novo texto codificado na tabela de caracteres do projeto
    (gba_poketext: montar_charset + inversa_prioritaria + encode),
    produzindo uma NOVA ROM — a entrada NUNCA é modificada (regra do
    projeto: trabalhar só sobre cópias).

GARANTIAS DE SEGURANÇA
    1. Saída obrigatória em caminho DIFERENTE da entrada (in-place recusado).
    2. --expect: pré-condição — o texto atual do slot DEVE corresponder ao
       esperado (decodificado cru, '¶' para quebra de linha). Se não bater,
       ABORTA sem tocar em byte algum (evita patch em offset errado).
    3. Comprimento: novo texto (codificado + terminador 0xFF) deve CABER no
       slot original (medido até o primeiro 0xFF). Nunca ultrapassa.
    4. Bytes do slot além do novo terminador são PRESERVADOS (preenchimento
       original); fora do slot nada muda.
    5. Relatório: decodificação antes/depois, hexdump do slot, nº de bytes
       alterados, SHA-256 de entrada/saída. Header da ROM NÃO é afetado
       (textos ficam fora de 0xA0–0xBC) → checksum de header se mantém.

USO
    python3 gba_patch_text.py ROM -o SAIDA.gba --offset 0x245F90 \
        --expect "PIDGEY" --new-text "NOVO NOME"
    python3 gba_patch_text.py --self-test           # 5 verificações sintéticas

EXEMPLO REAL (FireRed BPRE — tabela de espécies em 0x245EEB, slots de 11 B;
#16 PIDGEY = 0x245EEB + 15×11 = 0x245F90):
    python3 gba_patch_text.py rom/pokemon_firered_bpre_trabalho.gba \
        -o rom_mod/PATCH_TEXTO_DEMO.gba --offset 0x245F90 \
        --expect "PIDGEY" --new-text "PIDGEY!"

VALIDAÇÃO SUGERIDA NO EMULADOR
    Abrir a ROM de saída no mGBA e conferir o nome da espécie #16 na
    Pokédex/tela de status. A ROM original permanece intacta.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gba_poketext as pt  # noqa: E402  (módulo do projeto; self-test 13/13)

VERSAO = "1.0.0"
TERMINADOR = 0xFF
DEFAULT_OVERRIDE = Path(__file__).resolve().parent.parent / "notes_charset_remap_br.json"


# --------------------------------------------------------------------------- #
# Núcleo
# --------------------------------------------------------------------------- #

class CharsetPack:
    """Empacota as estruturas de charset do gba_poketext."""
    def __init__(self, override_path: Path | None):
        if override_path and not override_path.is_file():
            raise FileNotFoundError(f"override não encontrado: {override_path}")
        self.usa_override = override_path if (override_path and override_path.is_file()) else None
        self.nucleo, self.ext, self.tab, self.prio = pt.montar_charset(self.usa_override)
        self.inv = pt.inversa_prioritaria(self.tab, self.prio)

    def decod(self, data: bytes, inicio: int, max_len: int) -> str:
        return pt.decodificar(data, inicio, max_len, self.tab, self.nucleo)["texto"]

    def enc(self, texto: str) -> bytes:
        try:
            return pt.encode(texto, self.inv)
        except KeyError as e:
            raise ValueError(
                f"caractere ausente da tabela: {e.args[0]!r} — inclua no "
                f"override de charset ou troque o texto.") from e


def localizar_slot(rom: bytes, offset: int, slot_size: int | None = None) -> int:
    """Tamanho do slot.

    Padrão: distância até o 1º terminador 0xFF (regra estrita).
    Com --slot-size (tabelas de passo fixo, ex.: espécies = 11 B): usa o
    passo declarado, MAS exige que todo byte entre o 1º 0xFF e o fim do slot
    seja preenchimento 0x00/0xFF — caso contrário aborta (não sobrescreve
    conteúdo vivo do registro vizinho).
    """
    if not (0 <= offset < len(rom)):
        raise ValueError(f"offset {offset:#x} fora da ROM ({len(rom):#x} bytes)")
    i = rom.find(TERMINADOR, offset)
    if i < 0 and slot_size is None:
        raise ValueError(f"nenhum terminador 0xFF a partir de {offset:#x}")
    if slot_size is None:
        return i - offset
    if slot_size < 2 or offset + slot_size > len(rom):
        raise ValueError(f"--slot-size {slot_size} inválido para offset {offset:#x}")
    primeiro_ff = i if i >= 0 else offset + slot_size
    pad = rom[primeiro_ff:offset + slot_size]
    if any(b not in (0x00, 0xFF) for b in pad):
        raise ValueError(
            "REGISTO VIVO: bytes além do 1º 0xFF dentro do passo declarado "
            "não são preenchimento 00/FF — abortando por segurança.")
    return slot_size


def aplicar_patch(rom: bytes, offset: int, expect_txt: str | None,
                  novo_txt: str, cs: CharsetPack, slot_size: int | None = None) -> dict:
    """Devolve dict com ROM nova + relatório, OU levanta ValueError."""
    slot = localizar_slot(rom, offset, slot_size)
    atual_txt = cs.decod(rom, offset, slot)

    if expect_txt is not None and atual_txt != expect_txt:
        raise ValueError(
            f"PRÉ-CONDIÇÃO FALHOU: slot contém '{atual_txt}', esperado "
            f"'{expect_txt}'. Nenhum byte foi alterado.")

    novo_raw = cs.enc(novo_txt)
    if len(novo_raw) > slot - 1:  # precisa sobrar 1 B para o terminador
        raise ValueError(
            f"texto codificado ocupa {len(novo_raw)}+1 B > slot de {slot} B; "
            f"encurte o texto (máx. {slot - 1} caracteres de 1 B).")

    nova = bytearray(rom)
    nova[offset:offset + slot] = novo_raw + bytes([TERMINADOR]) + \
        rom[offset + len(novo_raw) + 1:offset + slot]

    n_alter = sum(a != b for a, b in zip(rom, nova))
    return {
        "rom": bytes(nova),
        "rel": {
            "offset": f"0x{offset:x}",
            "slot_tamanho": slot,
            "antes_txt": atual_txt,
            "depois_txt": novo_txt,
            "antes_hex": rom[offset:offset + slot].hex(" "),
            "depois_hex": bytes(nova[offset:offset + slot]).hex(" "),
            "bytes_alterados_na_rom": n_alter,
        },
    }


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# --------------------------------------------------------------------------- #
# Self-test (ROM sintética — não depende da ROM real)
# --------------------------------------------------------------------------- #

def _espera_erro(fn, *args, exc=Exception, **kw):
    try:
        fn(*args, **kw)
    except exc:
        return True
    return False


def self_test(verbose: bool) -> int:
    cs = CharsetPack(None)
    base = bytearray(b"\x00" * 64)
    off, slot_tam = 16, 6
    raw = cs.enc("PIDGEY")
    base[off:off + slot_tam] = raw + bytes([TERMINADOR]) + b"\x00" * (slot_tam - len(raw) - 1)
    rom = bytes(base)
    falhas = 0

    def chk(nome, fn):
        nonlocal falhas
        ok = False
        try:
            ok = fn()
        except Exception as e:  # noqa: BLE001
            print(f"  [ERRO] {nome}: {e}")
        if verbose or not ok:
            print(f"  [{'PASS' if ok else 'FAIL'}] {nome}")
        falhas += 0 if ok else 1

    r = aplicar_patch(rom, off, "PIDGEY", "PIDG!", cs)
    chk("patch feliz: texto novo aplicado",
        lambda: cs.decod(r["rom"], off, slot_tam - 1) == "PIDG!")
    chk("patch feliz: bytes fora do slot intactos",
        lambda: r["rom"][:off] == rom[:off] and r["rom"][off + slot_tam:] == rom[off + slot_tam:])
    chk("patch feliz: ROM de entrada intacta",
        lambda: rom[off:off + len(raw)] == raw)
    chk("pré-condição errada ABORTA sem alterar",
        lambda: _espera_erro(aplicar_patch, rom, off, "ERRADO", "X", cs, exc=ValueError))
    chk("texto que não cabe no slot ABORTA",
        lambda: _espera_erro(aplicar_patch, rom, off, "PIDGEY", "PIDGEYY", cs, exc=ValueError))
    chk("slot-size fixo: padding 00/FF pode ser usado",
        lambda: aplicar_patch(rom, off, "PIDGEY", "PIDGEY!", cs, slot_size=8)
                ["rel"]["antes_txt"] == "PIDGEY")
    rom_vivo = bytearray(rom)
    rom_vivo[off + 7] = 0xC4   # byte "vivo" dentro do passo declarado
    chk("slot-size fixo: byte vivo no padding ABORTA",
        lambda: _espera_erro(aplicar_patch, bytes(rom_vivo), off, "PIDGEY", "X",
                             cs, slot_size=8, exc=ValueError))

    print(f"self-test: {7 - falhas}/7 verificações OK")
    return 1 if falhas else 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rom", nargs="?", type=Path)
    ap.add_argument("-o", "--out", type=Path, required=False)
    ap.add_argument("--offset", type=lambda s: int(s, 0))
    ap.add_argument("--expect", default=None,
                    help="texto esperado atualmente no slot (pré-condição)")
    ap.add_argument("--new-text", default=None)
    ap.add_argument("--slot-size", type=int, default=None,
                    help="passo fixo do registro (ex.: 11 p/ tabela de espécies); "
                         "sem ele o slot é medido até o 1º 0xFF")
    ap.add_argument("--charset-override", type=Path, default=DEFAULT_OVERRIDE,
                    help=f"padrão: {DEFAULT_OVERRIDE.name} (se existir)")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test(args.verbose)

    if args.rom is None or not args.rom.is_file():
        print("erro: ROM de entrada inexistente.", file=sys.stderr)
        return 2
    if args.out is None or args.offset is None or args.new_text is None:
        print("erro: forneça -o, --offset e --new-text (veja --help).", file=sys.stderr)
        return 2
    if args.rom.resolve() == args.out.resolve():
        print("RECUSADO: saída == entrada (in-place proibido; use uma cópia).",
              file=sys.stderr)
        return 2

    t0 = time.perf_counter()
    try:
        cs = CharsetPack(args.charset_override)
    except FileNotFoundError as e:
        print(f"erro: {e}", file=sys.stderr)
        return 2
    rom = args.rom.read_bytes()
    try:
        r = aplicar_patch(rom, args.offset, args.expect, args.new_text, cs,
                          slot_size=args.slot_size)
    except ValueError as e:
        print(f"ABORTADO: {e}", file=sys.stderr)
        return 3

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(r["rom"])
    rel = r["rel"]
    sha_in, sha_out = sha256(rom), sha256(r["rom"])
    override_usado = cs.usa_override.name if cs.usa_override else "(nenhum)"

    print("== PATCH DE TEXTO APLICADO ==")
    print(f"  charset: gba_poketext (override: {override_usado})")
    print(f"  slot @ {rel['offset']} (tamanho {rel['slot_tamanho']} B, direto 0xFF)")
    print(f"  texto: '{rel['antes_txt']}'  →  '{rel['depois_txt']}'")
    print(f"  hex antes : {rel['antes_hex']}")
    print(f"  hex depois: {rel['depois_hex']}")
    print(f"  bytes alterados na ROM inteira: {rel['bytes_alterados_na_rom']}")
    print(f"  SHA-256 entrada: {sha_in[:32]}…")
    print(f"  SHA-256 saída  : {sha_out[:32]}…   ({args.out})")
    print("  header intocado (região de dados) → checksum de header se mantém")

    logs = Path(__file__).resolve().parent.parent / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    with (logs / "gba_patch_text_runs.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "ferramenta": "gba_patch_text.py", "versao": VERSAO,
            "entrada": str(args.rom), "saida": str(args.out),
            "offset": rel["offset"], "expect": args.expect,
            "novo": args.new_text, "override": override_usado, "ok": True,
            "sha256_in_prefixo": sha_in[:16], "sha256_out_prefixo": sha_out[:16],
            "duracao_s": round(time.perf_counter() - t0, 3)},
            ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
