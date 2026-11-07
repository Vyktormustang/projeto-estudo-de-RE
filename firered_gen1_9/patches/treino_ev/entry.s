    .syntax unified
    .cpu arm7tdmi
    .thumb
    .section .entry,"ax",%progbits
    .global treino_entry
    .type treino_entry,%function
    .thumb_func
/* Task entry receives the task id in r0. Keep an 8-byte-aligned stack. */
treino_entry:
    push {r0-r4, lr}
    bl treino_handle_input
    mov r12, r0
    pop {r0-r4}
    pop {r2}
    mov lr, r2
    mov r2, r12
    cmp r2, #0
    bne 1f
    /* Original eight bytes displaced by the hook, then resume at +8. */
    push {r4, r5, r6, r7, lr}
    mov lr, r9
    mov r7, r8
    push {r7, lr}
    ldr r3, =0x081222e9
    bx r3
1:  bx lr
    .size treino_entry, .-treino_entry
