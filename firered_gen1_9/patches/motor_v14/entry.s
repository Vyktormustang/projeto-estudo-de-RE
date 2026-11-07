.syntax unified
.cpu arm7tdmi
.thumb
.section .entry,"ax",%progbits
.align 2
.global entry_attackcanceler_v14
.thumb_func
entry_attackcanceler_v14:
 ldr r3,1f
 bx r3
 .align 2
1: .word hook_attackcanceler_v14
