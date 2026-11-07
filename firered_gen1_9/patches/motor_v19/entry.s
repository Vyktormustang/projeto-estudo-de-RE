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
vector entry_phase, clock_phase
vector entry_tint, clock_tint
vector entry_field, clock_field_vblank
vector entry_evolution, clock_evolution

/* Exact eight overwritten bytes at 0810DB44, no PC-relative instructions.
 * Preserve the original frame and high callee-saved registers, then resume. */
.section .text.original_evolution,"ax",%progbits
.align 2
.global original_evolution
.thumb_func
original_evolution:
 push {r4,r5,r6,r7,lr}
 mov lr,r11
 mov r7,r10
 mov r6,r9
 ldr r3,1f
 bx r3
 .align 2
1: .word 0x0810DB4D
