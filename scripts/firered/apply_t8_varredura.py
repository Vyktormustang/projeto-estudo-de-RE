#!/usr/bin/env python3
"""T8 — varredura final da tradução PT-BR (mudanças fora do alcance dos dicts).

O aplicar_traducao.py cobre strings _( "..." ) e blocos .string de text.inc.
Três coisas ficam fora desse alcance e são feitas aqui, de forma idempotente:

1. Pokédex em MÉTRICO: DexScreen_PrintMonHeight/Weight em src/pokedex_screen.c
   imprimem pés/polegadas e libras; viram metros ("2,3 m") e quilos
   ("99,9 kg"). A altura da dex está em decímetros e o peso em hectogramas
   (CONFIRMADO no código: 10000*height/254 = décimos de polegada;
   weight*100000/4536 = centésimos de libra).
2. Nomes do mapa (popup ao entrar na área + mapa de voo + área da dex):
   src/data/region_map/region_map_sections.json (o .h é auto-gerado dele).
   Só nomes descritivos; cidades/ilhas/nomes próprios ficam em inglês,
   consistente com o glossário das ondas do T7.
3. Bloco com #ifdef no meio (o validador de .inc não casa nele):
   PalletTown_RivalsHouse_Text_ThereYouGoAllDone (as DUAS variantes).

Uso:
    python3 apply_t8_varredura.py --pokefirered /tmp/pokefirered [--check]
    python3 apply_t8_varredura.py --self-test
"""
import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- 1. métrico

ALTURA_ANTIGA = """        inches = 10000 * height / 254; // actually tenths of inches here
        if (inches % 10 >= 5)
            inches += 10;
        feet = inches / 120;
        inches = (inches - (feet * 120)) / 10;
        if (feet / 10 == 0)
        {
            buffer[i++] = 0;
            buffer[i++] = feet + CHAR_0;
        }
        else
        {
            buffer[i++] = feet / 10 + CHAR_0;
            buffer[i++] = feet % 10 + CHAR_0;
        }
        buffer[i++] = CHAR_SGL_QUOTE_RIGHT;
        buffer[i++] = inches / 10 + CHAR_0;
        buffer[i++] = inches % 10 + CHAR_0;
        buffer[i++] = CHAR_DBL_QUOTE_RIGHT;
        buffer[i++] = EOS;
    }
    else
    {
        buffer[i++] = CHAR_QUESTION_MARK;
        buffer[i++] = CHAR_QUESTION_MARK;
        buffer[i++] = CHAR_SGL_QUOTE_RIGHT;
        buffer[i++] = CHAR_QUESTION_MARK;
        buffer[i++] = CHAR_QUESTION_MARK;
        buffer[i++] = CHAR_DBL_QUOTE_RIGHT;
    }"""

ALTURA_NOVA = """        // T8: metros ("9,9 m") — gPokedexEntries[].height esta em decimetros
        feet = height / 10;   // parte inteira em metros
        inches = height % 10; // decimo de metro
        if (feet >= 100)
            buffer[i++] = feet / 100 + CHAR_0;
        if (feet >= 10)
            buffer[i++] = (feet / 10) % 10 + CHAR_0;
        else
            buffer[i++] = CHAR_SPACE;
        buffer[i++] = feet % 10 + CHAR_0;
        buffer[i++] = CHAR_COMMA;
        buffer[i++] = inches + CHAR_0;
        buffer[i++] = CHAR_SPACE;
        buffer[i++] = CHAR_m;
        buffer[i++] = EOS;
    }
    else
    {
        buffer[i++] = CHAR_SPACE;
        buffer[i++] = CHAR_QUESTION_MARK;
        buffer[i++] = CHAR_QUESTION_MARK;
        buffer[i++] = CHAR_COMMA;
        buffer[i++] = CHAR_QUESTION_MARK;
        buffer[i++] = CHAR_SPACE;
        buffer[i++] = CHAR_m;
    }"""

PESO_ANTIGO = """        lbs = (weight * 100000) / 4536; // Convert to hundredths of lb

        // Round up to the nearest 0.1 lb
        if (lbs % 10 >= 5)
            lbs += 10;
"""

