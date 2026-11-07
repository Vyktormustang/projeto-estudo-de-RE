ENTRY(entry_select)
SECTIONS {
 . = 0x090F3000;
 .text : ALIGN(4) { KEEP(*(.entry)) *(.text*) *(.rodata*) }
 /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) }
}
