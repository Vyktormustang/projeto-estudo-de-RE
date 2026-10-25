// FICHA DE PERSONAGEM — tela extra no menu START (projeto de tradução PT-BR).
// Adaptação da ficha de RPG (estilo MHA/BNHA) ao design do FireRed, uma ficha
// POR POKéMON da equipe (pedido do usuário: "era pra ser para os pokemons"):
//  - NOME = espécie · CODINOME = apelido · TIPO = tipos do POKéMON
//  - ALTURA = altura da espécie (Pokédex) · AFILIAÇÃO = treinador original
//  - INDIVIDUALIDADE = habilidade · HABILIDADES = os 4 golpes
//  - EQUIPAMENTO = item segurado · radar hexagonal = os 6 atributos
//  - retrato = ícone animado do POKéMON · ←/→ folheia a equipe
// Estrutura baseada em src/diploma.c (tela cheia simples com janelas de texto).

#include "global.h"
#include "gflib.h"
#include "menu.h"
#include "new_menu_helpers.h"
#include "overworld.h"
#include "scanline_effect.h"
#include "task.h"
#include "text_window.h"
#include "item.h"
#include "event_data.h"
#include "string_util.h"
#include "party_menu.h"
#include "pokedex.h"
#include "pokedex_screen.h"
#include "pokemon_icon.h"
#include "battle_main.h"
#include "data.h"
#include "ficha_personagem.h"
#include "constants/songs.h"
#include "constants/items.h"
#include "constants/moves.h"

enum
{
    WIN_ESQ,   // coluna esquerda (18 tiles): título + campos
    WIN_DIR,   // coluna direita (12 tiles): ícone, radar e legenda
    WIN_FICHA_COUNT
};

enum
{
    BG_FICHA_ESQ,  // BG0, charbase 0
    BG_FICHA_DIR,  // BG1, charbase 1
};

struct FichaScreen
{
    u8 initState;
    u8 slot;
    u8 iconSpriteId;
    void (*savedCallback)(void);
    u16 bgBufEsq[0x400];
    u16 bgBufDir[0x400];
};

static EWRAM_DATA struct FichaScreen *sFicha = NULL;

static void CB2_Ficha(void);
static void Task_FichaInit(u8 taskId);
static void Task_FichaInput(u8 taskId);
static void FichaInitScreen(void);
static void FichaDesenharTudo(void);
static void FichaCriarIcone(void);

static const struct BgTemplate sFichaBgTemplates[] = {
    {
        .bg = BG_FICHA_ESQ,
        .charBaseIndex = 0,
        .mapBaseIndex = 31,
        .screenSize = 0,
        .paletteMode = 0,
        .priority = 0,
        .baseTile = 0,
    }, {
        .bg = BG_FICHA_DIR,
        .charBaseIndex = 1,
        .mapBaseIndex = 30,
        .screenSize = 0,
        .paletteMode = 0,
        .priority = 1,
        .baseTile = 0,
    }
};

static const struct WindowTemplate sFichaWinTemplates[WIN_FICHA_COUNT + 1] = {
    [WIN_ESQ] = {
        .bg = BG_FICHA_ESQ,
        .tilemapLeft = 0,
        .tilemapTop = 0,
        .width = 18,
        .height = 20,
        .paletteNum = 15,
        .baseBlock = 1
    },
    [WIN_DIR] = {
        .bg = BG_FICHA_DIR,
        .tilemapLeft = 18,
        .tilemapTop = 0,
        .width = 12,
        .height = 20,
        .paletteNum = 15,
        .baseBlock = 1
    },
    [WIN_FICHA_COUNT] = DUMMY_WIN_TEMPLATE
};

static const ALIGNED(4) u8 sCores_Rotulo[3] = { TEXT_COLOR_WHITE, TEXT_COLOR_DARK_GRAY, TEXT_COLOR_LIGHT_GRAY };
static const ALIGNED(4) u8 sCores_Valor[3]  = { TEXT_COLOR_WHITE, TEXT_COLOR_RED, TEXT_COLOR_LIGHT_RED };
static const ALIGNED(4) u8 sCores_Titulo[3] = { TEXT_COLOR_DARK_GRAY, TEXT_COLOR_WHITE, TEXT_COLOR_LIGHT_GRAY };

