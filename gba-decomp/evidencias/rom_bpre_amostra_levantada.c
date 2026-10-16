/* ============================================================================
   AMOSTRA do C levantado da ROM real -- Pokemon Fire Red BR (BPRE).

   A ROM NAO esta no repositorio: e imagem de terceiros (16 MB). O arquivo
   inteiro, de 1025643 linhas, e reproduzivel com:

     python -m gbadecomp.cli analisar ROM.gba --censo functions.csv \
            --json evidencias/rom_bpre_analise.json -o levantado_rom.c

   Estado medido (todos os numeros em evidencias/rom_bpre_analise.json):
     descoberta .........: 7998 funcoes,
                          442971 instrucoes listadas,
                          20393 arestas de chamada
     censo coberto ......: 5981/5981 (100%)
     fora do censo ......: 2017 funcoes que o censo nao tinha
     com C para ler .....: 7838 completas + 160 parciais (100.0%)
     tabelas de casos ...: 377 reconhecidas, 5789 casos viraram `switch`
     conferencia bytes ..: 442742/442971 (99.948%) remontam identicas
     compilacao .........: OK, 0 erros (objeto ARM de 2121016 bytes)

   O que isto NAO prova: semantica. Sem verdade-terreno nesta ROM, o que se prova
   e que cada instrucao remonta byte a byte e que o C compila -- comportamento so
   esta provado no corpus sintetico (59/59 por emulacao, no binario e no C
   levantado e recompilado). As lacunas que restam (100 desvios
   indiretos, 42 desvios para endereco nao desmontado...) aparecem MARCADAS
   dentro do proprio C, com endereco e motivo.
   ============================================================================ */


/* ---------------- FUN_08000a04 ---------------- */

