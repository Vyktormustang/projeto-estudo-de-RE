.syntax unified
.cpu arm7tdmi
.thumb
.section .entry,"ax",%progbits
.align 2
.global entry_disable_v15,entry_encore_v15
.macro VECTOR name,dest
.thumb_func
\name:
 ldr r3,1f
 bx r3
 .align 2
1: .word \dest
.endm
VECTOR entry_disable_v15,hook_disable_v15
VECTOR entry_encore_v15,hook_encore_v15
