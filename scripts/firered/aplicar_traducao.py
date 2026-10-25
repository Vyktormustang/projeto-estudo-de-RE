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
    (AQUI / "traducao_golpes_ptbr.py", "src/move_descriptions.c"),
    (AQUI / "traducao_habilidades_ptbr.py", "src/data/text/abilities.h"),
    (AQUI / "traducao_dex_fr_ptbr.py", "src/data/pokemon/pokedex_text_fr.h"),
    (AQUI / "traducao_dex_gen49_ptbr.py", "src/data/pokemon/pokedex_text_gen4_9.h"),
]

# diálogos dos mapas (T7): dicts label -> [(linha, sep)] aplicados aos
# data/maps/*/text.inc; sep: "n"=\n, "p"=\p, "l"=\l, "$"=fim.
# Guardar como tuplas evita o inferno de escapes de barra invertida.
DICIONARIOS_MAPAS = sorted(AQUI.glob("traducao_mapas_*_ptbr.py"))
LIMITE_LINHA_MAPA = 36          # aviso acima disso (p95 do inglês = 34)
_RE_PLACEHOLDER_MAPA = re.compile(r"\{[^{}]+\}")
_LARGURA_PLACEHOLDER = {"{PLAYER}": 7, "{RIVAL}": 7, "{STR_VAR_1}": 10,
                        "{STR_VAR_2}": 10, "{STR_VAR_3}": 10, "{KUN}": 0}


def _largura_visivel_mapa(linha: str) -> int:
    """Conta chars visíveis: placeholders de nome valem o tamanho máximo."""
    total = 0
    pos = 0
    for m in _RE_PLACEHOLDER_MAPA.finditer(linha):
        total += len(linha[pos:m.start()])
        total += _LARGURA_PLACEHOLDER.get(m.group(0), 0)
        pos = m.end()
    return total + len(linha[pos:])


def aplicar_mapas(clone: Path, charmap: set[str], escrever: bool) -> int:
    """Aplica os dicionários de diálogo aos text.inc dos mapas."""
    problemas = 0
    for dic_path in DICIONARIOS_MAPAS:
        ns: dict = {}
        exec(dic_path.read_text(encoding="utf-8"), ns)  # noqa: S102
        traducoes: dict[str, list[tuple[str, str]]] = ns["TRADUCOES"]
        por_label = dict(traducoes)
        aplicadas = ja_ok = 0
        labels_vistos: set[str] = set()
        # Onda 6+: além dos mapas, os textos de sistema em data/text/*.inc.
        # Fora: new_game_intro/save (cópia integral via traducao/) e braille
        # (sistema de escrita dos puzzles — não se traduz).
        incs = sorted((clone / "data/maps").glob("*/text.inc")) + sorted(
            p for p in (clone / "data/text").glob("*.inc")
            if p.name not in ("new_game_intro.inc", "save.inc", "braille.inc"))
        # Onda 7+: textos que vivem FORA de data/maps e data/text —
        # enfermeira do Centro POKéMON (event_scripts.s), Cable Club,
        # golpes de campo, repel. test.inc é debug e fica de fora.
        incs += [clone / "data/event_scripts.s"] + sorted(
            p for p in (clone / "data/scripts").glob("*.inc")
            if p.name != "test.inc")
        for inc in incs:
            texto = inc.read_text(encoding="utf-8")
            mudou = False
            def trocar(m: re.Match) -> str:
                nonlocal mudou, aplicadas, ja_ok, problemas
                label = m.group(1)
                if label not in por_label:
                    return m.group(0)
                labels_vistos.add(label)
                linhas = por_label[label]
                corpo_novo = []
                for txt, sep in linhas:
                    fim = {"n": "\\n", "p": "\\p", "l": "\\l", "$": "$"}[sep]
                    corpo_novo.append(f'    .string "{txt}{fim}"')
                bloco_novo = m.group(1) + "::\n" + "\n".join(corpo_novo) + "\n"
                # validações
                orig = "".join(re.findall(r'\.string "(.*)"', m.group(0)))
                novo_txt = "".join(t for t, _ in linhas)
                if sorted(_RE_PLACEHOLDER_MAPA.findall(orig)) != \
                        sorted(_RE_PLACEHOLDER_MAPA.findall(novo_txt)):
                    print(f"ERRO  {dic_path.name}:{label}: placeholders diferentes")
                    problemas += 1
                    return m.group(0)
                for t, sep in linhas:
                    for ch in _RE_PLACEHOLDER_MAPA.sub("", t):
                        if ch not in charmap:
                            print(f"ERRO  {dic_path.name}:{label}: char fora do charmap: {ch!r}")
                            problemas += 1
                            return m.group(0)
                    lv = _largura_visivel_mapa(t)
                    if lv > LIMITE_LINHA_MAPA + 4:
                        print(f"ERRO  {dic_path.name}:{label}: linha com {lv} chars: {t[:40]}…")
                        problemas += 1
                        return m.group(0)
                    if lv > LIMITE_LINHA_MAPA:
                        print(f"aviso  {dic_path.name}:{label}: linha com {lv} chars: {t[:40]}…")
                if m.group(0) == bloco_novo:
                    ja_ok += 1
                    return m.group(0)
                mudou = True
                aplicadas += 1
                return bloco_novo
            padrao = r'^(\w+)::\n((?:[ \t]+\.string "(?:[^"\\]|\\.)*"\n)+)'
            texto_novo = re.sub(padrao, trocar, texto, flags=re.M)
            if escrever and mudou:
                inc.write_text(texto_novo, encoding="utf-8")
        faltando = set(por_label) - labels_vistos
        for lbl in sorted(faltando):
            print(f"ERRO  {dic_path.name}:{lbl}: label não encontrado nos mapas")
            problemas += len(faltando)
            break
        print(f"{dic_path.name}: {aplicadas} aplicadas, {ja_ok} já ok, "
              f"{len(faltando)} labels não encontrados (de {len(por_label)})")
    return problemas


