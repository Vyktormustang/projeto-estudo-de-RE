.syntax unified
.cpu arm7tdmi
.thumb
.section .entry,"ax",%progbits
.align 2
.global entry_has,entry_space,entry_add,entry_remove,entry_quantity
.global entry_init,entry_destroy,entry_input,entry_title
.macro VECTOR name,dest
.thumb_func
\name:
 ldr r3,1f
 bx r3
 .align 2
1: .word \dest
.endm
VECTOR entry_has,hook_has
VECTOR entry_space,hook_space
VECTOR entry_add,hook_add
VECTOR entry_remove,hook_remove
VECTOR entry_quantity,hook_quantity
VECTOR entry_init,hook_init
VECTOR entry_destroy,hook_destroy
VECTOR entry_input,hook_input
VECTOR entry_title,hook_title

.section .text.gateways,"ax",%progbits
.global orig_has,orig_space,orig_add,orig_remove,orig_quantity
.global orig_init,orig_destroy,orig_input,orig_title
.thumb_func
orig_has:
 movs r3,#0x97
 lsls r0,r0,#16
 lsls r1,r1,#16
 push {r4,r5,lr}
 ldr r4,=0x080c6851
 bx r4
.thumb_func
orig_space:
 movs r3,#0x97
 lsls r0,r0,#16
 lsls r1,r1,#16
 push {r4,r5,r6,lr}
 ldr r4,=0x080c6905
 bx r4
.thumb_func
orig_add:
 movs r3,#0x97
 lsls r0,r0,#16
 lsls r1,r1,#16
 push {r4,r5,r6,r7,lr}
 ldr r4,=0x080c69ad
 bx r4
.thumb_func
orig_remove:
 movs r3,#0x97
 lsls r0,r0,#16
 lsls r1,r1,#16
 push {r4,r5,lr}
 ldr r4,=0x080c6b41
 bx r4
.thumb_func
orig_quantity:
 movs r3,#0x97
 lsls r0,r0,#16
 push {r4,lr}
 lsrs r0,r0,#16
 ldr r4,=0x080c7109
 bx r4
.thumb_func
orig_init:
 push {r4,r5,r6,r7,lr}
 movs r4,#0
 mov lr,r8
 ldr r3,=0x0203f080
 ldr r5,=0x0814b19d
 bx r5
.thumb_func
orig_destroy:
 ldr r3,=0x0203f078
 ldr r0,[r3]
 push {lr}
 cmp r0,#0
 ldr r3,=0x0814ba85
 bx r3
.thumb_func
orig_input:
 push {r4,r5,r6,r7,lr}
 mov lr,r10
 mov r7,r9
 mov r6,r8
 ldr r3,=0x0814bb85
 bx r3
.thumb_func
orig_title:
 push {r4,lr}
 ldr r4,=0x086d55ac
 sub sp,#12
 movs r1,r4
 ldr r3,=0x0814d011
 bx r3
.ltorg
