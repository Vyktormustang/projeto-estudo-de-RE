/* Rotinas auxiliares de batalha do motor_v9 (ARM7TDMI / Thumb).
 *
 * Encadeia sobre o motor_v8 sem tocar saves ou estruturas persistentes,
 * restaurando +378 entradas de subida de nivel em 51 golpes nao-TM divididos
 * em seis familias mecanicas compartilhadas:
 *
 *  1. Modificacao de tipo, terceiro tipo e eletrificacao:
 *     Soak (486), Magic Powder (675), Reflect Type (512), Trick-or-Treat
 *     (563), Forest's Curse (567) e Electrify (578).
 *  2. Trocas, divisoes, inversoes e impulsos compostos de atributos:
 *     Power Trick (379), Power Swap (384), Guard Swap (385), Heart Swap (391),
 *     Speed Swap (638), Guard Split (469), Power Split (470), Topsy-Turvy
 *     (572), Acupressure (367), Venom Drench (595), Toxic Thread (627),
 *     Tar Shot (674), Decorate (684), Spicy Extract (750), No Retreat (673),
 *     Clangorous Soul (682), Fillet Away (760), Magnetic Flux (598), Gear Up
 *     (629), Flower Shield (575) e Rototiller (559).
 *  3. Regeneracao, drenagem por Atk, sacrificio/substituto e purificacao:
 *     Aqua Ring (392), Strength Sap (623), Healing Wish (361), Lunar Dance
 *     (460), Shed Tail (770), Psycho Shift (375), Purify (640), Take Heart
 *     (743), Jungle Healing (710), Lunar Blessing (742) e Dark Void (463).
 *  4. Manipulacao de habilidade em batalha:
 *     Gastro Acid (380), Worry Seed (388), Entrainment (493) e Doodle (759).
 *  5. Controle de ordem/copia, foco critico, dano fixo por HP e Natural Gift:
 *     Copycat (383), After You (494), Quash (510), Final Gambit (514),
 *     Laser Focus (628) e Natural Gift (363).
 *  6. Salas de itens e travas de troca:
 *     Magic Room (477), Octolock (678) e Fairy Lock (583).
 *
 * Seis golpes de subida de nivel (24 linhas) permanecem documentadamente fora
 * de escopo por dependerem de habilidades ou UI ausentes na base Gen 3:
 * Simple Beam (492), Ally Switch (501), Instruct (644), Stuff Cheeks (672),
 * Teatime (677) e Revival Blessing (755).
 */
typedef unsigned char u8;
typedef signed char s8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef int s32;

#define TERRAIN_NONE      0u
#define TERRAIN_ELECTRIC  1u
#define TERRAIN_GRASSY    2u
#define TERRAIN_PSYCHIC   3u
#define TERRAIN_MISTY     4u

#define WEATHER_SNOW_BIT  0x0100u

#define STATUS2_SUBSTITUTE        0x01000000u
#define STATUS2_ESCAPE_PREVENTION 0x04000000u
#define STATUS2_FORESIGHT         0x20000000u

struct V7BattleState {
    u8 stat_rose_mask;
    u8 stat_fell_mask;
    u8 move_started_mask;
    u8 passed_canceler_mask;
    u8 prev_failed_mask;
    u8 last_failed_mask;
    u8 parting_dropped;
    u8 saved_attacker;
    u8 heal_block_turns[4];
    u32 rose_pid[4];
    u32 fell_pid[4];
    u32 failed_pid[4];
    u32 heal_block_pid[4];
    u32 cheer_minus1_pid[4];
};

struct V8BattleState {
    u8 terrain_type;
    u8 terrain_turns;
    u8 trick_room_turns;
    u8 wonder_room_turns;
    u8 gravity_turns;
    u8 endturn_step;
    u8 switchin_hazard_step;
    u8 switchin_bank;
    u8 tailwind_turns[2];
    u8 aurora_veil_turns[2];
    u8 stealth_rock[2];
    u8 toxic_spikes[2];
    u8 sticky_web[2];
    u8 magnet_rise_turns[4];
    u8 saved_target;
    u8 pending_tail_idx;
    u32 switchin_tag;
    u32 magnet_rise_pid[4];
};

struct V9BattleState {
    u16 last_used_move;
    u16 saved_dmg;
    u32 saved_status;
    u8 magic_room_turns;
    u8 fairy_lock_turns;
    u8 electrified_mask;
    u8 fairy_lock_mask;
    u8 wish_pending[2];
    u8 laser_focus_turns[4];
    u8 extra_type[4];
    u8 octolock_src[4];
    u8 shed_tail_sub_hp;
    u8 endturn_step_v9;
    u8 multi_step;
    u8 multi_aux;
    u8 saved_atk;
    u8 saved_tgt;
    u8 op_count;
    u8 op_idx;
    u8 op_bank[12];
    u8 op_changer[12];
    u32 extra_type_tag[4];
    u32 aqua_ring_tag[4];
    u32 tar_shot_tag[4];
    u32 no_retreat_tag[4];
    u32 laser_focus_tag[4];
    u32 octolock_src_tag[4];
    u32 octolock_tgt_tag[4];
};

#define V7_STATE                ((volatile struct V7BattleState *)0x0203FC00u)
#define V8_STATE                ((volatile struct V8BattleState *)0x0203FC60u)
#define V9_STATE ((volatile struct V9BattleState *)0x0203FCA0u)
_Static_assert(__builtin_offsetof(struct V9BattleState, multi_step) == 0x1Cu, "multi_step offset mismatch");
_Static_assert(sizeof(struct V9BattleState) <= 0xC0u, "V9BattleState exceeds 0x0203FCA0..0x0203FD5F");

#define MAIN_IN_BATTLE_BYTE     (*(volatile u8 *)0x03004A45u)
#define BATTLE_MAIN_FUNC        (*(volatile u32 *)0x03005318u)

#define BATTLE_TYPE_FLAGS       (*(volatile u32 *)0x02020374u)
#define ACTIVE_BATTLER          (*(volatile u8 *)0x020213ECu)
#define CONTROLLER_EXEC_FLAGS   (*(volatile u32 *)0x020213F0u)
#define BATTLERS_COUNT          (*(volatile u8 *)0x020213F4u)
#define PARTY_INDEXES           ((volatile u16 *)0x020213F8u)
#define ACTIONS_BY_TURN         ((volatile u8 *)0x02021404u)
#define BATTLER_BY_TURN         ((volatile u8 *)0x02021408u)
#define CURR_TURN_ACTION_NUM    (*(volatile u8 *)0x0202140Cu)
#define CURR_ACTION_FUNC_ID     (*(volatile u8 *)0x0202140Du)
#define BATTLE_MONS             ((volatile u8 *)0x02021410u)
#define CURRENT_MOVE            (*(volatile u16 *)0x02021586u)
#define BATTLE_MOVE_DMG         (*(volatile s32 *)0x0202158Cu)
#define ATTACKER                (*(volatile u8 *)0x020215A8u)
#define TARGET                  (*(volatile u8 *)0x020215A9u)
#define FAINTED_BATTLER         (*(volatile u8 *)0x020215AAu)
#define EFFECT_BATTLER          (*(volatile u8 *)0x020215ABu)
#define ABSENT_BATTLERS         (*(volatile u8 *)0x020215ADu)
#define CRIT_MULTIPLIER         (*(volatile u8 *)0x020215AEu)
#define CURR_INSTR              (*(const u8 *volatile *)0x020215B0u)
#define MOVE_RESULT_FLAGS       (*(volatile u8 *)0x02021608u)
#define HIT_MARKER              (*(volatile u32 *)0x0202160Cu)
#define SIDE_STATUSES           ((volatile u16 *)0x0202161Cu)
#define STATUSES3               ((volatile u32 *)0x02021638u)
#define DISABLE_STRUCTS_REAL    ((volatile u8 *)0x02021648u)
#define MOVE_EFFECT_BYTE        (*(volatile u8 *)0x020216C3u)
#define MULTISTRING_CHOOSER     (*(volatile u8 *)0x020216C5u)
#define BATTLE_OUTCOME          (*(volatile u8 *)0x020216C8u)
#define PROTECT_STRUCTS         ((volatile u8 *)0x020216CCu)
#define BATTLE_WEATHER          (*(volatile u16 *)0x0202175Cu)
#define WEATHER_DURATION        (*(volatile u8 *)0x02021788u)
#define DYNAMIC_POWER           (*(volatile u16 *)0x02021792u)
#define SCRIPTING_BATTLER       (*(volatile u8 *)0x0202181Fu)
#define STAT_BUFF_ADDR          (*(volatile u8 *)0x02021822u)
#define ANIM_ARG1_BYTE          (*(volatile u8 *)0x02021823u)
#define BATTLE_STRUCT_PTR       (*(volatile u8 *volatile *)0x0202182Cu)
#define BATTLE_RESOURCES_PTR    (*(volatile u8 *volatile *)0x02021838u)

#define ENEMY_PARTY_BASE        ((u8 *)0x0203A734u)
#define PLAYER_PARTY_BASE       ((u8 *)0x0203A98Cu)

#define MOVE_TABLE              ((const u8 *)0x09000000u)
#define SCRIPT_TABLE            ((const u8 *const *)0x0900A000u)
#define NEW_ITEMS_TABLE         ((const u8 *)0x08E11000u)
#define TYPE_EFFECT_TABLE       ((const u8 *)0x08200C18u)
#define STAT_STAGE_RATIOS       ((const u8 *)0x086BC7BCu)

/* Sub-scripts do motor_v7 / motor_v8 reutilizados */
#define BS_HEAL_BLOCK_CANCEL    ((const u8 *)0x090BF000u)
#define BS_V8_ENDTURN_MSGS      ((const u8 *)0x090C1030u)
#define BS_V8_ENDTURN_GRASSY    ((const u8 *)0x090C1070u)

