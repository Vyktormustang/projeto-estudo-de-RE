/* Rotinas auxiliares de batalha do motor_v10 (ARM7TDMI / Thumb-1).
 *
 * Encadeia de forma deterministica sobre o motor_v9 sem tocar estruturas de
 * save persistentes, consolidando:
 *
 *  1. Motor de consumo de Berries (itens 133..175) e restauracao de +3
 *     learnsets de nivel (15.005 -> 15.008 linhas, 708/729 = 97,1%):
 *     Stuff Cheeks (672), Teatime (677), Bug Bite (449, TM182), Pluck (365),
 *     Incinerate (509) e Belch (558), com rastreamento por slot da equipe.
 *  2. Consolidacao mecânica das TMs modernas de Scarlet/Violet e golpes de
 *     assinatura Gen 4-9 via EFF_V10_DISPATCH (slot 255 de SCRIPT_TABLE) e
 *     hooks encadeados em CMD_TABLE_V10 (0x00, 0x01, 0x04, 0x05, 0x06, 0x0C,
 *     0x88 e 0xDD).
 *
 * Quatro golpes de subida de nivel (21 linhas = 2,9%) permanecem fora de
 * escopo por dependerem de habilidades/UI ausentes na base Gen 3:
 * Simple Beam (492), Ally Switch (501), Instruct (644) e Revival Blessing (755).
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
#define WEATHER_SUN_MASK  0x0060u
#define WEATHER_SNOW_BIT  0x0100u

#define STATUS2_CONFUSION         0x00000007u
#define STATUS2_FOCUS_ENERGY      0x00100000u
#define STATUS2_SUBSTITUTE        0x01000000u
#define STATUS2_ESCAPE_PREVENTION 0x04000000u

#define STATUS3_INGRAIN           0x00000400u
#define STATUS3_GROUNDED_OVER     0x00002000u
#define STATUS3_GASTRO_ACID       0x00010000u

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

struct V10BattleState {
    u32 smacked_down_tag[4];
    u32 throat_chop_tag[4];
    u32 salt_cure_tag[4];
    u32 syrup_bomb_tag[4];
    u32 glaive_rush_tag[4];
    u32 rage_hits_nibbles[2];
    u8  berry_watch_idx[4];
    u8  berry_watch_slot[4];
    u8  throat_chop_turns[4];
    u8  syrup_bomb_turns[4];
    u8  autotomize_count[4];
    u8  autotomize_slot[4];
    u8  prev_heavy_slot[4];
    u8  curr_heavy_slot[4];
    u8  ate_berry_mask[2];
    u8  known_fainted_mask[2];
    u8  ally_fainted_flags;
    u8  aura_wheel_hangry_mask;
    u8  active_berry_idx;
    u8  ion_deluge_active;
    u8  acted_turn_mask;
    u8  damaged_turn_mask;
    u8  round_used_turn;
    u8  echoed_streak;
    u8  echoed_used_turn;
    u8  endturn_step_v10;
    u8  berry_mode;
    u8  berry_phase;
    u8  berry_consumer;
    u8  teatime_idx;
    u8  saved_atk;
    u8  saved_tgt;
    u8  queue_mode;
    u8  stat_len;
    u8  stat_idx;
    u8  stat_queue[4];
};

#define V7_STATE                ((volatile struct V7BattleState *)0x0203FC00u)
#define V8_STATE                ((volatile struct V8BattleState *)0x0203FC60u)
#define V9_STATE                ((volatile struct V9BattleState *)0x0203FCA0u)
#define V10_STATE               ((volatile struct V10BattleState *)0x0203FD60u)
_Static_assert(sizeof(struct V10BattleState) <= 0x98u, "V10BattleState exceeds 0x0203FD60..0x0203FDF7");

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
#define HP_DEALT                (*(volatile s32 *)0x02021590u)
#define ATTACKER                (*(volatile u8 *)0x020215A8u)
#define TARGET                  (*(volatile u8 *)0x020215A9u)
#define EFFECT_BATTLER          (*(volatile u8 *)0x020215ABu)
#define ABSENT_BATTLERS         (*(volatile u8 *)0x020215ADu)
#define CRIT_MULTIPLIER         (*(volatile u8 *)0x020215AEu)
#define CURR_INSTR              (*(const u8 *volatile *)0x020215B0u)
#define MOVE_RESULT_FLAGS       (*(volatile u8 *)0x02021608u)
#define HIT_MARKER              (*(volatile u32 *)0x0202160Cu)
#define SIDE_STATUSES           ((volatile u16 *)0x0202161Cu)
#define STATUSES3               ((volatile u32 *)0x02021638u)
#define MOVE_EFFECT_BYTE        (*(volatile u8 *)0x020216C3u)
#define MULTISTRING_CHOOSER     (*(volatile u8 *)0x020216C5u)
#define BATTLE_OUTCOME          (*(volatile u8 *)0x020216C8u)
#define PROTECT_STRUCTS         ((volatile u8 *)0x020216CCu)
#define LOCKED_MOVES            ((volatile u16 *)0x020216CCu)
#define BATTLE_WEATHER          (*(volatile u16 *)0x0202175Cu)
#define WEATHER_DURATION        (*(volatile u8 *)0x02021788u)
#define DYNAMIC_POWER           (*(volatile u16 *)0x02021792u)
#define MULTIHIT_COUNTER        (*(volatile u8 *)0x02021814u)
#define SCRIPTING_BATTLER       (*(volatile u8 *)0x0202181Fu)
#define STAT_BUFF_ADDR          (*(volatile u8 *)0x02021822u)
#define ANIM_ARG1_BYTE          (*(volatile u8 *)0x02021823u)
#define BATTLE_STRUCT_PTR       (*(volatile u8 *volatile *)0x0202182Cu)
#define BATTLE_RESOURCES_PTR    (*(volatile u8 *volatile *)0x02021838u)

#define ENEMY_PARTY_COUNT       (*(volatile u8 *)0x0203A730u)
#define PLAYER_PARTY_COUNT      (*(volatile u8 *)0x0203A731u)
#define ENEMY_PARTY_BASE        ((u8 *)0x0203A734u)
#define PLAYER_PARTY_BASE       ((u8 *)0x0203A98Cu)

#define MOVE_TABLE              ((const u8 *)0x09000000u)
#define WEIGHTS_TABLE           ((const u16 *)0x0900D000u)
#define CATEGORY_TABLE          ((const u8 *)0x0900E000u)
#define NEW_ITEMS_TABLE         ((const u8 *)0x08E11000u)
#define TYPE_EFFECT_TABLE       ((const u8 *)0x08200C18u)

/* Sub-scripts herdados de motor_v8 / motor_v9 */
#define BS_V8_ENDTURN_MSGS      ((const u8 *)0x090C1030u)
#define BS_V8_ENDTURN_GRASSY    ((const u8 *)0x090C1070u)
#define BS_V9_ENDTURN_AQUA_RING ((const u8 *)0x090C6000u)
#define BS_V9_ENDTURN_OCTOLOCK  ((const u8 *)0x090C6020u)
#define BS_V9_ENDTURN_MROOM     ((const u8 *)0x090C60A0u)

/* Sub-scripts nativos */
#define BS_EFFECT_HIT           ((const u8 *)0x081853CEu)
#define BS_HIT_CALC_START       ((const u8 *)0x081853D8u)
#define BS_MOVE_END             ((const u8 *)0x081853F6u)
#define BS_MISS_AFTER_PP        ((const u8 *)0x08185408u)
#define BS_MULTIHIT_MOVEEND     ((const u8 *)0x08185832u)
#define BS_BUT_IT_FAILED        ((const u8 *)0x0818689Au)
#define BS_INGRAIN_ANCHORED     ((const u8 *)0x081879D2u)
#define BS_SUCTION_ANCHORED     ((const u8 *)0x08187EB3u)

/* Sub-scripts fixos gravados em 0x090CD000..0x090CD7FF por motor_v10.py */
#define BS_V10_DISPATCH          ((const u8 *)0x090CD000u)
#define BS_V10_FAIL_PP           ((const u8 *)0x090CD010u)
#define BS_V10_THROAT_BLOCK      ((const u8 *)0x090CD020u)
#define BS_V10_CONSECUTIVE_FAIL  ((const u8 *)0x090CD030u)
#define BS_V10_ENDTURN_SALT_CURE ((const u8 *)0x090CD040u)
#define BS_V10_ENDTURN_SYRUP     ((const u8 *)0x090CD070u)
#define BS_V10_ENDTURN_THROAT    ((const u8 *)0x090CD0C0u)
#define BS_V10_BERRY_WAIT_STEP   ((const u8 *)0x090CD0D0u)
#define BS_V10_BERRY_HP_STEP     ((const u8 *)0x090CD0F0u)
#define BS_V10_BERRY_STATUS_STEP ((const u8 *)0x090CD110u)
#define BS_V10_BERRY_PP_STEP     ((const u8 *)0x090CD130u)
#define BS_V10_STAT_QUEUE_LOOP   ((const u8 *)0x090CD150u)
#define BS_V10_MSG_TAILS         ((const u8 *)0x090CD200u)
#define BS_V10_PHAZE_TAIL        ((const u8 *)0x090CD300u)
#define BS_V10_TRAP_TAIL         ((const u8 *)0x090CD330u)
#define BS_V10_PRIMARY_EFF_TAIL  ((const u8 *)0x090CD340u)
#define BS_V10_BURN_CURE_TAIL    ((const u8 *)0x090CD350u)
#define BS_V10_SLEEP_CURE_TAIL   ((const u8 *)0x090CD370u)
#define BS_V10_INCINERATE_TAIL   ((const u8 *)0x090CD390u)
#define BS_V10_SPECTRAL_CONT     ((const u8 *)0x090CD3B0u)
#define BS_V10_STANDARD_HIT      ((const u8 *)0x090CD400u)
#define BS_V10_TRIPLE_DIVE       ((const u8 *)0x090CD440u)
#define BS_V10_DOUBLE_IRON_BASH  ((const u8 *)0x090CD460u)
#define BS_V10_POPULATION_BOMB   ((const u8 *)0x090CD480u)
#define BS_V10_SCALE_SHOT        ((const u8 *)0x090CD580u)
#define BS_V10_MATCHA_GOTCHA     ((const u8 *)0x090CD660u)
#define BS_V10_SPECTRAL_THIEF    ((const u8 *)0x090CD700u)
#define BS_V10_POLLEN_ALLY       ((const u8 *)0x090CD720u)
#define BS_V10_STUFF_CHEEKS      ((const u8 *)0x090CD760u)
#define BS_V10_TEATIME           ((const u8 *)0x090CD780u)
#define BS_V10_VICTORY_DANCE     ((const u8 *)0x090CD7A0u)
#define BS_V10_ION_DELUGE        ((const u8 *)0x090CD7C0u)

/* Encadeamento sobre motor_v9 / motor_v8 / motor_v7 / funcoes nativas */
#define PREV_BATTLE_INIT_V9      ((void (*)(void))0x090C9001u)
#define PREV_TURN_START_V9       ((void (*)(void))0x090C9009u)
#define PREV_ATTACKCANCELER_V9   ((void (*)(void))0x090C9021u)
#define PREV_ACCURACYCHECK_V8    ((void (*)(void))0x090C3029u)
#define PREV_CRITCALC_V9         ((void (*)(void))0x090C9029u)
#define PREV_DAMAGE_V9           ((void (*)(void))0x090C9031u)
#define PREV_TYPECALC_V9         ((void (*)(void))0x090C9039u)
#define PREV_DATAHPUPDATE_V7     ((void (*)(void))0x090C0031u)
#define ORIG_NEGATIVEDAMAGE      ((void (*)(void))0x08060821u)

#define ENTRY_ENDTURN_V10_THUMB  0x090D0011u
#define ORIG_BATTLE_TURN_PASSED  ((void (*)(void))0x08053221u)
#define FN_TURN_VALUES_CLEANUP   ((void (*)(u8))0x080543A5u)
#define FN_DO_FIELD_ENDTURN      ((u8 (*)(void))0x0806D069u)

