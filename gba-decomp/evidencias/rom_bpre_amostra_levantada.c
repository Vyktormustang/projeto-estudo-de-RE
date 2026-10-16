/* ============================================================================
   AMOSTRA do C levantado da ROM real -- Pokemon Fire Red BR (BPRE).

   A ROM NAO esta no repositorio (imagem de terceiros, 16 MB): o arquivo inteiro,
   de 831870 linhas, e reproduzivel com um comando:

     python -m gbadecomp.cli analisar ROM.gba --censo functions.csv \
            --json evidencias/rom_bpre_analise.json -o levantado_rom.c

   Numeros desta rodada (evidencias/rom_bpre_analise.json):
     ROM .................: sha256 6035a98faf09f5f6db880f0ab436c54f...
     descoberta ..........: 7634 funcoes, 352918 instrucoes, 16387 arestas
     com C para ler ......: 7634/7634 (100.0%) -- 7228 completas + 406 parciais
     sem corpo nenhum ....: 0
     descartados .........: 83 enderecos tentados como funcao que nao tinham codigo do ARM7TDMI
     conferencia de bytes : 352888/352918 (99.991%) remontam identicas ao binario
     compilacao ..........: OK, 0 erros (zig cc -mcpu=arm7tdmi, objeto de 1761916 bytes)

   O que este arquivo NAO prova: semantica. Num binario de terceiros nao existe
   verdade-terreno; o que se prova e que cada instrucao remonta byte a byte e que
   o C compila. Comportamento so esta provado no corpus sintetico (59/59 casos,
   por emulacao, no binario e no C levantado e recompilado).
   ============================================================================ */


/* ---------------- tabela de casos (PARCIAL, g_erro |= 2 no ponto) ---------------- */

__attribute__((noinline, used)) u32 fn_080415B4(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    r4 = carrega32(sp + 0x18);
    { u32 a_ = r4, b_ = 0x5; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r4 <= 0x5) goto L_080415BE;
    /* bl 0x08042384 (no modulo) */
    r0 = fn_08042384(r0, r1, r2, r3);
    L_080415BE: ;
    { u32 c_ = c; u32 r_ = sh_lsl(r4, 0x2, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r1 = 0x080415CCu;  /* pool 0x080415C8 */
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega32(r0);
    /* PC calculado em r0: tabela de casos nao modelada */
    g_erro |= 2;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}



/* ---------------- fronteira de BIOS: declarada, nunca definida ---------------- */

__attribute__((noinline, used)) u32 fn_081E3B58(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    r0 = bios_svc(0xAu, r0, r1, r2, r3);  /* chamada de BIOS */
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}



/* ---------------- condicao fundida com o cmp ---------------- */

__attribute__((noinline, used)) u32 FUN_08060280(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 4;
    guarda32(sp + 0, lr);
    r0 = 0x1u;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 c_ = c; u32 r_ = sh_lsl(r1, 0x10, &c_);
      c = c_; r1 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r1, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((s32)r1 >= (s32)0x0) goto L_0806028C;
    r0 = 0x2u;
    z = (r0 == 0); n = (r0 >> 31);
    L_0806028C: ;
    r1 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}