// Textos (PT-BR)
static const u8 sTexto_Titulo[]    = _("FICHA DE PERSONAGEM");
static const u8 sTexto_Nome[]      = _("NOME:");
static const u8 sTexto_Codinome[]  = _("CODINOME:");
static const u8 sTexto_TipoRot[]   = _("TIPO:");
static const u8 sTexto_Afiliacao[] = _("AFILIAÇÃO:");
static const u8 sTexto_Individ[]   = _("INDIVIDUALIDADE:");
static const u8 sTexto_Equip[]     = _("EQUIPAMENTO:");
static const u8 sTexto_Habilid[]   = _("HABILIDADES:");
static const u8 sTexto_Altura[]    = _("ALTURA: ");
static const u8 sTexto_Metro[]     = _(" m");
static const u8 sTexto_Nenhum[]    = _("NENHUM");
static const u8 sTexto_Traco[]     = _("---");
static const u8 sTexto_Ovo[]       = _("OVO POKéMON");
static const u8 sTexto_SemMon[]    = _("NENHUM POKéMON NA EQUIPE.");
static const u8 sTexto_Barra[]     = _("/");

// Legenda do radar (ordem horária a partir do topo)
static const u8 sTexto_Poder[]    = _("PODER");
static const u8 sTexto_Tecnica[]  = _("TÉCNICA");
static const u8 sTexto_Veloc[]    = _("VELOC.");
static const u8 sTexto_Controle[] = _("CONTR.");
static const u8 sTexto_Cooper[]   = _("COOPER.");
static const u8 sTexto_Intelig[]  = _("INTELIG.");

// Radar: geometria do hexágono (vetores unitários x1000, sentido horário do topo)
static const s16 sHexDir[6][2] = {
    {    0, -1000 }, // PODER        (topo)
    {  866,  -500 }, // TÉCNICA      (sup. direita)
    {  866,   500 }, // VELOCIDADE   (inf. direita)
    {    0,  1000 }, // CONTROLE     (base)
    { -866,   500 }, // COOPERAÇÃO   (inf. esquerda)
    { -866,  -500 }, // INTELIGÊNCIA (sup. esquerda)
};

// Cor (índice da paleta de texto) de cada vértice/atributo
static const u8 sCorAtributo[6] = {
    TEXT_COLOR_RED,         // PODER        = Ataque
    TEXT_COLOR_GREEN,       // TÉCNICA      = Ataque Esp.
    TEXT_COLOR_LIGHT_BLUE,  // VELOCIDADE   = Velocidade
    TEXT_COLOR_DARK_GRAY,   // CONTROLE     = Defesa
    TEXT_COLOR_LIGHT_RED,   // COOPERAÇÃO   = PS
    TEXT_COLOR_BLUE,        // INTELIGÊNCIA = Defesa Esp.
};

#define RADAR_CX   48   // relativo à janela direita (px 144 da tela)
#define RADAR_CY   94
#define RADAR_R    30
#define ICONE_X    192  // coordenadas de tela do centro do ícone
#define ICONE_Y    34

static void VBlankCB_Ficha(void)
{
    LoadOam();
    ProcessSpriteCopyRequests();
    TransferPlttBuffer();
}

void ShowFichaPersonagem(void (*callback)(void))
{
    sFicha = AllocZeroed(sizeof(*sFicha));
    sFicha->initState = 0;
    sFicha->slot = 0;
    sFicha->iconSpriteId = SPRITE_NONE;
    sFicha->savedCallback = callback;
    ResetSpriteData();
    ResetPaletteFade();
    FreeAllSpritePalettes();
    ResetTasks();
    ScanlineEffect_Stop();
    CreateTask(Task_FichaInit, 0);
    SetMainCallback2(CB2_Ficha);
}

static void CB2_Ficha(void)
{
    RunTasks();
    AnimateSprites();
    BuildOamBuffer();
    UpdatePaletteFade();
}

