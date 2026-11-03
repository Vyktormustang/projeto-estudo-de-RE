/* v15: duracao fixa de Disable/Encore, contando a proxima acao do alvo.
 * Mantem a aplicacao/falha nativa e sua chamada Random; so normaliza os dois
 * nibbles do timer em uma aplicacao nova bem-sucedida. Sem RAM adicional.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef void (*command)(void);
#define MOVE (*(volatile u16 *)0x02021586u)
#define TARGET (*(volatile u8 *)0x020215A9u)
#define COUNT (*(volatile u8 *)0x020213F4u)
#define CURSOR (*(const u8 *volatile *)0x020215B0u)
#define DISABLE ((volatile u8 *)0x02021648u)
#define ACTIONS ((volatile u8 *)0x02021404u)
#define ORDER ((volatile u8 *)0x02021408u)
#define CURRENT_ACTION (*(volatile u8 *)0x0202140Cu)

static u8 will_move(u8 target)
{
    u8 count = COUNT;
    if (count > 4u) count = 4u;
    /* Nao usar acted_turn_mask v10: ele nao marca certos caminhos de
     * impedimento. A fila distingue acao ainda pendente de acao ja tentada. */
    for (unsigned i = (unsigned)CURRENT_ACTION + 1u; i < count; ++i)
        if (ORDER[i] == target && ACTIONS[i] == 0u) return 1u;
    return 0u;
}

static void apply(command previous, u16 expected_move, u8 field, u8 timer, u8 turns)
{
    u8 target = TARGET;
    if (MOVE != expected_move || target >= 4u || target >= COUNT) {
        previous();
        return;
    }
    volatile u8 *d = DISABLE + 28u*target;
    u16 before_move = *(volatile u16 *)(d + field);
    const u8 *before_cursor = CURSOR;
    u8 pending = will_move(target);
    previous();
    if (TARGET == target && MOVE == expected_move && before_move == 0u
        && CURSOR == before_cursor + 5 && *(volatile u16 *)(d + field) != 0u) {
        u8 duration = turns + (pending ? 0u : 1u);
        d[timer] = duration | (duration << 4);
    }
}

void hook_disable_v15(void) { apply((command)0x080620A9u,50u,4u,11u,4u); }
void hook_encore_v15(void) { apply((command)0x08062169u,227u,6u,14u,3u); }