PESO_NOVO = """        lbs = weight * 10; // T8: centesimos de kg (weight esta em hectogramas)
"""

# o peso usa CHAR_PERIOD duas vezes (valor e "????.?") -> virgula decimal
RE_PESO_FN = re.compile(
    r"(void DexScreen_PrintMonWeight.*?^\})", re.S | re.M)


def aplicar_metrico(pf: Path, escrever: bool) -> list[str]:
    caminho = pf / "src/pokedex_screen.c"
    src = caminho.read_text(encoding="utf-8")
    erros = []
    if "T8: metros" in src:
        return []  # já aplicado
    if ALTURA_ANTIGA not in src:
        return ["pokedex_screen.c: trecho da altura não encontrado"]
    src = src.replace(ALTURA_ANTIGA, ALTURA_NOVA, 1)

    m = RE_PESO_FN.search(src)
    if not m or PESO_ANTIGO not in m.group(1):
        return ["pokedex_screen.c: trecho do peso não encontrado"]
    fn = m.group(1)
    fn_novo = fn.replace(PESO_ANTIGO, PESO_NOVO, 1)
    fn_novo = fn_novo.replace("buffer[i++] = CHAR_PERIOD;",
                              "buffer[i++] = CHAR_COMMA;")
    fn_novo = fn_novo.replace("lbsText = gText_Lbs;",
                              "lbsText = sText_T8_Kg;")
    src = src.replace(fn, fn_novo, 1)
    src = src.replace("void DexScreen_PrintMonWeight",
                      'static const u8 sText_T8_Kg[] = _("kg");\n\n'
                      "void DexScreen_PrintMonWeight", 1)
    if escrever:
        caminho.write_text(src, encoding="utf-8")
    return erros


# ------------------------------------------------------- 2. nomes do mapa
# Consistente com o glossário T7; nomes próprios (cidades, ilhas Sevii,
# S.S. ANNE, SILPH CO., ROCK TUNNEL etc.) ficam em inglês.
NOMES_MAPA = {
    "MAPSEC_VIRIDIAN_FOREST": "FLORESTA VIRIDIAN",
    "MAPSEC_MT_MOON": "MONTE LUA",
    "MAPSEC_UNDERGROUND_PATH": "CAMINHO SUBTERRÂNEO",
    "MAPSEC_UNDERGROUND_PATH_2": "CAMINHO SUBTERRÂNEO",
    "MAPSEC_DIGLETTS_CAVE": "CAVERNA DIGLETT",
    "MAPSEC_KANTO_VICTORY_ROAD": "ESTRADA DA VITÓRIA",
    "MAPSEC_ROCKET_HIDEOUT": "ESCONDERIJO ROCKET",
    "MAPSEC_POKEMON_MANSION": "MANSÃO POKéMON",
    "MAPSEC_KANTO_SAFARI_ZONE": "ZONA DO SAFÁRI",
    "MAPSEC_POKEMON_LEAGUE": "LIGA POKéMON",
    "MAPSEC_SEAFOAM_ISLANDS": "ILHAS SEAFOAM",
    "MAPSEC_POKEMON_TOWER": "TORRE POKéMON",
    "MAPSEC_CERULEAN_CAVE": "CAVERNA CERULEAN",
    "MAPSEC_POWER_PLANT": "USINA",
    "MAPSEC_MT_EMBER": "MONTE EMBER",
    "MAPSEC_ROCKET_WAREHOUSE": "DEPÓSITO ROCKET",
    "MAPSEC_WATER_LABYRINTH": "LABIRINTO AQUÁTICO",
    "MAPSEC_SEVAULT_CANYON": "CÂNION SEVAULT",
    "MAPSEC_CANYON_ENTRANCE": "ENTRADA DO CÂNION",
    "MAPSEC_ICEFALL_CAVE": "CAVERNA ICEFALL",
    "MAPSEC_EMBER_SPA": "SPA EMBER",
    "MAPSEC_TANOBY_RUINS": "RUÍNAS TANOBY",
    "MAPSEC_TANOBY_CHAMBERS": "CÂMARAS TANOBY",
    "MAPSEC_TANOBY_KEY": "CHAVE TANOBY",
    "MAPSEC_MONEAN_CHAMBER": "CÂMARA MONEAN",
    "MAPSEC_LIPTOO_CHAMBER": "CÂMARA LIPTOO",
    "MAPSEC_WEEPTH_CHAMBER": "CÂMARA WEEPTH",
    "MAPSEC_DILFORD_CHAMBER": "CÂMARA DILFORD",
    "MAPSEC_SCUFIB_CHAMBER": "CÂMARA SCUFIB",
    "MAPSEC_RIXY_CHAMBER": "CÂMARA RIXY",
    "MAPSEC_VIAPOIS_CHAMBER": "CÂMARA VIAPOIS",
}
RE_ROTA = re.compile(r"^ROUTE (\d+)$")


