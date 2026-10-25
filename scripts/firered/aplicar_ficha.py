#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplica a tela "FICHA DE PERSONAGEM" ao pokefirered.

O que faz (idempotente — pode rodar quantas vezes quiser):
  1. Copia scripts/firered/ficha/ficha_personagem.c -> <pokefirered>/src/
  2. Copia scripts/firered/ficha/ficha_personagem.h -> <pokefirered>/include/
  3. Patcheia src/start_menu.c: novo item "FICHA" no menu START
     (enum, tabela de ações, descrições, SetUpStartMenu_NormalField e callback).

Uso:
  python3 aplicar_ficha.py --pokefirered /tmp/pokefirered --check   # só verifica
  python3 aplicar_ficha.py --pokefirered /tmp/pokefirered --write   # aplica
  python3 aplicar_ficha.py --self-test
"""
import argparse
import os
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_FICHA = os.path.join(AQUI, "ficha")

MARCADOR = "ficha_personagem.h"  # presença no start_menu.c == já aplicado

# (âncora, texto inserido DEPOIS da âncora)
PATCHES = [
    (
        '#include "trainer_card.h"\n',
        '#include "ficha_personagem.h"\n',
    ),
    (
        "    STARTMENU_PLAYER2,\n",
        "    STARTMENU_FICHA,\n",
    ),
    (
        "static bool8 StartMenuPlayerCallback(void);\n",
        "static bool8 StartMenuFichaCallback(void);\n",
    ),
    (
        "static const struct MenuAction sStartMenuActionTable[] = {\n",
        "",  # tratado em patch_tabela_acoes (precisa de texto antes da tabela)
    ),
]

TEXTO_MENU = (
    'static const u8 sText_MenuFicha[] = _("FICHA");\n'
    'static const u8 sStartMenuDesc_Ficha[] = _("A FICHA DE PERSONAGEM dos seus\\n"\n'
    '                                           "POKéMON, como num RPG.");\n\n'
)

LINHA_TABELA = (
    ",\n    [STARTMENU_FICHA]   = { sText_MenuFicha,   "
    "{.u8_void = StartMenuFichaCallback} }"
)

CALLBACK = """static bool8 StartMenuFichaCallback(void)
{
    if (!gPaletteFade.active)
    {
        PlayRainStoppingSoundEffect();
        DestroySafariZoneStatsWindow();
        CleanupOverworldWindowsAndTilemaps();
        ShowFichaPersonagem(CB2_ReturnToFieldWithOpenMenu);
        return TRUE;
    }
    return FALSE;
}