/* Sub-scripts fixos gravados em 0x090C6000..0x090C633F por motor_v9.py */
#define BS_V9_ENDTURN_AQUA_RING ((const u8 *)0x090C6000u)
#define BS_V9_ENDTURN_OCTOLOCK  ((const u8 *)0x090C6020u)
#define BS_V9_ENDTURN_MROOM     ((const u8 *)0x090C60A0u)
#define BS_V9_SWITCHIN_HWISH    ((const u8 *)0x090C60B0u)
#define BS_V9_SWITCHIN_LDANCE   ((const u8 *)0x090C60D0u)
#define BS_V9_WORRY_SEED_WAKE   ((const u8 *)0x090C60F0u)
#define BS_V9_OCTOLOCK_SET      ((const u8 *)0x090C6110u)
#define BS_V9_TOXIC_THREAD_PSN  ((const u8 *)0x090C6130u)
#define BS_V9_CLEANSE_CURE_STEP ((const u8 *)0x090C6150u)
#define BS_V9_CLEANSE_HEAL_STEP ((const u8 *)0x090C6170u)
#define BS_V9_PSHIFT_INFLICT    ((const u8 *)0x090C6190u)
#define BS_V9_PSHIFT_SELF_CURE  ((const u8 *)0x090C61B0u)
#define BS_V9_MSG_TAILS         ((const u8 *)0x090C61D0u)

#define BS_HIT_CALC_START       ((const u8 *)0x081853D8u)
#define BS_MOVE_END             ((const u8 *)0x081853F6u)
#define BS_MISS_AFTER_PP        ((const u8 *)0x08185408u)
#define BS_BUT_IT_FAILED        ((const u8 *)0x0818689Au)

/* Encadeamento sobre motor_v8 / motor_v7 / funcoes nativas */
#define PREV_BATTLE_INIT_V8     ((void (*)(void))0x090C3001u)
#define PREV_TURN_START_V8      ((void (*)(void))0x090C3009u)
#define PREV_ATTACKCANCELER_V8  ((void (*)(void))0x090C3021u)
#define PREV_CRITCALC_V7        ((void (*)(void))0x090C0019u)
#define PREV_DAMAGE_V8          ((void (*)(void))0x090C3031u)
#define PREV_TYPECALC_V8        ((void (*)(void))0x090C3039u)
#define PREV_SWITCHINEFFECTS_V8 ((void (*)(void))0x090C3059u)

#define ENTRY_ENDTURN_V9_THUMB  0x090C9011u
#define ORIG_BATTLE_TURN_PASSED ((void (*)(void))0x08053221u)
#define FN_TURN_VALUES_CLEANUP  ((void (*)(u8))0x080543A5u)
#define FN_DO_FIELD_ENDTURN     ((u8 (*)(void))0x0806D069u)

#define FN_GET_SIDE             ((u8 (*)(u8))0x08024685u)
#define FN_EMIT_SET_MON_DATA    ((void (*)(u8, u8, u8, u8, const void *))0x08049DF5u)
#define FN_GET_SCRIPT_BANK      ((u8 (*)(u8))0x0806C535u)
#define FN_MARK_BUFFER_EXEC     ((void (*)(u8))0x0806C8BDu)
#define FN_BS_PUSH              ((void (*)(const u8 *))0x0806CB2Du)
#define FN_ABILITY_EFFECTS      ((u8 (*)(u8, u8, u8, u8, u16))0x0806F4DDu)
#define FN_GET_MOVE_TARGET      ((u8 (*)(u16, u8))0x08071DE1u)
#define FN_SET_MON_DATA         ((void (*)(void *, u32, const void *))0x0810AF79u)
#define FN_RANDOM               ((u16 (*)(void))0x0812E9C5u)
#define FN_UDIV32               ((u32 (*)(u32, u32))0x08172B3Du)
#define FN_UMOD32               ((u32 (*)(u32, u32))0x08172B4Du)

/* Tabela oficial (Gen 6-7) de Natural Gift para Berries 133..175: {tipo, BP} */
static const u8 NATURAL_GIFT_TABLE[43][2] = {
    {10u,  80u}, {11u,  80u}, {13u,  80u}, {12u,  80u}, {15u,  80u},
    { 1u,  80u}, { 3u,  80u}, { 4u,  80u}, { 2u,  80u}, {14u,  80u},
    { 6u,  80u}, { 5u,  80u}, { 7u,  80u}, {16u,  80u}, {17u,  80u},
    { 8u,  80u}, {10u,  90u}, {11u,  90u}, {13u,  90u}, {12u,  90u},
    {15u,  90u}, { 1u,  90u}, { 3u,  90u}, { 4u,  90u}, { 2u,  90u},
    {14u,  90u}, { 6u,  90u}, { 5u,  90u}, { 7u,  90u}, {16u,  90u},
    {17u,  90u}, { 8u,  90u}, {10u, 100u}, {11u, 100u}, {13u, 100u},
    {12u, 100u}, {15u, 100u}, { 1u, 100u}, { 3u, 100u}, { 4u, 100u},
    { 2u, 100u}, {14u, 100u}, { 6u, 100u},
};

static u32 read_u32_unaligned(const u8 *p)
{
    return (u32)p[0] | ((u32)p[1] << 8) | ((u32)p[2] << 16) | ((u32)p[3] << 24);
}

static u32 mon_tag(u8 bank)
{
    bank &= 3u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    u32 pid = *(volatile u32 *)(m + 0x4Cu);
    u32 slot = PARTY_INDEXES[bank];
    return 0x80000000u | ((slot & 7u) << 28) | (pid & 0x0FFFFFFFu);
}

static u8 is_bank_alive(u8 bank)
{
    bank &= 3u;
    if (bank >= BATTLERS_COUNT || (ABSENT_BATTLERS & (1u << bank)) != 0u)
        return 0u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    return (*(volatile u16 *)(m + 0x2Au) > 0u) ? 1u : 0u;
}

static u8 has_substitute(u8 bank)
{
    volatile u8 *m = BATTLE_MONS + 0x5Cu * (bank & 3u);
    return ((*(volatile u32 *)(m + 0x54u) & STATUS2_SUBSTITUTE) != 0u) ? 1u : 0u;
}

static u8 is_heal_blocked(u8 bank)
{
    bank &= 3u;
    if (V7_STATE->heal_block_turns[bank] == 0u)
        return 0u;
    if (V7_STATE->heal_block_pid[bank] != mon_tag(bank)) {
        V7_STATE->heal_block_turns[bank] = 0u;
        return 0u;
    }
    return 1u;
}

static u8 get_extra_type(u8 bank)
{
    bank &= 3u;
    u8 et = V9_STATE->extra_type[bank];
    if (et == 0u)
        return 0u;
    if (V9_STATE->extra_type_tag[bank] != mon_tag(bank)) {
        V9_STATE->extra_type[bank] = 0u;
        return 0u;
    }
    return et;
}

static u8 has_type_v9(u8 bank, u8 typ)
{
    bank &= 3u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    if (m[0x22u] == typ || m[0x23u] == typ)
        return 1u;
    return (get_extra_type(bank) == typ) ? 1u : 0u;
}

static u8 has_aqua_ring(u8 bank)
{
    bank &= 3u;
    if (V9_STATE->aqua_ring_tag[bank] == 0u)
        return 0u;
    if (V9_STATE->aqua_ring_tag[bank] != mon_tag(bank)) {
        V9_STATE->aqua_ring_tag[bank] = 0u;
        return 0u;
    }
    return 1u;
}

static u8 has_tar_shot(u8 bank)
{
    bank &= 3u;
    if (V9_STATE->tar_shot_tag[bank] == 0u)
        return 0u;
    if (V9_STATE->tar_shot_tag[bank] != mon_tag(bank)) {
        V9_STATE->tar_shot_tag[bank] = 0u;
        return 0u;
    }
    return 1u;
}

static u8 has_no_retreat(u8 bank)
{
    bank &= 3u;
    if (V9_STATE->no_retreat_tag[bank] == 0u)
        return 0u;
    if (V9_STATE->no_retreat_tag[bank] != mon_tag(bank)) {
        V9_STATE->no_retreat_tag[bank] = 0u;
        return 0u;
    }
    return 1u;
}

static u8 has_octolock(u8 bank)
{
    bank &= 3u;
    if (V9_STATE->octolock_tgt_tag[bank] == 0u)
        return 0u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    u8 src = V9_STATE->octolock_src[bank] & 3u;
    if ((*(volatile u32 *)(m + 0x54u) & STATUS2_ESCAPE_PREVENTION) == 0u
        || V9_STATE->octolock_tgt_tag[bank] != mon_tag(bank)
        || !is_bank_alive(src)
        || V9_STATE->octolock_src_tag[bank] != mon_tag(src)) {
        V9_STATE->octolock_tgt_tag[bank] = 0u;
        return 0u;
    }
    return 1u;
}

static u8 is_magnet_risen_v9(u8 bank)
{
    bank &= 3u;
    if (V8_STATE->magnet_rise_turns[bank] == 0u)
        return 0u;
    if (V8_STATE->magnet_rise_pid[bank] != mon_tag(bank) || V8_STATE->gravity_turns > 0u)
        return 0u;
    return 1u;
}

static u8 is_grounded_v9(u8 bank)
{
    bank &= 3u;
    if ((STATUSES3[bank] & 0x00000008u) != 0u)
        return 0u;
    if (V8_STATE->gravity_turns > 0u || (STATUSES3[bank] & 0x00002000u) != 0u)
        return 1u;
    if (is_magnet_risen_v9(bank))
        return 0u;
    if (has_type_v9(bank, 2u))
        return 0u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    if (*(volatile u16 *)(m + 0x20u) == 26u)
        return 0u;
    return 1u;
}

static void *party_mon_ptr(u8 bank)
{
    u16 slot = PARTY_INDEXES[bank & 3u];
    if (slot > 5u)
        slot = 0u;
    u8 *base = (FN_GET_SIDE(bank & 3u) == 0u) ? PLAYER_PARTY_BASE : ENEMY_PARTY_BASE;
    return (void *)(base + 100u * slot);
}

static void emit_status_sync(u8 bank)
{
    bank &= 3u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    u32 st = *(volatile u32 *)(m + 0x50u);
    FN_SET_MON_DATA(party_mon_ptr(bank), 0x37u, &st);
    ACTIVE_BATTLER = bank;
    FN_EMIT_SET_MON_DATA(0u, 0x28u, 0u, 4u, (const void *)(m + 0x50u));
    FN_MARK_BUFFER_EXEC(bank);
}

static void start_endturn_script(const u8 *bs_ptr)
{
    CURR_INSTR = bs_ptr;
    volatile u8 *cb_stack = *(volatile u8 **)(BATTLE_RESOURCES_PTR + 0x0Cu);
    u8 depth = cb_stack[0x20u];
    cb_stack[0x20u] = (u8)(depth + 1u);
    ((volatile u32 *)cb_stack)[depth] = BATTLE_MAIN_FUNC;
    CURR_ACTION_FUNC_ID = 0u;
    BATTLE_MAIN_FUNC = 0x08054B91u;
}

