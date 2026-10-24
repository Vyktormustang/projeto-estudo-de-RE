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

    # criar/sobrescrever um Pokémon do time (precisa do --rom para ler os stats)
    savestate.py --rom R.gba --map X.map --offsets o.json --in S.bin --out T.bin \
        pokemon --slot 0 --species 700 --level 30 --moves 33 45

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


ROM_BASE = 0x08000000
STRIDE_SPECIESINFO = 28   # medido no ROM, não no compilador do host (offsets.py diz 26)
TAMANHO_BOXMON = 80
TAMANHO_POKEMON = 100

# `personality % 24` -> posição, dentro do bloco de 48 B, de cada substruct.
# Fonte: src/pokemon.c, GetSubstruct() (SUBSTRUCT_CASE) — não é ordem alfabética.
ORDEM_SUBSTRUCTS = [
    (0, 1, 2, 3), (0, 1, 3, 2), (0, 2, 1, 3), (0, 3, 1, 2), (0, 2, 3, 1), (0, 3, 2, 1),
    (1, 0, 2, 3), (1, 0, 3, 2), (2, 0, 1, 3), (3, 0, 1, 2), (2, 0, 3, 1), (3, 0, 2, 1),
    (1, 2, 0, 3), (1, 3, 0, 2), (2, 1, 0, 3), (3, 1, 0, 2), (2, 3, 0, 1), (3, 2, 0, 1),
    (1, 2, 3, 0), (1, 3, 2, 0), (2, 1, 3, 0), (3, 1, 2, 0), (2, 3, 1, 0), (3, 2, 1, 0),
]

# charmap do Gen 3 (só o que é preciso para nome de treinador/nickname ASCII).
def charmap_texto(txt) -> bytes:
    """Texto ASCII -> bytes do charmap do Gen 3 (aceita str ou bytes)."""
    if isinstance(txt, (bytes, bytearray)):
        return bytes(txt)
    saida = bytearray()
    for c in txt.upper():
        if "A" <= c <= "Z":
            saida.append(0xBB + ord(c) - ord("A"))
        elif "0" <= c <= "9":
            saida.append(0xA1 + ord(c) - ord("0"))
        elif c == " ":
            saida.append(0x00)
        else:
            raise SystemExit(f"caractere sem charmap: {c!r}")
    return bytes(saida)


def _xor_bloco(bloco: bytes, pid: int, otid: int) -> bytes:
    """Criptografia do BoxPokemon: cada u32 XOR (personality ^ otId)."""
    chave = pid ^ otid
    return b"".join(struct.pack("<I", struct.unpack_from("<I", bloco, i)[0] ^ chave)
                    for i in range(0, 48, 4))


def _checksum(bloco: bytes) -> int:
    return sum(struct.unpack_from("<24H", bloco)) & 0xFFFF


