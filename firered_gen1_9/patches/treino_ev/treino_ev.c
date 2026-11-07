/*
 * Treino de EV para a ROM PT-BR de encontros deste projeto.
 *
 * Codigo proprio, especifico para a ROM identificada por SHA-256 no patcher.
 * Nao usa saves adicionais: edita somente EVs existentes no Pokemon da equipe.
 * A estrutura de resumo tem um byte de alinhamento livre em +0x3221. Seu bit
 * alto marca a visualizacao temporaria; nao e parte de Pokemon nem do save.
 *
 * Atencao: os enderecos e offsets abaixo NAO sao portaveis para outra ROM.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;

#define PTR(address, type) ((type)(address))
#define READ8(p, o) (*(u8 *)((u8 *)(p) + (o)))
#define READ16(p, o) (*(u16 *)((u8 *)(p) + (o)))
#define READ32(p, o) (*(u32 *)((u8 *)(p) + (o)))

#define SUMMARY_PTR PTR(0x0203ac9c, u8 **)
#define SKILLS_XPOS_PTR PTR(0x0203aca0, u16 **)
#define SELECTED_MON PTR(0x0203acc8, u8 *)
#define PLAYER_PARTY PTR(0x0203a98c, u8 *)
#define MAIN PTR(0x0300460c, u8 *)

#define MON_LIST_OFFSET 0x330c
#define CURRENT_MON_OFFSET 0x32a8
#define ABILITY_DESC_OFFSET 0x31e4
#define HP_TEXT_OFFSET 0x3090
#define STAT_TEXT_OFFSET 0x309c
#define WINDOW_IDS_OFFSET 0x3000
#define STATE_OFFSET 0x3288
#define MODE_OFFSET 0x3220
#define META_OFFSET 0x3221 /* alignment byte following the u8 mode */
#define PAGE_OFFSET 0x322c
#define EGG_OFFSET 0x3218
#define BAD_EGG_OFFSET 0x321c
#define LAST_INDEX_OFFSET 0x3228
#define BOX_MON_OFFSET 0x3234
#define ENEMY_PARTY_OFFSET 0x3024

#define A_BUTTON 0x0001
#define B_BUTTON 0x0002
#define SELECT_BUTTON 0x0004
#define RIGHT_BUTTON 0x0010
#define LEFT_BUTTON 0x0020
#define UP_BUTTON 0x0040
#define DOWN_BUTTON 0x0080
#define R_BUTTON 0x0100
#define L_BUTTON 0x0200

#define GET_MON PTR(0x0810a96d, u32 (*)(void *, int, void *))
#define SET_MON PTR(0x0810af79, void (*)(void *, int, const void *))
#define CALCULATE_STATS PTR(0x081090ed, void (*)(void *))
#define BUFFER_SKILLS PTR(0x08123d0d, void (*)(void))
#define PRINT_RIGHT_PANE PTR(0x08124811, void (*)(void))
#define PRINT_ABILITY PTR(0x081254ad, void (*)(void))
#define PRINT_CONTROLS PTR(0x081246dd, void (*)(const u8 *))
#define COPY_WINDOW PTR(0x08165411, void (*)(u8, u8))
#define UPDATE_HP_BAR PTR(0x08127a65, void (*)(void))
#define DECIMAL PTR(0x0814408d, u8 *(*)(u8 *, int, u8, u8))
#define STRLEN_GAME PTR(0x08144025, u16 (*)(const u8 *))
#define IS_TASK_ACTIVE PTR(0x08144a05, u8 (*)(void *))
#define SWITCH_TASK PTR(0x08128a91, void *)
#define FLIP_TASK PTR(0x08122565, void *)
#define LINK_BUSY PTR(0x080e164d, u8 (*)(void))
#define LINK_QUEUE_BUSY PTR(0x080d64dd, u8 (*)(void))

/* ordem da tela: HP, ataque, defesa, esp. ataque, esp. defesa, velocidade */
static const u8 s_statOrder[6] = {0, 1, 2, 4, 5, 3};
/* Small header hint, encoded in the game's native character set. */
static const u8 s_controlsHint[] = {
    0xcd, 0xbf, 0xc6, 0xbf, 0xbd, 0xce, 0x00,
    0xbf, 0xd0, 0xba, 0xc3, 0xd0, 0xff
};

