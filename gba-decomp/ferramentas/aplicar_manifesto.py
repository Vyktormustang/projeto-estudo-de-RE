"""Aplica um manifesto JSON de patches numa ROM -- sem escrever codigo novo.

Motivo: cada modificacao nova virava um script novo. Um manifesto declara o que
muda, onde, o que tem de estar la' antes, e por que; a guarda e' a mesma do
`gbadecomp.patch`. Serve para dado (preco, tabela, texto) e para codigo (quando
o `novo` e' um salto montado a parte).

Formato:
    {
      "descricao": "texto livre",
      "patches": [
        {"endereco": "0x083DB0D8", "esperado": "c8 00",
         "novo": "01 00", "motivo": "Poke Ball 200 -> 1"}
      ]
    }

`esperado` e `novo` aceitam "c8 00", "c800", "0xc8 0x00" ou [200, 0].
O tamanho dos dois tem de ser igual: so' se troca o mesmo tanto.

Uso:
    python ferramentas/aplicar_manifesto.py ROM.gba patches/exemplo_dados.json \\
            -o ROM_patch.gba --json aplicado.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gbadecomp import patch, rom as rom_mod  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom", type=Path)
    parser.add_argument("manifesto", type=Path)
    parser.add_argument("-o", "--saida", type=Path, required=True)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.saida.resolve() == args.rom.resolve():
        print("recuso sobrescrever a ROM de entrada; use outro caminho de saida",
              file=sys.stderr)
        return 2

    original = args.rom.read_bytes()
    if not rom_mod.looks_like_rom(original):
        print(f"{args.rom}: nao parece uma ROM GBA", file=sys.stderr)
        return 2
    manifesto = json.loads(args.manifesto.read_text(encoding="utf-8"))
    try:
        nova, patches = patch.aplicar_manifesto(original, manifesto)
    except patch.ErroDePatch as exc:
        print(f"recusado: {exc}", file=sys.stderr)
        return 1

    # releitura: o que foi gravado tem de ser exatamente o prometido
    for aplicado in patches:
        deslocamento = rom_mod.to_offset(aplicado.endereco)
        if nova[deslocamento:deslocamento + len(aplicado.novo)] != aplicado.novo:
            print(f"ERRO ao reler 0x{aplicado.endereco:08X} depois de gravar",
                  file=sys.stderr)
            return 1

    args.saida.write_bytes(nova)
    relatorio = {
        "descricao": manifesto.get("descricao", ""),
        "rom_entrada": str(args.rom),
        "rom_saida": str(args.saida),
        "bytes_alterados": sum(1 for a, b in zip(original, nova) if a != b),
        "cabecalho": {
            "complemento": f"0x{nova[0xBD]:02X}",
            "confere": nova[0xBD] == patch.complemento_correto(nova),
        },
        "patches": [
            {"endereco": f"0x{p.endereco:08X}", "esperado": p.esperado.hex(),
             "novo": p.novo.hex(), "motivo": p.motivo}
            for p in patches
        ],
    }
    if args.json:
        args.json.write_text(json.dumps(relatorio, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")

    print(patch.relatar(original, patches))
    print(f"\ncabecalho: 0x{nova[0xBD]:02X} "
          + ("(confere)" if relatorio["cabecalho"]["confere"] else "(NAO CONFERE)"))
    print(f"bytes alterados: {relatorio['bytes_alterados']}")
    print(f"ROM gravada: {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
