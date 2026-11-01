// Estojo paginado e extensão persistente para a ROM identificada pelo aplicador.
// Não acessa saves pessoais fora do jogo. A expansão é ativada somente se o
// trecho de save estiver zerado ou possuir a assinatura desta versão.
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef void (*Callback)(void);
struct Slot { u16 id, quantity; };
struct Pocket { struct Slot *slots; u8 capacity; u8 padding[3]; };

#define SAVE1 (*(u8 **)0x03006f94u)
#define SAVE2 (*(u8 **)0x03006f98u)
#define POCKET (*(struct Pocket *)0x0202b7b4u)
#define STATIC ((volatile u8 *)0x0203f06cu)
#define DYNAMIC (*(u8 **)0x0203f078u)
#define MAIN ((volatile u8 *)0x0300460cu)
#define PALETTE_FADE ((volatile u8 *)0x0203a2bcu)
#define EXT_OFFSET 0x34d8u
#define EXT_SIZE 400u
#define PACK_SIZE 287u
#define FIRST 375u
#define LAST 603u
#define LEGACY_CAP 58u
#define PAGE_SIZE 115u
#define MAGIC 0x31583954u /* "T9X1" little-endian */
#define PAGE STATIC[6]

extern u8 orig_has(u16,u16);
extern u8 orig_space(u16,u16);
extern u8 orig_add(u16,u16);
extern u8 orig_remove(u16,u16);
extern u16 orig_quantity(u16);
extern void orig_init(u8,Callback,u8);
extern void orig_destroy(void);
extern void orig_input(u8);
extern void orig_title(void);

static struct Slot *legacy(void) { return (struct Slot *)(SAVE1 + 0x464); }
static u16 key(void) { return *(u16 *)(SAVE2 + 0xf24); }
static u8 *extension(void) { return SAVE1 + EXT_OFFSET; }
static u8 is_new(u16 item) { return item >= FIRST && item <= LAST; }
static u8 valid_save(void) {
    return SAVE1 && SAVE2 && (u32)SAVE1 >= 0x02000000u && (u32)SAVE1 < 0x0203c000u
         && (u32)SAVE2 >= 0x02000000u && (u32)SAVE2 < 0x0203c000u;
}
static u16 unpack(u16 index) {
    u32 pos = (u32)index * 10u;
    u8 *p = extension() + 4 + (pos >> 3);
    return (u16)(((u32)p[0] | ((u32)p[1] << 8)) >> (pos & 7u)) & 1023u;
}
static void pack(u16 index, u16 value) {
    u32 pos = (u32)index * 10u;
    u8 *p = extension() + 4 + (pos >> 3);
    u32 shift = pos & 7u, mask = 1023u << shift;
    u32 pair = (u32)p[0] | ((u32)p[1] << 8);
    pair = (pair & ~mask) | (((u32)value << shift) & mask);
    p[0] = (u8)pair; p[1] = (u8)(pair >> 8);
}

// Verifica primeiro toda a migração, inclusive pilhas duplicadas anormais;
// em qualquer dúvida a bolsa antiga permanece intacta e o motor original é usado.
static u8 migrate(void) {
    if (!valid_save()) return 0;
    u8 *ext = extension();
    if (*(u32 *)ext == MAGIC) return 1;
    for (u32 i = 0; i < EXT_SIZE; ++i) if (ext[i]) return 0;
    struct Slot *old = legacy();
    u16 crypt = key();
    for (u32 i = 0; i < LEGACY_CAP; ++i) {
        if (!is_new(old[i].id)) continue;
        u32 sum = 0;
        for (u32 j = 0; j < LEGACY_CAP; ++j)
            if (old[j].id == old[i].id) sum += old[j].quantity ^ crypt;
        if (!sum || sum > 999u) return 0;
    }
    for (u32 i = 0; i < LEGACY_CAP; ++i) {
        u16 id = old[i].id;
        if (is_new(id)) {
            u16 val = unpack(id - FIRST) + (old[i].quantity ^ crypt);
            pack(id - FIRST, val);
            old[i].id = 0;
            old[i].quantity = crypt;
        }
    }
    *(u32 *)ext = MAGIC;
    return 1;
}

