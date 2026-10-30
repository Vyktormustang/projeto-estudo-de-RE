#!/usr/bin/env python3
"""reprozip.py — empacota o APK de forma determinística (build reprodutível).

Problema: `aapt2` e o `zip` gravam o horário corrente em cada entrada, então o
mesmo commit gera bytes (e SHA-256) diferentes a cada build.

Solução: este script reconstrói o ZIP a partir das entradas do APK que o aapt2
gerou + os arquivos extras pedidos, gravando **timestamp fixo** (1980-01-01,
o mínimo do formato ZIP), ordem preservada e método de compressão preservado
(`resources.arsc` continua STORED). Depois o `zipalign` só ajusta offsets e o
`apksigner` gera assinaturas RSA PKCS#1 v1.5 — ambas determinísticas.

Resultado: mesmo commit + mesma versão + mesmo keystore ⇒ **mesmo SHA-256**.

Uso:
  python3 forja/tools/reprozip.py --base base.apk --out nao_assinado.apk \
      --extra classes.dex
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import zipfile

DOS_EPOCH = (1980, 1, 1, 0, 0, 0)


def norm(nome: str) -> str:
    return nome.replace("\\", "/").lstrip("/")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, help="APK de entrada (saída do aapt2)")
    ap.add_argument("--out", required=True, help="APK de saída (determinístico)")
    ap.add_argument("--extra", action="append", default=[],
                    help="arquivo extra na raiz do APK (ex.: classes.dex)")
    a = ap.parse_args(argv)

    base = pathlib.Path(a.base)
    if not base.is_file():
        print(f"[ERRO] base inexistente: {base}", file=sys.stderr)
        return 2

    extras = []
    for caminho in a.extra:
        p = pathlib.Path(caminho)
        if not p.is_file():
            print(f"[ERRO] extra inexistente: {p}", file=sys.stderr)
            return 2
        extras.append(p)

    saida = pathlib.Path(a.out)
    saida.parent.mkdir(parents=True, exist_ok=True)
    total = 0

    with zipfile.ZipFile(base) as origem, \
            zipfile.ZipFile(saida, "w", allowZip64=False) as destino:
        vistos = set()
        for info in origem.infolist():
            if info.is_dir():
                continue
            nome = norm(info.filename)
            if nome in vistos:            # duplicata: mantém a primeira
                continue
            vistos.add(nome)
            dados = origem.read(info)
            novo = zipfile.ZipInfo(nome, date_time=DOS_EPOCH)
            novo.compress_type = info.compress_type
            # atributos preservados para o Android (não usa permissões POSIX)
            novo.external_attr = 0o644 << 16
            novo.create_system = 0
            destino.writestr(novo, dados)
            total += len(dados)

        for p in extras:
            nome = norm(p.name)
            if nome in vistos:
                print(f"[ERRO] entrada duplicada: {nome}", file=sys.stderr)
                return 3
            vistos.add(nome)
            dados = p.read_bytes()
            novo = zipfile.ZipInfo(nome, date_time=DOS_EPOCH)
            novo.compress_type = zipfile.ZIP_DEFLATED
            novo.external_attr = 0o644 << 16
            novo.create_system = 0
            destino.writestr(novo, dados)
            total += len(dados)

    print(f"[reprozip] {saida} — {len(vistos)} entradas, {total} bytes de payload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
