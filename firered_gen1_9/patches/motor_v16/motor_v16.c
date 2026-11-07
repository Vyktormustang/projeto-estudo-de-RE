/* v16: retirar somente a falha legada por nivel do phazing de treinador.
 * Primeiro executa o comando nativo, inclusive seu RNG. Se falhou com
 * atacante de nivel inferior, repete uma unica vez com nivel equiparado
 * temporariamente. A rotina nativa ainda exige reserva elegivel e seleciona
 * o novo membro; sem reserva, a repeticao tambem falha. Nenhum nivel/EXP
 * persistente e alterado. O nivel de batalha e restaurado antes do retorno.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define MOVE (*(volatile u16 *)0x02021586u)
#define ATK (*(volatile u8 *)0x020215A8u)
#define TGT (*(volatile u8 *)0x020215A9u)
#define COUNT (*(volatile u8 *)0x020213F4u)
#define FLAGS (*(volatile u32 *)0x02020374u)
#define CURSOR (*(const u8 *volatile *)0x020215B0u)
#define MONS ((volatile u8 *)0x02021410u)
#define PREVIOUS ((void (*)(void))0x08060DD1u)

void hook_forcerandomswitch_v16(void)
{
    u8 a = ATK, t = TGT;
    u16 move = MOVE;
    if (!(FLAGS & 8u) || a >= COUNT || t >= COUNT || a >= 4u
        || t >= 4u || a == t
        || (move != 18u && move != 46u && move != 508u && move != 521u)) {
        PREVIOUS();
        return;
    }
    volatile u8 *level = MONS + 0x5Cu*a + 0x2Cu;
    u8 before = *level, target_level = MONS[0x5Cu*t + 0x2Cu];
    if (!before || before >= target_level || target_level > 100u) {
        PREVIOUS();
        return;
    }
    const u8 *start = CURSOR;
    const u8 *failure = (const u8 *)((u32)start[1] | ((u32)start[2] << 8)
                        | ((u32)start[3] << 16) | ((u32)start[4] << 24));
    PREVIOUS();
    if (CURSOR == failure && ATK == a && TGT == t && MOVE == move
        && *level == before && MONS[0x5Cu*t + 0x2Cu] == target_level) {
        CURSOR = start;
        *level = target_level;
        PREVIOUS();
        *level = before;
    }
}
