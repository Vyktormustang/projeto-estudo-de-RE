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
vector entry_header, hud_options_header
vector entry_input, hud_options_input
vector entry_preference, hud_preference
vector entry_toggle, hud_toggle

/* Native ProcessInput first 8 bytes, relocating its literal load. The last
 * LSLS must run AFTER loading the resume address so its flags reach BPL. */
.global original_input
.thumb_func
original_input:
 push {r4,lr}
 ldr r2,1f
 ldrh r3,[r2,#0x30]
 ldr r4,2f
 lsls r1,r3,#27
 bx r4
 .align 2
1: .word 0x0300460C
2: .word 0x080EF899
