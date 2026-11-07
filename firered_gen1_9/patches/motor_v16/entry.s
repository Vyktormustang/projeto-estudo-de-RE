.syntax unified
.cpu arm7tdmi
.thumb
.section .entry,"ax",%progbits
.align 2
.global entry_forcerandomswitch_v16
.thumb_func
entry_forcerandomswitch_v16:
 ldr r3,1f
 bx r3
 .align 2
1: .word hook_forcerandomswitch_v16