// Os hooks de item comuns não podem operar sobre a página temporária.
// A restauração é síncrona; não há outro processo executando enquanto é chamada.
static struct Pocket physical(void) {
    struct Pocket prior = POCKET;
    POCKET.slots = legacy(); POCKET.capacity = LEGACY_CAP;
    return prior;
}
static void restore(struct Pocket prior) { POCKET = prior; }
static u8 old2(u8 (*func)(u16,u16), u16 item, u16 count) {
    if (!valid_save()) return func(item,count);
    struct Pocket prior = physical();
    u8 result = func(item,count);
    restore(prior); return result;
}
static void update_view(u16 item, u16 count) {
    struct Slot *view = POCKET.slots;
    if (view == legacy()) return;
    u16 crypt = key();
    for (u32 i = 0; i < POCKET.capacity; ++i) {
        if (view[i].id == item) {
            view[i].id = count ? item : 0;
            view[i].quantity = count ^ crypt;
            return;
        }
    }
    // Adições normalmente ocorrem fora da tela, mas conservar a página caso
    // algum script a invoque enquanto a lista estiver aberta.
    if (count && ((PAGE == 1 && item < FIRST + PAGE_SIZE) ||
                  (PAGE == 2 && item >= FIRST + PAGE_SIZE))) {
        for (u32 i = 0; i < POCKET.capacity; ++i) if (!view[i].id) {
            view[i].id = item; view[i].quantity = count ^ crypt; return;
        }
    }
}

u8 hook_has(u16 item, u16 count) {
    if (!is_new(item) || !migrate()) return old2(orig_has,item,count);
    u16 have = unpack(item - FIRST);
    return have != 0 && have >= count;
}
u8 hook_space(u16 item, u16 count) {
    if (!is_new(item) || !migrate()) return old2(orig_space,item,count);
    return (u32)unpack(item - FIRST) + count <= 999u;
}
u8 hook_add(u16 item, u16 count) {
    if (!is_new(item) || !migrate()) return old2(orig_add,item,count);
    u16 have = unpack(item - FIRST);
    if (!count || (u32)have + count > 999u) return 0;
    if (!orig_has(364,1) && !old2(orig_add,364,1)) return 0;
    have += count; pack(item - FIRST,have); update_view(item,have);
    return 1;
}
u8 hook_remove(u16 item, u16 count) {
    if (!is_new(item) || !migrate()) return old2(orig_remove,item,count);
    u16 have = unpack(item - FIRST);
    if (!have || have < count) return 0;
    have -= count; pack(item - FIRST,have); update_view(item,have);
    return 1;
}
u16 hook_quantity(u16 item) {
    if (is_new(item) && migrate()) return unpack(item - FIRST);
    if (!valid_save()) return orig_quantity(item);
    struct Pocket prior = physical();
    u16 result = orig_quantity(item);
    restore(prior); return result;
}

