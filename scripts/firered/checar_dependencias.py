#!/usr/bin/env python3
"""Confere que o setup do ambiente baixa tudo que os geradores vao ler.

Por que isso existe
-------------------
O `setup_ambiente.sh` clona o RHH em modo *sparse*: so' alguns caminhos sao
baixados. Se um gerador passa a ler um arquivo que ninguem colocou na lista, o
`setup_ambiente.sh` inteiro morre **depois** de ~10 min de build, com um
`FileNotFoundError` seco. Foi exatamente o que aconteceu na E5:

    FileNotFoundError: [Errno 2] No such file or directory: '/tmp/fre/src/data/abilities.h'

O erro e' silencioso enquanto o `/tmp/fre` da sessao anterior ainda tem o
arquivo; so' aparece num ambiente limpo. Como `/tmp` zera entre sessoes, o
defeito aparece sempre na pior hora.

O que ele checa
---------------
1. Todo caminho do RHH que os geradores leem (`ref / "..."`, `Path(ref)/...`,
   constantes `RH_* = "..."`) esta' coberto por `RHH_ARQUIVOS` do setup.
2. No clone do pokefirered, todo arquivo que cada gerador abre (`pf / ...`,
   `FR_* = "..."`) existe de fato (pega nome de arquivo renomeado no upstream).
3. O clone do RHH tem os arquivos selecionados de verdade (pega sparse
   incompleto, que e' o sintoma do problema 1 num /tmp ja existente).

Uso
---
    python3 scripts/firered/checar_dependencias.py --self-test
    python3 scripts/firered/checar_dependencias.py \\
        --pokefirered /tmp/pokefirered --reference /tmp/fre
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


# --------------------------------------------------------------------------- #
# Leitura do setup
# --------------------------------------------------------------------------- #
def caminhos_do_rhh(setup: Path) -> list[str]:
    """Extrai a lista `RHH_ARQUIVOS=( ... )` do `setup_ambiente.sh`.

    Ignora os comentarios de cada linha (o `#` ate' o fim) — eles explicam qual
    etapa usa cada caminho e nao sao padroes de sparse-checkout.
    """
    texto = setup.read_text(encoding="utf-8")
    m = re.search(r"RHH_ARQUIVOS=\((.*?)\n\)", texto, re.S)
    if not m:
        raise SystemExit("nao achei RHH_ARQUIVOS=( ... ) em " + str(setup))
    itens = []
    for linha in m.group(1).splitlines():
        linha = linha.split("#", 1)[0].strip()
        achados = re.findall(r"'([^']+)'|\"([^\"]+)\"", linha)
        for a, b in achados:
            itens.append(a or b)
    return itens


# --------------------------------------------------------------------------- #
# Extracao das dependencias dos geradores
# --------------------------------------------------------------------------- #
# `*_TESTE` sao fixtures do self-test (textos literais, nao caminhos de verdade)
RE_CONST = re.compile(r'^(RH_\w+)\s*=\s*"([^"]+)"', re.M)
RE_CONST_FR = re.compile(r'^(FR_\w+)\s*=\s*"([^"]+)"', re.M)
# `ref / "a" / "b"` / `(ref / "a").glob(...)` / `Path(ref) / "a" "b"`
RE_REF = re.compile(r'(?:Path\(\s*ref\s*\)|ref)\s*/\s*((?:"[^"]+"\s*(?:/\s*)?)+)')
RE_PF = re.compile(r'(?:Path\(\s*pf\s*\)|pf)\s*/\s*((?:"[^"]+"\s*(?:/\s*)?)+)')


def sem_autoteste(texto: str) -> str:
    """Corta o arquivo no `def self_test`, onde ficam fixtures sinteticas.

    As fixtures montam `pf / "include/..."` num diretorio temporario: sao dados
    de teste, nao dependencias do gerador. Sem cortar, o cheque acusa 3 falsos
    positivos por script.
    """
    cortes = [m.start() for m in re.finditer(r"^def \w*(?:teste|self_test)\w*\(", texto, re.M)]
    corte = min(cortes) if cortes else -1
    return texto if corte == -1 else texto[:corte]


def _juntar(trecho: str) -> str:
    partes = re.findall(r'"([^"]+)"', trecho)
    return "/".join(partes)


ARTEFATOS = (".gba", ".map", ".sav", ".png", ".log", ".bin", ".elf")


def dependencias_do_rhh(fonte: Path) -> set[str]:
    texto = sem_autoteste(fonte.read_text(encoding="utf-8", errors="replace"))
    achados = {v for nome, v in RE_CONST.findall(texto) if not nome.endswith("_TESTE")}
    for trecho in RE_REF.findall(texto):
        caminho = _juntar(trecho)
        if caminho:
            achados.add(caminho)
    # `for arq in (ref / "include").rglob("*.h")` -> prefixo "include"
    return achados


def dependencias_do_firered(fonte: Path) -> set[str]:
    texto = sem_autoteste(fonte.read_text(encoding="utf-8", errors="replace"))
    achados = {v for nome, v in RE_CONST_FR.findall(texto) if not nome.endswith("_TESTE")}
    for trecho in RE_PF.findall(texto):
        caminho = _juntar(trecho)
        if caminho:
            achados.add(caminho)
    # a ROM e o .map sao saida do build, nao entrada do gerador
    return {c for c in achados if not c.endswith(ARTEFATOS)}


# --------------------------------------------------------------------------- #
# Cobertura
# --------------------------------------------------------------------------- #
def coberto(caminho: str, padroes: list[str]) -> bool:
    """O caminho e' baixado por algum padrao de sparse-checkout?

    As regras imitam o `--no-cone` do git sparse-checkout:
      - padrao terminando em `/` e' um diretorio: cobre tudo abaixo dele;
      - senao e' um arquivo (ou diretorio) exato.
    """
    caminho = caminho.strip("/")
    for p in padroes:
        p = p.strip("/")
        if not p:
            continue
        if caminho == p or caminho.startswith(p + "/"):
            return True
        # diretorio-pai usado só para montar caminho/mkdir: `ref / "src/data"`
        # está coberto quando algum padrao vive dentro dele
        if p.startswith(caminho + "/"):
            return True
    return False


def conferir(pf: Path, ref: Path, setup: Path, verboso: bool = True) -> list[str]:
    falhas: list[str] = []
    padroes = caminhos_do_rhh(setup)
    if verboso:
        print(f"setup: {len(padroes)} padrao(oes) no sparse-checkout do RHH")

    # ---- 1. dependencias declaradas nos geradores
    total = 0
    for fonte in sorted(AQUI.glob("*.py")):
        if fonte.name.startswith("checar_dependencias"):
            continue
        for caminho in sorted(dependencias_do_rhh(fonte)):
            total += 1
            if not coberto(caminho, padroes):
                falhas.append(
                    f"{fonte.name} le {caminho!r} no RHH, mas o setup nao baixa "
                    f"(adicione '/{caminho}' em RHH_ARQUIVOS)")
    if verboso:
        print(f"RHH: {total} referencia(s) nos geradores")

    # ---- 2. arquivos do pokefirered
    if pf.exists():
        for fonte in sorted(AQUI.glob("*.py")):
            if fonte.name.startswith("checar_dependencias"):
                continue
            for caminho in sorted(dependencias_do_firered(fonte)):
                # `src/data/text` (diretorio) e' valido; so' reclamamos do que nao existe
                if not (pf / caminho).exists():
                    falhas.append(f"{fonte.name} espera {caminho!r} no pokefirered, "
                                  f"que nao existe no clone")
    elif verboso:
        print("(clone do pokefirered ausente: pulei a checagem 2)")

    # ---- 3. sparse realmente completo
    if ref.exists():
        lidos: set[str] = set()
        for fonte in sorted(AQUI.glob("*.py")):
            if not fonte.name.startswith("checar_dependencias"):
                lidos |= dependencias_do_rhh(fonte)
        for caminho in sorted(lidos):
            if not (ref / caminho).exists():
                falhas.append(f"o clone do RHH nao tem {caminho!r} "
                              f"(sparse incompleto: rode o setup de novo)")
    elif verboso:
        print("(clone do RHH ausente: pulei a checagem 3)")

    return falhas


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #
def self_test() -> int:
    casos = 0
    ok = 0

    def checa(nome: str, cond: bool):
        nonlocal casos, ok
        casos += 1
        if cond:
            ok += 1
            print(f"  ok: {nome}")
        else:
            print(f"  FALHA: {nome}")

    padroes = ["/include/", "/src/data/moves_info.h", "/src/data/pokemon/species_info/"]
    checa("diretorio cobre arquivo dentro", coberto("include/constants/abilities.h", padroes))
    checa("arquivo exato cobre", coberto("src/data/moves_info.h", padroes))
    checa("arquivo fora da lista nao e' coberto",
          not coberto("src/data/abilities.h", padroes))
    checa("prefixo parecido nao engana",
          not coberto("src/data/moves_info.hx", padroes))
    checa("diretorio irmao nao engana",
          not coberto("src/data/pokemon/species_info_extra/x.h", padroes))
    checa("diretorio-pai de um padrao conta como coberto",
          coberto("src/data", padroes))

    # extracao real: um setup sintetico com comentarios
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "setup.sh"
        f.write_text(
            "RHH_ARQUIVOS=(\n"
            "  '/include/'    # constantes\n"
            "  \"/src/data/abilities.h\"  # E5\n"
            ")\n", encoding="utf-8")
        lidos = caminhos_do_rhh(f)
        checa("le a lista e ignora comentarios",
              lidos == ["/include/", "/src/data/abilities.h"])
        checa("a lista sintetica cobre a E5", coberto("src/data/abilities.h", lidos))

    # extracao de dependencias: constantes RH_* e `ref / "a" / "b"`
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "g.py"
        f.write_text(
            'RH_ABIL = "include/constants/abilities.h"\n'
            'x = (ref / "src" / "data" / "pokemon" / "species_info").glob("*.h")\n'
            'y = (Path(ref) / "src/data/moves_info.h").read_text()\n', encoding="utf-8")
        deps = dependencias_do_rhh(f)
        checa("pega constante RH_*", "include/constants/abilities.h" in deps)
        checa("pega ref / 'a' / 'b'", "src/data/pokemon/species_info" in deps)
        checa("pega Path(ref) / '...'", "src/data/moves_info.h" in deps)
    # fixture montada por um helper de teste (nome com "teste") nao conta
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "h.py"
        f.write_text(
            'RH_DATA = "src/data/abilities.h"\n'
            'def _montar_arvore_teste(raiz):\n'
            '    (ref / "src/data/pokemon/species_info/gen_teste.h").write_text("")\n',
            encoding="utf-8")
        deps = dependencias_do_rhh(f)
        checa("dependencia real continua sendo pega", "src/data/abilities.h" in deps)
        checa("fixture de helper de teste e' ignorada",
              "src/data/pokemon/species_info/gen_teste.h" not in deps)

    print(f"\n{ok}/{casos} casos ok")
    return 0 if ok == casos else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--pokefirered", default="/tmp/pokefirered")
    ap.add_argument("--reference", default="/tmp/fre")
    ap.add_argument("--setup", default=str(AQUI / "setup_ambiente.sh"))
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    falhas = conferir(Path(a.pokefirered), Path(a.reference), Path(a.setup))
    if falhas:
        print(f"\n{len(falhas)} problema(s):")
        for f in falhas:
            print("  - " + f)
        return 1
    print("\nok: toda dependencia dos geradores esta' no setup e no disco")
    return 0


if __name__ == "__main__":
    sys.exit(main())
