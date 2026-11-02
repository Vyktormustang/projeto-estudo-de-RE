ENTRY(entry_battle_init_v9)
SECTIONS {
  . = 0x090C9000;
  .text : ALIGN(4) { KEEP(*(.entry)) *(.text*) *(.rodata*) . = ALIGN(4); }
  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) }
}
