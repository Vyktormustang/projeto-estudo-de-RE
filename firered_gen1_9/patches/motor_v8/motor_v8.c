/* Rotinas auxiliares de batalha do motor_v8 (ARM7TDMI / Thumb).
 *
 * Habilita as 10 TMs finais de Scarlet/Violet (219 -> 229/229) e 8 golpes de
 * subida de nivel das mesmas familias de clima, terreno, salas, gravidade,
 * barreiras e armadilhas de entrada, encadeando sobre o motor_v7 sem tocar
 * saves ou estruturas persistentes:
 *
 *  1. Clima Snow: TM052 Snowscape (773) e Chilly Reception (771) - 5 turnos
 *     sem dano residual, +50% Defesa fisica para tipo Gelo, Blizzard (59)
 *     infalivel, Weather Ball (311) 100 BP Gelo e ativacao de Aurora Veil (649).
 *  2. Quatro Terrenos (5 turnos): TM136 Electric (599), TM137 Grassy (576),
 *     TM138 Psychic (633) e TM139 Misty (577), com bonus de 1,3x SV, bloqueio
 *     de sono/status/prioridade, cura de 1/16 no fim do turno e sinergias em
 *     Grassy Glide (805), Misty Explosion (810), Expanding Force (701), Rising
 *     Voltage (705), Terrain Pulse (706), Psyblade (783), Floral Healing (621)
 *     e reducao 0,5x em Earthquake (89), Magnitude (222) e Bulldoze (519).
 *  3. Armadilhas e Limpeza: TM091 Toxic Spikes (390), TM116 Stealth Rock (445),
 *     Sticky Web (560), Stone Axe (723), Ceaseless Edge (738), Rapid Spin (229),
 *     Mortal Spin (758), Defog (432), Tidy Up (772) e Court Change (681).
 *  4. Velocidade, Salas, Barreiras e Gravidade: TM113 Tailwind (366), TM161
 *     Trick Room (433), Wonder Room (471), TM178 Gravity (356), Magnet Rise
 *     (393), Aurora Veil (649), Shore Up (614), Brick Break (280) e Psychic
 *     Fangs (652).
 *
 * Limitacoes conhecidas e documentadas:
 *  - Itens e habilidades modernos ausentes na base Gen 3 (Heavy-Duty Boots,
 *    Terrain Extender, Icy Rock, Light Clay, Room Service, Seeds, Surge
 *    abilities, Slush Rush, Ice Scales, Magic Guard, Defiant) nao existem.
 *  - Expanding Force mantem selecao de alvo unico no menu de duplas da Gen 3.
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

#define WEATHER_RAIN_MASK 0x0007u
#define WEATHER_SAND_MASK 0x0018u
#define WEATHER_SUN_MASK  0x0060u
#define WEATHER_HAIL_BIT  0x0080u
#define WEATHER_SNOW_BIT  0x0100u

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

#define V7_STATE                ((volatile struct V7BattleState *)0x0203FC00u)
#define V8_STATE                ((volatile struct V8BattleState *)0x0203FC60u)

#define BATTLE_TYPE_FLAGS       (*(volatile u32 *)0x02020374u)
#define ACTIVE_BATTLER          (*(volatile u8 *)0x020213ECu)
#define CONTROLLER_EXEC_FLAGS   (*(volatile u32 *)0x020213F0u)
#define BATTLERS_COUNT          (*(volatile u8 *)0x020213F4u)
#define PARTY_INDEXES           ((volatile u16 *)0x020213F8u)
#define ACTIONS_BY_TURN         ((volatile u8 *)0x02021404u)
#define BATTLER_BY_TURN         ((volatile u8 *)0x02021408u)
#define CURR_ACTION_FUNC_ID     (*(volatile u8 *)0x0202140Du)
#define BATTLE_MONS             ((volatile u8 *)0x02021410u)
#define CURRENT_MOVE            (*(volatile u16 *)0x02021586u)
#define BATTLE_MOVE_DMG         (*(volatile s32 *)0x0202158Cu)
#define ATTACKER                (*(volatile u8 *)0x020215A8u)
#define TARGET                  (*(volatile u8 *)0x020215A9u)
#define FAINTED_BATTLER         (*(volatile u8 *)0x020215AAu)
#define EFFECT_BATTLER          (*(volatile u8 *)0x020215ABu)
#define POT_ITEM_BATTLER        (*(volatile u8 *)0x020215ACu)
#define ABSENT_BATTLERS         (*(volatile u8 *)0x020215ADu)
#define CURR_INSTR              (*(const u8 *volatile *)0x020215B0u)
#define CHOSEN_ACTION           ((volatile u8 *)0x020215B8u)
#define MOVE_RESULT_FLAGS       (*(volatile u8 *)0x02021608u)
#define HIT_MARKER              (*(volatile u32 *)0x0202160Cu)
#define SIDE_STATUSES           ((volatile u16 *)0x0202161Cu)
#define SIDE_TIMERS             ((volatile u8 *)0x02021620u)
#define STATUSES3               ((volatile u32 *)0x02021638u)
#define PROTECT_STRUCTS         ((volatile u8 *)0x020216CCu)
#define RANDOM_TURN_NUMBER      (*(volatile u16 *)0x020216BCu)
#define MOVE_EFFECT_BYTE        (*(volatile u8 *)0x020216C3u)
#define BATTLE_OUTCOME          (*(volatile u8 *)0x020216C8u)
#define LOCKED_MOVES            ((volatile u16 *)0x020216CCu)
#define BATTLE_WEATHER          (*(volatile u16 *)0x0202175Cu)
#define WEATHER_DURATION        (*(volatile u8 *)0x02021788u)
#define DYNAMIC_POWER           (*(volatile u16 *)0x02021792u)
#define DISABLE_STRUCTS         ((volatile u8 *)0x02021798u)
#define SCRIPTING_DMG_MULT      (*(volatile u8 *)0x02021816u)
#define SCRIPTING_BATTLER       (*(volatile u8 *)0x0202181Fu)
#define SCRIPTING_ANIM_TURN     (*(volatile u8 *)0x02021820u)
#define BATTLE_STRUCT_PTR       (*(volatile u8 *volatile *)0x0202182Cu)
#define BATTLE_RESOURCES_PTR    (*(volatile u8 *volatile *)0x02021838u)
#define BATTLE_MAIN_FUNC        (*(volatile u32 *)0x03005318u)

#define MOVE_TABLE              ((const u8 *)0x09000000u)
#define CATEGORY_TABLE          ((const u8 *)0x0900E000u)
#define TYPE_EFFECT_TABLE       ((const u8 *)0x08200C18u)
#define ACC_STAGE_RATIOS        ((const u8 *)0x08209BD0u)
#define STAT_STAGE_RATIOS       ((const u8 *)0x086BC7BCu)

/* Sub-scripts fixos gravados em 0x090C1000..0x090C12BF por motor_v8.py */
#define BS_V8_GRAVITY_CANCEL    ((const u8 *)0x090C1000u)
#define BS_V8_PTERRAIN_CANCEL   ((const u8 *)0x090C1010u)
#define BS_V8_TERRAIN_BLOCK     ((const u8 *)0x090C1020u)
#define BS_V8_ENDTURN_MSGS      ((const u8 *)0x090C1030u)
#define BS_V8_ENDTURN_GRASSY    ((const u8 *)0x090C1070u)
#define BS_V8_HAZARD_SPIKES_G   ((const u8 *)0x090C1090u)
#define BS_V8_HAZARD_SROCK      ((const u8 *)0x090C10D0u)
#define BS_V8_TSPIKES_ABSORB    ((const u8 *)0x090C1110u)
#define BS_V8_STICKY_WEB_DROP   ((const u8 *)0x090C1120u)
#define BS_V8_SUB_FADE          ((const u8 *)0x090C1160u)
#define BS_V8_RAPIDSPIN_CLEAR   ((const u8 *)0x090C1170u)
#define BS_V8_STATUS_TAILS      ((const u8 *)0x090C1180u)

