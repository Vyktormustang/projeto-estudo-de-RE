.syntax unified
.cpu arm7tdmi
.thumb
.section .entry,"ax",%progbits
.align 2
.global entry_damage_v6,entry_callasm,entry_fling_check,entry_fling_secondary
.global entry_poltergeist_check,entry_steel_beam_dmg,entry_supercell_dmg
.macro VECTOR name,dest
.thumb_func
\name:
 ldr r3,1f
 bx r3
 .align 2
1: .word \dest
.endm
VECTOR entry_damage_v6,hook_damage_v6
VECTOR entry_callasm,hook_callasm
VECTOR entry_fling_check,hook_fling_check
VECTOR entry_fling_secondary,hook_fling_secondary
VECTOR entry_poltergeist_check,hook_poltergeist_check
VECTOR entry_steel_beam_dmg,hook_steel_beam_dmg
VECTOR entry_supercell_dmg,hook_supercell_dmg