static void copy_bytes(u8 *out, const u8 *in, unsigned count)
{
    unsigned i;
    for (i = 0; i < count; ++i)
        out[i] = in[i];
}

static int equal_bytes(const u8 *a, const u8 *b, unsigned count)
{
    unsigned i;
    for (i = 0; i < count; ++i)
        if (a[i] != b[i])
            return 0;
    return 1;
}

/* Check the encrypted 48-byte box record without invoking a mutating reader. */
static int valid_checksum(const u8 *mon)
{
    u32 key = READ32(mon, 0) ^ READ32(mon, 4);
    u32 sum = 0;
    unsigned i;
    for (i = 0; i < 12; ++i)
    {
        u32 word = READ32(mon, 32 + 4 * i) ^ key;
        sum += (word & 0xffffu) + (word >> 16);
    }
    return (u16)sum == READ16(mon, 28);
}

static u32 ev(u8 *mon, unsigned visualIndex)
{
    return GET_MON(mon, 26 + s_statOrder[visualIndex], (void *)0);
}

static void set_ev(u8 *mon, unsigned visualIndex, u8 value)
{
    SET_MON(mon, 26 + s_statOrder[visualIndex], &value);
}

static unsigned ev_total(u8 *mon)
{
    unsigned i, total = 0;
    for (i = 0; i < 6; ++i)
        total += ev(mon, i);
    return total;
}

/* Encoding is the game's native character set; no external text engine. */
static u8 game_char(char c)
{
    if (c >= 'A' && c <= 'Z') return (u8)(0xbb + c - 'A');
    if (c >= '0' && c <= '9') return (u8)(0xa1 + c - '0');
    if (c == '/') return 0xba;
    if (c == ':') return 0xf0;
    if (c == '-') return 0xae;
    return 0;
}

static u8 *append_ascii(u8 *out, const char *s)
{
    while (*s) *out++ = game_char(*s++);
    return out;
}

static u8 *append_number(u8 *out, unsigned value)
{
    return DECIMAL(out, (int)value, 0, 3);
}

/* view = 1 (EV), 2 (IV), 3 (temporary EV editor). */
static void draw(u8 *summary, unsigned view, unsigned cursor, unsigned step, unsigned pool)
{
    u8 *work = summary + CURRENT_MON_OFFSET;
    u16 *xpos = *SKILLS_XPOS_PTR;
    u8 *desc = summary + ABILITY_DESC_OFFSET;
    u8 *p;
    unsigned i;
    BUFFER_SKILLS(); /* Also restores the real ability description when needed. */

    if (view != 0)
    {
        for (i = 0; i < 6; ++i)
        {
            u8 *text = i == 0 ? summary + HP_TEXT_OFFSET : summary + STAT_TEXT_OFFSET + (i - 1) * 5;
            unsigned value = view == 2
                ? GET_MON(work, 39 + s_statOrder[i], (void *)0)
                : ev(work, i);
            unsigned length;
            if (view == 3 && i == cursor)
                *text++ = 0x86; /* > selected attribute */
            DECIMAL(text, (int)value, 0, 3);
            text = i == 0 ? summary + HP_TEXT_OFFSET : summary + STAT_TEXT_OFFSET + (i - 1) * 5;
            length = STRLEN_GAME(text);
            xpos[1 + i] = (u16)((i == 0 ? 63 : 27) - length * 6);
        }
        p = desc;
        if (view == 1)
        {
            unsigned total = ev_total(work);
            p = append_ascii(p, "EV ");
            p = append_number(p, total);
            p = append_ascii(p, total <= 510 ? "/510  A:TREINAR" : "/510  INVALIDO");
        }
        else if (view == 2)
        {
            p = append_ascii(p, "IV NATURAIS  SELECT:ATR");
        }
        else
        {
            p = append_ascii(p, "SALDO ");
            p = append_number(p, pool);
            p = append_ascii(p, " SELECT:");
            p = append_number(p, step);
            p = append_ascii(p, " A:OK B:SAIR");
        }
        *p = 0xff;
    }

    PRINT_RIGHT_PANE();
    PRINT_ABILITY();
    COPY_WINDOW(summary[WINDOW_IDS_OFFSET + 3], 2);
    COPY_WINDOW(summary[WINDOW_IDS_OFFSET + 5], 2);
}

