#!/usr/bin/env python3
"""Scripts de batalha novos para a ROM identificada por atualizacoes_gen9.

O bytecode segue o interpretador FireRed da própria ROM. Não pretende portar
as regras completas de batalha de Scarlet/Violet. Não lê nem grava saves.
"""
from __future__ import annotations

import struct

SCRIPT_TABLE = 0x185050
MOVE_TABLE = 0x696F70
SCRIPT_START = 0xE03FD0
SCRIPT_END = 0xE04400
ROM_START = 0x08000000
MOVE_COUNT = 797

# Efeitos da própria ROM reaproveitados para golpes antes reduzidos a dano puro.
# (ID interno, efeito, chance secundária). Não são mecânicas Gen 9 completas.
NATIVE_EFFECTS = (
    (489, 70, 100), (551, 71, 100),  # Low Sweep, Snarl
    (428, 31, 20), (127, 31, 20),   # Zen Headbutt, Waterfall
    (398, 2, 30), (430, 72, 10), (399, 31, 20), (441, 31, 30),
    (440, 2, 30), (656, 69, 20), (412, 72, 10), (579, 68, 10),
    (414, 72, 10), (411, 72, 10), (405, 72, 10), (634, 68, 100),
    (502, 4, 30), (523, 70, 100), (481, 2, 10), (707, 71, 100),
    (689, 68, 100), (538, 76, 30), (409, 3, 0),
    (421, 43, 0), (525, 43, 0), (443, 43, 0), (396, 17, 0),
    (436, 204, 100),  # Leaf Storm: redução garantida de Sp. Atk
)

# Alguns poderes e precisão modernos, globais ao golpe; PP é preservado para
# não criar incompatibilidade com Pokémon já salvos. Restantes não auditados.
# (ID interno, poder antigo, poder novo, precisão antiga, precisão nova)
POWER_CHANGES = (
    (168, 40, 60, 100, 100), (317, 50, 60, 80, 95), (314, 55, 60, 95, 95),
    (141, 20, 80, 100, 100), (202, 60, 75, 100, 100), (57, 95, 90, 100, 100),
    (53, 95, 90, 100, 100), (85, 95, 90, 100, 100), (58, 95, 90, 100, 100),
    (126, 120, 110, 85, 85), (56, 120, 110, 80, 80),
    (59, 120, 110, 70, 70), (87, 120, 110, 70, 70),
)


class BattleScript:
    def __init__(self, base: int):
        self.base = base
        self.data = bytearray()
        self.labels: dict[str, int] = {}
        self.fixups: list[tuple[int, str]] = []

    def label(self, name: str):
        if name in self.labels:
            raise ValueError(f"Rótulo repetido: {name}")
        self.labels[name] = len(self.data)

    def emit(self, *values: int):
        self.data.extend(values)

    def ptr(self, target: int | str):
        if isinstance(target, str):
            self.fixups.append((len(self.data), target))
            self.data.extend(bytes(4))
        else:
            self.data.extend(struct.pack('<I', target))

    def jumpifstat(self, battler: int, comparison: int, stat: int, value: int, target: int | str):
        self.emit(0x20, battler, comparison, stat, value)
        self.ptr(target)

    def setbyte(self, address: int, value: int):
        self.emit(0x2E)
        self.ptr(address)
        self.emit(value)

    def goto(self, target: int):
        self.emit(0x28)
        self.ptr(target)

    def finish(self) -> bytes:
        for offset, name in self.fixups:
            struct.pack_into('<I', self.data, offset, ROM_START + self.base + self.labels[name])
        return bytes(self.data)


