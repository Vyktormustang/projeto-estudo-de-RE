// Encontros estáticos ("como os lendários") para espécies inobtíveis.
//
// Cada espécie cuja família não aparece em nenhuma tabela selvagem, presente,
// troca ou script vira um OBJETO no mapa (sprite = ícone do próprio POKéMON),
// no padrão do MEWTWO da Caverna Cerulean: interagir → grito → batalha única.
//
// Três truques de motor (zero mudança no formato do save):
//  1. ESPÉCIE no template: fica em objUnion.normal.trainerRange_berryTreeId
//     (u16 livre quando trainer_type é TRAINER_TYPE_NONE).
//  2. SPRITE: o objeto usa um graphics id placeholder 32x32; no spawn, o hook
//     troca o frame pelo ícone da espécie (gMonIconTable) e carrega a paleta
//     do ícone no slot PALSLOT_NPC_SPECIAL.
//  3. VISIBILIDADE: o campo flag do objeto recebe FLAG_ESTATICO_BASE+espécie,
//     uma "flag virtual" respondida pela Pokédex (capturou → objeto some;
//     fugiu/desmaiou → continua lá). Nenhuma flag real do save é gasta.

#include "global.h"
#include "event_data.h"
#include "event_object_movement.h"
#include "palette.h"
#include "pokedex.h"
#include "pokemon.h"
#include "pokemon_icon.h"
#include "script_pokemon_util.h"
#include "sprite.h"
#include "string_util.h"
#include "encontros_estaticos.h"
#include "constants/event_objects.h"
#include "constants/items.h"
#include "constants/species.h"

static EWRAM_DATA struct SpriteFrameImage sQuadroIcone[OBJECT_EVENTS_COUNT] = {};

// Nível do encontro em função do total de atributos-base (curva simples).
static u8 NivelEstatico(u16 especie)
{
    const struct SpeciesInfo *si = &gSpeciesInfo[especie];
    u16 bst = si->baseHP + si->baseAttack + si->baseDefense
            + si->baseSpeed + si->baseSpAttack + si->baseSpDefense;

    if (bst >= 580)
        return 70;
    if (bst >= 480)
        return 55;
    if (bst >= 380)
        return 40;
    return 25;
}

static const struct ObjectEventTemplate *TemplateDoUltimoTocado(void)
{
    u32 i;
    u8 localId = gSpecialVar_LastTalked;

    for (i = 0; i < OBJECT_EVENT_TEMPLATES_COUNT; i++)
    {
        const struct ObjectEventTemplate *t = &gSaveBlock1Ptr->objectEventTemplates[i];

        if (t->localId == localId && t->graphicsId == OBJ_EVENT_GFX_MON_ESTATICO
         && t->kind == OBJ_KIND_NORMAL)
            return t;
    }
    return NULL;
}

// special: VAR_RESULT=TRUE e VAR_0x8004/0x8005 = espécie/nível; bufferiza o
// nome da espécie em gStringVar1 (o script usa {STR_VAR_1}).
void EstaticoPrepararEncontro(void)
{
    const struct ObjectEventTemplate *t = TemplateDoUltimoTocado();
    u16 especie;

    if (t == NULL)
    {
        gSpecialVar_Result = FALSE;
        return;
    }
    especie = t->objUnion.normal.trainerRange_berryTreeId;
    if (especie == SPECIES_NONE || especie >= NUM_SPECIES)
    {
        gSpecialVar_Result = FALSE;
        return;
    }
    gSpecialVar_0x8004 = especie;
    gSpecialVar_0x8005 = NivelEstatico(especie);
    GetSpeciesName(gStringVar1, especie);
    gSpecialVar_Result = TRUE;
}

// special: cria o inimigo da batalha (setwildbattle não aceita variáveis).
void EstaticoCriarInimigo(void)
{
    CreateScriptedWildMon(gSpecialVar_0x8004, gSpecialVar_0x8005, ITEM_NONE);
}

// Flag virtual: FLAG_ESTATICO_BASE+espécie == "espécie já capturada na dex".
// Devolve TRUE se idx está na faixa virtual (e então *valor é a resposta).
bool8 EstaticoFlagVirtual(u16 idx, bool8 *valor)
{
    if (idx < FLAG_ESTATICO_BASE || idx >= FLAG_ESTATICO_BASE + NUM_SPECIES)
        return FALSE;
    *valor = GetSetPokedexFlag(SpeciesToNationalPokedexNum(idx - FLAG_ESTATICO_BASE),
                               FLAG_GET_CAUGHT) ? TRUE : FALSE;
    return TRUE;
}

// Troca o frame do sprite pelo ícone da espécie e carrega a paleta do ícone
// no slot especial. A cópia para o VRAM é direta porque objetos inanimados
// nunca disparam a cópia de frame do sistema de animação.
static void ConfigurarSpriteIcone(u16 especie, struct Sprite *sprite, u8 objectEventId)
{
    if (especie == SPECIES_NONE || especie >= NUM_SPECIES)
        return;
    sQuadroIcone[objectEventId].data = gMonIconTable[especie];
    sQuadroIcone[objectEventId].size = 0x200; // 32x32 4bpp (1º quadro do ícone)
    sprite->images = &sQuadroIcone[objectEventId];
    CpuFastCopy(gMonIconTable[especie],
                (u8 *)OBJ_VRAM0 + sprite->oam.tileNum * TILE_SIZE_4BPP, 0x200);
    LoadPalette(gMonIconPalettes[gMonIconPaletteIndices[especie]],
                OBJ_PLTT_ID(PALSLOT_NPC_SPECIAL), PLTT_SIZEOF(16));
    sprite->oam.paletteNum = PALSLOT_NPC_SPECIAL;
}

// Hook do spawn normal (TrySpawnObjectEventTemplate, template em mãos).
void EstaticoConfigurarSprite(const struct ObjectEventTemplate *template,
                              struct Sprite *sprite, u8 objectEventId)
{
    ConfigurarSpriteIcone(template->objUnion.normal.trainerRange_berryTreeId,
                          sprite, objectEventId);
}

// Hook do respawn ao voltar de menu/batalha (sem template: acha pela localId).
void EstaticoReconfigurarSprite(struct ObjectEvent *objectEvent,
                                struct Sprite *sprite, u8 objectEventId)
{
    u32 i;

    for (i = 0; i < OBJECT_EVENT_TEMPLATES_COUNT; i++)
    {
        const struct ObjectEventTemplate *t = &gSaveBlock1Ptr->objectEventTemplates[i];

        if (t->localId == objectEvent->localId
         && t->graphicsId == OBJ_EVENT_GFX_MON_ESTATICO && t->kind == OBJ_KIND_NORMAL)
        {
            ConfigurarSpriteIcone(t->objUnion.normal.trainerRange_berryTreeId,
                                  sprite, objectEventId);
            return;
        }
    }
}
