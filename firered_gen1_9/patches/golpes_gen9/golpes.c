/* Engine de aprendizado por nível para esta ROM exata, ARM7TDMI/Thumb.
 * Dados de entrada: pares (u16 move, u8 level) em três bytes, terminados por
 * move 0xffff. Os IDs de golpe são completos (16 bits), sem a máscara antiga
 * de 9 bits. Nível 0 representa um golpe aprendido na evolução.
 * Sem alocação persistente ou alteração do formato de Pokémon/saves.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
struct Entry { u8 lo, hi, level; };

#define TABLE ((const struct Entry *const *)0x08f50000u)
#define SPECIES_MAX 1025u
#define SPECIES_EGG 1026u
#define END 0xffffu
#define ALREADY 0xfffeu
#define MOVE_COUNT_MAX 50u
#define RELEARN_MAX 24u
#define GetMonData ((u32 (*)(const void *, u32, void *))0x0810a96du)
#define GetBoxData ((u32 (*)(const void *, u32, void *))0x0810aa09u)
#define BoxLevel ((u8 (*)(const void *))0x0810957du)
#define GiveMove ((u16 (*)(void *, u16))0x081095e9u)
#define DeleteFirst ((void (*)(void *, u16))0x081098fdu)
#define gIndex (*(volatile u8 *)0x0203a730u)
#define gMoveToLearn (*(volatile u16 *)0x02021866u)

static const struct Entry empty_list[] = {{0xff, 0xff, 0xff}};
static u16 get_move(const struct Entry *p) { return (u16)(p->lo | ((u16)p->hi << 8)); }

static const struct Entry *get_list(u16 species)
{
    if (species == 0 || species > SPECIES_MAX)
        return empty_list;
    return TABLE[species];
}

/* Substitui GiveBoxMonInitialMoveset. Nível 0 também pode estar disponível
 * para um Pokémon já evoluído encontrado na natureza/recebido por evento. */
void modern_initial(void *box)
{
    u16 species = (u16)GetBoxData(box, 11, (void *)0);
    u8 level = BoxLevel(box);
    const struct Entry *p = get_list(species);
    for (; get_move(p) != END; p++) {
        if (p->level > level)
            break;
        if (GiveMove(box, get_move(p)) == END)
            DeleteFirst(box, get_move(p));
    }
}

/* Mesmo contrato do jogo: primeiro=1 inicia busca; primeiro=0 continua.
 * A versão de evolução inclui golpes de nível 0 e do nível atual. */
static u16 try_move(void *mon, u8 first, u8 evolving)
{
    u16 species = (u16)GetBoxData(mon, 11, (void *)0);
    u8 level = *((u8 *)mon + 84);
    const struct Entry *p = get_list(species);
    u8 i = first ? 0 : gIndex;
    for (; get_move(&p[i]) != END; i++) {
        if (p[i].level == level || (evolving && p[i].level == 0)) {
            gIndex = i + 1;
            gMoveToLearn = get_move(&p[i]);
            return GiveMove(mon, get_move(&p[i]));
        }
    }
    gIndex = i;
    return 0;
}

u16 modern_try_level(void *mon, u8 first)
{
    return try_move(mon, first, 0);
}

/* Chamado somente pelas duas cenas de evolução. A cena também é executada
 * quando o jogador cancela; nesse caso preserva a busca original por nível. */
u16 modern_try_evolution(void *mon, u8 first, u16 canceled)
{
    return try_move(mon, first, canceled == 0);
}

/* A interface possui 25 itens incluindo Cancelar: nunca escreve mais que 24.
 * Se uma lista exceder isso, prioriza os últimos movimentos elegíveis. */
u8 modern_relearn(void *mon, u16 *out)
{
    u16 species = (u16)GetMonData(mon, 65, (void *)0);
    u16 known[4];
    const struct Entry *p;
    u8 level = *((u8 *)mon + 84), count = 0, i, j;
    if (species == SPECIES_EGG || species == 0 || species > SPECIES_MAX)
        return 0;
    for (i = 0; i < 4; i++)
        known[i] = (u16)GetMonData(mon, 13 + i, (void *)0);
    p = get_list(species);
    for (; get_move(p) != END; p++) {
        if (p->level > level)
            break;
        for (i = 0; i < 4 && known[i] != get_move(p); i++);
        if (i != 4) continue;
        for (i = 0; i < count && out[i] != get_move(p); i++);
        if (i != count) continue;
        if (count == RELEARN_MAX) {
            for (j = 1; j < RELEARN_MAX; j++) out[j - 1] = out[j];
            count--;
        }
        out[count++] = get_move(p);
    }
    return count;
}

/* O único chamador armazena até 50 u16 em sHatchedEggLevelUpMoves. */
u8 modern_egg_moves(u16 species, u16 *out)
{
    const struct Entry *p = get_list(species);
    u8 n = 0;
    while (get_move(p) != END && n < MOVE_COUNT_MAX)
        out[n++] = get_move(p++);
    return n;
}

u8 modern_relearn_count(void *mon)
{
    u16 scratch[RELEARN_MAX];
    return modern_relearn(mon, scratch);
}