#define FN_GET_SIDE              ((u8 (*)(u8))0x08024685u)
#define FN_EMIT_SET_MON_DATA     ((void (*)(u8, u8, u8, u8, const void *))0x08049DF5u)
#define FN_GET_SCRIPT_BANK       ((u8 (*)(u8))0x0806C535u)
#define FN_MARK_BUFFER_EXEC      ((void (*)(u8))0x0806C8BDu)
#define FN_GET_MON_DATA          ((u32 (*)(void *, u32, void *))0x0810A96Du)
#define FN_SET_MON_DATA          ((void (*)(void *, u32, const void *))0x0810AF79u)
#define FN_RANDOM                ((u16 (*)(void))0x0812E9C5u)
#define FN_UDIV32                ((u32 (*)(u32, u32))0x08172B3Du)
#define FN_UMOD32                ((u32 (*)(u32, u32))0x08172B4Du)

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

static u8 is_berry_item(u16 item)
{
    return (item >= 133u && item <= 175u) ? 1u : 0u;
}

static void *party_mon_ptr(u8 bank)
{
    u16 slot = PARTY_INDEXES[bank & 3u];
    if (slot > 5u)
        slot = 0u;
    u8 *base = (FN_GET_SIDE(bank & 3u) == 0u) ? PLAYER_PARTY_BASE : ENEMY_PARTY_BASE;
    return (void *)(base + 100u * slot);
}

static u8 effective_ability_v10(u8 bank)
{
    bank &= 3u;
    if ((STATUSES3[bank] & STATUS3_GASTRO_ACID) != 0u)
        return 0u;
    return BATTLE_MONS[0x5Cu * bank + 0x20u];
}

static u8 has_smack_down(u8 bank)
{
    bank &= 3u;
    if (V10_STATE->smacked_down_tag[bank] == 0u)
        return 0u;
    if (V10_STATE->smacked_down_tag[bank] != mon_tag(bank)) {
        V10_STATE->smacked_down_tag[bank] = 0u;
        return 0u;
    }
    return 1u;
}

static u8 is_grounded_v10(u8 bank)
{
    bank &= 3u;
    if (V8_STATE->gravity_turns > 0u || has_smack_down(bank))
        return 1u;
    if ((STATUSES3[bank] & (STATUS3_INGRAIN | STATUS3_GROUNDED_OVER)) != 0u)
        return 1u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    u16 item = *(volatile u16 *)(m + 0x30u);
    if (V9_STATE->magic_room_turns == 0u && item == 278u) /* Iron Ball */
        return 1u;
    if (V8_STATE->magnet_rise_turns[bank] > 0u && V8_STATE->magnet_rise_pid[bank] == mon_tag(bank))
        return 0u;
    u8 t1 = m[0x22u], t2 = m[0x23u];
    u8 t3 = (V9_STATE->extra_type_tag[bank] == mon_tag(bank)) ? V9_STATE->extra_type[bank] : 0xFFu;
    if (t1 == 2u || t2 == 2u || t3 == 2u)
        return 0u;
    if (effective_ability_v10(bank) == 26u) /* Levitate */
        return 0u;
    return 1u;
}

static void mark_ate_berry_bank(u8 bank)
{
    bank &= 3u;
    u8 side = FN_GET_SIDE(bank) & 1u;
    u8 slot = (u8)(PARTY_INDEXES[bank] & 7u);
    if (slot < 6u)
        V10_STATE->ate_berry_mask[side] |= (u8)(1u << slot);
}

static void sync_berry_watchers(void)
{
    u32 cnt = BATTLERS_COUNT;
    if (cnt > 4u)
        cnt = 4u;
    for (u32 b = 0u; b < cnt; ++b) {
        if (!is_bank_alive((u8)b)) {
            V10_STATE->berry_watch_idx[b] = 0u;
            V10_STATE->berry_watch_slot[b] = 0u;
            continue;
        }
        volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
        u16 cur = *(volatile u16 *)(m + 0x30u);
        u8 slot1 = (u8)((PARTY_INDEXES[b] & 7u) + 1u);
        if (V10_STATE->berry_watch_idx[b] != 0u
            && V10_STATE->berry_watch_slot[b] == slot1
            && cur == 0u) {
            mark_ate_berry_bank((u8)b);
        }
        if (is_berry_item(cur)) {
            V10_STATE->berry_watch_idx[b] = (u8)(cur - 132u);
            V10_STATE->berry_watch_slot[b] = slot1;
        } else {
            V10_STATE->berry_watch_idx[b] = 0u;
            V10_STATE->berry_watch_slot[b] = slot1;
        }
    }
}

static void clear_held_item_sync(u8 holder)
{
    holder &= 3u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * holder;
    u16 zero16 = 0u;
    *(volatile u16 *)(m + 0x30u) = 0u;
    V10_STATE->berry_watch_idx[holder] = 0u;
    FN_SET_MON_DATA(party_mon_ptr(holder), 0x0Cu, &zero16);
    ACTIVE_BATTLER = holder;
    FN_EMIT_SET_MON_DATA(0u, 0x02u, 0u, 2u, &zero16);
    FN_MARK_BUFFER_EXEC(holder);
}

static void emit_status_sync_v10(u8 bank)
{
    bank &= 3u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    u32 st = *(volatile u32 *)(m + 0x50u);
    FN_SET_MON_DATA(party_mon_ptr(bank), 0x37u, &st);
    ACTIVE_BATTLER = bank;
    FN_EMIT_SET_MON_DATA(0u, 0x28u, 0u, 4u, (const void *)(m + 0x50u));
    FN_MARK_BUFFER_EXEC(bank);
}

static void emit_pp_sync_v10(u8 bank, u8 mslot, u8 new_pp)
{
    bank &= 3u;
    mslot &= 3u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    m[0x25u + mslot] = new_pp;
    FN_SET_MON_DATA(party_mon_ptr(bank), 0x11u + mslot, &new_pp);
    ACTIVE_BATTLER = bank;
    FN_EMIT_SET_MON_DATA(0u, (u8)(0x09u + mslot), 0u, 1u, &new_pp);
    FN_MARK_BUFFER_EXEC(bank);
}

static void refresh_fainted_party_tracking(void)
{
    for (u32 side = 0u; side < 2u; ++side) {
        u8 *base = (side == 0u) ? PLAYER_PARTY_BASE : ENEMY_PARTY_BASE;
        u8 count = (side == 0u) ? PLAYER_PARTY_COUNT : ENEMY_PARTY_COUNT;
        if (count > 6u)
            count = 6u;
        u8 cur_fainted = 0u;
        for (u32 s = 0u; s < count; ++s) {
            void *pm = (void *)(base + 100u * s);
            u32 sp = FN_GET_MON_DATA(pm, 0x41u, 0); /* MON_DATA_SPECIES_OR_EGG */
            if (sp != 0u && sp != 412u) {
                u16 hp = *(volatile u16 *)((u8 *)pm + 86u);
                if (hp == 0u)
                    cur_fainted |= (u8)(1u << s);
            }
        }
        u8 newly = (u8)(cur_fainted & (u8)~V10_STATE->known_fainted_mask[side]);
        if (newly != 0u)
            V10_STATE->ally_fainted_flags |= (u8)(1u << (2u + side));
        V10_STATE->known_fainted_mask[side] = cur_fainted;
    }
}

static u32 effective_weight_hg(u8 bank)
{
    bank &= 3u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    u16 sp = *(volatile u16 *)m;
    u32 w = (sp > 0u && sp <= 1025u) ? (u32)WEIGHTS_TABLE[sp] : 1u;
    if (w == 0u)
        w = 1u;
    u8 slot1 = (u8)((PARTY_INDEXES[bank] & 7u) + 1u);
    if (V10_STATE->autotomize_count[bank] > 0u && V10_STATE->autotomize_slot[bank] == slot1) {
        u32 sub = 1000u * (u32)V10_STATE->autotomize_count[bank];
        w = (w > sub) ? (w - sub) : 1u;
    }
    return w;
}

static u32 staged_stat(u16 base_val, u8 stage)
{
    if (stage > 12u)
        stage = 12u;
    if (stage >= 6u)
        return ((u32)base_val * (u32)(stage - 4u)) >> 1;
    return FN_UDIV32((u32)base_val * 2u, (u32)(8u - stage));
}

static u8 get_rage_fist_hits(u8 bank)
{
    bank &= 3u;
    u8 side = FN_GET_SIDE(bank) & 1u;
    u8 slot = (u8)(PARTY_INDEXES[bank] & 7u);
    if (slot >= 6u)
        return 0u;
    return (u8)((V10_STATE->rage_hits_nibbles[side] >> (4u * slot)) & 0x0Fu);
}

static void inc_rage_fist_hits(u8 bank)
{
    bank &= 3u;
    u8 side = FN_GET_SIDE(bank) & 1u;
    u8 slot = (u8)(PARTY_INDEXES[bank] & 7u);
    if (slot >= 6u)
        return;
    u32 shift = 4u * (u32)slot;
    u32 cur = (V10_STATE->rage_hits_nibbles[side] >> shift) & 0x0Fu;
    if (cur < 6u) {
        cur++;
        V10_STATE->rage_hits_nibbles[side] =
            (V10_STATE->rage_hits_nibbles[side] & ~(0x0Fu << shift)) | (cur << shift);
    }
}

static u8 is_sound_move_v10(u16 move)
{
    switch (move) {
    case 45u:  /* Growl */
    case 46u:  /* Roar */
    case 47u:  /* Sing */
    case 48u:  /* Supersonic */
    case 103u: /* Screech */
    case 173u: /* Snore */
    case 195u: /* Perish Song */
    case 215u: /* Heal Bell */
    case 253u: /* Uproar */
    case 304u: /* Hyper Voice */
    case 319u: /* Metal Sound */
    case 320u: /* Grass Whistle */
    case 336u: /* Howl */
    case 405u: /* Bug Buzz */
    case 447u: /* Chatter */
    case 495u: /* Round */
    case 496u: /* Echoed Voice */
    case 543u: /* Relic Song */
    case 551u: /* Snarl */
    case 564u: /* Noble Roar */
    case 570u: /* Disarming Voice */
    case 571u: /* Parting Shot */
    case 582u: /* Boomburst */
    case 586u: /* Confide */
    case 619u: /* Sparkling Aria */
    case 646u: /* Clanging Scales */
    case 682u: /* Clangorous Soul */
    case 691u: /* Overdrive */
    case 720u: /* Eerie Spell */
    case 763u: /* Torch Song */
    case 819u: /* Alluring Voice */
    case 820u: /* Psychic Noise */
        return 1u;
    default:
        return 0u;
    }
}

static u8 mon_has_type(u8 bank, u8 typ)
{
    bank &= 3u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    if (m[0x22u] == typ || m[0x23u] == typ)
        return 1u;
    if (V9_STATE->extra_type_tag[bank] == mon_tag(bank) && V9_STATE->extra_type[bank] == typ)
        return 1u;
    return 0u;
}

static void remove_mon_type(u8 bank, u8 typ)
{
    bank &= 3u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
    u8 t1 = m[0x22u], t2 = m[0x23u];
    if (t1 == typ && t2 == typ) {
        m[0x22u] = 9u; /* TYPE_MYSTERY (sem tipo) */
        m[0x23u] = 9u;
    } else if (t1 == typ) {
        m[0x22u] = t2;
    } else if (t2 == typ) {
        m[0x23u] = t1;
    }
    if (V9_STATE->extra_type_tag[bank] == mon_tag(bank) && V9_STATE->extra_type[bank] == typ) {
        V9_STATE->extra_type_tag[bank] = 0u;
        V9_STATE->extra_type[bank] = 0xFFu;
    }
}

static u8 type_effectiveness_mult(u8 atk_type, u8 def_type)
{
    for (u32 i = 0u; i < 336u; i += 3u) {
        u8 a = TYPE_EFFECT_TABLE[i];
        if (a == 0xFFu)
            break;
        if (a == 0xFEu)
            continue;
        if (a == atk_type && TYPE_EFFECT_TABLE[i + 1u] == def_type)
            return TYPE_EFFECT_TABLE[i + 2u];
    }
    return 10u; /* 1.0x */
}