#define BS_MOVE_END             ((const u8 *)0x081853F6u)
#define BS_BUT_IT_FAILED        ((const u8 *)0x0818689Au)
#define BS_POISON_EFF           ((const u8 *)0x08187C7Du)
#define BS_TOXIC_EFF            ((const u8 *)0x08187CC0u)

/* Encadeamento sobre motor_v7 / funcoes nativas da ROM */
#define PREV_BATTLE_INIT_V7     ((void (*)(void))0x090C0001u)
#define PREV_TURN_START_V7      ((void (*)(void))0x090C0009u)
#define ORIG_SET_TURN_ORDER     ((void (*)(void))0x080541A5u)
#define ORIG_BATTLE_TURN_PASSED ((void (*)(void))0x08053221u)
#define FN_TURN_VALUES_CLEANUP  ((void (*)(u8))0x080543A5u)
#define FN_DO_FIELD_ENDTURN     ((u8 (*)(void))0x0806D069u)
#define PREV_ATTACKCANCELER_V7  ((void (*)(void))0x090C0011u)
#define ORIG_ACCURACYCHECK      ((void (*)(void))0x08057F2Du)
#define PREV_DAMAGE_V7          ((void (*)(void))0x090C0021u)
#define ORIG_TYPECALC           ((void (*)(void))0x08058879u)
#define PREV_SETEFFECT_CH_V7    ((void (*)(void))0x090C0039u)
#define PREV_SETEFFECT_PR_V7    ((void (*)(void))0x090C0041u)
#define PREV_SETEFFECT_SC_V7    ((void (*)(void))0x090C0049u)
#define ORIG_SWITCHINEFFECTS    ((void (*)(void))0x0805DD45u)
#define ORIG_JUMPIFCANTSLEEP    ((void (*)(void))0x08060571u)
#define ORIG_RAPIDSPINFREE      ((void (*)(void))0x08063525u)
#define ORIG_WEATHERBALL        ((void (*)(void))0x08064E05u)
#define ORIG_BRICKBREAK         ((void (*)(void))0x08065091u)

#define FN_GET_SIDE             ((u8 (*)(u8))0x08024685u)
#define FN_EMIT_SET_MON_DATA    ((void (*)(u8, u8, u8, u8, const void *))0x08049DF5u)
#define FN_GET_SCRIPT_BANK      ((u8 (*)(u8))0x0806C535u)
#define FN_MARK_BUFFER_EXEC     ((void (*)(u8))0x0806C8BDu)
#define FN_BS_PUSH              ((void (*)(const u8 *))0x0806CB2Du)
#define FN_ABILITY_EFFECTS      ((u8 (*)(u8, u8, u8, u8, u16))0x0806F4DDu)
#define FN_GET_HOLD_EFFECT      ((u8 (*)(u16))0x080C725Du)
#define FN_GET_HOLD_PARAM       ((u8 (*)(u16))0x080C7279u)
#define FN_RANDOM               ((u16 (*)(void))0x0812E9C5u)
#define FN_UDIV32               ((u32 (*)(u32, u32))0x08172B3Du)
#define FN_UMOD32               ((u32 (*)(u32, u32))0x08172B4Du)

static u32 read_u32_unaligned(const u8 *p)
{
    return (u32)p[0] | ((u32)p[1] << 8) | ((u32)p[2] << 16) | ((u32)p[3] << 24);
}

static u16 read_u16_unaligned(const u8 *p)
{
    return (u16)((u32)p[0] | ((u32)p[1] << 8));
}

