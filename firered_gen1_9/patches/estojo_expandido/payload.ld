ENTRY(entry_has)
SECTIONS {
  . = 0x090B8000;
  .text : ALIGN(4) { KEEP(*(.entry)) *(.text*) *(.rodata*) }
  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) }
}
