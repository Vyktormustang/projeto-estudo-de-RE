.syntax unified
.cpu arm7tdmi
.thumb

// Classificação em AllocPSA: 289–346 (TMs/HMs antigas) e 375–603
// (TMs modernas) usam a animação de máquina; os IDs intermediários
// permanecem itens normais. Poção continua tendo a própria animação.
.section .anim_inline,"ax",%progbits
.thumb_func
.global anim_inline
anim_inline:
    cmp r5,#13
    beq potion_inline
    movs r2,r5
    movs r3,#1
    subs r2,#255
    subs r2,#34              // item - 289
    cmp r2,#57               // 289..346
    bls 1f
    subs r2,#86              // item - 375, com underflow protegido
    movs r1,#228
    cmp r1,r2                // 375..603
    movs r3,#0               // MOVS não altera carry
    adcs r3,r3
1:  lsls r3,r3,#2            // PSA_ITEM_ANIM_TYPE_TMHM = 4

// A mesma lógica na função não inline, preservando sua ABI.
.section .anim_func,"ax",%progbits
.thumb_func
.global anim_func
anim_func:
    lsls r0,r0,#16
    lsrs r0,r0,#16
    cmp r0,#13
    beq 2f
    subs r0,#255
    subs r0,#34
    movs r3,#1
    cmp r0,#57
    bls 1f
    subs r0,#86
    movs r2,#228
    cmp r2,r0
    movs r3,#0
    adcs r3,r3
1:  lsls r0,r3,#2
    bx lr
2:  movs r0,#1
    bx lr
