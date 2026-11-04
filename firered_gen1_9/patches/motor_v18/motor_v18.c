/* v18: impedir self-switch de pivos de dano que falharam/nao afetaram.
 * O tail v7 ja executou moveend 0..15; terminar no estado 16, sem refazer
 * gasto de PP, historico ou efeitos. Parting Shot e Chilly Reception nao
 * passam pelo veto: Parting pode reduzir so um atributo e ainda trocar.
 * Soundproof/Parting e corrigido separadamente via lista nativa estendida.
 * Sem RAM adicional. O endereco PREVIOUS e a funcao, nao o vetor regravado.
 */
typedef unsigned char u8;
typedef unsigned short u16;
#define MOVE (*(volatile u16 *)0x02021586u)
#define RESULT (*(volatile u8 *)0x02021608u)
#define CURSOR (*(const u8 *volatile *)0x020215B0u)
#define FINISH ((const u8 *)0x081853FCu)
#define PREVIOUS ((void (*)(void))0x090C07B5u)

void hook_pivot_v18(void)
{
    u16 move = MOVE;
    if ((move == 369u || move == 517u || move == 708u)
        && (RESULT & 0x29u) != 0u) {
        CURSOR = FINISH;
        return;
    }
    PREVIOUS();
}
