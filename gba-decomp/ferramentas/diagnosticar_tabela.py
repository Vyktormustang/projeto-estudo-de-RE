"""Diz POR QUE um `mov pc, rX` virou (ou nao virou) `switch` -- com o que foi medido.

    python ferramentas/diagnosticar_tabela.py ROM.gba                     # resumo
    python ferramentas/diagnosticar_tabela.py ROM.gba --site 0x08050F5C    # detalhe
    python ferramentas/diagnosticar_tabela.py ROM.gba --censo censo.csv --json saida.json

Existe por um defeito de relato que este projeto ja' cometeu duas vezes: dizer
"nao reconheci a tabela de casos" manda quem le procurar defeito no lugar errado.
As quatro tabelas recusadas na ROM de estudo parecem a mesma coisa de longe, e nao
sao: umas falham no guarda (`cmp rX, #k`), outras no proprio idioma, outras porque
a entrada da tabela cai em endereco que nao e' codigo.

A classificacao vem da MESMA funcao que o desmontador usa
(`disasm._tabela_de_casos_ou_motivo`): sonda que reimplementa a regra mede a
regra da sonda, nao a do programa.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gbadecomp import analise as analise_mod              # noqa: E402
from gbadecomp import disasm as disasm_mod                # noqa: E402
from gbadecomp import rom as rom_mod                      # noqa: E402


def _detalhe(imagem: bytes, base: int, cs, funcao, site: int) -> dict:
    """O que da' para medir em volta de um `mov pc, rX`, sem julgar."""
    ins = next((i for i in funcao.instrucoes if i.endereco == site), None)
    anteriores = sorted((i for i in funcao.instrucoes if i.endereco < site),
                        key=lambda i: i.endereco)
    detalhe = {
        "site": f"0x{site:08X}",
        "janela": f"0x{funcao.entrada:08X}",
        "semente": funcao.semente,
        "instrucao": f"{ins.mnemonic} {ins.operadores}".strip() if ins else "?",
        "bytes": ins.bytes_.hex(" ") if ins else "",
        "anteriores": [],
        "leitura_bruta": {},
    }
    for item in anteriores[-14:]:
        detalhe["anteriores"].append(
            {"endereco": f"0x{item.endereco:08X}",
             "bytes": item.bytes_.hex(" "),
             "asm": f"{item.mnemonic} {item.operadores}".strip()})
    # leitura bruta (sem os criterios): pool da base, guarda e as entradas
    for item in reversed(anteriores[-40:]):
        lida = disasm_mod._operandos_de(imagem, base, item, cs)
        if lida is None or lida.mnemonic != "ldr" or len(lida.operands) != 2:
            continue
        memoria = lida.operands[1]
        if (lida.operands[0].type == disasm_mod.capstone.arm.ARM_OP_REG
                and memoria.type == disasm_mod.capstone.arm.ARM_OP_MEM
                and memoria.mem.base == disasm_mod.capstone.arm.ARM_REG_PC):
            pool = ((lida.address + 4) & ~3) + memoria.mem.disp
            detalhe["leitura_bruta"]["pool em"] = f"0x{pool:08X}"
            valor = disasm_mod._ler32(imagem, base, pool)
            if valor is not None:
                detalhe["leitura_bruta"]["valor do pool"] = f"0x{valor:08X}"
                detalhe["leitura_bruta"]["tabela"] = f"0x{valor:08X}"
            break
    guarda = None
    for item in reversed(anteriores[-18:]):
        lida = disasm_mod._operandos_de(imagem, base, item, cs)
        if (lida is not None and lida.mnemonic.startswith("cmp")
                and len(lida.operands) == 2
                and lida.operands[1].type == disasm_mod.capstone.arm.ARM_OP_IMM):
            guarda = lida.operands[1].imm
            detalhe["leitura_bruta"]["guarda"] = (f"`{lida.mnemonic} "
                                                  f"{lida.op_str}` em "
                                                  f"0x{lida.address:08X}")
            break
    tabela_txt = detalhe["leitura_bruta"].get("tabela")
    if guarda is not None and tabela_txt:
        tabela = int(tabela_txt, 16)
        entradas = []
        for indice in range(guarda + 1):
            valor = disasm_mod._ler32(imagem, base, tabela + 4 * indice)
            if valor is None:
                entradas.append({"indice": indice, "valor": "(fora da imagem)"})
                continue
            alvo = valor & ~1
            lidas = list(cs.disasm(imagem[alvo - base:alvo - base + 4], alvo, count=1))
            entradas.append({
                "indice": indice,
                "valor": f"0x{valor:08X}",
                "primeira": (f"{lidas[0].mnemonic} {lidas[0].op_str}".strip()
                             if lidas else "(nao decodifica)"),
                "existe_no_alvo": bool(lidas) and disasm_mod.impossivel_no_arm7tdmi(
                    lidas[0], "thumb") is None,
            })
        detalhe["leitura_bruta"]["entradas"] = entradas
    return detalhe


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom")
    parser.add_argument("--censo", help="CSV do censo (sementes) -- opcional")
    parser.add_argument("--entrada", help="semente unica (0x08000041 = Thumb); "
                                          "padrao: vetor de reset do cabecalho")
    parser.add_argument("--site", action="append",
                        help="detalhe de um site (0x...); pode repetir")
    parser.add_argument("--json", help="gravar o diagnostico em JSON")
    args = parser.parse_args(argv)

    rom = rom_mod.GbaRom(args.rom)
    base = rom_mod.ROM_BASE
    imagem = rom.data
    sementes = None
    if args.entrada:
        valor = int(args.entrada, 0)
        sementes = {valor & ~1: "thumb" if valor & 1 else "arm"}
    if args.censo:
        # mesmas sementes que `analise.medir` usa: o CSV do censo, com o modo
        # declarado em cada linha (nao suposto)
        sementes = {}
        for span in rom_mod.carregar_funcoes_csv(args.censo):
            sementes.setdefault(span.addr, span.mode or "thumb")
    desmontagem = disasm_mod.desmontar_por_sementes(imagem, sementes=sementes)
    cs = disasm_mod._capstone("thumb")

    por_funcao = {f.entrada: f for f in desmontagem.funcoes.values()}
    reconhecidas = [(f.entrada, t) for f in desmontagem.funcoes.values() for t in f.tabelas]
    recusadas = [(f.entrada, site, motivo)
                 for f in desmontagem.funcoes.values() for site, motivo in f.tabelas_recusadas]

    print(f"funcoes ..................: {len(desmontagem.funcoes)}")
    print(f"tabelas reconhecidas .....: {len(reconhecidas)} "
          f"({sum(len(t.alvos) for _, t in reconhecidas)} casos lidos da ROM)")
    print(f"`mov pc, rX` recusados ...: {len(recusadas)}")
    sem_escala = [t for _, t in reconhecidas if t.deslocamento is None]
    print(f"reconhecidas SEM o `lsls` : {len(sem_escala)} (escala do indice nao medida)")

    motivos: collections.Counter = collections.Counter()
    exemplo: dict[str, tuple[int, int]] = {}
    for entrada, site, motivo in recusadas:
        chave = analise_mod.motivo_canonico(motivo)
        motivos[chave] += 1
        exemplo.setdefault(chave, (entrada, site))
    if motivos:
        print("\npor que nao virou switch:")
        for chave, n in motivos.most_common():
            entrada, site = exemplo[chave]
            print(f"  {n:5d}  {chave[:150]}")
            print(f"         ex: `mov pc` em 0x{site:08X}, na janela 0x{entrada:08X}")

    alvos = []
    if args.site:
        alvos = [int(valor, 16) for valor in args.site]
    elif args.json:
        alvos = sorted({site for _, site, _ in recusadas})
    detalhes = []
    for site in alvos:
        # A janela dona: pode estar em `.instrucoes` (instrucao desmontada) OU em
        # `.tabelas_recusadas` -- o `mov pc, rX` que fecha a funcao fica
        # registrado mesmo quando nao esta na lista de instrucoes lidas.
        funcao = next((f for f in desmontagem.funcoes.values()
                       if any(i.endereco == site for i in f.instrucoes)), None)
        if funcao is None:
            funcao = next((f for f in desmontagem.funcoes.values()
                           if any(endereco == site
                                  for endereco, _ in f.tabelas_recusadas)), None)
        if funcao is None:
            print(f"\n0x{site:08X}: nenhuma janela desmontada contem este endereco")
            continue
        # quem chama esta janela: se o guarda (`cmp rX, #k`) nao esta dentro,
        # pode estar em quem CHAMA -- e isso muda a resposta de "nao da' para
        # saber quantos casos existem" para "da' para confirmar pelo chamador".
        chamadores = []
        for outra in desmontagem.funcoes.values():
            for endereco, destino in outra.chamadas:
                if destino != funcao.entrada:
                    continue
                antes_bl = [i for i in outra.instrucoes if i.endereco < endereco][-5:]
                chamadores.append({
                    "quem": f"0x{outra.entrada:08X}",
                    "chamada": f"0x{endereco:08X}",
                    "antes": [f"{i.mnemonic} {i.operadores}".strip()
                              for i in antes_bl]})
        detalhe = _detalhe(imagem, base, cs, funcao, site)
        motivo = next((m for _, s, m in recusadas if s == site), "")
        # ATENCAO: a funcao espera a instrucao do CAPSTONE, nao o `Instrucao` do
        # desmontador (o primeiro erro desta sonda foi exatamente esse: passar o
        # objeto errado e ler `address` dele).
        lidas_site = list(cs.disasm(imagem[site - base:site - base + 4], site, count=1))
        if not lidas_site:
            print(f"\n0x{site:08X}: nao decodifica como instrucao")
            continue
        tabela, por_que = disasm_mod._tabela_de_casos_ou_motivo(
            imagem, base,
            sorted((i for i in funcao.instrucoes if i.endereco < site),
                   key=lambda i: i.endereco),
            lidas_site[0], cs)
        detalhe["veredito"] = "RECONHECIDA" if tabela is not None else "recusada"
        detalhe["motivo"] = por_que or motivo
        detalhe["chamadores"] = chamadores
        if tabela is not None:
            detalhe["tabela_lida"] = {"endereco": f"0x{tabela.tabela:08X}",
                                      "casos": len(tabela.alvos),
                                      "deslocamento": tabela.deslocamento}
        detalhes.append(detalhe)
        if args.site:
            print()
            print(f"=== 0x{site:08X} na janela 0x{funcao.entrada:08X} "
                  f"(semente: {funcao.semente}) ===")
            print(f"veredito: {detalhe['veredito']} -- {detalhe['motivo']}")
            print("instrucoes anteriores:")
            for item in detalhe["anteriores"]:
                print(f"   {item['endereco']}  {item['bytes']:<12} {item['asm']}")
            if chamadores:
                print(f"quem chama 0x{funcao.entrada:08X} ({len(chamadores)}):")
                for chamador in chamadores[:6]:
                    print(f"   {chamador['chamada']} de {chamador['quem']}: "
                          f"{' | '.join(chamador['antes'])}")
            for rotulo, valor in detalhe["leitura_bruta"].items():
                if rotulo == "entradas":
                    print(f"entradas lidas ({len(valor)}):")
                    for entrada in valor:
                        marca = "" if entrada.get("existe_no_alvo") else "   <- NAO existe no alvo"
                        print(f"   [{entrada['indice']}] {entrada['valor']}  "
                              f"{entrada['primeira']}{marca}")
                else:
                    print(f"{rotulo}: {valor}")

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"funcoes": len(desmontagem.funcoes),
             "reconhecidas": len(reconhecidas),
             "casos_lidos": sum(len(t.alvos) for _, t in reconhecidas),
             "recusadas": len(recusadas),
             "motivos": dict(motivos.most_common()),
             "detalhes": detalhes}, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nJSON gravado em {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
