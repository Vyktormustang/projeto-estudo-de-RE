/* AMOSTRA do C levantado da ROM real (Pokemon - Fire Red BR, sha256
   6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae), gerado mecanicamente por decompile.py.
   Escolhidas entre as menores funcoes COMPLETAS com nome vindo do censo do
   projeto. O arquivo inteiro tem 776324 linhas / 29 MB e compila sem erros
   com: zig cc -target thumb-freestanding-eabi -mcpu=arm7tdmi -Os -c
   (o arquivo completo nao entra no Git: ele e reproduzivel pelo pipeline). */

/* origem: 0x080004B0 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 FUN_080004b0(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 4;
    guarda32(sp + 0, lr);
    /* bl 0x0800B178 (no modulo) */
    r0 = FUN_0800b178(r0, r1, r2, r3);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x18, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r0, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (!z) goto L_080004C0;
    /* bl 0x08000510 (no modulo) */
    r0 = FUN_08000510(r0, r1, r2, r3);
    L_080004C0: ;
    r0 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000564 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 FUN_08000564(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 8;
    guarda32(sp + 0, r4);
    guarda32(sp + 4, lr);
    r0 = 0x04000104u;  /* pool 0x08000580 */
    r4 = carrega16(r0);
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    /* bl 0x08044EE8 (no modulo) */
    r0 = fn_08044EE8(r0, r1, r2, r3);
    r1 = 0x04000106u;  /* pool 0x08000584 */
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    guarda16(r1, (u16)r0);
    r0 = 0x02020000u;  /* pool 0x08000588 */
    guarda16(r0, (u16)r4);
    r4 = carrega32(sp + 0);
    sp += 4;
    r0 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x080007C8 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 FUN_080007c8(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 4;
    guarda32(sp + 0, lr);
    r0 = 0x081E9F60u;  /* pool 0x080007D8 */
    r1 = carrega32(r0);
    r0 = 0x2u;
    z = (r0 == 0); n = (r0 >> 31);
    /* bl 0x081DE908 (no modulo) */
    r0 = FUN_081de908(r0, r1, r2, r3);
    r0 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000944 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 FUN_08000944(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 4;
    guarda32(sp + 0, lr);
    sp -= 4;  /* ajuste de pilha */
    r1 = sp;
    r0 = 0x0u;
    z = (r0 == 0); n = (r0 >> 31);
    guarda16(r1, (u16)r0);
    r1 = 0x03006F00u;  /* pool 0x08000960 */
    r2 = 0x01000034u;  /* pool 0x08000964 */
    r0 = sp;
    /* bl 0x081E3B64 (no modulo) */
    r0 = fn_081E3B64(r0, r1, r2, r3);
    sp += 4;  /* ajuste de pilha */
    r0 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}

/* origem: 0x08000B68 (thumb), pilha: balanceada */
__attribute__((noinline, used)) u32 FUN_08000b68(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 8;
    guarda32(sp + 0, r4);
    guarda32(sp + 4, lr);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x10, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x10, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r4 = 0x030000C2u;  /* pool 0x08000B8C */
    r1 = carrega16(r4);
    r0 = r0 | r1;
    z = (r0 == 0); n = (r0 >> 31);
    guarda16(r4, (u16)r0);
    r1 = 0x030000C1u;  /* pool 0x08000B90 */
    r0 = 0x1u;
    z = (r0 == 0); n = (r0 >> 31);
    guarda8(r1, (u8)r0);
    /* bl 0x08000B34 (no modulo) */
    r0 = FUN_08000b34(r0, r1, r2, r3);
    r0 = carrega16(r4);
    /* bl 0x08000BC0 (no modulo) */
    r0 = FUN_08000bc0(r0, r1, r2, r3);
    r4 = carrega32(sp + 0);
    sp += 4;
    r0 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}
