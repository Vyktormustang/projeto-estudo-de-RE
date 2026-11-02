.syntax unified
.cpu arm7tdmi
.thumb
.section .entry,"ax",%progbits
.align 2
.global entry_adjust_v13,entry_healthbar_v13,entry_datahp_v13,entry_post_hit_v13
.macro VECTOR name,dest
.thumb_func
\name:
 ldr r3,1f
 bx r3
 .align 2
1: .word \dest
.endm
VECTOR entry_adjust_v13,hook_adjust_v13
VECTOR entry_healthbar_v13,hook_healthbar_v13
VECTOR entry_datahp_v13,hook_datahp_v13
VECTOR entry_post_hit_v13,hook_post_hit_v13