static void start_endturn_script_v10(const u8 *bs_ptr)
{
    CURR_INSTR = bs_ptr;
    volatile u8 *cb_stack = *(volatile u8 **)(BATTLE_RESOURCES_PTR + 0x0Cu);
    u8 depth = cb_stack[0x20u];
    cb_stack[0x20u] = (u8)(depth + 1u);
    ((volatile u32 *)cb_stack)[depth] = BATTLE_MAIN_FUNC;
    CURR_ACTION_FUNC_ID = 0u;
    BATTLE_MAIN_FUNC = 0x08054B91u;
}

static const u8 *msg_tail_v10(u32 idx)
{
    return BS_V10_MSG_TAILS + 12u * idx;
}

/* ========================= Ciclo de vida de Batalha ===================== */

void hook_battle_init_v10(void)
{
    volatile u8 *p = (volatile u8 *)V10_STATE;
    for (u32 i = 0u; i < sizeof(struct V10BattleState); ++i)
        p[i] = 0u;
    PREV_BATTLE_INIT_V9();
}

void hook_turn_start_v10(void)
{
    sync_berry_watchers();
    refresh_fainted_party_tracking();

    V10_STATE->ion_deluge_active = 0u;
    V10_STATE->acted_turn_mask = 0u;
    V10_STATE->damaged_turn_mask = 0u;
    V10_STATE->round_used_turn = 0u;
    V10_STATE->endturn_step_v10 = 0u;

    if (V10_STATE->echoed_used_turn != 0u) {
        if (V10_STATE->echoed_streak < 4u)
            V10_STATE->echoed_streak++;
    } else {
        V10_STATE->echoed_streak = 0u;
    }
    V10_STATE->echoed_used_turn = 0u;

    V10_STATE->ally_fainted_flags = (u8)((V10_STATE->ally_fainted_flags >> 2) & 0x03u);
    for (u32 b = 0u; b < 4u; ++b) {
        V10_STATE->prev_heavy_slot[b] = V10_STATE->curr_heavy_slot[b];
        V10_STATE->curr_heavy_slot[b] = 0u;
    }

    /* Grassy Glide (805): +1 de prioridade quando o usuário está aterrado em Grassy Terrain */
    if (V8_STATE->terrain_type == TERRAIN_GRASSY && V8_STATE->terrain_turns > 0u) {
        u32 total = BATTLERS_COUNT;
        if (total > 4u)
            total = 4u;
        for (u32 i = 0u; i < total; ++i) {
            u8 b = BATTLER_BY_TURN[i] & 3u;
            if (ACTIONS_BY_TURN[i] != 0u || !is_bank_alive(b) || !is_grounded_v10(b))
                continue;
            volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
            u8 mslot = BATTLE_STRUCT_PTR[0x80u + b] & 3u;
            u16 mv = ((*(volatile u32 *)(m + 0x54u) & 0x00001000u) != 0u)
                ? LOCKED_MOVES[b]
                : *(volatile u16 *)(m + 0x0Cu + 2u * mslot);
            if (mv == 805u) {
                /* Promove antes de golpes de prioridade 0 mantendo ordem entre Grassy Glides */
                u32 pos = i;
                while (pos > 0u) {
                    u8 prev_b = BATTLER_BY_TURN[pos - 1u] & 3u;
                    if (ACTIONS_BY_TURN[pos - 1u] != 0u)
                        break;
                    volatile u8 *pm = BATTLE_MONS + 0x5Cu * prev_b;
                    u8 pslot = BATTLE_STRUCT_PTR[0x80u + prev_b] & 3u;
                    u16 pmv = ((*(volatile u32 *)(pm + 0x54u) & 0x00001000u) != 0u)
                        ? LOCKED_MOVES[prev_b]
                        : *(volatile u16 *)(pm + 0x0Cu + 2u * pslot);
                    s8 pprio = (pmv < 822u) ? (s8)MOVE_TABLE[12u * pmv + 7u] : 0;
                    if (pmv == 805u && is_grounded_v10(prev_b))
                        pprio = 1;
                    if (pprio >= 1)
                        break;
                    u8 tb = BATTLER_BY_TURN[pos - 1u];
                    u8 ta = ACTIONS_BY_TURN[pos - 1u];
                    BATTLER_BY_TURN[pos - 1u] = BATTLER_BY_TURN[pos];
                    ACTIONS_BY_TURN[pos - 1u] = ACTIONS_BY_TURN[pos];
                    BATTLER_BY_TURN[pos] = tb;
                    ACTIONS_BY_TURN[pos] = ta;
                    pos--;
                }
            }
        }
    }

    PREV_TURN_START_V9();
}

/* ==================== Fim de Turno encadeado (v8 + v9 + v10) ============ */

static u8 has_aqua_ring_v10(u8 b)
{
    if (V9_STATE->aqua_ring_tag[b] == 0u)
        return 0u;
    if (V9_STATE->aqua_ring_tag[b] != mon_tag(b)) {
        V9_STATE->aqua_ring_tag[b] = 0u;
        return 0u;
    }
    return 1u;
}

static u8 has_octolock_v10(u8 b)
{
    if (V9_STATE->octolock_tgt_tag[b] == 0u)
        return 0u;
    u8 src = V9_STATE->octolock_src[b] & 3u;
    if (V9_STATE->octolock_tgt_tag[b] != mon_tag(b)
        || !is_bank_alive(src)
        || V9_STATE->octolock_src_tag[b] != mon_tag(src)) {
        V9_STATE->octolock_tgt_tag[b] = 0u;
        V9_STATE->octolock_src_tag[b] = 0u;
        return 0u;
    }
    return 1u;
}

static u8 has_salt_cure_v10(u8 b)
{
    if (V10_STATE->salt_cure_tag[b] == 0u)
        return 0u;
    if (V10_STATE->salt_cure_tag[b] != mon_tag(b)) {
        V10_STATE->salt_cure_tag[b] = 0u;
        return 0u;
    }
    return 1u;
}

static u8 has_syrup_bomb_v10(u8 b)
{
    if (V10_STATE->syrup_bomb_turns[b] == 0u || V10_STATE->syrup_bomb_tag[b] == 0u)
        return 0u;
    if (V10_STATE->syrup_bomb_tag[b] != mon_tag(b)) {
        V10_STATE->syrup_bomb_tag[b] = 0u;
        V10_STATE->syrup_bomb_turns[b] = 0u;
        return 0u;
    }
    return 1u;
}

static u8 has_any_endturn_all(void)
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
            || V9_STATE->octolock_tgt_tag[b] != 0u
            || V10_STATE->salt_cure_tag[b] != 0u
            || V10_STATE->syrup_bomb_turns[b] > 0u
            || V10_STATE->throat_chop_turns[b] > 0u) {
            return 1u;
        }
    }
    return 0u;
}

void hook_endturn_v10(void)
{
    sync_berry_watchers();
    refresh_fainted_party_tracking();

    if (!has_any_endturn_all()) {
        V8_STATE->endturn_step = 0u;
        V9_STATE->endturn_step_v9 = 0u;
        V10_STATE->endturn_step_v10 = 0u;
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
            if ((STATUSES3[b] & 0x0800u) != 0u && is_grounded_v10((u8)b))
                STATUSES3[b] &= ~0x1800u;
        }
    }

    if (BATTLE_OUTCOME != 0u) {
        V8_STATE->endturn_step = 0u;
        V9_STATE->endturn_step_v9 = 0u;
        V10_STATE->endturn_step_v10 = 0u;
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
                    ((volatile u32 *)cb_stack)[depth - 1u] = ENTRY_ENDTURN_V10_THUMB;
            } else {
                BATTLE_MAIN_FUNC = ENTRY_ENDTURN_V10_THUMB;
            }
            return;
        }
        BATTLE_MAIN_FUNC = ENTRY_ENDTURN_V10_THUMB;
    }

    /* Passos v8 (0..16) */
    while (V8_STATE->endturn_step < 17u) {
        u8 step = V8_STATE->endturn_step++;
        if (step < 4u) {
            if (V8_STATE->terrain_type == TERRAIN_GRASSY
                && V8_STATE->terrain_turns > 0u
                && is_bank_alive(step)
                && is_grounded_v10(step)
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
                    start_endturn_script_v10(BS_V8_ENDTURN_GRASSY);
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
                    start_endturn_script_v10(BS_V8_ENDTURN_MSGS + 8u * 0u);
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
                    start_endturn_script_v10(BS_V8_ENDTURN_MSGS + 8u * 1u);
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
                    start_endturn_script_v10(BS_V8_ENDTURN_MSGS + 8u * 2u);
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
                    start_endturn_script_v10(BS_V8_ENDTURN_MSGS + 8u * 3u);
                    return;
                }
            }
            continue;
        }
        if (step == 10u) {
            if (V8_STATE->gravity_turns > 0u) {
                V8_STATE->gravity_turns--;
                if (V8_STATE->gravity_turns == 0u) {
                    start_endturn_script_v10(BS_V8_ENDTURN_MSGS + 8u * 4u);
                    return;
                }
            }
            continue;
        }
        if (step == 11u) {
            if (V8_STATE->trick_room_turns > 0u) {
                V8_STATE->trick_room_turns--;
                if (V8_STATE->trick_room_turns == 0u) {
                    start_endturn_script_v10(BS_V8_ENDTURN_MSGS + 8u * 5u);
                    return;
                }
            }
            continue;
        }
        if (step == 12u) {
            if (V8_STATE->wonder_room_turns > 0u) {
                V8_STATE->wonder_room_turns--;
                if (V8_STATE->wonder_room_turns == 0u) {
                    start_endturn_script_v10(BS_V8_ENDTURN_MSGS + 8u * 6u);
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
                        start_endturn_script_v10(BS_V8_ENDTURN_MSGS + 8u * 7u);
                        return;
                    }
                }
            }
            continue;
        }
    }

    /* Passos v9 (0..8) */
    while (V9_STATE->endturn_step_v9 < 9u) {
        u8 step = V9_STATE->endturn_step_v9++;
        if (step < 4u) {
            if (is_bank_alive(step) && has_aqua_ring_v10(step) && !is_heal_blocked(step)) {
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
                    start_endturn_script_v10(BS_V9_ENDTURN_AQUA_RING);
                    return;
                }
            }
            continue;
        }
        if (step >= 4u && step < 8u) {
            u8 b = (u8)(step - 4u);
            if (is_bank_alive(b) && has_octolock_v10(b)) {
                volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
                if (m[0x1Au] > 0u || m[0x1Du] > 0u) {
                    V9_STATE->saved_tgt = TARGET;
                    V9_STATE->saved_atk = ATTACKER;
                    ATTACKER = V9_STATE->octolock_src[b] & 3u;
                    TARGET = b;
                    SCRIPTING_BATTLER = b;
                    start_endturn_script_v10(BS_V9_ENDTURN_OCTOLOCK);
                    return;
                }
            }
            continue;
        }
        if (step == 8u) {
            if (V9_STATE->magic_room_turns > 0u) {
                V9_STATE->magic_room_turns--;
                if (V9_STATE->magic_room_turns == 0u) {
                    start_endturn_script_v10(BS_V9_ENDTURN_MROOM);
                    return;
                }
            }
            continue;
        }
    }

    /* Passos v10 (0..11): Salt Cure (0..3), Syrup Bomb (4..7) e Throat Chop (8..11) */
    while (V10_STATE->endturn_step_v10 < 12u) {
        u8 step = V10_STATE->endturn_step_v10++;
        if (step < 4u) {
            u8 b = step;
            if (is_bank_alive(b) && has_salt_cure_v10(b)) {
                volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
                u16 max_hp = *(volatile u16 *)(m + 0x2Eu);
                u8 extra = (mon_has_type(b, 8u) || mon_has_type(b, 11u)) ? 1u : 0u; /* Steel(8) / Water(11): 1/4 */
                s32 dmg = (s32)(extra ? (max_hp >> 2) : (max_hp >> 3));
                if (dmg < 1)
                    dmg = 1;
                V10_STATE->saved_atk = ATTACKER;
                V10_STATE->saved_tgt = TARGET;
                TARGET = b;
                SCRIPTING_BATTLER = b;
                BATTLE_MOVE_DMG = dmg;
                MOVE_RESULT_FLAGS &= (u8)~0x29u;
                start_endturn_script_v10(BS_V10_ENDTURN_SALT_CURE);
                return;
            }
            continue;
        }
        if (step >= 4u && step < 8u) {
            u8 b = (u8)(step - 4u);
            if (is_bank_alive(b) && has_syrup_bomb_v10(b)) {
                V10_STATE->syrup_bomb_turns[b]--;
                if (V10_STATE->syrup_bomb_turns[b] == 0u)
                    V10_STATE->syrup_bomb_tag[b] = 0u;
                volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
                if (m[0x1Bu] > 0u) {
                    V10_STATE->saved_atk = ATTACKER;
                    V10_STATE->saved_tgt = TARGET;
                    ATTACKER = b ^ 1u;
                    TARGET = b;
                    SCRIPTING_BATTLER = b;
                    start_endturn_script_v10(BS_V10_ENDTURN_SYRUP);
                    return;
                }
            }
            continue;
        }
        if (step >= 8u && step < 12u) {
            u8 b = (u8)(step - 8u);
            if (V10_STATE->throat_chop_turns[b] > 0u) {
                if (V10_STATE->throat_chop_tag[b] != mon_tag(b)) {
                    V10_STATE->throat_chop_turns[b] = 0u;
                    V10_STATE->throat_chop_tag[b] = 0u;
                } else {
                    V10_STATE->throat_chop_turns[b]--;
                    if (V10_STATE->throat_chop_turns[b] == 0u) {
                        V10_STATE->throat_chop_tag[b] = 0u;
                        if (is_bank_alive(b)) {
                            SCRIPTING_BATTLER = b;
                            start_endturn_script_v10(BS_V10_ENDTURN_THROAT);
                            return;
                        }
                    }
                }
            }
            continue;
        }
    }

    V8_STATE->endturn_step = 0u;
    V9_STATE->endturn_step_v9 = 0u;
    V10_STATE->endturn_step_v10 = 0u;
    BATTLE_MAIN_FUNC = 0x08053221u;
    ORIG_BATTLE_TURN_PASSED();
}

