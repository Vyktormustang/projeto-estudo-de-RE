/* v14: Protect/Detect nao cobram PP de continuacao Rollout/Ice Ball.
 * Sem RAM nova. Nao impede cancelamento da trava nem altera potencia.
 * O marcador so e armado no caminho que necessariamente chega a ppreduce;
 * o proprio comando nativo o consome. Demais caminhos nao recebem o bit.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define MOVE (*(volatile u16 *)0x02021586u)
#define ATTACKER (*(volatile u8 *)0x020215A8u)
#define TARGET (*(volatile u8 *)0x020215A9u)
#define COUNT (*(volatile u8 *)0x020213F4u)
#define CURSOR (*(const u8 *volatile *)0x020215B0u)
#define MONS ((volatile u8 *)0x02021410u)
#define PROTECT ((volatile u8 *)0x020216CCu)
#define RESULT (*(volatile u8 *)0x02021608u)
#define MARKER (*(volatile u32 *)0x0202160Cu)
#define MULTI 0x1000u
#define NO_PP 0x800u
#define ROLLOUT ((const u8 *)0x08186348u)
#define PREVIOUS ((void (*)(void))0x090D0019u)

void hook_attackcanceler_v14(void)
{
    u8 a = ATTACKER, t = TARGET;
    u16 move = MOVE;
    u8 continuing = CURSOR == ROLLOUT && (move == 205u || move == 301u)
        && a < 4u && t < 4u && a < COUNT && t < COUNT
        && ((*(volatile u32 *)(MONS + 0x5Cu*a + 0x54u) & MULTI) != 0u);
    PREVIOUS();
    if (continuing && CURSOR == ROLLOUT + 1 && MOVE == move
        && ATTACKER == a && TARGET == t
        && (PROTECT[16u*t] & 1u) && (RESULT & 1u)
        && ((*(volatile u32 *)(MONS + 0x5Cu*a + 0x54u) & MULTI) == 0u)) {
        /* attackstring -> jumpifstatus2 (agora falso) -> ppreduce.
         * Nao marcar continuacoes normais: elas saltam ppreduce!
         * Nao marcar sleep/flinch/confusao: esses caminhos desviam o cursor.
         */
        MARKER |= NO_PP;
    }
}
