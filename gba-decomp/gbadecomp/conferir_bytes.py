"""Conferencia byte a byte: a listagem remonta exatamente os bytes originais?

Motivo: num binario de terceiros NAO existe verdade-terreno (nao sabemos o que
cada funcao deveria devolver). O que da para provar e mais fraco, mas ainda
util: se cada instrucao listada for remontada e der exatamente os mesmos bytes
do binario, entao a listagem nao esta deslocada, nao pulou bytes e nao inventou
instrucao -- ou seja, o codigo levantado corresponde mesmo aquele binario.

O que ISSO NAO prova: que a semantica interpretada esta certa. Uma instrucao
lida com o significado errado remonta identica. Por isso a prova forte continua
sendo a emulacao com verdade-terreno conhecida (corpus), e aqui o resultado e
apresentado como o que ele e: fidelidade de bytes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import keystone

from . import rom as rom_mod


@dataclass
class ConferenciaBytes:
    """Resultado da remontagem: quantas instrucoes voltam identicas."""

    total: int = 0
    identicas: int = 0
    divergentes: list[tuple[int, str, str, str]] = field(default_factory=list)
    falhas_de_sintaxe: list[tuple[int, str, str]] = field(default_factory=list)
    limite_divergencias: int = 40

    @property
    def taxa(self) -> float:
        return 0.0 if not self.total else 100.0 * self.identicas / self.total

    def texto(self) -> str:
        linhas = [f"conferencia byte a byte: {self.identicas}/{self.total} "
                  f"instrucoes remontam identicas ({self.taxa:.3f}%)"]
        if self.falhas_de_sintaxe:
            linhas.append(f"  {len(self.falhas_de_sintaxe)} instrucoes que o "
                          f"remontador nao aceitou na sintaxe usada (nao contam "
                          f"como divergencia de bytes):")
            for endereco, asm, erro in self.falhas_de_sintaxe[:5]:
                linhas.append(f"    0x{endereco:08X} {asm} -> {erro}")
        if self.divergentes:
            linhas.append(f"  {len(self.divergentes)} instrucoes divergentes:")
            for endereco, asm, original, remontado in self.divergentes[:10]:
                linhas.append(f"    0x{endereco:08X} {asm}: binario {original} "
                              f"remonta {remontado}")
        return "\n".join(linhas)


def _texto_para_remontar(mnemonic: str, operadores: str) -> str:
    """Sintaxe do desmontador -> sintaxe aceita pelo remontador."""
    return f"{mnemonic} {operadores}".replace("#", "").strip()


def conferir(desmontagem, imagem: bytes, base: int = rom_mod.ROM_BASE,
             limite_divergencias: int = 40) -> ConferenciaBytes:
    """Remonta cada instrucao e compara com os bytes do binario."""
    montadores = {}
    resultado = ConferenciaBytes(limite_divergencias=limite_divergencias)

    for endereco in sorted(desmontagem.funcoes):
        funcao = desmontagem.funcoes[endereco]
        modo = (keystone.KS_MODE_THUMB if funcao.modo == "thumb" else keystone.KS_MODE_ARM)
        if funcao.modo not in montadores:
            ks = keystone.Ks(keystone.KS_ARCH_ARM, modo)
            montadores[funcao.modo] = ks
        ks = montadores[funcao.modo]
        for instrucao in funcao.instrucoes:
            resultado.total += 1
            texto = _texto_para_remontar(instrucao.mnemonic, instrucao.operadores)
            try:
                remontado, _ = ks.asm(texto, instrucao.endereco)
            except keystone.KsError as exc:
                resultado.falhas_de_sintaxe.append(
                    (instrucao.endereco, texto, str(exc)))
                continue
            if remontado is None:
                resultado.falhas_de_sintaxe.append(
                    (instrucao.endereco, texto, "sem bytes"))
                continue
            bytes_remontados = bytes(remontado)
            if bytes_remontados == instrucao.bytes_:
                resultado.identicas += 1
            elif len(resultado.divergentes) < limite_divergencias:
                resultado.divergentes.append(
                    (instrucao.endereco, texto, instrucao.bytes_.hex(),
                     bytes_remontados.hex()))
    return resultado
