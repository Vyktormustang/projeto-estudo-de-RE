/* ============================================================================
   AMOSTRA do C levantado da ROM real -- Pokemon Fire Red BR (BPRE).

   A ROM NAO esta no repositorio: e imagem de terceiros (16 MB), e o arquivo
   inteiro e' reproduzivel com:

     python -m gbadecomp.cli analisar ROM.gba --censo censo/functions.csv \
            --json evidencias/rom_bpre_analise.json -o levantado_rom.c

   Estado medido (tudo em evidencias/rom_bpre_analise.json, gerado por esse
   comando nesta rodada):
     descoberta .........: 8151 funcoes,
                          439869 instrucoes listadas,
                          20379 arestas de chamada,
                          170 enderecos descartados
     censo coberto ......: 5981/5981 (100%)
     fora do censo ......: 2170 funcoes que o censo nao tinha
     tabelas de casos ...: 375 reconhecidas,
                          5767 casos lidos da ROM
     saltos para tras ...: 245 saidas de funcao;
                          154 trechos orfaos
                          recuperados como janela propria
     com C para ler .....: 8005 completas + 146 parciais (100.0%)
     C ..................: 1020566 linhas / 38375181 bytes
     conferencia bytes ..: 439640/439869 (99.948%) remontam
                          identicas ao binario; 225 divergencias
                          ({'cmp': 219, 'bx': 6}) e 4
                          instrucoes que o remontador nao aceita na sintaxe
     compilacao .........: OK, 0 erros
                          (objeto ARM de 2124636 bytes, sha256
                          17192ca3644ad20d...)

   O que isto NAO prova: semantica. Sem verdade-terreno nesta ROM, o que se prova
   e que cada instrucao remonta byte a byte e que o C compila -- comportamento so
   esta provado no corpus sintetico (59/59, emulando o binario E o C levantado e
   recompilado). As 146 funcoes com lacuna trazem a lacuna MARCADA
   dentro do proprio C, com endereco e motivo; nada e silenciado.

   Cada funcao abaixo e' recortada do arquivo inteiro, sem edicao, e mostra um
   caso que esta rodada passou a distinguir:
     - tabela de casos lida da ROM virou `switch`: FUN_080011e4
     - desvio para tras: a leitura continua em outra rotina: fn_08014040
     - `bx rN` recusado, com o motivo dito por inteiro (thunk de 4 bytes): fn_081DC45A
   ============================================================================ */

/* ---------------- FUN_080011e4 -- tabela de casos lida da ROM virou `switch` ---------------- */