def aplicar_mapa(pf: Path, escrever: bool) -> list[str]:
    caminho = pf / "src/data/region_map/region_map_sections.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    secoes = dados["map_sections"] if isinstance(dados, dict) else dados
    erros, achou = [], set()
    for sec in secoes:
        nome = sec.get("name")
        if not nome:
            continue
        m = RE_ROTA.match(nome)
        if m:
            sec["name"] = f"ROTA {m.group(1)}"
            continue
        sid = sec.get("id")
        if sid in NOMES_MAPA:
            sec["name"] = NOMES_MAPA[sid]
            achou.add(sid)
    faltando = set(NOMES_MAPA) - achou
    # idempotência: se já estava em PT, nada de "faltando"
    ja_pt = {s.get("id") for s in secoes
             if s.get("name") in NOMES_MAPA.values()}
    faltando -= ja_pt
    if faltando:
        erros.append(f"region_map_sections.json: ids não achados: {sorted(faltando)}")
    if escrever and not erros:
        caminho.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    return erros


# Os símbolos sMapsecName_* são derivados do TEXTO do nome pelo gerador
# (cleanString), então traduzir o JSON muda o identificador. region_map.c
# referencia alguns deles diretamente (lista de dungeons) e precisa
# acompanhar. Byte não alfanumérico UTF-8 vira "_" (acentos = 2 "_").
RENOMES_REGION_MAP_C = {
    "sMapsecName_VIRIDIAN_FOREST": "sMapsecName_FLORESTA_VIRIDIAN",
    "sMapsecName_MT__MOON": "sMapsecName_MONTE_LUA",
    "sMapsecName_DIGLETT_S_CAVE": "sMapsecName_CAVERNA_DIGLETT",
    "sMapsecName_VICTORY_ROAD": "sMapsecName_ESTRADA_DA_VIT__RIA",
    "sMapsecName_POK__MON_MANSION": "sMapsecName_MANS__O_POK__MON",
    "sMapsecName_SAFARI_ZONE": "sMapsecName_ZONA_DO_SAF__RI",
    "sMapsecName_SEAFOAM_ISLANDS": "sMapsecName_ILHAS_SEAFOAM",
    "sMapsecName_POK__MON_TOWER": "sMapsecName_TORRE_POK__MON",
    "sMapsecName_CERULEAN_CAVE": "sMapsecName_CAVERNA_CERULEAN",
    "sMapsecName_POWER_PLANT": "sMapsecName_USINA",
    "sMapsecName_MT__EMBER": "sMapsecName_MONTE_EMBER",
    "sMapsecName_ICEFALL_CAVE": "sMapsecName_CAVERNA_ICEFALL",
    "sMapsecName_TANOBY_CHAMBERS": "sMapsecName_C__MARAS_TANOBY",
}


def aplicar_region_map_c(pf: Path, escrever: bool) -> list[str]:
    caminho = pf / "src/region_map.c"
    src = caminho.read_text(encoding="utf-8")
    pendentes = {k: v for k, v in RENOMES_REGION_MAP_C.items() if k in src}
    if not pendentes:
        # idempotência: ou já renomeado, ou upstream mudou — confere o novo
        faltam = [v for v in RENOMES_REGION_MAP_C.values() if v not in src]
        return ([f"region_map.c: nem o nome antigo nem o novo: {faltam}"]
                if faltam else [])
    for velho, novo in pendentes.items():
        src = re.sub(rf"\b{velho}\b", novo, src)
    if escrever:
        caminho.write_text(src, encoding="utf-8")
    return []


