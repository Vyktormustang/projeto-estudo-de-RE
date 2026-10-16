/* C levantado mecanicamente do binario pelo modulo decompile.py.
   Sem nomes inventados e sem estruturas de alto nivel: uma instrucao
   por linha, desvios como `goto`, flags explicitas. O nome de cada
   funcao guarda o endereco de origem no binario (fn_08000258). */

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed int s32;

static inline u32 carrega32(u32 end) { return *(volatile u32 *)end; }
static inline u16 carrega16(u32 end) { return *(volatile u16 *)end; }
static inline u8 carrega8(u32 end) { return *(volatile u8 *)end; }
static inline s32 carrega16s(u32 end) { return (s32)(*(volatile short *)end); }
static inline s32 carrega8s(u32 end) { return (s32)(*(volatile signed char *)end); }
static inline void guarda32(u32 end, u32 v) { *(volatile u32 *)end = v; }
static inline void guarda16(u32 end, u16 v) { *(volatile u16 *)end = v; }
static inline void guarda8(u32 end, u8 v) { *(volatile u8 *)end = v; }

/* Deslocamentos com o comportamento exato do ARM7TDMI (inclusive os casos que
   costumam ser esquecidos: n = 0 nao mexe em C; n = 32 e n > 32 tem regra
   propria; ASR satura no sinal). */
static inline u32 sh_lsl(u32 v, u32 n, u32 *pc) {
    if (n == 0) { return v; }
    if (n < 32) { *pc = (v >> (32 - n)) & 1; return v << n; }
    if (n == 32) { *pc = v & 1; return 0; }
    *pc = 0; return 0;
}
static inline u32 sh_lsr(u32 v, u32 n, u32 *pc) {
    if (n == 0) { return v; }
    if (n < 32) { *pc = (v >> (n - 1)) & 1; return v >> n; }
    if (n == 32) { *pc = (v >> 31) & 1; return 0; }
    *pc = 0; return 0;
}
static inline u32 sh_asr(u32 v, u32 n, u32 *pc) {
    s32 s = (s32)v;
    if (n == 0) { return v; }
    if (n < 32) { *pc = ((u32)s >> (n - 1)) & 1; return (u32)(s >> n); }
    *pc = (v >> 31) & 1; return (u32)(s >> 31);
}

/* Pilha de trabalho EM MEMORIA DE VERDADE, dentro da IWRAM do GBA e longe da
   pilha do proprio harness (0x03007F00). Assim `str r0,[sp,#12]` funciona sem
   traducao especial, o transbordo de registrador para a pilha sai igual ao do
   hardware e a recursao funciona. g_erro acusa desbalanceamento na saida. */
#define PILHA_BASE 0x03005000u
#define PILHA_TOPO (PILHA_BASE + 0x800u)
static int g_erro;

