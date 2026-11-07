.syntax unified
.cpu arm7tdmi
.thumb
.section .entry,"ax",%progbits
.align 2
.macro VECTOR name,dest
.global \name
.thumb_func
\name:
 ldr r3,1f
 bx r3
 .align 2
1: .word \dest
.endm
VECTOR entry_init_v17,hook_init_v17
VECTOR entry_switchin_v17,hook_switchin_v17
VECTOR entry_rapidspin_v17,hook_rapidspin_v17
VECTOR entry_field_apply_v17,hook_field_apply_v17
VECTOR entry_defog_v17,hook_defog_v17
VECTOR entry_tidy_v17,hook_tidy_v17
VECTOR entry_hazard_hit_v17,hook_hazard_hit_v17
VECTOR entry_set_spikes_v17,hook_set_spikes_v17
