ENTRY(entry_damage_v6)
SECTIONS {
  . = 0x090BE000;
  .text : ALIGN(4) { KEEP(*(.entry)) *(.text*) *(.rodata*) }
  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) }
}
