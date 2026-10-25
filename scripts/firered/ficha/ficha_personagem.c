// FICHA DE PERSONAGEM — tela extra no menu START (projeto de tradução PT-BR).
// Adaptação da ficha de RPG (estilo MHA/BNHA) ao design do FireRed:
//  - janela branca com texto nas cores padrão do jogo (cinza escuro / vermelho);
//  - barra de título escura com texto branco (eco das barras pretas da ficha);
//  - gráfico hexagonal (radar) desenhado pixel a pixel com os 6 atributos do
//    primeiro POKéMON da equipe, escalados pelo maior atributo;
//  - campos preenchidos automaticamente a partir do save.
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
#include "ficha_personagem.h"
#include "constants/songs.h"
#include "constants/flags.h"
#include "constants/items.h"

enum
{
    WIN_ESQ,   // coluna esquerda (18 tiles): título + campos
    WIN_DIR,   // coluna direita (12 tiles): radar + legenda
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
static const u8 sTexto_Titulo[]       = _("FICHA DE PERSONAGEM");
static const u8 sTexto_Insignias[]    = _("INSÍGNIAS: ");
static const u8 sTexto_Nome[]         = _("NOME:");
static const u8 sTexto_Idade[]        = _("IDADE:");
static const u8 sTexto_IdadeVal[]     = _("11 ANOS");
static const u8 sTexto_Sangue[]       = _("SANGUE:");
static const u8 sTexto_Tipo[]         = _("TIPO ");
static const u8 sTexto_Altura[]       = _("ALTURA:");
static const u8 sTexto_AlturaM[]      = _("1,40 m");
static const u8 sTexto_AlturaF[]      = _("1,38 m");
static const u8 sTexto_Afiliacao[]    = _("AFILIAÇÃO:");
static const u8 sTexto_Afil0[]        = _("NOVATO DE PALLET");
static const u8 sTexto_Afil1[]        = _("TREINADOR POKéMON");
static const u8 sTexto_Afil2[]        = _("DESAFIANTE DA LIGA");
static const u8 sTexto_Afil3[]        = _("ELITE DE KANTO");
static const u8 sTexto_Individ[]      = _("INDIVIDUALIDADE:");
static const u8 sTexto_Nenhuma[]      = _("NENHUMA");
static const u8 sTexto_Ovo[]          = _("OVO POKéMON");
static const u8 sTexto_Nv[]           = _(" Nv.");
static const u8 sTexto_Equip[]        = _("EQUIPAMENTO:");
static const u8 sTexto_Nenhum[]       = _("NENHUM");

static const u8 sTexto_SangueA[]  = _("A");
static const u8 sTexto_SangueB[]  = _("B");
static const u8 sTexto_SangueAB[] = _("AB");
static const u8 sTexto_SangueO[]  = _("O");
static const u8 *const sTiposSanguineos[4] = { sTexto_SangueA, sTexto_SangueB, sTexto_SangueAB, sTexto_SangueO };

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
    TEXT_COLOR_RED,         // PODER
    TEXT_COLOR_GREEN,       // TÉCNICA
    TEXT_COLOR_LIGHT_BLUE,  // VELOCIDADE
    TEXT_COLOR_DARK_GRAY,   // CONTROLE
    TEXT_COLOR_LIGHT_RED,   // COOPERAÇÃO
    TEXT_COLOR_BLUE,        // INTELIGÊNCIA
};

#define RADAR_CX 48   // relativo à janela direita (px 144 da tela)
#define RADAR_CY 62
#define RADAR_R  38

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
        break;
    case 3:
        FichaDesenharTudo();
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

