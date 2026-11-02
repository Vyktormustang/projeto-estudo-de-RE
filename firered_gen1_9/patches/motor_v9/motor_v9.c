/*
 * Payload nativo Thumb (ARM7TDMI) do motor_v9 — FireRed Gen 1-9 (PT-BR).
 *
 * Implementa as familias finais de golpes de subida de nivel antes omitidos
 * (49 golpes / +368 entradas em learnsets_motor_v9.csv), encadeado de forma
 * limpa sobre o motor_v8 sem tocar saves pessoais nem estruturas persistentes:
 *
 *  - Familia 1 (Tipos e vulnerabilidade elemental): Soak (486), Magic Powder
 *    (675), Reflect Type (512), Trick-or-Treat (563), Forest's Curse (567) e
 *    Tar Shot (674), com suporte a 3o tipo efemero (STAB + efetividade) e 2x
 *    de Fogo em alvos cobertos por Tar Shot.
 *  - Familia 2 (Habilidades nativas Gen 3 e eletrificacao): Gastro Acid (380),
 *    Worry Seed (388, acordando alvos adormecidos), Entrainment (493), Doodle
 *    (759) e Electrify (578).
 *  - Familia 3 (Trocas, divisoes, inversao e sinergias de atributos): Power
 *    Trick (379), Speed Swap (638), Power Split (470), Guard Split (469),
 *    Power Swap (384), Guard Swap (385), Heart Swap (391), Topsy-Turvy (572),
 *    Acupressure (367), Decorate (684), Spicy Extract (750), Venom Drench
 *    (595), Toxic Thread (627), Rototiller (559), Flower Shield (575),
 *    Magnetic Flux (598), Gear Up (629) e Strength Sap (623, com Liquid Ooze
 *    e bloqueio por Psychic Noise / Clear Body / Hyper Cutter).
 *  - Familia 4 (Sacrificio de HP, clerigo, cura continua, critico e pivot):
 *    Final Gambit (514), Fillet Away (760), Clangorous Soul (682), No Retreat
 *    (673), Shed Tail (770), Aqua Ring (392), Laser Focus (628), Psycho Shift
 *    (375), Purify (640), Take Heart (743), Jungle Healing (710), Lunar
 *    Blessing (742), Healing Wish (361), Lunar Dance (460) e Dark Void (463,
 *    restrito a Darkrai #491).
 *  - Familia 5 (Copia, controle de ordem de acao e prisao): Copycat (383),
 *    After You (494), Quash (510), Octolock (678) e Fairy Lock (583).
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

/* Estado efemero do motor_v7 em 0x0203FC00..0x0203FC5F (somente leitura). */
struct V7BattleState {
    u8 stat_rose_mask;
    u8 passed_canceler_mask;
    u8 parting_dropped;
    u8 heal_block_turns[4];
    u8 pad0;
    u32 heal_block_pid[4];
    u32 cheer_minus1_pid[4];
};

/* Estado efemero do motor_v8 em 0x0203FC60..0x0203FC9F (somente leitura). */
struct V8BattleState {
    u8 terrain_type;
    u8 terrain_turns;
    u8 trick_room_turns;
    u8 wonder_room_turns;
    u8 gravity_turns;
    u8 tailwind_turns[2];
    u8 aurora_veil_turns[2];
    u8 stealth_rock[2];
    u8 toxic_spikes[2];
    u8 sticky_web[2];
    u8 magnet_rise_turns[4];
    u8 endturn_step;
    u8 switchin_hazard_step;
    u8 switchin_bank;
    u8 saved_target;
    u32 magnet_rise_pid[4];
    u32 switchin_tag;
};

/* Estado efemero do motor_v9 em 0x0203FCA0..0x0203FD1F (128 B, fora de saves). */
struct V9BattleState {
    u32 active_tag[4];          /* 0x00..0x0F: tag de identidade por battler */
    u32 octolock_src_tag[4];    /* 0x10..0x1F: tag de quem aplicou Octolock */
    u16 last_used_move;         /* 0x20..0x21: ultimo golpe executado (Copycat) */
    u16 work_u16;               /* 0x22..0x23: valor temporario (Final Gambit / Sap) */
    u8 aqua_ring_mask;          /* 0x24: bitmask de Aqua Ring ativo */
    u8 tar_shot_mask;           /* 0x25: bitmask de Tar Shot ativo */
    u8 no_retreat_mask;         /* 0x26: bitmask de No Retreat ja usado */
    u8 gastro_acid_mask;        /* 0x27: bitmask de Gastro Acid ativo */
    u8 electrified_mask;        /* 0x28: bitmask de Electrify neste turno */
    u8 extra_type[4];           /* 0x29..0x2C: 3o tipo (0=nenhum, 7=Ghost, 12=Grass) */
    u8 laser_focus_turns[4];    /* 0x2D..0x30: contador de Laser Focus (2 -> 1 -> 0) */
    u8 octolock_active[4];      /* 0x31..0x34: 1 se preso por Octolock */
    u8 octolock_trapper[4];     /* 0x35..0x38: banco que aplicou Octolock */
    u8 fairy_lock_turns;        /* 0x39: contador de Fairy Lock (2 -> 1 -> 0) */
    u8 fairy_lock_mask;         /* 0x3A: bancos marcados por Fairy Lock */
    u8 healing_wish_pending[2]; /* 0x3B..0x3C: por lado (0=nao, 1=HWish, 2=LunarDance) */
    u8 shed_tail_sub_hp[4];     /* 0x3D..0x40: HP do Substitute a transferir */
    u8 endturn_step;            /* 0x41: cursor de fim de turno do motor_v9 */
    u8 saved_target;            /* 0x42: backup de TARGET em filas/loops */
    u8 saved_attacker;          /* 0x43: backup de ATTACKER em Octolock */
    u8 q_len;                   /* 0x44: tamanho da fila de mudancas de atributo */
    u8 q_pos;                   /* 0x45: cursor da fila de mudancas de atributo */
    u8 q_after_mode;            /* 0x46: acao pos-fila (0=end, 1=no_retreat, 2=tar_shot, 3=toxic_thread) */
    u8 work_idx;                /* 0x47: cursor auxiliar (Cleric / Dark Void / PP) */
    u8 work_bank;               /* 0x48: banco auxiliar */
    u8 work_mode;               /* 0x49: modo auxiliar */
    u8 q_bank[12];              /* 0x4A..0x55: bancos da fila de atributos */
    u8 q_stat[12];              /* 0x56..0x61: bytes statChanger da fila */
    u8 pad[2];                  /* 0x62..0x63: alinhamento a 4 bytes (100 B total) */
};

#define V7_STATE                ((volatile struct V7BattleState *)0x0203FC00u)
#define V8_STATE                ((volatile struct V8BattleState *)0x0203FC60u)
#define V9_STATE                ((volatile struct V9BattleState *)0x0203FCA0u)

/* Simbolos verificados de RAM da engine FireRed Gen 1-9 */
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
#define PROTECT_STRUCTS         ((volatile u8 *)0x020216CCu)
#define MOVE_EFFECT_BYTE        (*(volatile u8 *)0x020216C3u)
#define MULTISTRING_CHOOSER     (*(volatile u8 *)0x020216C5u)
#define BATTLE_OUTCOME          (*(volatile u8 *)0x020216C8u)
#define BATTLE_WEATHER          (*(volatile u16 *)0x0202175Cu)
#define SCRIPTING_BATTLER       (*(volatile u8 *)0x0202181Fu)
#define STAT_CHANGER_BYTE       (*(volatile u8 *)0x02021822u)
#define STAT_ANIM_PLAYED        (*(volatile u8 *)0x02021823u)
#define BATTLE_STRUCT_PTR       (*(volatile u8 *volatile *)0x0202182Cu)
#define BATTLE_RESOURCES_PTR    (*(volatile u8 *volatile *)0x02021838u)
#define ENEMY_PARTY             ((const u8 *)0x0203A734u)
#define PLAYER_PARTY            ((const u8 *)0x0203A98Cu)
#define BATTLE_MAIN_FUNC        (*(volatile u32 *)0x03005318u)

/* Tabelas ROM */
#define MOVE_TABLE              ((const u8 *)0x09000000u)
#define SCRIPT_TABLE_ROM        ((const u8 *const *)0x0900A000u)
#define TYPE_EFFECT_TABLE       ((const u8 *)0x08200C18u)
#define STAT_STAGE_RATIOS       ((const u8 *)0x086BC7BCu)

/* Enderecos fixos de BattleScripts em SCRIPTS_V9 (0x090C6000) e nativos */
#define BS_V9_ENDTURN_AQUA_RING ((const u8 *)0x090C6000u)
#define BS_V9_ENDTURN_OCTOLOCK  ((const u8 *)0x090C6020u)
#define BS_V9_STAT_QUEUE        ((const u8 *)0x090C6080u)
#define BS_V9_HEALING_WISH_IN   ((const u8 *)0x090C6100u)
#define BS_V9_LUNAR_DANCE_IN    ((const u8 *)0x090C6140u)
#define BS_V9_WORRY_SEED_WOKE   ((const u8 *)0x090C6180u)
#define BS_V9_CANT_ESCAPE_END   ((const u8 *)0x090C61A0u)
#define BS_V9_LIQUID_OOZE_TAIL  ((const u8 *)0x090C61C0u)
#define BS_V9_SLEEP_EFF         ((const u8 *)0x090C61E0u)
#define BS_V9_STR_TAILS         ((const u8 *)0x090C6200u)

#define BS_HEAL_BLOCK_CANCEL    ((const u8 *)0x090BF000u)
#define BS_DOESNT_AFFECT        ((const u8 *)0x081853DCu)
#define BS_MOVE_END             ((const u8 *)0x081853F6u)
#define BS_BUT_IT_FAILED        ((const u8 *)0x0818689Au)
#define BS_POISON_EFF           ((const u8 *)0x08187C7Du)
#define BS_BURN_EFF             ((const u8 *)0x08187C8Bu)
#define BS_PARALYSIS_EFF        ((const u8 *)0x08187CA7u)
#define BS_TOXIC_EFF            ((const u8 *)0x08187CC0u)

#define ENTRY_ENDTURN_V8_ADDR   0x090C3019u
#define ENTRY_ENDTURN_V9_ADDR   0x090C9011u

/* Encadeamento com motor_v8 / motor_v7 / funcoes nativas */
#define PREV_BATTLE_INIT_V8     ((void (*)(void))0x090C3001u)
#define PREV_TURN_START_V8      ((void (*)(void))0x090C3009u)
#define PREV_ENDTURN_V8         ((void (*)(void))0x090C3019u)
#define PREV_ATTACKCANCELER_V8  ((void (*)(void))0x090C3021u)
#define PREV_CRITCALC_V7        ((void (*)(void))0x090C0019u)
#define PREV_TYPECALC_V8        ((void (*)(void))0x090C3039u)
#define PREV_SWITCHINEFFECTS_V8 ((void (*)(void))0x090C3059u)

