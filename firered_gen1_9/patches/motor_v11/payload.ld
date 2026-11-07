ENTRY(entry_post_hit_v11)
SECTIONS {
  . = 0x090D6100;
  .text : ALIGN(4) { KEEP(*(.entry)) *(.text*) *(.rodata*) }
  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) }
}
