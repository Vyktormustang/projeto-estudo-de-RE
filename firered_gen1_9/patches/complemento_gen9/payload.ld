ENTRY(damage_entry)
SECTIONS { . = 0x0900C000; .text : ALIGN(4) { KEEP(*(.text.damage_entry)) *(.text*) *(.rodata*) } /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) } }