static u32 mon_tag(u8 bank)
{
    volatile u8 *m = BATTLE_MONS + 0x5Cu * (bank & 3u);
    u32 pid = *(volatile u32 *)(m + 0x4Cu);
    u32 slot = PARTY_INDEXES[bank & 3u];
    return 0x80000000u | ((slot & 7u) << 28) | (pid & 0x0FFFFFFFu);
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

static u8 weather_suppressed(void)
{
    if (FN_ABILITY_EFFECTS(0x13u, 0u, 0x0Du, 0u, 0u) != 0u)
        return 1u;
    if (FN_ABILITY_EFFECTS(0x13u, 0u, 0x4Cu, 0u, 0u) != 0u)
        return 1u;
    return 0u;
}

static u8 is_snow_active(void)
{
    return ((BATTLE_WEATHER & WEATHER_SNOW_BIT) != 0u && !weather_suppressed()) ? 1u : 0u;
}

static u8 is_snow_or_hail_active(void)
{
    return ((BATTLE_WEATHER & (WEATHER_HAIL_BIT | WEATHER_SNOW_BIT)) != 0u && !weather_suppressed()) ? 1u : 0u;
}

static u8 is_magnet_risen(u8 bank)
{
    bank &= 3u;
    if (V8_STATE->magnet_rise_turns[bank] == 0u)
        return 0u;
    if (V8_STATE->magnet_rise_pid[bank] != mon_tag(bank) || V8_STATE->gravity_turns > 0u) {
        V8_STATE->magnet_rise_turns[bank] = 0u;
        return 0u;
    }
    return 1u;
}

static u8 is_battler_grounded(u8 bank)
{
    bank &= 3u;
    /* Semi-invulneravel no ar (Fly/Bounce: STATUS3_ON_AIR = 0x08) nunca esta no chao. */
    if ((STATUSES3[bank] & 0x00000008u) != 0u)
        return 0u;
    /* Gravity ou Ingrain (STATUS3_ROOTED = 0x2000) aterram qualquer Pokemon. */
    if (V8_STATE->gravity_turns > 0u || (STATUSES3[bank] & 0x00002000u) != 0u)
        return 1u;
    if (is_magnet_risen(bank))
        return 0u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    if (m[0x22u] == 2u || m[0x23u] == 2u)
        return 0u;
    if (*(volatile u16 *)(m + 0x20u) == 26u)
        return 0u;
    return 1u;
}

static u8 is_gravity_blocked_move(u16 move)
{
    return (move == 19u || move == 26u || move == 136u || move == 150u
            || move == 340u || move == 393u || move == 476u
            || move == 506u || move == 556u) ? 1u : 0u;
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

/* ========================= Ciclo de vida e Ordem ========================= */

void hook_battle_init_v8(void)
{
    volatile u8 *p = (volatile u8 *)V8_STATE;
    for (u32 i = 0u; i < sizeof(struct V8BattleState); ++i)
        p[i] = 0u;
    PREV_BATTLE_INIT_V7();
}

void hook_turn_start_v8(void)
{
    V8_STATE->endturn_step = 0u;
    V8_STATE->switchin_hazard_step = 0u;
    V8_STATE->switchin_tag = 0u;
    PREV_TURN_START_V7();
}

static u16 chosen_move_for_bank(u8 b)
{
    if ((PROTECT_STRUCTS[16u * b] & 0x04u) != 0u)
        return 165u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
    if ((*(volatile u32 *)(m + 0x54u) & 0x00001000u) != 0u)
        return LOCKED_MOVES[b];
    u8 mslot = BATTLE_STRUCT_PTR[0x80u + b] & 3u;
    return *(volatile u16 *)(m + 0x0Cu + 2u * mslot);
}

static void compute_turn_metrics(u8 b, s8 *prio_out, u8 *qc_out, u32 *spd_out)
{
    b &= 3u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
    u16 move = chosen_move_for_bank(b);
    s8 prio = (move < 822u) ? (s8)MOVE_TABLE[12u * move + 7u] : 0;
    if (move == 805u
        && V8_STATE->terrain_type == TERRAIN_GRASSY
        && V8_STATE->terrain_turns > 0u
        && is_battler_grounded(b)) {
        prio = (s8)(prio + 1);
    }

    u32 mult = 1u;
    u16 ability = *(volatile u16 *)(m + 0x20u);
    if (!weather_suppressed()) {
        if (ability == 33u && (BATTLE_WEATHER & WEATHER_RAIN_MASK) != 0u)
            mult = 2u;
        else if (ability == 34u && (BATTLE_WEATHER & WEATHER_SUN_MASK) != 0u)
            mult = 2u;
    }
    u32 raw_spd = (u32)(*(volatile u16 *)(m + 0x06u)) * mult;
    u8 stage = m[0x1Bu];
    if (stage > 12u)
        stage = 6u;
    u32 spd = FN_UDIV32(raw_spd * STAT_STAGE_RATIOS[2u * stage], STAT_STAGE_RATIOS[2u * stage + 1u]);

    u16 item = *(volatile u16 *)(m + 0x30u);
    u8 hold_eff, hold_param;
    if (item == 0xAFu) {
        hold_eff = DISABLE_STRUCTS[28u * b + 7u];
        hold_param = DISABLE_STRUCTS[28u * b + 0x1Au];
    } else {
        hold_eff = FN_GET_HOLD_EFFECT(item);
        hold_param = FN_GET_HOLD_PARAM(item);
    }
    if ((BATTLE_TYPE_FLAGS & 0x02u) == 0u) {
        /* Em batalha normal, Quick Claw e Macho Brace seguem a logica nativa. */
    }
    if (hold_eff == 0x18u)
        spd >>= 1;
    if ((*(volatile u32 *)(m + 0x50u) & 0x40u) != 0u && ability != 62u)
        spd >>= 2;
    u8 side = FN_GET_SIDE(b);
    if (V8_STATE->tailwind_turns[side] > 0u)
        spd <<= 1;

    u8 qc = 0u;
    if (hold_eff == 0x1Au) {
        u32 thresh = FN_UDIV32((u32)hold_param * 0xFFFFu, 100u);
        if ((u32)RANDOM_TURN_NUMBER < thresh)
            qc = 1u;
    }

    *prio_out = prio;
    *qc_out = qc;
    *spd_out = spd;
}

static u8 bank_strikes_before(s8 p1, u8 qc1, u32 s1, s8 p2, u8 qc2, u32 s2)
{
    if (p1 != p2)
        return (p1 > p2) ? 1u : 0u;
    if (qc1 != qc2)
        return (qc1 > qc2) ? 1u : 0u;
    if (s1 != s2) {
        if (V8_STATE->trick_room_turns > 0u)
            return (s1 < s2) ? 1u : 0u;
        return (s1 > s2) ? 1u : 0u;
    }
    return (u8)(FN_RANDOM() & 1u);
}

void hook_set_turn_order_v8(void)
{
    ORIG_SET_TURN_ORDER();

    if (V8_STATE->trick_room_turns == 0u
        && V8_STATE->tailwind_turns[0] == 0u
        && V8_STATE->tailwind_turns[1] == 0u
        && !(V8_STATE->terrain_type == TERRAIN_GRASSY && V8_STATE->terrain_turns > 0u)) {
        return;
    }
    /* Nao interferir em Safari Zone (0x80) ou batalha com fuga prioritaria. */
    if ((BATTLE_TYPE_FLAGS & 0x80u) != 0u)
        return;

    u32 count = BATTLERS_COUNT;
    if (count <= 1u || count > 4u)
        return;

    s8 prio[4];
    u8 qc[4];
    u32 spd[4];
    for (u32 i = 0u; i < count; ++i) {
        if (ACTIONS_BY_TURN[i] == 0u)
            compute_turn_metrics(BATTLER_BY_TURN[i], &prio[i], &qc[i], &spd[i]);
    }

    for (u32 i = 0u; i + 1u < count; ++i) {
        if (ACTIONS_BY_TURN[i] == 1u || ACTIONS_BY_TURN[i] == 2u || ACTIONS_BY_TURN[i] == 3u)
            continue;
        for (u32 j = i + 1u; j < count; ++j) {
            if (ACTIONS_BY_TURN[j] == 1u || ACTIONS_BY_TURN[j] == 2u || ACTIONS_BY_TURN[j] == 3u)
                continue;
            if (ACTIONS_BY_TURN[i] == 0u && ACTIONS_BY_TURN[j] == 0u) {
                if (bank_strikes_before(prio[j], qc[j], spd[j], prio[i], qc[i], spd[i])) {
                    u8 tb = BATTLER_BY_TURN[i];
                    BATTLER_BY_TURN[i] = BATTLER_BY_TURN[j];
                    BATTLER_BY_TURN[j] = tb;
                    s8 tp = prio[i]; prio[i] = prio[j]; prio[j] = tp;
                    u8 tq = qc[i];   qc[i]   = qc[j];   qc[j]   = tq;
                    u32 ts = spd[i]; spd[i]  = spd[j];  spd[j]  = ts;
                }
            }
        }
    }
}

/* ===================== Fim de Turno (Cura e Timers) ===================== */

static u8 has_any_v8_endturn_effect(void)
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
        || V8_STATE->aurora_veil_turns[1] > 0u) {
        return 1u;
    }
    for (u32 b = 0u; b < 4u; ++b) {
        if (V8_STATE->magnet_rise_turns[b] > 0u)
            return 1u;
    }
    return 0u;
}

