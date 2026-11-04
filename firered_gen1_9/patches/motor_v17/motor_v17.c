/* v17: ordem de criacao dos quatro hazards, sem dados persistentes.
 * Reusa helpers/regras v8; --gc-sections descarta os hooks nao referenciados.
 * A fila ocupa 8 bytes antes ociosos da reserva v8, nao de outro subsistema.
 */
#include "../motor_v8/motor_v8.c"

#define ORDER ((volatile u8 (*)[4])0x0203FC90u)
#define FN_UPDATE_SENT ((void (*)(u8))0x0806CAD5u)
#define SPECIAL_STATUSES ((volatile u8 *)0x0202170Cu)
#define ORIG_SET_SPIKES ((void (*)(void))0x08062D31u)
#define SPIKES_DAMAGED 0x0200u
_Static_assert(sizeof(struct V8BattleState) <= 0x30u, "order overlaps v8");

static u8 present(u8 side, u8 hazard)
{
    if (hazard == 1u) return (SIDE_STATUSES[side] & 0x10u) != 0u;
    if (hazard == 2u) return V8_STATE->stealth_rock[side] != 0u;
    if (hazard == 3u) return V8_STATE->toxic_spikes[side] != 0u;
    return V8_STATE->sticky_web[side] != 0u;
}

/* Compacta apenas fora de uma sequencia em andamento. Camadas nao mudam
 * a identidade da condicao. O fallback serve a estados sinteticos pre-semeados;
 * nao pode recuperar a ordem perdida de um estado salvo por outra versao. */
static void sync_order(void)
{
    for (u8 side = 0u; side < 2u; ++side) {
        u8 count = 0u, seen = 0u;
        for (u8 i = 0u; i < 4u; ++i) {
            u8 h = ORDER[side][i];
            if (h >= 1u && h <= 4u && !(seen & (1u << h)) && present(side,h)) {
                ORDER[side][count++] = h;
                seen |= 1u << h;
            }
        }
        for (u8 h = 1u; h <= 4u; ++h)
            if (!(seen & (1u << h)) && present(side,h)) ORDER[side][count++] = h;
        while (count < 4u) ORDER[side][count++] = 0u;
    }
}

void hook_init_v17(void)
{
    for (u8 s = 0u; s < 2u; ++s)
        for (u8 i = 0u; i < 4u; ++i) ORDER[s][i] = 0u;
    hook_battle_init_v8();
}

void hook_set_spikes_v17(void) { sync_order(); ORIG_SET_SPIKES(); sync_order(); }
void hook_rapidspin_v17(void) { sync_order(); hook_rapidspinfree_v8(); sync_order(); }
void hook_defog_v17(void) { sync_order(); hook_defog_clear_v8(); sync_order(); }
void hook_tidy_v17(void) { sync_order(); hook_tidy_up_clear_v8(); sync_order(); }
void hook_hazard_hit_v17(void) { sync_order(); hook_hazard_hit_apply_v8(); sync_order(); }

void hook_field_apply_v17(void)
{
    sync_order();
    u16 move = CURRENT_MOVE;
    hook_field_status_apply_v8();
    if (move == 681u) {
        for (u8 i = 0u; i < 4u; ++i) swap_u8(&ORDER[0][i], &ORDER[1][i]);
    }
    sync_order();
}

static void end_sequence(void)
{
    V8_STATE->switchin_hazard_step = 0u;
    V8_STATE->switchin_tag = 0u;
}