#define ORIG_ACCURACYCHECK      ((void (*)(void))0x08057F2Du)
#define ORIG_BATTLE_TURN_PASSED ((void (*)(void))0x08053221u)
#define FN_TURN_VALUES_CLEANUP  ((void (*)(u8))0x080543A5u)
#define FN_MODULATE_TYPE_EFF    ((void (*)(u8))0x080587C1u)
#define FN_DO_FIELD_ENDTURN     ((u8 (*)(void))0x0806D069u)
#define FN_GET_SIDE             ((u8 (*)(u8))0x08024685u)
#define FN_OAK_TUTORIAL         ((u8 (*)(void))0x0803B575u)
#define FN_EMIT_SET_MON_DATA    ((void (*)(u8, u8, u8, u8, const void *))0x08049DF5u)
#define FN_GET_SCRIPT_BANK      ((u8 (*)(u8))0x0806C535u)
#define FN_MARK_BUFFER_EXEC     ((void (*)(u8))0x0806C8BDu)
#define FN_BS_PUSH              ((void (*)(const u8 *))0x0806CB2Du)
#define FN_ABILITY_EFFECTS      ((u8 (*)(u8, u8, u8, u8, u16))0x0806F4DDu)
#define FN_GET_MOVE_TARGET      ((u8 (*)(u16, u8))0x08071DE1u)
#define FN_GET_MON_DATA         ((u32 (*)(const void *, u32, const void *))0x0810A96Du)
#define FN_RANDOM               ((u16 (*)(void))0x0812E9C5u)
#define FN_UDIV32               ((u32 (*)(u32, u32))0x08172B3Du)
#define FN_UMOD32               ((u32 (*)(u32, u32))0x08172B4Du)

/* Indices de strings em BS_V9_STR_TAILS (0x01A4 + idx) */
enum {
    TAIL_SOAK = 0,
    TAIL_MAGIC_POWDER = 1,
    TAIL_REFLECT_TYPE = 2,
    TAIL_TRICK_OR_TREAT = 3,
    TAIL_FORESTS_CURSE = 4,
    TAIL_GASTRO_ACID = 5,
    TAIL_WORRY_SEED = 6,
    TAIL_ENTRAINMENT = 7,
    TAIL_DOODLE = 8,
    TAIL_ELECTRIFY = 9,
    TAIL_POWER_TRICK = 10,
    TAIL_SPEED_SWAP = 11,
    TAIL_POWER_SPLIT = 12,
    TAIL_GUARD_SPLIT = 13,
    TAIL_POWER_SWAP = 14,
    TAIL_GUARD_SWAP = 15,
    TAIL_HEART_SWAP = 16,
    TAIL_TOPSY_TURVY = 17,
    TAIL_TAR_SHOT = 18,
    TAIL_FAIRY_LOCK = 19,
    TAIL_AQUA_RING_SET = 20,
    TAIL_AQUA_RING_HEAL = 21,
    TAIL_LASER_FOCUS = 22,
    TAIL_ATK_HEALED = 23,
    TAIL_SCR_HEALED = 24,
    TAIL_SCR_CURED = 25,
    TAIL_DARK_VOID_BLOCK = 26,
    TAIL_HEALING_WISH_CAME = 27,
    TAIL_LUNAR_DANCE_CAME = 28,
    TAIL_AFTER_YOU = 29,
    TAIL_QUASH = 30,
    TAIL_LIQUID_OOZE = 31,
    TAIL_TGT_WOKE_UP = 32,
    TAIL_ATK_CANT_ESCAPE = 33
};

static u32 read_u32_unaligned(const u8 *p)
{
    return (u32)p[0] | ((u32)p[1] << 8) | ((u32)p[2] << 16) | ((u32)p[3] << 24);
}

static u32 mon_tag(u8 bank)
{
    volatile u8 *m = BATTLE_MONS + 0x5Cu * (bank & 3u);
    u32 pid = *(volatile u32 *)(m + 0x4Cu);
    u32 slot = PARTY_INDEXES[bank & 3u];
    return 0x80000000u | ((slot & 7u) << 28) | (pid & 0x0FFFFFFFu);
}

static void sync_battler_v9(u8 b)
{
    b &= 3u;
    u32 tag = mon_tag(b);
    if (V9_STATE->active_tag[b] != tag) {
        V9_STATE->active_tag[b] = tag;
        u8 inv = (u8)~(1u << b);
        V9_STATE->aqua_ring_mask &= inv;
        V9_STATE->tar_shot_mask &= inv;
        V9_STATE->no_retreat_mask &= inv;
        V9_STATE->gastro_acid_mask &= inv;
        V9_STATE->extra_type[b] = 0u;
        V9_STATE->laser_focus_turns[b] = 0u;
        V9_STATE->octolock_active[b] = 0u;
    }
}

static u8 is_bank_present_alive(u8 b)
{
    b &= 3u;
    if (b >= BATTLERS_COUNT || (ABSENT_BATTLERS & (1u << b)) != 0u)
        return 0u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
    return (*(volatile u16 *)(m + 0x2Au) > 0u) ? 1u : 0u;
}

static u8 is_behind_substitute(u8 b)
{
    volatile u8 *m = BATTLE_MONS + 0x5Cu * (b & 3u);
    return ((*(volatile u32 *)(m + 0x54u) & 0x01000000u) != 0u) ? 1u : 0u;
}

static u8 is_heal_blocked(u8 b)
{
    b &= 3u;
    if (V7_STATE->heal_block_turns[b] == 0u)
        return 0u;
    if (V7_STATE->heal_block_pid[b] != mon_tag(b)) {
        V7_STATE->heal_block_turns[b] = 0u;
        return 0u;
    }
    return 1u;
}

static u8 has_type_v9(u8 b, u8 typ)
{
    b &= 3u;
    sync_battler_v9(b);
    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
    return (m[0x22u] == typ || m[0x23u] == typ || V9_STATE->extra_type[b] == typ) ? 1u : 0u;
}

static u8 is_magnet_risen_v8(u8 b)
{
    b &= 3u;
    if (V8_STATE->magnet_rise_turns[b] == 0u)
        return 0u;
    if (V8_STATE->magnet_rise_pid[b] != mon_tag(b) || V8_STATE->gravity_turns > 0u)
        return 0u;
    return 1u;
}

static u8 is_battler_grounded_v9(u8 b)
{
    b &= 3u;
    if ((STATUSES3[b] & 0x00000008u) != 0u)
        return 0u;
    if (V8_STATE->gravity_turns > 0u || (STATUSES3[b] & 0x00002000u) != 0u)
        return 1u;
    if (is_magnet_risen_v8(b))
        return 0u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
    if (m[0x22u] == 2u || m[0x23u] == 2u)
        return 0u;
    if (*(volatile u16 *)(m + 0x20u) == 26u)
        return 0u;
    return 1u;
}

static u8 has_viable_party_replacement(u8 bank)
{
    u8 side = FN_GET_SIDE(bank & 3u);
    /* Pokemon selvagem nunca faz troca em Healing Wish / Lunar Dance / Shed Tail. */
    if (side == 1u && (BATTLE_TYPE_FLAGS & 0x08u) == 0u)
        return 0u;
    const u8 *party = (side == 0u) ? PLAYER_PARTY : ENEMY_PARTY;
    u16 active0 = PARTY_INDEXES[bank & 3u];
    u16 active2 = 0xFFFFu;
    if ((BATTLE_TYPE_FLAGS & 0x01u) != 0u) {
        u8 partner = (u8)((bank ^ 2u) & 3u);
        if ((ABSENT_BATTLERS & (1u << partner)) == 0u)
            active2 = PARTY_INDEXES[partner];
    }
    for (u32 i = 0u; i < 6u; ++i) {
        if (i == active0 || i == active2)
            continue;
        const u8 *mon = party + 100u * i;
        if (FN_GET_MON_DATA(mon, 0x0Bu, 0) != 0u
            && FN_GET_MON_DATA(mon, 0x2Du, 0) == 0u
            && FN_GET_MON_DATA(mon, 0x39u, 0) > 0u) {
            return 1u;
        }
    }
    return 0u;
}

static u8 calc_slot_max_pp(volatile u8 *m, u8 slot)
{
    u16 move = *(volatile u16 *)(m + 0x0Cu + 2u * slot);
    if (move == 0u || move >= 822u)
        return 0u;
    u32 base_pp = MOVE_TABLE[12u * move + 4u];
    u32 bonus = ((u32)m[0x24u] >> (2u * slot)) & 3u;
    return (u8)(base_pp + FN_UDIV32(base_pp * 20u * bonus, 100u));
}

static u8 any_move_pp_below_max(u8 b)
{
    volatile u8 *m = BATTLE_MONS + 0x5Cu * (b & 3u);
    for (u8 s = 0u; s < 4u; ++s) {
        u8 max_pp = calc_slot_max_pp(m, s);
        if (max_pp > 0u && m[0x25u + s] < max_pp)
            return 1u;
    }
    return 0u;
}

static void start_endturn_script_v9(const u8 *bs_ptr)
{
    CURR_INSTR = bs_ptr;
    volatile u8 *cb_stack = *(volatile u8 **)(BATTLE_RESOURCES_PTR + 0x0Cu);
    u8 depth = cb_stack[0x20u];
    cb_stack[0x20u] = (u8)(depth + 1u);
    ((volatile u32 *)cb_stack)[depth] = BATTLE_MAIN_FUNC;
    CURR_ACTION_FUNC_ID = 0u;
    BATTLE_MAIN_FUNC = 0x08054B91u;
}

static void queue_reset(u8 after_mode)
{
    V9_STATE->saved_target = TARGET;
    V9_STATE->q_len = 0u;
    V9_STATE->q_pos = 0u;
    V9_STATE->q_after_mode = after_mode;
}

static void queue_push(u8 bank, u8 stat_id, u8 stages, u8 is_down)
{
    if (V9_STATE->q_len >= 12u)
        return;
    u8 idx = V9_STATE->q_len++;
    V9_STATE->q_bank[idx] = bank & 3u;
    V9_STATE->q_stat[idx] = (u8)((stat_id & 7u) | ((stages & 7u) << 4) | (is_down ? 0x80u : 0u));
}

static u8 is_copycat_banned_move(u16 m)
{
    /* Golpes que Copycat nao pode copiar (Gen 4-9 + equivalentes nativos). */
    return (m == 0u || m >= 822u
            || m == 18u  || m == 46u       /* Whirlwind, Roar */
            || m == 68u  || m == 102u      /* Counter, Mimic */
            || m == 118u || m == 119u      /* Metronome, Mirror Move */
            || m == 144u || m == 165u      /* Transform, Struggle */
            || m == 166u || m == 168u      /* Sketch, Thief */
            || m == 182u || m == 194u      /* Protect, Destiny Bond */
            || m == 197u || m == 203u      /* Detect, Endure */
            || m == 214u || m == 243u      /* Sleep Talk, Mirror Coat */
            || m == 264u || m == 266u      /* Focus Punch, Follow Me */
            || m == 270u || m == 271u      /* Helping Hand, Trick */
            || m == 274u || m == 289u      /* Assist, Snatch */
            || m == 343u || m == 364u      /* Covet, Feint */
            || m == 383u || m == 409u      /* Copycat, Switcheroo (se mapeado) */
            || m == 509u || m == 511u      /* Circle Throw, Dragon Tail */
            || m == 771u || m == 770u)     /* Chilly Reception, Shed Tail */
        ? 1u : 0u;
}

