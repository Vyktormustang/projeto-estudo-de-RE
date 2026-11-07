/* World clock HUD v26, exact v25 only. Preference in last 8 T9X1 bytes.
 * No fixed private EWRAM reservation. Native Options SELECT is otherwise unused.
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
#define SAVE1 (*(volatile u8 *volatile *)0x03006F94)
#define SAVE2 (*(volatile u8 *volatile *)0x03006F98)
#define OPTIONS (*(volatile u8 *volatile *)0x020399B0)
#define T9 0x31583954u
#define PREF 0x3660u
#define MAGIC 0x36445548u /* HUD6 */
#define VISIBLE 0x26A5FF00u
#define HIDDEN 0x26A5FE01u /* value byte + complement; 1-bit errors rejected */
extern u32 original_input(void);
u32 hud_preference(void);
u32 hud_toggle(void);
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
    if (!eligible() || hud_preference()==1) {
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
    if (!eligible() || hud_preference()==1 || (display&0x10C7)!=0x1040) return;
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
                if (bits&(16u>>x)) pixel(vram,xpos[d]+x,y+7,3);
        }
    }
    pixel(vram,15,9,4); pixel(vram,15,12,4);
    for (u32 d=0;d<5;++d)
        for (u32 y=0;y<5;++y)
            for (u32 x=0;x<5;++x)
                if (caption[d][y]&(16u>>x)) pixel(vram,2+d*6+x,y+1,4);
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


static u32 ptr_ok(const volatile u8 *p) {
    u32 a=(u32)p;
    return a>=0x02000000 && a<=0x0203BFFC && !(a&3);
}

/* 0 = shown/default, 1 = hidden, 3 = foreign/corrupt/unavailable (shown).
 * Read only, including cold old saves. Never repair unfamiliar bytes. */
u32 hud_preference(void) {
    const volatile u8 *s=SAVE1;
    if (!ptr_ok(s)) return 3;
    u32 magic=*(const volatile u32 *)(s+PREF);
    u32 word=*(const volatile u32 *)(s+PREF+4);
    u32 owner=*(const volatile u32 *)(s+0x34D8);
    if (owner!=T9) return (!owner && !magic && !word)?0:3;
    if (!magic && !word) return 0;
    if (magic!=MAGIC) return 3;
    if (word==VISIBLE) return 0;
    if (word==HIDDEN) return 1;
    return 3;
}

static u32 options_origin(void) {
    /* Native return-to-field-with-open-menu, not title/Pokedude/link screens. */
    return *(volatile u32 *)(MAIN+8)==0x080F1B99;
}

u32 hud_toggle(void) {
    volatile u8 *opts=OPTIONS;
    if (*(volatile u32 *)(MAIN+4)!=0x080EF379 || !options_origin()
        || !ptr_ok(opts) || opts[0x10]!=2 || (FADE[7]&0x80)
        || ((u32 (*)(void))0x080E164D)()==1
        || !ptr_ok(SAVE1) || !ptr_ok(SAVE2)) return 0;
    u32 state=hud_preference();
    if (state==3) return 0;
    volatile u8 *one=SAVE1,*two=SAVE2;
    if (*(volatile u32 *)(one+0x34D8)!=T9) {
        /* Explicit option change in the NORMAL field's options screen.
         * Reuse the bag's validated migration, never migrate a temporary bag.
         * The existing routine verifies ALL 400 bytes and duplicate stacks. */
        (void)((u16 (*)(u16))0x080C7101)(375);
        if (SAVE1!=one || SAVE2!=two || *(volatile u32 *)(one+0x34D8)!=T9) return 0;
        if (hud_preference()==3) return 0;
    }
    *(volatile u32 *)(one+PREF+4)=state==1?VISIBLE:HIDDEN;
    *(volatile u32 *)(one+PREF)=MAGIC; /* publish last */
    return 1;
}

static void draw_header(u32 state) {
    ((void (*)(u8,u8))0x081658B5)(0,0x11);
    /* Preserve the actual Portuguese header and native window/font setup. */
    ((void (*)(u8,u8,const u8 *,u8,u8,u8,void *))0x08147991)
        (0,2,(const u8 *)0x086D8E00,8,1,255,(void *)0);
    static const u8 color[3]={1,2,3};
    const u8 *text=state==1?menu_hidden:state==3?menu_blocked:menu_shown;
    ((void (*)(u8,u8,u8,u8,const u8 *,u8,const u8 *))0x080E0DAD)
        (0,0,80,1,color,255,text);
    ((void (*)(u8))0x08165461)(0);
    ((void (*)(u8,u8))0x08165411)(0,3);
}

void hud_options_header(void) {
    draw_header(options_origin()?hud_preference():3);
}

u32 hud_options_input(void) {
    /* Edge-triggered SELECT alone. Never steal field SELECT, registered
     * items, Start, Help L/R, remapped L=A, or native option navigation. */
    if (*(volatile u16 *)(MAIN+0x2E)==4 && *(volatile u16 *)(MAIN+0x2C)==4) {
        if (hud_toggle()) hud_options_header(); else draw_header(3);
        return 0;
    }
    return original_input();
}
