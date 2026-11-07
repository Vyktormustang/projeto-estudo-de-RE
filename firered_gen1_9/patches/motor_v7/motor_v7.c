/* Rotinas auxiliares de batalha do motor_v7 (ARM7TDMI / Thumb).
 *
 * Agrupa quatro familias mecanicas autocontidas sobre o motor_v6:
 *  1. Troca automatica pos-golpe (Pivot): U-turn (369), Volt Switch (517),
 *     Flip Turn (708) e Parting Shot (571).
 *  2. Suporte a aliado em batalhas em dupla: Coaching (816) e Dragon Cheer
 *     (818, +1 estagio critico geral ou +2 se o aliado for tipo Dragao).
 *  3. Historico de turno e falha anterior: Burning Jealousy (813), Lash Out
 *     (814), Temper Flare (815) + Stomping Tantrum (653), Alluring Voice (819)
 *     e Upper Hand (821).
 *  4. Bloqueio temporario de cura (2 turnos) e cura direcionada/aliada:
 *     Psychic Noise (820), Heal Pulse (504), Floral Healing (621) e Life Dew
 *     (696).
 *
 * Limitacoes conhecidas e documentadas:
 *  - Movimentos sonoros novos (Alluring Voice, Psychic Noise, Dragon Cheer,
 *    Parting Shot) ainda nao interagem com Soundproof/Liquid Voice/Throat
 *    Spray nem ignoram Substitute quando aplicavel em SV.
 *  - Meteor Beam/Geomancy nao consomem Power Herb (item ausente na base).
 *  - Trocas de pivot nao interagem com Emergency Exit/Wimp Out/Eject Button/
 *    Red Card/Pursuit moderno (ausentes na base).
 */
typedef unsigned char u8;
typedef signed char s8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef int s32;

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

#define V7_STATE              ((volatile struct V7BattleState *)0x0203FC00u)

#define BATTLE_TYPE_FLAGS     (*(volatile u32 *)0x02020374u)
#define BATTLERS_COUNT        (*(volatile u8 *)0x020213F4u)
#define PARTY_INDEXES         ((volatile u16 *)0x020213F8u)
#define ACTIONS_BY_TURN       ((volatile u8 *)0x02021404u)
#define BATTLER_BY_TURN       ((volatile u8 *)0x02021408u)
#define CURR_TURN_ACTION_NUM  (*(volatile u8 *)0x0202140Cu)
#define BATTLE_MONS           ((volatile u8 *)0x02021410u)
#define CURRENT_MOVE          (*(volatile u16 *)0x02021586u)
#define BATTLE_MOVE_DMG       (*(volatile s32 *)0x0202158Cu)
#define ATTACKER              (*(volatile u8 *)0x020215A8u)
#define TARGET                (*(volatile u8 *)0x020215A9u)
#define EFFECT_BATTLER        (*(volatile u8 *)0x020215ACu)
#define ABSENT_BATTLERS       (*(volatile u8 *)0x020215ADu)
#define CRIT_MULTIPLIER       (*(volatile u8 *)0x020215AEu)
#define CURR_INSTR            (*(const u8 *volatile *)0x020215B0u)
#define CHOSEN_ACTION         ((volatile u8 *)0x020215B8u)
#define CHOSEN_MOVE           ((volatile u16 *)0x02021600u)
#define MOVE_RESULT_FLAGS     (*(volatile u8 *)0x02021608u)
#define HIT_MARKER            (*(volatile u32 *)0x0202160Cu)
#define SIDE_STATUSES         ((volatile u16 *)0x0202161Cu)
#define STATUSES3             ((volatile u32 *)0x02021638u)
#define MOVE_EFFECT_BYTE      (*(volatile u8 *)0x020216C3u)
#define BATTLE_OUTCOME        (*(volatile u8 *)0x020216C8u)
#define LOCKED_MOVES          ((volatile u16 *)0x020216CCu)
#define DYNAMIC_POWER         (*(volatile u16 *)0x02021792u)
#define DISABLE_STRUCTS       ((volatile u8 *)0x02021798u)
#define MOVEEND_STATE         (*(volatile u8 *)0x0202181Cu)
#define BATTLE_STRUCT_PTR     (*(const u8 *volatile *)0x0202182Cu)

