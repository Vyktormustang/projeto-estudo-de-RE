"""Interface de linha de comando do gbadecomp.

    python -m gbadecomp.cli rodada                  # corpus sintetico: prova o pipeline
    python -m gbadecomp.cli disasm ROM.gba          # funcoes, chamadas e listagem
    python -m gbadecomp.cli decompilar ROM.gba -o saida.c
    python -m gbadecomp.cli relatorio ROM.gba       # cabecalho, funcoes, espaco livre
    python -m gbadecomp.cli levantar ROM.gba --censo functions.csv

Regra desta CLI: nunca dizer mais do que foi medido. Onde nao existe
verdade-terreno (ROM de terceiros), o texto diz isso com todas as letras.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import decompile as decompile_mod
from . import disasm as disasm_mod
from . import reconstruir as reconstruir_mod
from . import rom as rom_mod


def _cmd_rodada(args) -> int:
    resultado = reconstruir_mod.rodada_corpus(diretorio=args.saida, zig=args.zig)
    print(resultado.resumo())
    if resultado.relatorio_original:
        print()
        print(resultado.relatorio_original.texto())
        print()
        print(resultado.relatorio_levantado.texto() if resultado.relatorio_levantado
              else "sem verificacao do C levantado")
    falhas = 0
    for rel in (resultado.relatorio_original, resultado.relatorio_levantado):
        falhas += len(rel.reprovados) if rel else 1
    return 0 if falhas == 0 and not resultado.erros else 1


def _cmd_disasm(args) -> int:
    rom = rom_mod.GbaRom(args.rom)
    sementes = _sementes(args)
    desmontagem = disasm_mod.desmontar_por_sementes(rom.data, sementes=sementes,
                                                    seguir_pool=not args.sem_pool)
    if args.json:
        Path(args.json).write_text(desmontagem.para_json(), encoding="utf-8")
        print(f"JSON gravado em {args.json}")
    if args.listagem:
        texto = desmontagem.texto()
        Path(args.listagem).write_text(texto, encoding="utf-8")
        print(f"listagem gravada em {args.listagem} "
              f"({len(texto.splitlines())} linhas)")
    if args.resumo or not (args.json or args.listagem):
        print(desmontagem.texto().splitlines()[0])
        print(f"arestas de chamada: {len(desmontagem.arestas())}")
        for a, b in desmontagem.arestas()[:40]:
            print(f"   0x{a:08X} -> 0x{b:08X}")
        if len(desmontagem.arestas()) > 40:
            print(f"   ... {len(desmontagem.arestas()) - 40} outras")
    if desmontagem.avisos:
        print("avisos:", *desmontagem.avisos, sep="\n  ")
    return 0


def _cmd_decompilar(args) -> int:
    rom = rom_mod.GbaRom(args.rom)
    desmontagem = disasm_mod.desmontar_por_sementes(rom.data, sementes=_sementes(args))
    codigo = decompile_mod.decompilar(desmontagem, rom.data)
    destino = Path(args.output) if args.output else Path("levantado.c")
    destino.write_text(codigo.texto(), encoding="utf-8")
    print(f"C levantado gravado em {destino}")
    print(f"funcoes completas .....: {len(codigo.completas)}")
    print(f"funcoes incompletas ...: {len(codigo.incompletas)}")
    for funcao in codigo.incompletas[:20]:
        print(f"   0x{funcao.endereco:08X}: {'; '.join(funcao.nao_levantadas[:2])}")
    if len(codigo.incompletas) > 20:
        print(f"   ... {len(codigo.incompletas) - 20} outras (lista completa no cabecalho "
              f"de cada funcao no .c)")
    return 0


def _cmd_relatorio(args) -> int:
    rom = rom_mod.GbaRom(args.rom)
    print(json.dumps(rom.report().to_json(), indent=2, ensure_ascii=False))
    if args.censo:
        funcoes = rom_mod.carregar_funcoes_csv(args.censo)
        print(f"\nfuncoes no censo {args.censo}: {len(funcoes)}")
        import collections
        modos = collections.Counter(f.mode for f in funcoes if f.mode)
        print("   modos:", dict(modos))
    return 0


def _cmd_levantar(args) -> int:
    """Fluxo para uma ROM de verdade: censo + boot como sementes."""
    rom = rom_mod.GbaRom(args.rom)
    sementes = _sementes(args)
    nomes: dict[int, str] = {}
    if args.censo:
        for span in rom_mod.carregar_funcoes_csv(args.censo):
            sementes.setdefault(span.addr, span.mode or "thumb")
            if span.name:
                nomes[span.addr] = _identificador(span.name)
    desmontagem = disasm_mod.desmontar_por_sementes(rom.data, sementes=sementes)
    codigo = decompile_mod.decompilar(desmontagem, rom.data, nomes=nomes or None)
    destino = Path(args.output) if args.output else Path("levantado_rom.c")
    destino.write_text(codigo.texto(), encoding="utf-8")
    print(f"sementes ................: {len(sementes)}")
    print(f"funcoes descobertas .....: {len(desmontagem.funcoes)}")
    print(f"instrucoes ..............: {desmontagem.total_instrucoes}")
    print(f"funcoes levantadas p/ C .: {len(codigo.completas)} "
          f"(incompletas: {len(codigo.incompletas)})")
    print(f"C gravado em ............: {destino}")
    print()
    print("LIMITE HONESTO: nesta ROM nao existe verdade-terreno conhecida, entao o "
          "C acima NAO esta provado -- so foi gerado. Prova exige comparar com o "
          "comportamento do binario original.")
    return 0


def _identificador(nome: str) -> str:
    """Nome do censo -> identificador C valido (sem inventar nem renomear)."""
    limpo = "".join(c if c.isalnum() or c == "_" else "_" for c in nome)
    if limpo[:1].isdigit():
        limpo = "_" + limpo
    return limpo


def _sementes(args) -> dict[int, str]:
    if getattr(args, "entrada", None):
        valor = int(args.entrada, 0)
        return {valor & ~1: "thumb" if valor & 1 else "arm"}
    return {}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="gbadecomp", description=__doc__.splitlines()[0])
    parser.add_argument("--zig", help="caminho do zig (compilador cruzado)")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("rodada", help="roda o pipeline completo no corpus sintetico")
    p.add_argument("--saida", help="diretorio de trabalho (padrao: temporario)")
    p.set_defaults(func=_cmd_rodada)

    p = sub.add_parser("disasm", help="descoberta recursiva de funcoes")
    p.add_argument("rom")
    p.add_argument("--entrada", help="endereco de entrada (0x080000C0); padrao: vetor de boot")
    p.add_argument("--json", help="gravar desmontagem em JSON")
    p.add_argument("--listagem", help="gravar listagem legivel")
    p.add_argument("--sem-pool", action="store_true", default=False,
                   help="nao seguir literais de pool")
    p.add_argument("--resumo", action="store_true", default=False)
    p.set_defaults(func=_cmd_disasm)

    p = sub.add_parser("decompilar", help="levantar o binario para C")
    p.add_argument("rom")
    p.add_argument("--entrada")
    p.add_argument("-o", "--output", help="arquivo .c de saida")
    p.set_defaults(func=_cmd_decompilar)

    p = sub.add_parser("relatorio", help="cabecalho, espaco livre e censo")
    p.add_argument("rom")
    p.add_argument("--censo", help="functions.csv do censo do projeto")
    p.set_defaults(func=_cmd_relatorio)

    p = sub.add_parser("levantar", help="ROM real: censo + boot como sementes")
    p.add_argument("rom")
    p.add_argument("--censo", help="functions.csv (sementes por nome/endereco)")
    p.add_argument("--entrada", help="endereco de entrada extra")
    p.add_argument("-o", "--output", help="arquivo .c de saida")
    p.set_defaults(func=_cmd_levantar)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
