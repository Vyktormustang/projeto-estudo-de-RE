ENTRY(entry_can)
SECTIONS { . = 0x08e04400; .text : ALIGN(4) { KEEP(*(.entry)) *(.text*) *(.rodata*) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) } }
