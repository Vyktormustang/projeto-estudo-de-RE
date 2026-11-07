/* Clock v19: exact expanded v18 ROM only. No allocated RAM or save writes.
 * 60 emulated frames = 1 virtual minute; start 08:00, period 24 played min.
 * Native playtime caps at 999:59:59; this read-only clock inherits that cap.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define CALL(a) ((void (*)(void))(a))
#define GET_MON ((u32 (*)(void *, int, void *))0x0810A96D)
#define HOLD_EFFECT ((u8 (*)(u16))0x080C725D)
#define FADE ((volatile u8 *)0x0203A2BC)
#define PALETTE ((volatile u16 *)0x05000000)
#define MOVE_TABLE ((const u8 *)0x09000000)
extern u16 original_evolution(void *mon, u8 mode, u16 item);

u32 clock_minutes(void)
{
    volatile u8 *s = *(volatile u8 * volatile *)0x03006F98;
    u32 addr = (u32)s;
    if (addr < 0x02000000 || addr > 0x0203FFE0 || (addr & 3)) return 480;
    u16 hours, after, ms;
    /* Aligned reads, consistent across the native VBlank hour rollover. */
    do {
        hours = *(volatile u16 *)(s + 14);
        ms = *(volatile u16 *)(s + 16);
        after = *(volatile u16 *)(s + 14);
    } while (hours != after);
    u32 minutes = ms & 255, seconds = ms >> 8;
    if (minutes > 59 || seconds > 59 || hours > 999) return 480;
    /* (hours * 3600) % 1440 == (hours & 1) * 720, no division runtime. */
    u32 t = 480 + (hours & 1) * 720 + minutes * 60 + seconds;
    if (t >= 2880) t -= 2880;
    if (t >= 1440) t -= 1440;
    return t;
}

/* 0 night [20,06); 1 dawn [06,08); 2 day [08,18); 3 dusk [18,20). */
u32 clock_phase(void)
{
    u32 t = clock_minutes();
    if (t < 360 || t >= 1200) return 0;
    if (t < 480) return 1;
    if (t < 1080) return 2;
    return 3;
}

void clock_tint(void)
{
    u8 type = *(volatile u8 *)0x02027523; /* gMapHeader + 0x17 */
    /* Town/city/route/ocean only. Caves/underwater/indoors retain native light.
     * Do not accumulate when DMA is disabled, or recolor an active fade.
     * Only field terrain BG slots 0..12. UI 13..15 and all OBJ untouched.
     */
    if (!(type == 1 || type == 2 || type == 3 || type == 6)) return;
    if ((FADE[8] & 0x80) || (FADE[7] & 0x80)) return;
    u32 phase = clock_phase();
    if (phase == 2) return;
    static const u8 gains[4][3] = {{18,20,28}, {29,27,28}, {32,32,32}, {30,25,25}};
    u32 r = gains[phase][0], g = gains[phase][1], b = gains[phase][2];
    for (u32 i = 0; i < 13 * 16; ++i) {
        u32 c = PALETTE[i];
        PALETTE[i] = ((c & 31) * r >> 5)
            | ((((c >> 5) & 31) * g >> 5) << 5)
            | ((((c >> 10) & 31) * b >> 5) << 10);
    }
}

void clock_field_vblank(void)
{
    /* Reproduce all six native calls, in order, including transfer flags and
     * hardware fade registers. Tint hardware AFTER a fresh native DMA only.
     * Neither gPlttBufferUnfaded nor gPlttBufferFaded is ever changed here.
     */
    CALL(0x08140ACD)(); /* LoadOam */
    CALL(0x08140D91)(); /* ProcessSpriteCopyRequests */
    CALL(0x081360D9)(); /* ScanlineEffect_InitHBlankDmaTransfer */
    CALL(0x080A5125)(); /* FieldUpdateBgTilemapScroll */
    CALL(0x080F4265)(); /* TransferPlttBuffer */
    clock_tint();
    CALL(0x081496A5)(); /* TransferTilesetAnimsBuffer */
}

u16 clock_evolution(void *mon, u8 mode, u16 item)
{
    u16 original = original_evolution(mon, mode, item);
    /* Preserve EVERY native denial, including the saved Enigma Berry
     * hold-effect override, not just the static Everstone item table. */
    if (!original || mode != 0) return original;
    u16 species = GET_MON(mon, 11, 0);
    if (species != 133 && species != 406 && species != 447) return original;
    /* Preserve native friendship >=220 and Everstone, regardless of time.
     * Invalid/egg Pokémon must not enter the new timed branch. */
    if (GET_MON(mon, 45, 0) || GET_MON(mon, 4, 0)) return 0;
    if (HOLD_EFFECT(GET_MON(mon, 12, 0)) == 38) return original;
    u32 t = clock_minutes();
    u32 day = t >= 360 && t < 1200;
    if (species != 133) return day ? original : 0; /* Budew and Riolu */
    if (GET_MON(mon, 32, 0) < 220) return original;
    /* Native Eevee has an unconditional friendship->Sylveon row AFTER the
     * disabled day/night rows, plus a simplified level->Glaceon row. Resolve
     * the timed branch explicitly; Fairy-known Sylveon takes precedence.
     * Other native simplifications (low friendship, stones) remain untouched.
     */
    for (u32 i = 0; i < 4; ++i) {
        u32 move = GET_MON(mon, 13 + i, 0);
        if (move && move < 822 && MOVE_TABLE[move * 12 + 2] == 18) return 700;
    }
    return day ? 196 : 197;
}