void hook_restore_banks_v10(void)
{
    ATTACKER = V10_STATE->saved_atk;
    TARGET = V10_STATE->saved_tgt;
}

/* ==================== Hooks encadeados em CMD_TABLE_V10 ================= */

static u8 target_chose_damaging_move_after(u8 tgt)
{
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
    if (!found_after)
        return 0u;
    volatile u8 *tmon = BATTLE_MONS + 0x5Cu * tgt;
    u16 tmove;
    if ((*(volatile u32 *)(tmon + 0x54u) & 0x00001000u) != 0u) {
        tmove = LOCKED_MOVES[tgt];
    } else {
        u8 mslot = BATTLE_STRUCT_PTR[0x80u + tgt] & 3u;
        tmove = *(volatile u16 *)(tmon + 0x0Cu + 2u * mslot);
    }
    if (tmove == 0u || tmove >= 822u)
        return 0u;
    return (CATEGORY_TABLE[tmove] != 2u) ? 1u : 0u;
}

void hook_attackcanceler_v10(void)
{
    sync_berry_watchers();
    refresh_fainted_party_tracking();

    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    u16 move = CURRENT_MOVE;

    /* Limpa vulnerabilidade pós-Glaive Rush quando o usuário tenta agir novamente */
    if (V10_STATE->glaive_rush_tag[atk] != 0u)
        V10_STATE->glaive_rush_tag[atk] = 0u;

    const u8 *before = CURR_INSTR;
    PREV_ATTACKCANCELER_V9();
    if (CURR_INSTR != before + 1)
        return;

    V10_STATE->acted_turn_mask |= (u8)(1u << atk);

    /* Throat Chop (630): bloqueia golpes de som por 2 turnos */
    if (V10_STATE->throat_chop_turns[atk] > 0u
        && V10_STATE->throat_chop_tag[atk] == mon_tag(atk)
        && is_sound_move_v10(move)) {
        CURR_INSTR = BS_V10_THROAT_BLOCK;
        return;
    }

    /* Gigaton Hammer (780) e Blood Moon (785): não podem ser usados em turnos consecutivos */
    if (move == 780u || move == 785u) {
        u8 slot1 = (u8)((PARTY_INDEXES[atk] & 7u) + 1u);
        if (V10_STATE->prev_heavy_slot[atk] == slot1) {
            CURR_INSTR = BS_V10_CONSECUTIVE_FAIL;
            return;
        }
        V10_STATE->curr_heavy_slot[atk] = slot1;
    }

    /* Belch (558): exige que este slot da party já tenha comido uma Berry nesta batalha */
    if (move == 558u) {
        u8 side = FN_GET_SIDE(atk) & 1u;
        u8 slot = (u8)(PARTY_INDEXES[atk] & 7u);
        if (slot >= 6u || (V10_STATE->ate_berry_mask[side] & (1u << slot)) == 0u) {
            CURR_INSTR = BS_V10_FAIL_PP;
            return;
        }
    }

    /* Steel Roller (702): falha sem terreno ativo */
    if (move == 702u && (V8_STATE->terrain_type == TERRAIN_NONE || V8_STATE->terrain_turns == 0u)) {
        CURR_INSTR = BS_V10_FAIL_PP;
        return;
    }

    /* Burn Up (637) exige tipo Fire (10); Double Shock (779) exige tipo Electric (13) */
    if (move == 637u && !mon_has_type(atk, 10u)) {
        CURR_INSTR = BS_V10_FAIL_PP;
        return;
    }
    if (move == 779u && !mon_has_type(atk, 13u)) {
        CURR_INSTR = BS_V10_FAIL_PP;
        return;
    }

    /* Hyperspace Fury (613): exclusivo de Hoopa (#720); Aura Wheel (688): exclusivo de Morpeko (#877) */
    if (move == 613u && *(volatile u16 *)(BATTLE_MONS + 0x5Cu * atk) != 720u) {
        CURR_INSTR = BS_V10_FAIL_PP;
        return;
    }
    if (move == 688u && *(volatile u16 *)(BATTLE_MONS + 0x5Cu * atk) != 877u) {
        CURR_INSTR = BS_V10_FAIL_PP;
        return;
    }

    /* Sucker Punch (389) e Thunderclap (793): falham se o alvo já agiu ou escolheu golpe de status */
    if (move == 389u || move == 793u) {
        if (!target_chose_damaging_move_after(tgt)) {
            CURR_INSTR = BS_V10_FAIL_PP;
            return;
        }
    }

    /* Synchronoise (484): exige ao menos um tipo em comum com o alvo */
    if (move == 484u) {
        volatile u8 *am = BATTLE_MONS + 0x5Cu * atk;
        u8 a1 = am[0x22u], a2 = am[0x23u];
        u8 a3 = (V9_STATE->extra_type_tag[atk] == mon_tag(atk)) ? V9_STATE->extra_type[atk] : 0xFFu;
        u8 shared = mon_has_type(tgt, a1) || mon_has_type(tgt, a2) || (a3 < 19u && mon_has_type(tgt, a3));
        if (!shared) {
            CURR_INSTR = BS_V10_FAIL_PP;
            return;
        }
    }

    /* Last Resort (387): exige ter outros golpes conhecidos e já gastos >= 1 PP em todos eles */
    if (move == 387u) {
        volatile u8 *am = BATTLE_MONS + 0x5Cu * atk;
        u8 other_cnt = 0u, all_used = 1u;
        for (u32 s = 0u; s < 4u; ++s) {
            u16 mv = *(volatile u16 *)(am + 0x0Cu + 2u * s);
            if (mv != 0u && mv != 387u && mv < 822u) {
                other_cnt++;
                u8 base_pp = MOVE_TABLE[12u * mv + 4u];
                u8 bonus = (am[0x24u] >> (2u * s)) & 3u;
                u32 max_pp = (u32)base_pp + FN_UDIV32((u32)base_pp * (u32)bonus, 5u);
                if ((u32)am[0x25u + s] >= max_pp)
                    all_used = 0u;
            }
        }
        if (other_cnt == 0u || !all_used) {
            CURR_INSTR = BS_V10_FAIL_PP;
            return;
        }
    }

    /* Rastreamentos leves em golpes nativos */
    if (move == 474u) { /* Autotomize */
        u8 slot1 = (u8)((PARTY_INDEXES[atk] & 7u) + 1u);
        if (V10_STATE->autotomize_slot[atk] != slot1) {
            V10_STATE->autotomize_slot[atk] = slot1;
            V10_STATE->autotomize_count[atk] = 0u;
        }
        if (V10_STATE->autotomize_count[atk] < 250u)
            V10_STATE->autotomize_count[atk]++;
    } else if (move == 496u) { /* Echoed Voice */
        V10_STATE->echoed_used_turn = 1u;
    } else if (move == 495u) { /* Round */
        V10_STATE->round_used_turn++;
    }
}

void hook_accuracycheck_v10(void)
{
    u8 tgt = TARGET & 3u;
    u16 move = CURRENT_MOVE;

    /* Feint (364) remove Protect/Detect; Hyperspace Hole (589), Hyperspace Fury (613)
     * e Hyper Drill (774) atravessam Protect/Detect sem remover a proteção de outros ataques */
    u8 saved_prot = PROTECT_STRUCTS[16u * tgt];
    u8 bypass_prot = (move == 589u || move == 613u || move == 774u) ? 1u : 0u;
    if (move == 364u || bypass_prot)
        PROTECT_STRUCTS[16u * tgt] = (u8)(saved_prot & ~0x01u);

    /* Alvo vulnerável após usar Glaive Rush (754): ataques recebidos nunca erram */
    if (V10_STATE->glaive_rush_tag[tgt] != 0u
        && V10_STATE->glaive_rush_tag[tgt] == mon_tag(tgt)
        && (PROTECT_STRUCTS[16u * tgt] & 0x01u) == 0u
        && (STATUSES3[tgt] & 0x000400F8u) == 0u) {
        if (bypass_prot)
            PROTECT_STRUCTS[16u * tgt] = saved_prot;
        CURR_INSTR = CURR_INSTR + 7;
        return;
    }

    /* Golpes ofensivos com acc == 0 em MOVE_TABLE (ex.: Flower Trick 762, Kowtow Cleave 761,
     * Smart Strike 639, Disarming Voice 570, Tachyon Cutter 795, Clear Smog 498, Magnet Bomb 442,
     * False Surrender 698, Trump Card 376, Hyperspace Hole/Fury 589/613) nunca erram */
    if (move > 0u && move < 822u
        && CATEGORY_TABLE[move] != 2u
        && MOVE_TABLE[12u * move + 3u] == 0u
        && (PROTECT_STRUCTS[16u * tgt] & 0x01u) == 0u
        && (STATUSES3[tgt] & 0x000400F8u) == 0u) {
        if (bypass_prot)
            PROTECT_STRUCTS[16u * tgt] = saved_prot;
        CURR_INSTR = CURR_INSTR + 7;
        return;
    }

    /* Tempestades dos Gênios sob chuva nunca erram (724, 739, 740, 741) */
    if ((BATTLE_WEATHER & WEATHER_RAIN_MASK) != 0u
        && (move == 724u || move == 739u || move == 740u || move == 741u)
        && (PROTECT_STRUCTS[16u * tgt] & 0x01u) == 0u
        && (STATUSES3[tgt] & 0x000400F8u) == 0u) {
        if (bypass_prot)
            PROTECT_STRUCTS[16u * tgt] = saved_prot;
        CURR_INSTR = CURR_INSTR + 7;
        return;
    }

    /* Sacred Sword (529), Chip Away (497) e Darkest Lariat (618) ignoram estágio de evasão do alvo */
    volatile u8 *tmon = BATTLE_MONS + 0x5Cu * tgt;
    u8 saved_eva = tmon[0x1Fu];
    u8 ignore_eva = (move == 497u || move == 529u || move == 618u) ? 1u : 0u;
    if (ignore_eva)
        tmon[0x1Fu] = 6u;
    PREV_ACCURACYCHECK_V8();
    if (ignore_eva)
        tmon[0x1Fu] = saved_eva;
    if (bypass_prot)
        PROTECT_STRUCTS[16u * tgt] = saved_prot;
}