static void Task_FichaInput(u8 taskId)
{
    void (*callback)(void);

    if (gTasks[taskId].data[0] == 0 && JOY_NEW(A_BUTTON | B_BUTTON))
    {
        PlaySE(SE_SELECT);
        BeginNormalPaletteFade(PALETTES_ALL, 0, 0, 16, RGB_BLACK);
        gTasks[taskId].data[0] = 1;
    }
    if (gTasks[taskId].data[0] == 1 && !gPaletteFade.active)
    {
        callback = sFicha->savedCallback;
        DestroyTask(taskId);
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

static void FichaDesenharRadar(void)
{
    u16 stats[6] = { 0, 0, 0, 0, 0, 0 };
    u16 raios[6];
    u16 maior = 0;
    s16 vx[6], vy[6];
    s16 x, y;
    u32 k;
    bool8 temMon = FALSE;

    if (CalculatePlayerPartyCount() != 0
     && GetMonData(&gPlayerParty[0], MON_DATA_SPECIES_OR_EGG) != SPECIES_EGG
     && GetMonData(&gPlayerParty[0], MON_DATA_SPECIES) != SPECIES_NONE)
    {
        temMon = TRUE;
        stats[0] = GetMonData(&gPlayerParty[0], MON_DATA_ATK);    // PODER
        stats[1] = GetMonData(&gPlayerParty[0], MON_DATA_SPATK);  // TÉCNICA
        stats[2] = GetMonData(&gPlayerParty[0], MON_DATA_SPEED);  // VELOCIDADE
        stats[3] = GetMonData(&gPlayerParty[0], MON_DATA_DEF);    // CONTROLE
        stats[4] = GetMonData(&gPlayerParty[0], MON_DATA_MAX_HP); // COOPERAÇÃO
        stats[5] = GetMonData(&gPlayerParty[0], MON_DATA_SPDEF);  // INTELIGÊNCIA
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
        u16 y = 110 + (k / 2) * 12;

        FillWindowPixelRect(WIN_DIR, PIXEL_FILL(sCorAtributo[atrib[k]]), x, y + 3, 5, 5);
        AddTextPrinterParameterized3(WIN_DIR, FONT_SMALL, x + 8, y, sCores_Rotulo, TEXT_SKIP_DRAW, rotulos[k]);
    }
}

// ---------- conteúdo ----------

static u8 FichaContarInsignias(void)
{
    u8 n = 0;
    u32 k;

    for (k = 0; k < 8; k++)
    {
        if (FlagGet(FLAG_BADGE01_GET + k))
            n++;
    }
    return n;
}

static void FichaCampo(u16 y, const u8 *rotulo, const u8 *valor)
{
    AddTextPrinterParameterized3(WIN_ESQ, FONT_NORMAL, 6, y, sCores_Rotulo, TEXT_SKIP_DRAW, rotulo);
    if (valor != NULL)
        AddTextPrinterParameterized3(WIN_ESQ, FONT_NORMAL, 12 + GetStringWidth(FONT_NORMAL, rotulo, 0), y, sCores_Valor, TEXT_SKIP_DRAW, valor);
}

static void FichaValorIndentado(u16 y, const u8 *valor)
{
    AddTextPrinterParameterized3(WIN_ESQ, FONT_NORMAL, 14, y, sCores_Valor, TEXT_SKIP_DRAW, valor);
}

static void FichaDesenharTudo(void)
{
    u8 buf[48];
    u8 insignias = FichaContarInsignias();
    u16 soma, especie;
    u32 width;

    FillWindowPixelBuffer(WIN_ESQ, PIXEL_FILL(TEXT_COLOR_WHITE));
    FillWindowPixelBuffer(WIN_DIR, PIXEL_FILL(TEXT_COLOR_WHITE));

    // barra de título (eco das barras pretas da ficha original)
    FillWindowPixelRect(WIN_ESQ, PIXEL_FILL(TEXT_COLOR_DARK_GRAY), 0, 0, 144, 16);
    FillWindowPixelRect(WIN_DIR, PIXEL_FILL(TEXT_COLOR_DARK_GRAY), 0, 0, 96, 16);
    AddTextPrinterParameterized3(WIN_ESQ, FONT_NORMAL, 4, 1, sCores_Titulo, TEXT_SKIP_DRAW, sTexto_Titulo);

    // INSÍGNIAS: n (na barra de título, à direita)
    StringCopy(buf, sTexto_Insignias);
    ConvertIntToDecimalStringN(buf + StringLength(buf), insignias, STR_CONV_MODE_LEFT_ALIGN, 1);
    width = GetStringWidth(FONT_SMALL, buf, 0);
    AddTextPrinterParameterized3(WIN_DIR, FONT_SMALL, 92 - width, 3, sCores_Titulo, TEXT_SKIP_DRAW, buf);

    // coluna esquerda
    FichaCampo(19, sTexto_Nome, gSaveBlock2Ptr->playerName);
    FichaCampo(33, sTexto_Idade, sTexto_IdadeVal);

    soma = gSaveBlock2Ptr->playerTrainerId[0] + gSaveBlock2Ptr->playerTrainerId[1]
         + gSaveBlock2Ptr->playerTrainerId[2] + gSaveBlock2Ptr->playerTrainerId[3];
    StringCopy(buf, sTexto_Tipo);
    StringAppend(buf, sTiposSanguineos[soma % 4]);
    FichaCampo(47, sTexto_Sangue, buf);

    FichaCampo(61, sTexto_Altura, gSaveBlock2Ptr->playerGender == MALE ? sTexto_AlturaM : sTexto_AlturaF);

    FichaCampo(75, sTexto_Afiliacao, NULL);
    if (insignias == 0)
        FichaValorIndentado(89, sTexto_Afil0);
    else if (insignias <= 3)
        FichaValorIndentado(89, sTexto_Afil1);
    else if (insignias <= 7)
        FichaValorIndentado(89, sTexto_Afil2);
    else
        FichaValorIndentado(89, sTexto_Afil3);

    FichaCampo(103, sTexto_Individ, NULL);
    if (CalculatePlayerPartyCount() == 0)
    {
        FichaValorIndentado(117, sTexto_Nenhuma);
    }
    else if (GetMonData(&gPlayerParty[0], MON_DATA_SPECIES_OR_EGG) == SPECIES_EGG)
    {
        FichaValorIndentado(117, sTexto_Ovo);
    }
    else
    {
        especie = GetMonData(&gPlayerParty[0], MON_DATA_SPECIES);
        GetSpeciesName(buf, especie);
        StringAppend(buf, sTexto_Nv);
        ConvertIntToDecimalStringN(buf + StringLength(buf), GetMonData(&gPlayerParty[0], MON_DATA_LEVEL), STR_CONV_MODE_LEFT_ALIGN, 3);
        FichaValorIndentado(117, buf);
    }

    FichaCampo(131, sTexto_Equip, NULL);
    if (gSaveBlock1Ptr->registeredItem != ITEM_NONE)
    {
        CopyItemName(gSaveBlock1Ptr->registeredItem, buf);
        FichaValorIndentado(145, buf);
    }
    else
    {
        FichaValorIndentado(145, sTexto_Nenhum);
    }

    // coluna direita
    FichaDesenharRadar();
    FichaLegenda();
}
