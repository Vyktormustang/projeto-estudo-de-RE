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

ALIASES = {"sb": "r9", "sl": "r10", "fp": "r11", "ip": "r12", "r13": "sp",
           "r14": "lr", "r15": "pc"}


@dataclass
class ConferenciaBytes:
    """Resultado da remontagem: quantas instrucoes voltam identicas."""

    total: int = 0
    identicas: int = 0
    exemplos: list[tuple[int, str, str, str]] = field(default_factory=list)
    falhas_de_sintaxe: list[tuple[int, str, str]] = field(default_factory=list)
    limite_exemplos: int = 25

    @property
    def taxa(self) -> float:
        return float("nan") if not self.total else 100.0 * self.identicas / self.total

    def texto(self) -> str:
        linhas = [f"conferencia de bytes: {self.identicas}/{self.total} "
                  f"({self.taxa:.2f}%) remontam identicas ao binario"]
        if self.falhas_de_sintaxe:
            linhas.append(f"  {len(self.falhas_de_sintaxe)} instrucoes que o "
                          f"remontador nao aceitou na sintaxe usada (nao contam "
                          f"como divergencia de bytes):")
            for endereco, texto, erro in self.falhas_de_sintaxe[:5]:
                linhas.append(f"    {endereco:08X} {texto}  -> {erro}")
        if self.exemplos:
            # Agrupar por mnemonico: interessa saber se as divergencias sao uma
            # classe so (mesma instrucao com codificacao alternativa, que e o
            # esperado) ou varias (o que indicaria leitura errada).
            por_mnemonico: dict[str, int] = {}
            for _, texto, _, _ in self.exemplos:
                por_mnemonico[texto.split(" ")[0]] = por_mnemonico.get(texto.split(" ")[0], 0) + 1
            linhas.append(f"  {len(self.exemplos)} divergencias, por mnemonico: "
                          f"{por_mnemonico}")
            for endereco, texto, original, remontado in self.exemplos[:8]:
                linhas.append(f"    {endereco:08X} {texto}: binario {original}, "
                              f"remonta {remontado}")
        return "\n".join(linhas)


def _texto_para_remontar(instrucao) -> str:
    texto = f"{instrucao.mnemonic} {instrucao.operadores}".strip()
    for alias, real in ALIASES.items():
        texto = texto.replace(f" {alias},", f" {real},").replace(f" {alias}]", f" {real}]")
    # o remontador calcula o endereco a partir do endereco da instrucao, entao o
    # `#` do capstone so atrapalha
    return texto.replace(" #", " ").replace("[#", "[")


def conferir(desmontagem, imagem: bytes, base: int = rom_mod.ROM_BASE,
             limite_exemplos: int = 25) -> ConferenciaBytes:
    """Remonta cada instrucao listada e compara com os bytes do binario."""
    import capstone

    montadores: dict[str, keystone.Ks] = {}
    resultado = ConferenciaBytes(limite_exemplos=limite_exemplos)
    for funcao in desmontagem.funcoes.values():
        if funcao.modo not in montadores:
            montadores[funcao.modo] = keystone.Ks(
                keystone.KS_ARCH_ARM,
                keystone.KS_MODE_THUMB if funcao.modo == "thumb" else keystone.KS_MODE_ARM)
        ks = montadores[funcao.modo]
        for instrucao in funcao.instrucoes:
            resultado.total += 1
            texto = _texto_para_remontar(instrucao)
            try:
                montado, _ = ks.asm(texto, instrucao.endereco)
            except keystone.KsError as exc:
                if len(resultado.falhas_de_sintaxe) < 200:
                    resultado.falhas_de_sintaxe.append(
                        (instrucao.endereco, texto, str(exc)))
                continue
            if not montado:
                if len(resultado.falhas_de_sintaxe) < 200:
                    resultado.falhas_de_sintaxe.append(
                        (instrucao.endereco, texto, "sem bytes"))
                continue
            if bytes(montado) == instrucao.bytes_:
                resultado.identicas += 1
            elif len(resultado.exemplos) < limite_exemplos:
                pass
                resultado.exemplos.append((instrucao.endereco, texto,
                                           instrucao.bytes_.hex(), bytes(montado).hex()))
    return resultado


def main(argv=None) -> int:
    """    python -m gbadecomp.conferir_bytes ROM.gba [--censo functions.csv]"""
    import argparse
    from pathlib import Path

    from . import disasm as disasm_mod

    parser = argparse.ArgumentParser(description="conferencia byte a byte da listagem")
    parser.add_argument("rom")
    parser.add_argument("--censo", help="functions.csv (sementes por endereco)")
    args = parser.parse_args(argv)

    rom = rom_mod.GbaRom(args.rom)
    sementes = {}
    if args.censo:
        for span in rom_mod.carregar_funcoes_csv(args.censo):
            sementes.setdefault(span.addr, span.mode or "thumb")
    desmontagem = disasm_mod.desmontar_por_sementes(rom.data, sementes=sementes or None)
    resultado = conferir(desmontagem, rom.data)
    print(resultado.texto())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