void hook_critcalc_v10(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    u8 ign_abil = (move == 659u || move == 660u || move == 667u) ? 1u : 0u;
    u8 t_abil = ign_abil ? 0u : effective_ability_v10(tgt);

    /* Golpes de acerto crítico garantido (100%): Storm Throw (479), Frost Breath (520),
     * Wicked Blow (711), Surging Strikes (712) e Flower Trick (762) */
    if (move == 479u || move == 520u || move == 711u || move == 712u || move == 762u) {
        CRIT_MULTIPLIER = (t_abil == 4u || t_abil == 75u) ? 1u : 2u;
        CURR_INSTR = CURR_INSTR + 1;
        return;
    }

    /* Golpes com razão crítica elevada (+1 estágio) combinada a outro efeito:
     * Snipe Shot (670), Esper Wing (733), Triple Arrows (736) e Ivy Cudgel (788) */
    volatile u8 *amon = BATTLE_MONS + 0x5Cu * atk;
    u32 saved_s2 = *(volatile u32 *)(amon + 0x54u);
    u8 boost_crit = (move == 670u || move == 733u || move == 736u || move == 788u) ? 1u : 0u;
    if (boost_crit)
        *(volatile u32 *)(amon + 0x54u) = saved_s2 | STATUS2_FOCUS_ENERGY;
    PREV_CRITCALC_V9();
    if (boost_crit)
        *(volatile u32 *)(amon + 0x54u) = saved_s2;
}

void hook_damage_v10(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *b = BATTLE_MONS + 0x5Cu * tgt;

    /* 1. Potências dinâmicas pré-cálculo */
    if (move == 358u) { /* Wake-Up Slap: 140 se alvo dormindo */
        DYNAMIC_POWER = ((*(volatile u32 *)(b + 0x50u) & 0x07u) != 0u) ? 140u : 70u;
    } else if (move == 362u) { /* Brine: 130 se HP <= 50% */
        u32 hp = *(volatile u16 *)(b + 0x2Au), mhp = *(volatile u16 *)(b + 0x2Eu);
        DYNAMIC_POWER = (hp * 2u <= mhp) ? 130u : 65u;
    } else if (move == 371u) { /* Payback: 100 se alvo já agiu no turno */
        DYNAMIC_POWER = ((V10_STATE->acted_turn_mask & (1u << tgt)) != 0u) ? 100u : 50u;
    } else if (move == 372u) { /* Assurance: 120 se alvo já sofreu dano no turno */
        DYNAMIC_POWER = ((V10_STATE->damaged_turn_mask & (1u << tgt)) != 0u) ? 120u : 60u;
    } else if (move == 376u) { /* Trump Card: 40/50/60/80/200 conforme PP restante */
        u8 mslot = BATTLE_STRUCT_PTR[0x80u + atk] & 3u;
        u8 rem_pp = a[0x25u + mslot];
        static const u8 tc_pwr[5] = {200u, 80u, 60u, 50u, 40u};
        DYNAMIC_POWER = tc_pwr[(rem_pp < 4u) ? rem_pp : 4u];
    } else if (move == 378u || move == 461u) { /* Wring Out / Crush Grip */
        u32 hp = *(volatile u16 *)(b + 0x2Au), mhp = *(volatile u16 *)(b + 0x2Eu);
        if (mhp == 0u)
            mhp = 1u;
        u32 pwr = 1u + FN_UDIV32(120u * hp, mhp);
        DYNAMIC_POWER = (u16)((pwr > 121u) ? 121u : pwr);
    } else if (move == 386u) { /* Punishment: 60 + 20 * boosts positivos (máx. 200) */
        u32 pwr = 60u;
        for (u32 i = 1u; i <= 7u; ++i) {
            u8 stg = b[0x18u + i];
            if (stg > 6u && stg <= 12u)
                pwr += 20u * (u32)(stg - 6u);
        }
        DYNAMIC_POWER = (u16)((pwr > 200u) ? 200u : pwr);
    } else if (move == 483u || move == 531u) { /* Heavy Slam / Heat Crash ajustado por Autotomize */
        u32 uw = effective_weight_hg(atk), tw = effective_weight_hg(tgt);
        u16 pwr = 40u;
        if (uw >= tw * 5u) pwr = 120u;
        else if (uw >= tw * 4u) pwr = 100u;
        else if (uw >= tw * 3u) pwr = 80u;
        else if (uw >= tw * 2u) pwr = 60u;
        DYNAMIC_POWER = pwr;
    } else if (move == 495u) { /* Round: 120 se aliado já cantou no turno */
        DYNAMIC_POWER = (V10_STATE->round_used_turn > 1u) ? 120u : 60u;
    } else if (move == 496u) { /* Echoed Voice: 40 + 40 * streak (máx. 200) */
        u32 pwr = 40u + 40u * (u32)V10_STATE->echoed_streak;
        DYNAMIC_POWER = (u16)((pwr > 200u) ? 200u : pwr);
    } else if (move == 513u) { /* Retaliate: 140 se aliado desmaiou no turno anterior */
        u8 side = FN_GET_SIDE(atk) & 1u;
        DYNAMIC_POWER = ((V10_STATE->ally_fainted_flags & (1u << side)) != 0u) ? 140u : 70u;
    } else if (move == 653u) { /* Stomping Tantrum (TM179): 150 se golpe anterior falhou */
        u8 boosted = ((V7_STATE->prev_failed_mask & (1u << atk)) != 0u
                      && V7_STATE->failed_pid[atk] == mon_tag(atk)) ? 1u : 0u;
        DYNAMIC_POWER = boosted ? 150u : 75u;
    } else if (move == 679u || move == 680u) { /* Bolt Beak / Fishious Rend: 170 se age antes do alvo */
        DYNAMIC_POWER = ((V10_STATE->acted_turn_mask & (1u << tgt)) == 0u) ? 170u : 85u;
    } else if (move == 693u) { /* Grav Apple: 120 sob Gravity */
        DYNAMIC_POWER = (V8_STATE->gravity_turns > 0u) ? 120u : 80u;
    } else if (move == 714u) { /* Dragon Energy: 150 * HP / MaxHP */
        u32 hp = *(volatile u16 *)(a + 0x2Au), mhp = *(volatile u16 *)(a + 0x2Eu);
        if (mhp == 0u)
            mhp = 1u;
        u32 pwr = FN_UDIV32(150u * hp, mhp);
        DYNAMIC_POWER = (u16)((pwr == 0u) ? 1u : pwr);
    } else if (move == 732u) { /* Barb Barrage: 120 se alvo envenenado */
        DYNAMIC_POWER = ((*(volatile u32 *)(b + 0x50u) & 0x88u) != 0u) ? 120u : 60u;
    } else if (move == 737u) { /* Infernal Parade: 120 se alvo com status não-volátil */
        DYNAMIC_POWER = (*(volatile u32 *)(b + 0x50u) != 0u) ? 120u : 60u;
    } else if (move == 746u) { /* Last Respects: 50 + 50 * aliados desmaiados na equipe */
        u8 side = FN_GET_SIDE(atk) & 1u;
        u8 mask = V10_STATE->known_fainted_mask[side];
        u32 cnt = 0u;
        for (u32 s = 0u; s < 6u; ++s) {
            if ((mask & (1u << s)) != 0u)
                cnt++;
        }
        DYNAMIC_POWER = (u16)(50u + 50u * cnt);
    } else if (move == 776u) { /* Rage Fist: 50 + 50 * hits sofridos (máx. 350) */
        DYNAMIC_POWER = (u16)(50u + 50u * (u32)get_rage_fist_hits(atk));
    } else if (move == 783u) { /* Psyblade: 120 em Electric Terrain */
        u8 et = (V8_STATE->terrain_type == TERRAIN_ELECTRIC && V8_STATE->terrain_turns > 0u) ? 1u : 0u;
        DYNAMIC_POWER = et ? 120u : 80u;
    } else if (move == 791u) { /* Fickle Beam: 30% de chance de dobrar para 160 BP */
        DYNAMIC_POWER = (FN_UMOD32((u32)FN_RANDOM(), 10u) < 3u) ? 160u : 80u;
    }

    /* 2. Substituições temporárias de atributos / estágios (restauradas logo após PREV_DAMAGE_V9) */
    u16 a_atk = *(volatile u16 *)(a + 0x02u), a_def = *(volatile u16 *)(a + 0x04u);
    u16 a_spa = *(volatile u16 *)(a + 0x08u), a_spd = *(volatile u16 *)(a + 0x0Au);
    u8  a_s_atk = a[0x19u], a_s_def = a[0x1Au], a_s_spa = a[0x1Cu], a_s_spd = a[0x1Du];

    u16 b_def = *(volatile u16 *)(b + 0x04u), b_spd = *(volatile u16 *)(b + 0x0Au);
    u8  b_s_def = b[0x1Au], b_s_spd = b[0x1Du];
    u8  b_abil = b[0x20u];

    /* Sunsteel Strike (659), Moongeist Beam (660) e Photon Geyser (667) ignoram habilidade defensiva */
    if (move == 659u || move == 660u || move == 667u)
        b[0x20u] = 0u;

    /* Nota: Wonder Room (V8_STATE->wonder_room_turns > 0) já troca Def <-> SpD brutos
     * dentro de PREV_DAMAGE_V9() -> hook_damage_v8(); para golpes especiais que miram a
     * Defesa física do alvo (Secret Sword / Photon Geyser físico), pré-igualamos ambos
     * os campos ao valor físico efetivo (b_spd sob Wonder Room, b_def caso contrário). */
    u16 tgt_phys_def = (V8_STATE->wonder_room_turns > 0u) ? b_spd : b_def;

    /* Secret Sword (544): golpe especial que atinge a Defesa física do alvo */
    if (move == 544u) {
        *(volatile u16 *)(b + 0x04u) = tgt_phys_def;
        *(volatile u16 *)(b + 0x0Au) = tgt_phys_def;
        b[0x1Du] = b[0x1Au];
    }

    /* Photon Geyser (667), Shell Side Arm (704), Tera Starstorm (790) e Tera Blast (804):
     * categoria Special (cat=1) usa Atk vs Def quando Atk efetivo > SpA efetivo */
    if (move == 667u || move == 704u || move == 790u || move == 804u) {
        u32 eff_atk = staged_stat(*(volatile u16 *)(a + 0x02u), a[0x19u]);
        u32 eff_spa = staged_stat(*(volatile u16 *)(a + 0x08u), a[0x1Cu]);
        if (eff_atk > eff_spa) {
            *(volatile u16 *)(a + 0x08u) = *(volatile u16 *)(a + 0x02u);
            a[0x1Cu] = a[0x19u];
            *(volatile u16 *)(b + 0x04u) = tgt_phys_def;
            *(volatile u16 *)(b + 0x0Au) = tgt_phys_def;
            b[0x1Du] = b[0x1Au];
        }
    }

    /* Sacred Sword (529), Chip Away (497) e Darkest Lariat (618) ignoram estágios de Def/SpD */
    if (move == 497u || move == 529u || move == 618u) {
        b[0x1Au] = 6u;
        b[0x1Du] = 6u;
    }

    /* Para Heavy Slam (483) e Heat Crash (531), evita que 0x0900C001 sobrescreva
     * DYNAMIC_POWER com o peso sem Autotomize, preservando tipo/categoria/STAB */
    if (move == 483u)
        CURRENT_MOVE = 232u; /* Metal Claw (Steel, Physical) */
    else if (move == 531u)
        CURRENT_MOVE = 7u;   /* Fire Punch (Fire, Physical) */

    PREV_DAMAGE_V9();

    CURRENT_MOVE = move;

    /* Restaura todos os campos temporários */
    *(volatile u16 *)(a + 0x02u) = a_atk;
    *(volatile u16 *)(a + 0x04u) = a_def;
    *(volatile u16 *)(a + 0x08u) = a_spa;
    *(volatile u16 *)(a + 0x0Au) = a_spd;
    a[0x19u] = a_s_atk;
    a[0x1Au] = a_s_def;
    a[0x1Cu] = a_s_spa;
    a[0x1Du] = a_s_spd;

    *(volatile u16 *)(b + 0x04u) = b_def;
    *(volatile u16 *)(b + 0x0Au) = b_spd;
    b[0x1Au] = b_s_def;
    b[0x1Du] = b_s_spd;
    b[0x20u] = b_abil;

    /* 3. Multiplicadores pós-dano */
    /* Knock Off (282, TM181): 1.5x (65 -> 97.5 BP) quando o alvo segura um item */
    if (move == 282u && *(volatile u16 *)(b + 0x30u) != 0u && BATTLE_MOVE_DMG > 0) {
        BATTLE_MOVE_DMG = (BATTLE_MOVE_DMG * 3) >> 1;
    }

    /* Hydro Steam (784): sob sol forte, reverte penalidade de 0.5x de Água para bônus de 1.5x (x3) */
    if (move == 784u && (BATTLE_WEATHER & WEATHER_SUN_MASK) != 0u && BATTLE_MOVE_DMG > 0) {
        BATTLE_MOVE_DMG = BATTLE_MOVE_DMG * 3;
    }

    /* Vulnerabilidade pós-Glaive Rush (754) no alvo: 2x de dano recebido */
    if (V10_STATE->glaive_rush_tag[tgt] != 0u
        && V10_STATE->glaive_rush_tag[tgt] == mon_tag(tgt)
        && BATTLE_MOVE_DMG > 0) {
        BATTLE_MOVE_DMG = BATTLE_MOVE_DMG * 2;
    }
}

