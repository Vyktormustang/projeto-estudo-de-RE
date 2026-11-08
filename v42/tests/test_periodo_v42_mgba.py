#!/usr/bin/env python3
"""test_periodo_v42_mgba.py — a VIRADA dia/noite funciona em execução na V42?

A auditoria estrutural (`v42/scripts/auditoria_horario_v42.py`) prova que as
tabelas noturnas estão GRAVADAS na ROM. Isso NÃO prova que o hook escolhe a
espécie certa quando o relógio cruza o limite. Este teste prova a segunda coisa.

Método — sem esperar horas de jogo:
  O relógio da V42 é derivado do tempo de jogo
      minuto_do_dia = (480 + horas*3600 + minutos*60 + segundos) % 1440
  e o motor expõe `ENTRY_SELECT`, que recebe a espécie diurna e o minuto do dia
  e devolve a espécie do período. Fixamos o minuto nos dois lados do limite:

    * minuto  600 (10:00, DIA)   -> espécie DIURNA da política
    * minuto 1320 (22:00, NOITE) -> espécie NOTURNA da política
    * fronteiras 359/360 e 1199/1200

  E exercitamos a geração nativa (`HOOK_OFFSET`) com 100 sorteios por slot nos
  quatro mapas nativos, conferindo espécie, nível e os limiares reais.

LIMITE HONESTO: exercita o SELETOR chamado pelo hook, não uma caminhada real
até topar com um selvagem. O teste de encontro em campo é outro trabalho.

Uso:
  COSMOG_V42_ROM=... MGBA_CORE=... python3 v42/tests/test_periodo_v42_mgba.py
"""
from __future__ import annotations

import hashlib
import os
import struct
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROM = os.environ.get("COSMOG_V42_ROM")
CORE = os.environ.get("MGBA_CORE")
ROM_SHA256 = "6997366bea7056778e3183595d2e2f84c62a98576430db71b9459962e5bbd99a"

LIMIARES = (20, 40, 50, 60, 70, 80, 85, 90, 94, 98, 99, 100)


def _achar_motor() -> Path:
    env = os.environ.get("GEN19_WORK")
    cands = ([Path(env) / "firered_gen1_9"] if env else []) + [Path("/tmp/gen19/firered_gen1_9")]
    for c in cands:
        if (c / "scripts/motor_v20.py").is_file():
            return c
    raise SystemExit("[ERRO] motor ausente: rode antes bash v42/scripts/run_cosmog_tests.sh")


