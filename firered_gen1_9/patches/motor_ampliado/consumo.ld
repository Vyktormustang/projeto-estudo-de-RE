ENTRY(consume1)
remove_item = 0x080c6b39;
set_callback = 0x08000595;
end_first = 0x080fcc7b;
end_second = 0x080fcd1d;
end_third = 0x080fdc91;
SECTIONS {
  .consume1 0x080FCCB8 : { KEEP(*(.consume1)) }
  .consume2 0x080FCD7C : { KEEP(*(.consume2)) }
  .consume3 0x080FDCFC : { KEEP(*(.consume3)) }
  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) }
}