static u8 pack_meta(unsigned view, unsigned cursor, unsigned step)
{
    return (u8)(0xc0u | view | (cursor << 2) | (step == 4 ? 0x20u : 0));
}

static int is_safe_context(u8 *summary)
{
    u32 ptr = (u32)summary;
    u32 xp = (u32)*SKILLS_XPOS_PTR;
    unsigned index = *SELECTED_MON;
    if (ptr < 0x02000000 || ptr > 0x02040000 - 0x3320) return 0;
    if (xp < 0x02000000 || xp > 0x02040000 - 32 || (xp & 1)) return 0;
    if (READ8(MAIN, 0x439) & 2) return 0;
    if (READ8(summary, PAGE_OFFSET) != 1 || READ8(summary, STATE_OFFSET) != 2) return 0;
    if (READ8(summary, MODE_OFFSET) != 0 || READ8(summary, BOX_MON_OFFSET) != 0) return 0;
    if (READ8(summary, EGG_OFFSET) || READ8(summary, BAD_EGG_OFFSET)) return 0;
    if (READ32(summary, ENEMY_PARTY_OFFSET)) return 0;
    if (READ32(summary, MON_LIST_OFFSET) != (u32)PLAYER_PARTY) return 0;
    if (index >= 6 || index > READ8(summary, LAST_INDEX_OFFSET)) return 0;
    return 1;
}

/*
 * Return true only if the draft differs from the real Pokemon exclusively in
 * its six EVs. Reconstruct an expected original copy and compare all 100 bytes,
 * so a stale or different Pokemon can never be overwritten accidentally.
 */
static int matches_except_evs(u8 *draft, u8 *real)
{
    u32 aligned_copy[25];
    u8 *copy = (u8 *)aligned_copy;
    unsigned i;
    copy_bytes(copy, draft, 100);
    for (i = 0; i < 6; ++i)
        set_ev(copy, i, (u8)ev(real, i));
    return valid_checksum(copy) && equal_bytes(copy, real, 100);
}

static int commit(u8 *draft, u8 *real)
{
    u16 oldHp = READ16(real, 0x56);
    u16 oldMax = READ16(real, 0x58);
    u8 oldLevel = READ8(real, 0x54);
    u16 newMax;
    int correctedHp;
    if (!valid_checksum(draft) || !valid_checksum(real)) return 0;
    if (ev_total(draft) != ev_total(real) || ev_total(real) > 510) return 0;
    if (!matches_except_evs(draft, real)) return 0;
    if (!oldMax || oldHp > oldMax) return 0;

    CALCULATE_STATS(draft);
    newMax = READ16(draft, 0x58);
    if (!newMax || READ8(draft, 0x54) != oldLevel) return 0;
    if (oldHp == 0)
        correctedHp = 0; /* Do not revive a fainted Pokemon. */
    else
    {
        correctedHp = (int)oldHp + (int)newMax - (int)oldMax;
        if (correctedHp < 1) correctedHp = 1; /* avoid HP underflow */
        if (correctedHp > (int)newMax) correctedHp = newMax;
    }
    READ16(draft, 0x56) = (u16)correctedHp;
    if (!valid_checksum(draft)) return 0;
    copy_bytes(real, draft, 100);
    return 1;
}