/* ========================= Ciclo de vida e Item ========================= */

void hook_battle_init_v9(void)
{
    volatile u8 *p = (volatile u8 *)V9_STATE;
    for (u32 i = 0u; i < sizeof(struct V9BattleState); ++i)
        p[i] = 0u;
    PREV_BATTLE_INIT_V8();
}

void hook_turn_start_v9(void)
{
    V9_STATE->electrified_mask = 0u;
    V9_STATE->endturn_step_v9 = 0u;

    for (u32 b = 0u; b < 4u; ++b) {
        if (V9_STATE->laser_focus_turns[b] > 0u) {
            if (!is_bank_alive((u8)b) || V9_STATE->laser_focus_tag[b] != mon_tag((u8)b))
                V9_STATE->laser_focus_turns[b] = 0u;
            else
                V9_STATE->laser_focus_turns[b]--;
        }
    }

    if (V9_STATE->fairy_lock_turns > 0u) {
        V9_STATE->fairy_lock_turns--;
        if (V9_STATE->fairy_lock_turns == 0u) {
            u8 mask = V9_STATE->fairy_lock_mask;
            V9_STATE->fairy_lock_mask = 0u;
            for (u32 b = 0u; b < 4u; ++b) {
                if ((mask & (1u << b)) != 0u && !has_no_retreat((u8)b) && !has_octolock((u8)b)) {
                    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
                    *(volatile u32 *)(m + 0x54u) &= ~STATUS2_ESCAPE_PREVENTION;
                }
            }
        }
    }

    PREV_TURN_START_V8();
}

u8 hook_get_hold_effect_v9(u16 item_id)
{
    if ((MAIN_IN_BATTLE_BYTE & 0x02u) != 0u
        && BATTLE_OUTCOME == 0u
        && V9_STATE->magic_room_turns > 0u) {
        return 0u;
    }
    if (item_id > 0x025Cu)
        return 0u;
    return NEW_ITEMS_TABLE[44u * (u32)item_id + 0x12u];
}

/* ==================== Fim de Turno encadeado (v8 + v9) ================== */

static u8 has_any_endturn_v8_v9(void)
{
    if ((BATTLE_WEATHER & WEATHER_SNOW_BIT) != 0u)
        return 1u;
    if (V8_STATE->terrain_turns > 0u
        || V8_STATE->trick_room_turns > 0u
        || V8_STATE->wonder_room_turns > 0u
        || V8_STATE->gravity_turns > 0u
        || V8_STATE->tailwind_turns[0] > 0u
        || V8_STATE->tailwind_turns[1] > 0u
        || V8_STATE->aurora_veil_turns[0] > 0u
        || V8_STATE->aurora_veil_turns[1] > 0u
        || V9_STATE->magic_room_turns > 0u) {
        return 1u;
    }
    for (u32 b = 0u; b < 4u; ++b) {
        if (V8_STATE->magnet_rise_turns[b] > 0u
            || V9_STATE->aqua_ring_tag[b] != 0u
            || V9_STATE->octolock_tgt_tag[b] != 0u) {
            return 1u;
        }
    }
    return 0u;
}

void hook_endturn_v9(void)
{
    if (!has_any_endturn_v8_v9()) {
        V8_STATE->endturn_step = 0u;
        V9_STATE->endturn_step_v9 = 0u;
        BATTLE_MAIN_FUNC = 0x08053221u;
        ORIG_BATTLE_TURN_PASSED();
        return;
    }

    if (CONTROLLER_EXEC_FLAGS != 0u)
        return;

    if ((V8_STATE->terrain_type == TERRAIN_ELECTRIC || V8_STATE->terrain_type == TERRAIN_MISTY)
        && V8_STATE->terrain_turns > 0u) {
        u32 cnt = BATTLERS_COUNT;
        if (cnt > 4u)
            cnt = 4u;
        for (u32 b = 0u; b < cnt; ++b) {
            if ((STATUSES3[b] & 0x0800u) != 0u && is_grounded_v9((u8)b))
                STATUSES3[b] &= ~0x1800u;
        }
    }

    if (BATTLE_OUTCOME != 0u) {
        V8_STATE->endturn_step = 0u;
        V9_STATE->endturn_step_v9 = 0u;
        V9_STATE->magic_room_turns = 0u;
        BATTLE_MAIN_FUNC = 0x08053221u;
        ORIG_BATTLE_TURN_PASSED();
        return;
    }

    if (BATTLE_STRUCT_PTR[3] < 10u) {
        FN_TURN_VALUES_CLEANUP(1u);
        BATTLE_MAIN_FUNC = 0x08053221u;
        u8 fld_busy = FN_DO_FIELD_ENDTURN();
        if (fld_busy != 0u) {
            if (BATTLE_MAIN_FUNC == 0x08054B91u) {
                volatile u8 *cb_stack = *(volatile u8 **)(BATTLE_RESOURCES_PTR + 0x0Cu);
                u8 depth = cb_stack[0x20u];
                if (depth > 0u)
                    ((volatile u32 *)cb_stack)[depth - 1u] = ENTRY_ENDTURN_V9_THUMB;
            } else {
                BATTLE_MAIN_FUNC = ENTRY_ENDTURN_V9_THUMB;
            }
            return;
        }
        BATTLE_MAIN_FUNC = ENTRY_ENDTURN_V9_THUMB;
    }

    /* Passos 0..16: identicos ao motor_v8 */
    while (V8_STATE->endturn_step < 17u) {
        u8 step = V8_STATE->endturn_step++;

        if (step < 4u) {
            if (V8_STATE->terrain_type == TERRAIN_GRASSY
                && V8_STATE->terrain_turns > 0u
                && is_bank_alive(step)
                && is_grounded_v9(step)
                && !is_heal_blocked(step)) {
                volatile u8 *m = BATTLE_MONS + 0x5Cu * step;
                u16 hp = *(volatile u16 *)(m + 0x2Au);
                u16 max_hp = *(volatile u16 *)(m + 0x2Eu);
                if (hp < max_hp) {
                    s32 heal = (s32)(max_hp >> 4);
                    if (heal < 1)
                        heal = 1;
                    SCRIPTING_BATTLER = step;
                    BATTLE_MOVE_DMG = -heal;
                    MOVE_RESULT_FLAGS &= (u8)~0x29u;
                    start_endturn_script(BS_V8_ENDTURN_GRASSY);
                    return;
                }
            }
            continue;
        }
        if (step == 4u) {
            if ((BATTLE_WEATHER & WEATHER_SNOW_BIT) != 0u && WEATHER_DURATION > 0u) {
                WEATHER_DURATION--;
                if (WEATHER_DURATION == 0u) {
                    BATTLE_WEATHER &= (u16)~WEATHER_SNOW_BIT;
                    start_endturn_script(BS_V8_ENDTURN_MSGS + 8u * 0u);
                    return;
                }
            }
            continue;
        }
        if (step == 5u || step == 6u) {
            u8 side = (u8)(step - 5u);
            if (V8_STATE->tailwind_turns[side] > 0u) {
                V8_STATE->tailwind_turns[side]--;
                if (V8_STATE->tailwind_turns[side] == 0u) {
                    start_endturn_script(BS_V8_ENDTURN_MSGS + 8u * 1u);
                    return;
                }
            }
            continue;
        }
        if (step == 7u || step == 8u) {
            u8 side = (u8)(step - 7u);
            if (V8_STATE->aurora_veil_turns[side] > 0u) {
                V8_STATE->aurora_veil_turns[side]--;
                if (V8_STATE->aurora_veil_turns[side] == 0u) {
                    start_endturn_script(BS_V8_ENDTURN_MSGS + 8u * 2u);
                    return;
                }
            }
            continue;
        }
        if (step == 9u) {
            if (V8_STATE->terrain_turns > 0u) {
                V8_STATE->terrain_turns--;
                if (V8_STATE->terrain_turns == 0u) {
                    V8_STATE->terrain_type = TERRAIN_NONE;
                    start_endturn_script(BS_V8_ENDTURN_MSGS + 8u * 3u);
                    return;
                }
            }
            continue;
        }
        if (step == 10u) {
            if (V8_STATE->gravity_turns > 0u) {
                V8_STATE->gravity_turns--;
                if (V8_STATE->gravity_turns == 0u) {
                    start_endturn_script(BS_V8_ENDTURN_MSGS + 8u * 4u);
                    return;
                }
            }
            continue;
        }
        if (step == 11u) {
            if (V8_STATE->trick_room_turns > 0u) {
                V8_STATE->trick_room_turns--;
                if (V8_STATE->trick_room_turns == 0u) {
                    start_endturn_script(BS_V8_ENDTURN_MSGS + 8u * 5u);
                    return;
                }
            }
            continue;
        }
        if (step == 12u) {
            if (V8_STATE->wonder_room_turns > 0u) {
                V8_STATE->wonder_room_turns--;
                if (V8_STATE->wonder_room_turns == 0u) {
                    start_endturn_script(BS_V8_ENDTURN_MSGS + 8u * 6u);
                    return;
                }
            }
            continue;
        }
        if (step >= 13u && step <= 16u) {
            u8 b = (u8)(step - 13u);
            if (b < BATTLERS_COUNT && V8_STATE->magnet_rise_turns[b] > 0u) {
                if (V8_STATE->magnet_rise_pid[b] != mon_tag(b)) {
                    V8_STATE->magnet_rise_turns[b] = 0u;
                } else {
                    V8_STATE->magnet_rise_turns[b]--;
                    if (V8_STATE->magnet_rise_turns[b] == 0u && is_bank_alive(b)) {
                        SCRIPTING_BATTLER = b;
                        start_endturn_script(BS_V8_ENDTURN_MSGS + 8u * 7u);
                        return;
                    }
                }
            }
            continue;
        }
    }

    /* Passos v9 (0..8): Aqua Ring (0..3), Octolock (4..7) e Magic Room (8) */
    while (V9_STATE->endturn_step_v9 < 9u) {
        u8 step = V9_STATE->endturn_step_v9++;

        if (step < 4u) {
            if (is_bank_alive(step) && has_aqua_ring(step) && !is_heal_blocked(step)) {
                volatile u8 *m = BATTLE_MONS + 0x5Cu * step;
                u16 hp = *(volatile u16 *)(m + 0x2Au);
                u16 max_hp = *(volatile u16 *)(m + 0x2Eu);
                if (hp < max_hp) {
                    s32 heal = (s32)(max_hp >> 4);
                    if (heal < 1)
                        heal = 1;
                    SCRIPTING_BATTLER = step;
                    BATTLE_MOVE_DMG = -heal;
                    MOVE_RESULT_FLAGS &= (u8)~0x29u;
                    start_endturn_script(BS_V9_ENDTURN_AQUA_RING);
                    return;
                }
            }
            continue;
        }
        if (step >= 4u && step < 8u) {
            u8 b = (u8)(step - 4u);
            if (is_bank_alive(b) && has_octolock(b)) {
                volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
                if (m[0x1Au] > 0u || m[0x1Du] > 0u) {
                    V9_STATE->saved_tgt = TARGET;
                    V9_STATE->saved_atk = ATTACKER;
                    ATTACKER = V9_STATE->octolock_src[b] & 3u;
                    TARGET = b;
                    SCRIPTING_BATTLER = b;
                    start_endturn_script(BS_V9_ENDTURN_OCTOLOCK);
                    return;
                }
            }
            continue;
        }
        if (step == 8u) {
            if (V9_STATE->magic_room_turns > 0u) {
                V9_STATE->magic_room_turns--;
                if (V9_STATE->magic_room_turns == 0u) {
                    start_endturn_script(BS_V9_ENDTURN_MROOM);
                    return;
                }
            }
            continue;
        }
    }

    V8_STATE->endturn_step = 0u;
    V9_STATE->endturn_step_v9 = 0u;
    BATTLE_MAIN_FUNC = 0x08053221u;
    ORIG_BATTLE_TURN_PASSED();
}