#define ENEMY_PARTY           ((const u8 *)0x0203A734u)
#define PLAYER_PARTY          ((const u8 *)0x0203A98Cu)

#define MOVE_TABLE            ((const u8 *)0x09000000u)
#define CRIT_CHANCE_TABLE     ((const u16 *)0x08209C04u)

#define BS_HEAL_BLOCK_CANCEL  ((const u8 *)0x090BF000u)
#define BS_FINISH_MOVEEND     ((const u8 *)0x081853FCu)
#define BS_MOVE_END           ((const u8 *)0x081853F6u)
#define BS_BUT_IT_FAILED      ((const u8 *)0x0818689Au)

#define ORIG_BATTLE_INIT      ((void (*)(void))0x08052725u)
#define ORIG_TURN_START       ((void (*)(void))0x080544B9u)
#define ORIG_ATTACKCANCELER   ((void (*)(void))0x08057A0Du)
#define ORIG_CRITCALC         ((void (*)(void))0x080584D1u)
#define PREV_DAMAGE_V6        ((void (*)(void))0x090BE001u)
#define ORIG_HEALTHBAR        ((void (*)(void))0x080593EDu)
#define ORIG_DATAHP           ((void (*)(void))0x080594ADu)
#define ORIG_SETEFFECT_CHANCE ((void (*)(void))0x0805A8CDu)
#define ORIG_SETEFFECT_PRIM   ((void (*)(void))0x0805A985u)
#define ORIG_SETEFFECT_SEC    ((void (*)(void))0x0805A995u)
#define ORIG_MOVEEND          ((void (*)(void))0x0805C62Du)
#define ORIG_STATBUFFCHANGE   ((void (*)(void))0x08060B99u)

#define FN_GET_SIDE           ((u8 (*)(u8))0x08024685u)
#define FN_OAK_TUTORIAL       ((u8 (*)(void))0x0803B575u)
#define FN_GET_SCRIPT_BANK    ((u8 (*)(u8))0x0806C535u)
#define FN_GET_HOLD_EFFECT    ((u8 (*)(u16))0x080C725Du)
#define FN_GET_MON_DATA       ((u32 (*)(const void *, u32, const void *))0x0810A96Du)
#define FN_RANDOM             ((u16 (*)(void))0x0812E9C5u)
#define FN_UMOD32             ((u32 (*)(u32, u32))0x08172B4Du)