__attribute__((noinline, used)) u32 FUN_08000a04(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    sp -= 12;
    guarda32(sp + 0, r4);
    guarda32(sp + 4, r5);
    guarda32(sp + 8, lr);
    r0 = 0x030000C0u;  /* pool 0x08000A30 */
    r0 = carrega8(r0);
    { u32 a_ = r0, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 != 0x0) goto L_08000A28;
    r5 = 0x0u;
    z = (r5 == 0); n = (r5 >> 31);
    L_08000A10: ;
    r0 = 0x03000060u;  /* pool 0x08000A34 */
    { u32 a_ = r5, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r4 = r_; }
    r0 = carrega8(r4);
    { u32 a_ = r0, b_ = 0xff; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 == 0xff) goto L_08000A28;
    /* bl 0x080009C0 (no modulo) */
    r0 = gpu_commit_idx_like(r0, r1, r2, r3);
    r0 = 0xFFu;
    z = (r0 == 0); n = (r0 >> 31);
    guarda8(r4, (u8)r0);
    { u32 a_ = r5, b_ = 0x1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r5 = r_; }
    { u32 a_ = r5, b_ = 0x5f; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if ((s32)r5 <= (s32)0x5f) goto L_08000A10;
    L_08000A28: ;
    r4 = carrega32(sp + 0);
    r5 = carrega32(sp + 4);
    sp += 8;
    r0 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}



/* ---------------- DISPATCHER_34c_tbl0803FC08 (Dispatcher do censo: tabela @0x0803FC08) ---------------- */
__attribute__((noinline, used)) u32 DISPATCHER_34c_tbl0803FC08(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    u32 idx_0803FC00 = 0;  /* indice da tabela de casos em 0x0803FC08 */
    (void)r1; (void)r2; (void)r3;
    sp -= 8;
    guarda32(sp + 0, r4);
    guarda32(sp + 4, lr);
    { u32 a_ = r0, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r4 = r_; }
    { u32 a_ = r1, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r3 = r_; }
    { u32 a_ = r3, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = 0x37; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = 0x21; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 <= 0x21) goto L_0803FBF8;
    goto L_0803FD36;
    L_0803FBF8: ;
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x2, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r1 = 0x0803FC08u;  /* pool 0x0803FC04 */
    idx_0803FC00 = r0;
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega32(r0);
    /* tabela de casos em 0x0803FC08: 34 casos lidos da ROM (indice x4) */
    switch (idx_0803FC00 >> 2) {
        case 0: goto L_0803FC90;
        case 1: goto L_0803FC94;
        case 2: goto L_0803FC9C;
        case 3: goto L_0803FCA4;
        case 4: goto L_0803FCAC;
        case 5: goto L_0803FCBE;
        case 6: goto L_0803FCD0;
        case 7: goto L_0803FCE2;
        case 8: goto L_0803FCF4;
        case 9: goto L_0803FD2E;
        case 10: goto L_0803FD36;
        case 11: goto L_0803FD36;
        case 12: goto L_0803FD36;
        case 13: goto L_0803FD36;
        case 14: goto L_0803FD36;
        case 15: goto L_0803FD36;
        case 16: goto L_0803FD36;
        case 17: goto L_0803FD36;
        case 18: goto L_0803FD36;
        case 19: goto L_0803FD36;
        case 20: goto L_0803FD36;
        case 21: goto L_0803FD36;
        case 22: goto L_0803FD36;
        case 23: goto L_0803FD36;
        case 24: goto L_0803FD36;
        case 25: goto L_0803FD36;
        case 26: goto L_0803FD36;
        case 27: goto L_0803FD36;
        case 28: goto L_0803FD36;
        case 29: goto L_0803FD06;
        case 30: goto L_0803FD0E;
        case 31: goto L_0803FD16;
        case 32: goto L_0803FD1E;
        case 33: goto L_0803FD26;
        default: g_erro |= 2; break;   /* fora da tabela */
    }
    return r0;   /* inalcancavel: todo caso salta */
    L_0803FC90: ;
    r0 = carrega32(r4 + 0x50);
    goto L_0803FD3E;
    L_0803FC94: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = 0x54 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega8(r0);
    goto L_0803FD3E;
    L_0803FC9C: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = 0x56 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega16(r0);
    goto L_0803FD3E;
    L_0803FCA4: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = 0x58 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega16(r0);
    goto L_0803FD3E;
    L_0803FCAC: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r1 = 0x1u;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08044674 (no modulo) */
    r0 = FUN_08044674(r0, r1, r2, r3);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x10, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x10, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r0, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 != 0x0) goto L_0803FD3E;
    goto L_0803FD06;
    L_0803FCBE: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r1 = 0x2u;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08044674 (no modulo) */
    r0 = FUN_08044674(r0, r1, r2, r3);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x10, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x10, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r0, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 != 0x0) goto L_0803FD3E;
    goto L_0803FD0E;
    L_0803FCD0: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r1 = 0x3u;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08044674 (no modulo) */
    r0 = FUN_08044674(r0, r1, r2, r3);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x10, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x10, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r0, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 != 0x0) goto L_0803FD3E;
    goto L_0803FD16;
    L_0803FCE2: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r1 = 0x4u;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08044674 (no modulo) */
    r0 = FUN_08044674(r0, r1, r2, r3);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x10, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x10, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r0, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 != 0x0) goto L_0803FD3E;
    goto L_0803FD1E;
    L_0803FCF4: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r1 = 0x5u;
    z = (r1 == 0); n = (r1 >> 31);
    /* bl 0x08044674 (no modulo) */
    r0 = FUN_08044674(r0, r1, r2, r3);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x10, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x10, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r0, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 != 0x0) goto L_0803FD3E;
    goto L_0803FD26;
    L_0803FD06: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = 0x5a + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega16(r0);
    goto L_0803FD3E;
    L_0803FD0E: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = 0x5c + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega16(r0);
    goto L_0803FD3E;
    L_0803FD16: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = 0x5e + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega16(r0);
    goto L_0803FD3E;
    L_0803FD1E: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = 0x60 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega16(r0);
    goto L_0803FD3E;
    L_0803FD26: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = 0x62 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega16(r0);
    goto L_0803FD3E;
    L_0803FD2E: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = 0x55 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega8(r0);
    goto L_0803FD3E;
    L_0803FD36: ;
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r3, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r1 = r_; }
    /* bl 0x0803FD44 (no modulo) */
    r0 = FUN_0803fd44(r0, r1, r2, r3);
    L_0803FD3E: ;
    r4 = carrega32(sp + 0);
    sp += 4;
    r1 = carrega32(sp + 0);
    sp += 4;
    return r0;
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}
