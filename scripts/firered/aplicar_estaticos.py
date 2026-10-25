#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplica os ENCONTROS ESTÁTICOS (espécies inobtíveis como lendários) ao pokefirered.

Copia scripts/firered/estaticos/* para a árvore do pokefirered e aplica os
patches de motor (novo graphics id, hook de sprite, flags virtuais da Pokédex,
specials e script compartilhado). Idempotente: rodar duas vezes não duplica.

Uso:
  aplicar_estaticos.py --pokefirered /tmp/pokefirered --check|--write
  aplicar_estaticos.py --self-test
"""
import argparse
import os
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_ESTATICOS = os.path.join(AQUI, "estaticos")

COPIAS = [
    ("encontros_estaticos.c", "src/encontros_estaticos.c"),
    ("encontros_estaticos.h", "include/encontros_estaticos.h"),
    ("encontros_estaticos.inc", "data/scripts/encontros_estaticos.inc"),
]

GFX_INFO_NOVO = """
// Encontros estáticos: placeholder 32x32 cujo frame vira o ícone da espécie
// em EstaticoConfigurarSprite (hook no spawn). paletteSlot=NPC_1 evita carga
// de paleta no spawn; a paleta real (do ícone) entra no slot NPC_SPECIAL.
const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_MonEstatico = {
    .tileTag = TAG_NONE,
    .paletteTag = OBJ_EVENT_PAL_TAG_NONE,
    .reflectionPaletteTag = OBJ_EVENT_PAL_TAG_NONE,
    .size = 512,
    .width = 32,
    .height = 32,
    .paletteSlot = PALSLOT_NPC_1,
    .shadowSize = SHADOW_SIZE_M,
    .inanimate = TRUE,
    .disableReflectionPaletteLoad = TRUE,
    .tracks = TRACKS_NONE,
    .oam = &gObjectEventBaseOam_32x32,
    .subspriteTables = gObjectEventSpriteOamTables_32x32,
    .anims = sAnimTable_Inanimate,
    .images = sPicTable_Biker,
    .affineAnims = gDummySpriteAffineAnimTable,
};
"""

# (arquivo, marcador_de_ja_aplicado, âncora, texto_novo, modo)
# modo "apos": insere texto_novo logo após a âncora
# modo "troca": substitui a âncora por texto_novo (que deve conter o marcador)
PATCHES = [
    (
        "include/constants/event_objects.h",
        "OBJ_EVENT_GFX_MON_ESTATICO",
        "#define OBJ_EVENT_GFX_SS_ANNE 151\n",
        "#define OBJ_EVENT_GFX_MON_ESTATICO 152\n",
        "apos",
    ),
    (
        "include/constants/event_objects.h",
        "#define NUM_OBJ_EVENT_GFX     153",
        "#define NUM_OBJ_EVENT_GFX     152",
        "#define NUM_OBJ_EVENT_GFX     153",
        "troca",
    ),
    (
        "src/data/object_events/object_event_graphics_info.h",
        "gObjectEventGraphicsInfo_MonEstatico",
        None,  # None => append no fim do arquivo
        GFX_INFO_NOVO,
        "apos",
    ),
    (
        "src/data/object_events/object_event_graphics_info_pointers.h",
        "gObjectEventGraphicsInfo_MonEstatico;",
        "const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_SSAnne;\n",
        "const struct ObjectEventGraphicsInfo gObjectEventGraphicsInfo_MonEstatico;\n",
        "apos",
    ),
    (
        "src/data/object_events/object_event_graphics_info_pointers.h",
        "[OBJ_EVENT_GFX_MON_ESTATICO]",
        "    [OBJ_EVENT_GFX_SS_ANNE]                  = &gObjectEventGraphicsInfo_SSAnne,\n",
        "    [OBJ_EVENT_GFX_MON_ESTATICO]             = &gObjectEventGraphicsInfo_MonEstatico,\n",
        "apos",
    ),
    (
        "src/event_object_movement.c",
        "encontros_estaticos.h",
        '#include "event_object_movement.h"\n',
        '#include "encontros_estaticos.h"\n',
        "apos",
    ),
    (
        # O hook fica no CALLER porque TrySpawnObjectEventTemplate sobrescreve
        # sprite->images com graphicsInfo->images DEPOIS de criar o sprite.
        "src/event_object_movement.c",
        "EstaticoConfigurarSprite(objectEventTemplate",
        "    gSprites[gObjectEvents[objectEventId].spriteId].images = graphicsInfo->images;\n"
        "    if (subspriteTables)\n",
        "    gSprites[gObjectEvents[objectEventId].spriteId].images = graphicsInfo->images;\n"
        "    if (gObjectEvents[objectEventId].graphicsId == OBJ_EVENT_GFX_MON_ESTATICO)\n"
        "        EstaticoConfigurarSprite(objectEventTemplate, &gSprites[gObjectEvents[objectEventId].spriteId], objectEventId);\n"
        "    if (subspriteTables)\n",
        "troca",
    ),
    (
        # Respawn de sprites ao voltar de menu/batalha não passa pelo spawn
        # normal; reconfigura o ícone pela localId.
        "src/event_object_movement.c",
        "EstaticoReconfigurarSprite(objectEvent",
        "        ResetObjectEventFldEffData(objectEvent);\n"
        "        SetObjectSubpriorityByElevation(objectEvent->previousElevation, sprite, 1);\n",
        "        ResetObjectEventFldEffData(objectEvent);\n"
        "        SetObjectSubpriorityByElevation(objectEvent->previousElevation, sprite, 1);\n"
        "        if (objectEvent->graphicsId == OBJ_EVENT_GFX_MON_ESTATICO)\n"
        "            EstaticoReconfigurarSprite(objectEvent, sprite, objectEventId);\n",
        "troca",
    ),
    (
        "src/event_data.c",
        "encontros_estaticos.h",
        '#include "event_data.h"\n',
        '#include "encontros_estaticos.h"\n',
        "apos",
    ),
    (
        # Set/Clear: GetFlagAddr devolve NULL na faixa virtual => nada escrito.
        "src/event_data.c",
        "estaticoDummy",
        "u8 *GetFlagAddr(u16 idx)\n{\n    u8 *ptr;\n    if (idx == 0)\n        return NULL;\n",
        "u8 *GetFlagAddr(u16 idx)\n{\n    u8 *ptr;\n    bool8 estaticoDummy;\n    if (idx == 0)\n        return NULL;\n"
        "    if (EstaticoFlagVirtual(idx, &estaticoDummy))\n        return NULL; // flag virtual dos encontros estaticos\n",
        "troca",
    ),
    (
        # Get: responde pela Pokédex na faixa virtual.
        "src/event_data.c",
        "estaticoValor",
        "bool8 FlagGet(u16 idx)\n{\n    u8 *ptr = GetFlagAddr(idx);\n",
        "bool8 FlagGet(u16 idx)\n{\n    u8 *ptr;\n    bool8 estaticoValor;\n"
        "    if (EstaticoFlagVirtual(idx, &estaticoValor))\n        return estaticoValor;\n"
        "    ptr = GetFlagAddr(idx);\n",
        "troca",
    ),
    (
        # Tem de entrar ANTES de gSpecialsEnd:: (o comando special valida o
        # índice contra o fim da tabela; depois do rótulo não funciona).
        "data/specials.inc",
        "EstaticoPrepararEncontro",
        "gSpecialsEnd::",
        "\tdef_special EstaticoPrepararEncontro\n\tdef_special EstaticoCriarInimigo\ngSpecialsEnd::",
        "troca",
    ),
    (
        "data/event_scripts.s",
        "encontros_estaticos.inc",
        None,
        '\n\t.include "data/scripts/encontros_estaticos.inc"\n',
        "apos",
    ),
    (
        "data/map_events.s",
        "constants/species.h",
        '#include "constants/maps.h"\n',
        '#include "constants/species.h"\n',
        "apos",
    ),
]


def aplicar_um(texto, marcador, ancora, novo, modo):
    """Devolve (texto_novo, situacao) com situacao em {ja_aplicado, aplicado, erro}."""
    if marcador in texto:
        return texto, "ja_aplicado"
    if ancora is None:  # append
        return texto + novo, "aplicado"
    if ancora not in texto:
        return texto, "erro"
    if texto.count(ancora) != 1:
        return texto, "erro"
    if modo == "apos":
        return texto.replace(ancora, ancora + novo, 1), "aplicado"
    return texto.replace(ancora, novo, 1), "aplicado"


def rodar(raiz, escrever):
    erros = 0
    for origem, destino in COPIAS:
        src = os.path.join(DIR_ESTATICOS, origem)
        dst = os.path.join(raiz, destino)
        igual = os.path.exists(dst) and open(src, "rb").read() == open(dst, "rb").read()
        print(("= " if igual else "C ") + destino)
        if escrever and not igual:
            shutil.copyfile(src, dst)
    for arquivo, marcador, ancora, novo, modo in PATCHES:
        caminho = os.path.join(raiz, arquivo)
        with open(caminho, "r", encoding="utf-8") as f:
            texto = f.read()
        texto2, situacao = aplicar_um(texto, marcador, ancora, novo, modo)
        print(f"{situacao:>11}  {arquivo}  [{marcador[:40]}]")
        if situacao == "erro":
            erros += 1
        elif escrever and situacao == "aplicado":
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(texto2)
    return erros


def self_test():
    # idempotência e os três modos sobre fixtures sintéticas
    t = "a\nANCORA\nb\n"
    t1, s1 = aplicar_um(t, "NOVO", "ANCORA\n", "NOVO\n", "apos")
    assert s1 == "aplicado" and "ANCORA\nNOVO\n" in t1
    t2, s2 = aplicar_um(t1, "NOVO", "ANCORA\n", "NOVO\n", "apos")
    assert s2 == "ja_aplicado" and t2 == t1
    t3, s3 = aplicar_um(t, "NOVO", "SUMIDO\n", "NOVO\n", "apos")
    assert s3 == "erro" and t3 == t
    t4, s4 = aplicar_um(t, "TROCADO", "ANCORA\n", "TROCADO\n", "troca")
    assert s4 == "aplicado" and "ANCORA" not in t4
    t5, s5 = aplicar_um(t, "APPEND", None, "APPEND\n", "apos")
    assert s5 == "aplicado" and t5.endswith("APPEND\n")
    t6, s6 = aplicar_um(t + "ANCORA\n", "X", "ANCORA\n", "X\n", "apos")
    assert s6 == "erro"  # âncora ambígua
    for origem, _ in COPIAS:
        assert os.path.exists(os.path.join(DIR_ESTATICOS, origem)), origem
    print("self-test OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pokefirered")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.pokefirered or not (args.check or args.write):
        ap.error("use --pokefirered PATH com --check ou --write")
    erros = rodar(args.pokefirered, args.write)
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