def stages(base: int, stats: tuple[tuple[int, int], ...], lower: bool = False) -> bytes:
    """Altera atributos; análogo aos scripts nativos de Bulk Up/Tickle.

    stat = 1 ATK, 2 DEF, 3 SPEED, 4 SPATK, 5 SPDEF, 6 ACC. Os limites
    são os estágios internos 0..12, com 6 neutro; stats têm o mesmo sinal.
    """
    s = BattleScript(base)
    battler = 0 if lower else 1
    s.emit(0x00, 0x02, 0x03)  # attackcanceler, attackstring, ppreduce
    for stat, _ in stats[:-1]:
        s.jumpifstat(battler, 2 if lower else 3, stat, 0 if lower else 12, 'animate')
    s.jumpifstat(battler, 0, stats[-1][0], 0 if lower else 12,
                 0x08186F41 if lower else 0x0818708F)
    s.label('animate')
    if lower:
        s.emit(0x01)  # accuracycheck, current move
        s.ptr(0x0818689A)
        s.emit(0, 0)
    s.emit(0x09, 0x0A)  # attackanimation, waitanimation
    s.setbyte(0x02021823, 0)
    mask = sum(1 << stat for stat, _ in stats)
    s.emit(0x48, battler, mask, 5 if lower else 0)
    for i, (stat, delta) in enumerate(stats):
        if lower:
            s.emit(0x48, battler, 1 << stat, 1)
        s.setbyte(0x02021822, stat | (delta << 4) | (0x80 if lower else 0))
        s.emit(0x89, 0x01 if lower else 0x41)
        s.ptr(f'next{i}')
        s.emit(0x29, 0x00)  # jumpifbyte CMP_EQUAL, MULTISTRING_CHOOSER, 2
        s.ptr(0x020216C5)
        s.emit(2)
        s.ptr(f'next{i}')
        s.emit(0x13)  # printfromtable
        s.ptr(0x082085AC if lower else 0x082085A0)
        s.emit(0x12, 0x40, 0)  # waitmessage
        s.label(f'next{i}')
    s.goto(0x081853F6)  # fluxo de fim de movimento do jogo
    return s.finish()


def damage_with_effects(rom: bytes, base: int, effects: tuple[int, ...]) -> bytes:
    """Dano nativo mais duas rolagens/efeitos, sem alterar outros movimentos."""
    s = BattleScript(base)
    # Trecho comum de EffectHit: cancelamento, precisão, cálculo e HP.
    s.data.extend(rom[0x1853CE:0x1853EE])
    if len(s.data) != 32 or s.data[0] != 0:
        raise ValueError('Script nativo de dano inesperado')
    for effect in effects:
        s.setbyte(0x020216C3, effect)
        s.emit(0x15)  # seteffectwithchance
    s.data.extend(rom[0x1853EF:0x1853F6])  # tryfaintmon alvo
    s.goto(0x081853F6)
    return s.finish()


def native_hit_with_secondary(value: int) -> bytes:
    # setmoveeffect value; goto BattleScript_EffectHit. Mesmo formato dos
    # scripts nativos de SpeedDownHit/AttackUpHit da ROM.
    return bytes.fromhex('2e c3 16 02 02') + bytes((value,)) + bytes.fromhex('28 a8 53 18 08')


def unerring_tearful_look(base: int) -> bytes:
    # Accuracy 0 means the move bypasses accuracy/evasion, not 0% chance.
    # Use the native always-hit mode, which still accounts for Protect and
    # semi-invulnerable states (including Lock-On).
    code = bytearray(stages(base, ((1, 1), (4, 1)), True))
    needle = bytes.fromhex('01 9a 68 18 08 00 00')
    if code.count(needle) != 1:
        raise ValueError('Checagem de precisão de Tickle divergente')
    at = code.index(needle)
    code[at + 5:at + 7] = b'\xff\xff'  # NO_ACC_CALC_CHECK_LOCK_ON
    return bytes(code)