static void reopen(void);
void hook_init(u8 type, Callback exit, u8 allow) {
    if (type != 5) { PAGE = 0; STATIC[7] = 0; }
    u8 enabled = type != 4 && migrate();
    if (!enabled) PAGE = 0;
    orig_init(type,exit,allow);
    if (!DYNAMIC) return; // original também requer memória livre
    *(struct Slot **)(DYNAMIC + 20) = (struct Slot *)0;
    DYNAMIC[25] = enabled;
    if (enabled) {
        // A ajuda captura L/R antes das tarefas. Altera a opção somente em RAM
        // enquanto o estojo está aberto; hook_destroy restaura o valor exato.
        DYNAMIC[24] = SAVE2[0x13];
        if (SAVE2[0x13] == 0) SAVE2[0x13] = 1;
    }
    if (!enabled || !PAGE) return;
    u16 start = FIRST + (PAGE == 1 ? 0 : PAGE_SIZE);
    u16 end = PAGE == 1 ? FIRST + PAGE_SIZE : LAST + 1;
    struct Slot *view = ((struct Slot *(*)(u32))0x080de85du)(PAGE_SIZE * sizeof(struct Slot));
    if (!view) { PAGE = 0; return; }
    u16 crypt = key();
    u32 used = 0;
    for (u16 id = start; id < end; ++id) {
        u16 count = unpack(id - FIRST);
        if (count) { view[used].id = id; view[used++].quantity = count ^ crypt; }
    }
    for (u32 i = used; i < PAGE_SIZE; ++i) {
        view[i].id = 0; view[i].quantity = crypt;
    }
    *(struct Slot **)(DYNAMIC + 20) = view;
    POCKET.slots = view; POCKET.capacity = PAGE_SIZE;
}
void hook_destroy(void) {
    // O tutorial do Pokedude aloca a estrutura por outro caminho e NÃO
    // inicializa os bytes usados por esta extensão. Nunca interpretá-los
    // como ponteiro de página ou cópia da opção de botões.
    if (STATIC[4] == 4) { orig_destroy(); return; }
    struct Slot *view = DYNAMIC ? *(struct Slot **)(DYNAMIC + 20) : (struct Slot *)0;
    if (DYNAMIC && DYNAMIC[25] && valid_save()) SAVE2[0x13] = DYNAMIC[24];
    if (view) {
        POCKET.slots = legacy(); POCKET.capacity = LEGACY_CAP;
        ((void (*)(void *))0x080de8a1u)(view);
        *(struct Slot **)(DYNAMIC + 20) = (struct Slot *)0;
    }
    orig_destroy();
}
static void reopen(void) {
    *(volatile u16 *)(STATIC + 8) = 0;
    *(volatile u16 *)(STATIC + 10) = 0;
    hook_init(5,(Callback)0,255);
}
void hook_input(u8 task) {
    // Leitura bruta também funciona quando a opção do jogo associa L ao A.
    // O latch evita repetir a troca de página ao segurar um botão.
    u16 pressed = *(volatile u16 *)(MAIN + 0x28);
    if (!(pressed & 0x300u)) STATIC[7] = 0;
    if (!(PALETTE_FADE[7] & 0x80u) && STATIC[4] != 4 &&
        (pressed & 0x300u) && !STATIC[7] && migrate() &&
        !((u8 (*)(void))0x080e164du)()) {
        STATIC[7] = 1;
        if (pressed & 0x100u) PAGE = (PAGE + 1u) % 3u;
        else PAGE = PAGE ? PAGE - 1u : 2u;
        ((void (*)(u16))0x0813f985u)(5);
        *(Callback *)DYNAMIC = reopen;
        ((void (*)(u8))0x0814bad9u)(task);
        return;
    }
    orig_input(task);
}
// Labels cabem no mesmo espaço da janela original e indicam L/R na página 0.
static const u8 label0[] = {0xc6,0xba,0xcc,0x00,0xbb,0xc8,0xce,0xff}; // L/R ANT
static const u8 label1[] = {0xcd,0xd0,0xa1,0xa1,0xa2,0xae,0xa2,0xa2,0xa6,0xff};
static const u8 label2[] = {0xcd,0xd0,0xa2,0xa2,0xa7,0xae,0xa3,0xa3,0xaa,0xff};
void hook_title(void) {
    if (STATIC[4] == 4 || !valid_save() || *(u32 *)extension() != MAGIC) {
        orig_title(); return;
    }
    const u8 *label = PAGE == 1 ? label1 : PAGE == 2 ? label2 : label0;
    u32 width = ((u16 (*)(u8,const u8 *,u8))0x08146ea5u)(1,label,0);
    u8 x = width < 72 ? (72u-width)/2u : 0;
    ((void (*)(u8,u8,u8,u8,const u8 *,u8,const u8 *))0x080e0dadu)(3,1,x,1,(const u8 *)0x08797f94u,0,label);
}
