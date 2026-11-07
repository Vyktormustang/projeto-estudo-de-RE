.syntax unified
.cpu arm7tdmi
.thumb

// Substitui somente os três testes de ITEM_HM01 no menu da equipe.
// Só HM01–HM08 (IDs 339–346) são reutilizáveis. TMs antigas e SV são
// consumidas após aprendizado bem-sucedido; cancelar não chega aqui.
.extern remove_item, set_callback, end_first, end_second, end_third

.section .consume1,"ax",%progbits
.thumb_func
.global consume1
consume1:
    ldrh r0,[r4]
    movs r3,r0
    subs r3,#255
    subs r3,#84
    cmp r3,#7
    bls 1f
    movs r1,#1
    bl remove_item
1:  ldr r0,[r6]
    bl set_callback
    b end_first
    nop

.section .consume2,"ax",%progbits
.thumb_func
.global consume2
consume2:
    mov r3,r8
    ldrh r0,[r3]
    movs r3,r0
    subs r3,#255
    subs r3,#84
    cmp r3,#7
    bls 1f
    movs r1,#1
    bl remove_item
1:  ldr r0,[r4]
    bl set_callback
    b end_second

.section .consume3,"ax",%progbits
.thumb_func
.global consume3
consume3:
    movs r3,r7
    subs r3,#255
    subs r3,#84
    cmp r3,#7
    bls end_third
    movs r1,#1
    movs r0,r7
    bl remove_item
    b end_third
