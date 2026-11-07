/* Exact v23. Keep native playtime/display capped; continue WORLD time only.
 * Shared project-owned T9X1 reservation: packed quantities end at +0x35FB;
 * CK24 uses +0x3658..365F, inside the already saved 400-byte extension.
 * Update is called from the main loop, NOT an IRQ. Existing TM migration is
 * queried once if needed; no new layout or independent item migration.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define SAVE1 (*(volatile u8 *volatile *)0x03006F94)
#define SAVE2 (*(volatile u8 *volatile *)0x03006F98)
#define STATE (*(volatile u8 *)0x030021D6)
#define QUANTITY ((u16 (*)(u16))0x080C7101)
#define T9 0x31583954u
#define CLOCK 0x34324B43u /* CK24 */
#define EXT 0x34D8u
#define RECORD 0x3658u
extern void original_update(void);

static u32 ptr_ok(const volatile u8 *s, u32 end) {
    u32 a=(u32)s;
    return a>=0x02000000u && a<=end && !(a&3);
}
static u32 time_ok(const volatile u8 *s) {
    return ptr_ok(s,0x0203FFE0u) && *(const volatile u16 *)(s+14)<=999
        && s[16]<60 && s[17]<60 && s[18]<60;
}
static u32 capped(const volatile u8 *s) {
    return *(const volatile u16 *)(s+14)==999 && s[16]==59 && s[17]==59 && s[18]==59;
}
/* CRC-15/CAN polynomial over the 17 payload bits, MSB first, seed 0x1D0F.
 * One aligned word commits minutes+frames+check atomically for VBlank readers.
 */
static u32 pack(u32 minute, u32 frame) {
    u32 raw=minute|(frame<<11), crc=0x1D0F;
    for (u32 i=0;i<17;++i) {
        u32 feedback=((crc>>14)^(raw>>(16-i)))&1;
        crc=(crc<<1)&0x7FFF;
        if (feedback) crc^=0x4599;
    }
    return raw|(crc<<17);
}
static u32 owned(const volatile u8 *s) {
    return ptr_ok(s,0x0203BFFCu) && *(const volatile u32 *)(s+EXT)==T9;
}
static u32 record_read(const volatile u8 *s, u32 *minute, u32 *frame) {
    if (!owned(s) || *(const volatile u32 *)(s+RECORD)!=CLOCK) return 0;
    u32 word=*(const volatile u32 *)(s+RECORD+4);
    u32 m=word&2047, f=(word>>11)&63;
    if (m>=1440 || f>=60 || word!=pack(m,f)) return 0;
    *minute=m; *frame=f; return 1;
}

u32 clock_minutes(void) {
    const volatile u8 *s=SAVE2;
    if (!ptr_ok(s,0x0203FFE0u)) return 480;
    u16 h,after,ms;
    do { h=*(const volatile u16 *)(s+14); ms=*(const volatile u16 *)(s+16);
         after=*(const volatile u16 *)(s+14); } while (h!=after);
    u32 m=ms&255, sec=ms>>8;
    if (h>999 || m>59 || sec>59) return 480;
    if (h==999 && m==59 && sec==59 && s[18]==59) {
        u32 minute,frame;
        if (record_read(SAVE1,&minute,&frame)) return minute;
    }
    u32 t=480+(h&1)*720+m*60+sec;
    if (t>=2880) t-=2880;
    if (t>=1440) t-=1440;
    return t;
}

void clock_update(void) {
    u8 state=STATE;
    if (state!=1 && state!=2) return; /* STOPPED/unknown: never start time */
    volatile u8 *s=SAVE2;
    if (!time_ok(s)) return;
    volatile u8 *one=SAVE1;
    u32 minute,frame;
    if (!capped(s)) {
        /* A native time reset/new game must not resurrect an old epoch.
         * Only clear a valid owned record, and only while actually running. */
        if (state==1 && record_read(one,&minute,&frame)) {
            *(volatile u32 *)(one+RECORD)=0;
            *(volatile u32 *)(one+RECORD+4)=0;
        }
        original_update();
        return;
    }
    if (!record_read(one,&minute,&frame)) {
        /* Fail closed on foreign/corrupt data, before any migration or write. */
        if (!ptr_ok(one,0x0203BFFCu) || !ptr_ok(s,0x0203BFFCu)
            || *(volatile u32 *)(one+RECORD) || *(volatile u32 *)(one+RECORD+4)) {
            original_update(); return;
        }
        if (!owned(one)) {
            /* Cold migration must see the REAL bag, not Pokedude's temporary
             * TM pocket or a link backup. Delay this one-time activation to
             * a normal outdoor field callback. Once T9X1 exists, the clock
             * can initialize/advance in any running gameplay context. */
            u8 map_type=*(volatile u8 *)0x02027523u;
            if (*(volatile u32 *)0x03004610u!=0x080F172Du
                || !((map_type>=1 && map_type<=3) || map_type==6)) {
                original_update(); return;
            }
            (void)QUANTITY(375); /* Existing migrate validates all 400 bytes. */
            if (SAVE1!=one || SAVE2!=s || !owned(one)) { original_update(); return; }
        }
        minute=479; frame=59; /* Last native instant: 07:59 + 59/60 min. */
        /* Publish data first, magic last. Getter before publication falls
         * back to native 07:59; it never repairs/writes save data itself. */
        *(volatile u32 *)(one+RECORD+4)=pack(minute,frame);
        *(volatile u32 *)(one+RECORD)=CLOCK;
    }
    if (++frame==60) { frame=0; if (++minute==1440) minute=0; }
    *(volatile u32 *)(one+RECORD+4)=pack(minute,frame);
    STATE=2; /* Native display and non-clock systems retain native saturation. */
}