def _stats_nivel(base: tuple[int, ...], nivel: int, iv: int = 31) -> tuple[int, ...]:
    """Stats do Gen 3 com EV 0 e natureza neutra (pid=600 -> Hardy)."""
    hp = (2 * base[0] + iv) * nivel // 100 + nivel + 10
    outros = [(2 * b + iv) * nivel // 100 + 5 for b in base[1:]]
    return (hp, *outros)


def montar_pokemon(especie: int, nivel: int, golpes: list[int], base: tuple[int, ...],
                   nome: bytes, pid: int = 600, otid: int = 0x12345678,
                   ot: str = "ARENA") -> bytes:
    """Monta os 100 bytes de `struct Pokemon` válidos (checksum incluso).

    `base` são os 6 stats base na ordem do `struct SpeciesInfo`
    (HP, Attack, Defense, Speed, SpAttack, SpDefense).
    """
    if len(golpes) > 4:
        raise SystemExit("no máximo 4 golpes")
    if len(nome) > 10:
        raise SystemExit("nickname com mais de 10 bytes")
    moves = list(golpes) + [0] * (4 - len(golpes))
    pp = [40 if m else 0 for m in moves]

    # Substruct 0 (Growth): species, heldItem, exp, ppBonuses, friendship, filler
    exp = min(nivel ** 3, 0xFFFFFFFF)
    growth = struct.pack("<HHI B B H", especie, 0, exp, 0, 70, 0)
    # Substruct 1 (Attacks)
    attacks = struct.pack("<4H4B", *moves, *pp)
    # Substruct 2 (EVs/contest)
    evs = bytes(12)
    # Substruct 3 (Misc): pokerus, metLocation, metLevel|metGame|pokeball|otGender, IVs, ribbons
    meta = (nivel & 0x7F) | (3 << 7) | (4 << 11) | (0 << 15)   # game 3 = FRLG, ball 4 = Poké
    ivs = 0x3FFFFFFF          # 31 em cada um dos 6 IVs; isEgg=0, abilityNum=0
    misc = struct.pack("<BBHII", 0, 0, meta, ivs, 0)

    canonico = growth + attacks + evs + misc
    ordem = ORDEM_SUBSTRUCTS[pid % 24]
    bloco = bytearray(48)
    for tipo in range(4):
        bloco[ordem[tipo] * 12:(ordem[tipo] + 1) * 12] = canonico[tipo * 12:(tipo + 1) * 12]

    perm = [0] * 24
    for tipo in range(4):
        perm[ordem[tipo]] = tipo
    assert sorted(perm[:4]) == [0, 1, 2, 3], "permutação inválida"

    box = bytearray()
    box += struct.pack("<II", pid, otid)
    box += nome.ljust(10, b"\xFF")[:10]
    box += bytes([2])                 # language = ENGLISH
    box += bytes([0x02])              # hasSpecies
    box += charmap_texto(ot).ljust(7, b"\xFF")[:7]
    box += bytes([0])                 # markings
    box += struct.pack("<HH", _checksum(bytes(bloco)), 0)
    box += _xor_bloco(bytes(bloco), pid, otid)
    assert len(box) == TAMANHO_BOXMON

    stats = _stats_nivel(base, nivel)
    mon = bytes(box) + struct.pack("<IBB7H", 0, nivel, 0, stats[0], stats[0],
                                   *stats[1:])
    assert len(mon) == TAMANHO_POKEMON
    return mon


def ler_pokemon(mon: bytes) -> dict:
    """Decripta um `struct Pokemon` e devolve species/golpes/level/stats."""
    pid, otid = struct.unpack_from("<II", mon, 0)
    bloco = _xor_bloco(mon[0x20:0x50], pid, otid)
    ordem = ORDEM_SUBSTRUCTS[pid % 24]
    canonico = b"".join(bloco[ordem[t] * 12:(ordem[t] + 1) * 12] for t in range(4))
    especie = struct.unpack_from("<H", canonico, 0)[0]
    golpes = list(struct.unpack_from("<4H", canonico, 12))
    nivel = mon[0x54]
    hp = struct.unpack_from("<H", mon, 0x56)[0]
    return {
        "especie": especie,
        "golpes": [g for g in golpes if g],
        "nivel": nivel,
        "hp": hp,
        "maxhp": struct.unpack_from("<H", mon, 0x58)[0],
        "checksum_ok": _checksum(bloco) == struct.unpack_from("<H", mon, 0x1C)[0],
    }


class Estado:
    def __init__(self, dados: bytes, mapa: Path):
        self.d = bytearray(dados)
        self.sym = simbolos_do_map(mapa, ["gSaveBlock1Ptr", "gSaveBlock2Ptr",
                                          "gPlayerParty", "gPlayerPartyCount",
                                          "gEnemyParty"])
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
        # gPlayerPartyCount é uma global de EWRAM; o campo homônimo do SaveBlock1
        # só é preenchido no SavePlayerParty (salvar o jogo). Ler o do SaveBlock
        # dava 0 e o menu START escondia o item POKéMON.
        return self.d[self.regiao("gPlayerPartyCount")]

    def time(self, qtd: int) -> list[dict]:
        base = self.regiao("gPlayerParty")
        return [ler_pokemon(bytes(self.d[base + i * TAMANHO_POKEMON:
                                   base + (i + 1) * TAMANHO_POKEMON])) for i in range(qtd)]

    def inimigo(self, qtd: int = 1) -> list[dict]:
        base = self.regiao("gEnemyParty")
        return [ler_pokemon(bytes(self.d[base + i * TAMANHO_POKEMON:
                                   base + (i + 1) * TAMANHO_POKEMON])) for i in range(qtd)]

    def escrever_pokemon(self, slot: int, mon: bytes) -> None:
        base = self.regiao("gPlayerParty")
        if len(mon) != TAMANHO_POKEMON:
            raise SystemExit(f"Pokémon com {len(mon)} B (esperado {TAMANHO_POKEMON})")
        self.d[base + slot * TAMANHO_POKEMON:base + (slot + 1) * TAMANHO_POKEMON] = mon
        cont = self.regiao("gPlayerPartyCount")
        if self.d[cont] < slot + 1:
            self.d[cont] = slot + 1

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

    def set_var(self, var_id: int, valor: int, off: dict) -> None:
        """Reescreve uma variável de script (u16). Aceita só vars de evento."""
        if not 0x4000 <= var_id < 0x4000 + 0x100:
            raise SystemExit(f"var 0x{var_id:04X} fora da faixa de evento (0x4000+)")
        struct.pack_into("<H", self.d, self.s1 + off["s1_vars"] + (var_id - 0x4000) * 2, valor)

    def set_nacional(self, off: dict) -> None:
        """Liga a Pokédex nacional: as três condições de IsNationalPokedexEnabled.

        `src/event_data.c` exige `pokedex.nationalMagic == 0xB9`,
        `VarGet(VAR_NATIONAL_DEX) == 0x6258` e `FLAG_SYS_NATIONAL_DEX`.
        """
        self.set_flag(0x829, True, off)          # FLAG_SYS_POKEDEX_GET
        self.set_flag(0x840, True, off)          # FLAG_SYS_NATIONAL_DEX
        self.d[self.s2 + off["s2_pokedex"] + 3] = 0xB9
        self.set_var(0x404E, 0x6258, off)        # VAR_NATIONAL_DEX

    def dados_do_jogador(self, off: dict) -> tuple[int, bytes]:
        """(otId, nome) do jogador — para o Pokémon não ser "de troca"."""
        base = self.s2 + off["s2_playerName"]
        fim = base
        while fim < base + 7 and self.d[fim] != 0xFF:
            fim += 1
        nome = bytes(self.d[base:fim])
        otid = struct.unpack_from("<I", self.d, self.s2 + off["s2_playerTrainerId"])[0]
        return otid, nome

    def get_flag(self, num: int, off: dict) -> bool:
        base = self.s1 + off["s1_flags"]
        return bool(self.d[base + num // 8] & (1 << (num % 8)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default="", help="ROM (para pokemon: stats base/nome)")
    ap.add_argument("--self-test", dest="self_test", action="store_true")
    # não são required no argparse: --self-test precisa rodar sem eles
    ap.add_argument("--map", default="")
    ap.add_argument("--offsets", default="", help="JSON gerado por offsets.py")
    ap.add_argument("--in", dest="entrada", default="")
    ap.add_argument("--out", dest="saida", default="")
    sub = ap.add_subparsers(dest="cmd", required=False)

    sub.add_parser("info")
    p_party = sub.add_parser("party")
    p_party.add_argument("--inimigo", "-e", action="store_true",
                         help="lê gEnemyParty em vez do time do jogador")
    p_dex = sub.add_parser("dex", help="marca espécies na Pokédex")
    p_dex.add_argument("nums", nargs="+", type=int)
    p_dex.add_argument("--no-caught", action="store_true")

    p_nac = sub.add_parser("nacional", help="liga a Pokédex nacional (flag + magic + var)")
    p_nac.set_defaults(sem_extra=True)

    p_flag = sub.add_parser("flag")
    p_flag.add_argument("--set", dest="ligar", nargs="*", type=lambda s: int(s, 0))
    p_flag.add_argument("--clear", dest="desligar", nargs="*", type=lambda s: int(s, 0))

    p_var = sub.add_parser("var", help="escreve uma variável de script")
    p_var.add_argument("--id", type=lambda s: int(s, 0), required=True)
    p_var.add_argument("--valor", type=lambda s: int(s, 0), required=True)

    p_mon = sub.add_parser("pokemon", help="cria/sobrescreve um Pokémon do time")
    p_mon.add_argument("--slot", type=int, default=0)
    p_mon.add_argument("--species", type=lambda s: int(s, 0), required=True)
    p_mon.add_argument("--level", type=int, default=20)
    p_mon.add_argument("--moves", nargs="*", type=lambda s: int(s, 0), default=[])
    p_mon.add_argument("--pid", type=lambda s: int(s, 0), default=600)
    p_mon.add_argument("--outsider", action="store_true",
                       help="usa OT de outro treinador (o Pokémon desobedece)")

    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.entrada or not a.cmd:
        raise SystemExit("precisa de --in e de um comando (ou use --self-test)")
    if not a.map or not a.offsets:
        raise SystemExit("precisa de --map e --offsets (ou use --self-test)")
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
        print(f"nationalMagic  : 0x{est.d[est.s2 + off['s2_pokedex'] + 3]:02X}")
        var = struct.unpack_from("<H", est.d, est.s1 + off["s1_vars"] + (0x404E - 0x4000) * 2)[0]
        print(f"VAR_NATIONAL_DEX: 0x{var:04X}")
        return 0

    if a.cmd == "party":
        qtd = est.contagem_time() if not a.inimigo else 1
        print(f"{'inimigo' if a.inimigo else 'time'}: {qtd} mon(s)")
        for i, m in enumerate(est.inimigo(a.inimigo) if a.inimigo else est.time(qtd)):
            ok = "checksum ok" if m["checksum_ok"] else "CHECKSUM RUIM"
            print(f"  slot {i}: especie {m['especie']} nivel {m['nivel']} "
                  f"hp {m['hp']}/{m['maxhp']} golpes {m['golpes']} ({ok})")
        return 0

    if a.cmd == "pokemon":
        if not a.rom:
            raise SystemExit("o comando pokemon precisa de --rom (stats base e nome saem do ROM)")
        rom = Path(a.rom).read_bytes()
        sym = simbolos_do_map(Path(a.map), ["gSpeciesInfo", "gSpeciesNames"])
        base_off = sym["gSpeciesInfo"] - ROM_BASE
        info = rom[base_off + a.species * STRIDE_SPECIESINFO:
                   base_off + (a.species + 1) * STRIDE_SPECIESINFO]
        if len(info) != STRIDE_SPECIESINFO:
            raise SystemExit(f"espécie {a.species} fora da tabela")
        base = tuple(info[:6])
        if base[0] == 0:
            raise SystemExit(f"espécie {a.species} tem stats zerados no ROM")
        # gSpeciesNames é u8[][11] (não tabela de ponteiros): conferido no ROM
        inicio = sym["gSpeciesNames"] - ROM_BASE + a.species * 11
        fim = rom.index(b"\xFF", inicio, inicio + 11)
        nome = rom[inicio:fim][:10]
        # Pokémon "de troca" (OT diferente) desobedece acima do nível permitido
        # pelas insígnias — o Sylveon nível 30 ignorou as ordens em batalha.
        if a.outsider:
            otid, ot = 0x12345678, charmap_texto("ARENA")
        else:
            otid, ot = est.dados_do_jogador(off)
        mon = montar_pokemon(a.species, a.level, a.moves or [], base, nome,
                             pid=a.pid, otid=otid, ot=ot)
        est.escrever_pokemon(a.slot, mon)
        # receber o primeiro Pokémon liga FLAG_SYS_POKEMON_GET (0x828); sem ela o
        # menu START esconde o item POKéMON (src/start_menu.c:217)
        est.set_flag(0x828, True, off)
        lido = ler_pokemon(mon)
        print(f"slot {a.slot}: espécie {lido['especie']} nível {lido['nivel']} "
              f"HP {lido['hp']} golpes {lido['golpes']} "
              f"({'checksum ok' if lido['checksum_ok'] else 'CHECKSUM RUIM'})")

    if a.cmd == "dex":
        est.set_flag(0x829, True, off)   # sem FLAG_SYS_POKEDEX_GET o item nem aparece no menu
        est.marcar_dex(a.nums, visto=True, capturado=not a.no_caught, off=off)
        print(f"{len(a.nums)} espécies marcadas na Pokédex: {a.nums[:8]}"
              f"{' ...' if len(a.nums) > 8 else ''}")
    elif a.cmd == "nacional":
        est.set_nacional(off)
        print("Pokédex nacional ligada (flag 0x829/0x840, nationalMagic 0xB9, VAR 0x404E=0x6258)")
    elif a.cmd == "var":
        est.set_var(a.id, a.valor, off)
        print(f"VAR 0x{a.id:04X} = 0x{a.valor:04X}")
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


def self_test() -> int:
    """Monta/desmonta um Pokémon e confere checksum, golpes, stats e ordem."""
    base = (95, 65, 65, 60, 110, 130)      # Sylveon
    nome = charmap_texto("SYLVEON")
    mon = montar_pokemon(700, 30, [33, 45], base, nome)
    d = ler_pokemon(mon)
    assert len(mon) == TAMANHO_POKEMON, len(mon)
    assert d["especie"] == 700 and d["nivel"] == 30, d
    assert d["golpes"] == [33, 45], d
    assert d["checksum_ok"], "checksum não bate"
    # stats: HP=(190+31)*30//100+30+10=106; Atk=(130+31)*30//100+5=53
    assert d["maxhp"] == 106 and d["hp"] == 106, d
    assert struct.unpack_from("<H", mon, 0x5A)[0] == 53
    assert struct.unpack_from("<H", mon, 0x60)[0] == 80   # SpAtk
    # qualquer PID: a permutação tem de devolver os mesmos campos
    for pid in (0, 1, 5, 7, 23, 24, 600, 0xDEADBEEF):
        m = montar_pokemon(700, 30, [33, 45], base, nome, pid=pid)
        l = ler_pokemon(m)
        assert l["especie"] == 700 and l["golpes"] == [33, 45] and l["checksum_ok"], (pid, l)
    # ordem das substructs: as 24 permutações têm de ser válidas e distintas
    assert len(set(ORDEM_SUBSTRUCTS)) == 24
    for p in ORDEM_SUBSTRUCTS:
        assert sorted(p) == [0, 1, 2, 3]
    print("self-test ok: montagem/leitura de Pokémon, checksum e 24 ordens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
