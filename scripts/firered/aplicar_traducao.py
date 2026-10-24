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
# dicionários var -> texto PT para strings _("...") em arquivos .c
# (cada .py tem um dict TRADUCOES aplicado ao .c correspondente)
DICIONARIOS_C = [
    (AQUI / "traducao_strings_ptbr.py", "src/strings.c"),
    (AQUI / "traducao_batalha_ptbr.py", "src/battle_message.c"),
]


# dicionários itemId -> [linhas] aplicados a campos de arquivos .json
# (jsonproc regenera o .h correspondente no build)
DICIONARIOS_JSON = [
    (AQUI / "traducao_itens_ptbr.py", "src/data/items.json", "description_english"),
]

RE_STRING = re.compile(r'\.string\s+"(.*)"')
RE_LABEL = re.compile(r"^(\w+)::", re.M)
RE_PLACEHOLDER = re.compile(r"\{[^{}]+\}")
RE_CONTROLE = re.compile(r"\{[^{}]+\}|\\n|\\p|\\l|\$")


def chars_do_charmap(clone: Path) -> set[str]:
    chars = set()
    for ln in (clone / "charmap.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^'(.+?)'\s*=", ln)
        if not m:
            continue
        ch = m.group(1)
        if ch == "\\'":
            ch = "'"
        if len(ch) == 1:
            chars.add(ch)
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


RE_VAR_C = r'((?:static\s+)?(?:ALIGNED\(4\)\s+)?const u8 {var}\[\]\s*=\s*_\(")((?:[^"\\]|\\.)*)("\))'


def _validar_corpo(rotulo: str, novo: str, velho: str, charmap: set[str]) -> list[str]:
    erros = []
    if sorted(RE_PLACEHOLDER.findall(novo)) != sorted(RE_PLACEHOLDER.findall(velho)):
        erros.append(f"{rotulo}: placeholders mudaram")
    for ch in RE_CONTROLE.sub("", novo):
        if ch not in charmap:
            erros.append(f"{rotulo}: caractere fora do charmap: {ch!r}")
    for linha in re.split(r"\\n|\\p|\\l", novo):
        # tokens sem largura visível não contam
        linha = re.sub(r"\{(PAUSE[^{}]*|PLAY_[^{}]*|COLOR [^{}]*|SHADOW [^{}]*|HIGHLIGHT [^{}]*|FONT_[^{}]*|CLEAR[^{}]*|ESCAPE [^{}]*)\}", "", linha)
        pura = RE_PLACEHOLDER.sub("XXXXXXX", linha)
        if len(pura) > LIMITE_LINHA:
            erros.append(f"{rotulo}: AVISO linha com {len(pura)} chars")
    return erros


def aplicar_strings_c(clone: Path, charmap: set[str], escrever: bool) -> int:
    """Aplica os dicionários var->texto nos .c correspondentes."""
    total = 0
    for arq_py, alvo in DICIONARIOS_C:
        if not arq_py.exists():
            continue
        ns: dict = {}
        exec(arq_py.read_text(encoding="utf-8"), ns)
        trad: dict[str, str] = ns["TRADUCOES"]
        destino = clone / alvo
        rotarq = alvo.split("/")[-1]
        texto = destino.read_text(encoding="utf-8")
        problemas = aplicados = ja_ok = 0
        for var, novo in trad.items():
            m = re.search(RE_VAR_C.format(var=re.escape(var)), texto)
            if not m:
                print(f"ERRO  {rotarq}:{var}: variável não encontrada")
                problemas += 1
                continue
            atual = m.group(2)
            if atual == novo:
                ja_ok += 1
                continue
            erros = _validar_corpo(f"{rotarq}:{var}", novo, atual, charmap)
            avisos = [e for e in erros if "AVISO" in e]
            erros = [e for e in erros if "AVISO" not in e]
            for a in avisos:
                print(f"aviso  {a}")
            if erros:
                for e in erros:
                    print(f"ERRO  {e}")
                problemas += len(erros)
                continue
            texto = texto[:m.start(2)] + novo + texto[m.end(2):]
            aplicados += 1
        if escrever and aplicados:
            destino.write_text(texto, encoding="utf-8")
        print(f"{rotarq}: {aplicados} aplicadas, {ja_ok} já ok, {problemas} problemas"
              f" (de {len(trad)} no dicionário)")
        total += problemas
    return total



def aplicar_json(clone: Path, charmap: set[str], escrever: bool) -> int:
    """Aplica dicionários itemId -> [linhas] em campos de arquivos .json."""
    import json as _json
    total = 0
    SEP = chr(92) + "n"  # separador \n literal (2 chars), como nos .c
    for arq_py, alvo, campo in DICIONARIOS_JSON:
        if not arq_py.exists():
            continue
        ns: dict = {}
        exec(arq_py.read_text(encoding="utf-8"), ns)
        trad: dict[str, list[str]] = ns["TRADUCOES"]
        destino = clone / alvo
        rotarq = alvo.split("/")[-1]
        texto = destino.read_text(encoding="utf-8")
        re_campo = re.compile('("' + campo + '"' + chr(92) + 's*:' + chr(92) + 's*)"((?:[^"' + chr(92) + chr(92) + ']|' + chr(92) + chr(92) + '.)*)"')
        problemas = aplicados = ja_ok = 0
        for item_id, linhas in trad.items():
            rot = rotarq + ":" + item_id
            if not isinstance(linhas, list) or not (1 <= len(linhas) <= 3):
                print("ERRO  " + rot + ": precisa ser lista de 1-3 linhas")
                problemas += 1
                continue
            if any((chr(92) in ln or chr(10) in ln) for ln in linhas):
                print("ERRO  " + rot + ": linha com barra/newline embutida")
                problemas += 1
                continue
            novo = SEP.join(linhas)
            m_id = re.search('"itemId"' + chr(92) + 's*:' + chr(92) + 's*"' + re.escape(item_id) + '"', texto)
            if not m_id:
                print("ERRO  " + rot + ": itemId não encontrado")
                problemas += 1
                continue
            m = re_campo.search(texto, m_id.end())
            if not m:
                print("ERRO  " + rot + ": campo não encontrado")
                problemas += 1
                continue
            atual = _json.loads('"' + m.group(2) + '"')
            if atual == novo:
                ja_ok += 1
                continue
            erros = _validar_corpo(rot, novo, atual, charmap)
            avisos = [e for e in erros if "AVISO" in e]
            erros = [e for e in erros if "AVISO" not in e]
            for a in avisos:
                print("aviso  " + a)
            if erros:
                for e in erros:
                    print("ERRO  " + e)
                problemas += len(erros)
                continue
            novo_raw = _json.dumps(novo)[1:-1]
            texto = texto[:m.start(2)] + novo_raw + texto[m.end(2):]
            aplicados += 1
        if escrever and aplicados:
            destino.write_text(texto, encoding="utf-8")
        print(rotarq + ": " + str(aplicados) + " aplicadas, " + str(ja_ok) + " já ok, "
              + str(problemas) + " problemas (de " + str(len(trad)) + " no dicionário)")
        total += problemas
    return total


def aplicar(clone: Path, escrever: bool) -> int:
    charmap = chars_do_charmap(clone)
    problemas = aplicar_strings_c(clone, charmap, escrever)
    problemas += aplicar_json(clone, charmap, escrever)
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
