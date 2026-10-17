"""Leitura e validacao de imagens de ROM do Game Boy Advance.

Objetivo: transformar um arquivo binario em FATOS verificaveis (cabecalho,
checksums, espaco livre, mapa de regioes de codigo/dados) antes de qualquer
tentativa de desmontagem. Nada aqui adivinha: o que nao da para provar fica
marcado como nao verificado.

Sobre a logo da Nintendo: ela e obra protegida e **nao** e replicada nem
comparada byte a byte neste codigo. O campo `logo_presente` apenas registra se a
area deixou de ser 0xFF/0x00 (isto e, se foi preenchida), o que basta para
triagem sem reproduzir o desenho.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

ROM_BASE = 0x08000000
ROM_END = 0x0A000000  # 32 MB: limite do espaco de cartucho
HEADER_SIZE = 0xC0
LOGO_OFFSET = 0x04
LOGO_SIZE = 0x9C
FIXED_BYTE = 0x96  # deve ser 0x00
COMPLEMENT_OFFSET = 0xBD


def to_offset(addr: int) -> int:
    """Endereco no espaco GBA -> offset no arquivo (espaco de cartucho)."""
    return addr - ROM_BASE


def to_addr(offset: int) -> int:
    return offset + ROM_BASE


def looks_like_rom(data: bytes) -> bool:
    return len(data) >= HEADER_SIZE and data[0xB2] != 0xFF


def complement_check(data: bytes) -> bool:
    """O ultimo byte do cabecalho e o complemento da soma (formula oficial).

    A soma comeca em 0xA0, NAO em 0x00: os bytes 0x04..0x9F sao o logo da
    Nintendo e o desvio inicial, e nao entram na conta. Esta funcao somava
    `data[:0xBD]` (ou seja, 0x00..0xBC) e por isso REPROVAVA o cabecalho desta
    ROM -- que na verdade esta' correto (`0xBD = 0x68`, soma(0xA0..0xBC)=0x7F,
    (0x7F + 0x68 + 0x19) & 0xFF == 0). O README chegou a publicar "o complemento
    nao confere" por causa disto; era o teste que estava errado, nao a imagem.
    Achado ao construir o patcher, que precisa recalcular esse byte.
    """
    if len(data) < HEADER_SIZE:
        return False
    soma = sum(data[0xA0:COMPLEMENT_OFFSET]) & 0xFF
    return ((soma + data[COMPLEMENT_OFFSET] + 0x19) & 0xFF) == 0


@dataclass
class FunctionSpan:
    """Um trecho de codigo delimitado. Fonte: censo externo ou descoberta propria."""

    addr: int
    size: int | None
    mode: str  # "thumb" | "arm"
    name: str = ""
    origem: str = "descoberta"
    confianca: str = "?"

    @property
    def end(self) -> int | None:
        return None if self.size is None else self.addr + self.size


@dataclass
class RomReport:
    path: str
    sha256: str
    size: int
    title: str
    game_code: str
    maker_code: str
    version: int
    software_version: int
    complement_ok: bool
    fixed_byte_ok: bool
    logo_area_preenchida: bool
    entry_point: int
    entry_thumb: bool
    free_space: list[tuple[int, int]] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)

    def to_json(self) -> dict:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "size": self.size,
            "title": self.title,
            "game_code": self.game_code,
            "maker_code": self.maker_code,
            "version": self.version,
            "complement_check_ok": self.complement_ok,
            "fixed_byte_ok": self.fixed_byte_ok,
            "logo_area_preenchida": self.logo_area_preenchida,
            "entry_point": f"0x{self.entry_point:08X}",
            "entry_modo": "thumb" if self.entry_thumb else "arm",
            "free_space": [[f"0x{a:08X}", b] for a, b in self.free_space],
            "notas": self.notas,
        }


class GbaRom:
    """ROM carregada em memoria, com acesso por endereco do espaco GBA."""

    def __init__(self, path: str | Path, data: bytes | None = None) -> None:
        self.path = str(path)
        self.data = data if data is not None else Path(path).read_bytes()

    # -- acesso -------------------------------------------------------------
    def __len__(self) -> int:
        return len(self.data)

    def in_rom(self, addr: int) -> bool:
        return ROM_BASE <= addr < ROM_BASE + len(self.data)

    def read(self, addr: int, n: int) -> bytes:
        if not self.in_rom(addr):
            raise ValueError(f"endereco fora da ROM: 0x{addr:08X}")
        off = to_offset(addr)
        return self.data[off:off + n]

    def u8(self, addr: int) -> int:
        return self.read(addr, 1)[0]

    def u16(self, addr: int) -> int:
        return int.from_bytes(self.read(addr, 2), "little")

    def u32(self, addr: int) -> int:
        return int.from_bytes(self.read(addr, 4), "little")

    def _str(self, offset: int, size: int) -> str:
        bruto = self.data[offset:offset + size]
        texto = bruto.decode("ascii", errors="replace").strip("\x00 ")
        return "".join(c for c in texto if 32 <= ord(c) < 127)

    # -- descoberta de espaco livre ----------------------------------------
    def free_space(self, min_run: int = 256, pad: int = 0xFF) -> list[tuple[int, int]]:
        """Regioes continuas de `pad` (0xFF numa ROM virgem; 0x00 em padding de
        ferramenta) com pelo menos `min_run` bytes. Serve para saber onde um
        hook poderia ser injetado sem sobrescrever conteudo original."""
        achados: list[tuple[int, int]] = []
        inicio = None
        for i, byte in enumerate(self.data):
            if byte == pad:
                if inicio is None:
                    inicio = i
            else:
                if inicio is not None and i - inicio >= min_run:
                    achados.append((to_addr(inicio), i - inicio))
                inicio = None
        if inicio is not None and len(self.data) - inicio >= min_run:
            achados.append((to_addr(inicio), len(self.data) - inicio))
        return achados

    def maior_buraco(self, pad: int = 0xFF) -> tuple[int, int]:
        regioes = self.free_space(min_run=16, pad=pad)
        return max(regioes, key=lambda r: r[1]) if regioes else (0, 0)

    # -- relatorio ----------------------------------------------------------
    def report(self, entry_point: int = 0, entry_thumb: bool = False) -> RomReport:
        notas: list[str] = []
        complement_ok = complement_check(self.data)
        if not complement_ok:
            notas.append("complement check FALHOU: imagem provavelmente modificada "
                         "sem recalcular o cabecalho, truncada ou de dump incompleto")
        fixed_ok = self.data[FIXED_BYTE] == 0x00
        if not fixed_ok:
            notas.append(f"byte fixo em 0x96 = 0x{self.data[FIXED_BYTE]:02X} (esperado 0x00)")

        logo = self.data[LOGO_OFFSET:LOGO_OFFSET + LOGO_SIZE]
        logo_preenchida = any(b not in (0x00, 0xFF) for b in logo)
        notas.append("logo Nintendo: presenca detectada, conteudo NAO comparado "
                     "(obra protegida - verificacao apenas por hash externo, se o "
                     "usuario fornecer a referencia)")
        if not logo_preenchida:
            notas.append("area da logo esta vazia: fixture sintetica, nao uma ROM comercial")

        if entry_point:
            entrada_no_cartucho = ROM_BASE <= entry_point < ROM_BASE + len(self.data)
            if not entrada_no_cartucho:
                notas.append(f"entry point 0x{entry_point:08X} fora dos limites da ROM")

        return RomReport(
            path=self.path,
            sha256=hashlib.sha256(self.data).hexdigest(),
            size=len(self.data),
            title=self._str(0xA0, 12),
            game_code=self._str(0xAC, 4),
            maker_code=self._str(0xB0, 2),
            version=self.data[0xBC],
            software_version=self.data[0xBC],
            complement_ok=complement_ok,
            fixed_byte_ok=fixed_ok,
            logo_area_preenchida=logo_preenchida,
            entry_point=entry_point,
            entry_thumb=entry_thumb,
            free_space=self.free_space(min_run=1024)[:40],
            notas=notas,
        )


def carregar_funcoes_csv(caminho: str | Path) -> list[FunctionSpan]:
    """Le o censo de funcoes do projeto gba-re (functions.csv) e devolve spans.

    Formato aceito (do projeto original): colunas endereco_hex, tamanho_hex,
    nome, modo_cpu, confianca, origem, evidencia, historico_renomeacao. Linhas
    iniciadas por '#' sao comentario.
    """
    spans: list[FunctionSpan] = []
    for linha in Path(caminho).read_text(encoding="utf-8", errors="replace").splitlines():
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        partes = _split_csv_respeitando_aspas(linha)
        if len(partes) < 4 or not partes[0].startswith("0x"):
            continue
        try:
            addr = int(partes[0], 16)
        except ValueError:
            continue
        tamanho = None
        texto_tam = partes[1].strip()
        if texto_tam.startswith("0x"):
            tamanho = int(texto_tam, 16)
        elif texto_tam.isdigit():
            tamanho = int(texto_tam)
        modo = (partes[3] or "").strip().lower()
        spans.append(FunctionSpan(
            addr=addr, size=tamanho,
            mode="arm" if modo == "arm" else "thumb",
            name=partes[2].strip(),
            origem=partes[5].strip() if len(partes) > 5 else "censo",
            confianca=partes[4].strip() if len(partes) > 4 else "?",
        ))
    return spans


def _split_csv_respeitando_aspas(linha: str) -> list[str]:
    campos: list[str] = []
    atual: list[str] = []
    dentro = False
    i = 0
    while i < len(linha):
        c = linha[i]
        if c == '"':
            if dentro and i + 1 < len(linha) and linha[i + 1] == '"':
                atual.append('"')
                i += 1
            else:
                dentro = not dentro
        elif c == "," and not dentro:
            campos.append("".join(atual))
            atual = []
        else:
            atual.append(c)
        i += 1
    campos.append("".join(atual))
    return campos
