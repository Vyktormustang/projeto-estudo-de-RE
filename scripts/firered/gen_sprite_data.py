#!/usr/bin/env python3
"""E6, onda 1: sprítes, ícones, footprints e cries das 639 espécies novas.

Por que isso existe
-------------------
Até a E5 as espécies 387-1025 existiam em **dados**, mas não em **imagem**: o
`gMonFrontPicTable[968]` (ORTHWORM) era `{NULL, 0, 0}`. Em batalha isso aparece
como campo vazio — a barra de HP, o nome e a mensagem, sem o Pokémon. As
capturas da E5 (`reports/firered_e5/02_earth_eater.png`) mostram exatamente
isso. Esta etapa preenche as tabelas que o motor consulta pelo índice da espécie.

O que é gerado (tudo idempotente, dentro de blocos `// E6:`)

| arquivo                                        | conteúdo                                  |
|------------------------------------------------|-------------------------------------------|
| `graphics/pokemon/<pasta>/…`                   | cópia dos PNG/PAL do RHH (+ recorte)      |
| `src/data/graphics/pokemon_gen4_9.h`           | os INCBIN (`.4bpp.lz`, `.gbapal.lz`, …)   |
| `include/graphics_gen4_9.h`                    | os `extern` correspondentes               |
| `src/data/pokemon_graphics/front_pic_table.h`  | `SPECIES_SPRITE(ORTHWORM, gMonFrontPic…)` |
| `…/front_pic_coordinates.h`                    | `.size` e `.y_offset`                     |
| `…/back_pic_table.h`, `…/back_pic_coordinates.h` | idem, costas                            |
| `…/palette_table.h`, `…/shiny_palette_table.h` | paletas normal e shiny                    |
| `…/footprint_table.h`                          | pegada                                    |
| `src/pokemon_icon.c`                           | `gMonIconTable` + `gMonIconPaletteIndices`|
| `sound/cry_tables.inc`                         | `cry` / `cry_reverse` (provisórios)       |

Decisões que valem registro
---------------------------
* **`anim_front.png` (419 espécies).** No RHH, quem tem animação de dois quadros
  usa um PNG 64×**128**; o FireRed lê 64×64. O corte é feito no **PNG** (via
  `png_indexado.py`), porque o build do FireRed converte o PNG na hora
  (`%.4bpp: %.png`) — cortar o `.4bpp` depois não adianta.
* **Ícone.** O FireRed tem 3 paletas de ícone e são **idênticas** às `pal0..2`
  do RHH, então para `iconPalIndex` 0-2 basta copiar o PNG. As 17 espécies com
  índice 3-5 usam paletas que o FireRed não tem: as cores são remapeadas para a
  mais próxima entre as 3 existentes (perde fidelidade, não quebra).
* **Cry.** O RHH tem cries próprios, mas são 639 amostras e o formato de
  importação do FireRed é outro; nesta onda cada espécie nova recebe o cry da
  espécie de **mesmo tipo primário** mais próxima na dex (≤386). É provisório e
  está listado como pendência — não é o cry oficial.
* **Formas.** A dex nacional tem um nome por espécie (`AEGISLASH`), o RHH tem um
  por forma (`AEGISLASH_SHIELD`). Vale a **primeira forma que aparece** no
  arquivo do RHH, que é a forma padrão da família (a regra da E2 — sufixo mais
  curto — escolhia `AEGISLASH_BLADE`, que não é a forma padrão).
* **Pasta.** `graphics/pokemon/<minúsculo>`, a mesma convenção do FireRed. Se a
  pasta já existir no clone é porque é de uma espécie 1-386: nesse caso o script
  **aborta**, em vez de sobrescrever o sprite de outro Pokémon.

Uso
---
    python3 scripts/firered/gen_sprite_data.py --self-test
    python3 scripts/firered/gen_sprite_data.py --pokefirered /tmp/pokefirered \\
        --reference /tmp/fre --write
    python3 scripts/firered/gen_sprite_data.py --pokefirered /tmp/pokefirered \\
        --reference /tmp/fre --check
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import gen_species_data as gsd          # noqa: E402  (mesma pasta)
import png_indexado as png              # noqa: E402

PRIMEIRA_NOVA = 387
ULTIMA = 1025
MARCA = "E6"
# arquivos que não existem no FireRed e a E6 cria: os INCBIN e os `extern` deles
ARQUIVOS_NOVOS = {"src/data/graphics/pokemon_gen4_9.h", "include/graphics_gen4_9.h"}
ARQUIVOS_NOVOS_COM_INCLUDE = {"include/graphics_gen4_9.h"}
RH_GRAFICOS = "graphics/pokemon"
LADO_SPRITE = 64

# Fallbacks para quando o RHH não tem o asset: os símbolos que o FireRed já usa
# para "Pokémon desconhecido". Melhor um ponto de interrogação do que um NULL.
PADRAO = {
    "front": "gMonFrontPic_CircledQuestionMark",
    "back": "gMonBackPic_CircledQuestionMark",
    "pal": "gMonPalette_CircledQuestionMark",
    "shiny": "gMonShinyPalette_CircledQuestionMark",
    "icon": "gMonIcon_QuestionMark",
    "footprint": "gMonFootprint_Bulbasaur",
}


@dataclass
class Especie:
    nome: str                       # ORTHWORM (nome da constante, sem SPECIES_)
    ndex: int
    forma: str                      # ORTHWORM / AEGISLASH_SHIELD (bloco do RHH)
    pasta: str                      # orthworm (pasta do gráfico)
    simbolos: dict[str, str] = field(default_factory=dict)
    coords: dict[str, str] = field(default_factory=dict)
    icon_pal: int = 0
    assets: dict[str, bool] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Coleta
# --------------------------------------------------------------------------- #
def especies_novas(poke: Path) -> list[tuple[int, str]]:
    """(número nacional, NOME) das espécies 387-1025, em ordem de dex."""
    numeracao = gsd.numeracao_nacional(poke)
    ordens = sorted((n, nome) for nome, n in numeracao.items())
    return [(n, nome) for n, nome in ordens if PRIMEIRA_NOVA <= n <= ULTIMA]


def escolher_forma(nome: str, dados: dict[str, dict[str, str]]) -> str | None:
    """Forma do RHH para essa espécie: exata ou a **primeira** que aparecer.

    A ordem do dicionário é a ordem dos arquivos do RHH (gen_4 … gen_9) e, dentro
    da família, a forma padrão vem primeiro. Por isso `AEGISLASH` resolve para
    `AEGISLASH_SHIELD` (e não `_BLADE`, que é o sufixo alfabeticamente menor).
    """
    if nome in dados:
        return nome
    for chave in dados:
        if chave.startswith(nome + "_"):
            return chave
    return None


_RE_FOOTPRINT = re.compile(r"FOOTPRINT\(\s*([A-Za-z0-9_]+)\s*\)")


_RE_COLAGEM = re.compile(r"\s*##\s*")


def limpar_simbolo(valor: str) -> str:
    """Normaliza um símbolo vindo do RHH.

    O RHH escreve `gMonFrontPic_Vivillon ##PokeBall`: o `##` é concatenação do
    preprocessador **dentro da macro da família**, e o `campos()` devolve o texto
    cru. Escrito assim num header comum dá `stray '##' in program` — 8 mil erros
    de compilação, e o `data.o` saía vazio sem o `make` reclamar (o `| cat -`
    esconde o código de saída do cc1).
    """
    return _RE_COLAGEM.sub("", valor.strip())


def _arquivo_do_simbolo(simbolo: str) -> str:
    """`gMonFrontPic_Orthworm` -> `Orthworm`."""
    return simbolo.rsplit("_", 1)[-1]


def footprints(ref: Path) -> dict[str, str]:
    """`FOOTPRINT(Orthworm)` do bloco do RHH -> `{"ORTHWORM": "Orthworm"}`.

    O `campos()` só vê `.campo = valor`; `FOOTPRINT(...)` é uma linha solta, então
    precisa de uma leitura própria — senão toda espécie cai na pegada padrão.
    """
    saida: dict[str, str] = {}
    for arquivo in sorted((ref / "src/data/pokemon/species_info").glob("gen_*_families.h")):
        texto = arquivo.read_text(errors="replace")
        for bloco in re.split(r"\n(?=\s*\[SPECIES_[A-Z0-9_]+\]\s*=)", texto):
            m = re.match(r"\s*\[SPECIES_([A-Z0-9_]+)\]\s*=", bloco)
            if not m:
                continue
            fp = _RE_FOOTPRINT.search(bloco)
            if fp:
                saida[m.group(1)] = fp.group(1)
    return saida


def pasta_do_grafico(forma: str, pastas: set[str]) -> str | None:
    """Pasta do RHH para essa forma.

    Nem toda forma tem pasta própria: `TATSUGIRI_CURLY` mora em `tatsugiri` e
    `OGERPON_TEAL` em `ogerpon`. A ordem é: nome exato, nome da família (sem o
    sufixo da forma), depois o prefixo mais longo que exista. Sem isso, 61
    espécies ficavam sem sprite e o gerador avisava uma por uma.
    """
    base = forma.lower()
    if base in pastas:
        return base
    familia = base.split("_")[0]
    if familia in pastas:
        return familia
    candidatos = [p for p in pastas if base.startswith(p + "_") or p.startswith(base + "_")]
    return max(candidatos, key=len) if candidatos else None


def coletar(ref: Path, poke: Path) -> tuple[list[Especie], dict[str, int]]:
    dados = gsd.carregar_referencia(ref)
    pes = footprints(ref)
    pastas = {p.name for p in (ref / RH_GRAFICOS).iterdir() if p.is_dir()}
    rel = {"especies": 0, "sem_bloco": 0, "sem_pasta": 0, "sem_asset": 0}
    lista: list[Especie] = []
    for ndex, nome in especies_novas(poke):
        forma = escolher_forma(nome, dados)
        if forma is None:
            rel["sem_bloco"] += 1
            continue
        c = dados[forma]
        pasta = pasta_do_grafico(forma, pastas)
        if pasta is None:
            rel["sem_pasta"] += 1
            continue
        e = Especie(nome=nome, ndex=ndex, forma=forma, pasta=pasta)
        e.simbolos = {
            "front": limpar_simbolo(c.get("frontPic", PADRAO["front"])),
            "back": limpar_simbolo(c.get("backPic", PADRAO["back"])),
            "pal": limpar_simbolo(c.get("palette", PADRAO["pal"])),
            "shiny": limpar_simbolo(c.get("shinyPalette", PADRAO["shiny"])),
            "icon": limpar_simbolo(c.get("iconSprite", PADRAO["icon"])),
        }
        e.simbolos["footprint"] = (f"gMonFootprint_{pes[forma]}" if forma in pes
                                   else PADRAO["footprint"])
        e.coords = {
            "front_size": c.get("frontPicSize", "MON_COORDS_SIZE(64, 64)"),
            "front_y": c.get("frontPicYOffset", "0"),
            "back_size": c.get("backPicSize", "MON_COORDS_SIZE(64, 64)"),
            "back_y": c.get("backPicYOffset", "0"),
        }
        try:
            e.icon_pal = int(c.get("iconPalIndex", "0"))
        except ValueError:
            e.icon_pal = 0
        lista.append(e)
    rel["especies"] = len(lista)
    return lista, rel


# --------------------------------------------------------------------------- #
# Preparo dos arquivos de imagem
# --------------------------------------------------------------------------- #
def _melhor_paleta(fonte: list[tuple[int, int, int]],
                   candidatas: list[list[tuple[int, int, int]]]) -> int:
    """Índice da paleta com menor erro total para as cores usadas."""
    melhor, melhor_erro = 0, None
    for i, pal in enumerate(candidatas):
        mapa = png.mapa_de_cores(fonte, pal)
        erro = sum(png._dist2(fonte[j], pal[mapa[j]]) for j in range(len(fonte)))
        if melhor_erro is None or erro < melhor_erro:
            melhor, melhor_erro = i, erro
    return melhor


def preparar(ref: Path, poke: Path, lista: list[Especie], escrever: bool,
             log=print) -> dict[str, int]:
    """Copia (e quando preciso recorta) os gráficos do RHH para o clone.

    Não faz nada quando o destino já está igual: é o que torna o build
    incremental (~10 s em vez de ~9 min).
    """
    dir_ref = ref / RH_GRAFICOS
    dir_pf = poke / RH_GRAFICOS
    paletas_icone = [png.ler_pal(poke / f"{RH_GRAFICOS}/icon_palettes/icon_palette_{i}.pal")
                     for i in range(3)]
    rel = {"copiados": 0, "recortados": 0, "icone_remapeado": 0,
           "sem_pasta": 0, "sem_asset": 0, "iguais": 0}

    for e in lista:
        origem = dir_ref / e.pasta
        destino = dir_pf / e.pasta
        if not origem.is_dir():
            rel["sem_pasta"] += 1
            log(f"  aviso: {e.forma} sem pasta no RHH ({e.pasta})")
            continue
        if destino.exists() and not (destino / ".e6").exists():
            # pasta de espécie 1-386: sobrescrever trocaria o sprite de outro Pokémon
            raise SystemExit(
                f"a pasta {destino} já existe e não foi criada pela E6 — "
                "abortando para não sobrescrever gráfico de outra espécie")
        if escrever:
            destino.mkdir(parents=True, exist_ok=True)
            (destino / ".e6").write_text(
                f"criado por gen_sprite_data.py (E6) para SPECIES_{e.nome}\n",
                encoding="utf-8")

        # frente: front.png ou o primeiro quadro de anim_front.png
        frente = origem / "front.png"
        if not frente.exists() and (origem / "anim_front.png").exists():
            e.assets["front"] = True
            if escrever:
                img = png.ler(origem / "anim_front.png")
                if img.altura > LADO_SPRITE:
                    img = png.recortar_altura(img, LADO_SPRITE)
                    rel["recortados"] += 1
                png.escrever(img, destino / "front.png")
        elif frente.exists():
            e.assets["front"] = True
            _copiar(frente, destino / "front.png", escrever, rel)
        else:
            rel["sem_asset"] += 1
            e.assets["front"] = False

        for nome, arq in (("back", "back.png"), ("normal", "normal.pal"), ("shiny", "shiny.pal")):
            fonte = origem / arq
            if fonte.exists():
                e.assets[nome] = True
                _copiar(fonte, destino / arq, escrever, rel)
            else:
                e.assets[nome] = False
                rel["sem_asset"] += 1

        # ícone: copia, mas se a paleta do RHH for 3-5 remapeia para 0-2
        fonte_icone = origem / "icon.png"
        if fonte_icone.exists():
            e.assets["icon"] = True
            # a escolha da paleta é feita SEMPRE (mesmo no `--check`), senão o
            # valor gravado depende do caminho e o check acusa divergência falsa
            img = png.ler(fonte_icone)
            if e.icon_pal >= len(paletas_icone):
                escolhida = _melhor_paleta(img.paleta, paletas_icone)
                e.icon_pal = escolhida
                rel["icone_remapeado"] += 1
                if escrever:
                    img = png.remapear(img, paletas_icone[escolhida])
            if escrever:
                png.escrever(img, destino / "icon.png")
        else:
            e.assets["icon"] = False
            rel["sem_asset"] += 1

        _copiar(origem / "footprint.png", destino / "footprint.png", escrever, rel)
        e.assets["footprint"] = (origem / "footprint.png").exists()
    return rel


def _copiar(origem: Path, destino: Path, escrever: bool, rel: dict[str, int]) -> None:
    if not origem.exists():
        return
    if destino.exists() and destino.read_bytes() == origem.read_bytes():
        rel["iguais"] += 1
        return
    if escrever:
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origem, destino)
    rel["copiados"] += 1


# --------------------------------------------------------------------------- #
# Geração dos blocos de código
# --------------------------------------------------------------------------- #
def _nome_arquivo(simbolo: str, especie: Especie, tipo: str) -> str:
    """Caminho do asset dentro do clone (relativo à raiz)."""
    ext = {"front": "front.4bpp.lz", "back": "back.4bpp.lz",
           "pal": "normal.gbapal.lz", "shiny": "shiny.gbapal.lz",
           "icon": "icon.4bpp", "footprint": "footprint.1bpp"}[tipo]
    return f"{RH_GRAFICOS}/{especie.pasta}/{ext}"


def _simbolo_de(e: Especie, tipo: str) -> str:
    """Símbolo a usar na tabela: o do RHH ou o fallback padrão."""
    if e.assets.get({"front": "front", "back": "back", "pal": "normal",
                     "shiny": "shiny", "icon": "icon",
                     "footprint": "footprint"}[tipo], False):
        return e.simbolos[tipo]
    return PADRAO[tipo]


def simbolos_existentes(poke: Path) -> set[str]:
    """Símbolos `gMon*` que o FireRed **já define**.

    O fallback aponta para `gMonFootprint_Bulbasaur`/`gMonIcon_QuestionMark`, que
    já têm INCBIN no clone. Gerar outro INCBIN com o mesmo nome dá
    "redefinition", e o linker perde a tabela inteira. A deduplicação tem de
    considerar o que já existe, não só o que esta passada escreveu.
    """
    nomes: set[str] = set()
    for arquivo in ("src/data/graphics/pokemon.h", "src/graphics.c",
                    "src/data/graphics/trainer.h"):
        caminho = poke / arquivo
        if not caminho.exists():
            continue
        texto = caminho.read_text(encoding="utf-8", errors="surrogateescape")
        nomes |= set(re.findall(r"^\s*(?:const\s+\w+\s+)?(g\w+)\[\]\s*=\s*INCBIN", texto, re.M))
    return nomes


def entradas_de_cry(poke: Path) -> int:
    """Quantas entradas `gCryTable` já tem (a tabela é posicional!).

    Contar em vez de assumir 388 é o que impede o desalinhamento: cada linha
    acrescentada vale para a espécie seguinte. Se a tabela já cobre a espécie,
    não se acrescenta nada para ela.
    """
    caminho = poke / "sound/cry_tables.inc"
    if not caminho.exists():
        return 0
    texto = caminho.read_text(encoding="utf-8", errors="surrogateescape")
    # desconta o que a própria E6 já escreveu: senão a segunda passada contaria
    # as 639 e geraria uma lista vazia — apagando os cries.
    for marca in ("normal", "reverse"):
        a = texto.find(f"// E6: inicio {marca}\n")
        b = texto.find(f"// E6: fim {marca}\n")
        if a != -1 and b != -1:
            texto = texto[:a] + texto[b + len(f"// E6: fim {marca}\n"):]
    a = texto.find("gCryTable::")
    b = texto.find("gCryTable_Reverse::")
    if a == -1 or b == -1:
        return 0
    return texto[a:b].count("\tcry ")


def blocos(lista: list[Especie], pokes: dict[int, str],
           inicio_cries: int = 0, existentes: set[str] | None = None) -> dict[str, str]:
    """Devolve {caminho relativo no clone: texto a inserir}."""
    incbin: list[str] = []
    externos: list[str] = []
    frente: list[str] = []
    coord_f: list[str] = []
    costas: list[str] = []
    coord_c: list[str] = []
    pal: list[str] = []
    shiny: list[str] = []
    pegada: list[str] = []
    icone: list[str] = []
    icone_pal: list[str] = []
    cries: list[str] = []
    ja_definido: set[str] = set(existentes or ())   # já tem INCBIN (clone ou esta geração)

    for e in lista:
        visto: set[str] = set()
        for tipo, colecao, macro in (
                ("front", incbin, None), ("pal", incbin, None),
                ("back", incbin, None), ("shiny", incbin, None),
                ("icon", incbin, None), ("footprint", incbin, None)):
            simb = _simbolo_de(e, tipo)
            if not e.assets.get({"front": "front", "back": "back", "pal": "normal",
                                 "shiny": "shiny", "icon": "icon",
                                 "footprint": "footprint"}[tipo], False):
                continue                       # usa o símbolo padrão, já definido
            if simb in visto or simb in ja_definido:
                continue
            visto.add(simb)
            ja_definido.add(simb)
            tipo_c = "u32" if tipo in ("front", "back", "pal", "shiny") else "u8"
            arquivo = _nome_arquivo(simb, e, tipo)
            colecao.append(f"const {tipo_c} {simb}[] = INCBIN_{tipo_c.upper()}(\"{arquivo}\");")
            externos.append(f"extern const {tipo_c} {simb}[];")

        frente.append(f"    SPECIES_SPRITE({e.nome}, {_simbolo_de(e, 'front')}),")
        costas.append(f"    SPECIES_SPRITE({e.nome}, {_simbolo_de(e, 'back')}),")
        pal.append(f"    SPECIES_PAL({e.nome}, {_simbolo_de(e, 'pal')}),")
        shiny.append(f"    SPECIES_SHINY_PAL({e.nome}, {_simbolo_de(e, 'shiny')}),")
        pegada.append(f"    [SPECIES_{e.nome}] = {_simbolo_de(e, 'footprint')},")
        icone.append(f"    [SPECIES_{e.nome}] = {_simbolo_de(e, 'icon')},")
        icone_pal.append(f"    [SPECIES_{e.nome}] = {min(e.icon_pal, 2)},")
        coord_f.append(
            f"    [SPECIES_{e.nome}] =\n"
            f"    {{\n"
            f"        .size = {e.coords.get('front_size', 'MON_COORDS_SIZE(64, 64)')},\n"
            f"        .y_offset = {e.coords.get('front_y', '0')},\n"
            f"    }},")
        coord_c.append(
            f"    [SPECIES_{e.nome}] =\n"
            f"    {{\n"
            f"        .size = {e.coords.get('back_size', 'MON_COORDS_SIZE(64, 64)')},\n"
            f"        .y_offset = {e.coords.get('back_y', '0')},\n"
            f"    }},")
        if e.ndex >= inicio_cries:
            cries.append(f"\tcry {pokes.get(e.ndex, 'Cry_Chimecho')}")

    return {
        "src/data/graphics/pokemon_gen4_9.h": "\n".join(incbin),
        "include/graphics_gen4_9.h": "\n".join(externos),
        "src/data/pokemon_graphics/front_pic_table.h": "\n".join(frente),
        "src/data/pokemon_graphics/front_pic_coordinates.h": "\n".join(coord_f),
        "src/data/pokemon_graphics/back_pic_table.h": "\n".join(costas),
        "src/data/pokemon_graphics/back_pic_coordinates.h": "\n".join(coord_c),
        "src/data/pokemon_graphics/palette_table.h": "\n".join(pal),
        "src/data/pokemon_graphics/shiny_palette_table.h": "\n".join(shiny),
        "src/data/pokemon_graphics/footprint_table.h": "\n".join(pegada),
        "src/pokemon_icon.c#tabela": "\n".join(icone),
        "src/pokemon_icon.c#paletas": "\n".join(icone_pal),
        "sound/cry_tables.inc#normal": "\n".join(cries),
        "sound/cry_tables.inc#reverse": "\n".join(c.replace("\tcry ", "\tcry_reverse ", 1)
                                                  for c in cries),
    }


# --------------------------------------------------------------------------- #
# Cries provisórios: mesmo tipo primário, dex mais próxima
# --------------------------------------------------------------------------- #
def simbolos_de_cry(poke: Path) -> list[str]:
    """Os símbolos de `gCryTable`, na ordem (= índice da espécie).

    Ler do arquivo em vez de montar `Cry_` + nome evita o erro de CamelCase:
    `SEVIPER` vira `Cry_Seviper`, e nomes como `NIDORAN_F`/`HO_OH`/`MR_MIME` não
    seguem regra mecânica. A primeira versão montava `Cry_SEVIPER` e o link
    quebrou com 100+ "undefined reference".
    """
    caminho = poke / "sound/cry_tables.inc"
    if not caminho.exists():
        return []
    texto = caminho.read_text(encoding="utf-8", errors="surrogateescape")
    a = texto.find("gCryTable::")
    b = texto.find("gCryTable_Reverse::")
    if a == -1 or b == -1:
        return []
    return re.findall(r"^\tcry (\w+)$", texto[a:b], re.M)


def cries_provisorios(poke: Path) -> dict[int, str]:
    """Mapa `ndex -> Cry_X` para as espécies novas.

    Regra: a espécie de **mesmo tipo primário** com a dex mais próxima entre as
    386 que o FireRed já tem. É arbitrário por natureza (não existe cry oficial
    para elas aqui) — o objetivo é só não deixar a tabela com lixo.
    """
    tipos: dict[int, str] = {}
    numeracao = gsd.numeracao_nacional(poke)
    for arquivo in ("src/data/pokemon/species_info.h",
                    "src/data/pokemon/species_info_gen4_9.h"):
        texto = (poke / arquivo).read_text(errors="replace")
        for m in re.finditer(r"\[SPECIES_([A-Z0-9_]+)\]\s*=\s*\{(.*?)\n    \},", texto, re.S):
            t = re.search(r"\.types\s*=\s*\{\s*(TYPE_[A-Z_]+)", m.group(2))
            dex = numeracao.get(m.group(1))
            if t and dex is not None and dex not in tipos:
                tipos[dex] = t.group(1)

    simbolos = simbolos_de_cry(poke)
    antigos = [(d, t) for d, t in tipos.items() if d <= 386]
    saida: dict[int, str] = {}
    for dex, tipo in tipos.items():
        if dex <= 386:
            continue
        candidatos = [d for d, t in antigos if t == tipo]
        perto = min(candidatos, key=lambda d: (abs(d - dex), d)) if candidatos else 386
        # a tabela é posicional: o símbolo da posição `perto` é o cry daquela espécie
        if 0 < perto < len(simbolos):
            saida[dex] = simbolos[perto]
        else:
            saida[dex] = simbolos[-1] if simbolos else "Cry_Chimecho"
    return saida


# --------------------------------------------------------------------------- #
# Aplicação idempotente
# --------------------------------------------------------------------------- #
def _bloco(conteudo: str, chave: str) -> str:
    return f"// E6: inicio {chave}\n{conteudo}\n// E6: fim {chave}\n"


def _remover(texto: str, chave: str) -> tuple[str, bool]:
    ini = f"// E6: inicio {chave}\n"
    fim = f"// E6: fim {chave}\n"
    a = texto.find(ini)
    if a == -1:
        return texto, False
    b = texto.find(fim, a)
    if b == -1:
        return texto, False
    return texto[:a] + texto[b + len(fim):], True


def _inserir_antes(texto: str, ancora: str, bloco: str) -> str:
    """Insere `bloco` imediatamente antes da linha que contém `ancora`."""
    i = texto.rfind(ancora)
    if i == -1:
        raise SystemExit(f"ancora nao encontrada: {ancora!r}")
    return texto[:i] + bloco + texto[i:]


def _inserir_no_array(texto: str, assinatura: str, bloco: str) -> str:
    """Insere antes do `};` que fecha o array que começa em `assinatura`.

    `rfind("};")` não serve para `src/pokemon_icon.c`: depois de
    `gMonIconPaletteIndices` ainda existem outros arrays, e a entrada iria parar
    no array errado (erro silencioso: compila e o ícone não aparece).
    """
    i = texto.find(assinatura)
    if i == -1:
        raise SystemExit(f"array nao encontrado: {assinatura!r}")
    j = texto.find("\n};", i)
    if j == -1:
        raise SystemExit(f"fim do array nao encontrado: {assinatura!r}")
    # o último elemento do array original pode não ter vírgula
    # (`[SPECIES_UNOWN_QMARK] = gMonIcon_UnownQuestionMark`) — inserir depois dele
    # sem acrescentar a vírgula dá "assignment of read-only location".
    antes = texto[:j].rstrip(" \t\n")
    if antes and not antes.endswith(",") and not antes.endswith("{"):
        antes += ","
        return antes + "\n" + bloco + texto[j + 1:]
    return texto[:j + 1] + bloco + texto[j + 1:]


def _anexar(texto: str, bloco: str) -> str:
    if not texto.endswith("\n"):
        texto += "\n"
    return texto + bloco


def aplicar(poke: Path, gerados: dict[str, str], incluir_pokemon_h: bool = True) -> list[str]:
    feitos: list[str] = []
    for chave, conteudo in gerados.items():
        arquivo, _, parte = chave.partition("#")
        caminho = poke / arquivo
        if not caminho.exists():
            if parte == "normal":
                continue                        # cry_tables.inc ausente: ignora
            if arquivo in ARQUIVOS_NOVOS:
                # arquivo que a E6 cria do zero (só existe depois da primeira
                # passada); antes disso o `/include` dele ainda não está no build
                caminho.parent.mkdir(parents=True, exist_ok=True)
                escrever = arquivo in ARQUIVOS_NOVOS_COM_INCLUDE
                caminho.write_text(f"// {MARCA}: gerado por gen_sprite_data.py\n"
                                   + ("#pragma once\n" if escrever else ""), encoding="utf-8")
            else:
                raise SystemExit(f"arquivo nao encontrado no clone: {arquivo}")
        texto = caminho.read_text(encoding="utf-8", errors="surrogateescape")
        marca = parte or "gerado"
        texto, _ = _remover(texto, marca)
        bloco = _bloco(conteudo, marca)

        if arquivo == "src/data/graphics/pokemon_gen4_9.h":
            novo = bloco                    # arquivo inteiro, sem ancora
        elif arquivo.startswith("src/data/pokemon_graphics/"):
            novo = _inserir_antes(texto, "};", bloco)
        elif arquivo == "src/pokemon_icon.c":
            assinatura = ("const u8 *const gMonIconTable[] = {"
                          if parte == "tabela" else "const u8 gMonIconPaletteIndices[] = {")
            novo = _inserir_no_array(texto, assinatura, bloco)
        elif arquivo == "sound/cry_tables.inc":
            ancora = "\n\t.align 2\ngCryTable_Reverse::" if parte == "normal" else None
            novo = _inserir_antes(texto, ancora, bloco) if ancora else _anexar(texto, bloco)
        elif arquivo == "include/graphics_gen4_9.h":
            novo = bloco
        else:
            # `include/graphics.h` tem guarda: incluir depois do `#endif` some
            novo = (_inserir_antes(texto, "#endif", bloco)
                    if arquivo.endswith("graphics.h") else _anexar(texto, bloco))
        caminho.write_text(novo, encoding="utf-8", errors="surrogateescape")
        feitos.append(chave)

    # liga os arquivos gerados no build
    if incluir_pokemon_h:
        for alvo, include, marca in (
                ("include/graphics.h", '#include "graphics_gen4_9.h"', "include-graphics"),
                # ESTE e' o arquivo dos INCBIN (o de `include/` so' tem os extern).
                # Trocar os dois faz o `data.c` nao definir nenhum sprite.
                ("src/data/graphics/pokemon.h",
                 # caminho relativo ao proprio arquivo: `src/data.c` e
                 # `src/graphics.c` incluem `data/graphics/pokemon.h`, e um
                 # caminho "data/graphics/..." resolveria para dentro de
                 # src/data/graphics/ a partir do segundo (erro de include).
                 '#include "pokemon_gen4_9.h"', "include-pokemon-h")):
            caminho = poke / alvo
            texto = caminho.read_text(encoding="utf-8", errors="surrogateescape")
            texto, _ = _remover(texto, marca)
            if include not in texto:
                # `include/graphics.h` tem guarda: depois do `#endif` a linha
                # continuaria valendo, mas fica fora do padrao do arquivo
                bloco = _bloco(include, marca)
                texto = (_inserir_antes(texto, "#endif", bloco)
                         if alvo.endswith("graphics.h") else _anexar(texto, bloco))
                caminho.write_text(texto, encoding="utf-8", errors="surrogateescape")
                feitos.append(alvo)
    return feitos


# --------------------------------------------------------------------------- #
# Conferência
# --------------------------------------------------------------------------- #
def verificar(poke: Path, lista: list[Especie], gerados: dict[str, str]) -> list[str]:
    falhas: list[str] = []
    for chave, conteudo in gerados.items():
        arquivo, _, parte = chave.partition("#")
        caminho = poke / arquivo
        if not caminho.exists():
            if parte == "normal":
                continue
            falhas.append(f"{arquivo} nao existe")
            continue
        texto = caminho.read_text(encoding="utf-8", errors="surrogateescape")
        marca = parte or "gerado"
        if f"// E6: inicio {marca}" not in texto:
            falhas.append(f"{arquivo}: bloco E6 ({marca}) ausente")
        if conteudo and conteudo not in texto:
            falhas.append(f"{arquivo}: conteudo gerado nao confere")

    # os arquivos de imagem precisam existir de verdade
    for e in lista:
        if not e.assets.get("front", False):
            continue
        for arq in ("front.png", "normal.pal", "shiny.pal"):
            if not (poke / RH_GRAFICOS / e.pasta / arq).exists():
                falhas.append(f"{e.pasta}/{arq} nao existe no clone")
    return falhas


# --------------------------------------------------------------------------- #
# Self-test
# --------------------------------------------------------------------------- #
def self_test() -> int:
    import tempfile

    casos = ok = 0

    def checa(nome: str, cond: bool):
        nonlocal casos, ok
        casos += 1
        if cond:
            ok += 1
            print(f"  ok: {nome}")
        else:
            print(f"  FALHA: {nome}")

    dados = {"AEGISLASH_SHIELD": {}, "AEGISLASH_BLADE": {}, "ORTHWORM": {},
             "BASCULEGION_M": {}, "BASCULEGION_F": {}}
    checa("forma exata vence", escolher_forma("ORTHWORM", dados) == "ORTHWORM")
    checa("forma ausente usa a primeira que aparece",
          escolher_forma("AEGISLASH", dados) == "AEGISLASH_SHIELD")
    checa("primeira aparencia, nao sufixo alfabetico",
          escolher_forma("BASCULEGION", dados) == "BASCULEGION_M")
    checa("especie desconhecida devolve None", escolher_forma("PIKACHU", dados) is None)
    checa("colagem do preprocessador e' removida",
          limpar_simbolo("gMonFrontPic_Vivillon ##PokeBall") == "gMonFrontPic_VivillonPokeBall")
    checa("colagem sem espaco tambem",
          limpar_simbolo("gMonIcon_A##B") == "gMonIcon_AB")

    # nome de arquivo por tipo
    e = Especie(nome="ORTHWORM", ndex=968, forma="ORTHWORM", pasta="orthworm")
    e.assets = {"front": True, "back": True, "normal": True,
                "shiny": True, "icon": True, "footprint": True}
    e.simbolos = {"front": "gMonFrontPic_Orthworm", "back": "gMonBackPic_Orthworm",
                  "pal": "gMonPalette_Orthworm", "shiny": "gMonShinyPalette_Orthworm",
                  "icon": "gMonIcon_Orthworm", "footprint": "gMonFootprint_Orthworm"}
    e.coords = {"front_size": "MON_COORDS_SIZE(64, 64)", "front_y": "3",
                "back_size": "MON_COORDS_SIZE(64, 64)", "back_y": "0"}
    checa("asset de frente: .4bpp.lz",
          _nome_arquivo("x", e, "front") == "graphics/pokemon/orthworm/front.4bpp.lz")
    checa("icone sem compressao",
          _nome_arquivo("x", e, "icon") == "graphics/pokemon/orthworm/icon.4bpp")

    gerados = blocos([e], {968: "Cry_Orthworm"})
    checa("tabela de frente usa SPECIES_SPRITE",
          "SPECIES_SPRITE(ORTHWORM, gMonFrontPic_Orthworm)," in
          gerados["src/data/pokemon_graphics/front_pic_table.h"])
    checa("coordenadas usam MON_COORDS_SIZE",
          ".size = MON_COORDS_SIZE(64, 64)," in
          gerados["src/data/pokemon_graphics/front_pic_coordinates.h"])
    checa("pegada indexada pela especie",
          "[SPECIES_ORTHWORM] = gMonFootprint_Orthworm," in
          gerados["src/data/pokemon_graphics/footprint_table.h"])
    checa("cry e cry_reverse sao gerados",
          "\tcry Cry_Orthworm" in gerados["sound/cry_tables.inc#normal"]
          and "\tcry_reverse Cry_Orthworm" in gerados["sound/cry_tables.inc#reverse"])
    checa("extern do simbolo gerado",
          "extern const u32 gMonFrontPic_Orthworm[];" in gerados["include/graphics_gen4_9.h"])

    # fallback quando o asset nao existe
    e2 = Especie(nome="X", ndex=900, forma="X", pasta="x")
    e2.assets = {}
    g2 = blocos([e2], {})
    checa("sem asset usa o ponto de interrogacao",
          "SPECIES_SPRITE(X, gMonFrontPic_CircledQuestionMark)," in
          g2["src/data/pokemon_graphics/front_pic_table.h"])
    checa("sem asset nao gera INCBIN",
          g2["src/data/graphics/pokemon_gen4_9.h"].strip() == "")

    # aplicação idempotente num clone sintético
    with tempfile.TemporaryDirectory() as d:
        raiz = Path(d)
        for rel, corpo in (
                ("src/data/graphics/pokemon_gen4_9.h", ""),
                ("include/graphics_gen4_9.h", ""),
                ("include/graphics.h", "// guarda\n#endif //GUARD_GRAPHICS_H\n"),
                ("src/data/graphics/pokemon.h", ""),
                ("src/data/pokemon_graphics/front_pic_table.h",
                 "const x[] = {\n    SPECIES_SPRITE(NONE, gMonFrontPic_CircledQuestionMark),\n};\n"),
                ("src/data/pokemon_graphics/front_pic_coordinates.h",
                 "const x[] = {\n    [SPECIES_NONE] = {},\n};\n"),
                ("src/data/pokemon_graphics/back_pic_table.h", "const x[] = {\n};\n"),
                ("src/data/pokemon_graphics/back_pic_coordinates.h", "const x[] = {\n};\n"),
                ("src/data/pokemon_graphics/palette_table.h", "const x[] = {\n};\n"),
                ("src/data/pokemon_graphics/shiny_palette_table.h", "const x[] = {\n};\n"),
                ("src/data/pokemon_graphics/footprint_table.h", "const x[] = {\n};\n"),
                ("src/pokemon_icon.c",
                 "const u8 *const gMonIconTable[] = {\n    [SPECIES_NONE] = gMonIcon_QuestionMark,\n};\n\n"
                 "const u8 gMonIconPaletteIndices[] = {\n    [SPECIES_NONE] = 0,\n};\n\n"
                 "const struct SpritePalette gMonIconPaletteTable[] = {\n};\n"),
                ("sound/cry_tables.inc",
                 "\t.align 2\ngCryTable::\n\tcry Cry_Bulbasaur\n\n\t.align 2\ngCryTable_Reverse::\n"
                 "\tcry_reverse Cry_Bulbasaur\n")):
            p = raiz / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(corpo, encoding="utf-8")
        aplicar(raiz, gerados, incluir_pokemon_h=True)
        aplicar(raiz, gerados, incluir_pokemon_h=True)      # duas vezes: idempotente
        frente_txt = (raiz / "src/data/pokemon_graphics/front_pic_table.h").read_text()
        checa("aplicar duas vezes nao duplica",
              frente_txt.count("SPECIES_SPRITE(ORTHWORM") == 1)
        checa("entrada entra antes do fecha-chaves",
              frente_txt.index("ORTHWORM") < frente_txt.rindex("};"))
        icon_txt = (raiz / "src/pokemon_icon.c").read_text()
        checa("icone entra na tabela certa",
              icon_txt.index("[SPECIES_ORTHWORM] = gMonIcon_Orthworm")
              < icon_txt.index("gMonIconPaletteIndices"))
        checa("indice de paleta entra no array de indices, nao no de icones",
              icon_txt.rindex("[SPECIES_ORTHWORM] = 0,") > icon_txt.index("gMonIconPaletteIndices"))
        checa("include entra antes do #endif da guarda",
              (raiz / "include/graphics.h").read_text().index("graphics_gen4_9.h")
              < (raiz / "include/graphics.h").read_text().index("#endif"))
        cry_txt = (raiz / "sound/cry_tables.inc").read_text()
        checa("cry entra antes do gCryTable_Reverse",
              cry_txt.index("cry Cry_Orthworm") < cry_txt.index("gCryTable_Reverse"))
        checa("cry_reverse entra no fim",
              cry_txt.rindex("cry_reverse Cry_Orthworm") > cry_txt.index("gCryTable_Reverse"))
        falhas = verificar(raiz, [], {k: v for k, v in gerados.items()
                                      if not k.startswith("sound/")})
        checa("verificar aceita o que foi aplicado", not falhas)

    print(f"\n{ok}/{casos} casos ok")
    return 0 if ok == casos else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--pokefirered", default="/tmp/pokefirered")
    ap.add_argument("--reference", default="/tmp/fre")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()

    ref, poke = Path(a.reference), Path(a.pokefirered)
    lista, rel = coletar(ref, poke)
    rel.update(preparar(ref, poke, lista, escrever=a.write, log=print))
    cries = cries_provisorios(poke)
    gerados = blocos(lista, cries, inicio_cries=entradas_de_cry(poke),
                     existentes=simbolos_existentes(poke))

    if a.write:
        feitos = aplicar(poke, gerados)
        print(f"aplicado em {len(feitos)} arquivo(s)")
    if a.check or not a.write:
        falhas = verificar(poke, lista, gerados)
        if falhas:
            print(f"{len(falhas)} problema(s):")
            for f in falhas[:20]:
                print("  - " + f)
            return 1
        print("ok: sprites, icones, pegadas e cries batem com o gerado")
    if a.json:
        print(json.dumps(rel, ensure_ascii=False, indent=2))
    else:
        print(rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
