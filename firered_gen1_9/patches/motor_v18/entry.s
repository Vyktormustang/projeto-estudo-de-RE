.syntax unified
.cpu arm7tdmi
.thumb
.section .entry,"ax",%progbits
.align 2
.global entry_pivot_v18
.thumb_func
entry_pivot_v18:
 ldr r3,1f
 bx r3
 .align 2
1: .word hook_pivot_v18