# categorias da Pokédex: dicionário EN -> PT aplicado aos .categoryName
# dos dois pokedex_entries*.h (campo u8[12] => máx 11 chars visíveis)
DICIONARIO_CATEGORIAS = AQUI / "traducao_categorias_ptbr.py"
ALVOS_CATEGORIAS = [
    "src/data/pokemon/pokedex_entries.h",
    "src/data/pokemon/pokedex_entries_gen4_9.h",
]
LIMITE_CATEGORIA = 11


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
# formato multilinha de pokedex_text_fr.h:  _( "a\n" "b\n" "c");
RE_VAR_C_ML = r'((?:static\s+)?(?:ALIGNED\(4\)\s+)?const u8 {var}\[\]\s*=\s*_\()((?:\s|#[^\n]*\n|"(?:[^"\\]|\\.)*")+)(\))'


def _validar_corpo(rotulo: str, novo: str, velho: str, charmap: set[str],
                   limite: int = LIMITE_LINHA) -> list[str]:
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
        if len(pura) > limite:
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
            if isinstance(novo, list):
                if any((chr(92) in ln or chr(10) in ln) for ln in novo):
                    print(f"ERRO  {rotarq}:{var}: linha com barra/newline embutida")
                    problemas += 1
                    continue
                novo = (chr(92) + "n").join(novo)
            m = re.search(RE_VAR_C.format(var=re.escape(var)), texto)
            multilinha = False
            if m:
                atual = m.group(2)
            else:
                m = re.search(RE_VAR_C_ML.format(var=re.escape(var)), texto)
                if not m:
                    print(f"ERRO  {rotarq}:{var}: variável não encontrada")
                    problemas += 1
                    continue
                multilinha = True
                atual = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(2)))
            if atual == novo:
                ja_ok += 1
                continue
            limite = 42 if "pokedex_text" in alvo else LIMITE_LINHA
            erros = _validar_corpo(f"{rotarq}:{var}", novo, atual, charmap, limite)
            avisos = [e for e in erros if "AVISO" in e]
            erros = [e for e in erros if "AVISO" not in e]
            for a in avisos:
                print(f"aviso  {a}")
            if erros:
                for e in erros:
                    print(f"ERRO  {e}")
                problemas += len(erros)
                continue
            if multilinha:
                texto = texto[:m.start(2)] + '"' + novo + '"' + texto[m.end(2):]
            else:
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


