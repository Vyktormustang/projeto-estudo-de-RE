// Rotina de potência dinâmica ampliada a partir do complemento anterior.
// A ROM de base
// ainda não implementa a maioria das habilidades/efeitos modernos de peso,
// velocidade ou terreno; este código é deliberadamente documentado como parcial.
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define BATTLE_MONS ((volatile u8 *)0x02021410u)
#define ATTACKER (*(volatile u8 *)0x020215A8u)
#define TARGET (*(volatile u8 *)0x020215A9u)
#define CURRENT_MOVE (*(volatile u16 *)0x02021586u)
#define DYNAMIC_POWER (*(volatile u16 *)0x02021792u)
#define WEIGHTS ((const u16 *)0x0900D000u)
#define ITEMS ((const u8 *)0x08E11000u)
#define OLD_DAMAGE ((void (*)(void))0x0805861Du)

static u32 divide(u32 n, u32 d) {
    if (!d) return 0;
    u32 q = 0;
    u32 rem = 0;
    for (u32 bit = 1u << 31; bit; bit >>= 1) {
        rem = (rem << 1) | ((n & bit) != 0);
        if (rem >= d) { rem -= d; q |= bit; }
    }
    return q;
}

static u32 speed(volatile u8 *mon) {
    u32 stat = *(volatile u16 *)(mon + 6);
    u8 stage = mon[0x1B];
    if (stage > 12) stage = 12;
    if (stage >= 6) stat = divide(stat * (stage - 4), 2);
    else stat = divide(stat * 2, 8 - stage);
    u16 item = *(volatile u16 *)(mon + 0x30);
    // Mesma regra da base Gen III para paralisia e Macho Brace.
    if (item <= 604 && ITEMS[44u * item + 18] == 24) stat /= 2;
    if (*(volatile u32 *)(mon + 0x50) & 0x40) stat /= 4;
    return stat ? stat : 1;
}

static u32 weight(volatile u8 *mon) {
    u16 species = *(volatile u16 *)mon;
    if (!species || species > 1025) return 1;
    u16 value = WEIGHTS[species];
    return value ? value : 1;
}

void damage_entry(void) {
    u16 move = CURRENT_MOVE;
    volatile u8 *a = BATTLE_MONS + 0x5cu * ATTACKER;
    volatile u8 *b = BATTLE_MONS + 0x5cu * TARGET;
    u32 power;
    if (move == 807) { // Hard Press: 100 * HP atual / HP máximo do alvo
        u32 hp = *(volatile u16 *)(b + 0x2A);
        u32 maximum = *(volatile u16 *)(b + 0x2E);
        if (!maximum) maximum = 1;
        if (hp > maximum) hp = maximum;
        // Arredondamento ao inteiro mais próximo, com empate para baixo.
        power = divide(200u * hp + maximum - 1u, 2u * maximum);
        if (!power) power = 1;
        DYNAMIC_POWER = power;
    } else if (move == 360) { // Gyro Ball
        power = divide(25u * speed(b), speed(a)) + 1;
        if (power > 150) power = 150;
        DYNAMIC_POWER = power;
    } else if (move == 485) { // Electro Ball
        u32 user = speed(a), target = speed(b);
        if (user >= target * 4u) power = 150;
        else if (user >= target * 3u) power = 120;
        else if (user >= target * 2u) power = 80;
        else if (user >= target) power = 60;
        else power = 40;
        DYNAMIC_POWER = power;
    } else if (move == 483 || move == 531) { // Heavy Slam / Heat Crash
        u32 user = weight(a), target = weight(b);
        if (user >= target * 5u) power = 120;
        else if (user >= target * 4u) power = 100;
        else if (user >= target * 3u) power = 80;
        else if (user >= target * 2u) power = 60;
        else power = 40;
        DYNAMIC_POWER = power;
    } else if (move == 511) { // Acrobatics
        DYNAMIC_POWER = (*(volatile u16 *)(a + 0x30) == 0) ? 110 : 55;
    } else if (move == 499 || move == 636) { // Stored Power / Power Trip
        power = 20;
        for (int i = 1; i <= 7; ++i) {
            u8 stage = a[0x18 + i];
            if (stage > 12) stage = 12;
            if (stage > 6) power += 20u * (stage - 6);
        }
        DYNAMIC_POWER = power;
    } else if (move == 473) { // Venoshock
        DYNAMIC_POWER = (*(volatile u32 *)(b + 0x50) & (0x08u | 0x80u)) ? 130 : 65;
    } else if (move == 505) { // Hex
        DYNAMIC_POWER = *(volatile u32 *)(b + 0x50) ? 130 : 65;
    }

    // A implementação nativa é da geração III. Substituímos os atributos só
    // durante o cálculo e os restauramos antes de retornar. Bônus de itens,
    // habilidades e telas ainda seguem a base, portanto o resultado é parcial.
    u16 atk = *(volatile u16 *)(a + 2);
    u16 spdef = *(volatile u16 *)(b + 10);
    u8 atk_stage = a[0x19], spdef_stage = b[0x1D];
    if (move == 683) { // Body Press: Defesa do próprio usuário
        *(volatile u16 *)(a + 2) = *(volatile u16 *)(a + 4);
        a[0x19] = a[0x1A];
    } else if (move == 491) { // Foul Play: Ataque do alvo
        *(volatile u16 *)(a + 2) = *(volatile u16 *)(b + 2);
        a[0x19] = b[0x19];
    } else if (move == 472 || move == 536) { // Psyshock / Psystrike
        *(volatile u16 *)(b + 10) = *(volatile u16 *)(b + 4);
        b[0x1D] = b[0x1A];
    }
    OLD_DAMAGE();
    if (move == 683 || move == 491) {
        *(volatile u16 *)(a + 2) = atk; a[0x19] = atk_stage;
    } else if (move == 472 || move == 536) {
        *(volatile u16 *)(b + 10) = spdef; b[0x1D] = spdef_stage;
    }
}