static void Task_FichaInit(u8 taskId)
{
    switch (sFicha->initState)
    {
    case 0:
        SetVBlankCallback(NULL);
        break;
    case 1:
        FichaInitScreen();
        break;
    case 2:
        LoadPalette(GetTextWindowPalette(2), BG_PLTT_ID(15), PLTT_SIZE_4BPP);
        LoadMonIconPalettes();
        break;
    case 3:
        FichaDesenharTudo();
        FichaCriarIcone();
        break;
    case 4:
        PutWindowTilemap(WIN_ESQ);
        PutWindowTilemap(WIN_DIR);
        CopyWindowToVram(WIN_ESQ, COPYWIN_FULL);
        CopyWindowToVram(WIN_DIR, COPYWIN_FULL);
        CopyBgTilemapBufferToVram(BG_FICHA_ESQ);
        CopyBgTilemapBufferToVram(BG_FICHA_DIR);
        break;
    case 5:
        BeginNormalPaletteFade(PALETTES_ALL, 0, 16, 0, RGB_BLACK);
        break;
    case 6:
        SetVBlankCallback(VBlankCB_Ficha);
        break;
    default:
        if (gPaletteFade.active)
            break;
        gTasks[taskId].func = Task_FichaInput;
    }
    sFicha->initState++;
}

static void FichaTrocarSlot(s8 delta)
{
    u8 n = CalculatePlayerPartyCount();

    if (n < 2)
        return;
    sFicha->slot = (sFicha->slot + n + delta) % n;
    PlaySE(SE_SELECT);
    FichaDesenharTudo();
    FichaCriarIcone();
    CopyWindowToVram(WIN_ESQ, COPYWIN_FULL);
    CopyWindowToVram(WIN_DIR, COPYWIN_FULL);
}

static void Task_FichaInput(u8 taskId)
{
    void (*callback)(void);

    if (gTasks[taskId].data[0] == 0)
    {
        if (JOY_NEW(DPAD_LEFT))
            FichaTrocarSlot(-1);
        else if (JOY_NEW(DPAD_RIGHT))
            FichaTrocarSlot(+1);
        else if (JOY_NEW(A_BUTTON | B_BUTTON))
        {
            PlaySE(SE_SELECT);
            BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
            gTasks[taskId].data[0] = 1;
        }
    }
    if (gTasks[taskId].data[0] == 1 && !gPaletteFade.active)
    {
        callback = sFicha->savedCallback;
        DestroyTask(taskId);
        FreeMonIconPalettes();
        FreeAllWindowBuffers();
        FREE_AND_SET_NULL(sFicha);
        SetMainCallback2(callback);
    }
}

static void FichaInitScreen(void)
{
    void *vram = (void *)VRAM;

    DmaClearLarge16(3, vram, VRAM_SIZE, 0x1000);
    DmaClear32(3, (void *)OAM, OAM_SIZE);
    DmaClear16(3, (void *)PLTT, PLTT_SIZE);
    SetGpuReg(REG_OFFSET_DISPCNT, 0);
    ResetBgsAndClearDma3BusyFlags(0);
    InitBgsFromTemplates(0, sFichaBgTemplates, ARRAY_COUNT(sFichaBgTemplates));
    ChangeBgX(0, 0, BG_COORD_SET);
    ChangeBgY(0, 0, BG_COORD_SET);
    ChangeBgX(1, 0, BG_COORD_SET);
    ChangeBgY(1, 0, BG_COORD_SET);
    ChangeBgX(2, 0, BG_COORD_SET);
    ChangeBgY(2, 0, BG_COORD_SET);
    ChangeBgX(3, 0, BG_COORD_SET);
    ChangeBgY(3, 0, BG_COORD_SET);
    SetBgTilemapBuffer(BG_FICHA_ESQ, sFicha->bgBufEsq);
    SetBgTilemapBuffer(BG_FICHA_DIR, sFicha->bgBufDir);
    InitWindows(sFichaWinTemplates);
    DeactivateAllTextPrinters();
    SetGpuReg(REG_OFFSET_DISPCNT, DISPCNT_OBJ_1D_MAP | DISPCNT_OBJ_ON);
    ShowBg(BG_FICHA_ESQ);
    ShowBg(BG_FICHA_DIR);
    FillBgTilemapBufferRect_Palette0(BG_FICHA_ESQ, 0, 0, 0, 32, 32);
    FillBgTilemapBufferRect_Palette0(BG_FICHA_DIR, 0, 0, 0, 32, 32);
}

// ---------- ícone do POKéMON (retrato da ficha) ----------