__attribute__((noinline, used)) u32 fn_080000CC(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_0800020C(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_08000258(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_08000288(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_080002BE(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_080002C2(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_080002DC(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_080002E4(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_080002EE(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_08000308(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_08000320(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_08000334(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_08000340(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_08000358(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_08000366(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_0800036A(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_08000376(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_08000394(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_080003B0(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_080003C0(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_080003EC(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_08000400(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_0800040A(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 fn_08000412(u32 r0, u32 r1, u32 r2, u32 r3);

/* origem: 0x080000CC (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_080000CC(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 20;
    guarda32(sp + 0, r4);
    guarda32(sp + 4, r5);
    guarda32(sp + 8, r6);
    guarda32(sp + 12, r7);
    guarda32(sp + 16, lr);
    sp -= 44;  /* ajuste de pilha */
    r0 = 0x5u;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x080002C2 (no modulo) */
    r0 = fn_080002C2(r0, r1, r2, r3);
    guarda32((sp + 36), r0);
    r0 = 0xFFu;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x080002EE (no modulo) */
    r0 = fn_080002EE(r0, r1, r2, r3);
    guarda32((sp + 32), r0);
    r0 = 0x08000418u;  /* pool 0x080001F4 */
    r1 = 0x1u;
    z = (r1 == 0); n = (r1 >> 31);
    L_080000E4: ;
    guarda16(r0, (u16)r1);
    { u32 a_ = r0, b_ = 0x2 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    { u32 a_ = r1, b_ = 0x1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r1 = r_; }
    { u32 a_ = r1, b_ = 0x5; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (!z) goto L_080000E4;
    r0 = 0x1u;
    z = (r0 == 0); n = (r0 >> 31);
    guarda32((sp + 40), r0);
    /* bl 0x08000334 (no modulo) */
    r0 = fn_08000334(r0, r1, r2, r3);
    guarda32((sp + 20), r0);
    r0 = 0x00F0F0F0u;  /* pool 0x080001F8 */
    r4 = 0x4u;
    z = (r4 == 0); n = (r4 >> 31);
    r2 = 0xBu;
    z = (r2 == 0); n = (r2 >> 31);
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000320 (no modulo) */
    r0 = fn_08000320(r0, r1, r2, r3);
    guarda32((sp + 16), r0);
    r0 = 0xAABBCCDDu;  /* pool 0x080001FC */
    r1 = 0x11223344u;  /* pool 0x08000200 */
    /* bl 0x08000308 (no modulo) */
    r0 = fn_08000308(r0, r1, r2, r3);
    guarda32((sp + 12), r0);
    r5 = 0x9u;
    z = (r5 == 0); n = (r5 >> 31);
    guarda32((sp + 28), r5);
    r0 = r5;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x080002E4 (no modulo) */
    r0 = fn_080002E4(r0, r1, r2, r3);
    guarda32((sp + 8), r0);
    r0 = r4;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r5;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x080002DC (no modulo) */
    r0 = fn_080002DC(r0, r1, r2, r3);
    guarda32((sp + 4), r0);
    r0 = 0x7u;
    z = (r0 == 0); n = (r0 >> 31);
    guarda32((sp + 24), r0);
    r1 = 0x23u;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x080002BE (no modulo) */
    r0 = fn_080002BE(r0, r1, r2, r3);
    r7 = r0;
    z = (r7 == 0); n = (r7 >> 31);
    r6 = 0x08000418u;  /* pool 0x080001F4 */
    r0 = r6;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000340 (no modulo) */
    r0 = fn_08000340(r0, r1, r2, r3);
    r5 = r0;
    z = (r5 == 0); n = (r5 >> 31);
    r0 = r6;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000358 (no modulo) */
    r0 = fn_08000358(r0, r1, r2, r3);
    r1 = 0x0000BEEFu;  /* pool 0x08000204 */
    r0 = r6;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x08000366 (no modulo) */
    r0 = fn_08000366(r0, r1, r2, r3);
    r0 = carrega32((sp + 36));
    r1 = carrega32((sp + 32));
    { u32 a_ = r1, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    r1 = carrega32((sp + 20));
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    r1 = carrega32((sp + 16));
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    r1 = carrega32((sp + 12));
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    r1 = carrega32((sp + 8));
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    r1 = carrega32((sp + 4));
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    { u32 a_ = r0, b_ = r7 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    { u32 a_ = r0, b_ = r5 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r5 = r_; }
    r0 = r6;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x0800036A (no modulo) */
    r0 = fn_0800036A(r0, r1, r2, r3);
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r5 = r_; }
    r0 = 0x96u;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x08000376 (no modulo) */
    r0 = fn_08000376(r0, r1, r2, r3);
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r7 = r_; }
    r5 = 0x5u;
    z = (r5 == 0); n = (r5 >> 31);
    r1 = 0x3u;
    z = (r1 == 0); n = (r1 >> 31);
    guarda32((sp + 36), r1);
    r0 = r5;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x08000394 (no modulo) */
    r0 = fn_08000394(r0, r1, r2, r3);
    { u32 a_ = r7, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r7 = r_; }
    r0 = carrega32((sp + 40));
    /* bl 0x080003B0 (no modulo) */
    r0 = fn_080003B0(r0, r1, r2, r3);
    { u32 a_ = r7, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r7 = r_; }
    r0 = r5;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x080003C0 (no modulo) */
    r0 = fn_080003C0(r0, r1, r2, r3);
    { u32 a_ = r7, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r5 = r_; }
    r0 = 0x64u;
    z = (r0 == 0); n = (r0 >> 31);
    r6 = carrega32((sp + 24));
    r1 = r6;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x080003EC (no modulo) */
    r0 = fn_080003EC(r0, r1, r2, r3);
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r5 = r_; }
    r7 = carrega32((sp + 28));
    r0 = r7;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000400 (no modulo) */
    r0 = fn_08000400(r0, r1, r2, r3);
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r5 = r_; }
    r4 = 0x0u;
    z = (r4 == 0); n = (r4 >> 31);
    r0 = r4;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r6;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x0800040A (no modulo) */
    r0 = fn_0800040A(r0, r1, r2, r3);
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r5 = r_; }
    r0 = carrega32((sp + 36));
    r1 = r7;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000412 (no modulo) */
    r0 = fn_08000412(r0, r1, r2, r3);
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r6 = r_; }
    r0 = 0x7Du;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x3, &c_);
      c = c_; r5 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r0 = r5;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r5;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000258 (no modulo) */
    r0 = fn_08000258(r0, r1, r2, r3);
    r7 = 0x0000FFFFu;  /* pool 0x08000208 */
    r0 = r0 & r7;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 a_ = r6, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r6 = r_; }
    r0 = r5;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    r2 = r5;
    z = (r2 == 0); n = (r2 >> 31);
    r3 = r4;
    z = (r3 == 0); n = (r3 >> 31);
    /* bl 0x08000288 (no modulo) */
    r0 = fn_08000288(r0, r1, r2, r3);
    r0 = r0 & r7;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 a_ = r6, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    sp += 44;  /* ajuste de pilha */
    r4 = carrega32(sp + 0);
    r5 = carrega32(sp + 4);
    r6 = carrega32(sp + 8);
    r7 = carrega32(sp + 12);
    sp += 16;
    r1 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x0800020C (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_0800020C(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 20;
    guarda32(sp + 0, r4);
    guarda32(sp + 4, r5);
    guarda32(sp + 8, r6);
    guarda32(sp + 12, r7);
    guarda32(sp + 16, lr);
    sp -= 4;  /* ajuste de pilha */
    guarda32(sp, r0);
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 a_ = r1, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (z) goto L_0800024A;
    r4 = 0x1Fu;
    z = (r4 == 0); n = (r4 >> 31);
    r5 = 0x1u;
    z = (r5 == 0); n = (r5 >> 31);
    r6 = r0;
    z = (r6 == 0); n = (r6 >> 31);
    r2 = r0;
    z = (r2 == 0); n = (r2 >> 31);
    L_08000220: ;
    r7 = r5;
    z = (r7 == 0); n = (r7 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsl(r7, (r4 & 0xFFu), &c_);
      c = c_; r7 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r3 = carrega32(sp);
    { u32 c_ = c; u32 r_ = sh_lsr(r3, (r4 & 0xFFu), &c_);
      c = c_; r3 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r3 = r3 & r5;
    z = (r3 == 0); n = (r3 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsl(r6, 0x1, &c_);
      c = c_; r6 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r3, b_ = r6 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r6 = r_; }
    { u32 a_ = r6, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r3 = r_; }
    { u32 a_ = r6, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (!c) goto L_08000238;
    ip = r3;
    r6 = ip;
    L_08000238: ;
    ip = r0;
    r3 = ip;
    if (!c) goto L_08000240;
    r3 = r7;
    z = (r3 == 0); n = (r3 >> 31);
    L_08000240: ;
    r2 = r2 | r3;
    z = (r2 == 0); n = (r2 >> 31);
    { u32 a_ = r4, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r4 = r_; }
    { u32 a_ = r4, b_ = 0x1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r3 = r_; }
    if (!c) goto L_08000220;
    goto L_0800024C;
    L_0800024A: ;
    r2 = ~r0;
    z = (r2 == 0); n = (r2 >> 31);
    L_0800024C: ;
    r0 = r2;
    z = (r0 == 0); n = (r0 >> 31);
    sp += 4;  /* ajuste de pilha */
    r4 = carrega32(sp + 0);
    r5 = carrega32(sp + 4);
    r6 = carrega32(sp + 8);
    r7 = carrega32(sp + 12);
    sp += 16;
    r1 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000258 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_08000258(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 16;
    guarda32(sp + 0, r4);
    guarda32(sp + 4, r5);
    guarda32(sp + 8, r7);
    guarda32(sp + 12, lr);
    r2 = r1;
    z = (r2 == 0); n = (r2 >> 31);
    r3 = 0x0000FFFFu;  /* pool 0x08000284 */
    { u32 c_ = c; u32 r_ = sh_lsr(r1, 0x10, &c_);
      c = c_; r4 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r2 = r2 & r3;
    z = (r2 == 0); n = (r2 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x10, &c_);
      c = c_; r1 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r5 = r1;
    z = (r5 == 0); n = (r5 >> 31);
    r5 = r5 * r2;
    z = (r5 == 0); n = (r5 >> 31);
    r0 = r0 & r3;
    z = (r0 == 0); n = (r0 >> 31);
    r3 = r0;
    z = (r3 == 0); n = (r3 >> 31);
    r3 = r3 * r4;
    z = (r3 == 0); n = (r3 >> 31);
    { u32 a_ = r3, b_ = r5 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r3 = r_; }
    { u32 c_ = c; u32 r_ = sh_lsr(r3, 0x10, &c_);
      c = c_; r5 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r0 = r0 * r2;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsl(r3, 0x10, &c_);
      c = c_; r2 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r1 = r1 * r4;
    z = (r1 == 0); n = (r1 >> 31);
    { u32 a_ = r0, b_ = r2 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    { u32 a_ = r1, b_ = r5 + c; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r1 = r_; }
    r4 = carrega32(sp + 0);
    r5 = carrega32(sp + 4);
    r7 = carrega32(sp + 8);
    sp += 12;
    r2 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000288 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_08000288(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 20;
    guarda32(sp + 0, r4);
    guarda32(sp + 4, r5);
    guarda32(sp + 8, r6);
    guarda32(sp + 12, r7);
    guarda32(sp + 16, lr);
    sp -= 12;  /* ajuste de pilha */
    r5 = r3;
    z = (r5 == 0); n = (r5 >> 31);
    r4 = r2;
    z = (r4 == 0); n = (r4 >> 31);
    guarda32((sp + 8), r1);
    r7 = r0;
    z = (r7 == 0); n = (r7 >> 31);
    r1 = r2;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000258 (no modulo) */
    r0 = fn_08000258(r0, r1, r2, r3);
    guarda32((sp + 4), r0);
    r6 = r1;
    z = (r6 == 0); n = (r6 >> 31);
    r0 = r7;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r5;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000258 (no modulo) */
    r0 = fn_08000258(r0, r1, r2, r3);
    r5 = r0;
    z = (r5 == 0); n = (r5 >> 31);
    r0 = carrega32((sp + 8));
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000258 (no modulo) */
    r0 = fn_08000258(r0, r1, r2, r3);
    { u32 a_ = r0, b_ = r5 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    { u32 a_ = r0, b_ = r6 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r1 = r_; }
    r0 = carrega32((sp + 4));
    sp += 12;  /* ajuste de pilha */
    r4 = carrega32(sp + 0);
    r5 = carrega32(sp + 4);
    r6 = carrega32(sp + 8);
    r7 = carrega32(sp + 12);
    sp += 16;
    r2 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x080002BE (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_080002BE(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r1, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x080002C2 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_080002C2(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = 0x2; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((n != v)) goto L_080002D8;
    r1 = r0;
    z = (r1 == 0); n = (r1 >> 31);
    r0 = 0x1u;
    z = (r0 == 0); n = (r0 >> 31);
    L_080002CA: ;
    r0 = r0 * r1;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 a_ = r1, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r2 = r_; }
    { u32 a_ = r1, b_ = 0x2; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    ip = r2;
    r1 = ip;
    if ((c && !z)) goto L_080002CA;
    return r0;
    L_080002D8: ;
    r0 = 0x1u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x080002DC (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_080002DC(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((!z && (n == v))) goto L_080002E2;
    r0 = r1;
    z = (r0 == 0); n = (r0 >> 31);
    L_080002E2: ;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x080002E4 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_080002E4(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    { u32 c_ = c; u32 r_ = sh_asr(r0, 0x1f, &c_);
      c = c_; r1 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r0 = r0 ^ r1;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 a_ = r0, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x080002EE (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_080002EE(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (z) goto L_08000304;
    r1 = r0;
    z = (r1 == 0); n = (r1 >> 31);
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    r2 = 0x1u;
    z = (r2 == 0); n = (r2 >> 31);
    L_080002F8: ;
    r3 = r1;
    z = (r3 == 0); n = (r3 >> 31);
    r3 = r3 & r2;
    z = (r3 == 0); n = (r3 >> 31);
    { u32 a_ = r0, b_ = r3 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    { u32 c_ = c; u32 r_ = sh_lsr(r1, 0x1, &c_);
      c = c_; r1 = r_; z = (r_ == 0); n = (r_ >> 31); }
    if (!z) goto L_080002F8;
    return r0;
    L_08000304: ;
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000308 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_08000308(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    r2 = 0xFF00FF00u;  /* pool 0x08000318 */
    r2 = r2 & r0;
    z = (r2 == 0); n = (r2 >> 31);
    r3 = 0x00FF00FFu;  /* pool 0x0800031C */
    r3 = r3 & r1;
    z = (r3 == 0); n = (r3 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x8, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r0 = r0 ^ r3;
    z = (r0 == 0); n = (r0 >> 31);
    r0 = r0 | r2;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000320 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_08000320(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r2, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r2 = r_; }
    { u32 a_ = r2, b_ = 0x1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r2 = r_; }
    r3 = 0x0u;
    z = (r3 == 0); n = (r3 >> 31);
    r3 = ~r3;
    z = (r3 == 0); n = (r3 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsl(r3, (r2 & 0xFFu), &c_);
      c = c_; r3 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r2 = ~r3;
    z = (r2 == 0); n = (r2 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsl(r2, (r1 & 0xFFu), &c_);
      c = c_; r2 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r0 = r0 & r2;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsr(r0, (r1 & 0xFFu), &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000334 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_08000334(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    r1 = 0x0001D207u;  /* pool 0x0800033C */
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000340 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_08000340(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r1, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((n != v)) goto L_08000354;
    r2 = r0;
    z = (r2 == 0); n = (r2 >> 31);
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    L_08000348: ;
    r3 = carrega16(r2);
    { u32 a_ = r0, b_ = r3 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    { u32 a_ = r2, b_ = 0x2 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r2 = r_; }
    { u32 a_ = r1, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r1 = r_; }
    if (!z) goto L_08000348;
    return r0;
    L_08000354: ;
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000358 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_08000358(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r1, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((n != v)) goto L_08000364;
    r2 = 0x0u;
    z = (r2 == 0); n = (r2 >> 31);
    L_0800035E: ;
    guarda32((r0 + 0), r2);
    r0 += 4;  /* writeback */
    { u32 a_ = r1, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r1 = r_; }
    if (!z) goto L_0800035E;
    L_08000364: ;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000366 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_08000366(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    guarda16(r0, (u16)r1);
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x0800036A (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_0800036A(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    r1 = carrega32((r0 + 16));
    r2 = 0x3u;
    z = (r2 == 0); n = (r2 >> 31);
    r2 = r2 * r1;
    z = (r2 == 0); n = (r2 >> 31);
    r0 = carrega32((r0 + 4));
    { u32 a_ = r2, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000376 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_08000376(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = 0xa; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((n == v)) goto L_0800037E;
    r0 = 0x1u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    L_0800037E: ;
    { u32 a_ = r0, b_ = 0x64; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (c) goto L_08000386;
    r0 = 0x2u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    L_08000386: ;
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x3, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r0, b_ = 0x7d; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (!c) goto L_08000390;
    r0 = 0x4u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    L_08000390: ;
    r0 = 0x3u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000394 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_08000394(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((n != v)) goto L_080003A0;
    { u32 a_ = r1, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((n != v)) goto L_080003A8;
    { u32 a_ = r1, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    return r0;
    L_080003A0: ;
    { u32 a_ = r1, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((!z && (n == v))) goto L_080003AC;
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    L_080003A8: ;
    { u32 a_ = r0, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    return r0;
    L_080003AC: ;
    { u32 a_ = r1, b_ = r0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x080003B0 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_080003B0(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 8;
    guarda32(sp + 0, r7);
    guarda32(sp + 4, lr);
    r1 = 0x64u;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x080002BE (no modulo) */
    r0 = fn_080002BE(r0, r1, r2, r3);
    { u32 a_ = r0, b_ = 0x1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    r7 = carrega32(sp + 0);
    sp += 4;
    r1 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x080003C0 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_080003C0(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 16;
    guarda32(sp + 0, r4);
    guarda32(sp + 4, r5);
    guarda32(sp + 8, r7);
    guarda32(sp + 12, lr);
    { u32 a_ = r0, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((n != v)) goto L_080003E4;
    r4 = r0;
    z = (r4 == 0); n = (r4 >> 31);
    { u32 a_ = r0, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r5 = r_; }
    { u32 a_ = r0, b_ = 0x2; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r2 = r_; }
    r1 = 0x0u;
    z = (r1 == 0); n = (r1 >> 31);
    r0 = r5;
    z = (r0 == 0); n = (r0 >> 31);
    r3 = r1;
    z = (r3 == 0); n = (r3 >> 31);
    /* bl 0x08000288 (no modulo) */
    r0 = fn_08000288(r0, r1, r2, r3);
    { u32 c_ = c; u32 r_ = sh_lsl(r1, 0x1f, &c_);
      c = c_; r1 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x1, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    r5 = r5 * r5;
    z = (r5 == 0); n = (r5 >> 31);
    { u32 a_ = r4, b_ = r5 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r1 = r_; }
    { u32 a_ = r1, b_ = r0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    goto L_080003E6;
    L_080003E4: ;
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    L_080003E6: ;
    r4 = carrega32(sp + 0);
    r5 = carrega32(sp + 4);
    r7 = carrega32(sp + 8);
    sp += 12;
    r1 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x080003EC (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_080003EC(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 8;
    guarda32(sp + 0, r7);
    guarda32(sp + 4, lr);
    { u32 a_ = r1, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (z) goto L_080003F8;
    /* bl 0x0800020C (no modulo) */
    r0 = fn_0800020C(r0, r1, r2, r3);
    goto L_080003FA;
    L_080003F8: ;
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    L_080003FA: ;
    r7 = carrega32(sp + 0);
    sp += 4;
    r1 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000400 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_08000400(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    { u32 c_ = c; u32 r_ = sh_asr(r0, 0x1f, &c_);
      c = c_; r1 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r0 = r0 ^ r1;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 a_ = r0, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x0800040A (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_0800040A(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    r2 = 0x1u;
    z = (r2 == 0); n = (r2 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsl(r2, (r1 & 0xFFu), &c_);
      c = c_; r2 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r0 = r0 | r2;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000412 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 fn_08000412(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, ip = 0, lr = 0;
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r1, b_ = r0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}