def aplicar_categorias(clone: Path, charmap: set[str], escrever: bool) -> int:
    """Aplica o dicionário EN->PT nos .categoryName dos pokedex_entries*.h."""
    if not DICIONARIO_CATEGORIAS.exists():
        return 0
    ns: dict = {}
    exec(DICIONARIO_CATEGORIAS.read_text(encoding="utf-8"), ns)
    trad: dict[str, str] = ns["TRADUCOES"]
    problemas = 0
    rx = re.compile(r'(\.categoryName = _\(")([^"]*)("\))')
    for alvo in ALVOS_CATEGORIAS:
        destino = clone / alvo
        rotarq = alvo.split("/")[-1]
        texto = destino.read_text(encoding="utf-8")
        aplicados = ja_ok = sem_trad = 0
        faltantes: set[str] = set()

        def troca(m: re.Match) -> str:
            nonlocal aplicados, ja_ok, sem_trad, problemas
            atual = m.group(2)
            if atual in trad.values():
                ja_ok += 1
                return m.group(0)
            novo = trad.get(atual)
            if novo is None:
                sem_trad += 1
                faltantes.add(atual)
                return m.group(0)
            ok = True
            if len(novo) > LIMITE_CATEGORIA:
                print(f"ERRO  {rotarq}: categoria {novo!r} com {len(novo)} chars (máx {LIMITE_CATEGORIA})")
                problemas += 1
                ok = False
            for ch in novo:
                if ch not in charmap:
                    print(f"ERRO  {rotarq}: categoria {novo!r} com char fora do charmap: {ch!r}")
                    problemas += 1
                    ok = False
            if not ok:
                return m.group(0)
            aplicados += 1
            return m.group(1) + novo + m.group(3)

        novo_texto = rx.sub(troca, texto)
        if escrever and aplicados:
            destino.write_text(novo_texto, encoding="utf-8")
        print(f"{rotarq}: categorias: {aplicados} aplicadas, {ja_ok} já ok, "
              f"{sem_trad} sem tradução, {problemas} problemas")
        if faltantes:
            for c in sorted(faltantes)[:10]:
                print(f"  sem tradução: {c!r}")
    return problemas


AJUSTES_CODIGO = [
    # A caixa de descricao da Pokedex (janela de 56 px, FONT_NORMAL de 14 px/linha)
    # imprimia a partir de y=8 e cortava a 4a linha (8 + 4*14 = 64 > 56). Os textos
    # das especies gen 4-9 tem 4 linhas por padrao; com y=0 as 4 linhas cabem exatas
    # (4*14 = 56). Bug herdado do port RHH, visivel tambem em ingles.
    ("src/pokedex_screen.c",
     "DexScreen_PrintMonFlavorText(sPokedexScreenData->windowIds[2], sPokedexScreenData->dexSpecies, 0, 8);",
     "DexScreen_PrintMonFlavorText(sPokedexScreenData->windowIds[2], sPokedexScreenData->dexSpecies, 0, 0);"),
]


def aplicar_ajustes_codigo(clone: Path, escrever: bool) -> int:
    problemas = 0
    for rel, velho, novo in AJUSTES_CODIGO:
        destino = clone / rel
        texto = destino.read_text(encoding="utf-8")
        if novo in texto:
            print(f"{rel}: ajuste de código já aplicado")
            continue
        if velho not in texto:
            print(f"ERRO  {rel}: trecho do ajuste de código não encontrado")
            problemas += 1
            continue
        if escrever:
            destino.write_text(texto.replace(velho, novo, 1), encoding="utf-8")
            print(f"{rel}: ajuste de código aplicado")
        else:
            print(f"{rel}: ajuste de código pendente (dry-run)")
    return problemas


def aplicar(clone: Path, escrever: bool) -> int:
    charmap = chars_do_charmap(clone)
    problemas = aplicar_strings_c(clone, charmap, escrever)
    problemas += aplicar_json(clone, charmap, escrever)
    problemas += aplicar_categorias(clone, charmap, escrever)
    problemas += aplicar_mapas(clone, charmap, escrever)
    problemas += aplicar_ajustes_codigo(clone, escrever)
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
