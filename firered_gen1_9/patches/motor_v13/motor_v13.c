/* motor_v13: Eerie Spell atravessa Substitute; Shield Dust barra seu dreno.
 * Sem RAM extra. Os wrappers de comandos sao restritos ao script padrao
 * de Eerie Spell; os demais usos seguem a cadeia anterior sem alteracao.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef void (*command)(void);
#define CURRENT_MOVE (*(volatile u16 *)0x02021586u)
#define TARGET (*(volatile u8 *)0x020215A9u)
#define COUNT (*(volatile u8 *)0x020213F4u)
#define ABSENT (*(volatile u8 *)0x020215ADu)
#define CURR_INSTR (*(const u8 *volatile *)0x020215B0u)
#define MONS ((volatile u8 *)0x02021410u)
#define STATUS3 ((volatile u32 *)0x02021638u)
#define HIT_MARKER (*(volatile u32 *)0x0202160Cu)
#define IGNORE_SUB 0x00000100u
#define SUB 0x01000000u
#define PREV_ADJUST ((command)0x08058FEDu)
#define PREV_HEALTHBAR ((command)0x090C0029u)
#define PREV_DATAHP ((command)0x090D0041u)
#define PREV_POST ((command)0x090D6101u)
#define END ((const u8 *)0x081853F6u)

static u8 is_eerie_target(void)
{
    u8 b = TARGET;
    return CURRENT_MOVE == 720u && b < 4u && b < COUNT
        && (ABSENT & (1u << b)) == 0u;
}

void hook_adjust_v13(void)
{
    if (is_eerie_target() && CURR_INSTR == (const u8 *)0x090CD40Du) {
        /* adjustnormaldamage testa status2, nao HITMARKER_IGNORE_SUBSTITUTE.
         * Remocao sincronica apenas durante o calculo preserva Endure/Focus
         * Band contra dano que agora vai atingir o alvo, nao o boneco.
         * O comando nao espera controller nem agenda leitura desse status. */
        volatile u32 *status = (volatile u32 *)(MONS + 0x5Cu * TARGET + 0x54u);
        u32 sub = *status & SUB;
        *status &= ~SUB;
        PREV_ADJUST();
        *status |= sub;
    } else {
        PREV_ADJUST();
    }
}

static void with_bypass(command previous, const u8 *site)
{
    if (is_eerie_target() && CURR_INSTR == site && (HIT_MARKER & IGNORE_SUB) == 0u) {
        /* Os comandos podem estar aguardando o controller. O bit que este
         * wrapper acrescenta e removido antes de retornar, mesmo sem avancar
         * a instrucao. Nunca sobrevive entre comandos/frames/outros golpes.
         * Nao restaurar o marcador inteiro: o nativo pode mudar outros bits. */
        HIT_MARKER |= IGNORE_SUB;
        previous();
        HIT_MARKER &= ~IGNORE_SUB;
    } else {
        previous();
    }
}

void hook_healthbar_v13(void)
{
    with_bypass(PREV_HEALTHBAR, (const u8 *)0x090CD414u);
}

void hook_datahp_v13(void)
{
    with_bypass(PREV_DATAHP, (const u8 *)0x090CD416u);
}

void hook_post_hit_v13(void)
{
    if (!is_eerie_target()) {
        PREV_POST();
        return;
    }
    u8 b = TARGET;
    volatile u8 *m = MONS + 0x5Cu * b;
    /* Mesmo criterio de supressao ja usado pelo motor_v10. Nao adicionar
     * habilidades/itens modernos inexistentes (Mold Breaker/Covert Cloak). */
    if (m[0x20u] == 19u && (STATUS3[b] & 0x00010000u) == 0u) {
        CURR_INSTR = END;
        return;
    }
    /* Reutiliza integralmente o v11: ultimo golpe, limites PP, checksum,
     * controller e protecao de Transform/Mimic. O bit e ocultado apenas
     * durante essa chamada sincronica, restaurado antes do controller agir. */
    volatile u32 *status = (volatile u32 *)(m + 0x54u);
    u32 sub = *status & SUB;
    *status &= ~SUB;
    PREV_POST();
    *status |= sub;
}