void hook_endturn_v8(void)
{
    if (!has_any_v8_endturn_effect()) {
        V8_STATE->endturn_step = 0u;
        BATTLE_MAIN_FUNC = 0x08053221u;
        ORIG_BATTLE_TURN_PASSED();
        return;
    }

    if (CONTROLLER_EXEC_FLAGS != 0u)
        return;

    /* Impede sono por Yawn ao fim do turno em Electric/Misty Terrain. */
    if ((V8_STATE->terrain_type == TERRAIN_ELECTRIC || V8_STATE->terrain_type == TERRAIN_MISTY)
        && V8_STATE->terrain_turns > 0u) {
        u32 cnt = BATTLERS_COUNT;
        if (cnt > 4u)
            cnt = 4u;
        for (u32 b = 0u; b < cnt; ++b) {
            if ((STATUSES3[b] & 0x0800u) != 0u && is_battler_grounded((u8)b))
                STATUSES3[b] &= ~0x1800u;
        }
    }

    if (BATTLE_OUTCOME != 0u) {
        V8_STATE->endturn_step = 0u;
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
                    ((volatile u32 *)cb_stack)[depth - 1u] = 0x090C3019u;
            } else {
                BATTLE_MAIN_FUNC = 0x090C3019u;
            }
            return;
        }
        BATTLE_MAIN_FUNC = 0x090C3019u;
    }

    while (V8_STATE->endturn_step < 17u) {
        u8 step = V8_STATE->endturn_step++;

        /* Passos 0..3: cura de 1/16 de Grassy Terrain para battlers aterrados */
        if (step < 4u) {
            if (V8_STATE->terrain_type == TERRAIN_GRASSY
                && V8_STATE->terrain_turns > 0u
                && step < BATTLERS_COUNT
                && (ABSENT_BATTLERS & (1u << step)) == 0u
                && is_battler_grounded(step)
                && !is_heal_blocked(step)) {
                volatile u8 *m = BATTLE_MONS + 0x5Cu * step;
                u16 hp = *(volatile u16 *)(m + 0x2Au);
                u16 max_hp = *(volatile u16 *)(m + 0x2Eu);
                if (hp > 0u && hp < max_hp) {
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

        /* Passo 4: expiracao do clima Snow (sem dano residual) */
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

        /* Passos 5..6: Tailwind por lado */
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

        /* Passos 7..8: Aurora Veil por lado */
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

        /* Passo 9: Terreno ativo */
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

        /* Passo 10: Gravity */
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

        /* Passo 11: Trick Room */
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

        /* Passo 12: Wonder Room */
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

        /* Passos 13..16: Magnet Rise por battler */
        if (step >= 13u && step <= 16u) {
            u8 b = (u8)(step - 13u);
            if (b < BATTLERS_COUNT && V8_STATE->magnet_rise_turns[b] > 0u) {
                if (V8_STATE->magnet_rise_pid[b] != mon_tag(b)) {
                    V8_STATE->magnet_rise_turns[b] = 0u;
                } else {
                    V8_STATE->magnet_rise_turns[b]--;
                    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
                    if (V8_STATE->magnet_rise_turns[b] == 0u
                        && (*(volatile u16 *)(m + 0x2Au)) > 0u) {
                        SCRIPTING_BATTLER = b;
                        start_endturn_script(BS_V8_ENDTURN_MSGS + 8u * 7u);
                        return;
                    }
                }
            }
            continue;
        }
    }

    V8_STATE->endturn_step = 0u;
    BATTLE_MAIN_FUNC = 0x08053221u;
    ORIG_BATTLE_TURN_PASSED();
}

/* ================== Comandos da Tabela Relocada (v8) ==================== */

void hook_attackcanceler_v8(void)
{
    const u8 *before = CURR_INSTR;
    PREV_ATTACKCANCELER_V7();
    if (CURR_INSTR != before + 1)
        return;

    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;

    /* Gravity impede movimentos aereos/salto/Splash/Magnet Rise. */
    if (V8_STATE->gravity_turns > 0u && is_gravity_blocked_move(move)) {
        V7_STATE->passed_canceler_mask &= (u8)~(1u << atk);
        CURR_INSTR = BS_V8_GRAVITY_CANCEL;
        return;
    }

    /* Psychic Terrain bloqueia golpes de prioridade >0 contra oponentes aterrados. */
    if (V8_STATE->terrain_type == TERRAIN_PSYCHIC
        && V8_STATE->terrain_turns > 0u
        && move > 0u && move < 822u
        && FN_GET_SIDE(atk) != FN_GET_SIDE(tgt)
        && is_battler_grounded(tgt)) {
        const u8 *rec = MOVE_TABLE + 12u * move;
        s8 prio = (s8)rec[7];
        u8 mtarget = rec[6];
        if (prio > 0 && (mtarget & 0x50u) == 0u) {
            V7_STATE->passed_canceler_mask &= (u8)~(1u << atk);
            CURR_INSTR = BS_V8_PTERRAIN_CANCEL;
            return;
        }
    }
}

void hook_accuracycheck_v8(void)
{
    const u8 *instr = CURR_INSTR;
    u16 move_arg = read_u16_unaligned(instr + 5);
    u16 move = (move_arg == 0u) ? CURRENT_MOVE : move_arg;

    u8 snow_blizzard = (move == 59u && is_snow_or_hail_active()) ? 1u : 0u;
    if (!snow_blizzard && V8_STATE->gravity_turns == 0u) {
        ORIG_ACCURACYCHECK();
        return;
    }
    if (move_arg >= 0xFFFEu || (BATTLE_TYPE_FLAGS & 0x10010u) != 0u) {
        ORIG_ACCURACYCHECK();
        return;
    }

    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    /* Deixa Protect, semi-invulnerabilidade, Lock-On e acc==0 para a rotina nativa. */
    if ((PROTECT_STRUCTS[16u * tgt] & 0x01u) != 0u
        || (STATUSES3[tgt] & 0x000400F8u) != 0u
        || move >= 822u
        || MOVE_TABLE[12u * move + 3u] == 0u) {
        ORIG_ACCURACYCHECK();
        return;
    }
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    if (*(volatile u16 *)(a + 0x20u) == 99u || *(volatile u16 *)(t + 0x20u) == 99u) {
        ORIG_ACCURACYCHECK();
        return;
    }

    if (snow_blizzard) {
        MOVE_RESULT_FLAGS &= (u8)~0x01u;
        CURR_INSTR = instr + 7;
        return;
    }

    /* Gravity ativa: multiplica a precisao calculada por 5/3 (~1,67x). */
    s32 buff = (s32)a[0x1Eu] + 6 - (s32)t[0x1Fu];
    if ((*(volatile u32 *)(t + 0x54u) & 0x20000000u) != 0u && a[0x1Eu] >= t[0x1Fu])
        buff = (s32)a[0x1Eu];
    if (buff < 0)
        buff = 0;
    else if (buff > 12)
        buff = 12;

    u32 acc = MOVE_TABLE[12u * move + 3u];
    u32 calc = FN_UDIV32(acc * ACC_STAGE_RATIOS[2u * (u32)buff], ACC_STAGE_RATIOS[2u * (u32)buff + 1u]);
    if (*(volatile u16 *)(a + 0x20u) == 14u)
        calc = FN_UDIV32(calc * 130u, 100u);
    if (*(volatile u16 *)(a + 0x20u) == 55u && CATEGORY_TABLE[move] == 0u)
        calc = FN_UDIV32(calc * 80u, 100u);

    u16 t_item = *(volatile u16 *)(t + 0x30u);
    u8 t_heff = (t_item == 0xAFu) ? DISABLE_STRUCTS[28u * tgt + 7u] : FN_GET_HOLD_EFFECT(t_item);
    u8 t_hprm = (t_item == 0xAFu) ? DISABLE_STRUCTS[28u * tgt + 0x1Au] : FN_GET_HOLD_PARAM(t_item);
    POT_ITEM_BATTLER = tgt;
    if (t_heff == 0x16u && t_hprm < 100u)
        calc = FN_UDIV32(calc * (100u - t_hprm), 100u);

    calc = FN_UDIV32(calc * 5u, 3u);
    if ((FN_UMOD32(FN_RANDOM(), 100u) + 1u) > calc) {
        MOVE_RESULT_FLAGS |= 0x01u;
        CURR_INSTR = (const u8 *)read_u32_unaligned(instr + 1);
    } else {
        CURR_INSTR = instr + 7;
    }
}

void hook_damage_v8(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    volatile u8 *bstruct = BATTLE_STRUCT_PTR;

    /* Sinergias de BP e tipo dinamico com Terrenos antes do calculo base. */
    if (V8_STATE->terrain_turns > 0u) {
        u8 ttype = V8_STATE->terrain_type;
        if (move == 701u && ttype == TERRAIN_PSYCHIC && is_battler_grounded(atk)) {
            DYNAMIC_POWER = 120u;
        } else if (move == 705u && ttype == TERRAIN_ELECTRIC && is_battler_grounded(tgt)) {
            DYNAMIC_POWER = 140u;
        } else if (move == 706u && is_battler_grounded(atk)) {
            DYNAMIC_POWER = 100u;
            u8 dtype = (ttype == TERRAIN_ELECTRIC) ? 13u
                     : (ttype == TERRAIN_GRASSY)   ? 12u
                     : (ttype == TERRAIN_MISTY)    ? 18u : 14u;
            bstruct[0x13u] = (u8)(0x40u | dtype);
        } else if (move == 783u && ttype == TERRAIN_ELECTRIC) {
            DYNAMIC_POWER = 120u;
        } else if (move == 810u && ttype == TERRAIN_MISTY && is_battler_grounded(atk)) {
            DYNAMIC_POWER = 150u;
        }
    }

    /* Wonder Room: troca temporaria de Defense e Sp. Def brutos. */
    u16 a_def = *(volatile u16 *)(a + 0x04u);
    u16 a_spd = *(volatile u16 *)(a + 0x0Au);
    u16 t_def = *(volatile u16 *)(t + 0x04u);
    u16 t_spd = *(volatile u16 *)(t + 0x0Au);
    if (V8_STATE->wonder_room_turns > 0u) {
        *(volatile u16 *)(a + 0x04u) = a_spd;
        *(volatile u16 *)(a + 0x0Au) = a_def;
        if (atk != tgt) {
            *(volatile u16 *)(t + 0x04u) = t_spd;
            *(volatile u16 *)(t + 0x0Au) = t_def;
        }
    }

    /* Snow: +50% na Defesa fisica efetiva de Pokemon tipo Gelo (15). */
    u16 pre_snow_def = *(volatile u16 *)(t + 0x04u);
    if (is_snow_active() && (t[0x22u] == 15u || t[0x23u] == 15u)) {
        u32 boosted = ((u32)pre_snow_def * 3u) >> 1;
        if (boosted > 0xFFFFu)
            boosted = 0xFFFFu;
        *(volatile u16 *)(t + 0x04u) = (u16)boosted;
    }

    /* Aurora Veil: aplica a reducao nativa de Reflect/Light Screen sem empilhar. */
    u8 t_side = FN_GET_SIDE(tgt);
    u16 orig_side = SIDE_STATUSES[t_side];
    if (V8_STATE->aurora_veil_turns[t_side] > 0u)
        SIDE_STATUSES[t_side] = (u16)(orig_side | 0x0003u);

    PREV_DAMAGE_V7();

    SIDE_STATUSES[t_side] = orig_side;
    *(volatile u16 *)(t + 0x04u) = pre_snow_def;
    if (V8_STATE->wonder_room_turns > 0u) {
        *(volatile u16 *)(a + 0x04u) = a_def;
        *(volatile u16 *)(a + 0x0Au) = a_spd;
        if (atk != tgt) {
            *(volatile u16 *)(t + 0x04u) = t_def;
            *(volatile u16 *)(t + 0x0Au) = t_spd;
        }
    }

    /* Multiplicadores globais de Terreno (SV Gen 9: 1,3x e reducoes 0,5x). */
    if (V8_STATE->terrain_turns > 0u && BATTLE_MOVE_DMG > 0 && move > 0u && move < 822u) {
        u8 mtype = (bstruct[0x13u] & 0x40u)
            ? (bstruct[0x13u] & 0x3Fu)
            : MOVE_TABLE[12u * move + 2u];
        u8 ttype = V8_STATE->terrain_type;
        u32 dmg = (u32)BATTLE_MOVE_DMG;
        u8 changed = 0u;

        if (ttype == TERRAIN_ELECTRIC && mtype == 13u && is_battler_grounded(atk)) {
            dmg = FN_UDIV32(dmg * 13u, 10u);
            changed = 1u;
        } else if (ttype == TERRAIN_GRASSY) {
            if (mtype == 12u && is_battler_grounded(atk)) {
                dmg = FN_UDIV32(dmg * 13u, 10u);
                changed = 1u;
            }
            if ((move == 89u || move == 222u || move == 519u) && is_battler_grounded(tgt)) {
                dmg >>= 1;
                changed = 1u;
            }
        } else if (ttype == TERRAIN_PSYCHIC && mtype == 14u && is_battler_grounded(atk)) {
            dmg = FN_UDIV32(dmg * 13u, 10u);
            changed = 1u;
        } else if (ttype == TERRAIN_MISTY && mtype == 16u && is_battler_grounded(tgt)) {
            dmg >>= 1;
            changed = 1u;
        }

        if (changed) {
            if (dmg < 1u)
                dmg = 1u;
            BATTLE_MOVE_DMG = (s32)dmg;
        }
    }
}

void hook_typecalc_v8(void)
{
    u16 move = CURRENT_MOVE;
    u8 tgt = TARGET & 3u;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    volatile u8 *bstruct = BATTLE_STRUCT_PTR;
    u8 mtype = (bstruct[0x13u] & 0x40u)
        ? (bstruct[0x13u] & 0x3Fu)
        : ((move < 822u) ? MOVE_TABLE[12u * move + 2u] : 0u);

    if (mtype == 4u) {
        /* Magnet Rise concede imunidade a Ground fora de Gravity/Ingrain. */
        if (V8_STATE->gravity_turns == 0u
            && (STATUSES3[tgt] & 0x00002000u) == 0u
            && is_magnet_risen(tgt)) {
            MOVE_RESULT_FLAGS = (u8)((MOVE_RESULT_FLAGS & ~0x06u) | 0x08u);
            CURR_INSTR = CURR_INSTR + 1;
            return;
        }

        /* Gravity/Ingrain remove imunidade de Flying (2) e Levitate (26) a Ground. */
        if (V8_STATE->gravity_turns > 0u || (STATUSES3[tgt] & 0x00002000u) != 0u) {
            u8 orig_t1 = t[0x22u];
            u8 orig_t2 = t[0x23u];
            u16 orig_ab = *(volatile u16 *)(t + 0x20u);
            if (orig_t1 == 2u)
                t[0x22u] = (orig_t2 != 2u) ? orig_t2 : 0u;
            if (orig_t2 == 2u)
                t[0x23u] = t[0x22u];
            if (orig_ab == 26u)
                *(volatile u16 *)(t + 0x20u) = 0u;

            ORIG_TYPECALC();

            t[0x22u] = orig_t1;
            t[0x23u] = orig_t2;
            *(volatile u16 *)(t + 0x20u) = orig_ab;
            return;
        }
    }

    ORIG_TYPECALC();
}

static u8 terrain_blocks_move_effect(void)
{
    if (V8_STATE->terrain_turns == 0u)
        return 0u;
    u8 eff = MOVE_EFFECT_BYTE & 0x3Fu;
    u8 bank = ((MOVE_EFFECT_BYTE & 0x40u) != 0u) ? (ATTACKER & 3u) : (TARGET & 3u);
    if (!is_battler_grounded(bank))
        return 0u;
    if (V8_STATE->terrain_type == TERRAIN_ELECTRIC && eff == 1u)
        return 1u;
    if (V8_STATE->terrain_type == TERRAIN_MISTY && eff >= 1u && eff <= 7u)
        return 1u;
    return 0u;
}

void hook_seteffect_chance_v8(void)
{
    if (terrain_blocks_move_effect()) {
        CURR_INSTR = CURR_INSTR + 1;
        return;
    }
    PREV_SETEFFECT_CH_V7();
}

void hook_seteffect_primary_v8(void)
{
    if (terrain_blocks_move_effect()) {
        if ((MOVE_EFFECT_BYTE & 0x40u) == 0u && CATEGORY_TABLE[CURRENT_MOVE] == 2u)
            CURR_INSTR = BS_V8_TERRAIN_BLOCK;
        else
            CURR_INSTR = CURR_INSTR + 1;
        return;
    }
    PREV_SETEFFECT_PR_V7();
}

void hook_seteffect_secondary_v8(void)
{
    if (terrain_blocks_move_effect()) {
        CURR_INSTR = CURR_INSTR + 1;
        return;
    }
    PREV_SETEFFECT_SC_V7();
}

void hook_jumpifcantmakeasleep_v8(void)
{
    const u8 *instr = CURR_INSTR;
    u8 tgt = TARGET & 3u;
    if (V8_STATE->terrain_turns > 0u
        && (V8_STATE->terrain_type == TERRAIN_ELECTRIC || V8_STATE->terrain_type == TERRAIN_MISTY)
        && is_battler_grounded(tgt)) {
        CURR_INSTR = (const u8 *)read_u32_unaligned(instr + 1);
        return;
    }
    ORIG_JUMPIFCANTSLEEP();
}

/* ==================== Armadilhas de Entrada (0x52) ====================== */

static u32 stealth_rock_mult32(u8 t1, u8 t2)
{
    u32 mult = 4u; /* 4/32 = 1/8 neutro */
    u8 types[2];
    u32 n = 1u;
    types[0] = t1;
    if (t2 != t1) {
        types[1] = t2;
        n = 2u;
    }
    for (u32 k = 0u; k < n; ++k) {
        const u8 *p = TYPE_EFFECT_TABLE;
        while (p[0] != 0xFFu) {
            if (p[0] == 0xFEu) {
                p += 3;
                continue;
            }
            if (p[0] == 5u && p[1] == types[k]) {
                if (p[2] == 20u)
                    mult <<= 1;
                else if (p[2] == 5u)
                    mult >>= 1;
                else if (p[2] == 0u)
                    return 0u;
                break;
            }
            p += 3;
        }
    }
    return mult;
}

void hook_switchineffects_v8(void)
{
    const u8 *instr = CURR_INSTR;
    u8 b = FN_GET_SCRIPT_BANK(instr[1]) & 3u;
    u32 tag = mon_tag(b);

    if (V8_STATE->switchin_hazard_step == 0u
        || V8_STATE->switchin_tag != tag
        || V8_STATE->switchin_bank != b) {
        V8_STATE->switchin_hazard_step = 0u;
        ORIG_SWITCHINEFFECTS();
        if (CURR_INSTR != instr + 2)
            return;
        V8_STATE->switchin_tag = tag;
        V8_STATE->switchin_bank = b;
    }

    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
    if ((ABSENT_BATTLERS & (1u << b)) != 0u || (*(volatile u16 *)(m + 0x2Au)) == 0u) {
        V8_STATE->switchin_hazard_step = 0u;
        V8_STATE->switchin_tag = 0u;
        CURR_INSTR = instr + 2;
        return;
    }

    u8 side = FN_GET_SIDE(b);
    while (V8_STATE->switchin_hazard_step < 4u) {
        u8 step = V8_STATE->switchin_hazard_step++;

        /* Passo 0: Spikes sob Gravity/Ingrain em Flying/Levitate ignorados pelo nativo */
        if (step == 0u) {
            u8 skipped_by_vanilla = (m[0x22u] == 2u || m[0x23u] == 2u
                                     || *(volatile u16 *)(m + 0x20u) == 26u) ? 1u : 0u;
            if (skipped_by_vanilla
                && (SIDE_STATUSES[side] & 0x0010u) != 0u
                && is_battler_grounded(b)) {
                u8 layers = SIDE_TIMERS[12u * side + 0x0Au];
                if (layers < 1u)
                    layers = 1u;
                else if (layers > 3u)
                    layers = 3u;
                u16 max_hp = *(volatile u16 *)(m + 0x2Eu);
                u32 dmg = FN_UDIV32(max_hp, (5u - layers) * 2u);
                if (dmg < 1u)
                    dmg = 1u;
                SCRIPTING_BATTLER = b;
                FAINTED_BATTLER = b;
                BATTLE_MOVE_DMG = (s32)dmg;
                MOVE_RESULT_FLAGS &= (u8)~0x29u;
                FN_BS_PUSH(instr);
                CURR_INSTR = BS_V8_HAZARD_SPIKES_G;
                return;
            }
            continue;
        }

        /* Passo 1: Stealth Rock (afeta aterrados e nao-aterrados) */
        if (step == 1u) {
            if (V8_STATE->stealth_rock[side] != 0u) {
                u32 mult = stealth_rock_mult32(m[0x22u], m[0x23u]);
                if (mult > 0u) {
                    u16 max_hp = *(volatile u16 *)(m + 0x2Eu);
                    u32 dmg = ((u32)max_hp * mult) >> 5;
                    if (dmg < 1u)
                        dmg = 1u;
                    SCRIPTING_BATTLER = b;
                    FAINTED_BATTLER = b;
                    BATTLE_MOVE_DMG = (s32)dmg;
                    MOVE_RESULT_FLAGS &= (u8)~0x29u;
                    FN_BS_PUSH(instr);
                    CURR_INSTR = BS_V8_HAZARD_SROCK;
                    return;
                }
            }
            continue;
        }

        /* Passo 2: Toxic Spikes (absorvido por Poison aterrado; 1=PSN, 2=TOX) */
        if (step == 2u) {
            u8 layers = V8_STATE->toxic_spikes[side];
            if (layers > 0u && is_battler_grounded(b)) {
                u8 t1 = m[0x22u], t2 = m[0x23u];
                if (t1 == 3u || t2 == 3u) {
                    V8_STATE->toxic_spikes[side] = 0u;
                    SCRIPTING_BATTLER = b;
                    FN_BS_PUSH(instr);
                    CURR_INSTR = BS_V8_TSPIKES_ABSORB;
                    return;
                }
                u16 ability = *(volatile u16 *)(m + 0x20u);
                u32 status1 = *(volatile u32 *)(m + 0x50u);
                u32 status2 = *(volatile u32 *)(m + 0x54u);
                u8 misty = (V8_STATE->terrain_type == TERRAIN_MISTY && V8_STATE->terrain_turns > 0u) ? 1u : 0u;
                if (t1 != 8u && t2 != 8u
                    && ability != 17u
                    && status1 == 0u
                    && (status2 & 0x01000000u) == 0u
                    && (SIDE_STATUSES[side] & 0x0020u) == 0u
                    && !misty) {
                    u32 new_st = (layers >= 2u) ? 0x80u : 0x08u;
                    *(volatile u32 *)(m + 0x50u) = new_st;
                    ACTIVE_BATTLER = b;
                    FN_EMIT_SET_MON_DATA(0u, 0x28u, 0u, 4u, (const void *)(m + 0x50u));
                    FN_MARK_BUFFER_EXEC(b);
                    EFFECT_BATTLER = b;
                    FN_BS_PUSH(instr);
                    CURR_INSTR = (layers >= 2u) ? BS_TOXIC_EFF : BS_POISON_EFF;
                    return;
                }
            }
            continue;
        }

        /* Passo 3: Sticky Web (-1 estagio de Velocidade para aterrados) */
        if (step == 3u) {
            if (V8_STATE->sticky_web[side] != 0u && is_battler_grounded(b)) {
                SCRIPTING_BATTLER = b;
                V8_STATE->saved_target = TARGET;
                TARGET = b;
                FN_BS_PUSH(instr);
                CURR_INSTR = BS_V8_STICKY_WEB_DROP;
                return;
            }
            continue;
        }
    }

    V8_STATE->switchin_hazard_step = 0u;
    V8_STATE->switchin_tag = 0u;
    CURR_INSTR = instr + 2;
}

void hook_sticky_web_restore_v8(void)
{
    TARGET = V8_STATE->saved_target;
}

/* ============= Rapid Spin / Weather Ball / Brick Break / Cura =========== */

void hook_rapidspinfree_v8(void)
{
    const u8 *before = CURR_INSTR;
    ORIG_RAPIDSPINFREE();

    u8 side = FN_GET_SIDE(ATTACKER & 3u);
    if (V8_STATE->stealth_rock[side] != 0u
        || V8_STATE->toxic_spikes[side] != 0u
        || V8_STATE->sticky_web[side] != 0u) {
        V8_STATE->stealth_rock[side] = 0u;
        V8_STATE->toxic_spikes[side] = 0u;
        V8_STATE->sticky_web[side] = 0u;
        if (CURR_INSTR == before + 1) {
            FN_BS_PUSH(before + 1);
            CURR_INSTR = BS_V8_RAPIDSPIN_CLEAR;
        }
    }
}

void hook_weatherball_v8(void)
{
    if (is_snow_active()) {
        SCRIPTING_DMG_MULT = 2u;
        BATTLE_STRUCT_PTR[0x13u] = (u8)(0x40u | 15u);
        CURR_INSTR = CURR_INSTR + 1;
        return;
    }
    ORIG_WEATHERBALL();
}

void hook_brickbreak_v8(void)
{
    ORIG_BRICKBREAK();
    u8 t_side = FN_GET_SIDE(TARGET & 3u);
    if (V8_STATE->aurora_veil_turns[t_side] > 0u) {
        V8_STATE->aurora_veil_turns[t_side] = 0u;
        SCRIPTING_ANIM_TURN = 1u;
    }
}

void hook_target_heal_prep_v8(void)
{
    u8 tgt = TARGET & 3u;
    if ((ABSENT_BATTLERS & (1u << tgt)) != 0u || is_heal_blocked(tgt)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    u16 hp = *(volatile u16 *)(t + 0x2Au);
    u16 max_hp = *(volatile u16 *)(t + 0x2Eu);
    if (hp == 0u || hp >= max_hp) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    s32 heal;
    if (CURRENT_MOVE == 621u
        && V8_STATE->terrain_type == TERRAIN_GRASSY
        && V8_STATE->terrain_turns > 0u) {
        heal = (s32)FN_UDIV32((u32)max_hp * 2u, 3u);
    } else {
        heal = (s32)((max_hp + 1u) >> 1);
    }
    if (heal < 1)
        heal = 1;
    BATTLE_MOVE_DMG = -heal;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
}

void hook_shore_up_prep_v8(void)
{
    u8 atk = ATTACKER & 3u;
    if (is_heal_blocked(atk)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    u16 hp = *(volatile u16 *)(a + 0x2Au);
    u16 max_hp = *(volatile u16 *)(a + 0x2Eu);
    if (hp == 0u || hp >= max_hp) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    s32 heal;
    if (!weather_suppressed() && (BATTLE_WEATHER & WEATHER_SAND_MASK) != 0u)
        heal = (s32)FN_UDIV32((u32)max_hp * 2u, 3u);
    else
        heal = (s32)((max_hp + 1u) >> 1);
    if (heal < 1)
        heal = 1;
    TARGET = atk;
    BATTLE_MOVE_DMG = -heal;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
}

/* ================ Golpes de Status de Campo (eff 236..242) ============== */

/* Indices das caudas BS_V8_STATUS_TAILS + 12 * idx:
 *  0: STR_SNOW_STARTED (0x0182)
 *  1: STR_TAILWIND_BLEW (0x0184)
 *  2: STR_AURORA_VEIL_SET (0x0186)
 *  3: STR_ELECTRIC_TERRAIN (0x0188)
 *  4: STR_GRASSY_TERRAIN (0x0189)
 *  5: STR_PSYCHIC_TERRAIN (0x018A)
 *  6: STR_MISTY_TERRAIN (0x018B)
 *  7: STR_TRICK_ROOM_SET (0x018D)
 *  8: STR_TRICK_ROOM_ENDED (0x018E)
 *  9: STR_WONDER_ROOM_SET (0x018F)
 * 10: STR_WONDER_ROOM_ENDED (0x0190)
 * 11: STR_GRAVITY_SET (0x0191)
 * 12: STR_STEALTH_ROCK_SET (0x0195)
 * 13: STR_TOXIC_SPIKES_SET (0x0197)
 * 14: STR_STICKY_WEB_SET (0x0199)
 * 15: STR_MAGNET_RISE_SET (0x019B)
 * 16: STR_COURT_CHANGE (0x019E)
 */
void hook_field_status_prep_v8(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 side = FN_GET_SIDE(atk);
    u8 opp = (u8)(side ^ 1u);

    if (move == 773u) {
        if ((BATTLE_WEATHER & WEATHER_SNOW_BIT) != 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 366u) {
        if (V8_STATE->tailwind_turns[side] > 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 649u) {
        if (!is_snow_or_hail_active() || V8_STATE->aurora_veil_turns[side] > 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 599u) {
        if (V8_STATE->terrain_type == TERRAIN_ELECTRIC && V8_STATE->terrain_turns > 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 576u) {
        if (V8_STATE->terrain_type == TERRAIN_GRASSY && V8_STATE->terrain_turns > 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 633u) {
        if (V8_STATE->terrain_type == TERRAIN_PSYCHIC && V8_STATE->terrain_turns > 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 577u) {
        if (V8_STATE->terrain_type == TERRAIN_MISTY && V8_STATE->terrain_turns > 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 356u) {
        if (V8_STATE->gravity_turns > 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 445u) {
        if (V8_STATE->stealth_rock[opp] != 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 390u) {
        if (V8_STATE->toxic_spikes[opp] >= 2u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 560u) {
        if (V8_STATE->sticky_web[opp] != 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
    } else if (move == 393u) {
        if (V8_STATE->gravity_turns > 0u
            || (STATUSES3[atk] & 0x00002000u) != 0u
            || is_magnet_risen(atk)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
        }
    }
}

static void swap_u8(volatile u8 *a, volatile u8 *b)
{
    u8 t = *a;
    *a = *b;
    *b = t;
}

void hook_field_status_apply_v8(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 side = FN_GET_SIDE(atk);
    u8 opp = (u8)(side ^ 1u);
    u32 idx = 0u;

    if (move == 773u) {
        BATTLE_WEATHER = WEATHER_SNOW_BIT;
        WEATHER_DURATION = 5u;
        idx = 0u;
    } else if (move == 366u) {
        V8_STATE->tailwind_turns[side] = 4u;
        idx = 1u;
    } else if (move == 649u) {
        V8_STATE->aurora_veil_turns[side] = 5u;
        idx = 2u;
    } else if (move == 599u) {
        V8_STATE->terrain_type = TERRAIN_ELECTRIC;
        V8_STATE->terrain_turns = 5u;
        idx = 3u;
    } else if (move == 576u) {
        V8_STATE->terrain_type = TERRAIN_GRASSY;
        V8_STATE->terrain_turns = 5u;
        idx = 4u;
    } else if (move == 633u) {
        V8_STATE->terrain_type = TERRAIN_PSYCHIC;
        V8_STATE->terrain_turns = 5u;
        idx = 5u;
    } else if (move == 577u) {
        V8_STATE->terrain_type = TERRAIN_MISTY;
        V8_STATE->terrain_turns = 5u;
        idx = 6u;
    } else if (move == 433u) {
        if (V8_STATE->trick_room_turns > 0u) {
            V8_STATE->trick_room_turns = 0u;
            idx = 8u;
        } else {
            V8_STATE->trick_room_turns = 5u;
            idx = 7u;
        }
    } else if (move == 471u) {
        if (V8_STATE->wonder_room_turns > 0u) {
            V8_STATE->wonder_room_turns = 0u;
            idx = 10u;
        } else {
            V8_STATE->wonder_room_turns = 5u;
            idx = 9u;
        }
    } else if (move == 356u) {
        V8_STATE->gravity_turns = 5u;
        for (u32 b = 0u; b < 4u; ++b) {
            V8_STATE->magnet_rise_turns[b] = 0u;
            if ((STATUSES3[b] & 0x00000008u) != 0u) {
                STATUSES3[b] &= ~0x00000008u;
                volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
                *(volatile u32 *)(m + 0x54u) &= ~0x00001000u;
            }
        }
        idx = 11u;
    } else if (move == 445u) {
        V8_STATE->stealth_rock[opp] = 1u;
        idx = 12u;
    } else if (move == 390u) {
        V8_STATE->toxic_spikes[opp]++;
        idx = 13u;
    } else if (move == 560u) {
        V8_STATE->sticky_web[opp] = 1u;
        idx = 14u;
    } else if (move == 393u) {
        V8_STATE->magnet_rise_turns[atk] = 5u;
        V8_STATE->magnet_rise_pid[atk] = mon_tag(atk);
        idx = 15u;
    } else if (move == 681u) {
        /* Court Change: troca barreiras, salvaguardas, Tailwind e armadilhas entre os lados. */
        const u16 mask = 0x0133u; /* Reflect | LightScreen | Spikes | Safeguard | Mist */
        u16 s0 = SIDE_STATUSES[0], s1 = SIDE_STATUSES[1];
        SIDE_STATUSES[0] = (u16)((s0 & ~mask) | (s1 & mask));
        SIDE_STATUSES[1] = (u16)((s1 & ~mask) | (s0 & mask));
        for (u32 k = 0u; k < 8u; ++k)
            swap_u8(&SIDE_TIMERS[k], &SIDE_TIMERS[12u + k]);
        swap_u8(&SIDE_TIMERS[0x0Au], &SIDE_TIMERS[12u + 0x0Au]);
        swap_u8(&V8_STATE->tailwind_turns[0], &V8_STATE->tailwind_turns[1]);
        swap_u8(&V8_STATE->aurora_veil_turns[0], &V8_STATE->aurora_veil_turns[1]);
        swap_u8(&V8_STATE->stealth_rock[0], &V8_STATE->stealth_rock[1]);
        swap_u8(&V8_STATE->toxic_spikes[0], &V8_STATE->toxic_spikes[1]);
        swap_u8(&V8_STATE->sticky_web[0], &V8_STATE->sticky_web[1]);
        idx = 16u;
    }

    CURR_INSTR = BS_V8_STATUS_TAILS + 12u * idx;
}

void hook_defog_evasion_check_v8(void)
{
    const u8 *p = CURR_INSTR;
    u32 skip = read_u32_unaligned(p);
    volatile u8 *t = BATTLE_MONS + 0x5Cu * (TARGET & 3u);
    if ((*(volatile u32 *)(t + 0x54u) & 0x01000000u) != 0u) {
        CURR_INSTR = (const u8 *)skip;
        return;
    }
    CURR_INSTR = p + 4;
}

void hook_defog_clear_v8(void)
{
    u8 t_side = FN_GET_SIDE(TARGET & 3u);
    u8 cleared = 0u;

    if ((SIDE_STATUSES[t_side] & 0x0123u) != 0u) {
        SIDE_STATUSES[t_side] &= (u16)~0x0123u;
        for (u32 k = 0u; k < 8u; ++k)
            SIDE_TIMERS[12u * t_side + k] = 0u;
        cleared = 1u;
    }
    if (V8_STATE->aurora_veil_turns[t_side] > 0u) {
        V8_STATE->aurora_veil_turns[t_side] = 0u;
        cleared = 1u;
    }
    for (u32 s = 0u; s < 2u; ++s) {
        if ((SIDE_STATUSES[s] & 0x0010u) != 0u) {
            SIDE_STATUSES[s] &= (u16)~0x0010u;
            SIDE_TIMERS[12u * s + 0x0Au] = 0u;
            cleared = 1u;
        }
        if (V8_STATE->stealth_rock[s] != 0u) {
            V8_STATE->stealth_rock[s] = 0u;
            cleared = 1u;
        }
        if (V8_STATE->toxic_spikes[s] != 0u) {
            V8_STATE->toxic_spikes[s] = 0u;
            cleared = 1u;
        }
        if (V8_STATE->sticky_web[s] != 0u) {
            V8_STATE->sticky_web[s] = 0u;
            cleared = 1u;
        }
    }
    if (V8_STATE->terrain_turns > 0u) {
        V8_STATE->terrain_type = TERRAIN_NONE;
        V8_STATE->terrain_turns = 0u;
        cleared = 1u;
    }

    if (!cleared)
        CURR_INSTR = BS_MOVE_END;
}

static u8 any_tidy_up_targets(void)
{
    for (u32 s = 0u; s < 2u; ++s) {
        if ((SIDE_STATUSES[s] & 0x0010u) != 0u
            || V8_STATE->stealth_rock[s] != 0u
            || V8_STATE->toxic_spikes[s] != 0u
            || V8_STATE->sticky_web[s] != 0u) {
            return 1u;
        }
    }
    u32 cnt = BATTLERS_COUNT;
    if (cnt > 4u)
        cnt = 4u;
    for (u32 b = 0u; b < cnt; ++b) {
        volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
        if ((*(volatile u32 *)(m + 0x54u) & 0x01000000u) != 0u)
            return 1u;
    }
    return 0u;
}

void hook_tidy_up_check_v8(void)
{
    V8_STATE->pending_tail_idx = 0u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * (ATTACKER & 3u);
    if (!any_tidy_up_targets() && (s8)a[0x19u] >= 12 && (s8)a[0x1Bu] >= 12)
        CURR_INSTR = BS_BUT_IT_FAILED;
}

void hook_tidy_up_clear_v8(void)
{
    const u8 *p = CURR_INSTR;
    u32 boost_step = read_u32_unaligned(p);

    for (u32 s = 0u; s < 2u; ++s) {
        if ((SIDE_STATUSES[s] & 0x0010u) != 0u) {
            SIDE_STATUSES[s] &= (u16)~0x0010u;
            SIDE_TIMERS[12u * s + 0x0Au] = 0u;
            V8_STATE->pending_tail_idx = 1u;
        }
        if (V8_STATE->stealth_rock[s] != 0u) {
            V8_STATE->stealth_rock[s] = 0u;
            V8_STATE->pending_tail_idx = 1u;
        }
        if (V8_STATE->toxic_spikes[s] != 0u) {
            V8_STATE->toxic_spikes[s] = 0u;
            V8_STATE->pending_tail_idx = 1u;
        }
        if (V8_STATE->sticky_web[s] != 0u) {
            V8_STATE->sticky_web[s] = 0u;
            V8_STATE->pending_tail_idx = 1u;
        }
    }
    u32 cnt = BATTLERS_COUNT;
    if (cnt > 4u)
        cnt = 4u;
    for (u32 b = 0u; b < cnt; ++b) {
        volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
        if ((*(volatile u32 *)(m + 0x54u) & 0x01000000u) != 0u) {
            *(volatile u32 *)(m + 0x54u) &= ~0x01000000u;
            DISABLE_STRUCTS[28u * b + 0x0Au] = 0u;
            V8_STATE->pending_tail_idx = 1u;
            SCRIPTING_BATTLER = (u8)b;
            FN_BS_PUSH(p - 5);
            CURR_INSTR = BS_V8_SUB_FADE;
            return;
        }
    }

    if (V8_STATE->pending_tail_idx == 0u)
        CURR_INSTR = (const u8 *)boost_step;
    else
        CURR_INSTR = p + 4;
}

void hook_chilly_reception_snow_v8(void)
{
    const u8 *p = CURR_INSTR;
    u32 pivot_step = read_u32_unaligned(p);
    if ((BATTLE_WEATHER & WEATHER_SNOW_BIT) != 0u) {
        CURR_INSTR = (const u8 *)pivot_step;
        return;
    }
    BATTLE_WEATHER = WEATHER_SNOW_BIT;
    WEATHER_DURATION = 5u;
    CURR_INSTR = p + 4;
}

void hook_hazard_hit_apply_v8(void)
{
    if ((MOVE_RESULT_FLAGS & 0x29u) != 0u) {
        CURR_INSTR = BS_MOVE_END;
        return;
    }
    u8 opp = (u8)(FN_GET_SIDE(ATTACKER & 3u) ^ 1u);
    if (CURRENT_MOVE == 723u) {
        /* Stone Axe: planta Stealth Rock no lado oposto se ainda nao houver. */
        if (V8_STATE->stealth_rock[opp] != 0u) {
            CURR_INSTR = BS_MOVE_END;
            return;
        }
        V8_STATE->stealth_rock[opp] = 1u;
        CURR_INSTR = BS_V8_STATUS_TAILS + 12u * 12u;
        return;
    }
    if (CURRENT_MOVE == 738u) {
        /* Ceaseless Edge: adiciona 1 camada de Spikes (ate 3) no lado oposto. */
        u8 layers = SIDE_TIMERS[12u * opp + 0x0Au];
        if (layers >= 3u) {
            CURR_INSTR = BS_MOVE_END;
            return;
        }
        SIDE_TIMERS[12u * opp + 0x0Au] = (u8)(layers + 1u);
        SIDE_STATUSES[opp] |= 0x0010u;
        return;
    }
    CURR_INSTR = BS_MOVE_END;
}

void hook_mortal_spin_check_v8(void)
{
    volatile u8 *a = BATTLE_MONS + 0x5Cu * (ATTACKER & 3u);
    if ((MOVE_RESULT_FLAGS & 0x29u) != 0u || (*(volatile u16 *)(a + 0x2Au)) == 0u)
        CURR_INSTR = BS_MOVE_END;
}
