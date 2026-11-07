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
vector entry_select, select_info
vector entry_encounter, timed_encounter
vector entry_night, is_night
vector entry_sign, sign_period

.section .text.original_try,"ax",%progbits
.align 2
.global original_try
.thumb_func
original_try:
 push {r4,r5,r6,r7,lr}
 mov r7,r8
 mov lr,r9
 lsls r1,r1,#24
 ldr r3,1f
 bx r3
 .align 2
1: .word 0x08164349
