ENTRY(entry_select)
SECTIONS {
 . = 0x0911B000;
 .text : ALIGN(4) { KEEP(*(.entry)) *(.text*) *(.rodata*) }
 /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) }
}