static void FichaCriarIcone(void)
{
    struct Pokemon *mon = &gPlayerParty[sFicha->slot];
    u16 especie;

    if (sFicha->iconSpriteId != SPRITE_NONE)
    {
        DestroyMonIcon(&gSprites[sFicha->iconSpriteId]);
        sFicha->iconSpriteId = SPRITE_NONE;
    }
    if (CalculatePlayerPartyCount() == 0)
        return;
    especie = GetMonData(mon, MON_DATA_SPECIES_OR_EGG);
    if (especie == SPECIES_NONE)
        return;
    sFicha->iconSpriteId = CreateMonIcon(especie, SpriteCB_MonIcon, ICONE_X, ICONE_Y, 0,
                                         GetMonData(mon, MON_DATA_PERSONALITY), TRUE);
}

// ---------- primitivas de desenho (sobre o pixel buffer da janela) ----------

static void FichaPixel(u8 winId, u8 cor, s16 x, s16 y)
{
    if (x < 0 || y < 0)
        return;
    FillWindowPixelRect(winId, PIXEL_FILL(cor), x, y, 1, 1);
}

static void FichaLinha(u8 winId, u8 cor, s16 x0, s16 y0, s16 x1, s16 y1)
{
    s16 dx = x1 >= x0 ? x1 - x0 : x0 - x1;
    s16 dy = y1 >= y0 ? y1 - y0 : y0 - y1;
    s16 sx = x0 < x1 ? 1 : -1;
    s16 sy = y0 < y1 ? 1 : -1;
    s16 err = dx - dy;
    s16 e2;

    while (TRUE)
    {
        FichaPixel(winId, cor, x0, y0);
        if (x0 == x1 && y0 == y1)
            break;
        e2 = 2 * err;
        if (e2 > -dy)
        {
            err -= dy;
            x0 += sx;
        }
        if (e2 < dx)
        {
            err += dx;
            y0 += sy;
        }
    }
}

static void FichaVertice(u8 indice, u16 raio, s16 *x, s16 *y)
{
    *x = RADAR_CX + (s32)sHexDir[indice][0] * raio / 1000;
    *y = RADAR_CY + (s32)sHexDir[indice][1] * raio / 1000;
}

static void FichaDesenharAnel(u16 raio, u8 cor)
{
    s16 x0, y0, x1, y1;
    u32 k;

    for (k = 0; k < 6; k++)
    {
        FichaVertice(k, raio, &x0, &y0);
        FichaVertice((k + 1) % 6, raio, &x1, &y1);
        FichaLinha(WIN_DIR, cor, x0, y0, x1, y1);
    }
}

static void FichaDesenharRadar(struct Pokemon *mon)
{
    u16 stats[6] = { 0, 0, 0, 0, 0, 0 };
    u16 raios[6];
    u16 maior = 0;
    s16 vx[6], vy[6];
    s16 x, y;
    u32 k;
    bool8 temMon = FALSE;

    if (mon != NULL
     && GetMonData(mon, MON_DATA_SPECIES_OR_EGG) != SPECIES_EGG
     && GetMonData(mon, MON_DATA_SPECIES) != SPECIES_NONE)
    {
        temMon = TRUE;
        stats[0] = GetMonData(mon, MON_DATA_ATK);    // PODER
        stats[1] = GetMonData(mon, MON_DATA_SPATK);  // TÉCNICA
        stats[2] = GetMonData(mon, MON_DATA_SPEED);  // VELOCIDADE
        stats[3] = GetMonData(mon, MON_DATA_DEF);    // CONTROLE
        stats[4] = GetMonData(mon, MON_DATA_MAX_HP); // COOPERAÇÃO
        stats[5] = GetMonData(mon, MON_DATA_SPDEF);  // INTELIGÊNCIA
    }

    // grade: 3 anéis concêntricos + raios, em cinza claro
    FichaDesenharAnel(RADAR_R, TEXT_COLOR_LIGHT_GRAY);
    FichaDesenharAnel(RADAR_R * 2 / 3, TEXT_COLOR_LIGHT_GRAY);
    FichaDesenharAnel(RADAR_R / 3, TEXT_COLOR_LIGHT_GRAY);
    for (k = 0; k < 6; k++)
    {
        FichaVertice(k, RADAR_R, &x, &y);
        FichaLinha(WIN_DIR, TEXT_COLOR_LIGHT_GRAY, RADAR_CX, RADAR_CY, x, y);
    }

    if (!temMon)
        return;

    for (k = 0; k < 6; k++)
    {
        if (stats[k] > maior)
            maior = stats[k];
    }
    if (maior == 0)
        maior = 1;

    for (k = 0; k < 6; k++)
    {
        raios[k] = (u32)RADAR_R * stats[k] / maior;
        if (raios[k] < 4)
            raios[k] = 4;
        FichaVertice(k, raios[k], &vx[k], &vy[k]);
    }

    // polígono dos atributos (cinza escuro)
    for (k = 0; k < 6; k++)
        FichaLinha(WIN_DIR, TEXT_COLOR_DARK_GRAY, vx[k], vy[k], vx[(k + 1) % 6], vy[(k + 1) % 6]);

    // pontos coloridos nos vértices (como na ficha original)
    for (k = 0; k < 6; k++)
        FillWindowPixelRect(WIN_DIR, PIXEL_FILL(sCorAtributo[k]), vx[k] - 1, vy[k] - 1, 3, 3);
}