void hook_restore_tgt_v9(void)
{
    TARGET = V9_STATE->saved_tgt;
    ATTACKER = V9_STATE->saved_atk;
}

/* ================== Comandos Relocados em CMD_TABLE_V9 ================== */

static u8 is_v9_heal_blocked_move(u16 move, u8 atk)
{
    if (!is_heal_blocked(atk))
        return 0u;
    if (move == 392u || move == 623u || move == 640u)
        return 1u;
    if (move == 710u || move == 742u) {
        volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
        if (*(volatile u32 *)(a + 0x50u) != 0u)
            return 0u;
        if ((BATTLE_TYPE_FLAGS & 0x01u) != 0u) {
            u8 ally = (u8)(atk ^ 2u);
            if (is_bank_alive(ally)) {
                volatile u8 *al = BATTLE_MONS + 0x5Cu * ally;
                if (*(volatile u32 *)(al + 0x50u) != 0u)
                    return 0u;
                if (!is_heal_blocked(ally)
                    && *(volatile u16 *)(al + 0x2Au) < *(volatile u16 *)(al + 0x2Eu)) {
                    return 0u;
                }
            }
        }
        return 1u;
    }
    return 0u;
}

void hook_attackcanceler_v9(void)
{
    const u8 *before = CURR_INSTR;
    PREV_ATTACKCANCELER_V8();
    if (CURR_INSTR != before + 1)
        return;

    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;

    if (is_v9_heal_blocked_move(move, atk)) {
        V7_STATE->passed_canceler_mask &= (u8)~(1u << atk);
        CURR_INSTR = BS_HEAL_BLOCK_CANCEL;
        return;
    }

    if (move != 0u && move != 165u && move != 383u)
        V9_STATE->last_used_move = move;
}

void hook_critcalc_v9(void)
{
    PREV_CRITCALC_V7();

    u8 atk = ATTACKER & 3u;
    if (V9_STATE->laser_focus_turns[atk] > 0u
        && V9_STATE->laser_focus_tag[atk] == mon_tag(atk)) {
        u8 tgt = TARGET & 3u;
        volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
        u16 t_ab = *(volatile u16 *)(t + 0x20u);
        if (t_ab != 4u && t_ab != 75u && (STATUSES3[tgt] & 0x00008000u) == 0u)
            CRIT_MULTIPLIER = 2u;
    }
}

void hook_damage_v9(void)
{
    u8 atk = ATTACKER & 3u;
    u16 move = CURRENT_MOVE;
    volatile u8 *bstruct = BATTLE_STRUCT_PTR;

    if ((V9_STATE->electrified_mask & (1u << atk)) != 0u)
        bstruct[0x13u] = (u8)(0x40u | 13u);

    PREV_DAMAGE_V8();

    if (BATTLE_MOVE_DMG > 0 && move > 0u && move < 822u) {
        u8 et = get_extra_type(atk);
        if (et != 0u) {
            u8 mtype = (bstruct[0x13u] & 0x40u)
                ? (bstruct[0x13u] & 0x3Fu)
                : MOVE_TABLE[12u * move + 2u];
            volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
            if (et == mtype && a[0x22u] != mtype && a[0x23u] != mtype) {
                u32 dmg = ((u32)BATTLE_MOVE_DMG * 3u) >> 1;
                if (dmg < 1u)
                    dmg = 1u;
                BATTLE_MOVE_DMG = (s32)dmg;
            }
        }
    }
}

static u8 lookup_type_chart(u8 atk_type, u8 def_type, u8 foresight)
{
    const u8 *p = TYPE_EFFECT_TABLE;
    u8 after_fe = 0u;
    while (p[0] != 0xFFu) {
        if (p[0] == 0xFEu) {
            after_fe = 1u;
            p += 3;
            continue;
        }
        if (p[0] == atk_type && p[1] == def_type) {
            if (after_fe && foresight && p[2] == 0u)
                return 10u;
            return p[2];
        }
        p += 3;
    }
    return 10u;
}

static s32 type_step_score(u8 atk_type, u8 def_type, u8 foresight, u8 grounded_override)
{
    if (atk_type == 4u && def_type == 2u && grounded_override)
        return 0;
    u8 rel = lookup_type_chart(atk_type, def_type, foresight);
    if (rel == 20u)
        return 1;
    if (rel == 5u)
        return -1;
    return 0;
}

void hook_typecalc_v9(void)
{
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    u16 move = CURRENT_MOVE;
    volatile u8 *bstruct = BATTLE_STRUCT_PTR;

    if ((V9_STATE->electrified_mask & (1u << atk)) != 0u)
        bstruct[0x13u] = (u8)(0x40u | 13u);

    PREV_TYPECALC_V8();

    if ((MOVE_RESULT_FLAGS & 0x29u) != 0u)
        return;

    u8 mtype = (bstruct[0x13u] & 0x40u)
        ? (bstruct[0x13u] & 0x3Fu)
        : ((move < 822u) ? MOVE_TABLE[12u * move + 2u] : 0u);

    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    u8 et = get_extra_type(tgt);
    u8 tar = (mtype == 10u && has_tar_shot(tgt)) ? 1u : 0u;
    if ((et == 0u || et == t[0x22u] || et == t[0x23u]) && !tar)
        return;

    u8 foresight = ((*(volatile u32 *)(t + 0x54u) & STATUS2_FORESIGHT) != 0u) ? 1u : 0u;
    if (et != 0u && et != t[0x22u] && et != t[0x23u]) {
        u8 rel = lookup_type_chart(mtype, et, foresight);
        if (rel == 0u) {
            BATTLE_MOVE_DMG = 0;
            MOVE_RESULT_FLAGS = (u8)((MOVE_RESULT_FLAGS & ~0x06u) | 0x08u);
            return;
        }
        if (rel == 20u) {
            s32 dmg = BATTLE_MOVE_DMG << 1;
            if (dmg < 1)
                dmg = 1;
            BATTLE_MOVE_DMG = dmg;
        } else if (rel == 5u) {
            s32 dmg = BATTLE_MOVE_DMG >> 1;
            if (dmg < 1)
                dmg = 1;
            BATTLE_MOVE_DMG = dmg;
        }
    }

    if (tar) {
        s32 dmg = BATTLE_MOVE_DMG << 1;
        if (dmg < 1)
            dmg = 1;
        BATTLE_MOVE_DMG = dmg;
    }

    u8 g_over = (V8_STATE->gravity_turns > 0u || (STATUSES3[tgt] & 0x00002000u) != 0u) ? 1u : 0u;
    s32 net = type_step_score(mtype, t[0x22u], foresight, g_over);
    if (t[0x23u] != t[0x22u])
        net += type_step_score(mtype, t[0x23u], foresight, g_over);
    if (et != 0u && et != t[0x22u] && et != t[0x23u])
        net += type_step_score(mtype, et, foresight, g_over);
    if (tar)
        net += 1;

    MOVE_RESULT_FLAGS &= (u8)~0x06u;
    if (net > 0)
        MOVE_RESULT_FLAGS |= 0x02u;
    else if (net < 0)
        MOVE_RESULT_FLAGS |= 0x04u;
}

/* ============= Switch-in: Healing Wish & Lunar Dance (0x52) ============= */

static u8 max_pp_for_slot(volatile u8 *m, u32 slot)
{
    u16 mv = *(volatile u16 *)(m + 0x0Cu + 2u * slot);
    if (mv == 0u || mv >= 822u)
        return 0u;
    u32 base_pp = MOVE_TABLE[12u * mv + 4u];
    u32 bonus = ((u32)m[0x24u] >> (2u * slot)) & 3u;
    return (u8)(base_pp + FN_UDIV32(base_pp * bonus, 5u));
}

