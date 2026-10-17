"""Emulador de console (mGBA via libretro) para rodar a ROM de verdade.

Por que isto existe: o `verificador.py` (unicorn) executa uma funcao isolada com
a memoria montada a mao. Ele NAO prova que a ROM inteira boota, que o hook e'
alcancado no fluxo real, nem que a bag recebe o item no jogo de verdade. Este
modulo roda a imagem inteira num emulador de GBA e le a memoria do console.

Como o mGBA e' acessado: pelo core libretro `mgba_libretro.so` via `ctypes`.
Duas armadilhas ja' custaram tempo e estao resolvidas aqui:

* **glibc**: este core e' compilado para glibc 2.38 (variantes C23 de `strtol`
  e `strlcpy`) e o sandbox tem 2.36. Nao basta renomear a string de versao no
  ELF: o loader compara tambem o *hash* da versao (`vna_hash`). `compat/`
  ajusta os dois e fornece um shim com os 5 simbolos.
* **memoria**: `retro_get_memory_data` so' expoe a SAVE_RAM (flash). EWRAM e
  IWRAM chegam pelo mapa de memoria que o core publica em
  `SET_MEMORY_MAPS` (`0x10024`); e' o que `ler()` usa.

O que este modulo NAO faz: nao e' debugger (sem breakpoint por PC) e nao
substitui o verificador por emulacao -- ele complementa: o unicorn prova a
funcao isolada, este prova o fluxo do jogo.
"""

from __future__ import annotations

import ctypes as C
import struct
import sys
import zlib
from dataclasses import dataclass, field
from pathlib import Path

# --- ABI libretro (o minimo necessario) ------------------------------------
ENV_SET_PIXEL_FORMAT = 10
ENV_GET_CAN_DUPE = 3
ENV_GET_SYSTEM_DIRECTORY = 9
ENV_GET_LOG_INTERFACE = 27
ENV_GET_VARIABLE = 15
ENV_SET_MEMORY_MAPS = 0x10024          # experimental, e' o que o mGBA usa
FMT_CODES = {0: ("0RGB1555", 2), 1: ("XRGB8888", 4), 2: ("RGB565", 2)}

BOTOES = {"B": 0, "Y": 1, "SELECT": 2, "START": 3, "UP": 4, "DOWN": 5,
          "LEFT": 6, "RIGHT": 7, "A": 8, "X": 9, "L": 10, "R": 11}

# flags de RETRO_MEMDESC_*
MEMDESC_CONST = (1 << 0)
MEMDESC_BIGENDIAN = (1 << 1)


class GameInfo(C.Structure):
    _fields_ = [("path", C.c_char_p), ("data", C.POINTER(C.c_ubyte)),
                ("size", C.c_size_t), ("meta", C.c_char_p)]


class Geometry(C.Structure):
    _fields_ = [("base_width", C.c_uint), ("base_height", C.c_uint),
                ("max_width", C.c_uint), ("max_height", C.c_uint),
                ("aspect_ratio", C.c_float)]


class Timing(C.Structure):
    _fields_ = [("fps", C.c_double), ("sample_rate", C.c_double)]


class MemDescriptor(C.Structure):
    _fields_ = [("flags", C.c_uint64), ("ptr", C.c_void_p),
                ("offset", C.c_uint64), ("start", C.c_uint64),
                ("select", C.c_uint64), ("disconnect", C.c_uint64),
                ("len", C.c_uint64), ("addrspace", C.c_char_p)]


class MemMap(C.Structure):
    _fields_ = [("descriptors", C.POINTER(MemDescriptor)),
                ("num_descriptors", C.c_uint)]


class AvInfo(C.Structure):
    _fields_ = [("geometry", Geometry), ("timing", Timing)]


ENV_CB = C.CFUNCTYPE(C.c_int, C.c_uint, C.c_void_p)
VIDEO_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUS_CB = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUB_CB = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
IPOLL_CB = C.CFUNCTYPE(None)
ISTATE_CB = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)
LOG_CB = C.CFUNCTYPE(None, C.c_char_p)


