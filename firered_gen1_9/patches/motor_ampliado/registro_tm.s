.syntax unified
.cpu arm7tdmi
.thumb
// No registro de aventuras, somente HM01–HM08 recebem a descrição HM.
.section .registro_substituiu,"ax",%progbits
.thumb_func
.global registro_substituiu
registro_substituiu:
    ldrh r2,[r4]
    subs r2,#255
    subs r2,#84
    cmp r2,#7
    bhi substituiu_tm
.section .registro_aprendeu,"ax",%progbits
.thumb_func
.global registro_aprendeu
registro_aprendeu:
    ldrh r2,[r4]
    subs r2,#255
    subs r2,#84
    cmp r2,#7
    bhi aprendeu_tm
