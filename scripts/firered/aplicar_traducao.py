#!/usr/bin/env python3
"""Aplica a tradução PT-BR ao clone do pokefirered e valida o texto.

A pasta `traducao/` (ao lado deste script) espelha a árvore do clone:
`traducao/data/text/new_game_intro.inc` substitui `data/text/new_game_intro.inc`
e assim por diante. Antes de copiar, cada arquivo é validado:

1. **Charset** — todo caractere fora de controle `{...}`/`\\n`/`\\p` etc.
   precisa existir no charmap.txt do clone (senão o preproc quebra o build
   ou, pior, engole texto silenciosamente).
2. **Placeholders** — o conjunto de `{PLACEHOLDER}` de cada label traduzida
   deve ser IGUAL ao do original (não pode sumir {PLAYER} nem nascer um
   {RIVAL} extra).
3. **Comprimento de linha** — aviso quando uma linha passa de 36 chars
   (caixa de diálogo padrão estoura por volta disso na fonte normal).

Uso:
    python3 aplicar_traducao.py --pokefirered /tmp/pokefirered --check
    python3 aplicar_traducao.py --pokefirered /tmp/pokefirered --write
    python3 aplicar_traducao.py --self-test

Windows: rodar no WSL (ver docs/FIRERED.md).
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

AQUI = Path(__file__).parent
RAIZ_TRADUCAO = AQUI / "traducao"
LIMITE_LINHA = 36

RE_STRING = re.compile(r'\.string\s+"(.*)"')
RE_LABEL = re.compile(r"^(\w+)::", re.M)
RE_PLACEHOLDER = re.compile(r"\{[A-Z_0-9]+\}")
RE_CONTROLE = re.compile(r"\{[A-Z_0-9]+\}|\\n|\\p|\\l|\$")


def chars_do_charmap(clone: Path) -> set[str]:
    chars = set()
    for ln in (clone / "charmap.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^'(.+?)'\s*=", ln)
        if m and len(m.group(1)) == 1:
            chars.add(m.group(1))
    return chars


def labels_e_strings(texto: str) -> dict[str, str]:
    """{label: conteúdo concatenado das .string} na ordem do arquivo."""
    resultado: dict[str, list[str]] = {}
    label = None
    for ln in texto.splitlines():
        m = RE_LABEL.match(ln.strip())
        if m:
            label = m.group(1)
            resultado[label] = []
            continue
        m = RE_STRING.search(ln)
        if m and label:
            resultado[label].append(m.group(1))
    return {k: "".join(v) for k, v in resultado.items()}


def validar(rel: Path, traduzido: str, original: str, charmap: set[str]) -> list[str]:
    erros = []
    t_labels = labels_e_strings(traduzido)
    o_labels = labels_e_strings(original)
    if set(t_labels) != set(o_labels):
        extra = set(t_labels) - set(o_labels)
        falta = set(o_labels) - set(t_labels)
        erros.append(f"{rel}: labels diferentes (extra={extra or '—'} falta={falta or '—'})")
    for label, corpo in t_labels.items():
        orig = o_labels.get(label, "")
        if sorted(RE_PLACEHOLDER.findall(corpo)) != sorted(RE_PLACEHOLDER.findall(orig)):
            erros.append(f"{rel}:{label}: placeholders mudaram")
        texto_puro = RE_CONTROLE.sub("", corpo)
        for ch in texto_puro:
            if ch not in charmap:
                erros.append(f"{rel}:{label}: caractere fora do charmap: {ch!r}")
        for linha in re.split(r"\\n|\\p|\\l", corpo):
            linha_pura = RE_PLACEHOLDER.sub("XXXXXXX", linha).rstrip("$")
            if len(linha_pura) > LIMITE_LINHA:
                erros.append(f"{rel}:{label}: AVISO linha com {len(linha_pura)} chars: {linha_pura[:40]}…")
    return erros


def aplicar(clone: Path, escrever: bool) -> int:
    charmap = chars_do_charmap(clone)
    problemas = 0
    arquivos = sorted(p for p in RAIZ_TRADUCAO.rglob("*") if p.is_file())
    if not arquivos:
        print("nada em traducao/ para aplicar")
        return 1
    for arq in arquivos:
        rel = arq.relative_to(RAIZ_TRADUCAO)
        destino = clone / rel
        if not destino.exists():
            print(f"ERRO  {rel}: não existe no clone")
            problemas += 1
            continue
        erros = validar(rel, arq.read_text(encoding="utf-8"),
                        destino.read_text(encoding="utf-8"), charmap)
        avisos = [e for e in erros if "AVISO" in e]
        erros = [e for e in erros if "AVISO" not in e]
        for a in avisos:
            print(f"aviso  {a}")
        if erros:
            for e in erros:
                print(f"ERRO  {e}")
            problemas += len(erros)
            continue
        identico = arq.read_bytes() == destino.read_bytes()
        if escrever and not identico:
            shutil.copyfile(arq, destino)
            print(f"aplicado  {rel}")
        else:
            print(f"{'ok (já aplicado)' if identico else 'ok (validado)'}  {rel}")
    return problemas


def self_test() -> int:
    falhas = 0

    def caso(nome, cond):
        nonlocal falhas
        print(f"{'ok' if cond else 'FALHOU'}  {nome}")
        if not cond:
            falhas += 1

    orig = 'gX::\n    .string "Hello {PLAYER}!\\n"\n    .string "Bye.$"\n'
    bom = 'gX::\n    .string "Olá {PLAYER}!\\n"\n    .string "Tchau.$"\n'
    sem_ph = 'gX::\n    .string "Olá!\\n"\n    .string "Tchau.$"\n'
    char_ruim = 'gX::\n    .string "Olá ☺ {PLAYER}!$"\n'
    charmap = set("OláTchau!ÁéçãõÃÕêâôúíó Hello PLAYERBye.")

    caso("labels extraídas", labels_e_strings(orig) == {"gX": "Hello {PLAYER}!\\nBye.$"})
    caso("tradução válida passa", validar(Path("x"), bom, orig, charmap) == [])
    caso("placeholder sumido é erro",
         any("placeholders" in e for e in validar(Path("x"), sem_ph, orig, charmap)))
    caso("char fora do charmap é erro",
         any("charmap" in e for e in validar(Path("x"), char_ruim, orig, charmap)))
    linha_grande = 'gX::\n    .string "' + "a" * 50 + '$"\n'
    orig_grande = 'gX::\n    .string "' + "b" * 50 + '$"\n'
    caso("linha comprida vira aviso",
         any("AVISO" in e for e in validar(Path("x"), linha_grande, orig_grande,
                                           set("ab$"))))
    print(f"\nself-test: {'PASS' if falhas == 0 else f'{falhas} FALHA(S)'}")
    return falhas


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pokefirered", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(self_test())
    if not args.pokefirered:
        ap.error("--pokefirered é obrigatório (ou use --self-test)")
    sys.exit(1 if aplicar(args.pokefirered, escrever=args.write) else 0)


if __name__ == "__main__":
    main()
