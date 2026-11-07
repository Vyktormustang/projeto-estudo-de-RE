/* Rotinas auxiliares de batalha do motor_v6 (ARM7TDMI / Thumb).
 *
 * Escopo deliberadamente contido e auditavel:
 *  - entry_damage_v6 (0x090BE000): potencia dinamica de Fling (move 374) via
 *    tabela derivada do PokeAPI items.csv em 0x090BD800, encadeando em seguida
 *    a damage_entry existente do motor_v5 (0x0900C001) sem sobrescreve-la.
 *  - entry_callasm (0x090BE008): opcode 0xF8 da tabela relocada de scripts de
 *    batalha (0x090BD400), permitindo helpers C curtos sem alterar saves/RAM.
 *  - Helpers para Fling (TM043), Poltergeist (TM198), Steel Beam (TM170) e
 *    Supercell Slam (TM210).
 *
 * Limitacoes conhecidas e documentadas:
 *  - Fling consome o item via atk6A_removeitem e aplica os efeitos secundarios
 *    dos itens nao-berry/nao-herb presentes na ROM (King's Rock flinch,
 *    Light Ball paralisia, Poison Barb veneno), mas ainda nao forca ativacao
 *    imediata de Berries/Herbs no alvo nem interage com Magic Room/Klutz.
 *  - Poltergeist nao verifica Klutz ou Magic Room (ausentes na base).
 *  - Steel Beam nao verifica Magic Guard (ausente na base).
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef int s32;

#define BATTLE_MONS       ((volatile u8 *)0x02021410u)
#define CURRENT_MOVE      (*(volatile u16 *)0x02021586u)
#define BATTLE_MOVE_DMG   (*(volatile s32 *)0x0202158Cu)
#define ATTACKER          (*(volatile u8 *)0x020215A8u)
#define TARGET            (*(volatile u8 *)0x020215A9u)
#define CURR_INSTR        (*(const u8 *volatile *)0x020215B0u)
#define MOVE_RESULT_FLAGS (*(volatile u8 *)0x02021608u)
#define MOVE_EFFECT_BYTE  (*(volatile u8 *)0x020216C3u)
#define DYNAMIC_POWER     (*(volatile u16 *)0x02021792u)

#define BS_BUT_IT_FAILED  ((const u8 *)0x0818708Fu)
#define BS_MOVE_END       ((const u8 *)0x081853F6u)
#define ITEMS             ((const u8 *)0x08E11000u)
#define FLING_TABLE       ((const u8 *)0x090BD800u)
#define MAX_ITEM_ID       604u
#define PREV_DAMAGE_ENTRY ((void (*)(void))0x0900C001u)

static u8 fling_power_for(u16 item)
{
    if (item == 0u || item > MAX_ITEM_ID)
        return 0u;
    /* Nunca consumir Key Items (bolso 2, ex.: fosseis em FireRed) ou HMs. */
    if (ITEMS[44u * item + 26u] == 2u || (item >= 339u && item <= 346u))
        return 0u;
    return FLING_TABLE[2u * item];
}

void hook_damage_v6(void)
{
    if (CURRENT_MOVE == 374u) {
        volatile u8 *a = BATTLE_MONS + 0x5Cu * ATTACKER;
        u16 item = *(volatile u16 *)(a + 0x30u);
        u8 pwr = fling_power_for(item);
        DYNAMIC_POWER = pwr ? (u16)pwr : 1u;
    }
    PREV_DAMAGE_ENTRY();
}

void hook_callasm(void)
{
    const u8 *p = CURR_INSTR;
    u32 addr = (u32)p[1] | ((u32)p[2] << 8) | ((u32)p[3] << 16) | ((u32)p[4] << 24);
    CURR_INSTR = p + 5;
    ((void (*)(void))(addr | 1u))();
}

void hook_fling_check(void)
{
    volatile u8 *a = BATTLE_MONS + 0x5Cu * ATTACKER;
    u16 item = *(volatile u16 *)(a + 0x30u);
    if (fling_power_for(item) == 0u)
        CURR_INSTR = BS_BUT_IT_FAILED;
}

void hook_fling_secondary(void)
{
    volatile u8 *a = BATTLE_MONS + 0x5Cu * ATTACKER;
    u16 item = *(volatile u16 *)(a + 0x30u);
    MOVE_EFFECT_BYTE = (item <= MAX_ITEM_ID) ? FLING_TABLE[2u * item + 1u] : 0u;
}

void hook_poltergeist_check(void)
{
    volatile u8 *b = BATTLE_MONS + 0x5Cu * TARGET;
    u16 item = *(volatile u16 *)(b + 0x30u);
    if (item == 0u)
        CURR_INSTR = BS_BUT_IT_FAILED;
}

void hook_steel_beam_dmg(void)
{
    volatile u8 *a = BATTLE_MONS + 0x5Cu * ATTACKER;
    u16 hp = *(volatile u16 *)(a + 0x2Au);
    if (hp == 0u) {
        CURR_INSTR = BS_MOVE_END;
        return;
    }
    u32 max_hp = *(volatile u16 *)(a + 0x2Eu);
    s32 dmg = (s32)((max_hp + 1u) >> 1);
    if (dmg < 1)
        dmg = 1;
    BATTLE_MOVE_DMG = dmg;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
}

void hook_supercell_dmg(void)
{
    volatile u8 *a = BATTLE_MONS + 0x5Cu * ATTACKER;
    u16 hp = *(volatile u16 *)(a + 0x2Au);
    if (hp == 0u) {
        CURR_INSTR = BS_MOVE_END;
        return;
    }
    u32 max_hp = *(volatile u16 *)(a + 0x2Eu);
    s32 dmg = (s32)(max_hp >> 1);
    if (dmg < 1)
        dmg = 1;
    BATTLE_MOVE_DMG = dmg;
    MOVE_RESULT_FLAGS &= (u8)~0x29u;
}
