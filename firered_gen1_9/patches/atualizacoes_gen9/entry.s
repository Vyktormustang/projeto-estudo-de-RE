.syntax unified
.cpu arm7tdmi
.thumb
.section .entry,"ax",%progbits
.align 2
.global entry_can,entry_label
.macro VECTOR name,dest
.thumb_func
\name:
 ldr r3,1f
 bx r3
 .align 2
1: .word \dest
.endm
VECTOR entry_can,tm_can
VECTOR entry_label,tm_label
VECTOR entry_shopnum,shopnum
VECTOR entry_disc_create,disc_create
VECTOR entry_disc_swap,disc_swap
.section .text.hooks,"ax",%progbits
.thumb_func
disc_create:
 movs r7,r4
 lsls r6,r0,#4
 ldr r3,=0x0203cfcc
 ldr r2,=375
 cmp r4,r2
 blo 1f
 movs r7,#0
 b 2f
1: subs r7,#33
2: ldr r2,=0x0814d2ed
 bx r2
.thumb_func
disc_swap:
 ldr r2,=375
 cmp r3,r2
 blo 1f
 movs r3,#0
 b 2f
1: subs r3,#34
 subs r3,#255
2: lsls r3,r3,#16
 lsrs r3,r3,#16
 ldr r2,=0x0814d48d
 bx r2
.thumb_func
shopnum:
 ldr r6,=0x0203e67c
 ldr r3,=375
 cmp r4,r3
 blo 1f
 subs r1,#119
 movs r3,#3
 b 2f
1:
 subs r1,#33
 movs r3,#2
2:
 movs r2,#2
 ldr r0,=0x0813bba1
 bx r0
.thumb_func
.global orig_can
orig_can:
 lsls r1,r1,#16
 push {r4,r5,r6,lr}
 lsls r2,r2,#24
 lsrs r4,r1,#16
 ldr r3,=0x080f8469
 bx r3
.thumb_func
.global orig_label
orig_label:
 push {r4,r5,r6,r7,lr}
 ldr r4,=0x0203e6c4
 lsls r5,r1,#16
 movs r6,r0
 ldr r3,=0x0814b679
 bx r3
.ltorg
