.syntax unified
.cpu arm7tdmi
.thumb
.section .entry,"ax",%progbits
.align 2
.global entry_post_hit_v11
.thumb_func
entry_post_hit_v11:
 ldr r3,1f
 bx r3
 .align 2
1: .word hook_post_hit_v11