/* ==================== Ciclo de Vida e Fim de Turno ======================= */

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
    V9_STATE->endturn_step = 0u;
    for (u8 b = 0u; b < 4u; ++b) {
        sync_battler_v9(b);
        if (V9_STATE->laser_focus_turns[b] > 0u)
            V9_STATE->laser_focus_turns[b]--;
    }
    PREV_TURN_START_V8();
}

static u8 has_any_v9_endturn_effect(void)
{
    if (V9_STATE->aqua_ring_mask != 0u || V9_STATE->fairy_lock_turns > 0u)
        return 1u;
    for (u8 b = 0u; b < 4u; ++b) {
        if (V9_STATE->octolock_active[b] != 0u)
            return 1u;
    }
    return 0u;
}

void hook_endturn_v9(void)
{
    if (!has_any_v9_endturn_effect()) {
        V9_STATE->endturn_step = 0u;
        BATTLE_MAIN_FUNC = ENTRY_ENDTURN_V8_ADDR;
        PREV_ENDTURN_V8();
        return;
    }

    if (CONTROLLER_EXEC_FLAGS != 0u)
        return;

    if (BATTLE_OUTCOME != 0u) {
        V9_STATE->endturn_step = 0u;
        BATTLE_MAIN_FUNC = ENTRY_ENDTURN_V8_ADDR;
        PREV_ENDTURN_V8();
        return;
    }

    /* Executa DoFieldEndTurnEffects nativo primeiro, preservando retorno para v9. */
    if (BATTLE_STRUCT_PTR[3] < 10u) {
        FN_TURN_VALUES_CLEANUP(1u);
        BATTLE_MAIN_FUNC = 0x08053221u;
        u8 fld_busy = FN_DO_FIELD_ENDTURN();
        if (fld_busy != 0u) {
            if (BATTLE_MAIN_FUNC == 0x08054B91u) {
                volatile u8 *cb_stack = *(volatile u8 **)(BATTLE_RESOURCES_PTR + 0x0Cu);
                u8 depth = cb_stack[0x20u];
                if (depth > 0u)
                    ((volatile u32 *)cb_stack)[depth - 1u] = ENTRY_ENDTURN_V9_ADDR;
            } else {
                BATTLE_MAIN_FUNC = ENTRY_ENDTURN_V9_ADDR;
            }
            return;
        }
        BATTLE_MAIN_FUNC = ENTRY_ENDTURN_V9_ADDR;
    }

    while (V9_STATE->endturn_step < 9u) {
        u8 step = V9_STATE->endturn_step++;

        /* Passos 0..3: Aqua Ring cura 1/16 do HP maximo por turno */
        if (step < 4u) {
            sync_battler_v9(step);
            if ((V9_STATE->aqua_ring_mask & (1u << step)) != 0u
                && is_bank_present_alive(step)
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
                    BATTLE_MAIN_FUNC = ENTRY_ENDTURN_V9_ADDR;
                    start_endturn_script_v9(BS_V9_ENDTURN_AQUA_RING);
                    return;
                }
            }
            continue;
        }

        /* Passos 4..7: Octolock reduz Def -1 e Sp. Def -1 enquanto ambos em campo */
        if (step >= 4u && step < 8u) {
            u8 b = (u8)(step - 4u);
            sync_battler_v9(b);
            if (V9_STATE->octolock_active[b] != 0u) {
                u8 src = V9_STATE->octolock_trapper[b] & 3u;
                sync_battler_v9(src);
                if (!is_bank_present_alive(b)
                    || !is_bank_present_alive(src)
                    || mon_tag(src) != V9_STATE->octolock_src_tag[b]) {
                    V9_STATE->octolock_active[b] = 0u;
                } else {
                    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
                    if (m[0x1Au] > 0u || m[0x1Du] > 0u) {
                        V9_STATE->saved_attacker = ATTACKER;
                        V9_STATE->saved_target = TARGET;
                        ATTACKER = src;
                        TARGET = b;
                        BATTLE_MAIN_FUNC = ENTRY_ENDTURN_V9_ADDR;
                        start_endturn_script_v9(BS_V9_ENDTURN_OCTOLOCK);
                        return;
                    }
                }
            }
            continue;
        }

        /* Passo 8: Fairy Lock decrementa contador e libera prisao ao expirar */
        if (step == 8u) {
            if (V9_STATE->fairy_lock_turns > 0u) {
                V9_STATE->fairy_lock_turns--;
                if (V9_STATE->fairy_lock_turns == 0u) {
                    for (u8 b = 0u; b < 4u; ++b) {
                        sync_battler_v9(b);
                        if ((V9_STATE->fairy_lock_mask & (1u << b)) != 0u
                            && (V9_STATE->no_retreat_mask & (1u << b)) == 0u
                            && V9_STATE->octolock_active[b] == 0u) {
                            volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
                            *(volatile u32 *)(m + 0x54u) &= ~0x04000000u;
                        }
                    }
                    V9_STATE->fairy_lock_mask = 0u;
                }
            }
            continue;
        }
    }

    V9_STATE->endturn_step = 0u;
    BATTLE_MAIN_FUNC = ENTRY_ENDTURN_V8_ADDR;
    PREV_ENDTURN_V8();
}

void hook_octolock_restore_v9(void)
{
    ATTACKER = V9_STATE->saved_attacker;
    TARGET = V9_STATE->saved_target;
}

/* =================== Hooks Relocados da CMD_TABLE_V9 ===================== */

void hook_attackcanceler_v9(void)
{
    const u8 *before = CURR_INSTR;
    PREV_ATTACKCANCELER_V8();
    if (CURR_INSTR != before + 1)
        return;

    u8 atk = ATTACKER & 3u;
    sync_battler_v9(atk);
    V9_STATE->work_idx = 0u;
    V9_STATE->work_mode = 0u;

    /* Electrify converte o tipo do golpe deste battler em Eletrico (13). */
    if ((V9_STATE->electrified_mask & (1u << atk)) != 0u)
        BATTLE_STRUCT_PTR[0x13u] = (u8)(0x40u | 13u);

    /* Registra o ultimo golpe executado para Copycat (383). */
    u16 move = CURRENT_MOVE;
    if (!is_copycat_banned_move(move))
        V9_STATE->last_used_move = move;
}

void hook_critcalc_v9(void)
{
    PREV_CRITCALC_V7();

    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    sync_battler_v9(atk);
    if (V9_STATE->laser_focus_turns[atk] == 0u)
        return;
    if ((BATTLE_TYPE_FLAGS & 0x00010200u) != 0u || FN_OAK_TUTORIAL() != 0u)
        return;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    u16 t_ab = *(volatile u16 *)(t + 0x20u);
    if (t_ab == 4u || t_ab == 75u)
        return;
    CRIT_MULTIPLIER = 2u;
}

static u8 lookup_type_eff(u8 atk_type, u8 def_type, u8 foresight)
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
            if (after_fe && foresight)
                return 10u;
            return p[2];
        }
        p += 3;
    }
    return 10u;
}

void hook_typecalc_v9(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    sync_battler_v9(atk);
    sync_battler_v9(tgt);

    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    volatile u8 *bstruct = BATTLE_STRUCT_PTR;
    u8 mtype = (bstruct[0x13u] & 0x40u)
        ? (bstruct[0x13u] & 0x3Fu)
        : ((move < 822u) ? MOVE_TABLE[12u * move + 2u] : 0u);

    /* STAB do 3o tipo adicionado por Trick-or-Treat (7) ou Forest's Curse (12). */
    u8 atk_et = V9_STATE->extra_type[atk];
    if (atk_et != 0u && atk_et == mtype && a[0x22u] != mtype && a[0x23u] != mtype && move != 165u) {
        BATTLE_MOVE_DMG = (s32)FN_UDIV32((u32)BATTLE_MOVE_DMG * 15u, 10u);
    }

    PREV_TYPECALC_V8();

    if (move == 165u || (MOVE_RESULT_FLAGS & 0x09u) != 0u)
        return;

    /* Efetividade contra o 3o tipo do alvo (Trick-or-Treat / Forest's Curse). */
    u8 tgt_et = V9_STATE->extra_type[tgt];
    if (tgt_et != 0u && tgt_et != t[0x22u] && tgt_et != t[0x23u]) {
        u8 foresight = ((*(volatile u32 *)(t + 0x54u) & 0x20000000u) != 0u) ? 1u : 0u;
        u8 mult = lookup_type_eff(mtype, tgt_et, foresight);
        if (mult != 10u)
            FN_MODULATE_TYPE_EFF(mult);
    }

    /* Tar Shot: dobra eficacia de golpes de Fogo (10) contra o alvo marcado. */
    if ((MOVE_RESULT_FLAGS & 0x09u) == 0u
        && (V9_STATE->tar_shot_mask & (1u << tgt)) != 0u
        && mtype == 10u) {
        FN_MODULATE_TYPE_EFF(20u);
    }
}

void hook_switchineffects_v9(void)
{
    const u8 *instr = CURR_INSTR;
    u8 b = FN_GET_SCRIPT_BANK(instr[1]) & 3u;
    sync_battler_v9(b);

    /* Antes dos hazards de entrada: se o substituto ja entra ferido/statusado/PP gasto,
     * Healing Wish / Lunar Dance cura primeiro (evitando KO prematuro por Stealth Rock). */
    if (V8_STATE->switchin_hazard_step == 0u && is_bank_present_alive(b)) {
        u8 side0 = FN_GET_SIDE(b);
        u8 mode0 = V9_STATE->healing_wish_pending[side0];
        if (mode0 != 0u) {
            volatile u8 *m0 = BATTLE_MONS + 0x5Cu * b;
            u16 hp0 = *(volatile u16 *)(m0 + 0x2Au);
            u16 max0 = *(volatile u16 *)(m0 + 0x2Eu);
            u32 st0 = *(volatile u32 *)(m0 + 0x50u);
            if (hp0 < max0 || st0 != 0u || (mode0 == 2u && any_move_pp_below_max(b))) {
                V9_STATE->healing_wish_pending[side0] = 0u;
                V9_STATE->work_bank = b;
                V9_STATE->work_mode = mode0;
                V9_STATE->work_idx = 0u;
                SCRIPTING_BATTLER = b;
                FN_BS_PUSH(instr);
                CURR_INSTR = (mode0 == 2u) ? BS_V9_LUNAR_DANCE_IN : BS_V9_HEALING_WISH_IN;
                return;
            }
        }
    }

    PREV_SWITCHINEFFECTS_V8();
    if (CURR_INSTR != instr + 2)
        return;

    sync_battler_v9(b);
    if (!is_bank_present_alive(b))
        return;

    /* Apos hazards (Gen 8/9): se entrou saudavel e sofreu dano/status de hazards, cura agora;
     * caso contrario mantem o desejo armazenado para um aliado futuro. */
    u8 side = FN_GET_SIDE(b);
    u8 mode = V9_STATE->healing_wish_pending[side];
    if (mode == 0u)
        return;

    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
    u16 hp = *(volatile u16 *)(m + 0x2Au);
    u16 max_hp = *(volatile u16 *)(m + 0x2Eu);
    u32 st1 = *(volatile u32 *)(m + 0x50u);
    u8 needs = (hp < max_hp || st1 != 0u || (mode == 2u && any_move_pp_below_max(b))) ? 1u : 0u;
    if (!needs)
        return;

    V9_STATE->healing_wish_pending[side] = 0u;
    V9_STATE->work_bank = b;
    V9_STATE->work_mode = mode;
    V9_STATE->work_idx = 0u;
    SCRIPTING_BATTLER = b;
    FN_BS_PUSH(CURR_INSTR);
    CURR_INSTR = (mode == 2u) ? BS_V9_LUNAR_DANCE_IN : BS_V9_HEALING_WISH_IN;
}

