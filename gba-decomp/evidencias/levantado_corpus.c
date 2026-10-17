/* C levantado mecanicamente do binario pelo modulo decompile.py.
   Sem nomes inventados e sem estruturas de alto nivel: uma instrucao
   por linha, desvios como `goto`, flags explicitas. O nome de cada
   funcao guarda o endereco de origem no binario (fn_08000258). */

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed int s32;
typedef unsigned long long u64;

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
static inline u32 sh_ror(u32 v, u32 n, u32 *pc) {
    if (n == 0) { return v; }
    n &= 31;
    if (n == 0) { *pc = (v >> 31) & 1; return v; }   /* 32 volta no mesmo lugar */
    { u32 r = (v >> n) | (v << (32 - n)); *pc = (r >> 31) & 1; return r; }
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
/* Fronteira de BIOS: SWI/SVC nao e codigo do jogo, e chamada ao firmware do
   GBA. Fica declarada e NAO definida de proposito -- o link acusa onde a
   traducao para no limite da BIOS, em vez de inventar o que ela faz. */
u32 bios_svc(u32 numero, u32 r0, u32 r1, u32 r2, u32 r3);

#define PILHA_BASE 0x03005000u
#define PILHA_TOPO (PILHA_BASE + 0x800u)
static int g_erro;

__attribute__((noinline, used)) u32 f_main_teste(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f___aeabi_uidiv(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_mul32(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f___aeabi_lmul(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_soma(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_fat(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_maximo(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_abs_dif(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_conta_bits(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_mistura(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_mascara(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_soma_const(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_soma_vetor(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_limpa(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_escreve_u16(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_campo_offsets(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_classifica(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_if_aninhado(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_chama_soma(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_loop_decrescente(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_divide(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_ternario(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_poe_bit(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_troca(u32 r0, u32 r1, u32 r2, u32 r3);
__attribute__((noinline, used)) u32 f_distancia_adr(u32 r0, u32 r1, u32 r2, u32 r3);

/* origem: 0x080000CC (thumb), semente: vetor de boot, pilha: balanceada */
__attribute__((noinline, used)) u32 f_main_teste(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
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
    /* bl 0x080002CA (no modulo) */
    r0 = f_fat(r0, r1, r2, r3);
    guarda32(sp + 0x24, r0);
    r0 = 0xFFu;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x080002F6 (no modulo) */
    r0 = f_conta_bits(r0, r1, r2, r3);
    guarda32(sp + 0x20, r0);
    r0 = 0x08000430u;  /* pool 0x080001FC */
    r1 = 0x1u;
    z = (r1 == 0); n = (r1 >> 31);
    L_080000E4: ;
    guarda16(r0, (u16)r1);
    { u32 a_ = r0, b_ = 0x2 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r1, b_ = 0x1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r1 = r_; }
    { u32 a_ = r1, b_ = 0x5; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r1 != 0x5) goto L_080000E4;
    r0 = 0x1u;
    z = (r0 == 0); n = (r0 >> 31);
    guarda32(sp + 0x28, r0);
    /* bl 0x0800033C (no modulo) */
    r0 = f_soma_const(r0, r1, r2, r3);
    guarda32(sp + 0x14, r0);
    r0 = 0x00F0F0F0u;  /* pool 0x08000200 */
    r4 = 0x4u;
    z = (r4 == 0); n = (r4 >> 31);
    r2 = 0xBu;
    z = (r2 == 0); n = (r2 >> 31);
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000328 (no modulo) */
    r0 = f_mascara(r0, r1, r2, r3);
    guarda32(sp + 0x10, r0);
    r0 = 0xAABBCCDDu;  /* pool 0x08000204 */
    r1 = 0x11223344u;  /* pool 0x08000208 */
    /* bl 0x08000310 (no modulo) */
    r0 = f_mistura(r0, r1, r2, r3);
    guarda32(sp + 0xc, r0);
    r5 = 0x9u;
    z = (r5 == 0); n = (r5 >> 31);
    guarda32(sp + 0x1c, r5);
    r0 = r5;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x080002EC (no modulo) */
    r0 = f_abs_dif(r0, r1, r2, r3);
    guarda32(sp + 0x8, r0);
    r0 = r4;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r5;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x080002E4 (no modulo) */
    r0 = f_maximo(r0, r1, r2, r3);
    guarda32(sp + 0x4, r0);
    r0 = 0x7u;
    z = (r0 == 0); n = (r0 >> 31);
    guarda32(sp + 0x18, r0);
    r1 = 0x23u;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x080002C6 (no modulo) */
    r0 = f_soma(r0, r1, r2, r3);
    r7 = r0;
    z = (r7 == 0); n = (r7 >> 31);
    r6 = 0x08000430u;  /* pool 0x080001FC */
    r0 = r6;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000348 (no modulo) */
    r0 = f_soma_vetor(r0, r1, r2, r3);
    r5 = r0;
    z = (r5 == 0); n = (r5 >> 31);
    r0 = r6;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000360 (no modulo) */
    r0 = f_limpa(r0, r1, r2, r3);
    r1 = 0x0000BEEFu;  /* pool 0x0800020C */
    r0 = r6;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x0800036E (no modulo) */
    r0 = f_escreve_u16(r0, r1, r2, r3);
    r0 = carrega32(sp + 0x24);
    r1 = carrega32(sp + 0x20);
    { u32 a_ = r1, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r1 = carrega32(sp + 0x14);
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r1 = carrega32(sp + 0x10);
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r1 = carrega32(sp + 0xc);
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r1 = carrega32(sp + 0x8);
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r1 = carrega32(sp + 0x4);
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = r7 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = r5 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r5 = r_; }
    r0 = r6;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x08000372 (no modulo) */
    r0 = f_campo_offsets(r0, r1, r2, r3);
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r5 = r_; }
    r0 = 0x96u;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x0800037E (no modulo) */
    r0 = f_classifica(r0, r1, r2, r3);
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r7 = r_; }
    r5 = 0x5u;
    z = (r5 == 0); n = (r5 >> 31);
    r1 = 0x3u;
    z = (r1 == 0); n = (r1 >> 31);
    guarda32(sp + 0x24, r1);
    r0 = r5;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x0800039C (no modulo) */
    r0 = f_if_aninhado(r0, r1, r2, r3);
    { u32 a_ = r7, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r7 = r_; }
    r0 = carrega32(sp + 0x28);
    /* bl 0x080003B8 (no modulo) */
    r0 = f_chama_soma(r0, r1, r2, r3);
    { u32 a_ = r7, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r7 = r_; }
    r0 = r5;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x080003C8 (no modulo) */
    r0 = f_loop_decrescente(r0, r1, r2, r3);
    { u32 a_ = r7, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r5 = r_; }
    r0 = 0x64u;
    z = (r0 == 0); n = (r0 >> 31);
    r6 = carrega32(sp + 0x18);
    r1 = r6;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x080003F4 (no modulo) */
    r0 = f_divide(r0, r1, r2, r3);
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r5 = r_; }
    r7 = carrega32(sp + 0x1c);
    r0 = r7;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000408 (no modulo) */
    r0 = f_ternario(r0, r1, r2, r3);
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r5 = r_; }
    r4 = 0x0u;
    z = (r4 == 0); n = (r4 >> 31);
    r0 = r4;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r6;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000412 (no modulo) */
    r0 = f_poe_bit(r0, r1, r2, r3);
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r5 = r_; }
    r0 = carrega32(sp + 0x24);
    r1 = r7;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x0800041A (no modulo) */
    r0 = f_troca(r0, r1, r2, r3);
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r5 = r_; }
    /* bl 0x0800041E (no modulo) */
    r0 = f_distancia_adr(r0, r1, r2, r3);
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r6 = r_; }
    r0 = 0x7Du;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x3, &c_);
      c = c_; r5 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r0 = r5;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r5;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000260 (no modulo) */
    r0 = f_mul32(r0, r1, r2, r3);
    r7 = 0x0000FFFFu;  /* pool 0x08000210 */
    r0 = r0 & r7;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 a_ = r6, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r6 = r_; }
    r0 = r5;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    r2 = r5;
    z = (r2 == 0); n = (r2 >> 31);
    r3 = r4;
    z = (r3 == 0); n = (r3 >> 31);
    /* bl 0x08000290 (no modulo) */
    r0 = f___aeabi_lmul(r0, r1, r2, r3);
    r0 = r0 & r7;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 a_ = r6, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
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

/* chamada por 1: f_divide */
/* origem: 0x08000214 (thumb), semente: chamada (bl) em 0x080003FA, pilha: balanceada */
__attribute__((noinline, used)) u32 f___aeabi_uidiv(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
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
    if (r1 == 0x0) goto L_08000252;
    r4 = 0x1Fu;
    z = (r4 == 0); n = (r4 >> 31);
    r5 = 0x1u;
    z = (r5 == 0); n = (r5 >> 31);
    r6 = r0;
    z = (r6 == 0); n = (r6 >> 31);
    r2 = r0;
    z = (r2 == 0); n = (r2 >> 31);
    L_08000228: ;
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
      z = (r_ == 0); n = (r_ >> 31);
      r6 = r_; }
    { u32 a_ = r6, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r3 = r_; }
    { u32 a_ = r6, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r6 < r1) goto L_08000240;
    r12 = r3;
    r6 = r12;
    L_08000240: ;
    r12 = r0;
    r3 = r12;
    if (!c) goto L_08000248;
    r3 = r7;
    z = (r3 == 0); n = (r3 >> 31);
    L_08000248: ;
    r2 = r2 | r3;
    z = (r2 == 0); n = (r2 >> 31);
    { u32 a_ = r4, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r4 = r_; }
    { u32 a_ = r4, b_ = 0x1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r3 = r_; }
    if (!c) goto L_08000228;
    goto L_08000254;
    L_08000252: ;
    r2 = ~r0;
    z = (r2 == 0); n = (r2 >> 31);
    L_08000254: ;
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

/* chamada por 2: f___aeabi_lmul, f_main_teste */
/* origem: 0x08000260 (thumb), semente: chamada (bl) em 0x080001D8, pilha: balanceada */
__attribute__((noinline, used)) u32 f_mul32(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
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
    r3 = 0x0000FFFFu;  /* pool 0x0800028C */
    { u32 c_ = c; u32 r_ = sh_lsr(r1, 0x10, &c_);
      c = c_; r4 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r2 = r2 & r3;
    z = (r2 == 0); n = (r2 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x10, &c_);
      c = c_; r1 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r5 = r1;
    z = (r5 == 0); n = (r5 >> 31);
    r5 = r2 * r5;
    z = (r5 == 0); n = (r5 >> 31);
    r0 = r0 & r3;
    z = (r0 == 0); n = (r0 >> 31);
    r3 = r0;
    z = (r3 == 0); n = (r3 >> 31);
    r3 = r4 * r3;
    z = (r3 == 0); n = (r3 >> 31);
    { u32 a_ = r3, b_ = r5 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r3 = r_; }
    { u32 c_ = c; u32 r_ = sh_lsr(r3, 0x10, &c_);
      c = c_; r5 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r0 = r2 * r0;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsl(r3, 0x10, &c_);
      c = c_; r2 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r1 = r4 * r1;
    z = (r1 == 0); n = (r1 >> 31);
    { u32 a_ = r0, b_ = r2 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r1, b_ = r5 + c; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r1 = r_; }
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

/* chamada por 2: f_loop_decrescente, f_main_teste */
/* origem: 0x08000290 (thumb), semente: chamada (bl) em 0x080001EA, pilha: balanceada */
__attribute__((noinline, used)) u32 f___aeabi_lmul(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
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
    guarda32(sp + 0x8, r1);
    r7 = r0;
    z = (r7 == 0); n = (r7 >> 31);
    r1 = r2;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000260 (no modulo) */
    r0 = f_mul32(r0, r1, r2, r3);
    guarda32(sp + 0x4, r0);
    r6 = r1;
    z = (r6 == 0); n = (r6 >> 31);
    r0 = r7;
    z = (r0 == 0); n = (r0 >> 31);
    r1 = r5;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000260 (no modulo) */
    r0 = f_mul32(r0, r1, r2, r3);
    r5 = r0;
    z = (r5 == 0); n = (r5 >> 31);
    r0 = carrega32(sp + 0x8);
    r1 = r4;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08000260 (no modulo) */
    r0 = f_mul32(r0, r1, r2, r3);
    { u32 a_ = r0, b_ = r5 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = r6 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r1 = r_; }
    r0 = carrega32(sp + 0x4);
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

/* chamada por 2: f_chama_soma, f_main_teste */
/* origem: 0x080002C6 (thumb), semente: chamada (bl) em 0x0800012E, pilha: balanceada */
__attribute__((noinline, used)) u32 f_soma(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r1, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x080002CA (thumb), semente: chamada (bl) em 0x080000D2, pilha: balanceada */
__attribute__((noinline, used)) u32 f_fat(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = 0x2; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((s32)r0 < (s32)0x2) goto L_080002E0;
    r1 = r0;
    z = (r1 == 0); n = (r1 >> 31);
    r0 = 0x1u;
    z = (r0 == 0); n = (r0 >> 31);
    L_080002D2: ;
    r0 = r1 * r0;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 a_ = r1, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r2 = r_; }
    { u32 a_ = r1, b_ = 0x2; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    r12 = r2;
    r1 = r12;
    if ((c && !z)) goto L_080002D2;
    return r0;
    L_080002E0: ;
    r0 = 0x1u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x080002E4 (thumb), semente: chamada (bl) em 0x08000122, pilha: balanceada */
__attribute__((noinline, used)) u32 f_maximo(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((s32)r0 > (s32)r1) goto L_080002EA;
    r0 = r1;
    z = (r0 == 0); n = (r0 >> 31);
    L_080002EA: ;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x080002EC (thumb), semente: chamada (bl) em 0x08000118, pilha: balanceada */
__attribute__((noinline, used)) u32 f_abs_dif(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 c_ = c; u32 r_ = sh_asr(r0, 0x1f, &c_);
      c = c_; r1 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r0 = r0 ^ r1;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 a_ = r0, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x080002F6 (thumb), semente: chamada (bl) em 0x080000DA, pilha: balanceada */
__attribute__((noinline, used)) u32 f_conta_bits(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 == 0x0) goto L_0800030C;
    r1 = r0;
    z = (r1 == 0); n = (r1 >> 31);
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    r2 = 0x1u;
    z = (r2 == 0); n = (r2 >> 31);
    L_08000300: ;
    r3 = r1;
    z = (r3 == 0); n = (r3 >> 31);
    r3 = r3 & r2;
    z = (r3 == 0); n = (r3 >> 31);
    { u32 a_ = r0, b_ = r3 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 c_ = c; u32 r_ = sh_lsr(r1, 0x1, &c_);
      c = c_; r1 = r_; z = (r_ == 0); n = (r_ >> 31); }
    if (!z) goto L_08000300;
    return r0;
    L_0800030C: ;
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x08000310 (thumb), semente: chamada (bl) em 0x0800010A, pilha: balanceada */
__attribute__((noinline, used)) u32 f_mistura(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    r2 = 0xFF00FF00u;  /* pool 0x08000320 */
    r2 = r2 & r0;
    z = (r2 == 0); n = (r2 >> 31);
    r3 = 0x00FF00FFu;  /* pool 0x08000324 */
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

/* chamada por 1: f_main_teste */
/* origem: 0x08000328 (thumb), semente: chamada (bl) em 0x08000100, pilha: balanceada */
__attribute__((noinline, used)) u32 f_mascara(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r2, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r2 = r_; }
    { u32 a_ = r2, b_ = 0x1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r2 = r_; }
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

/* chamada por 1: f_main_teste */
/* origem: 0x0800033C (thumb), semente: chamada (bl) em 0x080000F2, pilha: balanceada */
__attribute__((noinline, used)) u32 f_soma_const(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    r1 = 0x0001D207u;  /* pool 0x08000344 */
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x08000348 (thumb), semente: chamada (bl) em 0x0800013A, pilha: balanceada */
__attribute__((noinline, used)) u32 f_soma_vetor(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r1, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((s32)r1 < (s32)0x1) goto L_0800035C;
    r2 = r0;
    z = (r2 == 0); n = (r2 >> 31);
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    L_08000350: ;
    r3 = carrega16(r2);
    { u32 a_ = r0, b_ = r3 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r2, b_ = 0x2 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r2 = r_; }
    { u32 a_ = r1, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r1 = r_; }
    if (!z) goto L_08000350;
    return r0;
    L_0800035C: ;
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x08000360 (thumb), semente: chamada (bl) em 0x08000144, pilha: balanceada */
__attribute__((noinline, used)) u32 f_limpa(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r1, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((s32)r1 < (s32)0x1) goto L_0800036C;
    r2 = 0x0u;
    z = (r2 == 0); n = (r2 >> 31);
    L_08000366: ;
    { u32 base_ = r0;
        guarda32(base_ + 0, r2);
        r0 = base_ + 4;  /* writeback */
    }
    { u32 a_ = r1, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r1 = r_; }
    if (!z) goto L_08000366;
    L_0800036C: ;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x0800036E (thumb), semente: chamada (bl) em 0x0800014C, pilha: balanceada */
__attribute__((noinline, used)) u32 f_escreve_u16(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    guarda16(r0, (u16)r1);
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x08000372 (thumb), semente: chamada (bl) em 0x08000170, pilha: balanceada */
__attribute__((noinline, used)) u32 f_campo_offsets(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    r1 = carrega32(r0 + 0x10);
    r2 = 0x3u;
    z = (r2 == 0); n = (r2 >> 31);
    r2 = r1 * r2;
    z = (r2 == 0); n = (r2 >> 31);
    r0 = carrega32(r0 + 0x4);
    { u32 a_ = r2, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x0800037E (thumb), semente: chamada (bl) em 0x08000178, pilha: balanceada */
__attribute__((noinline, used)) u32 f_classifica(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = 0xa; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((s32)r0 >= (s32)0xa) goto L_08000386;
    r0 = 0x1u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    L_08000386: ;
    { u32 a_ = r0, b_ = 0x64; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 >= 0x64) goto L_0800038E;
    r0 = 0x2u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    L_0800038E: ;
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x3, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r0, b_ = 0x7d; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 < 0x7d) goto L_08000398;
    r0 = 0x4u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    L_08000398: ;
    r0 = 0x3u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x0800039C (thumb), semente: chamada (bl) em 0x08000186, pilha: balanceada */
__attribute__((noinline, used)) u32 f_if_aninhado(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((s32)r0 < (s32)0x1) goto L_080003A8;
    { u32 a_ = r1, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((s32)r1 < (s32)0x1) goto L_080003B0;
    { u32 a_ = r1, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    return r0;
    L_080003A8: ;
    { u32 a_ = r1, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((s32)r1 > (s32)0x0) goto L_080003B4;
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    return r0;
    L_080003B0: ;
    { u32 a_ = r0, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    return r0;
    L_080003B4: ;
    { u32 a_ = r1, b_ = r0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x080003B8 (thumb), semente: chamada (bl) em 0x0800018E, pilha: balanceada */
__attribute__((noinline, used)) u32 f_chama_soma(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 8;
    guarda32(sp + 0, r7);
    guarda32(sp + 4, lr);
    r1 = 0x64u;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x080002C6 (no modulo) */
    r0 = f_soma(r0, r1, r2, r3);
    { u32 a_ = r0, b_ = 0x1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r7 = carrega32(sp + 0);
    sp += 4;
    r1 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x080003C8 (thumb), semente: chamada (bl) em 0x08000196, pilha: balanceada */
__attribute__((noinline, used)) u32 f_loop_decrescente(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
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
    if ((s32)r0 < (s32)0x1) goto L_080003EC;
    r4 = r0;
    z = (r4 == 0); n = (r4 >> 31);
    { u32 a_ = r0, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r5 = r_; }
    { u32 a_ = r0, b_ = 0x2; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r2 = r_; }
    r1 = 0x0u;
    z = (r1 == 0); n = (r1 >> 31);
    r0 = r5;
    z = (r0 == 0); n = (r0 >> 31);
    r3 = r1;
    z = (r3 == 0); n = (r3 >> 31);
    /* bl 0x08000290 (no modulo) */
    r0 = f___aeabi_lmul(r0, r1, r2, r3);
    { u32 c_ = c; u32 r_ = sh_lsl(r1, 0x1f, &c_);
      c = c_; r1 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x1, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r5 = r5 * r5;
    z = (r5 == 0); n = (r5 >> 31);
    { u32 a_ = r4, b_ = r5 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r1 = r_; }
    { u32 a_ = r1, b_ = r0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    goto L_080003EE;
    L_080003EC: ;
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    L_080003EE: ;
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

/* chamada por 1: f_main_teste */
/* origem: 0x080003F4 (thumb), semente: chamada (bl) em 0x080001A2, pilha: balanceada */
__attribute__((noinline, used)) u32 f_divide(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 8;
    guarda32(sp + 0, r7);
    guarda32(sp + 4, lr);
    { u32 a_ = r1, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r1 == 0x0) goto L_08000400;
    /* bl 0x08000214 (no modulo) */
    r0 = f___aeabi_uidiv(r0, r1, r2, r3);
    goto L_08000402;
    L_08000400: ;
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    L_08000402: ;
    r7 = carrega32(sp + 0);
    sp += 4;
    r1 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x08000408 (thumb), semente: chamada (bl) em 0x080001AE, pilha: balanceada */
__attribute__((noinline, used)) u32 f_ternario(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r0, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 c_ = c; u32 r_ = sh_asr(r0, 0x1f, &c_);
      c = c_; r1 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r0 = r0 ^ r1;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 a_ = r0, b_ = r1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x08000412 (thumb), semente: chamada (bl) em 0x080001BA, pilha: balanceada */
__attribute__((noinline, used)) u32 f_poe_bit(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
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

/* chamada por 1: f_main_teste */
/* origem: 0x0800041A (thumb), semente: chamada (bl) em 0x080001C4, pilha: balanceada */
__attribute__((noinline, used)) u32 f_troca(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    { u32 a_ = r1, b_ = r0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* chamada por 1: f_main_teste */
/* origem: 0x0800041E (thumb), semente: chamada (bl) em 0x080001CA, pilha: balanceada */
__attribute__((noinline, used)) u32 f_distancia_adr(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    r8 = r8;
    r8 = r8;
    r0 = 0x08000428u;  /* adr: pc 0x08000424 + 0x4 */
    r1 = 0x0800042Cu;  /* adr: pc 0x08000428 + 0x4 */
    goto L_0800042C;
    L_0800042C: ;
    { u32 a_ = r1, b_ = r0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}