void hook_typecalc_v10(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *b = BATTLE_MONS + 0x5Cu * tgt;

    /* 1. Adaptação de tipo dinâmico (BATTLE_STRUCT_PTR[0x13] = 0x40 | tipo) */
    if (move == 641u) { /* Revelation Dance: assume o tipo primário do usuário */
        BATTLE_STRUCT_PTR[0x13u] = (u8)(0x40u | (a[0x22u] & 0x1Fu));
    } else if (move == 688u) { /* Aura Wheel: alterna Electric (13) e Dark (17) */
        u8 dyn = ((V10_STATE->aura_wheel_hangry_mask & (1u << atk)) != 0u) ? 17u : 13u;
        BATTLE_STRUCT_PTR[0x13u] = (u8)(0x40u | dyn);
    } else if (move == 765u) { /* Raging Bull: adapta-se ao tipo de Tauros (Fighting/Fire/Water/Normal) */
        u8 dyn = 0u;
        if (mon_has_type(atk, 10u)) dyn = 10u;
        else if (mon_has_type(atk, 11u)) dyn = 11u;
        else if (mon_has_type(atk, 1u)) dyn = 1u;
        BATTLE_STRUCT_PTR[0x13u] = (u8)(0x40u | dyn);
    } else if (move == 788u) { /* Ivy Cudgel: adapta-se ao tipo secundário (Fire/Water/Rock/Grass) */
        u8 dyn = 12u;
        if (mon_has_type(atk, 10u)) dyn = 10u;
        else if (mon_has_type(atk, 11u)) dyn = 11u;
        else if (mon_has_type(atk, 5u)) dyn = 5u;
        BATTLE_STRUCT_PTR[0x13u] = (u8)(0x40u | dyn);
    } else if (V10_STATE->ion_deluge_active != 0u && move < 822u) {
        u8 cur_t = ((BATTLE_STRUCT_PTR[0x13u] & 0x40u) != 0u)
            ? (BATTLE_STRUCT_PTR[0x13u] & 0x1Fu)
            : MOVE_TABLE[12u * move + 2u];
        if (cur_t == 0u)
            BATTLE_STRUCT_PTR[0x13u] = (u8)(0x40u | 13u);
    }

    /* 2. Overrides temporários para Smack Down, Thousand Arrows, Freeze-Dry e habilidades ignoradas */
    u32 saved_s3 = STATUSES3[tgt];
    u8 saved_t1 = b[0x22u], saved_t2 = b[0x23u], saved_abil = b[0x20u];
    u8 saved_t3 = V9_STATE->extra_type[tgt];

    if (move == 659u || move == 660u || move == 667u)
        b[0x20u] = 0u;

    if (has_smack_down(tgt))
        STATUSES3[tgt] = saved_s3 | STATUS3_GROUNDED_OVER;

    /* Thousand Arrows (606): contra alvo não aterrado, causa 1x neutro de Ground no 1º impacto */
    u8 ta_neutral = 0u;
    if (move == 606u && !is_grounded_v10(tgt)) {
        ta_neutral = 1u;
        STATUSES3[tgt] = saved_s3 | STATUS3_GROUNDED_OVER;
        b[0x22u] = 0u;
        b[0x23u] = 0u;
        b[0x20u] = 0u;
        if (V9_STATE->extra_type_tag[tgt] == mon_tag(tgt))
            V9_STATE->extra_type[tgt] = 0u;
    }

    /* Freeze-Dry (569): super efetivo (2x) contra Water (11), modelado via substituição temporária p/ Grass (12) */
    if (move == 569u) {
        if (b[0x22u] == 11u) b[0x22u] = 12u;
        if (b[0x23u] == 11u) b[0x23u] = 12u;
        if (V9_STATE->extra_type_tag[tgt] == mon_tag(tgt) && V9_STATE->extra_type[tgt] == 11u)
            V9_STATE->extra_type[tgt] = 12u;
    }

    PREV_TYPECALC_V9();

    STATUSES3[tgt] = saved_s3;
    b[0x22u] = saved_t1;
    b[0x23u] = saved_t2;
    b[0x20u] = saved_abil;
    V9_STATE->extra_type[tgt] = saved_t3;
    if (ta_neutral)
        MOVE_RESULT_FLAGS &= (u8)~0x06u; /* força mensagem neutra 1x */

    /* 3. Flying Press (556): combina Fighting (1) + eficácia adicional de Flying (2) */
    if (move == 556u && (MOVE_RESULT_FLAGS & 0x29u) == 0u && BATTLE_MOVE_DMG > 0) {
        u8 m1 = type_effectiveness_mult(2u, saved_t1);
        u8 m2 = (saved_t2 != saved_t1) ? type_effectiveness_mult(2u, saved_t2) : 10u;
        u8 m3 = (V9_STATE->extra_type_tag[tgt] == mon_tag(tgt)
                 && saved_t3 < 19u && saved_t3 != saved_t1 && saved_t3 != saved_t2)
            ? type_effectiveness_mult(2u, saved_t3)
            : 10u;
        u32 num = (u32)m1 * (u32)m2 * (u32)m3;
        if (num == 0u) {
            BATTLE_MOVE_DMG = 0;
            MOVE_RESULT_FLAGS = (u8)((MOVE_RESULT_FLAGS & ~0x06u) | 0x08u);
        } else {
            s32 scaled = (s32)FN_UDIV32((u32)BATTLE_MOVE_DMG * num, 1000u);
            if (scaled < 1)
                scaled = 1;
            BATTLE_MOVE_DMG = scaled;
            if (num > 1000u) {
                if ((MOVE_RESULT_FLAGS & 0x04u) != 0u)
                    MOVE_RESULT_FLAGS &= (u8)~0x04u;
                else
                    MOVE_RESULT_FLAGS |= 0x02u;
            } else if (num < 1000u) {
                if ((MOVE_RESULT_FLAGS & 0x02u) != 0u)
                    MOVE_RESULT_FLAGS &= (u8)~0x02u;
                else
                    MOVE_RESULT_FLAGS |= 0x04u;
            }
        }
    }

    /* 4. Collision Course (768) e Electro Drift (769): +33% (4/3x) quando super efetivo */
    if ((move == 768u || move == 769u)
        && (MOVE_RESULT_FLAGS & 0x02u) != 0u
        && (MOVE_RESULT_FLAGS & 0x29u) == 0u
        && BATTLE_MOVE_DMG > 0) {
        BATTLE_MOVE_DMG = (s32)FN_UDIV32((u32)BATTLE_MOVE_DMG * 4u, 3u);
    }
}

void hook_datahpupdate_v10(void)
{
    if (CONTROLLER_EXEC_FLAGS != 0u) {
        PREV_DATAHPUPDATE_V7();
        return;
    }

    const u8 *before = CURR_INSTR;
    u8 script_arg = before[1];
    u8 bank = FN_GET_SCRIPT_BANK(script_arg) & 3u;
    u8 atk = ATTACKER & 3u;
    s32 dmg = BATTLE_MOVE_DMG;
    u8 res = MOVE_RESULT_FLAGS;

    PREV_DATAHPUPDATE_V7();

    if (CURR_INSTR == before)
        return;

    if (V10_STATE->endturn_step_v10 == 0u
        && script_arg == 0u
        && bank != atk
        && dmg > 0
        && (res & 0x29u) == 0u) {
        V10_STATE->damaged_turn_mask |= (u8)(1u << bank);
        inc_rage_fist_hits(bank);
    }
    sync_berry_watchers();
    refresh_fainted_party_tracking();
}

void hook_negativedamage_v10(void)
{
    u16 move = CURRENT_MOVE;
    /* Draining Kiss (573, TM037) e Oblivion Wing (605): drenam 75% do dano causado */
    if (move == 573u || move == 605u) {
        s32 dealt = HP_DEALT;
        if (dealt < 0)
            dealt = 0;
        s32 heal = (s32)(((u32)dealt * 3u) >> 2);
        if (heal < 1)
            heal = 1;
        BATTLE_MOVE_DMG = -heal;
        CURR_INSTR = CURR_INSTR + 1;
        return;
    }
    ORIG_NEGATIVEDAMAGE();
}

void hook_lowkick_v10(void)
{
    /* Usa WEIGHTS_TABLE Gen 1-9 (0x0900D000) + ajuste de Autotomize (474) */
    u32 w = effective_weight_hg(TARGET & 3u);
    u16 pwr;
    if (w < 100u) pwr = 20u;
    else if (w < 250u) pwr = 40u;
    else if (w < 500u) pwr = 60u;
    else if (w < 1000u) pwr = 80u;
    else if (w < 2000u) pwr = 100u;
    else pwr = 120u;
    DYNAMIC_POWER = pwr;
    CURR_INSTR = CURR_INSTR + 1;
}

/* ============= Fila de Mudanças de Atributos e Motor de Berries ========= */

static void start_stat_queue_v10(u8 target_bank, u8 qmode, const u8 *entries, u8 count)
{
    V10_STATE->saved_tgt = TARGET;
    V10_STATE->saved_atk = ATTACKER;
    TARGET = target_bank & 3u;
    V10_STATE->queue_mode = qmode;
    V10_STATE->stat_len = count;
    V10_STATE->stat_idx = 0u;
    for (u8 i = 0u; i < count && i < 4u; ++i)
        V10_STATE->stat_queue[i] = entries[i];
    CURR_INSTR = BS_V10_STAT_QUEUE_LOOP;
}

void hook_berry_step_v10(void);

void hook_stat_queue_step_v10(void)
{
    const u8 *up_ptr = (const u8 *)read_u32_unaligned(CURR_INSTR);
    const u8 *dn_ptr = (const u8 *)read_u32_unaligned(CURR_INSTR + 4);

    if (V10_STATE->stat_idx < V10_STATE->stat_len && is_bank_alive(TARGET & 3u)) {
        u8 chg = V10_STATE->stat_queue[V10_STATE->stat_idx++];
        ANIM_ARG1_BYTE = 0u;
        STAT_BUFF_ADDR = chg;
        CURR_INSTR = ((chg & 0x80u) != 0u) ? dn_ptr : up_ptr;
        return;
    }

    u8 qmode = V10_STATE->queue_mode;
    TARGET = V10_STATE->saved_tgt;
    ATTACKER = V10_STATE->saved_atk;

    if (qmode == 1u) {
        CURR_INSTR = BS_MULTIHIT_MOVEEND;
    } else if (qmode == 2u) {
        hook_berry_step_v10();
    } else {
        CURR_INSTR = BS_MOVE_END;
    }
}

/* Fases de consumo de Berry:
 *   phase 0: aplica efeito da Berry (HP / status / PP / stat / foco) em berry_consumer
 *   phase 1: pós-efeito da Berry (ex.: +2 Def em Stuff Cheeks, próximo banco em Teatime, ou fim)
 */
