#!/usr/bin/env python3
"""Diz se dois `.o` diferem no CODIGO gerado ou so' em metadados do ELF.

    conferir_objetos.py A.o B.o [--json saida.json]

Existe porque "o objeto mudou" nao diz nada sobre o que mudou. Medido neste
projeto, nos dois sentidos:

* um conserto de TEXTO de recusa (que vive dentro de comentario C) mudou o
  `.text` -- porque na mesma passada o `stmdb sp!, {lr}` do ARM deixou de passar
  pelo caminho generico de transferencia multipla e entrou no caminho da pilha:
  8 bytes a mais de codigo, e e' isso que o objeto mudou;
* um polimento de legibilidade (`0x...u + 0x0u` virando `0x...u`, 7 bytes menos
  de C) nao mudou byte nenhum do objeto.

Sem separar secao por secao, os dois casos se parecem ("o sha256 mudou"). Aqui a
saida separa: secao igual byte a byte, secao diferente, e -- quando o `.text`
muda -- QUAL funcao mudou de tamanho, pelo nome, que e' o que interessa.

A sonda nunca derruba: objeto ilegivel vira veredito, nao excecao.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

SECOES_DE_CODIGO = (".text", ".data", ".rodata", ".ARM.exidx")


def _secoes(caminho: Path) -> dict[str, tuple[int, str]]:
    """nome -> (tamanho, sha256 do conteudo). Secao sem conteudo legivel entra
    como `?` -- o que importa e' que ela nao derruba a comparacao."""
    from elftools.elf.elffile import ELFFile

    with caminho.open("rb") as fh:
        elf = ELFFile(fh)
        saida: dict[str, tuple[int, str]] = {}
        for secao in elf.iter_sections():
            try:
                dados = secao.data()
            except Exception as erro:                      # secao SHT_NOBITS
                dados = None
                resumo = f"? {type(erro).__name__}"
            else:
                resumo = hashlib.sha256(dados).hexdigest()[:16]
            saida[secao.name] = (int(secao["sh_size"]), resumo)
        return saida


def _simbolos(caminho: Path) -> dict[str, tuple[int, int]]:
    """nome -> (valor, tamanho) para todo simbolo de FUNCAO com tamanho > 0."""
    from elftools.elf.elffile import ELFFile

    with caminho.open("rb") as fh:
        elf = ELFFile(fh)
        tabela = elf.get_section_by_name(".symtab")
        if tabela is None:
            return {}
        saida: dict[str, tuple[int, int]] = {}
        for simbolo in tabela.iter_symbols():
            if simbolo["st_info"]["type"] != "STT_FUNC":
                continue
            if simbolo["st_size"] == 0:
                continue
            # nome repetido (funcao pequena com alias?): guarda o maior
            atual = saida.get(simbolo.name)
            novo = (int(simbolo["st_value"]), int(simbolo["st_size"]))
            if atual is None or novo[1] > atual[1]:
                saida[simbolo.name] = novo
        return saida


