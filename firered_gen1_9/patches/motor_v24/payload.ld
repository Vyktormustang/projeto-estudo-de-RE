ENTRY(entry_minutes)
SECTIONS {
 . = 0x090E6000;
 .text : ALIGN(4) { KEEP(*(.entry)) *(.text*) *(.rodata*) }
 /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) }
}