@dataclass
class Descritor:
    """Um trecho do mapa de memoria que o core publicou.

    `select` (aqui `mascara`) nao e' "onde comeca": sao os bits de endereco que
    SELECIONAM o trecho. Quando vale 0, o trecho e' exatamente
    `[base_gba, base_gba+tamanho)`. Quando nao vale, um endereco pertence ao
    trecho se `(endereco & ~select) == (base_gba & ~select)`.

    Ja' testado errado duas vezes: (a) ignorar a mascara fazia VRAM
    (0x06000000) "cobrir" endereco de EWRAM e a leitura caia em ponteiro
    invalido (segfault); (b) tratar `select` como "bits que NAO importam" fazia
    IWRAM sumir do mapa. A regra que vale e' a do libretro: os bits LIGADOS em
    `select` sao os que precisam casar com `start`.
    """

    base_gba: int
    tamanho: int
    ponteiro: int
    deslocamento: int
    mascara: int

    def cobre(self, endereco: int, n: int) -> bool:
        if not self.ponteiro:
            return False
        if (endereco & self.mascara) != (self.base_gba & self.mascara):
            return False
        return endereco >= self.base_gba and endereco + n - self.base_gba <= self.tamanho


class ErroDeEmulacao(Exception):
    pass


@dataclass
class EmuladorConsole:
    """Roda uma ROM GBA no mGBA e le a memoria do console.

    Uso:
        emu = EmuladorConsole(rom, core)
        emu.rodar(600)
        emu.ler(0x02025000, 4)
    """

    rom: Path
    core: Path
    workdir: Path = Path("/tmp/mgba-work")
    verbose: bool = False
    _core: object = None
    _mmaps: list = field(default_factory=list)
    _agenda: dict = field(default_factory=dict)
    _entradas: dict = field(default_factory=dict)
    _fotogramas: int = 0
    _quadro_atual: int = 0
    _rgb: bytes | None = None
    _w: int = 0
    _h: int = 0
    _fmt: tuple | None = None
    _logs: list = field(default_factory=list)
    opcoes: dict = field(default_factory=dict)
    av: object = None

    # -- ciclo de vida ------------------------------------------------------
    def __post_init__(self) -> None:
        self.rom = Path(self.rom)
        self.core = Path(self.core)
        if not self.rom.is_file():
            raise ErroDeEmulacao(f"ROM ausente: {self.rom}")
        if not self.core.is_file():
            raise ErroDeEmulacao(f"core libretro ausente: {self.core}")
        self.workdir.mkdir(parents=True, exist_ok=True)
        self._carregar_core()

    def _carregar_core(self) -> None:
        # o core depende de libinih; carrega com RTLD_GLOBAL antes dele, senao
        # o loader do core falha mesmo com LD_LIBRARY_PATH setado depois
        bibliotecas = [self.core.parent, self.core.parent.parent,
                       self.core.parent.parent.parent]
        for nome in ("libinih.so.1", "libinih.so.58"):
            for pasta in bibliotecas:
                caminho = pasta / nome
                if caminho.exists():
                    try:
                        C.CDLL(str(caminho), mode=C.RTLD_GLOBAL)
                    except OSError:
                        pass
                    break
        self._core = C.CDLL(str(self.core))
        self._core.retro_get_memory_data.restype = C.c_void_p
        self._core.retro_get_memory_size.restype = C.c_size_t

        def _env(cmd, data):
            try:
                if cmd == ENV_SET_PIXEL_FORMAT and data:
                    valor = C.cast(data, C.POINTER(C.c_int)).contents.value
                    if valor in FMT_CODES:
                        self._fmt = FMT_CODES[valor]
                        return 1
                    return 0
                if cmd == ENV_GET_CAN_DUPE and data:
                    C.cast(data, C.POINTER(C.c_int))[0] = 1
                    return 1
                if cmd == ENV_GET_VARIABLE and data:
                    # devolve "valor\0chave\0" em buffer de 128 bytes; usado
                    # para AUTO-ADVANCE (pular dialogos) sem apertar botao
                    chave = C.string_at(data).decode("ascii", "replace")
                    valor = self.opcoes.get(chave, "")
                    buf = C.cast(data, C.POINTER(C.c_char))
                    C.memmove(buf, valor.encode() + b"\x00\x00", len(valor) + 2)
                    return 1
                if cmd == ENV_GET_SYSTEM_DIRECTORY and data:
                    C.cast(data, C.POINTER(C.c_char_p))[0] = str(self.workdir).encode()
                    return 1
                if cmd == ENV_GET_LOG_INTERFACE:
                    # logprintf_t e' variadico; ctypes nao modela essa ABI
                    return 0
                if cmd == ENV_SET_MEMORY_MAPS and data:
                    mapa = C.cast(data, C.POINTER(MemMap)).contents
                    self._mmaps = []
                    for i in range(mapa.num_descriptors):
                        d = mapa.descriptors[i]
                        self._mmaps.append(Descritor(
                            base_gba=int(d.start), tamanho=int(d.len),
                            ponteiro=int(d.ptr or 0),
                            deslocamento=int(d.offset),
                            mascara=int(d.select)))
                    if self.verbose:
                        for d in self._mmaps:
                            print(f"[mapa] 0x{d.base_gba:08X} +0x{d.tamanho:X} "
                                  f"(offset 0x{d.deslocamento:X})")
                    return 1
                return 0
            except Exception:  # noqa: BLE001 - callback em C: nao pode propagar
                return 0

        def _video(data, w, h, pitch):
            if not data or not self._fmt:
                return
            codigo = 1 if self._fmt[0] == "XRGB8888" else (2 if self._fmt[0] == "RGB565" else 0)
            bpp = self._fmt[1]
            stride = w * bpp
            if pitch == stride:
                bruto = bytearray(C.string_at(data, stride * h))
            else:
                bruto = bytearray()
                for y in range(h):
                    bruto += C.string_at(data + y * pitch, stride)
            rgb = bytearray(w * h * 3)
            passo = 4 if codigo == 1 else 2
            for i in range(0, stride * h, passo):
                if codigo == 1:
                    b, g, r = bruto[i], bruto[i + 1], bruto[i + 2]
                else:
                    v = bruto[i] | (bruto[i + 1] << 8)
                    if codigo == 2:
                        r = ((v >> 11) & 31) * 255 // 31
                        g = ((v >> 5) & 63) * 255 // 63
                        b = (v & 31) * 255 // 31
                    else:
                        r = ((v >> 10) & 31) * 255 // 31
                        g = ((v >> 5) & 31) * 255 // 31
                        b = (v & 31) * 255 // 31
                o = (i // passo) * 3
                rgb[o] = r
                rgb[o + 1] = g
                rgb[o + 2] = b
            self._rgb, self._w, self._h = bytes(rgb), w, h
            self._fotogramas += 1

        self._env_cb = ENV_CB(_env)
        self._video_cb = VIDEO_CB(_video)
        self._aus_cb = AUS_CB(lambda l, r: None)
        self._aub_cb = AUB_CB(lambda dados, quadros: quadros)
        self._ipoll_cb = IPOLL_CB(lambda: None)
        self._istate_cb = ISTATE_CB(
            lambda porta, disp, idx, ident: self._entradas.get((porta, disp, idx, ident), 0))

        c = self._core
        c.retro_set_environment(self._env_cb)
        c.retro_set_video_refresh(self._video_cb)
        c.retro_set_audio_sample(self._aus_cb)
        c.retro_set_audio_sample_batch(self._aub_cb)
        c.retro_set_input_poll(self._ipoll_cb)
        c.retro_set_input_state(self._istate_cb)
        c.retro_init()

        info = GameInfo(str(self.rom.resolve()).encode(), None, 0, None)
        if not c.retro_load_game(C.byref(info)):
            raise ErroDeEmulacao(f"retro_load_game recusou {self.rom}")
        self.av = AvInfo()
        c.retro_get_system_av_info(C.byref(self.av))

    def fechar(self) -> None:
        if self._core is not None:
            try:
                self._core.retro_unload_game()
            except Exception:  # noqa: BLE001
                pass
            self._core = None

    # -- execucao -----------------------------------------------------------
    def agendar(self, quadro: int, botao: str, segurar: int = 8) -> None:
        """Segura `botao` do quadro `quadro` ate' `quadro+segurar`."""
        self._agenda[BOTOES[botao.upper()]] = (quadro, quadro + segurar)

    def rodar(self, quadros: int) -> int:
        """Roda `quadros` quadros. A agenda usa QUADRO ABSOLUTO DESDE O 0.

        O contador e' cumulativo: reiniciar `i` a cada chamada fazia a agenda
        inteira nunca disparar em execucoes feitas em blocos (bug real que
        custou uma rodada de 26 000 quadros sem nenhum botao apertado).
        """
        for _ in range(quadros):
            i = self._quadro_atual
            self._entradas = {}
            for botao, (inicio, fim) in list(self._agenda.items()):
                if i < inicio:
                    continue
                if i > fim:
                    del self._agenda[botao]
                    continue
                self._entradas[(0, 1, 0, botao)] = 1
            self._core.retro_run()
            self._quadro_atual += 1
        return self._fotogramas

    # -- leitura de memoria -------------------------------------------------
    def ler(self, endereco_gba: int, tamanho: int) -> bytes:
        """Le a memoria do console pelo mapa que o core publicou."""
        for d in self._mmaps:
            if d.cobre(endereco_gba, tamanho):
                desloc = d.deslocamento + (endereco_gba - d.base_gba)
                return bytes(C.string_at(d.ponteiro + desloc, tamanho))
        raise ErroDeEmulacao(
            f"0x{endereco_gba:08X}+{tamanho} nao esta' em nenhum descritor de "
            f"memoria ({len(self._mmaps)} descritores)")

    def ler_u8(self, endereco: int) -> int:
        return self.ler(endereco, 1)[0]

    def ler_u16(self, endereco: int) -> int:
        return struct.unpack("<H", self.ler(endereco, 2))[0]

    def ler_u32(self, endereco: int) -> int:
        return struct.unpack("<I", self.ler(endereco, 4))[0]

    def escrever(self, endereco_gba: int, dados: bytes) -> None:
        for d in self._mmaps:
            if d.cobre(endereco_gba, len(dados)) and not (d.base_gba >= 0x0E000000):
                desloc = d.deslocamento + (endereco_gba - d.base_gba)
                C.memmove(d.ponteiro + desloc, dados, len(dados))
                return
        raise ErroDeEmulacao(f"escrita em 0x{endereco_gba:08X} nao mapeada")

    # -- imagem -------------------------------------------------------------
    @property
    def quadro(self) -> bytes:
        if self._rgb is None:
            raise ErroDeEmulacao("nenhum quadro capturado ainda")
        return self._rgb

    def salvar_png(self, caminho: Path) -> None:
        def bloco(tag: bytes, dados: bytes) -> bytes:
            return (struct.pack(">I", len(dados)) + tag + dados
                    + struct.pack(">I", zlib.crc32(tag + dados)))
        w, h, rgb = self._w, self._h, self._rgb
        bruto = b"".join(b"\x00" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
        png = (b"\x89PNG\r\n\x1a\n"
               + bloco(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
               + bloco(b"IDAT", zlib.compress(bruto, 6))
               + bloco(b"IEND", b""))
        Path(caminho).write_bytes(png)


def encurtar(texto: str, limite: int = 60) -> str:
    return texto if len(texto) <= limite else texto[:limite - 3] + "..."


if __name__ == "__main__":  # pragma: no cover - utilitario manual
    rom = Path(sys.argv[1])
    core = Path(sys.argv[2])
    emu = EmuladorConsole(rom, core, verbose=True)
    emu.rodar(int(sys.argv[3]) if len(sys.argv) > 3 else 600)
    print(f"{emu._fotogramas} quadros; descritores: {len(emu._mmaps)}")