def conferir(a: Path, b: Path) -> dict:
    secoes_a, secoes_b = _secoes(a), _secoes(b)
    iguais = sorted(n for n in secoes_a if secoes_a[n] == secoes_b.get(n))
    diferentes = []
    for nome in sorted(set(secoes_a) | set(secoes_b)):
        ta, tb = secoes_a.get(nome), secoes_b.get(nome)
        if ta == tb:
            continue
        deem = {"secao": nome,
                "tamanho_a": ta[0] if ta else None,
                "tamanho_b": tb[0] if tb else None,
                "sha_a": ta[1] if ta else None,
                "sha_b": tb[1] if tb else None}
        deem["mesmo_conteudo"] = bool(ta and tb and ta[1] == tb[1] and ta[0] == tb[0])
        diferentes.append(deem)

    simbolos_a, simbolos_b = _simbolos(a), _simbolos(b)
    so_a = sorted(set(simbolos_a) - set(simbolos_b))
    so_b = sorted(set(simbolos_b) - set(simbolos_a))
    tamanho_mudou = sorted(
        f"{nome}: {simbolos_a[nome][1]} -> {simbolos_b[nome][1]} bytes"
        for nome in set(simbolos_a) & set(simbolos_b)
        if simbolos_a[nome][1] != simbolos_b[nome][1])
    endereco_mudou = sorted(
        f"{nome}: 0x{simbolos_a[nome][0]:08X} -> 0x{simbolos_b[nome][0]:08X}"
        for nome in set(simbolos_a) & set(simbolos_b)
        if simbolos_a[nome][0] != simbolos_b[nome][0] and simbolos_a[nome][1] == simbolos_b[nome][1])

    codigo_diferente = [d["secao"] for d in diferentes
                        if d["secao"].startswith(SECOES_DE_CODIGO) or d["secao"] == ".data"]
    if not diferentes:
        veredito = "objetos IDENTICOS byte a byte"
    elif not codigo_diferente and not tamanho_mudou and not so_a and not so_b:
        veredito = ("mesmo CODIGO e mesmas funcoes: a diferenca esta' so' em "
                    "metadados do ELF (tabela de simbolos / indices)")
    else:
        veredito = "CODIGO GERADO DIFERENTE"
    return {
        "a": str(a), "b": str(b),
        "secoes_iguais": iguais, "secoes_diferentes": diferentes,
        "codigo_diferente": codigo_diferente,
        "simbolos": {"so_em_a": so_a[:20], "so_em_b": so_b[:20],
                     "tamanho_mudou": tamanho_mudou[:20],
                     "endereco_mudou": endereco_mudou[:20],
                     "n_funcoes_a": len(simbolos_a), "n_funcoes_b": len(simbolos_b)},
        "veredito": veredito,
    }


def relatar(m: dict) -> str:
    linhas = [f"a: {m['a']}", f"b: {m['b']}", ""]
    linhas.append(f"secoes iguais byte a byte ({len(m['secoes_iguais'])}): "
                  + (", ".join(m["secoes_iguais"]) or "-"))
    if m["secoes_diferentes"]:
        linhas.append(f"secoes diferentes ({len(m['secoes_diferentes'])}):")
        for d in m["secoes_diferentes"]:
            marca = "  (mesmo conteudo, tamanho diferente)" if d["mesmo_conteudo"] and d["tamanho_a"] != d["tamanho_b"] else ""
            linhas.append(f"   {d['secao']:16s} {d['tamanho_a']!s:>9s} -> {d['tamanho_b']!s:>9s}"
                          f"   {d['sha_a']} -> {d['sha_b']}{marca}")
    s = m["simbolos"]
    linhas.append(f"funcoes no .symtab: {s['n_funcoes_a']} -> {s['n_funcoes_b']}")
    if s["so_em_a"]:
        linhas.append("   so' no primeiro: " + ", ".join(s["so_em_a"]))
    if s["so_em_b"]:
        linhas.append("   so' no segundo: " + ", ".join(s["so_em_b"]))
    if s["tamanho_mudou"]:
        linhas.append("   funcoes que mudaram de TAMANHO (codigo mudou):")
        linhas.extend(f"      {x}" for x in s["tamanho_mudou"])
    if s["endereco_mudou"]:
        linhas.append(f"   funcoes so' deslocadas ({len(s['endereco_mudou'])}), "
                      "mesmo tamanho (a anterior cresceu)")
    linhas.append("")
    linhas.append(f"veredito: {m['veredito']}")
    return "\n".join(linhas)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="dois .o: mesmo codigo ou nao?")
    ap.add_argument("a", type=Path)
    ap.add_argument("b", type=Path)
    ap.add_argument("--json", type=Path, help="gravar o resultado em JSON")
    args = ap.parse_args(argv)
    medido = conferir(args.a, args.b)
    print(relatar(medido))
    if args.json:
        args.json.write_text(json.dumps(medido, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nJSON gravado em {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
