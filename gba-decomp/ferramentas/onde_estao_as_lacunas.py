#!/usr/bin/env python3
"""Onde estao as lacunas do levantamento -- e de onde vem cada alvo recusado.

Por que isto existe: o resumo (`cli analisar`) diz QUANTAS instrucoes ficaram sem
traducao, mas nao diz ONDE nem POR QUE. Sem isso a proxima rodada vira chute
sobre o que atacar. Este script responde tres perguntas, todas medidas na ROM:

  1. As lacunas estao espalhadas ou concentradas? (quantas por pagina de 4 KB)
  2. Em que tipo de codigo elas caem? (funcao do censo x descoberta pelo boot)
  3. `bx rN` sem origem rastreada: DE ONDE vem o rN?

Sobre (3): o lifter recusa `bx rN` quando nao viu o alvo ser carregado da pilha
como retorno. Este script NAO usa o lifter para responder -- ele olha o desmonte
cru e procura a ULTIMA escrita em rN antes do `bx`, classificando a origem da
escrita (pilha, literal de pool, outro registrador, imediato). A leitura e
heuristica de texto (nao e execucao), e diz isso: serve para escolher o que
implementar, nao para afirmar semantica.

Uso:
    python ferramentas/onde_estao_as_lacunas.py ROM.gba --censo functions.csv \\
        --exemplos 3 [--json lacunas.json] [--pagina 4096] [--so-motivo "bx"]
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import capstone                                            # noqa: E402
from gbadecomp import analise as analise_mod              # noqa: E402
from gbadecomp import decompile as decompile_mod          # noqa: E402
from gbadecomp import disasm as disasm_mod                # noqa: E402
from gbadecomp import rom as rom_mod                      # noqa: E402

# Como o THUMB carrega um alvo de desvio. A ordem importa: o primeiro padrao que
# casa vence. Tudo aqui e' foi escrito a partir das instrucoes que apareceram na
# ROM, nao de um manual genérico -- o que nao casar sai como "nao identificada",
# que e' uma resposta util (diz que ainda nao se sabe), diferente de chutar.
PADROES_DE_CARGA = (
    ("pilha (pop)", re.compile(r"^pop\b")),
    ("pilha (ldr do sp)", re.compile(r"^ldr\w*\s+\w+\s*,\s*\[\s*sp")),
    ("pilha (ldm/ldmia do sp)", re.compile(r"^ldm\w*\s+sp")),
    ("literal de pool (ldr [pc])", re.compile(r"^ldr\w*\s+\w+\s*,\s*\[\s*pc")),
    ("imediato (mov/ldr #)", re.compile(r"^(mov|movs)\s+\w+\s*,\s*#")),
    ("endereco fixo (add de pc)", re.compile(r"^(add|adds)\s+\w+\s*,\s*pc")),
    ("outro registrador", re.compile(r"^(mov|movs|add|adds|sub|subs|ldr\w*|orr|and|bic)\b")),
)


def _registradores_escritos(instrucao) -> list[str]:
    """Registradores que a instrucao escreve, lidos do texto do desmonte.

    Detalhe que importa AQUI: `pop {r1}` e `ldmia sp!, {r1, r2}` escrevem uma
    LISTA -- olhar so o primeiro operando faria a varredura nao enxergar o
    proprio carregamento que se esta procurando, e a resposta viraria "nao ha
    escrita anterior" para o caso mais comum da ROM.
    """
    texto = instrucao.operadores.strip()
    if texto.startswith("{"):
        lista = texto.split("}", 1)[0].strip("{} ")
        return [r.strip() for r in lista.split(",") if r.strip()]
    m = re.match(r"^\s*(\w+)", texto)
    return [m.group(1)] if m else []


def _origem_do_alvo(instrucoes: list, registro: str) -> tuple[str, str]:
    """Ultima escrita em `registro` antes do fim da lista: origem e instrucao."""
    for instrucao in reversed(instrucoes[:-1]):
        if registro not in _registradores_escritos(instrucao):
            continue
        texto = f"{instrucao.mnemonic} {instrucao.operadores}".strip()
        for rotulo, padrao in PADROES_DE_CARGA:
            if padrao.match(instrucao.mnemonic + " " + instrucao.operadores):
                return rotulo, texto
        return "nao identificada", texto
    return "nenhuma escrita anterior na funcao", ""


def _motivo(item: str) -> str:
    return item.partition(": ")[2] or item


def _endereco(item: str) -> int | None:
    m = re.match(r"^0x([0-9A-Fa-f]+)", item)
    return int(m.group(1), 16) if m else None


def coletar(rom_caminho: str, censo: str | None) -> dict:
    rom = rom_mod.GbaRom(rom_caminho)
    sementes: dict[int, str] = {}
    nomes: dict[int, str] = {}
    do_censo: set[int] = set()
    if censo:
        for span in rom_mod.carregar_funcoes_csv(censo):
            sementes.setdefault(span.addr, span.mode or "thumb")
            do_censo.add(span.addr)
            if span.name:
                nomes[span.addr] = span.name
    desmontagem = disasm_mod.desmontar_por_sementes(rom.data, sementes=sementes or None)
    codigo = decompile_mod.decompilar(desmontagem, rom.data, nomes=nomes or None)

    lacunas = []
    for funcao in codigo.funcoes:
        for item in funcao.nao_levantadas:
            lacunas.append({
                "funcao": funcao.endereco,
                "nome": funcao.nome,
                "do_censo": funcao.endereco in do_censo,
                "instrucao": _endereco(item),
                "motivo": _motivo(item),
                "texto": item,
            })
    return {"desmontagem": desmontagem, "codigo": codigo, "lacunas": lacunas,
            "nomes": nomes, "do_censo": do_censo, "imagem": rom.data}


def analisar(dados: dict, pagina: int, exemplos: int, so_motivo: str | None) -> dict:
    desmontagem = dados["desmontagem"]
    lacunas = [l for l in dados["lacunas"]
               if not so_motivo or so_motivo in l["motivo"]]
    balanceamento = {f.endereco: f.balanceamento for f in dados["codigo"].funcoes}

    # canoniza antes de contar: quase todo motivo carrega o endereco dentro do
    # texto, entao sem isto cada motivo vira um grupo de 1 e o histograma nao
    # agrupa nada (a soma do relatorio nao fecha com o total de lacunas).
    por_motivo = collections.Counter(
        analise_mod.motivo_canonico(l["motivo"]) for l in lacunas)
    por_mnemonico = collections.Counter(
        (l["texto"].split(" ", 2)[1].split(",")[0].split(" ")[0]
         if " " in l["texto"] else "?") for l in lacunas)

    # (1) concentracao: pagina de 4 KB -> quantas lacunas e quantas funcoes
    funcoes_por_pagina: dict[int, set] = collections.defaultdict(set)
    lacunas_por_pagina: collections.Counter = collections.Counter()
    for l in lacunas:
        base = l["funcao"] & ~(pagina - 1)
        funcoes_por_pagina[base].add(l["funcao"])
        lacunas_por_pagina[base] += 1

    # (2) censo x boot: calar sobre o que nao foi medido
    do_censo = len([l for l in lacunas if l["do_censo"]])
    fora_do_censo = len(lacunas) - do_censo

    # (3) `bx rN`: de onde vem o alvo
    origens_bx: collections.Counter = collections.Counter()
    exemplos_bx: dict[str, list[str]] = collections.defaultdict(list)
    for l in lacunas:
        if not l["motivo"].startswith("desvio indireto por registrador"):
            continue
        funcao = desmontagem.funcoes.get(l["funcao"])
        if funcao is None or l["instrucao"] is None:
            continue
        ordenadas = sorted(funcao.instrucoes, key=lambda i: i.endereco)
        ate = [i for i in ordenadas if i.endereco <= l["instrucao"]]
        if not ate:
            continue
        alvo = ate[-1].operadores.strip()
        origem, texto = _origem_do_alvo(ate, alvo)
        origens_bx[origem] += 1
        chave = f"{origem} -> {ate[-1].mnemonic} {alvo}"
        if len(exemplos_bx[chave]) < exemplos:
            anteriores = " | ".join(f"{i.mnemonic} {i.operadores}" for i in ate[-4:-1])
            # O balanceamento de pilha vem do proprio levantamento: se a maioria
            # dos `bx rN` estiver em funcao "desequilibrada", o problema NAO e a
            # origem do alvo (tabela/ponteiro) e sim a contagem de slots da
            # pilha -- sao dois consertos diferentes, e este campo diz qual.
            exemplos_bx[chave].append(
                f"0x{l['instrucao']:08X} em {l['nome']} "
                f"(pilha: {balanceamento.get(l['funcao'], '?')}) -- antes: {anteriores}")

    # (4) O DESVIO RECUSADO VAI PARA ONDE? "para endereco que nao foi desmontado"
    # e' uma frase que nao ajuda quem le. O que ajuda (e o que decide o proximo
    # conserto) e' saber se o destino e' instrucao de outra janela ja desmontada,
    # buraco dentro da propria faixa, ou endereco que NINGUEM desmontou -- as tres
    # coisas pedem acoes diferentes.
    destinos = _para_onde_vai_o_desvio(desmontagem, lacunas, dados.get("nomes") or {})

    # contexto impresso para cada motivo (o que o lifter viu antes de recusar)
    contexto = []
    for l in lacunas[:exemplos * 4]:
        funcao = desmontagem.funcoes.get(l["funcao"])
        if funcao is None or l["instrucao"] is None:
            continue
        ate = [i for i in sorted(funcao.instrucoes, key=lambda i: i.endereco)
               if i.endereco <= l["instrucao"]]
        contexto.append({
            "motivo": l["motivo"],
            "funcao": f"0x{l['funcao']:08X} ({l['nome']}, "
                      f"{'censo' if l['do_censo'] else 'fora do censo'})",
            "antes": [f"{i.endereco:08X} {i.mnemonic} {i.operadores}" for i in ate[-5:]],
        })

    return {
        "total_lacunas": len(lacunas),
        "por_motivo": dict(por_motivo.most_common()),
        "por_mnemonico": dict(por_mnemonico.most_common()),
        "no_censo": do_censo,
        "fora_do_censo": fora_do_censo,
        "paginas": [{"pagina": f"0x{p:08X}", "lacunas": n,
                     "funcoes": len(funcoes_por_pagina[p])}
                    for p, n in lacunas_por_pagina.most_common(12)],
        "destinos_de_desvio": destinos,
        # (5) E O QUE TEM NOS ALVOS QUE NINGUEM COBRIU? A tabela acima diz quantos
        # desvios foram recusados por classe; esta diz o que HA' em cada classe de
        # alvo (instrucao, descarte ja' medido, ou bytes lidos na hora).
        "alvos_nao_cobertos": alvos_nao_cobertos(dados),
        "origens_bx": dict(origens_bx.most_common()),
        "exemplos_bx": {k: v for k, v in list(exemplos_bx.items())[:12]},
        "contexto": contexto,
    }


def relatar(medido: dict, exemplos: int) -> str:
    saida = [f"lacunas (instrucoes recusadas pelo lifter): {medido['total_lacunas']}",
             f"  no censo: {medido['no_censo']} | fora do censo: {medido['fora_do_censo']}",
             "", "por motivo:"]
    for motivo, n in list(medido["por_motivo"].items())[:15]:
        saida.append(f"  {n:5d}  {motivo[:110]}")
    saida += ["", "por mnemonico:"]
    for mnemonico, n in list(medido["por_mnemonico"].items())[:15]:
        saida.append(f"  {n:5d}  {mnemonico}")
    saida += ["", "concentracao (paginas de 4 KB com mais lacunas):"]
    for pagina in medido["paginas"]:
        saida.append(f"  {pagina['pagina']}: {pagina['lacunas']:4d} lacunas "
                     f"em {pagina['funcoes']} funcoes")
    if medido.get("destinos_de_desvio", {}).get("por_classe"):
        d = medido["destinos_de_desvio"]
        saida += ["", "para onde vai o desvio recusado:"]
        for classe, n in d["por_classe"].items():
            saida.append(f"  {n:5d}  {classe}")
        for exemplo in d["exemplos"].get("instrucao de outra janela", [])[:3]:
            saida.append(f"        {exemplo}")
        for exemplo in d["exemplos"].get("ninguem desmontou", [])[:3]:
            saida.append(f"        SEM DONO: {exemplo}")
        if d["paginas_dos_destinos"]:
            saida.append("    destinos por pagina: " + ", ".join(
                f"{p['pagina']}={p['n']}" for p in d["paginas_dos_destinos"][:6]))
    alvos = medido.get("alvos_nao_cobertos") or {}
    if alvos.get("alvos"):
        saida += ["", "alvos de desvio imediato (todos os `b`/`bl` da desmontagem):"]
        for classe, n in alvos["alvos"].items():
            saida.append(f"  {n:5d}  {classe}")
        for porque, n in alvos["veredito_dos_nao_tentados"].items():
            saida.append(f"  {n:5d}  veredito dos nunca tentados: {porque}")
        for chave, lista in alvos["exemplos"].items():
            for exemplo in lista[:2]:
                saida.append(f"        {exemplo}")
    if medido["origens_bx"]:
        saida += ["", "de onde vem o registrador do `bx rN` (heuristica: ultima "
                      "escrita antes do bx, lida do desmonte):"]
        for origem, n in medido["origens_bx"].items():
            saida.append(f"  {n:5d}  {origem}")
        for chave, lista in medido["exemplos_bx"].items():
            saida.append(f"    {chave}")
            for exemplo in lista:
                saida.append(f"        {exemplo}")
    if medido["contexto"]:
        saida += ["", f"contexto das primeiras lacunas (ate {exemplos} por bloco):"]
        for bloco in medido["contexto"]:
            saida.append(f"  {bloco['funcao']}: {bloco['motivo'][:90]}")
            for linha in bloco["antes"]:
                saida.append(f"      {linha}")
    return "\n".join(saida)


def _para_onde_vai_o_desvio(desmontagem, lacunas: list, nomes: dict) -> dict:
    """Classifica cada desvio recusado pelo destino que ele aponta.

    Classes (mutuamente exclusivas, na ordem em que sao testadas):
      instrucao de outra janela .... o destino E uma instrucao desmontada, de
                                    outra funcao: a leitura continua la (bloco
                                    comum). Nada a implementar; o que faltava era
                                    dizer PARA ONDE vai.
      buraco dentro da propria faixa  o destino esta entre a entrada e o fim
                                    desta funcao, mas nao foi desmontado
      buraco de outra janela ....... o destino cai no intervalo de outra funcao
                                    sem ser instrucao dela
      ninguem desmontou ............ nenhuma funcao passou por esse endereco:
                                    e' o caso que merece investigacao (dado?)
    """
    import re as _re
    donos: dict[int, list[int]] = collections.defaultdict(list)
    faixas: list[tuple[int, int, int]] = []
    for f in desmontagem.funcoes.values():
        for instrucao in f.instrucoes:
            donos[instrucao.endereco].append(f.entrada)
        faixas.append((f.entrada, f.fim, f.entrada))
    faixas.sort()

    def janela_que_contem(endereco: int) -> int | None:
        for entrada, fim, _ in faixas:
            if entrada <= endereco < fim:
                return entrada
        return None

    contagem: collections.Counter = collections.Counter()
    exemplos: dict[str, list[str]] = collections.defaultdict(list)
    por_faixa: collections.Counter = collections.Counter()
    for l in lacunas:
        motivo = l["motivo"]
        if not (motivo.startswith("salto para fora") or motivo.startswith("desvio para")):
            continue
        achado = _re.search(r"0x([0-9A-Fa-f]{8})", motivo)
        if not achado:
            continue
        alvo = int(achado.group(1), 16)
        funcao = desmontagem.funcoes.get(l["funcao"])
        fim = funcao.fim if funcao else l["funcao"]
        if alvo in donos and l["funcao"] not in donos[alvo]:
            classe = "instrucao de outra janela"
        elif funcao is not None and l["funcao"] <= alvo < fim:
            classe = "buraco dentro da propria faixa"
        elif janela_que_contem(alvo) is not None:
            classe = "buraco de outra janela"
        else:
            classe = "ninguem desmontou"
        contagem[classe] += 1
        por_faixa[f"0x{alvo & ~0xFFF:08X}"] += 1
        if len(exemplos[classe]) < 4:
            dono = donos.get(alvo, [])
            rotulo = ", ".join(f"0x{d:08X}" for d in dono) or "-"
            exemplos[classe].append(
                f"0x{alvo:08X} (janela dona: {rotulo}) <- desvio em "
                f"0x{l['instrucao']:08X} de 0x{l['funcao']:08X} "
                f"({nomes.get(l['funcao'], '(sem nome no censo)')})")
    return {
        "por_classe": dict(contagem.most_common()),
        "paginas_dos_destinos": [{"pagina": p, "n": n}
                                 for p, n in por_faixa.most_common(8)],
        "exemplos": {k: v for k, v in exemplos.items()},
    }


def alvos_nao_cobertos(dados: dict, limite: int = 40) -> dict:
    """Cada alvo de desvio imediato que NAO e' instrucao de janela nenhuma.

    A pergunta que decide se vale "preencher buraco" com semente: os alvos que
    nunca foram tentados (nem desmontados, nem descartados como semente) sao
    codigo perdido ou dado? A resposta sai dos BYTES REAIS, no modo da janela
    dona, lidos ate' um retorno ou ate' a primeira instrucao que nao existe no
    ARM7TDMI. Se a leitura morre na primeira, ali e' dado -- e semear seria ler
    dado como codigo, o defeito que a rodada r13 desfez.

    A conta fecha com a tabela de destinos: um alvo recusado ou ja' e'
    instrucao (outra janela), ou ja' foi tentado e descartado, ou esta' neste
    balde. Sem os tres numeros juntos, "102 recusas por buraco" parece codigo
    faltando; com eles, ve-se quanto e' dado medido.
    """
    desmontagem = dados["desmontagem"]
    imagem = dados.get("imagem") or b""
    base = desmontagem.base
    cs_de = {modo: disasm_mod._capstone(modo) for modo in ("thumb", "arm")}
    cobertos = {i.endereco for f in desmontagem.funcoes.values() for i in f.instrucoes}
    tentados = set(desmontagem.descartes)

    contagem: collections.Counter = collections.Counter()
    veredito: collections.Counter = collections.Counter()
    exemplos: dict[str, list[str]] = collections.defaultdict(list)
    for f in desmontagem.funcoes.values():
        cs = cs_de[f.modo]
        for instrucao in f.instrucoes:
            if not instrucao.mnemonic.startswith("b"):
                continue          # so' `b`, `b<cond>` e `bl` tem alvo imediato
            uma = list(cs.disasm(instrucao.bytes_, instrucao.endereco, count=1))
            if not uma or not uma[0].group(capstone.CS_GRP_JUMP):
                continue          # `bx`/`blx` nao tem imediato; `bl` e' chamada
            operandos = uma[0].operands
            if not operandos or operandos[0].type != capstone.arm.ARM_OP_IMM:
                continue
            alvo = operandos[0].imm & 0xFFFFFFFF
            if not (base <= alvo < base + len(imagem)):
                contagem["fora da imagem"] += 1
                continue
            if alvo in cobertos:
                contagem["coberto (instrucao de alguma janela)"] += 1
                continue
            if alvo in tentados:
                contagem["ja' tentado como semente (descartado: dado)"] += 1
                continue
            contagem["nunca tentado"] += 1
            lidas, porque = [], "limite de instrucoes sem retorno"
            atual = alvo
            for _ in range(limite):
                uma = list(cs.disasm(imagem[atual - base:atual - base + 4], atual, count=1))
                if not uma:
                    porque = "para na primeira: codigo invalido"
                    break
                ins = uma[0]
                # OS DOIS motivos que o levantador usa para dizer "isto nao
                # existe no alvo": o de mnemonic (que tambem PARA a leitura no
                # desmontador) e o de FORMA por tamanho de codificacao (que so'
                # o levantador pergunta, de proposito -- ver o comentario de
                # `disasm.forma_impossivel_no_thumb1`). Perguntar so' pelo
                # primeiro deixaria passar dado do Thumb-2 que decodifica com
                # cara de instrucao -- `adc r4, r4, #0xd000` e' o exemplo medido.
                motivo = (disasm_mod.impossivel_no_arm7tdmi(ins, f.modo)
                          or disasm_mod.forma_impossivel_no_thumb1(ins, f.modo))
                if motivo is not None:
                    porque = f"para na primeira: {motivo}"
                    break
                lidas.append(f"{ins.mnemonic} {ins.op_str}")
                if disasm_mod._eh_retorno(ins):
                    porque = "a leitura fecha (chega a um retorno)"
                    break
                atual += len(ins.bytes)
            veredito[porque.split(":")[0]] += 1
            if len(exemplos[porque]) < 3:
                exemplos[porque].append(
                    f"0x{alvo:08X} <- desvio em 0x{instrucao.endereco:08X} de "
                    f"0x{f.entrada:08X} ({f.semente}) | {porque} | "
                    f"{' | '.join(lidas[:4]) or '(nada)'}")
    return {
        "alvos": dict(contagem.most_common()),
        "veredito_dos_nao_tentados": dict(veredito.most_common()),
        "exemplos": {k: v for k, v in list(exemplos.items())[:6]},
    }


def listar_regiao(dados: dict, inicio: int, fim: int) -> str:
    """Desmonte cru de uma faixa, dizendo a QUAL funcao cada endereco pertence.

    Serve para o caso que mais confunde: o MESMO endereco aparecendo em duas
    funcoes. Sem isso, "a funcao 0x08018258 tem um bx em 0x0801824C" (endereco
    ANTES da propria entrada) parece bug de impressao -- e nao e: e' a mesma
    faixa de codigo reivindicada por duas descobertas diferentes. Aqui isso fica
    visivel: a linha mostra todas as funcoes que contem o endereco.
    """
    desmontagem = dados["desmontagem"]
    donos: dict[int, list[str]] = collections.defaultdict(list)
    for funcao in desmontagem.funcoes.values():
        for instrucao in funcao.instrucoes:
            donos[instrucao.endereco].append(f"0x{funcao.entrada:08X}")
    linhas = []
    for endereco in sorted(donos):
        if not (inicio <= endereco < fim):
            continue
        instrucao = next(i for f in desmontagem.funcoes.values()
                         for i in f.instrucoes if i.endereco == endereco)
        proprios = donos[endereco]
        marca = "varias: " + ", ".join(proprios) if len(proprios) > 1 else proprios[0]
        linhas.append(f"{endereco:08X}  {instrucao.bytes_.hex():<8} "
                      f"{instrucao.mnemonic:<8} {instrucao.operadores:<28} [{marca}]")
    return "\n".join(linhas) or "(nada desmontado nesta faixa)"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom")
    parser.add_argument("--censo", help="functions.csv do censo (mesmas sementes)")
    parser.add_argument("--json", help="gravar a medicao neste arquivo")
    parser.add_argument("--pagina", type=int, default=4096, help="tamanho da pagina")
    parser.add_argument("--exemplos", type=int, default=3)
    parser.add_argument("--so-motivo", help="medir apenas lacunas com este motivo")
    parser.add_argument("--regiao", metavar="0xINICIO-0xFIM",
                        help="listar o desmonte da faixa, com a funcao dona")
    args = parser.parse_args(argv)

    dados = coletar(args.rom, args.censo)
    if args.regiao:
        inicio, _, fim = args.regiao.partition("-")
        print(listar_regiao(dados, int(inicio, 0), int(fim, 0)))
        return 0
    medido = analisar(dados, args.pagina, args.exemplos, args.so_motivo)
    print(relatar(medido, args.exemplos))
    if args.json:
        Path(args.json).write_text(json.dumps(medido, indent=2, ensure_ascii=False),
                                   encoding="utf-8")
        print(f"\nJSON gravado em {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
