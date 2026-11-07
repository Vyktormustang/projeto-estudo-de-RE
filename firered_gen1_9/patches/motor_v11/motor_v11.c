/* motor_v11: correcao isolada de Eerie Spell (720), sem RAM extra.
 * gLastMoves foi identificado pelo comando nativo Spite (0xAD),
 * literal 0x08062A54 -> 0x020215D4. Nao usar slot 0 como fallback.
 * Demais golpes continuam no helper original do motor_v10.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define CURRENT_MOVE (*(volatile u16 *)0x02021586u)
#define TARGET (*(volatile u8 *)0x020215A9u)
#define CURR_INSTR (*(const u8 *volatile *)0x020215B0u)
#define RESULT (*(volatile u8 *)0x02021608u)
#define MONS ((volatile u8 *)0x02021410u)
#define LAST_MOVES ((volatile u16 *)0x020215D4u)
#define PARTY_INDEX ((volatile u16 *)0x020213F8u)
#define ACTIVE (*(volatile u8 *)0x020213ECu)
#define DISABLE ((volatile u8 *)0x02021648u)
#define PREV ((void (*)(void))0x090D0061u)
#define GET_SIDE ((u8 (*)(u8))0x08024685u)
#define SET_MON ((void (*)(void *, u32, const void *))0x0810AF79u)
#define EMIT ((void (*)(u8,u8,u8,u8,const void *))0x08049DF5u)
#define MARK ((void (*)(u8))0x0806C8BDu)
#define END ((const u8 *)0x081853F6u)
#define WAIT ((const u8 *)0x090D6000u)

void hook_post_hit_v11(void)
{
    if (CURRENT_MOVE != 720u) {
        PREV();
        return;
    }
    CURR_INSTR = END;
    u8 b = TARGET;
    if (b >= 4u || b >= *(volatile u8 *)0x020213F4u
        || (*(volatile u8 *)0x020215ADu & (1u << b)) != 0u
        || (RESULT & 0x29u) != 0u)
        return;
    volatile u8 *m = MONS + 0x5Cu * b;
    u32 status2 = *(volatile u32 *)(m + 0x54u);
    if (*(volatile u16 *)(m + 0x2Au) == 0u || (status2 & 0x01000000u) != 0u)
        return;
    u16 last = LAST_MOVES[b];
    if (last == 0u || last >= 822u)
        return;
    for (u8 s = 0u; s < 4u; ++s) {
        if (*(volatile u16 *)(m + 0x0Cu + 2u * s) != last)
            continue;
        u8 pp = m[0x25u + s];
        if (pp == 0u)
            return; /* Nunca drenar outro golpe se o ultimo ja esta sem PP. */
        pp = pp > 3u ? pp - 3u : 0u;
        m[0x25u + s] = pp;
        /* Mesmo criterio de persistencia do Spite/ppreduce nativos:
         * golpes de Transform/Mimic nao devem alterar o moveset original. */
        if ((status2 & 0x00200000u) == 0u
            && ((DISABLE[28u * b + 0x18u] >> 4) & (1u << s)) == 0u) {
            u16 slot = PARTY_INDEX[b];
            if (slot >= 6u)
                return;
            u8 *party = (u8 *)(GET_SIDE(b) == 0u ? 0x0203A98Cu : 0x0203A734u);
            SET_MON(party + 100u * slot, 0x11u + s, &pp);
            ACTIVE = b;
            EMIT(0u, 0x09u + s, 0u, 1u, &pp);
            MARK(b);
            CURR_INSTR = WAIT; /* Espera controller antes de moveend. */
        }
        return;
    }
}