/* chamada por 14: FUN_080014f0, FUN_080017d0, FUN_08001aa8, FUN_08001b90, FUN_08001ccc, FUN_08001d08, ... (+8) */
/* origem: 0x080011E4 (thumb), semente: informada, pilha: balanceada */
__attribute__((noinline, used)) u32 FUN_080011e4(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    u32 idx_08001218 = 0;  /* indice da tabela de casos em 0x08001224 */
    (void)r1; (void)r2; (void)r3;
    sp -= 12;
    guarda32(sp + 0, r4);
    guarda32(sp + 4, r5);
    guarda32(sp + 8, lr);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x18, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x18, &c_);
      c = c_; r4 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsl(r1, 0x18, &c_);
      c = c_; r1 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r1, 0x18, &c_);
      c = c_; r5 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r4, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    /* bl 0x080014DC (no modulo) */
    r0 = FUN_080014dc(r0, r1, r2, r3);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x18, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r0, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 != 0x0) goto L_08001290;
    r1 = 0x030008D0u;  /* pool 0x0800121C */
    { u32 c_ = c; u32 r_ = sh_lsl(r4, 0x2, &c_);
      c = c_; r2 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r2, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega8(r0);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x1f, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 a_ = r1, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r3 = r_; }
    { u32 a_ = r0, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 == 0x0) goto L_08001290;
    { u32 a_ = r5, b_ = 0x1; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    { u32 a_ = r0, b_ = 0x7; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 > 0x7) goto L_08001290;
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x2, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r1 = 0x08001224u;  /* pool 0x08001220 */
    idx_08001218 = r0;
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega32(r0);
    /* tabela de casos em 0x08001224: 8 casos lidos da ROM (indice x4) */
    switch (idx_08001218 >> 2) {
        case 0: goto L_08001244;
        case 1: goto L_0800124E;
        case 2: goto L_08001258;
        case 3: goto L_08001262;
        case 4: goto L_0800126C;
        case 5: goto L_08001274;
        case 6: goto L_0800127E;
        case 7: goto L_08001288;
        default: g_erro |= 2; break;   /* fora da tabela */
    }
    return r0;   /* inalcancavel: todo caso salta */
    L_08001244: ;
    { u32 a_ = r2, b_ = r3 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega8(r0);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x1f, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x1f, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    goto L_08001292;
    L_0800124E: ;
    { u32 a_ = r2, b_ = r3 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega8(r0 + 0x1);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x1e, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x1e, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    goto L_08001292;
    L_08001258: ;
    { u32 a_ = r2, b_ = r3 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega8(r0 + 0x1);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x19, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x1b, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    goto L_08001292;
    L_08001262: ;
    { u32 a_ = r2, b_ = r3 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
    /* ... 61 linhas omitidas AQUI para a amostra caber; a funcao inteira esta no levantado_rom.c, que este comando gera */
/* ---------------- fn_08014040 -- desvio para tras: a leitura continua em outra rotina ---------------- */


/* PARCIAL (0x08014040): o corpo abaixo tem lacunas marcadas -- em execucao, marca g_erro:
     0x0801415C b #0x8013a18: desvio para tras, para fora da funcao (0x08013A18 < entrada 0x08014040): a leitura continua em bloco comum de outra rotina
   */
/* origem: 0x08014040 (thumb), semente: ponteiro de pool em 0x08013CCC, pilha: balanceada, fim: salto para fora (para tras): 0x08013A18 */
__attribute__((noinline, used)) u32 fn_08014040(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    u32 idx_08014088 = 0;  /* indice da tabela de casos em 0x0801409C */
    u32 idx_08014230 = 0;  /* indice da tabela de casos em 0x0801424C */
    u32 idx_080147A6 = 0;  /* indice da tabela de casos em 0x080147BC */
    (void)r1; (void)r2; (void)r3;
    sp -= 20;
    guarda32(sp + 0, r4);
    guarda32(sp + 4, r5);
    guarda32(sp + 8, r6);
    guarda32(sp + 12, r7);
    guarda32(sp + 16, lr);
    r7 = r10;
    r6 = r9;
    r5 = r8;
    sp -= 12;
    guarda32(sp + 0, r5);
    guarda32(sp + 4, r6);
    guarda32(sp + 8, r7);
    sp -= 28;  /* ajuste de pilha */
    r0 = 0x02023E82u;  /* pool 0x0801408C */
    r1 = 0x0u;
    z = (r1 == 0); n = (r1 >> 31);
    guarda8(r0 + 0x4, (u8)r1);
    r0 = 0x02023BC4u;  /* pool 0x08014090 */
    guarda8(r0, (u8)r1);
    r0 = 0x02023BCCu;  /* pool 0x08014094 */
    { u32 a_ = r0, b_ = 0x0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r2 = r_; }
    r0 = carrega8(r2);
    { u32 a_ = r1, b_ = r0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r1 < r0) goto L_08014064;
    /* bl 0x08014C68 (no modulo) */
    r0 = fn_08014C68(r0, r1, r2, r3);
    L_08014064: ;
    r4 = 0x02023BC4u;  /* pool 0x08014090 */
    r0 = carrega8(r4);
    /* bl 0x080751D8 (no modulo) */
    r0 = fn_080751D8(r0, r1, r2, r3);
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x18, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    { u32 c_ = c; u32 r_ = sh_lsr(r0, 0x18, &c_);
      c = c_; r5 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r1 = 0x02023E82u;  /* pool 0x0801408C */
    r0 = carrega8(r4);
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega8(r0);
    { u32 a_ = r0, b_ = 0x6; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 <= 0x6) goto L_08014080;
    /* bl 0x08014C4E (no modulo) */
    r0 = fn_08014C4E(r0, r1, r2, r3);
    L_08014080: ;
    { u32 c_ = c; u32 r_ = sh_lsl(r0, 0x2, &c_);
      c = c_; r0 = r_; z = (r_ == 0); n = (r_ >> 31); }
    r1 = 0x0801409Cu;  /* pool 0x08014098 */
    idx_08014088 = r0;
    { u32 a_ = r0, b_ = r1 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r0 = r_; }
    r0 = carrega32(r0);
    /* tabela de casos em 0x0801409C: 7 casos lidos da ROM (indice x4) */
    switch (idx_08014088 >> 2) {
        case 0: goto L_080140B8;
        case 1: goto L_080141DC;
        case 2: goto L_08014764;
        case 3: goto L_08014AA0;
        case 4: goto L_08014B44;
        case 5: goto L_08014B88;
        case 6: goto L_08014C20;
        default: g_erro |= 2; break;   /* fora da tabela */
    }
    return r0;   /* inalcancavel: todo caso salta */
    L_080140B8: ;
    r0 = 0x02023BC4u;  /* pool 0x08014150 */
    r1 = carrega8(r0);
    r4 = 0x02023FE8u;  /* pool 0x08014154 */
    r0 = carrega32(r4);
    { u32 a_ = r1, b_ = r0 + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r1 = r_; }
    { u32 a_ = r1, b_ = 0x5c + 0; u32 r_ = a_ + b_;
      c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31);
      r1 = r_; }
    r0 = 0x6u;
    z = (r0 == 0); n = (r0 >> 31);
    guarda8(r1, (u8)r0);
    r0 = 0x02022B4Cu;  /* pool 0x08014158 */
    r0 = carrega32(r0);
    r1 = 0x40u;
    z = (r1 == 0); n = (r1 >> 31);
    r0 = r0 & r1;
    z = (r0 == 0); n = (r0 >> 31);
    { u32 a_ = r0, b_ = 0x0; u32 r_ = a_ - b_;
      c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;
      z = (r_ == 0); n = (r_ >> 31); }
    if (r0 != 0x0) goto L_08014114;
    r1 = 0x2u;
    z = (r1 == 0); n = (r1 >> 31);
    r0 = 0x2u;
    /* ... 2406 linhas omitidas AQUI para a amostra caber; a funcao inteira esta no levantado_rom.c, que este comando gera */
/* ---------------- fn_081DC45A -- `bx rN` recusado, com o motivo dito por inteiro (thunk de 4 bytes) ---------------- */


/* PARCIAL (0x081DC45A): o corpo abaixo tem lacunas marcadas -- em execucao, marca g_erro:
     0x081DC45A bx r3: thunk de salto indireto: a janela comeca em `bx rN` (com nop de alinhamento), ou seja o destino vem NO REGISTRADOR, de quem chamou -- traduzir exigiria inventar a assinatura
   */
/* chamada por 1: fn_081DC020 */
/* origem: 0x081DC45A (thumb), semente: chamada (bl) em 0x081DC064, pilha: balanceada */
__attribute__((noinline, used)) u32 fn_081DC45A(u32 r0, u32 r1, u32 r2, u32 r3) {
    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;
    u32 pc = 0;  /* escrever em pc = retorno/desvio: tratado explicitamente, ver comentarios */
    u32 z = 0, n = 0, c = 0, v = 0;
    u32 sp = PILHA_TOPO, sp0 = sp;
    (void)r1; (void)r2; (void)r3;
    /* NAO LEVANTADO: bx r3 */
    if (sp != sp0) { g_erro |= 1; }
    return r0;
}
