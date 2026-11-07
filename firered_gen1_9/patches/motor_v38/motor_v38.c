/* Exact v37 expanded ROM only. Sixty-map land encounter expansion.
 * No RNG call, saved state or global RAM allocation. All selection, level,
 * Repel and Pokemon creation remain in the native TryGenerateWildMon. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
struct Route { const void *day; const void *night; u8 group, map; u16 reserved; };
#define ROUTES ((const struct Route *)0x09121000)
#define MINUTES ((u32 (*)(void))0x090DD001)
#define VAR_SET ((u8 (*)(u16,u16))0x0808EA15)
extern u8 original_try(const void *, u8, u8);

u32 is_night(void)
{
    u32 t=MINUTES();
    return t<360 || t>=1200;
}

const void *select_info(const void *info, u8 area)
{
    if (area!=0) return info;
    const volatile u8 *s=*(const volatile u8 *volatile *)0x03006F94;
    u32 p=(u32)s;
    if (p<0x02000000 || p>0x0203FFF8 || (p&3)) return info;
    for (u32 i=0;i<60;++i) {
        const struct Route *r=&ROUTES[i];
        if (info==r->day && s[4]==r->group && s[5]==r->map)
            return is_night() ? r->night : info;
    }
    return info;
}

u8 timed_encounter(const void *info, u8 area, u8 flags)
{
    return original_try(select_info(info,area),area,flags);
}

/* Only the engine's standard transient VAR_RESULT, consumed by the sign's
 * compare immediately. No permanent event flags, items or story changes. */
void sign_period(void)
{
    VAR_SET(0x800D,(u16)is_night());
}