static void FichaLegenda(void)
{
    static const u8 *const rotulos[6] = {
        sTexto_Poder, sTexto_Tecnica, sTexto_Intelig,
        sTexto_Cooper, sTexto_Veloc, sTexto_Controle
    };
    // índice do atributo (cor) correspondente a cada rótulo acima
    static const u8 atrib[6] = { 0, 1, 5, 4, 2, 3 };
    u32 k;

    for (k = 0; k < 6; k++)
    {
        u16 x = (k & 1) ? 50 : 4;
        u16 y = 127 + (k / 2) * 11;

        FillWindowPixelRect(WIN_DIR, PIXEL_FILL(sCorAtributo[atrib[k]]), x, y + 3, 5, 5);
        AddTextPrinterParameterized3(WIN_DIR, FONT_SMALL, x + 8, y, sCores_Rotulo, TEXT_SKIP_DRAW, rotulos[k]);
    }
}

// ---------- conteúdo ----------

// Linhas da coluna esquerda: passo fixo de 11 px a partir de y=19 (13 linhas)
#define LINHA_Y(n) (18 + (n) * 11)

static void FichaCampo(u8 linha, const u8 *rotulo, const u8 *valor)
{
    AddTextPrinterParameterized3(WIN_ESQ, FONT_SMALL, 4, LINHA_Y(linha), sCores_Rotulo, TEXT_SKIP_DRAW, rotulo);
    if (valor != NULL)
        AddTextPrinterParameterized3(WIN_ESQ, FONT_SMALL, 10 + GetStringWidth(FONT_SMALL, rotulo, 0), LINHA_Y(linha), sCores_Valor, TEXT_SKIP_DRAW, valor);
}

static void FichaValorIndentado(u8 linha, const u8 *valor)
{
    AddTextPrinterParameterized3(WIN_ESQ, FONT_SMALL, 14, LINHA_Y(linha), sCores_Valor, TEXT_SKIP_DRAW, valor);
}

