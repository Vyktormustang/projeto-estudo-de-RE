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
vector entry_update, hud_update
vector entry_field, hud_field_vblank
vector entry_render, hud_render
vector entry_digits, hud_digits
vector entry_prepare, hud_prepare