void hook_switchineffects_v9(void)
{
    const u8 *instr = CURR_INSTR;
    u8 b = FN_GET_SCRIPT_BANK(instr[1]) & 3u;

    PREV_SWITCHINEFFECTS_V8();
    if (CURR_INSTR != instr + 2)
        return;

    if (!is_bank_alive(b))
        return;

    u8 side = FN_GET_SIDE(b);
    u8 wish = V9_STATE->wish_pending[side];
    if (wish == 0u)
        return;

    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
    u16 hp = *(volatile u16 *)(m + 0x2Au);
    u16 max_hp = *(volatile u16 *)(m + 0x2Eu);
    u32 st1 = *(volatile u32 *)(m + 0x50u);
    u8 need_pp = 0u;
    if (wish == 2u) {
        for (u32 i = 0u; i < 4u; ++i) {
            u8 mpp = max_pp_for_slot(m, i);
            if (mpp > 0u && m[0x25u + i] < mpp)
                need_pp = 1u;
        }
    }

    if (hp >= max_hp && st1 == 0u && !need_pp)
        return;

    V9_STATE->wish_pending[side] = 0u;
    void *pmon = party_mon_ptr(b);
    if (st1 != 0u) {
        u32 zero = 0u;
        *(volatile u32 *)(m + 0x50u) = 0u;
        FN_SET_MON_DATA(pmon, 0x37u, &zero);
    }
    if (wish == 2u) {
        for (u32 i = 0u; i < 4u; ++i) {
            u8 mpp = max_pp_for_slot(m, i);
            if (mpp > 0u) {
                m[0x25u + i] = mpp;
                u32 v = mpp;
                FN_SET_MON_DATA(pmon, 0x11u + i, &v);
            }
        }
    }

    SCRIPTING_BATTLER = b;
    BATTLE_MOVE_DMG = -((s32)max_hp - (s32)hp);
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
    FN_BS_PUSH(instr + 2);
    CURR_INSTR = (wish == 2u) ? BS_V9_SWITCHIN_LDANCE : BS_V9_SWITCHIN_HWISH;
}

/* ============= Familia One-Shot (eff 243 com acc, 244 sem acc) ========== */

static u8 is_uncopyable_ability(u16 ab)
{
    return (ab == 0u || ab == 25u || ab == 36u || ab == 59u) ? 1u : 0u;
}

static int find_pending_turn_slot(u8 bank)
{
    u32 cnt = BATTLERS_COUNT;
    if (cnt > 4u)
        cnt = 4u;
    for (u32 i = (u32)CURR_TURN_ACTION_NUM + 1u; i < cnt; ++i) {
        if (BATTLER_BY_TURN[i] == bank)
            return (int)i;
    }
    return -1;
}

