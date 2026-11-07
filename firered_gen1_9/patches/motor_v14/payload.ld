ENTRY(entry_attackcanceler_v14)
SECTIONS {
  . = 0x090D8000;
  .text : ALIGN(4) { KEEP(*(.entry)) *(.text*) *(.rodata*) }
  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) }
}