# --------------------------------------------- 3. bloco com #ifdef no meio
IFDEF_ANTIGO = '''PalletTown_RivalsHouse_Text_ThereYouGoAllDone::
#ifdef BUGFIX @ The localizers missed what should be a textcolor change in the localizations.
    .string "{COLOR DARK_GRAY}{STR_VAR_1} looks dreamily content…\\p"
    .string "{COLOR RED}DAISY: There you go! All done.\\n"
#else @ In the JP games, gender-based text used a different font instead of different colors.
    .string "{FONT_NORMAL}{STR_VAR_1} looks dreamily content…\\p"
    .string "{FONT_FEMALE}DAISY: There you go! All done.\\n"
#endif
    .string "See? Doesn't it look nice?\\p"
    .string "Giggle…\\n"
    .string "It's such a cute POKéMON.$"'''

IFDEF_NOVO = '''PalletTown_RivalsHouse_Text_ThereYouGoAllDone::
#ifdef BUGFIX @ The localizers missed what should be a textcolor change in the localizations.
    .string "{COLOR DARK_GRAY}{STR_VAR_1} parece contente, sonhando…\\p"
    .string "{COLOR RED}DAISY: Prontinho! Terminei.\\n"
#else @ In the JP games, gender-based text used a different font instead of different colors.
    .string "{FONT_NORMAL}{STR_VAR_1} parece contente, sonhando…\\p"
    .string "{FONT_FEMALE}DAISY: Prontinho! Terminei.\\n"
#endif
    .string "Viu? Não ficou uma graça?\\p"
    .string "Hihihi…\\n"
    .string "É um POKéMON tão fofo.$"'''


def aplicar_ifdef(pf: Path, escrever: bool) -> list[str]:
    caminho = pf / "data/maps/PalletTown_RivalsHouse/text.inc"
    src = caminho.read_text(encoding="utf-8")
    if IFDEF_NOVO in src:
        return []
    if IFDEF_ANTIGO not in src:
        return ["PalletTown_RivalsHouse/text.inc: bloco #ifdef não encontrado"]
    if escrever:
        caminho.write_text(src.replace(IFDEF_ANTIGO, IFDEF_NOVO, 1),
                           encoding="utf-8")
    return []


def self_test() -> int:
    # 1. nenhum nome do mapa estoura 19 chars (janela do mapa de voo = 120 px
    #    em FONT_SMALL; o maior original tem 15)
    pior = max(NOMES_MAPA.values(), key=len)
    assert len(pior) <= 19, pior
    # 2. ROTA regex
    assert RE_ROTA.match("ROUTE 10").group(1) == "10"
    assert not RE_ROTA.match("ROUTE 10 X")
    # 3. os trechos de C antigos têm chaves balanceadas (sanidade de recorte)
    for t in (ALTURA_ANTIGA, PESO_ANTIGO):
        assert t.count("(") == t.count(")"), "parênteses"
    # 4. as variantes do ifdef mantêm os mesmos placeholders
    ph = re.findall(r"\{[A-Z_ 0-9]+\}", IFDEF_ANTIGO)
    ph2 = re.findall(r"\{[A-Z_ 0-9]+\}", IFDEF_NOVO)
    assert ph == ph2, (ph, ph2)
    print("self-test: OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered", type=Path)
    ap.add_argument("--check", action="store_true",
                    help="só verifica, não escreve")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.pokefirered:
        ap.error("--pokefirered é obrigatório (ou use --self-test)")
    pf = args.pokefirered
    escrever = not args.check
    erros = (aplicar_metrico(pf, escrever)
             + aplicar_mapa(pf, escrever)
             + aplicar_region_map_c(pf, escrever)
             + aplicar_ifdef(pf, escrever))
    for e in erros:
        print("ERRO:", e)
    if not erros:
        print(("aplicado" if escrever else "check ok")
              + ": métrico na dex + nomes do mapa (json+region_map.c) + bloco #ifdef")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
