ENTRY(registro_substituiu)
substituiu_tm = 0x0812c415;
aprendeu_tm = 0x0812c40b;
SECTIONS {
  .registro_substituiu 0x0812C3BC : { KEEP(*(.registro_substituiu)) }
  .registro_aprendeu 0x0812C3EC : { KEEP(*(.registro_aprendeu)) }
  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) }
}