void hook_berry_step_v10(void)
{
    u8 mode = V10_STATE->berry_mode;

    if (V10_STATE->berry_phase == 0u) {
        V10_STATE->berry_phase = 1u;
        u8 c = V10_STATE->berry_consumer & 3u;
        u16 item = (V10_STATE->active_berry_idx != 0u) ? (u16)(132u + V10_STATE->active_berry_idx) : 0u;
        if (is_bank_alive(c) && is_berry_item(item)) {
            u8 he = NEW_ITEMS_TABLE[44u * (u32)item + 18u];
            u8 param = NEW_ITEMS_TABLE[44u * (u32)item + 19u];
            volatile u8 *cm = BATTLE_MONS + 0x5Cu * c;
            u16 hp = *(volatile u16 *)(cm + 0x2Au);
            u16 max_hp = *(volatile u16 *)(cm + 0x2Eu);

            if ((he == 1u || (he >= 10u && he <= 14u)) && !is_heal_blocked(c) && hp < max_hp) {
                s32 heal;
                if (item == 142u) { /* Sitrus Berry: 25% MaxHP (Gen 4-9) */
                    heal = (s32)(max_hp >> 2);
                } else if (he >= 10u && he <= 14u) { /* Figy..Iapapa: 33% MaxHP */
                    heal = (s32)FN_UDIV32((u32)max_hp, 3u);
                } else {
                    heal = (s32)param;
                }
                if (heal < 1)
                    heal = 1;
                SCRIPTING_BATTLER = c;
                BATTLE_MOVE_DMG = -heal;
                MOVE_RESULT_FLAGS &= (u8)~0x29u;
                CURR_INSTR = BS_V10_BERRY_HP_STEP;
                return;
            }
            if ((he >= 2u && he <= 6u) || he == 8u || he == 9u) {
                u32 s1 = *(volatile u32 *)(cm + 0x50u);
                u32 s2 = *(volatile u32 *)(cm + 0x54u);
                u32 mask1 = 0u;
                if (he == 2u) mask1 = 0x40u;
                else if (he == 3u) mask1 = 0x07u;
                else if (he == 4u) mask1 = 0x88u;
                else if (he == 5u) mask1 = 0x10u;
                else if (he == 6u) mask1 = 0x20u;
                else if (he == 9u) mask1 = 0xFFu;

                u8 cured_s2 = ((he == 8u || he == 9u) && (s2 & STATUS2_CONFUSION) != 0u) ? 1u : 0u;
                if (cured_s2)
                    *(volatile u32 *)(cm + 0x54u) = s2 & ~STATUS2_CONFUSION;

                if ((s1 & mask1) != 0u) {
                    *(volatile u32 *)(cm + 0x50u) = s1 & ~mask1;
                    SCRIPTING_BATTLER = c;
                    emit_status_sync_v10(c);
                    CURR_INSTR = BS_V10_BERRY_STATUS_STEP;
                    return;
                }
            }
            if (he == 7u) { /* Leppa Berry: restaura até +10 PP */
                s32 pick = -1;
                for (u32 pass = 0u; pass < 2u && pick < 0; ++pass) {
                    for (u32 s = 0u; s < 4u; ++s) {
                        u16 mv = *(volatile u16 *)(cm + 0x0Cu + 2u * s);
                        if (mv == 0u || mv >= 822u)
                            continue;
                        u8 base_pp = MOVE_TABLE[12u * mv + 4u];
                        u8 bonus = (cm[0x24u] >> (2u * s)) & 3u;
                        u32 max_pp = (u32)base_pp + FN_UDIV32((u32)base_pp * (u32)bonus, 5u);
                        u8 cur_pp = cm[0x25u + s];
                        if ((pass == 0u && cur_pp == 0u && max_pp > 0u)
                            || (pass == 1u && (u32)cur_pp < max_pp)) {
                            pick = (s32)s;
                            u32 npp = (u32)cur_pp + (u32)param;
                            if (npp > max_pp)
                                npp = max_pp;
                            SCRIPTING_BATTLER = c;
                            emit_pp_sync_v10(c, (u8)s, (u8)npp);
                            CURR_INSTR = BS_V10_BERRY_PP_STEP;
                            return;
                        }
                    }
                }
            }
            if (he >= 15u && he <= 19u) { /* Liechi..Apicot: +1 em stat 1..5 */
                u8 st = (u8)((he - 14u) | 0x10u);
                start_stat_queue_v10(c, 2u, &st, 1u);
                return;
            }
            if (he == 20u) { /* Lansat Berry: Focus Energy */
                *(volatile u32 *)(cm + 0x54u) |= STATUS2_FOCUS_ENERGY;
            }
            if (he == 21u) { /* Starf Berry: +2 em atributo aleatório 1..5 */
                u8 cand[5];
                u8 n = 0u;
                for (u8 st = 1u; st <= 5u; ++st) {
                    if (cm[0x18u + st] < 12u)
                        cand[n++] = st;
                }
                if (n > 0u) {
                    u8 chosen = (u8)(cand[FN_UMOD32((u32)FN_RANDOM(), (u32)n)] | 0x20u);
                    start_stat_queue_v10(c, 2u, &chosen, 1u);
                    return;
                }
            }
        }
    }

    /* Fase 1+: continuação específica por modo */
    if (mode == 1u) { /* Stuff Cheeks: após efeito da Berry, +2 Def no usuário */
        V10_STATE->berry_mode = 0u;
        u8 atk = ATTACKER & 3u;
        if (is_bank_alive(atk)) {
            u8 def2 = 0x22u;
            start_stat_queue_v10(atk, 0u, &def2, 1u);
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    if (mode == 2u) { /* Teatime: avança para o próximo banco com Berry */
        u32 total = BATTLERS_COUNT;
        if (total > 4u)
            total = 4u;
        while (V10_STATE->teatime_idx < total) {
            u8 b = V10_STATE->teatime_idx++;
            if (!is_bank_alive(b))
                continue;
            u16 it = *(volatile u16 *)(BATTLE_MONS + 0x5Cu * b + 0x30u);
            if (is_berry_item(it)) {
                V10_STATE->active_berry_idx = (u8)(it - 132u);
                V10_STATE->berry_consumer = b;
                V10_STATE->berry_phase = 0u;
                mark_ate_berry_bank(b);
                clear_held_item_sync(b);
                CURR_INSTR = BS_V10_BERRY_WAIT_STEP;
                return;
            }
        }
        V10_STATE->berry_mode = 0u;
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    V10_STATE->berry_mode = 0u;
    CURR_INSTR = BS_MOVE_END;
}

/* ============== Dispatcher de Golpes (EFF_V10_DISPATCH = 255) =========== */

void hook_dispatch_v10(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;

    if (move == 672u) { /* Stuff Cheeks */
        u16 it = *(volatile u16 *)(BATTLE_MONS + 0x5Cu * atk + 0x30u);
        if (V9_STATE->magic_room_turns > 0u || !is_berry_item(it)) {
            CURR_INSTR = BS_V10_FAIL_PP;
            return;
        }
        CURR_INSTR = BS_V10_STUFF_CHEEKS;
        return;
    }
    if (move == 677u) { /* Teatime */
        u32 total = BATTLERS_COUNT;
        if (total > 4u)
            total = 4u;
        u8 any_berry = 0u;
        for (u32 b = 0u; b < total; ++b) {
            if (is_bank_alive((u8)b) && is_berry_item(*(volatile u16 *)(BATTLE_MONS + 0x5Cu * b + 0x30u)))
                any_berry = 1u;
        }
        if (!any_berry) {
            CURR_INSTR = BS_V10_FAIL_PP;
            return;
        }
        CURR_INSTR = BS_V10_TEATIME;
        return;
    }
    if (move == 730u) { /* Victory Dance: +1 Atk, +1 Def, +1 Spe */
        CURR_INSTR = BS_V10_VICTORY_DANCE;
        return;
    }
    if (move == 565u) { /* Ion Deluge */
        CURR_INSTR = BS_V10_ION_DELUGE;
        return;
    }
    if (move == 631u) { /* Pollen Puff: cura aliado em 50% ou causa dano 90 BP em oponente */
        if (FN_GET_SIDE(atk) == FN_GET_SIDE(tgt) && tgt != atk) {
            CURR_INSTR = BS_V10_POLLEN_ALLY;
        } else {
            CURR_INSTR = BS_EFFECT_HIT;
        }
        return;
    }
    if (move == 712u || move == 757u) { /* Surging Strikes / Triple Dive (3 hits) */
        CURR_INSTR = BS_V10_TRIPLE_DIVE;
        return;
    }
    if (move == 668u) { /* Double Iron Bash (2 hits + 30% flinch) */
        CURR_INSTR = BS_V10_DOUBLE_IRON_BASH;
        return;
    }
    if (move == 752u) { /* Population Bomb (até 10 hits com precisão independente) */
        CURR_INSTR = BS_V10_POPULATION_BOMB;
        return;
    }
    if (move == 703u) { /* Scale Shot (TM200: 2-5 hits + -1 Def / +1 Spe) */
        CURR_INSTR = BS_V10_SCALE_SHOT;
        return;
    }
    if (move == 786u) { /* Matcha Gotcha (dreno 50% + 20% queimadura) */
        CURR_INSTR = BS_V10_MATCHA_GOTCHA;
        return;
    }
    if (move == 658u) { /* Spectral Thief (rouba boosts positivos antes do golpe) */
        CURR_INSTR = BS_V10_SPECTRAL_THIEF;
        return;
    }
    CURR_INSTR = BS_V10_STANDARD_HIT;
}

/* ============= Pós-Impacto e Inicializadores de Sub-Scripts ============= */

void hook_post_hit_v10(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *am = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *tm = BATTLE_MONS + 0x5Cu * tgt;

    /* Ações de status acionadas pelos próprios scripts dedicados */
    if (move == 672u) { /* Stuff Cheeks: inicia consumo da Berry do usuário */
        u16 it = *(volatile u16 *)(am + 0x30u);
        V10_STATE->active_berry_idx = is_berry_item(it) ? (u8)(it - 132u) : 0u;
        V10_STATE->berry_consumer = atk;
        V10_STATE->berry_mode = 1u;
        V10_STATE->berry_phase = 0u;
        mark_ate_berry_bank(atk);
        clear_held_item_sync(atk);
        CURR_INSTR = BS_V10_BERRY_WAIT_STEP;
        return;
    }
    if (move == 677u) { /* Teatime: inicia varredura de todos os bancos ativos */
        V10_STATE->berry_mode = 2u;
        V10_STATE->berry_phase = 1u;
        V10_STATE->teatime_idx = 0u;
        hook_berry_step_v10();
        return;
    }
    if (move == 730u) { /* Victory Dance: +1 Atk, +1 Def, +1 Spe */
        static const u8 vd[3] = {0x11u, 0x12u, 0x13u};
        start_stat_queue_v10(atk, 0u, vd, 3u);
        return;
    }
    if (move == 565u) { /* Ion Deluge */
        V10_STATE->ion_deluge_active = 1u;
        CURR_INSTR = msg_tail_v10(7u);
        return;
    }
    if (move == 631u && FN_GET_SIDE(atk) == FN_GET_SIDE(tgt) && tgt != atk) { /* Pollen Puff no aliado */
        if (!is_bank_alive(tgt) || is_heal_blocked(tgt)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        u16 hp = *(volatile u16 *)(tm + 0x2Au);
        u16 mhp = *(volatile u16 *)(tm + 0x2Eu);
        if (hp >= mhp) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        s32 heal = (s32)((mhp + 1u) >> 1);
        BATTLE_MOVE_DMG = -heal;
        MOVE_RESULT_FLAGS &= (u8)~0x29u;
        return; /* CURR_INSTR já aponta para 0x09 (attackanimation) após callasm */
    }
    if (move == 658u) { /* Spectral Thief (pré-dano): rouba estágios positivos do alvo */
        u8 stole = 0u;
        for (u32 i = 1u; i <= 7u; ++i) {
            u8 ts = tm[0x18u + i];
            if (ts > 6u && ts <= 12u) {
                u8 gain = (u8)(ts - 6u);
                u8 as = am[0x18u + i];
                u32 ns = (u32)as + (u32)gain;
                am[0x18u + i] = (u8)((ns > 12u) ? 12u : ns);
                tm[0x18u + i] = 6u;
                stole = 1u;
            }
        }
        CURR_INSTR = stole ? BS_V10_SPECTRAL_CONT : BS_HIT_CALC_START;
        return;
    }
    if (move == 703u) { /* Scale Shot (pós-loop multi-hit): -1 Def, +1 Spe no usuário */
        if ((MOVE_RESULT_FLAGS & 0x29u) == 0u && is_bank_alive(atk)) {
            static const u8 ss[2] = {0x92u, 0x13u};
            start_stat_queue_v10(atk, 1u, ss, 2u);
            return;
        }
        CURR_INSTR = BS_MULTIHIT_MOVEEND;
        return;
    }

    /* Para golpes de dano padrão: aborta se falhou / errou / imune */
    if ((MOVE_RESULT_FLAGS & 0x29u) != 0u) {
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Feint (364): remove Protect / Detect do alvo para o restante do turno */
    if (move == 364u) {
        PROTECT_STRUCTS[16u * tgt] &= (u8)~0x01u;
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Ice Spinner (753) e Steel Roller (702): limpam o terreno ativo */
    if (move == 753u || move == 702u) {
        if (is_bank_alive(atk) && V8_STATE->terrain_turns > 0u) {
            V8_STATE->terrain_turns = 0u;
            V8_STATE->terrain_type = TERRAIN_NONE;
            CURR_INSTR = msg_tail_v10(1u);
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Plasma Fists (666): converte golpes Normal em Electric pelo resto do turno */
    if (move == 666u) {
        if (!V10_STATE->ion_deluge_active) {
            V10_STATE->ion_deluge_active = 1u;
            CURR_INSTR = msg_tail_v10(7u);
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Burn Up (637) e Double Shock (779): removem Fire (10) / Electric (13) do usuário */
    if (move == 637u && is_bank_alive(atk)) {
        remove_mon_type(atk, 10u);
        CURR_INSTR = msg_tail_v10(8u);
        return;
    }
    if (move == 779u && is_bank_alive(atk)) {
        remove_mon_type(atk, 13u);
        CURR_INSTR = msg_tail_v10(9u);
        return;
    }

    /* Glaive Rush (754): deixa o usuário vulnerável até sua próxima ação */
    if (move == 754u && is_bank_alive(atk)) {
        V10_STATE->glaive_rush_tag[atk] = mon_tag(atk);
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Fell Stinger (561): +3 Atk se nocauteou o alvo */
    if (move == 561u) {
        if (!is_bank_alive(tgt) && is_bank_alive(atk)) {
            u8 atk3 = 0x31u;
            start_stat_queue_v10(atk, 0u, &atk3, 1u);
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Auto-modificações garantidas de estágios no usuário (mesmo se o alvo desmaiou!) */
    if (is_bank_alive(atk)) {
        if (move == 359u || move == 620u) { /* Hammer Arm / Ice Hammer: -1 Spe */
            u8 s = 0x93u;
            start_stat_queue_v10(atk, 0u, &s, 1u);
            return;
        }
        if (move == 751u) { /* Spin Out: -2 Spe */
            u8 s = 0xA3u;
            start_stat_queue_v10(atk, 0u, &s, 1u);
            return;
        }
        if (move == 613u || move == 646u) { /* Hyperspace Fury / Clanging Scales: -1 Def */
            u8 s = 0x92u;
            start_stat_queue_v10(atk, 0u, &s, 1u);
            return;
        }
        if (move == 766u) { /* Make It Rain: -1 SpA */
            u8 s = 0x94u;
            start_stat_queue_v10(atk, 0u, &s, 1u);
            return;
        }
        if (move == 553u) { /* V-create: -1 Def, -1 SpD, -1 Spe */
            static const u8 vc[3] = {0x92u, 0x95u, 0x93u};
            start_stat_queue_v10(atk, 0u, vc, 3u);
            return;
        }
        if (move == 688u) { /* Aura Wheel: +1 Spe e alterna modo Full Belly / Hangry */
            V10_STATE->aura_wheel_hangry_mask ^= (u8)(1u << atk);
            u8 s = 0x13u;
            start_stat_queue_v10(atk, 0u, &s, 1u);
            return;
        }
        if (move == 763u || move == 725u) { /* Torch Song / Mystical Power: +1 SpA */
            u8 s = 0x14u;
            start_stat_queue_v10(atk, 0u, &s, 1u);
            return;
        }
        if (move == 764u || move == 733u) { /* Aqua Step / Esper Wing: +1 Spe */
            u8 s = 0x13u;
            start_stat_queue_v10(atk, 0u, &s, 1u);
            return;
        }
        if (move == 722u) { /* Psyshield Bash: +1 Def */
            u8 s = 0x12u;
            start_stat_queue_v10(atk, 0u, &s, 1u);
            return;
        }
    }

    /* Demais efeitos secundários sobre o alvo exigem alvo vivo e sem Substitute */
    if (!is_bank_alive(tgt) || has_substitute(tgt)) {
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Smack Down (478) e Thousand Arrows (606): derrubam alvos não aterrados */
    if (move == 478u || move == 606u) {
        if (!has_smack_down(tgt) && !is_grounded_v10(tgt)) {
            V10_STATE->smacked_down_tag[tgt] = mon_tag(tgt);
            CURR_INSTR = msg_tail_v10(0u);
            return;
        }
        V10_STATE->smacked_down_tag[tgt] = mon_tag(tgt);
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Dragon Tail (521) e Circle Throw (508): forçam troca aleatória (CMD 0x8F) */
    if (move == 521u || move == 508u) {
        if (!is_bank_alive(atk)) {
            CURR_INSTR = BS_MOVE_END;
            return;
        }
        if (effective_ability_v10(tgt) == 21u) { /* Suction Cups */
            CURR_INSTR = BS_SUCTION_ANCHORED;
            return;
        }
        if ((STATUSES3[tgt] & STATUS3_INGRAIN) != 0u) {
            CURR_INSTR = BS_INGRAIN_ANCHORED;
            return;
        }
        CURR_INSTR = BS_V10_PHAZE_TAIL;
        return;
    }

    /* Pluck (365) e Bug Bite (449, TM182): roubam e consomem a Berry do alvo */
    if (move == 365u || move == 449u) {
        u16 it = *(volatile u16 *)(tm + 0x30u);
        if (is_bank_alive(atk) && effective_ability_v10(tgt) != 60u && is_berry_item(it)) {
            V10_STATE->active_berry_idx = (u8)(it - 132u);
            V10_STATE->berry_consumer = atk;
            V10_STATE->berry_mode = 3u;
            V10_STATE->berry_phase = 0u;
            mark_ate_berry_bank(atk);
            clear_held_item_sync(tgt);
            CURR_INSTR = BS_V10_BERRY_WAIT_STEP;
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Incinerate (509): destrói a Berry do alvo sem consumi-la */
    if (move == 509u) {
        u16 it = *(volatile u16 *)(tm + 0x30u);
        if (effective_ability_v10(tgt) != 60u && is_berry_item(it)) {
            clear_held_item_sync(tgt);
            CURR_INSTR = BS_V10_INCINERATE_TAIL;
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Throat Chop (630): impede golpes de som por 2 turnos */
    if (move == 630u) {
        if (V10_STATE->throat_chop_turns[tgt] == 0u || V10_STATE->throat_chop_tag[tgt] != mon_tag(tgt)) {
            V10_STATE->throat_chop_tag[tgt] = mon_tag(tgt);
            V10_STATE->throat_chop_turns[tgt] = 2u;
            CURR_INSTR = msg_tail_v10(2u);
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Salt Cure (756): instala cura em sal residual (1/8 HP; 1/4 em Water/Steel) */
    if (move == 756u) {
        if (!has_salt_cure_v10(tgt)) {
            V10_STATE->salt_cure_tag[tgt] = mon_tag(tgt);
            CURR_INSTR = msg_tail_v10(3u);
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Syrup Bomb (787): cobre em calda por 3 turnos (-1 Spe por turno) */
    if (move == 787u) {
        if (!has_syrup_bomb_v10(tgt)) {
            V10_STATE->syrup_bomb_tag[tgt] = mon_tag(tgt);
            V10_STATE->syrup_bomb_turns[tgt] = 3u;
            CURR_INSTR = msg_tail_v10(4u);
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Clear Smog (498): zera todas as mudanças de estágios do alvo */
    if (move == 498u) {
        for (u32 i = 1u; i <= 7u; ++i)
            tm[0x18u + i] = 6u;
        CURR_INSTR = msg_tail_v10(5u);
        return;
    }

    /* Core Enforcer (642): suprime habilidade se o alvo já agiu neste turno */
    if (move == 642u) {
        if ((V10_STATE->acted_turn_mask & (1u << tgt)) != 0u
            && (STATUSES3[tgt] & STATUS3_GASTRO_ACID) == 0u) {
            STATUSES3[tgt] |= STATUS3_GASTRO_ACID;
            CURR_INSTR = msg_tail_v10(6u);
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Wake-Up Slap (358): desperta alvo adormecido */
    if (move == 358u) {
        u32 s1 = *(volatile u32 *)(tm + 0x50u);
        if ((s1 & 0x07u) != 0u) {
            *(volatile u32 *)(tm + 0x50u) = s1 & ~0x07u;
            emit_status_sync_v10(tgt);
            CURR_INSTR = BS_V10_SLEEP_CURE_TAIL;
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Sparkling Aria (619): cura queimadura do alvo */
    if (move == 619u) {
        u32 s1 = *(volatile u32 *)(tm + 0x50u);
        if ((s1 & 0x10u) != 0u) {
            *(volatile u32 *)(tm + 0x50u) = s1 & ~0x10u;
            emit_status_sync_v10(tgt);
            CURR_INSTR = BS_V10_BURN_CURE_TAIL;
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Trava de troca em impacto: Thousand Waves (607), Spirit Shackle (617), Anchor Shot (632), Jaw Lock (671) */
    if (move == 607u || move == 617u || move == 632u || move == 671u) {
        if (move == 671u && is_bank_alive(atk))
            *(volatile u32 *)(am + 0x54u) |= STATUS2_ESCAPE_PREVENTION;
        if ((*(volatile u32 *)(tm + 0x54u) & STATUS2_ESCAPE_PREVENTION) == 0u) {
            CURR_INSTR = BS_V10_TRAP_TAIL;
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Dire Claw (721): 50% de chance de infligir Poison, Paralysis ou Sleep (1/3 cada) */
    if (move == 721u && *(volatile u32 *)(tm + 0x50u) == 0u) {
        if ((FN_RANDOM() & 1u) == 0u) {
            u32 r = FN_UMOD32((u32)FN_RANDOM(), 3u);
            static const u8 dc_eff[3] = {0x02u, 0x05u, 0x01u};
            MOVE_EFFECT_BYTE = dc_eff[r];
            CURR_INSTR = BS_V10_PRIMARY_EFF_TAIL;
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Malignant Chain (796): 50% de chance de Badly Poison (0x06) */
    if (move == 796u && *(volatile u32 *)(tm + 0x50u) == 0u) {
        if ((FN_RANDOM() & 1u) == 0u) {
            MOVE_EFFECT_BYTE = 0x06u;
            CURR_INSTR = BS_V10_PRIMARY_EFF_TAIL;
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Triple Arrows (736): 50% -1 Def + 30% Flinch no alvo */
    if (move == 736u) {
        if (FN_UMOD32((u32)FN_RANDOM(), 10u) < 3u) {
            MOVE_EFFECT_BYTE = 0x08u; /* Flinch */
        }
        if ((FN_RANDOM() & 1u) == 0u && tm[0x1Au] > 0u) {
            u8 d1 = 0x92u;
            start_stat_queue_v10(tgt, 0u, &d1, 1u);
            return;
        }
        if (MOVE_EFFECT_BYTE == 0x08u) {
            CURR_INSTR = BS_V10_PRIMARY_EFF_TAIL;
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Eerie Spell (720): reduz em até 3 PP o último golpe usado pelo alvo (ou slot 0) */
    if (move == 720u) {
        for (u32 s = 0u; s < 4u; ++s) {
            u16 mv = *(volatile u16 *)(tm + 0x0Cu + 2u * s);
            if (mv != 0u && tm[0x25u + s] > 0u) {
                u8 cur = tm[0x25u + s];
                u8 npp = (cur > 3u) ? (u8)(cur - 3u) : 0u;
                SCRIPTING_BATTLER = tgt;
                emit_pp_sync_v10(tgt, (u8)s, npp);
                V10_STATE->berry_mode = 0u;
                V10_STATE->berry_phase = 1u;
                CURR_INSTR = BS_V10_BERRY_WAIT_STEP;
                return;
            }
        }
    }

    CURR_INSTR = BS_MOVE_END;
}
