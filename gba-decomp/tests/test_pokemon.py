"""Decifragem da caixa do Pokemon provada em dois especimes REAIS.

Os dois buffers de 100 bytes abaixo sao o Bulbasaur inicial lido da RAM
(0x02024284) em duas execucoes diferentes da ferramenta ir_ao_inicial.py
(2026-10-20, §20): "venceu" = execucao do boot (nv6, subiu na batalha do
rival); "perdeu" = execucao em etapas (nv5, EXP intocado em 135 -> perdeu
e foi curado). Sem emulador: sao bytes publicos do NOSSO save.
"""

from gbadecomp.pokemon import (
    BASES_CONHECIDAS, exp_minima_medio_lento, ler_pokemon,
)

VENCEU = bytes.fromhex(
    "c83aad5ddbd3bc10bbffffffffffffffffff0202bbffffffffffff0072560000"
    "32e93c4d13e9114d30c1114d13e9114c13e9114d13e9114d12e9114ddfe9114"
    "d13a5114d13b1146f40d8cd7913e9114d0000000006ff160016000b000b00"
    "0c000d000c00")
PERDEU = bytes.fromhex(
    "f48e6bb8dbd3bc10bbffffffffffffffffff0202bbffffffffffff0071330000"
    "2f05d28a481cdba22f5dd7a80e5dfaa82f5dd7a80c75d7a82e5dd7a8a85dd7"
    "a82f18d7a82f5dd7a82f5dd7a82f5dd7a80000000005ff130013000a000a00"
    "09000c000b00")


def test_checksum_bate_nos_dois():
    assert ler_pokemon(VENCEU).integro()
    assert ler_pokemon(PERDEU).integro()


def test_campos_decifrados_batem_com_o_jogo():
    venceu, perdeu = ler_pokemon(VENCEU), ler_pokemon(PERDEU)
    for mon in (venceu, perdeu):
        assert mon.especie == 1                      # Bulbasaur
        assert mon.golpes == (33, 45, 0, 0)          # Tackle, Growl
        assert mon.pps == (35, 40, 0, 0)
        assert mon.apelido_bruto[0] == 0xBB          # "A" (nao cifrado)
    assert (venceu.nivel, venceu.experiencia) == (6, 204)
    assert (perdeu.nivel, perdeu.experiencia) == (5, 135)
    for mon in (venceu, perdeu):
        assert exp_minima_medio_lento(mon.nivel) <= mon.experiencia \
            < exp_minima_medio_lento(mon.nivel + 1)


def test_evidencia_da_batalha_fica_nos_dados():
    venceu, perdeu = ler_pokemon(VENCEU), ler_pokemon(PERDEU)
    # derrotar um Charmander rende 1 EV de velocidade; perder, nada
    assert venceu.evs == (0, 0, 0, 1, 0, 0)
    assert perdeu.evs == (0, 0, 0, 0, 0, 0)
    assert venceu.ivs == (19, 10, 12, 24, 13, 26)
    assert perdeu.ivs == (7, 11, 16, 24, 0, 5)


def test_atributos_gravados_pelo_jogo_recomputam_dos_ivs():
    for bruto in (VENCEU, PERDEU):
        mon = ler_pokemon(bruto)
        hp_max, *stats = mon.recalcular(BASES_CONHECIDAS[mon.especie])
        assert hp_max == mon.hp[1]
        assert tuple(stats) == mon.atributos


def test_serializar_sem_editar_e_byte_identico():
    for bruto in (VENCEU, PERDEU):
        assert ler_pokemon(bruto).serializar() == bruto


def test_definir_golpe_recifra_e_preserva_o_resto():
    mon = ler_pokemon(VENCEU)
    antes = (mon.especie, mon.experiencia, mon.ivs, mon.evs, mon.nivel)
    mon.definir_golpe(2, 73, 10)                      # slot vazio -> golpe 73
    assert mon.integro()                              # checksum refeito
    relido = ler_pokemon(mon.serializar())
    assert relido.golpes == (33, 45, 73, 0)
    assert relido.pps == (35, 40, 10, 0)
    assert (relido.especie, relido.experiencia, relido.ivs,
            relido.evs, relido.nivel) == antes
    # so' mudam checksum e a regiao segura; cabecalho e extras intactos
    novo = mon.serializar()
    assert novo[:0x1C] == VENCEU[:0x1C]
    assert novo[0x1E:0x20] == VENCEU[0x1E:0x20]
    assert novo[0x50:] == VENCEU[0x50:]


def test_definir_experiencia_e_ivs_recifra_e_preserva_o_resto():
    mon = ler_pokemon(VENCEU)
    antes = (mon.especie, mon.golpes, mon.pps, mon.evs, mon.nivel,
             mon.hp, mon.atributos)
    mon.definir_experiencia(560)
    mon.definir_ivs((31, 31, 31, 31, 31, 31))
    assert mon.integro()
    relido = ler_pokemon(mon.serializar())
    assert relido.experiencia == 560
    assert relido.ivs == (31, 31, 31, 31, 31, 31)
    assert (relido.especie, relido.golpes, relido.pps, relido.evs,
            relido.nivel, relido.hp, relido.atributos) == antes


def test_sincronizar_nivel_10_recalcula_hp_e_atributos():
    mon = ler_pokemon(VENCEU)
    mon.definir_experiencia(exp_minima_medio_lento(10))
    mon.definir_ivs((31, 31, 31, 31, 31, 31))
    mon.sincronizar_nivel_atributos(10, BASES_CONHECIDAS[mon.especie])
    assert mon.integro()
    assert mon.nivel == 10
    assert mon.experiencia == 560
    assert mon.hp == (32, 32)
    # natureza 14: +Velocidade, -Def.Especial
    assert mon.atributos == (17, 17, 18, 21, 18)
    assert mon.recalcular(BASES_CONHECIDAS[mon.especie]) == (
        mon.hp[1], *mon.atributos)
    assert mon.golpes == (33, 45, 0, 0)
    assert mon.evs == (0, 0, 0, 1, 0, 0)