static void FichaDesenharTudo(void)
{
    u8 buf[48];
    u8 n = CalculatePlayerPartyCount();
    struct Pokemon *mon = &gPlayerParty[sFicha->slot];
    bool8 ehOvo = FALSE;
    u16 especie = SPECIES_NONE;
    u32 width;
    u32 k;

    FillWindowPixelBuffer(WIN_ESQ, PIXEL_FILL(TEXT_COLOR_WHITE));
    FillWindowPixelBuffer(WIN_DIR, PIXEL_FILL(TEXT_COLOR_WHITE));

    // barra de título (eco das barras pretas da ficha original)
    FillWindowPixelRect(WIN_ESQ, PIXEL_FILL(TEXT_COLOR_DARK_GRAY), 0, 0, 144, 16);
    FillWindowPixelRect(WIN_DIR, PIXEL_FILL(TEXT_COLOR_DARK_GRAY), 0, 0, 96, 16);
    AddTextPrinterParameterized3(WIN_ESQ, FONT_NORMAL, 4, 1, sCores_Titulo, TEXT_SKIP_DRAW, sTexto_Titulo);

    // indicador "slot/total" na barra de título
    ConvertIntToDecimalStringN(buf, n == 0 ? 0 : sFicha->slot + 1, STR_CONV_MODE_LEFT_ALIGN, 1);
    StringAppend(buf, sTexto_Barra);
    ConvertIntToDecimalStringN(buf + StringLength(buf), n, STR_CONV_MODE_LEFT_ALIGN, 1);
    width = GetStringWidth(FONT_SMALL, buf, 0);
    AddTextPrinterParameterized3(WIN_DIR, FONT_SMALL, 92 - width, 3, sCores_Titulo, TEXT_SKIP_DRAW, buf);

    if (n == 0)
    {
        AddTextPrinterParameterized3(WIN_ESQ, FONT_SMALL, 4, LINHA_Y(0), sCores_Rotulo, TEXT_SKIP_DRAW, sTexto_SemMon);
        FichaDesenharRadar(NULL);
        FichaLegenda();
        return;
    }

    especie = GetMonData(mon, MON_DATA_SPECIES_OR_EGG);
    ehOvo = (especie == SPECIES_EGG);

    // NOME (espécie) e CODINOME (apelido)
    if (ehOvo)
    {
        FichaCampo(0, sTexto_Nome, sTexto_Ovo);
        FichaCampo(1, sTexto_Codinome, sTexto_Traco);
        FichaCampo(2, sTexto_TipoRot, sTexto_Traco);
    }
    else
    {
        GetSpeciesName(buf, especie);
        FichaCampo(0, sTexto_Nome, buf);
        GetMonNickname(mon, buf);
        FichaCampo(1, sTexto_Codinome, buf);
        // TIPO (o "tipo sanguíneo" do POKéMON)
        StringCopy(buf, gTypeNames[gSpeciesInfo[especie].types[0]]);
        if (gSpeciesInfo[especie].types[1] != gSpeciesInfo[especie].types[0])
        {
            StringAppend(buf, sTexto_Barra);
            StringAppend(buf, gTypeNames[gSpeciesInfo[especie].types[1]]);
        }
        FichaCampo(2, sTexto_TipoRot, buf);
    }

    // AFILIAÇÃO = treinador original
    GetMonData(mon, MON_DATA_OT_NAME, buf);
    FichaCampo(3, sTexto_Afiliacao, buf);

    // INDIVIDUALIDADE = habilidade
    FichaCampo(4, sTexto_Individ, NULL);
    if (ehOvo)
        FichaValorIndentado(5, sTexto_Traco);
    else
        FichaValorIndentado(5, gAbilityNames[GetMonAbility(mon)]);

    // EQUIPAMENTO = item segurado
    FichaCampo(6, sTexto_Equip, NULL);
    if (!ehOvo && GetMonData(mon, MON_DATA_HELD_ITEM) != ITEM_NONE)
    {
        CopyItemName(GetMonData(mon, MON_DATA_HELD_ITEM), buf);
        FichaValorIndentado(7, buf);
    }
    else
    {
        FichaValorIndentado(7, ehOvo ? sTexto_Traco : sTexto_Nenhum);
    }

    // HABILIDADES = os 4 golpes
    FichaCampo(8, sTexto_Habilid, NULL);
    if (!ehOvo)
    {
        for (k = 0; k < MAX_MON_MOVES; k++)
        {
            u16 golpe = GetMonData(mon, MON_DATA_MOVE1 + k);
            if (golpe != MOVE_NONE)
                FichaValorIndentado(9 + k, gMoveNames[golpe]);
        }
    }
    else
    {
        FichaValorIndentado(9, sTexto_Traco);
    }

    // coluna direita: ALTURA (da Pokédex) sob o ícone + radar + legenda
    if (!ehOvo)
    {
        u16 alt = gPokedexEntries[SpeciesToNationalPokedexNum(especie)].height; // decímetros
        StringCopy(buf, sTexto_Altura);
        ConvertIntToDecimalStringN(buf + StringLength(buf), alt / 10, STR_CONV_MODE_LEFT_ALIGN, 3);
        k = StringLength(buf);
        buf[k] = CHAR_COMMA;
        buf[k + 1] = EOS;
        ConvertIntToDecimalStringN(buf + k + 1, alt % 10, STR_CONV_MODE_LEFT_ALIGN, 1);
        StringAppend(buf, sTexto_Metro);
        width = GetStringWidth(FONT_SMALL, buf, 0);
        AddTextPrinterParameterized3(WIN_DIR, FONT_SMALL, (96 - width) / 2, 52, sCores_Rotulo, TEXT_SKIP_DRAW, buf);
    }

    FichaDesenharRadar(ehOvo ? NULL : mon);
    FichaLegenda();
}
