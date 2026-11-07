.syntax unified
.cpu arm7tdmi
.thumb
.section .entry,"ax",%progbits
.align 2
.macro vector name, target
.global \name
.thumb_func
\name:
 ldr r3,1f
 bx r3
 .align 2
1: .word \target
.endm
vector entry_minutes, clock_minutes
vector entry_update, clock_update

/* Relocate the PC-relative load/conditional from 08101664; do NOT copy its
 * raw eight bytes. The unmodified native bx lr at 0810166C stays in place. */
.section .text.original_update,"ax",%progbits
.align 2
.global original_update
.thumb_func
original_update:
 ldr r2,1f
 ldrb r3,[r2]
 cmp r3,#1
 beq 2f
 bx lr
2:
 ldr r3,3f
 bx r3
 .align 2
1: .word 0x030021D6
3: .word 0x0810166F