static u32 mon_tag(u8 bank)
{
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    u32 pid = *(volatile u32 *)(m + 0x4Cu);
    u32 slot = PARTY_INDEXES[bank];
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

static u8 is_status_heal_move(u16 move)
{
    if (move == 0u || move >= 822u)
        return 0u;
    u8 eff = MOVE_TABLE[12u * move];
    return (eff == 32u || eff == 37u || eff == 132u || eff == 133u
            || eff == 134u || eff == 157u || eff == 162u || eff == 179u
            || eff == 234u || eff == 235u) ? 1u : 0u;
}

static u8 stat_rose_this_turn(u8 bank)
{
    bank &= 3u;
    return ((V7_STATE->stat_rose_mask & (1u << bank)) != 0u
            && V7_STATE->rose_pid[bank] == mon_tag(bank)) ? 1u : 0u;
}

static u8 stat_fell_this_turn(u8 bank)
{
    bank &= 3u;
    return ((V7_STATE->stat_fell_mask & (1u << bank)) != 0u
            && V7_STATE->fell_pid[bank] == mon_tag(bank)) ? 1u : 0u;
}

static u8 prev_move_failed(u8 bank)
{
    bank &= 3u;
    return ((V7_STATE->prev_failed_mask & (1u << bank)) != 0u
            && V7_STATE->failed_pid[bank] == mon_tag(bank)) ? 1u : 0u;
}

static void run_with_stat_tracking(void (*orig_fn)(void))
{
    s8 before[4][8];
    u32 b, s;
    for (b = 0u; b < 4u; ++b) {
        volatile u8 *m = BATTLE_MONS + 0x5Cu * b + 0x18u;
        for (s = 0u; s < 8u; ++s)
            before[b][s] = (s8)m[s];
    }
    orig_fn();
    for (b = 0u; b < 4u; ++b) {
        volatile u8 *m = BATTLE_MONS + 0x5Cu * b + 0x18u;
        u8 rose = 0u, fell = 0u;
        for (s = 1u; s < 8u; ++s) {
            s8 cur = (s8)m[s];
            if (cur > before[b][s])
                rose = 1u;
            else if (cur < before[b][s])
                fell = 1u;
        }
        if (rose) {
            V7_STATE->stat_rose_mask |= (u8)(1u << b);
            V7_STATE->rose_pid[b] = mon_tag((u8)b);
        }
        if (fell) {
            V7_STATE->stat_fell_mask |= (u8)(1u << b);
            V7_STATE->fell_pid[b] = mon_tag((u8)b);
            if ((u8)b == (TARGET & 3u))
                V7_STATE->parting_dropped = 1u;
        }
    }
}

void hook_battle_init_v7(void)
{
    volatile u8 *p = (volatile u8 *)V7_STATE;
    for (u32 i = 0u; i < sizeof(struct V7BattleState); ++i)
        p[i] = 0u;
    ORIG_BATTLE_INIT();
}

void hook_turn_start_v7(void)
{
    V7_STATE->stat_rose_mask = 0u;
    V7_STATE->stat_fell_mask = 0u;
    V7_STATE->move_started_mask = 0u;
    V7_STATE->passed_canceler_mask = 0u;

    u32 count = BATTLERS_COUNT;
    if (count > 4u)
        count = 4u;
    for (u32 b = 0u; b < count; ++b) {
        if (CHOSEN_ACTION[b] != 0u) {
            u8 bit = (u8)(1u << b);
            V7_STATE->last_failed_mask &= (u8)~bit;
            V7_STATE->prev_failed_mask &= (u8)~bit;
        }
        if (V7_STATE->heal_block_turns[b] > 0u) {
            if (V7_STATE->heal_block_pid[b] != mon_tag((u8)b))
                V7_STATE->heal_block_turns[b] = 0u;
            else
                V7_STATE->heal_block_turns[b]--;
        }
    }
    ORIG_TURN_START();
}

void hook_attackcanceler_v7(void)
{
    u8 atk = ATTACKER & 3u;
    u8 bit = (u8)(1u << atk);
    u32 tag = mon_tag(atk);

    if ((V7_STATE->move_started_mask & bit) == 0u) {
        if ((V7_STATE->last_failed_mask & bit) != 0u && V7_STATE->failed_pid[atk] == tag)
            V7_STATE->prev_failed_mask |= bit;
        else
            V7_STATE->prev_failed_mask &= (u8)~bit;
        V7_STATE->last_failed_mask |= bit;
        V7_STATE->failed_pid[atk] = tag;
        V7_STATE->move_started_mask |= bit;
    }
    V7_STATE->passed_canceler_mask &= (u8)~bit;

    const u8 *before = CURR_INSTR;
    ORIG_ATTACKCANCELER();
    if (CURR_INSTR == before + 1) {
        if (is_heal_blocked(atk) && is_status_heal_move(CURRENT_MOVE)) {
            CURR_INSTR = BS_HEAL_BLOCK_CANCEL;
            return;
        }
        V7_STATE->passed_canceler_mask |= bit;
    }
}

void hook_moveend_v7(void)
{
    if (MOVEEND_STATE == 0u) {
        u8 atk = ATTACKER & 3u;
        u8 bit = (u8)(1u << atk);
        if ((V7_STATE->passed_canceler_mask & bit) != 0u
            && (MOVE_RESULT_FLAGS & 0x29u) == 0u) {
            V7_STATE->last_failed_mask &= (u8)~bit;
        }
        V7_STATE->passed_canceler_mask &= (u8)~bit;
    }
    ORIG_MOVEEND();
}

void hook_critcalc_v7(void)
{
    u8 atk = ATTACKER & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    u32 status2 = *(volatile u32 *)(a + 0x54u);
    if ((status2 & 0x00100000u) == 0u || V7_STATE->cheer_minus1_pid[atk] != mon_tag(atk)) {
        ORIG_CRITCALC();
        return;
    }

    /* Aliado nao-Dragao sob Dragon Cheer: +1 estagio critico em vez de +2. */
    u16 item = *(volatile u16 *)(a + 0x30u);
    u8 hold_eff = (item == 0xAFu)
        ? DISABLE_STRUCTS[28u * atk + 7u]
        : FN_GET_HOLD_EFFECT(item);
    EFFECT_BATTLER = atk;

    u16 move = CURRENT_MOVE;
    u8 eff = MOVE_TABLE[12u * move];
    u32 stage = 1u; /* +1 de Dragon Cheer nao-Dragao */
    if (eff == 0x2Bu || eff == 0x4Bu || eff == 0xC8u || eff == 0xD1u)
        stage += 1u;
    if (hold_eff == 0x29u)
        stage += 1u;
    u16 species = *(volatile u16 *)a;
    if (hold_eff == 0x42u && species == 0x53u)
        stage += 2u;
    if (hold_eff == 0x3Fu && species == 0x71u)
        stage += 2u;
    if (stage > 4u)
        stage = 4u;

    u8 tgt = TARGET & 3u;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    u16 t_ability = *(volatile u16 *)(t + 0x20u);
    u8 mult = 1u;
    if (t_ability != 4u && t_ability != 0x4Bu
        && (STATUSES3[atk] & 0x8000u) == 0u
        && (HIT_MARKER & 0x00040200u) == 0u) {
        u32 rng = FN_RANDOM();
        if (FN_UMOD32(rng, CRIT_CHANCE_TABLE[stage]) == 0u) {
            if ((HIT_MARKER & 0x10u) != 0u) {
                if (FN_OAK_TUTORIAL() != 0u)
                    mult = 2u;
            } else if ((HIT_MARKER & 0x00010000u) == 0u) {
                mult = 2u;
            }
        }
    }
    CRIT_MULTIPLIER = mult;
    CURR_INSTR = CURR_INSTR + 1;
}

void hook_damage_v7(void)
{
    u16 move = CURRENT_MOVE;
    if (move == 814u) {
        /* TM199 Lash Out: 75 -> 150 BP se algum estagio do usuario caiu neste turno. */
        if (stat_fell_this_turn(ATTACKER))
            DYNAMIC_POWER = 150u;
    } else if (move == 815u || move == 653u) {
        /* TM207 Temper Flare (815) e TM084 Stomping Tantrum (653): 75 -> 150 BP. */
        if (prev_move_failed(ATTACKER))
            DYNAMIC_POWER = 150u;
    }
    PREV_DAMAGE_V6();
}

void hook_healthbar_v7(void)
{
    if (BATTLE_OUTCOME == 0u && (MOVE_RESULT_FLAGS & 0x29u) == 0u && BATTLE_MOVE_DMG < 0) {
        u8 bank = FN_GET_SCRIPT_BANK(CURR_INSTR[1]);
        if (is_heal_blocked(bank)) {
            CURR_INSTR = CURR_INSTR + 2;
            return;
        }
    }
    ORIG_HEALTHBAR();
}

void hook_datahp_v7(void)
{
    if (BATTLE_OUTCOME == 0u && (MOVE_RESULT_FLAGS & 0x29u) == 0u && BATTLE_MOVE_DMG < 0) {
        u8 bank = FN_GET_SCRIPT_BANK(CURR_INSTR[1]);
        if (is_heal_blocked(bank)) {
            BATTLE_MOVE_DMG = 0;
            CURR_INSTR = CURR_INSTR + 2;
            return;
        }
    }
    ORIG_DATAHP();
}

void hook_seteffect_chance_v7(void)
{
    run_with_stat_tracking(ORIG_SETEFFECT_CHANCE);
}

void hook_seteffect_primary_v7(void)
{
    run_with_stat_tracking(ORIG_SETEFFECT_PRIM);
}

void hook_seteffect_secondary_v7(void)
{
    run_with_stat_tracking(ORIG_SETEFFECT_SEC);
}

void hook_statbuffchange_v7(void)
{
    run_with_stat_tracking(ORIG_STATBUFFCHANGE);
}

static u8 opposing_party_has_alive_mon(u8 atk_side)
{
    const u8 *party = (atk_side == 0u) ? ENEMY_PARTY : PLAYER_PARTY;
    for (u32 i = 0u; i < 6u; ++i) {
        const u8 *mon = party + 100u * i;
        if (FN_GET_MON_DATA(mon, 0x0Bu, 0) != 0u
            && FN_GET_MON_DATA(mon, 0x2Du, 0) == 0u
            && FN_GET_MON_DATA(mon, 0x39u, 0) > 0u) {
            return 1u;
        }
    }
    return 0u;
}

void hook_pivot_check(void)
{
    u8 atk = ATTACKER & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    if (*(volatile u16 *)(a + 0x2Au) == 0u || BATTLE_OUTCOME != 0u) {
        CURR_INSTR = BS_FINISH_MOVEEND;
        return;
    }
    u8 side = FN_GET_SIDE(atk);
    /* Pokemon selvagem nunca faz troca de pivot. */
    if (side == 1u && (BATTLE_TYPE_FLAGS & 0x08u) == 0u) {
        CURR_INSTR = BS_FINISH_MOVEEND;
        return;
    }
    if (!opposing_party_has_alive_mon(side)) {
        CURR_INSTR = BS_FINISH_MOVEEND;
        return;
    }
}

void hook_parting_init(void)
{
    V7_STATE->parting_dropped = 0u;
}

void hook_parting_check(void)
{
    if (V7_STATE->parting_dropped == 0u) {
        CURR_INSTR = BS_MOVE_END;
    }
}

static u8 find_alive_ally(u8 atk, u8 *ally_out)
{
    if ((BATTLE_TYPE_FLAGS & 0x01u) == 0u)
        return 0u;
    u8 ally = (u8)(atk ^ 2u);
    if ((ABSENT_BATTLERS & (1u << ally)) != 0u)
        return 0u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * ally;
    if (*(volatile u16 *)(m + 0x2Au) == 0u)
        return 0u;
    *ally_out = ally;
    return 1u;
}

void hook_coaching_check(void)
{
    u8 ally = 0u;
    if (!find_alive_ally(ATTACKER & 3u, &ally)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    volatile u8 *m = BATTLE_MONS + 0x5Cu * ally;
    if ((s8)m[0x18u + 1u] >= 12 && (s8)m[0x18u + 2u] >= 12) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    TARGET = ally;
}

void hook_dragon_cheer_apply(void)
{
    u8 atk = ATTACKER & 3u;
    u8 ally = 0u;
    if (!find_alive_ally(atk, &ally)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    volatile u8 *m = BATTLE_MONS + 0x5Cu * ally;
    u32 status2 = *(volatile u32 *)(m + 0x54u);
    if ((status2 & 0x00100000u) != 0u) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    *(volatile u32 *)(m + 0x54u) = status2 | 0x00100000u;
    u8 t1 = m[0x22u], t2 = m[0x23u];
    V7_STATE->cheer_minus1_pid[ally] = (t1 == 16u || t2 == 16u) ? 0u : mon_tag(ally);
    TARGET = ally;
}

void hook_restore_attacker(void)
{
    u8 tmp = ATTACKER;
    ATTACKER = TARGET;
    TARGET = tmp;
}

void hook_upper_hand_check(void)
{
    u8 tgt = TARGET & 3u;
    u32 total = BATTLERS_COUNT;
    if (total > 4u)
        total = 4u;
    u8 found_after = 0u;
    for (u32 i = (u32)CURR_TURN_ACTION_NUM + 1u; i < total; ++i) {
        if (BATTLER_BY_TURN[i] == tgt) {
            if (ACTIONS_BY_TURN[i] == 0u)
                found_after = 1u;
            break;
        }
    }
    if (!found_after) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    volatile u8 *tmon = BATTLE_MONS + 0x5Cu * tgt;
    u16 tmove;
    if ((*(volatile u32 *)(tmon + 0x54u) & 0x00001000u) != 0u) {
        tmove = LOCKED_MOVES[tgt];
    } else {
        const u8 *bstruct = BATTLE_STRUCT_PTR;
        u8 mslot = bstruct[0x80u + tgt] & 3u;
        tmove = *(volatile u16 *)(tmon + 0x0Cu + 2u * mslot);
    }
    if (tmove == 0u || tmove >= 822u) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    const u8 *rec = MOVE_TABLE + 12u * tmove;
    u8 pwr = rec[1];
    s8 prio = (s8)rec[7];
    if (pwr == 0u || prio <= 0) {
        CURR_INSTR = BS_BUT_IT_FAILED;
    }
}

void hook_burning_jealousy_sec(void)
{
    MOVE_EFFECT_BYTE = stat_rose_this_turn(TARGET) ? 3u : 0u;
}

void hook_alluring_voice_sec(void)
{
    MOVE_EFFECT_BYTE = stat_rose_this_turn(TARGET) ? 7u : 0u;
}

void hook_psychic_noise_apply(void)
{
    u8 tgt = TARGET & 3u;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    if ((MOVE_RESULT_FLAGS & 0x29u) == 0u
        && (*(volatile u16 *)(t + 0x2Au)) > 0u
        && (*(volatile u32 *)(t + 0x54u) & 0x01000000u) == 0u) {
        V7_STATE->heal_block_turns[tgt] = 2u;
        V7_STATE->heal_block_pid[tgt] = mon_tag(tgt);
    }
}

void hook_target_heal_prep(void)
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
    s32 heal = (s32)((max_hp + 1u) >> 1);
    if (heal < 1)
        heal = 1;
    BATTLE_MOVE_DMG = -heal;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
}

static u8 can_life_dew_heal(u8 bank)
{
    if (is_heal_blocked(bank))
        return 0u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    u16 hp = *(volatile u16 *)(m + 0x2Au);
    u16 max_hp = *(volatile u16 *)(m + 0x2Eu);
    return (hp > 0u && hp < max_hp) ? 1u : 0u;
}

void hook_life_dew_check(void)
{
    u8 atk = ATTACKER & 3u;
    u8 ok = can_life_dew_heal(atk);
    u8 ally = 0u;
    if (!ok && find_alive_ally(atk, &ally))
        ok = can_life_dew_heal(ally);
    if (!ok)
        CURR_INSTR = BS_BUT_IT_FAILED;
}

void hook_life_dew_self(void)
{
    const u8 *p = CURR_INSTR;
    u32 skip = (u32)p[0] | ((u32)p[1] << 8) | ((u32)p[2] << 16) | ((u32)p[3] << 24);
    u8 atk = ATTACKER & 3u;
    if (!can_life_dew_heal(atk)) {
        CURR_INSTR = (const u8 *)skip;
        return;
    }
    volatile u8 *m = BATTLE_MONS + 0x5Cu * atk;
    s32 heal = (s32)((*(volatile u16 *)(m + 0x2Eu)) >> 2);
    if (heal < 1)
        heal = 1;
    TARGET = atk;
    BATTLE_MOVE_DMG = -heal;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
    CURR_INSTR = p + 4;
}

void hook_life_dew_ally(void)
{
    u8 atk = ATTACKER & 3u;
    u8 ally = 0u;
    if (!find_alive_ally(atk, &ally) || !can_life_dew_heal(ally)) {
        CURR_INSTR = BS_MOVE_END;
        return;
    }
    volatile u8 *m = BATTLE_MONS + 0x5Cu * ally;
    s32 heal = (s32)((*(volatile u16 *)(m + 0x2Eu)) >> 2);
    if (heal < 1)
        heal = 1;
    TARGET = ally;
    BATTLE_MOVE_DMG = -heal;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
}