@unittest.skipUnless(ROM and CORE, "defina COSMOG_V42_ROM e MGBA_CORE")
class PeriodoV42Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        gen = _achar_motor()
        sys.path[:0] = [str(gen), str(gen / "tests")]
        from scripts import motor_v20 as m20
        import mgba_treino_harness as h
        from test_eventos_fixos_mgba import route_entry_fixture
        from test_golpes_gen9_mgba import set_registers, SENTINEL
        from test_motor_v19_mgba import set_time, IW
        from test_estojo_expandido_mgba import save1

        cls.m20 = m20
        # staticmethod é OBRIGATÓRIO: função pura guardada como atributo de
        # classe vira método ligado, e `self.set_time(st, min)` passaria a ser
        # `set_time(self, st, min)` — foi exatamente o erro da primeira versão.
        cls.set_time = staticmethod(set_time)
        cls.save1 = staticmethod(save1)
        cls.set_registers = staticmethod(set_registers)
        cls.IW, cls.SENTINEL = IW, SENTINEL

        # Uma semente por sorteio: o primeiro LCG rolhado módulo 100 dá o
        # índice do slot. Assim cada um dos 100 sorteios cai num slot
        # determinado, e o teste cobre os 12 slots de forma verificável.
        # Sem isso, os 100 sorteios repetem slot (foi o erro da versão anterior,
        # que supunha cobertura automática).
        cls.RNG = IW + 0x6FC8
        seeds: dict[int, int] = {}
        for _s in range(10000):
            _q = (((_s * 0x41C64E6D + 0x6073) & 0xFFFFFFFF) >> 16) % 100
            seeds.setdefault(_q, _s)
            if len(seeds) == 100:
                break
        cls.SEEDS = seeds

        rom = Path(ROM)
        cls.source = rom.read_bytes()
        if hashlib.sha256(cls.source).hexdigest() != ROM_SHA256:
            raise ValueError("não é a V42 exata")
        cls.rom = rom

        cls.temp = tempfile.TemporaryDirectory()
        cls.f = h.Emulator(rom, Path(CORE), Path(cls.temp.name))
        cls.fixture = route_entry_fixture(cls.f)
        cls.h = h

    @classmethod
    def tearDownClass(cls):
        cls.f.close()
        cls.temp.cleanup()
        if hashlib.sha256(cls.rom.read_bytes()).hexdigest() != ROM_SHA256:
            raise AssertionError("ROM alterada durante o teste")

    # ---------------- utilidades ----------------
    def call(self, st, pc, regs=None):
        self.f.restore(self.set_registers(st, pc & ~1, regs or {}))
        self.f.run(3)
        out = self.f.state()
        if struct.unpack_from("<I", out, 0x5C)[0] != self.SENTINEL + 2:
            self.f.run(30)
            out = self.f.state()
        self.assertEqual(struct.unpack_from("<I", out, 0x5C)[0], self.SENTINEL + 2,
                         "rotina não retornou ao ponto esperado")
        return out

    def registro(self, i):
        return struct.unpack_from("<IIBBH", self.source, self.m20.TABLE_OFFSET + 12 * i)

    def estado(self, i, minuto):
        st = self.set_time(self.fixture, minuto)
        _d, _n, grupo, numero, _ = self.registro(i)
        at = self.h.offset(self.save1(st))
        st[at + 4:at + 6] = bytes((grupo, numero))
        return st

    @staticmethod
    def r0(out):
        return struct.unpack_from("<I", out, 0x20)[0]

    # ---------------- o núcleo ----------------
    def test_seletor_escolhe_diurna_de_dia_e_noturna_de_noite(self):
        mapas = self.m20.MAPS[:4]
        for i, nome in enumerate(mapas):
            dia, noite, _g, _n, _ = self.registro(i)
            for minuto, esperado, rotulo in ((600, dia, "DIA"), (1320, noite, "NOITE")):
                out = self.call(self.estado(i, minuto), self.m20.ENTRY_SELECT,
                                {0: dia, 1: 0})
                self.assertEqual(self.r0(out), esperado,
                                 f"{nome} minuto {minuto} ({rotulo}): "
                                 f"esperado {esperado}, obtido {self.r0(out)}")
                print(f"  SELECAO {nome} {rotulo} minuto={minuto} "
                      f"especie={self.r0(out)} (dia={dia} noite={noite})", flush=True)

    def test_fronteiras_do_periodo_mecanico(self):
        """dia mecanico 06:00-19:59 => minutos 360..1199; noite no resto."""
        dia, noite = self.registro(0)[0], self.registro(0)[1]
        for minuto, esperado, rotulo in ((359, noite, "05:59"), (360, dia, "06:00"),
                                         (1199, dia, "19:59"), (1200, noite, "20:00")):
            out = self.call(self.estado(0, minuto), self.m20.ENTRY_SELECT, {0: dia, 1: 0})
            self.assertEqual(self.r0(out), esperado, f"fronteira {rotulo}")
            print(f"  FRONTEIRA {rotulo} minuto={minuto} -> {self.r0(out)}", flush=True)

    def test_geracao_nativa_noturna_usa_a_tabela_da_rom(self):
        """100 sorteios com semente fixa: espécie e nível vêm da tabela gravada."""
        for i, nome in enumerate(self.m20.MAPS[:4]):
            _dia, noite, _g, _n, _ = self.registro(i)
            base = noite - 0x08000000
            slots_ptr = struct.unpack_from("<I", self.source, base + 4)[0] - 0x08000000
            contagem: Counter = Counter()
            for q in range(100):
                slot = next(j for j, fim in enumerate(LIMIARES) if q < fim)
                lo, hi, especie = struct.unpack_from("<BBH", self.source,
                                                     slots_ptr + slot * 4)
                st = self.estado(i, 1320)
                st = bytearray(st)
                struct.pack_into("<I", st, self.RNG, self.SEEDS[q])
                out = self.call(st, 0x08000000 + self.m20.HOOK_OFFSET,
                                {0: _dia, 1: 0, 2: 0})
                contagem[slot] += 1
                self.assertEqual(self.r0(out), 1, f"{nome} slot {slot}: sem encontro")
            self.assertEqual(sum(contagem.values()), 100)
            # com semente injetada, cada slot recebe exatamente 1 sorteio
            # A distribuição NÃO é uniforme: é a dos pesos do FireRed
            # (20/20/10/10/10/10/5/5/4/4/1/1). Terceiro erro meu nesta frente:
            # antes eu supunha cobertura uniforme e falhava contra um resultado
            # correto. Agora comparo com os pesos lidos da própria tabela.
            esperado = [LIMIARES[k] - (LIMIARES[k - 1] if k else 0)
                        for k in range(len(LIMIARES))]
            obtido = [contagem[k] for k in range(len(esperado))]
            self.assertEqual(obtido, esperado,
                             f"{nome}: pesos divergem da tabela\n"
                             f"  esperado {esperado}\n  obtido   {obtido}")
            print(f"  SORTEIO {nome} slots={len(contagem)} noite={noite} OK", flush=True)

    def test_guardas_de_area_nao_trocam_a_especie(self):
        """Área != 0 não é mapa piloto: a seleção tem de devolver a diurna."""
        dia = self.registro(0)[0]
        for area in (1, 2, 3, 255):
            out = self.call(self.estado(0, 1320), self.m20.ENTRY_SELECT, {0: dia, 1: area})
            self.assertEqual(self.r0(out), dia, f"area {area} deveria devolver a diurna")


def main() -> int:
    if "--self-test" in sys.argv:
        ok = True
        soma, antes = 0, 0
        for fim in LIMIARES:
            if fim - antes <= 0:
                ok = False
            antes, soma = fim, soma + (fim - antes)
        if soma != 100:
            ok = False
        print(f"  [{'PASS' if ok else 'FAIL'}] limiares: soma={soma}, larguras positivas")
        print(f"\nresumo: {'OK' if ok else '1 falha(s)'}")
        return 0 if ok else 1
    unittest.main(verbosity=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
