#!/usr/bin/env python3
"""A rodada inteira e' deterministica? Roda duas vezes e COMPARA o que saiu.

Por que isto existe: o README afirma "duas execucoes seguidas dao JSON identico e
o mesmo .c byte a byte". Afirmacao assim tem de ter um comando que a refaca -- e
o que este script faz, com uma ressalva que so apareceu ao comparar de verdade:

  * o .c levantado e' comparado byte a byte, sem tirar nada;
  * o JSON e' comparado DEPOIS de apagar os campos que sao caminho de arquivo
    (`rom`, `caminho_c`, `compilacao.comando`): rodar em arquivos de saida
    diferentes muda esses campos por construcao, e fingir que isso e'
    nao-determinismo seria tao errado quanto esconder uma diferenca real;
  * `compilacao.bytes_objeto` e' comparado A PARTE, porque quem compila e' o zig
    e nao este projeto: se o objeto variar, a rodada nao deixa de ser
    deterministica no que este projeto faz -- mas isso tem de aparecer no
    resultado, nao sumir.

Uso:
    python ferramentas/checar_determinismo.py ROM.gba --censo functions.csv
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CAMPOS_DE_CAMINHO = ("rom", "caminho_c", "censo")


def rodar(rom: str, censo: str | None, destino: Path, zig: str | None) -> None:
    comando = [sys.executable, "-m", "gbadecomp.cli", "analisar", rom,
               "--json", str(destino / "analise.json"),
               "-o", str(destino / "levantado.c")]
    if censo:
        comando += ["--censo", censo]
    if zig:
        comando += ["--zig", zig]
    proc = subprocess.run(comando, cwd=RAIZ, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"a rodada falhou ({proc.returncode}):\n{proc.stderr[-2000:]}")


def _sem_caminhos(dados: dict) -> dict:
    limpo = dict(dados)
    for campo in CAMPOS_DE_CAMINHO:
        limpo.pop(campo, None)
    if isinstance(limpo.get("compilacao"), dict):
        limpo["compilacao"] = dict(limpo["compilacao"])
        limpo["compilacao"].pop("comando", None)
    return limpo


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom")
    parser.add_argument("--censo")
    parser.add_argument("--zig")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        (raiz / "a").mkdir()
        (raiz / "b").mkdir()
        print("rodada 1...", flush=True)
        rodar(args.rom, args.censo, raiz / "a", args.zig)
        print("rodada 2...", flush=True)
        rodar(args.rom, args.censo, raiz / "b", args.zig)

        c_a = (raiz / "a" / "levantado.c").read_bytes()
        c_b = (raiz / "b" / "levantado.c").read_bytes()
        j_a = json.loads((raiz / "a" / "analise.json").read_text(encoding="utf-8"))
        j_b = json.loads((raiz / "b" / "analise.json").read_text(encoding="utf-8"))

        print()
        print(f"C levantado ....: {'IDENTICO' if c_a == c_b else 'DIFERE'} "
              f"({len(c_a)} bytes nas duas)")
        iguais = _sem_caminhos(j_a) == _sem_caminhos(j_b)
        print(f"JSON (sem os campos de caminho): "
              f"{'IDENTICO' if iguais else 'DIFERE'}")
        if not iguais:
            diferentes = [k for k in _sem_caminhos(j_a)
                          if _sem_caminhos(j_a)[k] != _sem_caminhos(j_b).get(k)]
            print(f"  campos que diferem: {diferentes}")

        comp_a = j_a.get("compilacao") or {}
        comp_b = j_b.get("compilacao") or {}
        if comp_a.get("bytes_objeto") is None:
            print("Objeto compilado: nao testado (sem zig)")
        elif comp_a.get("sha256_objeto") == comp_b.get("sha256_objeto"):
            print(f"Objeto compilado: IDENTICO ({comp_a['bytes_objeto']} bytes, "
                  f"sha256 {comp_a['sha256_objeto'][:16]}...)")
        else:
            print(f"Objeto compilado: DIFERE (sha256 "
                  f"{str(comp_a.get('sha256_objeto'))[:16]}... e "
                  f"{str(comp_b.get('sha256_objeto'))[:16]}..., "
                  f"{comp_a.get('bytes_objeto')} e {comp_b.get('bytes_objeto')} "
                  f"bytes) -- o C e' identico, entao a diferenca vem do compilador")
        return 0 if (c_a == c_b and iguais) else 1


if __name__ == "__main__":
    raise SystemExit(main())
