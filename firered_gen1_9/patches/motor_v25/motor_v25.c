/* World clock HUD, exact v24 only. No save fields or private EWRAM reservation.
 * Native tagged OBJ resources; never allocate/free from the VBlank IRQ.
 * Slot 127 is used ONLY when disabled or the native offscreen dummy. Its affine
 * matrix halfword is never modified. Dialog/menu/fade/resource pressure hides
 * the overlay rather than borrowing another object's tiles/palette/OAM.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define TAG 0xF925u
#define CALL(a) ((void (*)(void))(a))
#define MAIN ((volatile u8 *)0x0300460C)
#define FADE ((volatile u8 *)0x0203A2BC)
#define OAM ((volatile u16 *)0x070003F8)
#define NATIVE_OAM ((volatile u16 *)0x03004A3C)
#define TILE_START ((u16 (*)(u16))0x0814212D)
#define TILE_INDEX ((u8 (*)(u16))0x08142161)
#define FREE_TILES ((void (*)(u16))0x0814208D)
#define PAL_INDEX ((u8 (*)(u16))0x08142331)
#define FREE_PAL ((void (*)(u16))0x08142379)
#define GET_MINUTE ((u32 (*)(void))0x090E6001)
struct Sheet { const void *data; u16 size,tag; };
struct Pal { const void *data; u16 tag,pad; };
#include "art.h"
static const struct Sheet sheet={background,256,TAG};
static const struct Pal palette={colors,TAG,0};

static u32 eligible(void) {
    u32 s=*(volatile u32 *)0x03006F98;
    u8 type=*(volatile u8 *)0x02027523;
    return *(volatile u32 *)(MAIN+4)==0x080F172D
        && s>=0x02000000 && s<=0x0203FFE0 && !(s&3)
        && type>=1 && type<=9
        && !*(volatile u8 *)0x03002468 /* native field-controls lock */
        && !(FADE[7]&0x80) && !(FADE[8]&0x80)
        && !(MAIN[0x439]&1);
}

void hud_prepare(void) {
    if (!eligible()) {
        if (TILE_START(TAG)!=0xFFFF) FREE_TILES(TAG);
        if (PAL_INDEX(TAG)!=0xFF) FREE_PAL(TAG);
        return;
    }
    /* Native LoadSpriteSheet has no safe full-tag-table failure branch.
     * Check a free range descriptor before entering it, as well as checking
     * its tag afterwards (its return 0 also means valid tile zero). */
    if (TILE_START(TAG)==0xFFFF && TILE_INDEX(0xFFFF)!=0xFF)
        ((u16 (*)(const struct Sheet *))0x08141FE1)(&sheet);
    if (TILE_START(TAG)==0xFFFF) {
        if (PAL_INDEX(TAG)!=0xFF) FREE_PAL(TAG);
        return;
    }
    if (PAL_INDEX(TAG)==0xFF)
        ((u8 (*)(const struct Pal *))0x08142231)(&palette);
    if (PAL_INDEX(TAG)==0xFF) FREE_TILES(TAG);
}

void hud_update(void) {
    CALL(0x090E6009)(); /* all v24 time/CRC/migration semantics, exactly once */
    hud_prepare();
}

/* BCD HHMM, with leading zeroes. No division helper/libc on ARM7TDMI. */
u32 hud_digits(u32 minute) {
    if (minute>=1440) return 0xFFFFFFFFu;
    u32 h=0,mt=0;
    if (minute>=960) { minute-=960; h+=16; }
    if (minute>=480) { minute-=480; h+=8; }
    if (minute>=240) { minute-=240; h+=4; }
    if (minute>=120) { minute-=120; h+=2; }
    if (minute>=60) { minute-=60; ++h; }
    if (minute>=40) { minute-=40; mt+=4; }
    if (minute>=20) { minute-=20; mt+=2; }
    if (minute>=10) { minute-=10; ++mt; }
    u32 ht=0;
    if (h>=20) { h-=20; ht=2; }
    else if (h>=10) { h-=10; ht=1; }
    return (ht<<12)|(h<<8)|(mt<<4)|minute;
}

static void pixel(volatile u16 *tiles,u32 x,u32 y,u32 color) {
    u32 at=((y>>3)*4+(x>>3))*16+(y&7)*2+((x&7)>>2);
    u32 shift=(x&3)*4;
    tiles[at]=(tiles[at]&~(15u<<shift))|(color<<shift);
}

static u32 slot_idle(void) {
    return (NATIVE_OAM[0]&0x0300)==0x0200
        || (NATIVE_OAM[0]==0x00A0 && NATIVE_OAM[1]==0x0130 && NATIVE_OAM[2]==0x0C00);
}

void hud_render(void) {
    /* Usually native LoadOam has already removed the previous frame's HUD.
     * If that transfer was suppressed, remove our old shape before any
     * eligibility check. Only restore an idle native slot, never its matrix.
     * Other native VBlanks erase the HUD through their ordinary OAM load. */
    if (OAM[0]==0x4004 && OAM[1]==0x80CC && slot_idle()) {
        OAM[0]=NATIVE_OAM[0]; OAM[1]=NATIVE_OAM[1]; OAM[2]=NATIVE_OAM[2];
    }
    u16 display=*(volatile u16 *)0x04000000;
    if (!eligible() || (display&0x10C0)!=0x1040) return;
    /* Non-affine disabled, not an active/double-size affine sprite. */
    if (!slot_idle()) return;
    u16 tile=TILE_START(TAG);
    u8 pal=PAL_INDEX(TAG);
    if (tile>1016 || pal>=16) return;
    u32 digits=hud_digits(GET_MINUTE());
    if (digits==0xFFFFFFFFu) return;
    volatile u16 *vram=(volatile u16 *)(0x06010000+tile*32);
    for (u32 i=0;i<128;++i) vram[i]=background[i];
    static const u8 xpos[4]={3,9,18,24};
    for (u32 d=0;d<4;++d) {
        u32 digit=(digits>>(12-d*4))&15;
        for (u32 y=0;y<7;++y) {
            u32 bits=font[digit][y];
            for (u32 x=0;x<5;++x)
                if (bits&(16u>>x)) pixel(vram,xpos[d]+x,y+4,3);
        }
    }
    pixel(vram,15,6,4); pixel(vram,15,9,4);
    /* Own OBJ palette only, after the native transfer/tint. Do not recolor
     * native buffers or other OBJ/BG banks, including during weather/fades. */
    volatile u16 *pram=(volatile u16 *)(0x05000200+pal*32);
    for (u32 i=0;i<16;++i) pram[i]=colors[i];
    OAM[1]=0x8000|204; /* wide size 2 = 32x16, x=204 */
    OAM[2]=tile|((u16)pal<<12); /* priority 0; normal OBJ, no effects */
    OAM[0]=0x4000|4; /* y=4, wide, enabled last */
}

void hud_field_vblank(void) {
    CALL(0x090DD019)(); /* v19 native transfers + v24-derived terrain tint */
    hud_render();
}