void hook_switchin_v17(void)
{
    const u8 *instr = CURR_INSTR;
    u8 b = FN_GET_SCRIPT_BANK(instr[1]) & 3u;
    u8 side = FN_GET_SIDE(b);
    u32 tag = mon_tag(b);
    volatile u8 *m = BATTLE_MONS + 0x5Cu * b;
    if (V8_STATE->switchin_hazard_step == 0u
        || V8_STATE->switchin_tag != tag || V8_STATE->switchin_bank != b) {
        sync_order();
        V8_STATE->switchin_hazard_step = 1u;
        V8_STATE->switchin_tag = tag;
        V8_STATE->switchin_bank = b;
        /* Prologo nativo de 0805DD44, antes de qualquer hazard/KO. Essencial
         * para participacao/EXP e reposicao no mesmo banco. A parte restante
         * (habilidades/itens, cancelamento de acao e avancar banco) fica nativa
         * e so ocorre depois dos hazards, se o entrante ainda estiver vivo. */
        ACTIVE_BATTLER = b;
        FN_UPDATE_SENT(b);
        HIT_MARKER &= ~(1u << (28u + b));
        SPECIAL_STATUSES[20u*b] &= (u8)~0x40u;
    }
    if ((ABSENT_BATTLERS & (1u << b)) || *(volatile u16 *)(m + 0x2Au) == 0u) {
        SIDE_STATUSES[side] &= (u16)~SPIKES_DAMAGED;
        end_sequence();
        CURR_INSTR = instr + 2;
        return;
    }
    while (V8_STATE->switchin_hazard_step <= 4u) {
        u8 index = V8_STATE->switchin_hazard_step++ - 1u;
        u8 hazard = ORDER[side][index];
        if (hazard == 0u || !present(side,hazard)) continue;
        if (hazard == 1u || hazard == 2u) {
            u32 damage;
            if (hazard == 1u) {
                if (!is_battler_grounded(b)) continue;
                u8 layers = SIDE_TIMERS[12u*side+10u];
                if (layers < 1u) layers = 1u;
                if (layers > 3u) layers = 3u;
                damage = FN_UDIV32(*(volatile u16 *)(m+0x2Eu), (5u-layers)*2u);
            } else {
                u32 mult = stealth_rock_mult32(m[0x22u],m[0x23u]);
                if (mult == 0u) continue;
                damage = ((u32)*(volatile u16 *)(m+0x2Eu)*mult) >> 5;
            }
            if (damage == 0u) damage = 1u;
            SCRIPTING_BATTLER = b;
            FAINTED_BATTLER = b;
            BATTLE_MOVE_DMG = (s32)damage;
            MOVE_RESULT_FLAGS &= (u8)~0x29u;
            FN_BS_PUSH(instr);
            CURR_INSTR = hazard == 1u ? BS_V8_HAZARD_SPIKES_G : BS_V8_HAZARD_SROCK;
            return;
        }
        if (hazard == 3u && is_battler_grounded(b)) {
            u8 layers = V8_STATE->toxic_spikes[side];
            u8 t1 = m[0x22u], t2 = m[0x23u];
            if (t1 == 3u || t2 == 3u) {
                V8_STATE->toxic_spikes[side] = 0u;
                /* Nao compactar: isso saltaria o proximo hazard da entrada. */
                ORDER[side][index] = 0u;
                SCRIPTING_BATTLER = b;
                FN_BS_PUSH(instr);
                CURR_INSTR = BS_V8_TSPIKES_ABSORB;
                return;
            }
            u16 ability = *(volatile u16 *)(m + 0x20u);
            u32 status1 = *(volatile u32 *)(m + 0x50u);
            u32 status2 = *(volatile u32 *)(m + 0x54u);
            u8 misty = V8_STATE->terrain_type == TERRAIN_MISTY && V8_STATE->terrain_turns > 0u;
            if (t1 != 8u && t2 != 8u && ability != 17u && status1 == 0u
                && !(status2 & 0x01000000u) && !(SIDE_STATUSES[side] & 0x0020u) && !misty) {
                *(volatile u32 *)(m+0x50u) = layers >= 2u ? 0x80u : 0x08u;
                ACTIVE_BATTLER = b;
                FN_EMIT_SET_MON_DATA(0u,0x28u,0u,4u,(const void *)(m+0x50u));
                FN_MARK_BUFFER_EXEC(b);
                EFFECT_BATTLER = b;
                FN_BS_PUSH(instr);
                CURR_INSTR = layers >= 2u ? BS_TOXIC_EFF : BS_POISON_EFF;
                return;
            }
        }
        if (hazard == 4u && is_battler_grounded(b)) {
            SCRIPTING_BATTLER = b;
            V8_STATE->saved_target = TARGET;
            TARGET = b;
            FN_BS_PUSH(instr);
            CURR_INSTR = BS_V8_STICKY_WEB_DROP;
            return;
        }
    }
    /* Impede uma segunda aplicacao pelos Spikes nativos, sem esconder a
     * condicao do campo. O proprio nativo limpa o bit ao concluir as etapas.
     * Se uma habilidade/um item abrir script, a fase 5 permanece ate voltar. */
    SIDE_STATUSES[side] |= SPIKES_DAMAGED;
    ORIG_SWITCHINEFFECTS();
    if (CURR_INSTR == instr + 2) end_sequence();
}
