ENTRY(entry_update)
SECTIONS {
 . = 0x090E8000;
 .text : ALIGN(4) { KEEP(*(.entry)) *(.text*) *(.rodata*) }
 /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) }
}