"""


def inserir_apos(conteudo, ancora, novo):
    assert ancora in conteudo, "âncora não encontrada: %r" % ancora[:60]
    i = conteudo.index(ancora) + len(ancora)
    return conteudo[:i] + novo + conteudo[i:]


def patch_start_menu(texto):
    """Devolve o start_menu.c patcheado (ou o original, se já aplicado)."""
    if MARCADOR in texto:
        return texto, False

    # include
    texto = inserir_apos(texto, '#include "trainer_card.h"\n',
                         '#include "ficha_personagem.h"\n')
    # enum (antes de MAX_STARTMENU_ITEMS)
    texto = inserir_apos(texto, "    STARTMENU_PLAYER2,\n",
                         "    STARTMENU_FICHA,\n")
    # protótipo
    texto = inserir_apos(texto, "static bool8 StartMenuPlayerCallback(void);\n",
                         "static bool8 StartMenuFichaCallback(void);\n")
    # strings locais antes da tabela de ações
    ancora_tab = "static const struct MenuAction sStartMenuActionTable[] = {"
    assert ancora_tab in texto
    i = texto.index(ancora_tab)
    texto = texto[:i] + TEXTO_MENU + texto[i:]
    # entrada na tabela de ações
    fim_tab = "[STARTMENU_PLAYER2] = { gText_MenuPlayer,  {.u8_void = StartMenuLinkPlayerCallback} }"
    texto = inserir_apos(texto, fim_tab, LINHA_TABELA)
    # tabela de descrições (termina com gStartMenuDesc_Player\n};)
    antigo = "    gStartMenuDesc_Retire,\n    gStartMenuDesc_Player\n};"
    novo = ("    gStartMenuDesc_Retire,\n    gStartMenuDesc_Player,\n"
            "    sStartMenuDesc_Ficha\n};")
    assert antigo in texto
    texto = texto.replace(antigo, novo, 1)
    # item no menu do campo normal (depois de PLAYER, antes de SAVE)
    antigo = ("    AppendToStartMenuItems(STARTMENU_PLAYER);\n"
              "    AppendToStartMenuItems(STARTMENU_SAVE);\n")
    novo = ("    AppendToStartMenuItems(STARTMENU_PLAYER);\n"
            "    AppendToStartMenuItems(STARTMENU_FICHA);\n"
            "    AppendToStartMenuItems(STARTMENU_SAVE);\n")
    assert antigo in texto
    texto = texto.replace(antigo, novo, 1)
    # callback antes da definição de StartMenuSaveCallback
    ancora_cb = "static bool8 StartMenuSaveCallback(void)\n{"
    assert ancora_cb in texto
    i = texto.index(ancora_cb)
    texto = texto[:i] + CALLBACK + texto[i:]
    # com 8 itens o menu ficaria por baixo da caixa de ajuda: compacta o
    # espaçamento de 15 -> 14 px só quando houver 8+ itens
    antigo = "static EWRAM_DATA u8 sStartMenuOrder[MAX_STARTMENU_ITEMS] = {};\n"
    assert antigo in texto
    texto = texto.replace(
        antigo,
        antigo + "\n#define ESPACO_ITEM_MENU (sNumStartMenuItems >= 8 ? 14 : 15)\n",
        1)
    for antigo, novo in (
        ("sStartMenuActionTable[sStartMenuOrder[i]].text, 8, i * 15);",
         "sStartMenuActionTable[sStartMenuOrder[i]].text, 8, i * ESPACO_ITEM_MENU);"),
        ("AddTextPrinterParameterized(GetStartMenuWindowId(), FONT_NORMAL, gStringVar4, 8, i * 15, 0xFF, NULL);",
         "AddTextPrinterParameterized(GetStartMenuWindowId(), FONT_NORMAL, gStringVar4, 8, i * ESPACO_ITEM_MENU, 0xFF, NULL);"),
        ("Menu_InitCursor(GetStartMenuWindowId(), FONT_NORMAL, 0, 0, 15, sNumStartMenuItems, sStartMenuCursorPos);",
         "Menu_InitCursor(GetStartMenuWindowId(), FONT_NORMAL, 0, 0, ESPACO_ITEM_MENU, sNumStartMenuItems, sStartMenuCursorPos);"),
    ):
        assert antigo in texto, antigo[:50]
        texto = texto.replace(antigo, novo, 1)
    return texto, True


def patch_menu_helpers(texto):
    """Janela do menu START 1 tile menor quando há 8+ itens (acompanha os 14 px)."""
    antigo = "struct WindowTemplate template = SetWindowTemplateFields(0, 0x16, 1, 7, height * 2 - 1, DLG_WINDOW_PALETTE_NUM, 0x13D);"
    novo = "struct WindowTemplate template = SetWindowTemplateFields(0, 0x16, 1, 7, height >= 8 ? height * 2 - 2 : height * 2 - 1, DLG_WINDOW_PALETTE_NUM, 0x13D);"
    if novo in texto:
        return texto, False
    assert antigo in texto
    return texto.replace(antigo, novo, 1), True


def aplicar(raiz, escrever):
    ok = True
    # 1-2. fontes novos
    pares = [
        (os.path.join(DIR_FICHA, "ficha_personagem.c"), os.path.join(raiz, "src", "ficha_personagem.c")),
        (os.path.join(DIR_FICHA, "ficha_personagem.h"), os.path.join(raiz, "include", "ficha_personagem.h")),
    ]
    for origem, destino in pares:
        igual = (os.path.exists(destino)
                 and open(destino, encoding="utf-8").read() == open(origem, encoding="utf-8").read())
        if igual:
            print("ok  : %s (já copiado)" % os.path.relpath(destino, raiz))
        elif escrever:
            shutil.copyfile(origem, destino)
            print("copy: %s" % os.path.relpath(destino, raiz))
        else:
            print("PENDENTE: %s" % os.path.relpath(destino, raiz))
            ok = False
    # 3. start_menu.c e new_menu_helpers.c — sempre partindo do arquivo
    #    pristine do git (HEAD), para ser idempotente e imune a versões
    #    antigas do patch que tenham ficado no diretório de trabalho.
    import subprocess
    for rel, funcao in (("src/start_menu.c", patch_start_menu),
                        ("src/new_menu_helpers.c", patch_menu_helpers)):
        pristine = subprocess.run(["git", "-C", raiz, "show", "HEAD:" + rel],
                                  capture_output=True, text=True, check=True).stdout
        patcheado, _ = funcao(pristine)
        caminho = os.path.join(raiz, rel)
        atual = open(caminho, encoding="utf-8").read()
        if atual == patcheado:
            print("ok  : %s (já patcheado)" % rel)
        elif escrever:
            open(caminho, "w", encoding="utf-8").write(patcheado)
            print("patch: %s" % rel)
        else:
            print("PENDENTE: %s" % rel)
            ok = False
    return ok


def self_test():
    # patch deve ser aplicável sobre um esqueleto mínimo e ser idempotente
    esqueleto = (
        '#include "trainer_card.h"\n'
        "enum StartMenuOption\n{\n    STARTMENU_PLAYER2,\n    MAX_STARTMENU_ITEMS\n};\n"
        "static bool8 StartMenuPlayerCallback(void);\n"
        "static EWRAM_DATA u8 sStartMenuOrder[MAX_STARTMENU_ITEMS] = {};\n"
        "static const struct MenuAction sStartMenuActionTable[] = {\n"
        "    [STARTMENU_PLAYER2] = { gText_MenuPlayer,  {.u8_void = StartMenuLinkPlayerCallback} }\n};\n"
        "static const u8 *const sStartMenuDescPointers[] = {\n"
        "    gStartMenuDesc_Retire,\n    gStartMenuDesc_Player\n};\n"
        "sStartMenuActionTable[sStartMenuOrder[i]].text, 8, i * 15);\n"
        "AddTextPrinterParameterized(GetStartMenuWindowId(), FONT_NORMAL, gStringVar4, 8, i * 15, 0xFF, NULL);\n"
        "Menu_InitCursor(GetStartMenuWindowId(), FONT_NORMAL, 0, 0, 15, sNumStartMenuItems, sStartMenuCursorPos);\n"
        "static void SetUpStartMenu_NormalField(void)\n{\n"
        "    AppendToStartMenuItems(STARTMENU_PLAYER);\n"
        "    AppendToStartMenuItems(STARTMENU_SAVE);\n}\n"
        "static bool8 StartMenuSaveCallback(void)\n{\n}\n"
    )
    uma_vez, mudou1 = patch_start_menu(esqueleto)
    assert mudou1
    duas_vezes, mudou2 = patch_start_menu(uma_vez)
    assert not mudou2 and duas_vezes == uma_vez
    for trecho in ("STARTMENU_FICHA,", "sText_MenuFicha", "StartMenuFichaCallback(void)\n{",
                   "sStartMenuDesc_Ficha", "AppendToStartMenuItems(STARTMENU_FICHA);",
                   "ESPACO_ITEM_MENU (sNumStartMenuItems >= 8 ? 14 : 15)",
                   "i * ESPACO_ITEM_MENU);"):
        assert trecho in uma_vez, trecho
    # helper da janela
    esqueleto2 = ("struct WindowTemplate template = SetWindowTemplateFields(0, 0x16, 1, 7, "
                  "height * 2 - 1, DLG_WINDOW_PALETTE_NUM, 0x13D);\n")
    h1, m1 = patch_menu_helpers(esqueleto2)
    assert m1 and "height >= 8" in h1
    h2, m2 = patch_menu_helpers(h1)
    assert not m2 and h2 == h1
    # fontes existem e têm o símbolo público
    c = open(os.path.join(DIR_FICHA, "ficha_personagem.c"), encoding="utf-8").read()
    assert "void ShowFichaPersonagem" in c
    assert os.path.exists(os.path.join(DIR_FICHA, "ficha_personagem.h"))
    print("self-test: OK")


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
    if not args.pokefirered:
        ap.error("--pokefirered é obrigatório (exceto com --self-test)")
    ok = aplicar(args.pokefirered, args.write)
    if args.check and not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
