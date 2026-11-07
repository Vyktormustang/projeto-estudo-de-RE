.syntax unified
.cpu arm7tdmi
.thumb
.section .entry,"ax",%progbits
.align 2
.global entry_initial, entry_level, entry_relearn, entry_egg, entry_count
.global entry_evo_normal, entry_evo_trade, entry_relearn_name
.global entry_tm_forget_name, entry_tm_teach_name, entry_battle_name
/* 8-byte stable branch veneers: offsets 0x00, 0x08, ..., 0x50. */
.macro VECTOR name, dest
.thumb_func
\name:
    ldr r3, 1f
    bx r3
    .align 2
1:  .word \dest
.endm
VECTOR entry_initial, modern_initial
VECTOR entry_level, modern_try_level
VECTOR entry_relearn, modern_relearn
VECTOR entry_egg, modern_egg_moves
VECTOR entry_count, modern_relearn_count
VECTOR entry_evo_normal, evo_normal
VECTOR entry_evo_trade, evo_trade
VECTOR entry_relearn_name, relearn_name
/* These hooks receive the move-name table in r3; keep it intact. */
.macro VECTOR_R2 name, dest
.thumb_func
\name:
    ldr r2, 1f
    bx r2
    .align 2
1:  .word \dest
.endm
VECTOR_R2 entry_tm_forget_name, tm_forget_name
VECTOR_R2 entry_tm_teach_name, tm_teach_name
VECTOR_R2 entry_battle_name, battle_name

.section .text.hooks,"ax",%progbits
.align 2
.thumb_func
evo_normal:
    ldrb r1, [r4, #0x10]
    ldrh r2, [r4, #0x1a]
    bl modern_try_evolution
    mov r8, r0
    ldr r3, =0x080a0c79
    bx r3
.thumb_func
evo_trade:
    mov r0, sb
    ldrb r1, [r4, #0x10]
    ldrh r2, [r4, #0x1a]
    bl modern_try_evolution
    ldr r3, =0x080a135d
    bx r3
/* Copy at most r2 characters plus the 0xff terminator. Only clobbers the
 * caller-saved registers that the old StringCopy call could clobber. */
.thumb_func
bounded_copy:
    cmp r2, #0
    beq 2f
1:  ldrb r3, [r1]
    cmp r3, #0xff
    beq 2f
    strb r3, [r0]
    adds r0, #1
    adds r1, #1
    subs r2, #1
    bne 1b
2:  movs r3, #0xff
    strb r3, [r0]
    bx lr
.thumb_func
relearn_name:
    add r1, r8
    movs r2, #12
    bl bounded_copy
    ldr r0, [r7]
    ldr r3, =0x080cf7fd
    bx r3
.thumb_func
tm_forget_name:
    adds r1, r1, r3
    adds r0, #0x77
    movs r2, #12
    bl bounded_copy
    ldr r3, =0x081148d5
    bx r3
.thumb_func
tm_teach_name:
    adds r0, #0x84
    adds r1, r1, r3
    movs r2, #12
    bl bounded_copy
    ldr r3, =0x08114a6d
    bx r3
.thumb_func
battle_name:
    adds r1, r1, r3
    movs r2, #15
    bl bounded_copy
    ldr r3, =0x08055b59
    bx r3
.ltorg
