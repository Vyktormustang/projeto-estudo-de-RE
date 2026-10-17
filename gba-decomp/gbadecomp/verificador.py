"""Verificador por emulacao (unicorn) com verdade-terreno conhecida.

Motivo de existir: um disassembler ou um decompilador que "parece certo" nao
prova nada. A unica prova honesta e executar o codigo e comparar com o
resultado que ja sabemos ser o correto -- em C, na ROM sintetica, e depois (no
mesmo harness) no codigo levantado pelo decompilador.

Este modulo NAO adivinha comportamento: ele le a tabela VERDADE_TERRENO e
reporta, sem maquiagem, cada caso que diverge.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass, field
from pathlib import Path

from unicorn import Uc, UcError
from unicorn import UC_ARCH_ARM, UC_MODE_ARM
from unicorn.arm_const import (
    UC_ARM_REG_LR,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_SP,
)

from . import rom as rom_mod

# Mapa de memoria do GBA (o que basta para este corpus; nao e um GBA completo).
RAM_BASE = 0x02000000          # EWRAM
STACK_BASE = 0x03000000        # IWRAM
STACK_TOPO = 0x03007F00        # topo da pilha IRQ/User no GBA
SENTINELA = 0x0200F000         # LR=fim de execucao (fora da RAM mapeada)
TAM_RAM = 0x40000
TAM_IWRAM = 0x8000


@dataclass
class Resultado:
    """Resultado de um caso da verdade-terreno."""

    nome: str
    argumentos: tuple
    esperado: int | None
    obtido: int | None
    erro: str | None = None

    @property
    def ok(self) -> bool:
        if self.esperado is None:          # caso sem comparacao (so memoria)
            return self.erro is None
        return self.erro is None and self.obtido == self.esperado


@dataclass
class RelatorioEmulacao:
    """Relatorio completo de uma rodada de verificacao."""

    fonte: str
    casos: list[Resultado] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.casos)

    @property
    def aprovados(self) -> int:
        return sum(1 for c in self.casos if c.ok)

    @property
    def reprovados(self) -> list[Resultado]:
        return [c for c in self.casos if not c.ok]

    def texto(self) -> str:
        linhas = [f"verificacao por emulacao -- {self.fonte}",
                  f"{self.aprovados}/{self.total} casos corretos"]
        for c in self.reprovados:
            if c.erro:
                linhas.append(f"  FALHA {c.nome}{c.argumentos}: excecao {c.erro}")
            else:
                linhas.append(f"  FALHA {c.nome}{c.argumentos}: obtido {c.obtido} "
                              f"!= esperado {c.esperado}")
        return "\n".join(linhas)

    def para_json(self) -> str:
        return json.dumps(
            {
                "fonte": self.fonte,
                "total": self.total,
                "aprovados": self.aprovados,
                "falhas": [
                    {"nome": c.nome, "argumentos": list(c.argumentos),
                     "esperado": c.esperado, "obtido": c.obtido, "erro": c.erro}
                    for c in self.reprovados
                ],
            },
            indent=2,
            ensure_ascii=False,
        )


class Emulador:
    """Executa funcoes Thumb/ARM de uma imagem GBA dentro do unicorn.

    Uso:
        emu = Emulador(rom_bytes)
        emu.chamar(0x0800012E, 7, 35)      -> r0 final
    """

    def __init__(self, imagem: bytes, base: int = rom_mod.ROM_BASE):
        self.base = base
        self.mu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        # ATENCAO (armadilha ja verificada na pratica): no unicorn 2, mapear com
        # UC_MODE_THUMB (ou THUMB|MCLASS) faz o modo de execucao sair errado; o
        # caminho confiavel e UC_MODE_ARM e entrar com o bit0 ligado em `addr|1`.
        self.mu.mem_map(base, _arredonda(imagem))
        self.mu.mem_write(base, imagem)
        self.mu.mem_map(RAM_BASE, TAM_RAM)
        self.mu.mem_map(STACK_BASE, TAM_IWRAM)

    def reset(self) -> None:
        """Zera RAM e registradores entre chamadas (evita contaminacao)."""
        self.mu.mem_write(RAM_BASE, b"\x00" * TAM_RAM)
        self.mu.mem_write(STACK_BASE, b"\x00" * TAM_IWRAM)
        self.mu.reg_write(UC_ARM_REG_SP, STACK_TOPO)

    def escrever(self, endereco: int, dados: bytes) -> None:
        self.mu.mem_write(endereco, dados)

    def ler(self, endereco: int, tamanho: int) -> bytes:
        return bytes(self.mu.mem_read(endereco, tamanho))

    def chamar(self, endereco: int, *args: int, limite: int = 200_000,
               zerar: bool = True) -> int:
        """Chama uma funcao e devolve r0. `endereco` pode vir com bit0 ligado."""
        if zerar:
            self.reset()
        for i, valor in enumerate(args):
            self.mu.reg_write(UC_ARM_REG_R0 + i, valor & 0xFFFFFFFF)
        self.mu.reg_write(UC_ARM_REG_SP, STACK_TOPO - 0x100)
        self.mu.reg_write(UC_ARM_REG_LR, SENTINELA)
        self.mu.emu_start(endereco | 1, SENTINELA, count=limite)
        return self.mu.reg_read(UC_ARM_REG_R0)


def _arredonda(dados: bytes) -> int:
    """Tamanho de mapeamento alinhado em pagina (o unicorn exige)."""
    return max(0x1000, (len(dados) + 0xFFF) & ~0xFFF)


def verificar_verdade_terreno(corpus, casos=None, imagem: bytes | None = None,
                              base: int = rom_mod.ROM_BASE) -> RelatorioEmulacao:
    """Roda a tabela de verdade sobre uma imagem e devolve o relatorio.

    Serve tanto para a ROM sintetica compilada do C (`corpus`) quanto para o
    resultado do decompilador (`imagem`), permitindo comparar as duas coisas
    executando-as de verdade -- mesma tabela, mesmos numeros.
    """
    from .corpus import VERDADE_TERRENO

    if imagem is None:
        imagem = Path(corpus.rom_path).read_bytes()
    emu = Emulador(imagem, base=base)
    enderecos = {f.nome: f.addr for f in corpus.funcoes}
    rel = RelatorioEmulacao(fonte=f"{len(imagem)} bytes @ 0x{base:08X}")

    for caso in (casos if casos is not None else VERDADE_TERRENO):
        nome = caso["funcao"]
        args = tuple(_ajusta(caso["args"]))
        if nome not in enderecos:
            rel.casos.append(Resultado(nome, args, caso.get("esperado"), None,
                                       erro="funcao ausente na imagem"))
            continue
        try:
            for deslocamento, blob in caso.get("memoria", ()):
                emu.escrever(RAM_BASE + deslocamento, bytes.fromhex(blob))
            preparo = bool(caso.get("memoria"))
            bruto = emu.chamar(enderecos[nome], *args, zerar=not preparo,
                               limite=caso.get("limite", 200_000))
            if caso.get("verificar"):
                deslocamento, tamanho, formato = caso["verificar"]
                dados = emu.ler(RAM_BASE + deslocamento, tamanho)
                valor = int.from_bytes(dados, "little",
                                       signed=(formato == "int_com_sinal"))
            else:
                valor = _converte(bruto, caso.get("sinal"))
            rel.casos.append(Resultado(nome, args, caso.get("esperado"), valor))
        except UcError as exc:
            rel.casos.append(Resultado(nome, args, caso.get("esperado"), None,
                                       erro=str(exc)))
    return rel


def _ajusta(args: tuple) -> list[int]:
    """Resolve marcadores de memoria nos argumentos: "RAM", "RAM+0x100", "RAM-0x10"."""
    saida = []
    for a in args:
        if isinstance(a, str) and a.startswith("RAM"):
            resto = a[3:]
            saida.append(RAM_BASE + (int(resto, 16) if resto else 0)
                         if resto else RAM_BASE)
        else:
            saida.append(a)
    return saida


def _converte(valor: int, sinal: str | None) -> int:
    """Interpreta r0 como inteiro com ou sem sinal (32 bits)."""
    valor &= 0xFFFFFFFF
    if sinal == "com":
        return struct.unpack("<i", struct.pack("<I", valor))[0]
    return valor


def _leitura_verificada(emu: Emulador, caso: dict, valor: int) -> int:
    """Casos em que o resultado se le da memoria, nao de r0."""
    endereco, tamanho, formato = caso["verificar"]
    dados = emu.ler(RAM_BASE + endereco, tamanho)
    return int.from_bytes(dados, "little") if formato == "int" else int.from_bytes(
        dados, "little", signed=True)