void hook_oneshot_prep_v9(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;

    /* Golpes em alvo unico que exigem alvo vivo */
    if (move != 379u && move != 392u && move != 477u && move != 583u && move != 628u) {
        if (!is_bank_alive(tgt)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
    }

    if (move == 486u) { /* Soak */
        if (has_substitute(tgt) || (t[0x22u] == 11u && t[0x23u] == 11u && get_extra_type(tgt) == 0u))
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 675u) { /* Magic Powder */
        if (has_substitute(tgt) || (t[0x22u] == 14u && t[0x23u] == 14u && get_extra_type(tgt) == 0u))
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 512u) { /* Reflect Type */
        if (t[0x22u] == 9u && t[0x23u] == 9u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 563u) { /* Trick-or-Treat */
        if (has_substitute(tgt) || has_type_v9(tgt, 7u))
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 567u) { /* Forest's Curse */
        if (has_substitute(tgt) || has_type_v9(tgt, 12u))
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 578u) { /* Electrify */
        int slot = find_pending_turn_slot(tgt);
        if (slot < 0 || ACTIONS_BY_TURN[slot] != 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 572u) { /* Topsy-Turvy */
        if (has_substitute(tgt)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        u8 any = 0u;
        for (u32 s = 1u; s <= 7u; ++s) {
            if (t[0x18u + s] != 6u)
                any = 1u;
        }
        if (!any)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 380u) { /* Gastro Acid */
        u16 ab = *(volatile u16 *)(t + 0x20u);
        if (has_substitute(tgt) || ab == 0u || (STATUSES3[tgt] & 0x00010000u) != 0u || is_uncopyable_ability(ab))
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 388u) { /* Worry Seed */
        u16 ab = *(volatile u16 *)(t + 0x20u);
        if (has_substitute(tgt) || ab == 15u || ab == 54u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 493u) { /* Entrainment */
        u16 a_ab = *(volatile u16 *)(a + 0x20u);
        u16 t_ab = *(volatile u16 *)(t + 0x20u);
        if (has_substitute(tgt) || is_uncopyable_ability(a_ab) || t_ab == 54u || a_ab == t_ab)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 759u) { /* Doodle */
        u16 t_ab = *(volatile u16 *)(t + 0x20u);
        if (is_uncopyable_ability(t_ab)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        u8 any = (*(volatile u16 *)(a + 0x20u) != t_ab && *(volatile u16 *)(a + 0x20u) != 54u) ? 1u : 0u;
        if ((BATTLE_TYPE_FLAGS & 0x01u) != 0u && is_bank_alive((u8)(atk ^ 2u))) {
            volatile u8 *al = BATTLE_MONS + 0x5Cu * (atk ^ 2u);
            u16 al_ab = *(volatile u16 *)(al + 0x20u);
            if (al_ab != t_ab && al_ab != 54u)
                any = 1u;
        }
        if (!any)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 392u) { /* Aqua Ring */
        if (has_aqua_ring(atk))
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 583u) { /* Fairy Lock */
        if (V9_STATE->fairy_lock_turns > 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 678u) { /* Octolock */
        if (has_substitute(tgt) || has_octolock(tgt)
            || (*(volatile u32 *)(t + 0x54u) & STATUS2_ESCAPE_PREVENTION) != 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
        }
    } else if (move == 494u || move == 510u) { /* After You / Quash */
        if (find_pending_turn_slot(tgt) < 0)
            CURR_INSTR = BS_BUT_IT_FAILED;
    }
}

static void swap_u8_v9(volatile u8 *x, volatile u8 *y)
{
    u8 tmp = *x;
    *x = *y;
    *y = tmp;
}

static void swap_u16_v9(volatile u16 *x, volatile u16 *y)
{
    u16 tmp = *x;
    *x = *y;
    *y = tmp;
}

void hook_oneshot_apply_v9(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    u32 tail_idx = 0u;

    if (move == 392u) { /* Aqua Ring */
        V9_STATE->aqua_ring_tag[atk] = mon_tag(atk);
        tail_idx = 0u;
    } else if (move == 486u) { /* Soak */
        t[0x22u] = 11u;
        t[0x23u] = 11u;
        V9_STATE->extra_type[tgt] = 0u;
        tail_idx = 1u;
    } else if (move == 675u) { /* Magic Powder */
        t[0x22u] = 14u;
        t[0x23u] = 14u;
        V9_STATE->extra_type[tgt] = 0u;
        tail_idx = 2u;
    } else if (move == 512u) { /* Reflect Type */
        a[0x22u] = t[0x22u];
        a[0x23u] = t[0x23u];
        u8 et = get_extra_type(tgt);
        V9_STATE->extra_type[atk] = et;
        if (et != 0u)
            V9_STATE->extra_type_tag[atk] = mon_tag(atk);
        tail_idx = 3u;
    } else if (move == 563u) { /* Trick-or-Treat */
        V9_STATE->extra_type[tgt] = 7u;
        V9_STATE->extra_type_tag[tgt] = mon_tag(tgt);
        tail_idx = 4u;
    } else if (move == 567u) { /* Forest's Curse */
        V9_STATE->extra_type[tgt] = 12u;
        V9_STATE->extra_type_tag[tgt] = mon_tag(tgt);
        tail_idx = 5u;
    } else if (move == 578u) { /* Electrify */
        V9_STATE->electrified_mask |= (u8)(1u << tgt);
        tail_idx = 6u;
    } else if (move == 379u) { /* Power Trick */
        swap_u16_v9((volatile u16 *)(a + 0x02u), (volatile u16 *)(a + 0x04u));
        tail_idx = 7u;
    } else if (move == 384u) { /* Power Swap */
        swap_u8_v9(a + 0x19u, t + 0x19u);
        swap_u8_v9(a + 0x1Cu, t + 0x1Cu);
        tail_idx = 8u;
    } else if (move == 385u) { /* Guard Swap */
        swap_u8_v9(a + 0x1Au, t + 0x1Au);
        swap_u8_v9(a + 0x1Du, t + 0x1Du);
        tail_idx = 9u;
    } else if (move == 391u) { /* Heart Swap */
        for (u32 s = 1u; s <= 7u; ++s)
            swap_u8_v9(a + 0x18u + s, t + 0x18u + s);
        tail_idx = 10u;
    } else if (move == 638u) { /* Speed Swap */
        swap_u16_v9((volatile u16 *)(a + 0x06u), (volatile u16 *)(t + 0x06u));
        tail_idx = 11u;
    } else if (move == 469u) { /* Guard Split */
        u16 avg_d = (u16)(((u32)(*(volatile u16 *)(a + 0x04u)) + *(volatile u16 *)(t + 0x04u)) >> 1);
        u16 avg_s = (u16)(((u32)(*(volatile u16 *)(a + 0x0Au)) + *(volatile u16 *)(t + 0x0Au)) >> 1);
        if (avg_d < 1u) avg_d = 1u;
        if (avg_s < 1u) avg_s = 1u;
        *(volatile u16 *)(a + 0x04u) = avg_d;
        *(volatile u16 *)(t + 0x04u) = avg_d;
        *(volatile u16 *)(a + 0x0Au) = avg_s;
        *(volatile u16 *)(t + 0x0Au) = avg_s;
        tail_idx = 12u;
    } else if (move == 470u) { /* Power Split */
        u16 avg_a = (u16)(((u32)(*(volatile u16 *)(a + 0x02u)) + *(volatile u16 *)(t + 0x02u)) >> 1);
        u16 avg_s = (u16)(((u32)(*(volatile u16 *)(a + 0x08u)) + *(volatile u16 *)(t + 0x08u)) >> 1);
        if (avg_a < 1u) avg_a = 1u;
        if (avg_s < 1u) avg_s = 1u;
        *(volatile u16 *)(a + 0x02u) = avg_a;
        *(volatile u16 *)(t + 0x02u) = avg_a;
        *(volatile u16 *)(a + 0x08u) = avg_s;
        *(volatile u16 *)(t + 0x08u) = avg_s;
        tail_idx = 13u;
    } else if (move == 572u) { /* Topsy-Turvy */
        u8 rose = 0u, fell = 0u;
        for (u32 s = 1u; s <= 7u; ++s) {
            u8 old_st = t[0x18u + s];
            if (old_st != 6u && old_st <= 12u) {
                u8 new_st = (u8)(12u - old_st);
                t[0x18u + s] = new_st;
                if (new_st > old_st)
                    rose = 1u;
                else
                    fell = 1u;
            }
        }
        if (rose) {
            V7_STATE->stat_rose_mask |= (u8)(1u << tgt);
            V7_STATE->rose_pid[tgt] = mon_tag(tgt);
        }
        if (fell) {
            V7_STATE->stat_fell_mask |= (u8)(1u << tgt);
            V7_STATE->fell_pid[tgt] = mon_tag(tgt);
        }
        tail_idx = 14u;
    } else if (move == 380u) { /* Gastro Acid */
        STATUSES3[tgt] |= 0x00010000u;
        *(volatile u16 *)(t + 0x20u) = 0u;
        tail_idx = 15u;
    } else if (move == 388u) { /* Worry Seed */
        *(volatile u16 *)(t + 0x20u) = 15u;
        if ((*(volatile u32 *)(t + 0x50u) & 0x07u) != 0u) {
            *(volatile u32 *)(t + 0x50u) = 0u;
            *(volatile u32 *)(t + 0x54u) &= ~0x08000000u; /* Nightmare */
            emit_status_sync(tgt);
            CURR_INSTR = BS_V9_WORRY_SEED_WAKE;
            return;
        }
        tail_idx = 16u;
    } else if (move == 493u) { /* Entrainment */
        *(volatile u16 *)(t + 0x20u) = *(volatile u16 *)(a + 0x20u);
        tail_idx = 17u;
    } else if (move == 759u) { /* Doodle */
        u16 t_ab = *(volatile u16 *)(t + 0x20u);
        if (*(volatile u16 *)(a + 0x20u) != 54u)
            *(volatile u16 *)(a + 0x20u) = t_ab;
        if ((BATTLE_TYPE_FLAGS & 0x01u) != 0u && is_bank_alive((u8)(atk ^ 2u))) {
            volatile u8 *al = BATTLE_MONS + 0x5Cu * (atk ^ 2u);
            if (*(volatile u16 *)(al + 0x20u) != 54u)
                *(volatile u16 *)(al + 0x20u) = t_ab;
        }
        tail_idx = 18u;
    } else if (move == 628u) { /* Laser Focus */
        V9_STATE->laser_focus_turns[atk] = 2u;
        V9_STATE->laser_focus_tag[atk] = mon_tag(atk);
        tail_idx = 19u;
    } else if (move == 477u) { /* Magic Room */
        if (V9_STATE->magic_room_turns > 0u) {
            V9_STATE->magic_room_turns = 0u;
            tail_idx = 21u;
        } else {
            V9_STATE->magic_room_turns = 5u;
            tail_idx = 20u;
        }
    } else if (move == 583u) { /* Fairy Lock */
        V9_STATE->fairy_lock_turns = 2u;
        V9_STATE->fairy_lock_mask = 0u;
        for (u32 b = 0u; b < BATTLERS_COUNT && b < 4u; ++b) {
            if (is_bank_alive((u8)b) && !has_type_v9((u8)b, 7u)) {
                volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
                if ((*(volatile u32 *)(m + 0x54u) & STATUS2_ESCAPE_PREVENTION) == 0u) {
                    *(volatile u32 *)(m + 0x54u) |= STATUS2_ESCAPE_PREVENTION;
                    V9_STATE->fairy_lock_mask |= (u8)(1u << b);
                }
            }
        }
        tail_idx = 22u;
    } else if (move == 494u) { /* After You */
        int pos = find_pending_turn_slot(tgt);
        int next = (int)CURR_TURN_ACTION_NUM + 1;
        if (pos > next) {
            u8 b_save = BATTLER_BY_TURN[pos];
            u8 a_save = ACTIONS_BY_TURN[pos];
            for (int k = pos; k > next; --k) {
                BATTLER_BY_TURN[k] = BATTLER_BY_TURN[k - 1];
                ACTIONS_BY_TURN[k] = ACTIONS_BY_TURN[k - 1];
            }
            BATTLER_BY_TURN[next] = b_save;
            ACTIONS_BY_TURN[next] = a_save;
        }
        tail_idx = 23u;
    } else if (move == 510u) { /* Quash */
        int pos = find_pending_turn_slot(tgt);
        int last = (int)BATTLERS_COUNT - 1;
        if (pos >= 0 && pos < last) {
            u8 b_save = BATTLER_BY_TURN[pos];
            u8 a_save = ACTIONS_BY_TURN[pos];
            for (int k = pos; k < last; ++k) {
                BATTLER_BY_TURN[k] = BATTLER_BY_TURN[k + 1];
                ACTIONS_BY_TURN[k] = ACTIONS_BY_TURN[k + 1];
            }
            BATTLER_BY_TURN[last] = b_save;
            ACTIONS_BY_TURN[last] = a_save;
        }
        tail_idx = 24u;
    } else if (move == 678u) { /* Octolock */
        V9_STATE->octolock_src[tgt] = atk;
        V9_STATE->octolock_src_tag[tgt] = mon_tag(atk);
        V9_STATE->octolock_tgt_tag[tgt] = mon_tag(tgt);
        CURR_INSTR = BS_V9_OCTOLOCK_SET;
        return;
    }

    CURR_INSTR = BS_V9_MSG_TAILS + 12u * tail_idx;
}

/* ============= Familia Multi-Boost / Stat Queue (eff 245/246) =========== */

static void push_stat_op(u8 bank, u8 stat, u8 stages, u8 is_down)
{
    u8 idx = V9_STATE->op_count;
    if (idx >= 12u)
        return;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * (bank & 3u);
    u8 cur = m[0x18u + stat];
    if (!is_down && cur >= 12u)
        return;
    if (is_down && cur == 0u)
        return;
    V9_STATE->op_bank[idx] = bank & 3u;
    V9_STATE->op_changer[idx] = (u8)(stat | (stages << 4) | (is_down ? 0x80u : 0u));
    V9_STATE->op_count = (u8)(idx + 1u);
}

static u8 can_poison_target(u8 tgt)
{
    if (!is_bank_alive(tgt) || has_substitute(tgt))
        return 0u;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    if (*(volatile u32 *)(t + 0x50u) != 0u)
        return 0u;
    if (has_type_v9(tgt, 3u) || has_type_v9(tgt, 8u))
        return 0u;
    if (*(volatile u16 *)(t + 0x20u) == 17u)
        return 0u;
    if ((SIDE_STATUSES[FN_GET_SIDE(tgt)] & 0x0020u) != 0u)
        return 0u;
    if (V8_STATE->terrain_type == TERRAIN_MISTY && V8_STATE->terrain_turns > 0u && is_grounded_v9(tgt))
        return 0u;
    return 1u;
}

void hook_multi_prep_v9(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;

    V9_STATE->op_count = 0u;
    V9_STATE->op_idx = 0u;
    V9_STATE->multi_aux = 0u;
    V9_STATE->saved_dmg = 0u;
    V9_STATE->saved_tgt = tgt;

    if (move == 367u) { /* Acupressure */
        u8 cand[7];
        u32 n = 0u;
        for (u8 s = 1u; s <= 7u; ++s) {
            if (a[0x18u + s] < 12u)
                cand[n++] = s;
        }
        if (n == 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        u8 pick = cand[FN_UMOD32(FN_RANDOM(), n)];
        push_stat_op(atk, pick, 2u, 0u);
    } else if (move == 684u) { /* Decorate */
        if (!is_bank_alive(tgt)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        push_stat_op(tgt, 1u, 2u, 0u);
        push_stat_op(tgt, 4u, 2u, 0u);
        if (V9_STATE->op_count == 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 750u) { /* Spicy Extract */
        if (!is_bank_alive(tgt) || has_substitute(tgt)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        push_stat_op(tgt, 1u, 2u, 0u);
        push_stat_op(tgt, 2u, 2u, 1u);
        if (V9_STATE->op_count == 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 673u) { /* No Retreat */
        if (has_no_retreat(atk)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        for (u8 s = 1u; s <= 5u; ++s)
            push_stat_op(atk, s, 1u, 0u);
        V9_STATE->multi_aux = 1u; /* trava no pos-efeito */
    } else if (move == 682u) { /* Clangorous Soul */
        u16 hp = *(volatile u16 *)(a + 0x2Au);
        u16 max_hp = *(volatile u16 *)(a + 0x2Eu);
        u16 cost = (u16)FN_UDIV32(max_hp, 3u);
        if (cost < 1u)
            cost = 1u;
        for (u8 s = 1u; s <= 5u; ++s)
            push_stat_op(atk, s, 1u, 0u);
        if (hp <= cost || V9_STATE->op_count == 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        V9_STATE->saved_dmg = cost;
    } else if (move == 760u) { /* Fillet Away */
        u16 hp = *(volatile u16 *)(a + 0x2Au);
        u16 max_hp = *(volatile u16 *)(a + 0x2Eu);
        u16 cost = (u16)(max_hp >> 1);
        if (cost < 1u)
            cost = 1u;
        push_stat_op(atk, 1u, 2u, 0u);
        push_stat_op(atk, 4u, 2u, 0u);
        push_stat_op(atk, 3u, 2u, 0u);
        if (hp <= cost || V9_STATE->op_count == 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        V9_STATE->saved_dmg = cost;
    } else if (move == 743u) { /* Take Heart */
        u32 st1 = *(volatile u32 *)(a + 0x50u);
        push_stat_op(atk, 4u, 1u, 0u);
        push_stat_op(atk, 5u, 1u, 0u);
        if (st1 == 0u && V9_STATE->op_count == 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        if (st1 != 0u)
            V9_STATE->multi_aux = 2u; /* cura status antes dos boosts */
    } else if (move == 595u) { /* Venom Drench */
        u8 foes[2];
        u32 nf = 1u;
        foes[0] = tgt;
        if ((BATTLE_TYPE_FLAGS & 0x01u) != 0u && is_bank_alive((u8)(tgt ^ 2u))) {
            foes[1] = (u8)(tgt ^ 2u);
            nf = 2u;
        }
        for (u32 i = 0u; i < nf; ++i) {
            u8 f = foes[i];
            if (!is_bank_alive(f) || has_substitute(f))
                continue;
            volatile u8 *fm = BATTLE_MONS + 0x5Cu * f;
            if ((*(volatile u32 *)(fm + 0x50u) & 0x88u) != 0u) {
                push_stat_op(f, 1u, 1u, 1u);
                push_stat_op(f, 4u, 1u, 1u);
                push_stat_op(f, 3u, 1u, 1u);
            }
        }
        if (V9_STATE->op_count == 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 627u) { /* Toxic Thread */
        if (!is_bank_alive(tgt) || has_substitute(tgt)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        push_stat_op(tgt, 3u, 1u, 1u);
        u8 can_psn = can_poison_target(tgt);
        if (V9_STATE->op_count == 0u && !can_psn) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        if (can_psn)
            V9_STATE->multi_aux = 3u;
    } else if (move == 674u) { /* Tar Shot */
        if (!is_bank_alive(tgt) || has_substitute(tgt)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        push_stat_op(tgt, 3u, 1u, 1u);
        u8 can_tar = has_tar_shot(tgt) ? 0u : 1u;
        if (V9_STATE->op_count == 0u && !can_tar) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        if (can_tar)
            V9_STATE->multi_aux = 4u;
    } else if (move == 598u || move == 629u) { /* Magnetic Flux / Gear Up */
        u8 banks[2];
        u32 nb = 1u;
        banks[0] = atk;
        if ((BATTLE_TYPE_FLAGS & 0x01u) != 0u && is_bank_alive((u8)(atk ^ 2u))) {
            banks[1] = (u8)(atk ^ 2u);
            nb = 2u;
        }
        for (u32 i = 0u; i < nb; ++i) {
            u8 b = banks[i];
            volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
            u16 ab = *(volatile u16 *)(m + 0x20u);
            if (ab == 57u || ab == 58u) {
                if (move == 598u) {
                    push_stat_op(b, 2u, 1u, 0u);
                    push_stat_op(b, 5u, 1u, 0u);
                } else {
                    push_stat_op(b, 1u, 1u, 0u);
                    push_stat_op(b, 4u, 1u, 0u);
                }
            }
        }
        if (V9_STATE->op_count == 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 575u || move == 559u) { /* Flower Shield / Rototiller */
        for (u32 b = 0u; b < BATTLERS_COUNT && b < 4u; ++b) {
            if (!is_bank_alive((u8)b) || !has_type_v9((u8)b, 12u))
                continue;
            if (move == 559u && !is_grounded_v9((u8)b))
                continue;
            if (move == 575u) {
                push_stat_op((u8)b, 2u, 1u, 0u);
            } else {
                push_stat_op((u8)b, 1u, 1u, 0u);
                push_stat_op((u8)b, 4u, 1u, 0u);
            }
        }
        if (V9_STATE->op_count == 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    }
}

void hook_multi_pre_fx_v9(void)
{
    /* Layout no script logo apos callasm: [0..3]=ptr_hp_cost, [4..7]=ptr_cure, [8..11]=ptr_loop */
    const u8 *instr = CURR_INSTR;
    const u8 *ptr_hp = (const u8 *)read_u32_unaligned(instr);
    const u8 *ptr_cure = (const u8 *)read_u32_unaligned(instr + 4);
    const u8 *ptr_loop = (const u8 *)read_u32_unaligned(instr + 8);

    if (V9_STATE->saved_dmg > 0u) {
        u16 dmg = V9_STATE->saved_dmg;
        V9_STATE->saved_dmg = 0u;
        BATTLE_MOVE_DMG = (s32)dmg;
        MOVE_RESULT_FLAGS &= (u8)~0x29u;
        CURR_INSTR = ptr_hp;
        return;
    }
    if (V9_STATE->multi_aux == 2u) {
        V9_STATE->multi_aux = 0u;
        u8 atk = ATTACKER & 3u;
        volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
        *(volatile u32 *)(a + 0x50u) = 0u;
        SCRIPTING_BATTLER = atk;
        emit_status_sync(atk);
        CURR_INSTR = ptr_cure;
        return;
    }
    CURR_INSTR = ptr_loop;
}

void hook_multi_next_stat_v9(void)
{
    /* Layout: [0..3]=ptr_up, [4..7]=ptr_down, [8..11]=ptr_post */
    const u8 *instr = CURR_INSTR;
    const u8 *ptr_up = (const u8 *)read_u32_unaligned(instr);
    const u8 *ptr_down = (const u8 *)read_u32_unaligned(instr + 4);
    const u8 *ptr_post = (const u8 *)read_u32_unaligned(instr + 8);

    u8 idx = V9_STATE->op_idx;
    if (idx >= V9_STATE->op_count) {
        TARGET = V9_STATE->saved_tgt;
        CURR_INSTR = ptr_post;
        return;
    }
    V9_STATE->op_idx = (u8)(idx + 1u);
    u8 b = V9_STATE->op_bank[idx] & 3u;
    u8 chg = V9_STATE->op_changer[idx];
    TARGET = b;
    SCRIPTING_BATTLER = b;
    ANIM_ARG1_BYTE = 0u;
    STAT_BUFF_ADDR = chg;
    CURR_INSTR = ((chg & 0x80u) != 0u) ? ptr_down : ptr_up;
}

void hook_multi_post_fx_v9(void)
{
    u8 atk = ATTACKER & 3u;
    u8 tgt = V9_STATE->saved_tgt & 3u;
    TARGET = tgt;

    u8 aux = V9_STATE->multi_aux;
    V9_STATE->multi_aux = 0u;
    if (aux == 1u) { /* No Retreat */
        volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
        *(volatile u32 *)(a + 0x54u) |= STATUS2_ESCAPE_PREVENTION;
        V9_STATE->no_retreat_tag[atk] = mon_tag(atk);
        CURR_INSTR = BS_V9_MSG_TAILS + 12u * 25u;
        return;
    }
    if (aux == 3u) { /* Toxic Thread */
        if (can_poison_target(tgt)) {
            CURR_INSTR = BS_V9_TOXIC_THREAD_PSN;
            return;
        }
    } else if (aux == 4u) { /* Tar Shot */
        V9_STATE->tar_shot_tag[tgt] = mon_tag(tgt);
        CURR_INSTR = BS_V9_MSG_TAILS + 12u * 26u;
        return;
    }
    CURR_INSTR = BS_MOVE_END;
}

/* ============= Strength Sap (247), Wishes (248) & Shed Tail (249) ======= */

void hook_strength_sap_prep_v9(void)
{
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    if (!is_bank_alive(tgt) || has_substitute(tgt) || is_heal_blocked(atk)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    u8 stage = t[0x19u];
    if (stage == 0u) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    if (stage > 12u)
        stage = 6u;
    u32 raw_atk = *(volatile u16 *)(t + 0x02u);
    u32 eff_atk = FN_UDIV32(raw_atk * STAT_STAGE_RATIOS[2u * stage], STAT_STAGE_RATIOS[2u * stage + 1u]);
    if (eff_atk < 1u)
        eff_atk = 1u;
    if (eff_atk > 0x7FFFu)
        eff_atk = 0x7FFFu;
    V9_STATE->saved_dmg = (u16)eff_atk;
    ANIM_ARG1_BYTE = 0u;
    STAT_BUFF_ADDR = (u8)(1u | (1u << 4) | 0x80u);
}

void hook_strength_sap_heal_v9(void)
{
    /* Layout: [0..3]=ptr_heal, [4..7]=ptr_ooze */
    const u8 *instr = CURR_INSTR;
    const u8 *ptr_heal = (const u8 *)read_u32_unaligned(instr);
    const u8 *ptr_ooze = (const u8 *)read_u32_unaligned(instr + 4);

    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    s32 amt = (s32)V9_STATE->saved_dmg;

    if (*(volatile u16 *)(t + 0x20u) == 64u) { /* Liquid Ooze */
        BATTLE_MOVE_DMG = amt;
        MOVE_RESULT_FLAGS &= (u8)~0x29u;
        CURR_INSTR = ptr_ooze;
        return;
    }
    if (*(volatile u16 *)(a + 0x2Au) >= *(volatile u16 *)(a + 0x2Eu)) {
        CURR_INSTR = BS_MOVE_END;
        return;
    }
    BATTLE_MOVE_DMG = -amt;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
    CURR_INSTR = ptr_heal;
}

void hook_wish_sac_prep_v9(void)
{
    u8 atk = ATTACKER & 3u;
    u8 side = FN_GET_SIDE(atk);
    V9_STATE->wish_pending[side] = (CURRENT_MOVE == 460u) ? 2u : 1u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    BATTLE_MOVE_DMG = (s32)(*(volatile u16 *)(a + 0x2Au));
    FAINTED_BATTLER = atk;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
}

void hook_shed_tail_prep_v9(void)
{
    u8 atk = ATTACKER & 3u;
    if (has_substitute(atk)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    u16 hp = *(volatile u16 *)(a + 0x2Au);
    u16 max_hp = *(volatile u16 *)(a + 0x2Eu);
    u16 cost = (u16)((max_hp + 1u) >> 1);
    if (cost < 1u)
        cost = 1u;
    if (hp <= cost) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    u32 sub_hp = max_hp >> 2;
    if (sub_hp < 1u)
        sub_hp = 1u;
    else if (sub_hp > 255u)
        sub_hp = 255u;
    V9_STATE->shed_tail_sub_hp = (u8)sub_hp;
    BATTLE_MOVE_DMG = (s32)cost;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
}

void hook_shed_tail_install_v9(void)
{
    u8 atk = ATTACKER & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    *(volatile u32 *)(a + 0x54u) |= STATUS2_SUBSTITUTE;
    DISABLE_STRUCTS_REAL[28u * atk + 0x0Au] = V9_STATE->shed_tail_sub_hp;
}

/* ============= Cleanse / Psycho Shift / Dark Void (250/251) ============= */

static u8 can_receive_psycho_shift(u8 tgt, u32 st1)
{
    if (!is_bank_alive(tgt) || has_substitute(tgt))
        return 0u;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    if (*(volatile u32 *)(t + 0x50u) != 0u)
        return 0u;
    if ((SIDE_STATUSES[FN_GET_SIDE(tgt)] & 0x0020u) != 0u)
        return 0u;
    u8 grounded = is_grounded_v9(tgt);
    if (V8_STATE->terrain_type == TERRAIN_MISTY && V8_STATE->terrain_turns > 0u && grounded)
        return 0u;

    u16 ab = *(volatile u16 *)(t + 0x20u);
    if ((st1 & 0x07u) != 0u) { /* Sleep */
        if (ab == 15u || ab == 72u)
            return 0u;
        if (V8_STATE->terrain_type == TERRAIN_ELECTRIC && V8_STATE->terrain_turns > 0u && grounded)
            return 0u;
    } else if ((st1 & 0x88u) != 0u) { /* Poison / Toxic */
        if (has_type_v9(tgt, 3u) || has_type_v9(tgt, 8u) || ab == 17u)
            return 0u;
    } else if ((st1 & 0x10u) != 0u) { /* Burn */
        if (has_type_v9(tgt, 10u) || ab == 41u)
            return 0u;
    } else if ((st1 & 0x40u) != 0u) { /* Paralysis */
        if (has_type_v9(tgt, 13u) || ab == 7u)
            return 0u;
    } else if ((st1 & 0x20u) != 0u) { /* Freeze */
        if (has_type_v9(tgt, 15u) || ab == 40u)
            return 0u;
    }
    return 1u;
}

void hook_cleanse_prep_v9(void)
{
    /* Layout apos callasm: [0..3]=ptr_noacc_anim (pula 0x01 para golpes sem acc) */
    const u8 *instr = CURR_INSTR;
    const u8 *ptr_anim = (const u8 *)read_u32_unaligned(instr);
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;

    V9_STATE->multi_step = 0u;

    if (move == 375u) { /* Psycho Shift (usa 0x01 logo em instr + 4) */
        u32 st1 = *(volatile u32 *)(a + 0x50u);
        if (st1 == 0u || !can_receive_psycho_shift(tgt, st1)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        if ((st1 & 0x80u) != 0u)
            st1 = 0x0180u;
        V9_STATE->saved_status = st1;
        CURR_INSTR = instr + 4;
        return;
    }
    if (move == 640u) { /* Purify */
        if (!is_bank_alive(tgt) || has_substitute(tgt) || *(volatile u32 *)(t + 0x50u) == 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        CURR_INSTR = ptr_anim;
        return;
    }
    /* Jungle Healing (710) / Lunar Blessing (742) */
    u8 any = 0u;
    u8 banks[2];
    u32 nb = 1u;
    banks[0] = atk;
    if ((BATTLE_TYPE_FLAGS & 0x01u) != 0u && is_bank_alive((u8)(atk ^ 2u))) {
        banks[1] = (u8)(atk ^ 2u);
        nb = 2u;
    }
    for (u32 i = 0u; i < nb; ++i) {
        u8 b = banks[i];
        volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
        if (*(volatile u32 *)(m + 0x50u) != 0u)
            any = 1u;
        if (!is_heal_blocked(b) && *(volatile u16 *)(m + 0x2Au) < *(volatile u16 *)(m + 0x2Eu))
            any = 1u;
    }
    if (!any) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    CURR_INSTR = ptr_anim;
}

void hook_cleanse_step_v9(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;

    if (move == 375u) { /* Psycho Shift */
        u8 stp = V9_STATE->multi_step++;
        if (stp == 0u) {
            *(volatile u32 *)(a + 0x50u) = 0u;
            *(volatile u32 *)(a + 0x54u) &= ~0x08000000u;
            emit_status_sync(atk);
            CURR_INSTR = BS_V9_PSHIFT_SELF_CURE;
            return;
        }
        *(volatile u32 *)(t + 0x50u) = V9_STATE->saved_status;
        emit_status_sync(tgt);
        CURR_INSTR = BS_V9_PSHIFT_INFLICT;
        return;
    }

    if (move == 640u) { /* Purify */
        u8 stp = V9_STATE->multi_step++;
        if (stp == 0u) {
            *(volatile u32 *)(t + 0x50u) = 0u;
            *(volatile u32 *)(t + 0x54u) &= ~0x08000000u;
            SCRIPTING_BATTLER = tgt;
            emit_status_sync(tgt);
            CURR_INSTR = BS_V9_CLEANSE_CURE_STEP;
            return;
        }
        if (stp == 1u && !is_heal_blocked(atk)) {
            u16 hp = *(volatile u16 *)(a + 0x2Au);
            u16 max_hp = *(volatile u16 *)(a + 0x2Eu);
            if (hp < max_hp) {
                s32 heal = (s32)((max_hp + 1u) >> 1);
                if (heal < 1)
                    heal = 1;
                SCRIPTING_BATTLER = atk;
                BATTLE_MOVE_DMG = -heal;
                MOVE_RESULT_FLAGS &= (u8)~0x29u;
                CURR_INSTR = BS_V9_CLEANSE_HEAL_STEP;
                return;
            }
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Jungle Healing (710) / Lunar Blessing (742): passos 0..3 */
    while (V9_STATE->multi_step < 4u) {
        u8 stp = V9_STATE->multi_step++;
        u8 b = (stp < 2u) ? atk : (u8)(atk ^ 2u);
        if (stp >= 2u && ((BATTLE_TYPE_FLAGS & 0x01u) == 0u || !is_bank_alive(b)))
            continue;
        volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
        if ((stp & 1u) == 0u) {
            if (!is_heal_blocked(b)) {
                u16 hp = *(volatile u16 *)(m + 0x2Au);
                u16 max_hp = *(volatile u16 *)(m + 0x2Eu);
                if (hp < max_hp) {
                    s32 heal = (s32)(max_hp >> 2);
                    if (heal < 1)
                        heal = 1;
                    SCRIPTING_BATTLER = b;
                    BATTLE_MOVE_DMG = -heal;
                    MOVE_RESULT_FLAGS &= (u8)~0x29u;
                    CURR_INSTR = BS_V9_CLEANSE_HEAL_STEP;
                    return;
                }
            }
        } else {
            if (*(volatile u32 *)(m + 0x50u) != 0u) {
                *(volatile u32 *)(m + 0x50u) = 0u;
                *(volatile u32 *)(m + 0x54u) &= ~0x08000000u;
                SCRIPTING_BATTLER = b;
                emit_status_sync(b);
                CURR_INSTR = BS_V9_CLEANSE_CURE_STEP;
                return;
            }
        }
    }
    CURR_INSTR = BS_MOVE_END;
}

void hook_dark_void_step_v9(void)
{
    /* Layout: [0..3]=ptr_try_foe (0x01 acc -> 09 0A -> sono -> volta a step) */
    const u8 *instr = CURR_INSTR;
    const u8 *ptr_try_foe = (const u8 *)read_u32_unaligned(instr);
    u8 atk = ATTACKER & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;

    if (V9_STATE->multi_step == 0u) {
        if (*(volatile u16 *)(a + 0x00u) != 491u) {
            CURR_INSTR = BS_V9_MSG_TAILS + 12u * 27u;
            return;
        }
        V9_STATE->saved_tgt = TARGET & 3u;
        V9_STATE->multi_aux = 0u;
    }

    while (V9_STATE->multi_step < 2u) {
        u8 idx = V9_STATE->multi_step++;
        u8 foe = (idx == 0u) ? V9_STATE->saved_tgt : (u8)(V9_STATE->saved_tgt ^ 2u);
        if (idx == 1u && (BATTLE_TYPE_FLAGS & 0x01u) == 0u)
            continue;
        if (!is_bank_alive(foe))
            continue;
        if (!can_receive_psycho_shift(foe, 1u))
            continue;
        TARGET = foe;
        V9_STATE->multi_aux = 1u;
        CURR_INSTR = ptr_try_foe;
        return;
    }

    TARGET = V9_STATE->saved_tgt;
    CURR_INSTR = (V9_STATE->multi_aux == 0u) ? BS_BUT_IT_FAILED : BS_MOVE_END;
}

/* ============= Copycat (252), Final Gambit (253), Natural Gift (254) ==== */

static u8 is_copycat_banned(u16 m)
{
    if (m == 0u || m >= 822u)
        return 1u;
    /* Golpes proibidos pelo Copycat oficial (Gen 4-9) presentes na ROM */
    switch (m) {
    case 18u:  case 46u:  case 68u:  case 102u: case 111u: case 118u:
    case 119u: case 144u: case 165u: case 166u: case 168u: case 182u:
    case 194u: case 197u: case 203u: case 214u: case 226u: case 243u:
    case 252u: case 264u: case 266u: case 270u: case 271u: case 274u:
    case 277u: case 289u: case 343u: case 364u: case 383u: case 507u:
    case 521u: case 584u: case 616u: case 692u: case 755u: case 761u:
    case 770u: case 771u: case 785u: case 821u:
        return 1u;
    default:
        return 0u;
    }
}

void hook_turn_ctrl_exec_v9(void)
{
    u16 m = V9_STATE->last_used_move;
    if (is_copycat_banned(m)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    CURRENT_MOVE = m;
    HIT_MARKER = (HIT_MARKER & ~0x00000400u) | 0x00000200u;
    TARGET = FN_GET_MOVE_TARGET(m, 0u);
    CURR_INSTR = SCRIPT_TABLE[MOVE_TABLE[12u * m]];
}

void hook_final_gambit_prep_v9(void)
{
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;

    u8 foresight = ((*(volatile u32 *)(t + 0x54u) & STATUS2_FORESIGHT) != 0u) ? 1u : 0u;
    if (!foresight && has_type_v9(tgt, 7u)) {
        MOVE_RESULT_FLAGS = (u8)((MOVE_RESULT_FLAGS & ~0x06u) | 0x08u);
        CURR_INSTR = BS_MISS_AFTER_PP;
        return;
    }
    u16 hp = *(volatile u16 *)(a + 0x2Au);
    V9_STATE->saved_dmg = hp;
    BATTLE_MOVE_DMG = (s32)hp;
    FAINTED_BATTLER = atk;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
}

void hook_final_gambit_dmg_v9(void)
{
    FAINTED_BATTLER = TARGET & 3u;
    BATTLE_MOVE_DMG = (s32)V9_STATE->saved_dmg;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
}

void hook_natural_gift_prep_v9(void)
{
    u8 atk = ATTACKER & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    u16 item = *(volatile u16 *)(a + 0x30u);

    if (V9_STATE->magic_room_turns > 0u || item < 133u || item > 175u) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }

    u32 idx = (u32)(item - 133u);
    u8 ntype = NATURAL_GIFT_TABLE[idx][0];
    u8 npwr = NATURAL_GIFT_TABLE[idx][1];
    DYNAMIC_POWER = npwr;
    BATTLE_STRUCT_PTR[0x13u] = (u8)(0x40u | ntype);

    u16 zero = 0u;
    *(volatile u16 *)(a + 0x30u) = 0u;
    FN_SET_MON_DATA(party_mon_ptr(atk), 0x0Cu, &zero);
    ACTIVE_BATTLER = atk;
    FN_EMIT_SET_MON_DATA(0u, 0x02u, 0u, 2u, (const void *)(a + 0x30u));
    FN_MARK_BUFFER_EXEC(atk);
}