/* ================== Fila Reutilizavel de Atributos ======================= */

void hook_stat_queue_step_v9(void)
{
    const u8 *p = CURR_INSTR;
    const u8 *down_ptr = (const u8 *)read_u32_unaligned(p);
    const u8 *done_ptr = (const u8 *)read_u32_unaligned(p + 4);

    if (V9_STATE->q_pos >= V9_STATE->q_len) {
        TARGET = V9_STATE->saved_target;
        CURR_INSTR = done_ptr;
        return;
    }

    u8 idx = V9_STATE->q_pos++;
    u8 bank = V9_STATE->q_bank[idx] & 3u;
    u8 sb = V9_STATE->q_stat[idx];
    TARGET = bank;
    STAT_ANIM_PLAYED = 0u;
    STAT_CHANGER_BYTE = sb;
    if ((sb & 0x80u) != 0u)
        CURR_INSTR = down_ptr;
    else
        CURR_INSTR = p + 8;
}

void hook_stat_queue_after_v9(void)
{
    u8 mode = V9_STATE->q_after_mode;
    V9_STATE->q_after_mode = 0u;

    if (mode == 1u) {
        /* No Retreat (673): prende o usuario apos elevar os 5 atributos */
        u8 atk = ATTACKER & 3u;
        sync_battler_v9(atk);
        V9_STATE->no_retreat_mask |= (u8)(1u << atk);
        volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
        if ((*(volatile u32 *)(a + 0x54u) & 0x04000000u) == 0u) {
            *(volatile u32 *)(a + 0x54u) |= 0x04000000u;
            DISABLE_STRUCTS_REAL[28u * atk + 0x14u] = atk;
        }
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_ATK_CANT_ESCAPE;
        return;
    }

    if (mode == 2u) {
        /* Tar Shot (674): aplica vulnerabilidade 2x a Fogo no alvo */
        u8 tgt = TARGET & 3u;
        sync_battler_v9(tgt);
        if ((V9_STATE->tar_shot_mask & (1u << tgt)) == 0u) {
            V9_STATE->tar_shot_mask |= (u8)(1u << tgt);
            CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_TAR_SHOT;
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    if (mode == 3u) {
        /* Toxic Thread (627): tenta envenenar o alvo apos reduzir Velocidade */
        if (CONTROLLER_EXEC_FLAGS != 0u) {
            V9_STATE->q_after_mode = 3u;
            CURR_INSTR = CURR_INSTR - 5;
            return;
        }
        u8 tgt = TARGET & 3u;
        volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
        u8 side = FN_GET_SIDE(tgt);
        u8 misty = (V8_STATE->terrain_type == TERRAIN_MISTY
                    && V8_STATE->terrain_turns > 0u
                    && is_battler_grounded_v9(tgt)) ? 1u : 0u;
        if (!is_behind_substitute(tgt)
            && *(volatile u32 *)(t + 0x50u) == 0u
            && !has_type_v9(tgt, 3u)
            && !has_type_v9(tgt, 8u)
            && *(volatile u16 *)(t + 0x20u) != 17u
            && (SIDE_STATUSES[side] & 0x0020u) == 0u
            && !misty) {
            *(volatile u32 *)(t + 0x50u) = 0x08u;
            ACTIVE_BATTLER = tgt;
            FN_EMIT_SET_MON_DATA(0u, 0x28u, 0u, 4u, (const void *)(t + 0x50u));
            FN_MARK_BUFFER_EXEC(tgt);
            EFFECT_BATTLER = tgt;
            FN_BS_PUSH(BS_MOVE_END);
            CURR_INSTR = BS_POISON_EFF;
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    if (mode == 4u) {
        CURR_INSTR = BS_V9_CANT_ESCAPE_END;
        return;
    }

    if (mode == 5u) {
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_FAIRY_LOCK;
        return;
    }

    CURR_INSTR = BS_MOVE_END;
}

/* ==================== Efeito 243: Final Gambit (514) ===================== */

void hook_final_gambit_calc_v9(void)
{
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    sync_battler_v9(atk);
    sync_battler_v9(tgt);

    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    u8 foresight = ((*(volatile u32 *)(t + 0x54u) & 0x20000000u) != 0u) ? 1u : 0u;

    /* Verifica imunidades ao tipo Lutador (1) e Wonder Guard (25). */
    u8 m1 = lookup_type_eff(1u, t[0x22u], foresight);
    u8 m2 = (t[0x23u] != t[0x22u]) ? lookup_type_eff(1u, t[0x23u], foresight) : 10u;
    u8 et = V9_STATE->extra_type[tgt];
    u8 m3 = (et != 0u && et != t[0x22u] && et != t[0x23u]) ? lookup_type_eff(1u, et, foresight) : 10u;
    if (m1 == 0u || m2 == 0u || m3 == 0u) {
        MOVE_RESULT_FLAGS = 0x09u;
        CURR_INSTR = BS_DOESNT_AFFECT;
        return;
    }
    if (*(volatile u16 *)(t + 0x20u) == 25u) {
        u32 prod = (u32)m1 * (u32)m2 * (u32)m3;
        if (prod <= 1000u) {
            MOVE_RESULT_FLAGS = 0x09u;
            CURR_INSTR = BS_DOESNT_AFFECT;
            return;
        }
    }

    u16 user_hp = *(volatile u16 *)(a + 0x2Au);
    if (user_hp < 1u)
        user_hp = 1u;
    V9_STATE->work_u16 = user_hp;
    CRIT_MULTIPLIER = 1u;
    MOVE_RESULT_FLAGS &= (u8)~0x2Fu;
    BATTLE_MOVE_DMG = (s32)user_hp;
}

void hook_final_gambit_self_ko_v9(void)
{
    u8 atk = ATTACKER & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    u16 cur_hp = *(volatile u16 *)(a + 0x2Au);
    BATTLE_MOVE_DMG = (s32)cur_hp;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
    HIT_MARKER |= 0x00000100u;
}

/* ============= Efeito 244: Tipos, Habilidades e Electrify ================ */

void hook_type_ability_acc_v9(void)
{
    const u8 *p = CURR_INSTR;
    const u8 *acc100_branch = (const u8 *)read_u32_unaligned(p);
    u16 move = CURRENT_MOVE;
    if (move < 822u && move != 595u && MOVE_TABLE[12u * move + 3u] > 0u)
        CURR_INSTR = acc100_branch;
    else
        CURR_INSTR = p + 4;
}

static u8 is_protected_ability_target(u16 ab)
{
    /* Truant (54), Wonder Guard (25), Forecast (59) nao sao sobrescritas no alvo. */
    return (ab == 54u || ab == 25u || ab == 59u) ? 1u : 0u;
}

static u8 is_uncopyable_source_ability(u16 ab)
{
    /* None (0), Wonder Guard (25), Trace (36), Forecast (59). */
    return (ab == 0u || ab == 25u || ab == 36u || ab == 59u) ? 1u : 0u;
}

static u8 has_battler_still_to_act(u8 bank, u32 *pos_out)
{
    u32 cnt = BATTLERS_COUNT;
    if (cnt > 4u)
        cnt = 4u;
    for (u32 i = (u32)CURR_TURN_ACTION_NUM + 1u; i < cnt; ++i) {
        if (BATTLER_BY_TURN[i] == bank) {
            if (ACTIONS_BY_TURN[i] == 0u) {
                if (pos_out != (u32 *)0)
                    *pos_out = i;
                return 1u;
            }
            return 0u;
        }
    }
    return 0u;
}

void hook_type_ability_prep_v9(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    sync_battler_v9(atk);
    sync_battler_v9(tgt);

    if (!is_bank_present_alive(tgt)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }

    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    u16 a_ab = *(volatile u16 *)(a + 0x20u);
    u16 t_ab = *(volatile u16 *)(t + 0x20u);

    if (move == 486u) {
        /* Soak: falha sob Substitute ou se ja for puro Agua (11) */
        if (is_behind_substitute(tgt)
            || (t[0x22u] == 11u && t[0x23u] == 11u && V9_STATE->extra_type[tgt] == 0u)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
        }
        return;
    }
    if (move == 675u) {
        /* Magic Powder: po (bloqueado por Planta 12), Substitute ou ja puro Psiquico (14) */
        if (has_type_v9(tgt, 12u)
            || is_behind_substitute(tgt)
            || (t[0x22u] == 14u && t[0x23u] == 14u && V9_STATE->extra_type[tgt] == 0u)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
        }
        return;
    }
    if (move == 512u) {
        /* Reflect Type: ignora Substitute; copia tipos do alvo */
        return;
    }
    if (move == 563u) {
        /* Trick-or-Treat: adiciona Ghost (7) */
        if (is_behind_substitute(tgt) || has_type_v9(tgt, 7u))
            CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    if (move == 567u) {
        /* Forest's Curse: adiciona Grass (12) */
        if (is_behind_substitute(tgt) || has_type_v9(tgt, 12u))
            CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    if (move == 380u) {
        /* Gastro Acid */
        if (is_behind_substitute(tgt)
            || t_ab == 0u
            || (V9_STATE->gastro_acid_mask & (1u << tgt)) != 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
        }
        return;
    }
    if (move == 388u) {
        /* Worry Seed: muda habilidade para Insomnia (15) */
        if (is_behind_substitute(tgt) || t_ab == 15u || is_protected_ability_target(t_ab))
            CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    if (move == 493u) {
        /* Entrainment */
        if (is_behind_substitute(tgt)
            || is_uncopyable_source_ability(a_ab)
            || is_protected_ability_target(t_ab)
            || a_ab == t_ab) {
            CURR_INSTR = BS_BUT_IT_FAILED;
        }
        return;
    }
    if (move == 759u) {
        /* Doodle: copia habilidade do alvo para usuario (e parceiro em duplas) */
        if (is_uncopyable_source_ability(t_ab) || t_ab == 54u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        u8 changed_any = (a_ab != t_ab && !is_protected_ability_target(a_ab)) ? 1u : 0u;
        if ((BATTLE_TYPE_FLAGS & 0x01u) != 0u) {
            u8 ally = (u8)((atk ^ 2u) & 3u);
            if (is_bank_present_alive(ally)) {
                u16 al_ab = *(volatile u16 *)(BATTLE_MONS + 0x5Cu * ally + 0x20u);
                if (al_ab != t_ab && !is_protected_ability_target(al_ab))
                    changed_any = 1u;
            }
        }
        if (!changed_any)
            CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    if (move == 578u) {
        /* Electrify: falha se o alvo ja agiu neste turno */
        if (!has_battler_still_to_act(tgt, (u32 *)0)
            || (V9_STATE->electrified_mask & (1u << tgt)) != 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
        }
        return;
    }
    CURR_INSTR = BS_BUT_IT_FAILED;
}

void hook_type_ability_apply_v9(void)
{
    if (CONTROLLER_EXEC_FLAGS != 0u)
        return;

    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;

    if (move == 486u) {
        t[0x22u] = 11u;
        t[0x23u] = 11u;
        V9_STATE->extra_type[tgt] = 0u;
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_SOAK;
        return;
    }
    if (move == 675u) {
        t[0x22u] = 14u;
        t[0x23u] = 14u;
        V9_STATE->extra_type[tgt] = 0u;
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_MAGIC_POWDER;
        return;
    }
    if (move == 512u) {
        a[0x22u] = t[0x22u];
        a[0x23u] = t[0x23u];
        V9_STATE->extra_type[atk] = V9_STATE->extra_type[tgt];
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_REFLECT_TYPE;
        return;
    }
    if (move == 563u) {
        V9_STATE->extra_type[tgt] = 7u;
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_TRICK_OR_TREAT;
        return;
    }
    if (move == 567u) {
        V9_STATE->extra_type[tgt] = 12u;
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_FORESTS_CURSE;
        return;
    }
    if (move == 380u) {
        *(volatile u16 *)(t + 0x20u) = 0u;
        V9_STATE->gastro_acid_mask |= (u8)(1u << tgt);
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_GASTRO_ACID;
        return;
    }
    if (move == 388u) {
        *(volatile u16 *)(t + 0x20u) = 15u;
        if ((*(volatile u32 *)(t + 0x50u) & 0x07u) != 0u) {
            *(volatile u32 *)(t + 0x50u) = 0u;
            *(volatile u32 *)(t + 0x54u) &= ~0x08000000u;
            ACTIVE_BATTLER = tgt;
            FN_EMIT_SET_MON_DATA(0u, 0x28u, 0u, 4u, (const void *)(t + 0x50u));
            FN_MARK_BUFFER_EXEC(tgt);
            CURR_INSTR = BS_V9_WORRY_SEED_WOKE;
            return;
        }
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_WORRY_SEED;
        return;
    }
    if (move == 493u) {
        *(volatile u16 *)(t + 0x20u) = *(volatile u16 *)(a + 0x20u);
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_ENTRAINMENT;
        return;
    }
    if (move == 759u) {
        u16 copied = *(volatile u16 *)(t + 0x20u);
        if (!is_protected_ability_target(*(volatile u16 *)(a + 0x20u)))
            *(volatile u16 *)(a + 0x20u) = copied;
        if ((BATTLE_TYPE_FLAGS & 0x01u) != 0u) {
            u8 ally = (u8)((atk ^ 2u) & 3u);
            if (is_bank_present_alive(ally)) {
                volatile u8 *al = BATTLE_MONS + 0x5Cu * ally;
                if (!is_protected_ability_target(*(volatile u16 *)(al + 0x20u)))
                    *(volatile u16 *)(al + 0x20u) = copied;
            }
        }
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_DOODLE;
        return;
    }
    if (move == 578u) {
        V9_STATE->electrified_mask |= (u8)(1u << tgt);
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_ELECTRIFY;
        return;
    }
    CURR_INSTR = BS_MOVE_END;
}

/* ======== Efeito 245: Trocas, Divisoes e Inversao de Atributos =========== */

void hook_raw_swap_apply_v9(void)
{
    const u8 *p = CURR_INSTR;
    u8 phase = p[0];
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    sync_battler_v9(atk);
    sync_battler_v9(tgt);

    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;

    if (move == 379u) {
        if (phase == 0u) {
            CURR_INSTR = p + 1;
            return;
        }
        /* Power Trick: permuta Attack (+0x02) e Defense (+0x04) do usuario */
        u16 tmp = *(volatile u16 *)(a + 0x02u);
        *(volatile u16 *)(a + 0x02u) = *(volatile u16 *)(a + 0x04u);
        *(volatile u16 *)(a + 0x04u) = tmp;
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_POWER_TRICK;
        return;
    }

    if (!is_bank_present_alive(tgt)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }

    if (move == 572u) {
        /* Topsy-Turvy: inverte estagios nao neutros do alvo */
        if (is_behind_substitute(tgt)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        u8 any_non_neutral = 0u;
        for (u8 i = 1u; i <= 7u; ++i) {
            if (t[0x18u + i] != 6u)
                any_non_neutral = 1u;
        }
        if (!any_non_neutral) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        if (phase == 0u) {
            CURR_INSTR = p + 1;
            return;
        }
        for (u8 i = 1u; i <= 7u; ++i) {
            if (t[0x18u + i] != 6u)
                t[0x18u + i] = (u8)(12u - t[0x18u + i]);
        }
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_TOPSY_TURVY;
        return;
    }

    if (phase == 0u) {
        CURR_INSTR = p + 1;
        return;
    }

    if (move == 638u) {
        /* Speed Swap */
        u16 tmp = *(volatile u16 *)(a + 0x06u);
        *(volatile u16 *)(a + 0x06u) = *(volatile u16 *)(t + 0x06u);
        *(volatile u16 *)(t + 0x06u) = tmp;
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_SPEED_SWAP;
        return;
    }
    if (move == 470u) {
        /* Power Split: media de Attack (+0x02) e Sp. Atk (+0x08) */
        u16 avg_atk = (u16)(((u32)(*(volatile u16 *)(a + 0x02u)) + (u32)(*(volatile u16 *)(t + 0x02u))) >> 1);
        u16 avg_spa = (u16)(((u32)(*(volatile u16 *)(a + 0x08u)) + (u32)(*(volatile u16 *)(t + 0x08u))) >> 1);
        if (avg_atk < 1u) avg_atk = 1u;
        if (avg_spa < 1u) avg_spa = 1u;
        *(volatile u16 *)(a + 0x02u) = avg_atk;
        *(volatile u16 *)(t + 0x02u) = avg_atk;
        *(volatile u16 *)(a + 0x08u) = avg_spa;
        *(volatile u16 *)(t + 0x08u) = avg_spa;
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_POWER_SPLIT;
        return;
    }
    if (move == 469u) {
        /* Guard Split: media de Defense (+0x04) e Sp. Def (+0x0A) */
        u16 avg_def = (u16)(((u32)(*(volatile u16 *)(a + 0x04u)) + (u32)(*(volatile u16 *)(t + 0x04u))) >> 1);
        u16 avg_spd = (u16)(((u32)(*(volatile u16 *)(a + 0x0Au)) + (u32)(*(volatile u16 *)(t + 0x0Au))) >> 1);
        if (avg_def < 1u) avg_def = 1u;
        if (avg_spd < 1u) avg_spd = 1u;
        *(volatile u16 *)(a + 0x04u) = avg_def;
        *(volatile u16 *)(t + 0x04u) = avg_def;
        *(volatile u16 *)(a + 0x0Au) = avg_spd;
        *(volatile u16 *)(t + 0x0Au) = avg_spd;
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_GUARD_SPLIT;
        return;
    }
    if (move == 384u) {
        /* Power Swap: permuta estagios de Atk (1) e Sp. Atk (4) */
        u8 s1 = a[0x19u]; a[0x19u] = t[0x19u]; t[0x19u] = s1;
        u8 s4 = a[0x1Cu]; a[0x1Cu] = t[0x1Cu]; t[0x1Cu] = s4;
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_POWER_SWAP;
        return;
    }
    if (move == 385u) {
        /* Guard Swap: permuta estagios de Def (2) e Sp. Def (5) */
        u8 s2 = a[0x1Au]; a[0x1Au] = t[0x1Au]; t[0x1Au] = s2;
        u8 s5 = a[0x1Du]; a[0x1Du] = t[0x1Du]; t[0x1Du] = s5;
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_GUARD_SWAP;
        return;
    }
    if (move == 391u) {
        /* Heart Swap: permuta todos os 7 estagios (Atk..Eva) */
        for (u8 i = 1u; i <= 7u; ++i) {
            u8 tmp = a[0x18u + i];
            a[0x18u + i] = t[0x18u + i];
            t[0x18u + i] = tmp;
        }
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_HEART_SWAP;
        return;
    }
    CURR_INSTR = BS_BUT_IT_FAILED;
}

/* =========== Efeito 246: Buffs/Debuffs Direcionados e Octolock =========== */

void hook_target_buff_prep_v9(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    sync_battler_v9(atk);
    sync_battler_v9(tgt);

    if (move == 367u) {
        /* Acupressure: +2 aleatorio em atributo < 12 do alvo (usuario/aliado) */
        u8 bank = is_bank_present_alive(tgt) ? tgt : atk;
        if (bank != atk && is_behind_substitute(bank)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        volatile u8 *m = BATTLE_MONS + 0x5Cu * bank;
        u8 cand[7];
        u32 n = 0u;
        for (u8 s = 1u; s <= 7u; ++s) {
            if (m[0x18u + s] < 12u)
                cand[n++] = s;
        }
        if (n == 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        u8 chosen = cand[FN_UMOD32(FN_RANDOM(), n)];
        queue_reset(0u);
        queue_push(bank, chosen, 2u, 0u);
        return;
    }

    if (move == 595u) {
        /* Venom Drench: afeta oponentes envenenados (-1 Atk, -1 SpAtk, -1 Speed) */
        queue_reset(0u);
        u8 atk_side = FN_GET_SIDE(atk);
        u32 cnt = BATTLERS_COUNT;
        if (cnt > 4u)
            cnt = 4u;
        for (u8 b = 0u; b < cnt; ++b) {
            if (FN_GET_SIDE(b) == atk_side || !is_bank_present_alive(b) || is_behind_substitute(b))
                continue;
            if ((PROTECT_STRUCTS[16u * b] & 0x01u) != 0u)
                continue;
            volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
            if ((*(volatile u32 *)(m + 0x50u) & 0x88u) == 0u)
                continue;
            if (m[0x19u] > 0u || m[0x1Cu] > 0u || m[0x1Bu] > 0u) {
                if (m[0x19u] > 0u) queue_push(b, 1u, 1u, 1u);
                if (m[0x1Cu] > 0u) queue_push(b, 4u, 1u, 1u);
                if (m[0x1Bu] > 0u) queue_push(b, 3u, 1u, 1u);
            }
        }
        if (V9_STATE->q_len == 0u)
            CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }

    if (!is_bank_present_alive(tgt)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }

    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;

    if (move == 684u) {
        /* Decorate: +2 Atk, +2 Sp. Atk no alvo (ignora Substitute) */
        if (t[0x19u] >= 12u && t[0x1Cu] >= 12u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        queue_reset(0u);
        queue_push(tgt, 1u, 2u, 0u);
        queue_push(tgt, 4u, 2u, 0u);
        return;
    }

    if (is_behind_substitute(tgt)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }

    if (move == 750u) {
        /* Spicy Extract: +2 Atk e -2 Def no alvo */
        if (t[0x19u] >= 12u && t[0x1Au] == 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        queue_reset(0u);
        if (t[0x19u] < 12u) queue_push(tgt, 1u, 2u, 0u);
        if (t[0x1Au] > 0u)  queue_push(tgt, 2u, 2u, 1u);
        return;
    }

    if (move == 627u) {
        /* Toxic Thread: -1 Speed + envenena */
        u8 side = FN_GET_SIDE(tgt);
        u8 misty = (V8_STATE->terrain_type == TERRAIN_MISTY
                    && V8_STATE->terrain_turns > 0u
                    && is_battler_grounded_v9(tgt)) ? 1u : 0u;
        u8 can_psn = (*(volatile u32 *)(t + 0x50u) == 0u
                      && !has_type_v9(tgt, 3u)
                      && !has_type_v9(tgt, 8u)
                      && *(volatile u16 *)(t + 0x20u) != 17u
                      && (SIDE_STATUSES[side] & 0x0020u) == 0u
                      && !misty) ? 1u : 0u;
        if (t[0x1Bu] == 0u && !can_psn) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        queue_reset(3u);
        if (t[0x1Bu] > 0u)
            queue_push(tgt, 3u, 1u, 1u);
        return;
    }

    if (move == 674u) {
        /* Tar Shot: -1 Speed + marca 2x Fogo */
        u8 already = ((V9_STATE->tar_shot_mask & (1u << tgt)) != 0u) ? 1u : 0u;
        if (already && t[0x1Bu] == 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        queue_reset(2u);
        if (t[0x1Bu] > 0u)
            queue_push(tgt, 3u, 1u, 1u);
        return;
    }

    if (move == 678u) {
        /* Octolock: prende alvo nao-Fantasma e reduz Def/SpDef ao fim do turno */
        if (has_type_v9(tgt, 7u) || V9_STATE->octolock_active[tgt] != 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        V9_STATE->octolock_active[tgt] = 1u;
        V9_STATE->octolock_trapper[tgt] = atk;
        V9_STATE->octolock_src_tag[tgt] = mon_tag(atk);
        if ((*(volatile u32 *)(t + 0x54u) & 0x04000000u) == 0u) {
            *(volatile u32 *)(t + 0x54u) |= 0x04000000u;
            DISABLE_STRUCTS_REAL[28u * tgt + 0x14u] = atk;
        }
        queue_reset(4u);
        return;
    }

    CURR_INSTR = BS_BUT_IT_FAILED;
}

/* ============= Efeito 247: Sinergias de Campo / Equipe (v9) ============== */

void hook_field_team_prep_v9(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    sync_battler_v9(atk);

    u32 cnt = BATTLERS_COUNT;
    if (cnt > 4u)
        cnt = 4u;

    if (move == 583u) {
        /* Fairy Lock: bloqueia fuga/troca no turno seguinte */
        if (V9_STATE->fairy_lock_turns > 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        V9_STATE->fairy_lock_turns = 2u;
        V9_STATE->fairy_lock_mask = 0u;
        for (u8 b = 0u; b < cnt; ++b) {
            sync_battler_v9(b);
            if (!is_bank_present_alive(b) || has_type_v9(b, 7u))
                continue;
            volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
            if ((*(volatile u32 *)(m + 0x54u) & 0x04000000u) == 0u) {
                *(volatile u32 *)(m + 0x54u) |= 0x04000000u;
                DISABLE_STRUCTS_REAL[28u * b + 0x14u] = b;
                V9_STATE->fairy_lock_mask |= (u8)(1u << b);
            }
        }
        queue_reset(5u);
        return;
    }

    queue_reset(0u);

    if (move == 559u) {
        /* Rototiller: +1 Atk, +1 SpAtk em Planta (12) aterrados */
        for (u8 b = 0u; b < cnt; ++b) {
            if (!is_bank_present_alive(b) || (STATUSES3[b] & 0x000400F8u) != 0u)
                continue;
            if (has_type_v9(b, 12u) && is_battler_grounded_v9(b)) {
                volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
                if (m[0x19u] < 12u) queue_push(b, 1u, 1u, 0u);
                if (m[0x1Cu] < 12u) queue_push(b, 4u, 1u, 0u);
            }
        }
    } else if (move == 575u) {
        /* Flower Shield: +1 Def em todos os Planta (12) em campo */
        for (u8 b = 0u; b < cnt; ++b) {
            if (!is_bank_present_alive(b) || (STATUSES3[b] & 0x000400F8u) != 0u)
                continue;
            if (has_type_v9(b, 12u)) {
                volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
                if (m[0x1Au] < 12u) queue_push(b, 2u, 1u, 0u);
            }
        }
    } else if (move == 598u || move == 629u) {
        /* Magnetic Flux (Def/SpDef +1) e Gear Up (Atk/SpAtk +1) para Plus(57)/Minus(58) */
        u8 atk_side = FN_GET_SIDE(atk);
        for (u8 b = 0u; b < cnt; ++b) {
            if (FN_GET_SIDE(b) != atk_side || !is_bank_present_alive(b))
                continue;
            volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
            u16 ab = *(volatile u16 *)(m + 0x20u);
            if (ab != 57u && ab != 58u)
                continue;
            if (move == 598u) {
                if (m[0x1Au] < 12u) queue_push(b, 2u, 1u, 0u);
                if (m[0x1Du] < 12u) queue_push(b, 5u, 1u, 0u);
            } else {
                if (m[0x19u] < 12u) queue_push(b, 1u, 1u, 0u);
                if (m[0x1Cu] < 12u) queue_push(b, 4u, 1u, 0u);
            }
        }
    }

    if (V9_STATE->q_len == 0u)
        CURR_INSTR = BS_BUT_IT_FAILED;
}

/* ======== Efeito 248: Fillet Away / Clangorous Soul / No Retreat ========= */

void hook_sacrifice_prep_v9(void)
{
    const u8 *p = CURR_INSTR;
    const u8 *skip_hp_ptr = (const u8 *)read_u32_unaligned(p);
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    sync_battler_v9(atk);

    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    u16 cur_hp = *(volatile u16 *)(a + 0x2Au);
    u16 max_hp = *(volatile u16 *)(a + 0x2Eu);

    if (move == 760u) {
        /* Fillet Away: consome maxHP/2 e sobe Atk/SpAtk/Speed +2 */
        u16 cost = max_hp >> 1;
        if (cost < 1u)
            cost = 1u;
        if (cur_hp <= cost || (a[0x19u] >= 12u && a[0x1Cu] >= 12u && a[0x1Bu] >= 12u)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        queue_reset(0u);
        queue_push(atk, 1u, 2u, 0u);
        queue_push(atk, 4u, 2u, 0u);
        queue_push(atk, 3u, 2u, 0u);
        BATTLE_MOVE_DMG = (s32)cost;
        MOVE_RESULT_FLAGS &= (u8)~0x29u;
        CURR_INSTR = p + 4;
        return;
    }

    if (move == 682u) {
        /* Clangorous Soul: consome maxHP/3 e sobe Atk..Speed +1 */
        u16 cost = (u16)FN_UDIV32(max_hp, 3u);
        if (cost < 1u)
            cost = 1u;
        u8 any_room = 0u;
        for (u8 s = 1u; s <= 5u; ++s) {
            if (a[0x18u + s] < 12u)
                any_room = 1u;
        }
        if (cur_hp <= cost || !any_room) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        queue_reset(0u);
        for (u8 s = 1u; s <= 5u; ++s)
            queue_push(atk, s, 1u, 0u);
        BATTLE_MOVE_DMG = (s32)cost;
        MOVE_RESULT_FLAGS &= (u8)~0x29u;
        CURR_INSTR = p + 4;
        return;
    }

    if (move == 673u) {
        /* No Retreat: falha se ja ativado por este Pokemon */
        if ((V9_STATE->no_retreat_mask & (1u << atk)) != 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        queue_reset(1u);
        for (u8 s = 1u; s <= 5u; ++s)
            queue_push(atk, s, 1u, 0u);
        CURR_INSTR = skip_hp_ptr;
        return;
    }

    CURR_INSTR = BS_BUT_IT_FAILED;
}

/* ============= Efeito 249: Aqua Ring (392) / Laser Focus (628) =========== */

void hook_self_volatile_apply_v9(void)
{
    const u8 *p = CURR_INSTR;
    u8 phase = p[0];
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    sync_battler_v9(atk);

    if (move == 392u) {
        if (phase == 0u) {
            if ((V9_STATE->aqua_ring_mask & (1u << atk)) != 0u) {
                CURR_INSTR = BS_BUT_IT_FAILED;
                return;
            }
            CURR_INSTR = p + 1;
            return;
        }
        V9_STATE->aqua_ring_mask |= (u8)(1u << atk);
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_AQUA_RING_SET;
        return;
    }

    if (move == 628u) {
        if (phase == 0u) {
            CURR_INSTR = p + 1;
            return;
        }
        V9_STATE->laser_focus_turns[atk] = 2u;
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_LASER_FOCUS;
        return;
    }

    CURR_INSTR = BS_BUT_IT_FAILED;
}

/* =================== Efeito 250: Strength Sap (623) ====================== */

void hook_strength_sap_prep_v9(void)
{
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    sync_battler_v9(atk);
    sync_battler_v9(tgt);

    if (!is_bank_present_alive(tgt) || is_behind_substitute(tgt)) {
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
    if (eff_atk > 0xFFFFu)
        eff_atk = 0xFFFFu;
    V9_STATE->work_u16 = (u16)eff_atk;
    V9_STATE->work_idx = stage;
}

void hook_strength_sap_heal_v9(void)
{
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;

    /* Se o Ataque nao diminuiu (ex.: Clear Body / Hyper Cutter / Mist), nao cura. */
    if (t[0x19u] >= V9_STATE->work_idx) {
        CURR_INSTR = BS_MOVE_END;
        return;
    }
    if (is_heal_blocked(atk)) {
        CURR_INSTR = BS_HEAL_BLOCK_CANCEL;
        return;
    }

    s32 amt = (s32)V9_STATE->work_u16;
    if (*(volatile u16 *)(t + 0x20u) == 64u) {
        /* Liquid Ooze (64): causa dano em vez de curar */
        BATTLE_MOVE_DMG = amt;
        MOVE_RESULT_FLAGS &= (u8)~0x29u;
        CURR_INSTR = BS_V9_LIQUID_OOZE_TAIL;
        return;
    }

    u16 cur_hp = *(volatile u16 *)(a + 0x2Au);
    u16 max_hp = *(volatile u16 *)(a + 0x2Eu);
    if (cur_hp >= max_hp) {
        CURR_INSTR = BS_MOVE_END;
        return;
    }
    BATTLE_MOVE_DMG = -amt;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
}

/* ====== Efeito 251: Clerigo (Psycho Shift / Purify / Take Heart / etc.) == */

static u8 can_receive_psycho_shift(u8 tgt, u32 atk_st1)
{
    if (!is_bank_present_alive(tgt) || is_behind_substitute(tgt))
        return 0u;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
    if (*(volatile u32 *)(t + 0x50u) != 0u)
        return 0u;
    u8 side = FN_GET_SIDE(tgt);
    if ((SIDE_STATUSES[side] & 0x0020u) != 0u)
        return 0u;
    u8 grounded = is_battler_grounded_v9(tgt);
    if (grounded && V8_STATE->terrain_turns > 0u && V8_STATE->terrain_type == TERRAIN_MISTY)
        return 0u;

    u16 ab = *(volatile u16 *)(t + 0x20u);
    if ((atk_st1 & 0x07u) != 0u) {
        if (ab == 15u || ab == 72u)
            return 0u;
        if (grounded && V8_STATE->terrain_turns > 0u && V8_STATE->terrain_type == TERRAIN_ELECTRIC)
            return 0u;
        return 1u;
    }
    if ((atk_st1 & 0x88u) != 0u) {
        if (has_type_v9(tgt, 3u) || has_type_v9(tgt, 8u) || ab == 17u)
            return 0u;
        return 1u;
    }
    if ((atk_st1 & 0x10u) != 0u) {
        if (has_type_v9(tgt, 10u) || ab == 41u)
            return 0u;
        return 1u;
    }
    if ((atk_st1 & 0x40u) != 0u) {
        if (has_type_v9(tgt, 13u) || ab == 7u)
            return 0u;
        return 1u;
    }
    return 0u;
}

void hook_cleric_prep_v9(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    sync_battler_v9(atk);
    sync_battler_v9(tgt);

    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    u32 a_st = *(volatile u32 *)(a + 0x50u);

    if (move == 375u) {
        /* Psycho Shift */
        if (a_st == 0u || !can_receive_psycho_shift(tgt, a_st)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        V9_STATE->work_idx = 0u;
        return;
    }

    if (move == 640u) {
        /* Purify: exige que o alvo tenha status1 != 0 e nao esteja sob Substitute */
        if (!is_bank_present_alive(tgt) || is_behind_substitute(tgt)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;
        if (*(volatile u32 *)(t + 0x50u) == 0u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        V9_STATE->work_idx = 0u;
        return;
    }

    if (move == 743u) {
        /* Take Heart: cura status1 do usuario + SpAtk/SpDef +1 */
        if (a_st == 0u && a[0x1Cu] >= 12u && a[0x1Du] >= 12u) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        V9_STATE->work_idx = 0u;
        return;
    }

    if (move == 710u || move == 742u) {
        /* Jungle Healing / Lunar Blessing: cura 1/4 HP + status1 em usuario e aliado */
        u8 any_ok = 0u;
        u8 banks[2];
        u32 nb = 1u;
        banks[0] = atk;
        if ((BATTLE_TYPE_FLAGS & 0x01u) != 0u && is_bank_present_alive((u8)(atk ^ 2u))) {
            banks[1] = (u8)((atk ^ 2u) & 3u);
            nb = 2u;
        }
        for (u32 i = 0u; i < nb; ++i) {
            u8 b = banks[i];
            volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
            u16 hp = *(volatile u16 *)(m + 0x2Au);
            u16 max_hp = *(volatile u16 *)(m + 0x2Eu);
            if (*(volatile u32 *)(m + 0x50u) != 0u || (hp < max_hp && !is_heal_blocked(b)))
                any_ok = 1u;
        }
        if (!any_ok) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        V9_STATE->work_idx = 0u;
        return;
    }

    CURR_INSTR = BS_BUT_IT_FAILED;
}

void hook_cleric_step_v9(void)
{
    if (CONTROLLER_EXEC_FLAGS != 0u)
        return;

    const u8 *p = CURR_INSTR;
    const u8 *cure_ui_branch = (const u8 *)read_u32_unaligned(p);
    const u8 *heal_hp_branch = (const u8 *)read_u32_unaligned(p + 4);

    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    volatile u8 *t = BATTLE_MONS + 0x5Cu * tgt;

    if (move == 375u) {
        /* Psycho Shift: passo 0 aplica status no alvo; passo 1 limpa status do usuario */
        if (V9_STATE->work_idx == 0u) {
            V9_STATE->work_idx = 1u;
            u32 a_st = *(volatile u32 *)(a + 0x50u);
            u32 new_st = 0u;
            const u8 *eff_bs = BS_POISON_EFF;
            if ((a_st & 0x07u) != 0u) {
                new_st = 2u + (FN_RANDOM() & 1u);
                eff_bs = BS_V9_SLEEP_EFF;
            } else if ((a_st & 0x80u) != 0u) {
                new_st = 0x80u;
                eff_bs = BS_TOXIC_EFF;
            } else if ((a_st & 0x08u) != 0u) {
                new_st = 0x08u;
                eff_bs = BS_POISON_EFF;
            } else if ((a_st & 0x10u) != 0u) {
                new_st = 0x10u;
                eff_bs = BS_BURN_EFF;
            } else if ((a_st & 0x40u) != 0u) {
                new_st = 0x40u;
                eff_bs = BS_PARALYSIS_EFF;
            }
            *(volatile u32 *)(t + 0x50u) = new_st;
            ACTIVE_BATTLER = tgt;
            FN_EMIT_SET_MON_DATA(0u, 0x28u, 0u, 4u, (const void *)(t + 0x50u));
            FN_MARK_BUFFER_EXEC(tgt);
            EFFECT_BATTLER = tgt;
            /* Reexecuta este callasm apos o sub-script de status terminar */
            FN_BS_PUSH(p - 5);
            CURR_INSTR = eff_bs;
            return;
        }
        if (V9_STATE->work_idx == 1u) {
            V9_STATE->work_idx = 2u;
            *(volatile u32 *)(a + 0x50u) = 0u;
            *(volatile u32 *)(a + 0x54u) &= ~0x08000000u;
            ACTIVE_BATTLER = atk;
            FN_EMIT_SET_MON_DATA(0u, 0x28u, 0u, 4u, (const void *)(a + 0x50u));
            FN_MARK_BUFFER_EXEC(atk);
            EFFECT_BATTLER = atk;
            SCRIPTING_BATTLER = atk;
            CURR_INSTR = cure_ui_branch;
            return;
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    if (move == 640u) {
        /* Purify: passo 0 cura alvo; passo 1 cura 50% do HP do usuario */
        if (V9_STATE->work_idx == 0u) {
            V9_STATE->work_idx = 1u;
            *(volatile u32 *)(t + 0x50u) = 0u;
            *(volatile u32 *)(t + 0x54u) &= ~0x08000000u;
            ACTIVE_BATTLER = tgt;
            FN_EMIT_SET_MON_DATA(0u, 0x28u, 0u, 4u, (const void *)(t + 0x50u));
            FN_MARK_BUFFER_EXEC(tgt);
            EFFECT_BATTLER = tgt;
            SCRIPTING_BATTLER = tgt;
            CURR_INSTR = cure_ui_branch;
            return;
        }
        if (V9_STATE->work_idx == 1u) {
            V9_STATE->work_idx = 2u;
            u16 hp = *(volatile u16 *)(a + 0x2Au);
            u16 max_hp = *(volatile u16 *)(a + 0x2Eu);
            if (!is_heal_blocked(atk) && hp > 0u && hp < max_hp) {
                s32 heal = (s32)((max_hp + 1u) >> 1);
                if (heal < 1)
                    heal = 1;
                SCRIPTING_BATTLER = atk;
                BATTLE_MOVE_DMG = -heal;
                MOVE_RESULT_FLAGS &= (u8)~0x29u;
                CURR_INSTR = heal_hp_branch;
                return;
            }
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    if (move == 743u) {
        /* Take Heart: passo 0 cura status1 se houver; passo 1 enfileira SpAtk/SpDef +1 */
        if (V9_STATE->work_idx == 0u) {
            V9_STATE->work_idx = 1u;
            if (*(volatile u32 *)(a + 0x50u) != 0u) {
                *(volatile u32 *)(a + 0x50u) = 0u;
                *(volatile u32 *)(a + 0x54u) &= ~0x08000000u;
                ACTIVE_BATTLER = atk;
                FN_EMIT_SET_MON_DATA(0u, 0x28u, 0u, 4u, (const void *)(a + 0x50u));
                FN_MARK_BUFFER_EXEC(atk);
                EFFECT_BATTLER = atk;
                SCRIPTING_BATTLER = atk;
                CURR_INSTR = cure_ui_branch;
                return;
            }
        }
        if (V9_STATE->work_idx == 1u) {
            V9_STATE->work_idx = 2u;
            queue_reset(0u);
            if (a[0x1Cu] < 12u) queue_push(atk, 4u, 1u, 0u);
            if (a[0x1Du] < 12u) queue_push(atk, 5u, 1u, 0u);
            if (V9_STATE->q_len > 0u) {
                CURR_INSTR = BS_V9_STAT_QUEUE;
                return;
            }
        }
        CURR_INSTR = BS_MOVE_END;
        return;
    }

    /* Jungle Healing (710) / Lunar Blessing (742): passos 0..3 (atk HP, atk ST, ally HP, ally ST) */
    while (V9_STATE->work_idx < 4u) {
        u8 step = V9_STATE->work_idx++;
        u8 b = (step < 2u) ? atk : (u8)((atk ^ 2u) & 3u);
        if (step >= 2u && (BATTLE_TYPE_FLAGS & 0x01u) == 0u)
            break;
        if (!is_bank_present_alive(b))
            continue;
        volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
        if ((step & 1u) == 0u) {
            u16 hp = *(volatile u16 *)(m + 0x2Au);
            u16 max_hp = *(volatile u16 *)(m + 0x2Eu);
            if (!is_heal_blocked(b) && hp < max_hp) {
                s32 heal = (s32)(max_hp >> 2);
                if (heal < 1)
                    heal = 1;
                SCRIPTING_BATTLER = b;
                BATTLE_MOVE_DMG = -heal;
                MOVE_RESULT_FLAGS &= (u8)~0x29u;
                CURR_INSTR = heal_hp_branch;
                return;
            }
        } else {
            if (*(volatile u32 *)(m + 0x50u) != 0u) {
                *(volatile u32 *)(m + 0x50u) = 0u;
                *(volatile u32 *)(m + 0x54u) &= ~0x08000000u;
                ACTIVE_BATTLER = b;
                FN_EMIT_SET_MON_DATA(0u, 0x28u, 0u, 4u, (const void *)(m + 0x50u));
                FN_MARK_BUFFER_EXEC(b);
                EFFECT_BATTLER = b;
                SCRIPTING_BATTLER = b;
                CURR_INSTR = cure_ui_branch;
                return;
            }
        }
    }
    CURR_INSTR = BS_MOVE_END;
}

/* ==================== Efeito 252: Dark Void (463) ======================== */

void hook_dark_void_step_v9(void)
{
    if (CONTROLLER_EXEC_FLAGS != 0u)
        return;

    const u8 *p = CURR_INSTR;
    const u8 *anim_branch = (const u8 *)read_u32_unaligned(p);
    u8 atk = ATTACKER & 3u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;

    /* Apenas Darkrai (species == 491) pode executar Dark Void (Gen 7-9). */
    if (*(volatile u16 *)(a + 0x00u) != 491u) {
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_DARK_VOID_BLOCK;
        return;
    }

    if (V9_STATE->work_idx == 0u && V9_STATE->work_mode == 0u) {
        V9_STATE->saved_target = TARGET;
    }

    if (V9_STATE->work_mode == 2u) {
        V9_STATE->work_mode = 1u;
        u8 b = V9_STATE->work_bank & 3u;
        volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
        *(volatile u32 *)(m + 0x50u) = 2u + (FN_RANDOM() & 1u);
        ACTIVE_BATTLER = b;
        FN_EMIT_SET_MON_DATA(0u, 0x28u, 0u, 4u, (const void *)(m + 0x50u));
        FN_MARK_BUFFER_EXEC(b);
        EFFECT_BATTLER = b;
        FN_BS_PUSH(p - 5);
        CURR_INSTR = BS_V9_SLEEP_EFF;
        return;
    }

    u8 atk_side = FN_GET_SIDE(atk);
    u32 cnt = BATTLERS_COUNT;
    if (cnt > 4u)
        cnt = 4u;

    while (V9_STATE->work_idx < cnt) {
        u8 b = V9_STATE->work_idx++;
        if (FN_GET_SIDE(b) == atk_side || !is_bank_present_alive(b))
            continue;
        if ((PROTECT_STRUCTS[16u * b] & 0x01u) != 0u || is_behind_substitute(b))
            continue;
        volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
        if (*(volatile u32 *)(m + 0x50u) != 0u)
            continue;
        u8 b_side = FN_GET_SIDE(b);
        if ((SIDE_STATUSES[b_side] & 0x0020u) != 0u)
            continue;
        u16 ab = *(volatile u16 *)(m + 0x20u);
        if (ab == 15u || ab == 72u)
            continue;
        if (is_battler_grounded_v9(b)
            && V8_STATE->terrain_turns > 0u
            && (V8_STATE->terrain_type == TERRAIN_ELECTRIC || V8_STATE->terrain_type == TERRAIN_MISTY)) {
            continue;
        }

        /* Checagem de precisao (50% base, 5/3x em Gravity, estagios Acc/Eva) */
        u32 calc = 50u;
        s32 buff = (s32)a[0x1Eu] + 6 - (s32)m[0x1Fu];
        if (buff < 0) buff = 0;
        else if (buff > 12) buff = 12;
        const u8 *acc_tbl = (const u8 *)0x08209BD0u;
        calc = FN_UDIV32(calc * acc_tbl[2u * (u32)buff], acc_tbl[2u * (u32)buff + 1u]);
        if (*(volatile u16 *)(a + 0x20u) == 14u)
            calc = FN_UDIV32(calc * 130u, 100u);
        if (V8_STATE->gravity_turns > 0u)
            calc = FN_UDIV32(calc * 5u, 3u);
        if ((FN_UMOD32(FN_RANDOM(), 100u) + 1u) > calc)
            continue;

        TARGET = b;
        V9_STATE->work_bank = b;
        if (V9_STATE->work_mode == 0u) {
            V9_STATE->work_mode = 2u;
            CURR_INSTR = anim_branch;
            return;
        }
        /* Segundo alvo em duplas: aplica sono direto */
        *(volatile u32 *)(m + 0x50u) = 2u + (FN_RANDOM() & 1u);
        ACTIVE_BATTLER = b;
        FN_EMIT_SET_MON_DATA(0u, 0x28u, 0u, 4u, (const void *)(m + 0x50u));
        FN_MARK_BUFFER_EXEC(b);
        EFFECT_BATTLER = b;
        FN_BS_PUSH(p - 5);
        CURR_INSTR = BS_V9_SLEEP_EFF;
        return;
    }

    TARGET = V9_STATE->saved_target;
    if (V9_STATE->work_mode == 0u) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    CURR_INSTR = BS_MOVE_END;
}

/* ============ Efeito 253: Healing Wish (361) / Lunar Dance (460) ========= */

void hook_healing_wish_prep_v9(void)
{
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    if (!has_viable_party_replacement(atk)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    u8 side = FN_GET_SIDE(atk);
    V9_STATE->healing_wish_pending[side] = (move == 460u) ? 2u : 1u;
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
    BATTLE_MOVE_DMG = (s32)(*(volatile u16 *)(a + 0x2Au));
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
}

void hook_hwish_cure_status_v9(void)
{
    if (CONTROLLER_EXEC_FLAGS != 0u)
        return;
    const u8 *p = CURR_INSTR;
    const u8 *pp_step = (const u8 *)read_u32_unaligned(p);
    u8 b = V9_STATE->work_bank & 3u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
    if (*(volatile u32 *)(m + 0x50u) == 0u) {
        CURR_INSTR = pp_step;
        return;
    }
    *(volatile u32 *)(m + 0x50u) = 0u;
    *(volatile u32 *)(m + 0x54u) &= ~0x08000000u;
    ACTIVE_BATTLER = b;
    FN_EMIT_SET_MON_DATA(0u, 0x28u, 0u, 4u, (const void *)(m + 0x50u));
    FN_MARK_BUFFER_EXEC(b);
    EFFECT_BATTLER = b;
    CURR_INSTR = p + 4;
}

void hook_hwish_restore_pp_v9(void)
{
    if (CONTROLLER_EXEC_FLAGS != 0u)
        return;
    const u8 *p = CURR_INSTR;
    const u8 *hp_step = (const u8 *)read_u32_unaligned(p);
    if (V9_STATE->work_mode != 2u) {
        CURR_INSTR = hp_step;
        return;
    }
    u8 b = V9_STATE->work_bank & 3u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
    while (V9_STATE->work_idx < 4u) {
        u8 slot = V9_STATE->work_idx++;
        u8 max_pp = calc_slot_max_pp(m, slot);
        if (max_pp > 0u && m[0x25u + slot] < max_pp) {
            m[0x25u + slot] = max_pp;
            ACTIVE_BATTLER = b;
            FN_EMIT_SET_MON_DATA(0u, (u8)(0x09u + slot), 0u, 1u, (const void *)(m + 0x25u + slot));
            FN_MARK_BUFFER_EXEC(b);
            /* Permanece nesta instrucao callasm ate sincronizar todos os slots */
            CURR_INSTR = p - 5;
            return;
        }
    }
    CURR_INSTR = hp_step;
}

void hook_hwish_prep_hp_v9(void)
{
    if (CONTROLLER_EXEC_FLAGS != 0u)
        return;
    const u8 *p = CURR_INSTR;
    const u8 *ret_step = (const u8 *)read_u32_unaligned(p);
    u8 b = V9_STATE->work_bank & 3u;
    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
    u16 hp = *(volatile u16 *)(m + 0x2Au);
    u16 max_hp = *(volatile u16 *)(m + 0x2Eu);
    if (hp >= max_hp) {
        CURR_INSTR = ret_step;
        return;
    }
    SCRIPTING_BATTLER = b;
    BATTLE_MOVE_DMG = -((s32)(max_hp - hp));
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
    HIT_MARKER |= 0x00100100u;
    CURR_INSTR = p + 4;
}

/* ==================== Efeito 254: Shed Tail (770) ======================== */

void hook_shed_tail_prep_v9(void)
{
    const u8 *p = CURR_INSTR;
    const u8 *already_sub_ptr = (const u8 *)read_u32_unaligned(p);
    const u8 *too_weak_ptr = (const u8 *)read_u32_unaligned(p + 4);

    u8 atk = ATTACKER & 3u;
    sync_battler_v9(atk);
    volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;

    if ((*(volatile u32 *)(a + 0x54u) & 0x01000000u) != 0u) {
        CURR_INSTR = already_sub_ptr;
        return;
    }
    if (!has_viable_party_replacement(atk)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }
    u16 cur_hp = *(volatile u16 *)(a + 0x2Au);
    u16 max_hp = *(volatile u16 *)(a + 0x2Eu);
    u16 cost = (u16)((max_hp + 1u) >> 1);
    if (cost < 1u)
        cost = 1u;
    if (cur_hp <= cost) {
        CURR_INSTR = too_weak_ptr;
        return;
    }

    u32 sub_hp = max_hp >> 2;
    if (sub_hp < 1u)
        sub_hp = 1u;
    if (sub_hp > 255u)
        sub_hp = 255u;

    V9_STATE->shed_tail_sub_hp[atk] = (u8)sub_hp;
    *(volatile u32 *)(a + 0x54u) = (*(volatile u32 *)(a + 0x54u) & 0xFFFF1FFFu) | 0x01000000u;
    DISABLE_STRUCTS_REAL[28u * atk + 0x0Au] = (u8)sub_hp;
    BATTLE_MOVE_DMG = (s32)cost;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
    HIT_MARKER |= 0x00000100u;
    CURR_INSTR = p + 8;
}

void hook_shed_tail_post_switch_v9(void)
{
    u8 atk = ATTACKER & 3u;
    sync_battler_v9(atk);
    u8 sub_hp = V9_STATE->shed_tail_sub_hp[atk];
    V9_STATE->shed_tail_sub_hp[atk] = 0u;
    if (sub_hp > 0u) {
        volatile u8 *a = BATTLE_MONS + 0x5Cu * atk;
        *(volatile u32 *)(a + 0x54u) |= 0x01000000u;
        DISABLE_STRUCTS_REAL[28u * atk + 0x0Au] = sub_hp;
    }
}

/* ======== Efeito 255: Copycat (383) / After You (494) / Quash (510) ====== */

void hook_turn_copy_ctrl_v9(void)
{
    const u8 *p = CURR_INSTR;
    u8 phase = p[0];
    u16 move = CURRENT_MOVE;
    u8 atk = ATTACKER & 3u;
    u8 tgt = TARGET & 3u;

    if (move == 383u) {
        /* Copycat: redireciona para o ultimo golpe executado na batalha */
        u16 copied = V9_STATE->last_used_move;
        if (is_copycat_banned_move(copied)) {
            CURR_INSTR = BS_BUT_IT_FAILED;
            return;
        }
        CURRENT_MOVE = copied;
        HIT_MARKER = (HIT_MARKER & ~0x00000400u) | 0x00000800u;
        TARGET = FN_GET_MOVE_TARGET(copied, 0u);
        u8 eff = MOVE_TABLE[12u * copied];
        CURR_INSTR = SCRIPT_TABLE_ROM[eff];
        return;
    }

    if (!is_bank_present_alive(tgt) || atk == tgt) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }

    if (move == 510u && is_behind_substitute(tgt)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }

    u32 pos = 0u;
    if (!has_battler_still_to_act(tgt, &pos)) {
        CURR_INSTR = BS_BUT_IT_FAILED;
        return;
    }

    if (phase == 0u) {
        CURR_INSTR = p + 1;
        return;
    }

    u32 cnt = BATTLERS_COUNT;
    if (cnt > 4u)
        cnt = 4u;

    if (move == 494u) {
        /* After You: move tgt para CURR_TURN_ACTION_NUM + 1 */
        u32 dest = (u32)CURR_TURN_ACTION_NUM + 1u;
        if (pos > dest) {
            u8 b_save = BATTLER_BY_TURN[pos];
            u8 a_save = ACTIONS_BY_TURN[pos];
            for (u32 k = pos; k > dest; --k) {
                BATTLER_BY_TURN[k] = BATTLER_BY_TURN[k - 1u];
                ACTIONS_BY_TURN[k] = ACTIONS_BY_TURN[k - 1u];
            }
            BATTLER_BY_TURN[dest] = b_save;
            ACTIONS_BY_TURN[dest] = a_save;
        }
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_AFTER_YOU;
        return;
    }

    if (move == 510u) {
        /* Quash: move tgt para o ultimo slot de acao do turno */
        u32 last = cnt - 1u;
        while (last > pos && ACTIONS_BY_TURN[last] != 0u)
            last--;
        if (pos < last) {
            u8 b_save = BATTLER_BY_TURN[pos];
            u8 a_save = ACTIONS_BY_TURN[pos];
            for (u32 k = pos; k < last; ++k) {
                BATTLER_BY_TURN[k] = BATTLER_BY_TURN[k + 1u];
                ACTIONS_BY_TURN[k] = ACTIONS_BY_TURN[k + 1u];
            }
            BATTLER_BY_TURN[last] = b_save;
            ACTIONS_BY_TURN[last] = a_save;
        }
        CURR_INSTR = BS_V9_STR_TAILS + 12u * TAIL_QUASH;
        return;
    }

    CURR_INSTR = BS_BUT_IT_FAILED;
}