def apply_effects(rom: bytes) -> bytes:
    """Retorna nova cópia; o chamador valida o SHA e as regiões de destino."""
    out = bytearray(rom)
    # IDs de efeito sem usuários no conjunto de 797 golpes desta ROM. Alguns
    # são tratados pela IA legada como outros efeitos; a IA não foi modernizada.
    definitions = (
        (96, 467, lambda at: stages(at, ((1, 1), (6, 1)))),              # Hone Claws
        (110, 522, lambda at: stages(at, ((1, 1), (4, 1)))),             # Work Up
        (131, 564, lambda at: stages(at, ((1, 1), (4, 1)), True)),       # Noble Roar
        (141, 482, lambda at: stages(at, ((4, 1), (5, 1), (3, 1)))),   # Quiver Dance
        (163, 488, lambda at: stages(at, ((1, 1), (2, 1), (6, 1)))),   # Coil
        (12, 534, lambda at: stages(at, ((2, 3),))),                   # Cotton Guard
        (15, 507, lambda at: stages(at, ((1, 1), (3, 2)))),              # Shift Gear
        (22, 394, lambda at: damage_with_effects(rom, at, (3, 0xE6))),  # Flare Blitz
        (55, 424, lambda at: damage_with_effects(rom, at, (3, 8))),     # Fire Fang
        (56, 661, lambda at: unerring_tearful_look(at)),                # Tearful Look
        (63, 490, lambda at: native_hit_with_secondary(50)),             # Acid Spray: Sp. Def -2
        (64, 487, lambda at: native_hit_with_secondary(17 | 0x40)),     # Flame Charge: Speed +1
        (74, 450, lambda at: native_hit_with_secondary(18 | 0x40)),     # Charge Beam: Sp. Atk +1
    )
    cursor = SCRIPT_START
    for effect, move, make in definitions:
        if any(rom[MOVE_TABLE + i * 12] == effect for i in range(1, MOVE_COUNT)):
            raise ValueError(f'ID de efeito {effect} já é usado por outro golpe')
        table_index = SCRIPT_TABLE + effect * 4
        if struct.unpack_from('<I', rom, table_index)[0] != 0x081853A8:
            raise ValueError(f'Script-base de efeito {effect} não corresponde')
        code = make(cursor)
        if cursor + len(code) > SCRIPT_END or out[cursor:cursor + len(code)] != b'\xff' * len(code):
            raise ValueError('Área de scripts de batalha ocupada')
        out[cursor:cursor + len(code)] = code
        struct.pack_into('<I', out, table_index, ROM_START + cursor)
        out[MOVE_TABLE + move * 12] = effect
        if move in (394, 424):
            out[MOVE_TABLE + move * 12 + 5] = 10
        if move in (490, 487, 450):
            out[MOVE_TABLE + move * 12 + 5] = {490: 100, 487: 100, 450: 70}[move]
        cursor = (cursor + len(code) + 3) & ~3
    for move, effect, chance in NATIVE_EFFECTS:
        at = MOVE_TABLE + move * 12
        if rom[at] != 0 or rom[at + 5] != 0:
            raise ValueError(f'Efeito original divergente para golpe {move}')
        out[at] = effect
        out[at + 5] = chance
    for move, old_power, new_power, old_accuracy, new_accuracy in POWER_CHANGES:
        at = MOVE_TABLE + move * 12
        if rom[at + 1] != old_power or rom[at + 3] != old_accuracy:
            raise ValueError(f'Poder/precisão originais divergentes para golpe {move}')
        out[at + 1], out[at + 3] = new_power, new_accuracy
    for move, effect, chance in ((403, 31, 30), (516, 4, 100), (518, 71, 100)):
        at = MOVE_TABLE + move * 12
        out[at] = effect
        out[at + 5] = chance
    # O interpretador original usa Random()%100 <= chance, adicionando um
    # ponto percentual a todos os efeitos. Trocar BHI por BHS aplica < chance
    # e conserva o caminho especial de efeitos CERTAIN.
    if rom[0x05A914:0x05A916] != b'\x0e\xd8':
        raise ValueError('Comparação de chance de efeito inesperada')
    out[0x05A914:0x05A916] = b'\x0e\xd2'
    return bytes(out)