/* Return 1 when the original task must not process these keys. */
int treino_handle_input(void)
{
    u8 *summary = *SUMMARY_PTR;
    u8 *draft, *real;
    unsigned meta, view, cursor, step, newKeys, repeated, original, current, pool;
    if (!is_safe_context(summary)) return 0;
    if (LINK_BUSY() == 1 || LINK_QUEUE_BUSY() == 1) return 0;
    if (IS_TASK_ACTIVE(SWITCH_TASK) || IS_TASK_ACTIVE(FLIP_TASK)) return 0;
    newKeys = READ16(MAIN, 0x2e);
    repeated = READ16(MAIN, 0x30);
    meta = READ8(summary, META_OFFSET);
    view = meta & 0x80 ? meta & 3 : 0;
    cursor = meta >> 2 & 7;
    step = meta & 0x20 ? 4 : 1;
    if (cursor > 5) cursor = 0;
    if ((meta & 0x40) && !(newKeys | repeated)) return view == 3;

    draft = summary + CURRENT_MON_OFFSET;
    real = PLAYER_PARTY + *SELECTED_MON * 100;
    if (!valid_checksum(draft) || !valid_checksum(real)) return 0;
    if (!GET_MON(real, 11, (void *)0) || !GET_MON(draft, 11, (void *)0)) return 0;
    if (!(meta & 0x40))
    {
        PRINT_CONTROLS(s_controlsHint);
        COPY_WINDOW(summary[WINDOW_IDS_OFFSET + 1], 2);
        meta |= 0x40;
        READ8(summary, META_OFFSET) = (u8)meta;
    }
    if (!(newKeys | repeated)) return view == 3;

    if (view == 3)
    {
        original = ev_total(real);
        current = ev_total(draft);
        /* Corruption/stale copy: discard only the draft, never touch party. */
        if (original > 510 || current > original || !matches_except_evs(draft, real))
        {
            copy_bytes(draft, real, 100);
            READ8(summary, META_OFFSET) = 0x40;
            draw(summary, 0, 0, 1, 0);
            return 1;
        }
        pool = original - current;
        if (newKeys & (B_BUTTON | L_BUTTON | R_BUTTON))
        {
            copy_bytes(draft, real, 100);
            READ8(summary, META_OFFSET) = 0x40;
            draw(summary, 0, 0, 1, 0);
            /* Preserve native L/R help. B is consumed as editor cancel. */
            return (newKeys & B_BUTTON) ? 1 : 0;
        }
        if (newKeys & A_BUTTON)
        {
            if (pool == 0)
            {
                if (commit(draft, real)) UPDATE_HP_BAR();
                else copy_bytes(draft, real, 100);
                READ8(summary, META_OFFSET) = 0x40;
                draw(summary, 0, 0, 1, 0);
            }
            return 1;
        }
        if (newKeys & SELECT_BUTTON)
            step = step == 1 ? 4 : 1;
        else if (repeated & UP_BUTTON)
            cursor = cursor ? cursor - 1 : 5;
        else if (repeated & DOWN_BUTTON)
            cursor = cursor == 5 ? 0 : cursor + 1;
        else if (repeated & LEFT_BUTTON)
        {
            unsigned value = ev(draft, cursor);
            unsigned amount = value < step ? value : step;
            set_ev(draft, cursor, (u8)(value - amount));
            pool += amount;
        }
        else if (repeated & RIGHT_BUTTON)
        {
            unsigned value = ev(draft, cursor);
            unsigned room = 255 - value;
            unsigned amount = pool < step ? pool : step;
            if (amount > room) amount = room;
            set_ev(draft, cursor, (u8)(value + amount));
            pool -= amount;
        }
        else
            return 1; /* Modal: native task must not exit or switch Pokemon. */
        READ8(summary, META_OFFSET) = pack_meta(3, cursor, step);
        draw(summary, 3, cursor, step, pool);
        return 1;
    }

    if (newKeys & SELECT_BUTTON)
    {
        view = view == 0 ? 1 : view == 1 ? 2 : 0;
        READ8(summary, META_OFFSET) = view ? pack_meta(view, 0, 4) : 0x40;
        draw(summary, view, 0, 4, 0);
        return 1;
    }
    if (view == 1 && (newKeys & A_BUTTON))
    {
        if (ev_total(real) <= 510 && equal_bytes(draft, real, 100))
        {
            READ8(summary, META_OFFSET) = pack_meta(3, 0, 4);
            draw(summary, 3, 0, 4, 0);
        }
        return 1;
    }
    if (newKeys & (B_BUTTON | L_BUTTON | R_BUTTON | UP_BUTTON | DOWN_BUTTON | LEFT_BUTTON | RIGHT_BUTTON))
    {
        READ8(summary, META_OFFSET) = 0;
        if (view) draw(summary, 0, 0, 1, 0);
    }
    return 0;
}
