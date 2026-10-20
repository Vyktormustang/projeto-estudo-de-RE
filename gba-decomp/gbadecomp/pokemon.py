"""Leitura e escrita SEGURA de Pokemon do time (estrutura de 100 bytes).

O time durante o jogo nao mora no SaveBlock1 (medido, §19.2): a contagem
esta' em `0x02024029` e os 6 Pokemon de 100 bytes a partir de
`0x02024284` (`gPlayerParty`/`gPlayerPartyCount` do pret/pokefirered).

Anatomia (pret `include/pokemon.h`), PROVADA nesta ROM em dois especimes
(checksum, especie, golpes, EXP, IVs e atributos recalculados -- §20):

    struct BoxPokemon (80 bytes)
      +0x00 personalidade u32      +0x04 otId u32
      +0x08 apelido[10]            +0x12 idioma u8
      +0x13 flags u8 (isBadEgg/hasSpecies/isEgg/...)
      +0x14 nome do OT[7]          +0x1B marcacoes u8
      +0x1C checksum u16           +0x1E (desconhecido) u16
      +0x20 dados seguros: 48 bytes = 4 subestruturas de 12
    extras do time (20 bytes)
      +0x50 status u32  +0x54 nivel u8  +0x55 carta u8
      +0x56 HP u16, HPMax, Atk, Def, Vel, AtkEsp, DefEsp (u16 cada)

Os 48 bytes sao cifrados por XOR de cada u32 com
`personalidade ^ otId` (pret `EncryptBoxMon`/`DecryptBoxMon`); decifrados,
sao 4 subestruturas logicas -- 0 crescimento (especie/item/EXP/...),
1 golpes+PP, 2 EVs/condicao, 3 miscelânea (origem/IVs/fitas) -- guardadas
em slots fisicos permutados por `personalidade % 24` (`ORDEM`).
O `checksum` e' a soma (mod 2^16) dos 24 u16 dos dados DECIFRADOS;
checksum errado = o jogo marca o Pokemon como "Bad Egg". Por isso toda
escrita aqui decifra, altera, **recifra e recalcula o checksum** na mesma
operacao -- nunca edite os bytes seguros na mao.

Escopo honesto: ler/escrever na RAM (via estado do emulador) esta'
provado; gravar no save do cartucho e' o jogo quem faz ao salvar --
incluindo, presumivelmente, copiar o time para os campos +0x34/+0x38 do
SaveBlock1, que ficam zerados durante o jogo (§19.2, nao provado).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

# tipo logico -> slot fisico, por personalidade % 24 (pret: GetSubstruct)
ORDEM = [
    (0, 1, 2, 3), (0, 1, 3, 2), (0, 2, 1, 3), (0, 3, 1, 2),
    (0, 2, 3, 1), (0, 3, 2, 1), (1, 0, 2, 3), (1, 0, 3, 2),
    (2, 0, 1, 3), (3, 0, 1, 2), (2, 0, 3, 1), (3, 0, 2, 1),
    (1, 2, 0, 3), (1, 3, 0, 2), (2, 1, 0, 3), (3, 1, 0, 2),
    (2, 3, 0, 1), (3, 2, 0, 1), (1, 2, 3, 0), (1, 3, 2, 0),
    (2, 1, 3, 0), (3, 1, 2, 0), (2, 3, 1, 0), (3, 2, 1, 0),
]

CRESCIMENTO, GOLPES, EVS, MISC = 0, 1, 2, 3
TAMANHO = 100
END_CONTAGEM = 0x02024029   # gPlayerPartyCount (medido nesta ROM)
END_TIME = 0x02024284       # gPlayerParty[0]    (medido nesta ROM)
MAX_TIME = 6

# ordem usada em toda a API: (HP, Atk, Def, Vel, AtkEsp, DefEsp)
BASES_CONHECIDAS = {1: (45, 49, 49, 45, 65, 65)}  # especie 1 = Bulbasaur


def _xor48(dados: bytes, chave: int) -> bytes:
    return b"".join(struct.pack("<I", w ^ chave)
                    for w in struct.unpack("<12I", dados))


def checksum(dados_decifrados: bytes) -> int:
    """Soma dos 24 u16 dos dados decifrados (pret: CalculateBoxMonChecksum)."""
    return sum(struct.unpack("<24H", dados_decifrados)) & 0xFFFF


@dataclass
class Pokemon:
    """Um Pokemon do time sobre o buffer bruto de 100 bytes (editavel)."""

    bruto: bytearray

    def __post_init__(self):
        if len(self.bruto) != TAMANHO:
            raise ValueError(f"esperava {TAMANHO} bytes, veio {len(self.bruto)}")
        self.bruto = bytearray(self.bruto)

    # -- campos nao cifrados ------------------------------------------------
    @property
    def personalidade(self) -> int:
        return struct.unpack_from("<I", self.bruto, 0x00)[0]

    @property
    def ot_id(self) -> int:
        return struct.unpack_from("<I", self.bruto, 0x04)[0]

    @property
    def apelido_bruto(self) -> bytes:
        return bytes(self.bruto[0x08:0x12])

    @property
    def nivel(self) -> int:
        return self.bruto[0x54]

    @property
    def hp(self) -> tuple[int, int]:
        return struct.unpack_from("<2H", self.bruto, 0x56)

    @property
    def atributos(self) -> tuple[int, ...]:
        """(Atk, Def, Vel, AtkEsp, DefEsp) gravados (o jogo recalcula)."""
        return struct.unpack_from("<5H", self.bruto, 0x5A)

    @property
    def checksum_guardado(self) -> int:
        return struct.unpack_from("<H", self.bruto, 0x1C)[0]

    @property
    def natureza(self) -> int:
        """Indice 0..24 (pret: personalidade % 25)."""
        return self.personalidade % 25

    # -- os 48 bytes seguros --------------------------------------------------
    def _chave(self) -> int:
        return self.personalidade ^ self.ot_id

    def dados_decifrados(self) -> bytes:
        return _xor48(bytes(self.bruto[0x20:0x50]), self._chave())

    def checksum_calculado(self) -> int:
        return checksum(self.dados_decifrados())

    def integro(self) -> bool:
        """True se o checksum bate (senao o jogo trata como Bad Egg)."""
        return self.checksum_guardado == self.checksum_calculado()

    def _subestruturas(self) -> list[bytearray]:
        """4 blocos de 12 bytes indexados pelo TIPO logico (0..3)."""
        dados = self.dados_decifrados()
        fisicos = [dados[i * 12:(i + 1) * 12] for i in range(4)]
        ordem = ORDEM[self.personalidade % 24]
        return [bytearray(fisicos[ordem[tipo]]) for tipo in range(4)]

    def _gravar(self, subs: list[bytearray]) -> None:
        ordem = ORDEM[self.personalidade % 24]
        fisicos = [b""] * 4
        for tipo in range(4):
            fisicos[ordem[tipo]] = bytes(subs[tipo])
        dados = b"".join(fisicos)
        self.bruto[0x20:0x50] = _xor48(dados, self._chave())
        struct.pack_into("<H", self.bruto, 0x1C, checksum(dados))

    # -- subestrutura 0: crescimento -----------------------------------------
    @property
    def especie(self) -> int:
        return struct.unpack_from("<H", self._subestruturas()[CRESCIMENTO], 0)[0]

    @property
    def item_segurado(self) -> int:
        return struct.unpack_from("<H", self._subestruturas()[CRESCIMENTO], 2)[0]

    @property
    def experiencia(self) -> int:
        return struct.unpack_from("<I", self._subestruturas()[CRESCIMENTO], 4)[0]

    @property
    def amizade(self) -> int:
        return self._subestruturas()[CRESCIMENTO][9]

    # -- subestrutura 1: golpes ------------------------------------------------
    @property
    def golpes(self) -> tuple[int, ...]:
        return struct.unpack_from("<4H", self._subestruturas()[GOLPES], 0)

    @property
    def pps(self) -> tuple[int, ...]:
        return tuple(self._subestruturas()[GOLPES][8:12])

    def definir_golpe(self, posicao: int, golpe: int, pp: int) -> None:
        """Troca o golpe da `posicao` (0..3) e recifra com checksum novo."""
        if not 0 <= posicao <= 3:
            raise ValueError("posicao deve ser 0..3")
        subs = self._subestruturas()
        struct.pack_into("<H", subs[GOLPES], posicao * 2, golpe)
        subs[GOLPES][8 + posicao] = pp
        self._gravar(subs)

    # -- subestrutura 2: EVs ----------------------------------------------------
    @property
    def evs(self) -> tuple[int, ...]:
        return tuple(self._subestruturas()[EVS][:6])

    # -- subestrutura 3: miscelânea/IVs ------------------------------------------
    @property
    def ivs(self) -> tuple[int, ...]:
        bruto32 = struct.unpack_from("<I", self._subestruturas()[MISC], 4)[0]
        return tuple((bruto32 >> (5 * i)) & 31 for i in range(6))

    # -- utilidades ---------------------------------------------------------------
    def recalcular(self, bases: tuple[int, ...]) -> tuple[int, ...]:
        """(HPMax, Atk, Def, Vel, AtkEsp, DefEsp) pelas formulas da ger. 3.

        Serve de prova cruzada: se a decifragem estiver certa, o resultado
        e' igual ao que o proprio jogo gravou em `hp`/`atributos`.
        """
        ivs, evs, nivel = self.ivs, self.evs, self.nivel
        hp_max = ((2 * bases[0] + ivs[0] + evs[0] // 4) * nivel) // 100 \
            + nivel + 10
        sobe, desce = divmod(self.natureza, 5)[0], self.natureza % 5
        stats = []
        for i in range(5):  # Atk, Def, Vel, AtkEsp, DefEsp
            n = ((2 * bases[i + 1] + ivs[i + 1] + evs[i + 1] // 4) * nivel) // 100 + 5
            if sobe != desce:
                if i == sobe:
                    n = n * 110 // 100
                elif i == desce:
                    n = n * 90 // 100
            stats.append(n)
        return (hp_max, *stats)

    def serializar(self) -> bytes:
        return bytes(self.bruto)


def ler_pokemon(buffer100: bytes) -> Pokemon:
    return Pokemon(bytearray(buffer100))


def exp_minima_medio_lento(nivel: int) -> int:
    """Curva "medium slow" (ex.: Bulbasaur): 6n^3/5 - 15n^2 + 100n - 140."""
    if nivel <= 1:
        return 0
    return 6 * nivel ** 3 // 5 - 15 * nivel * nivel + 100 * nivel - 140
