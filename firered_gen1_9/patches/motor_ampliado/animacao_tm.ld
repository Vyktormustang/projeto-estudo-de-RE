ENTRY(anim_inline)
potion_inline = 0x08114a73;
SECTIONS {
  .anim_inline 0x081149E4 : { KEEP(*(.anim_inline)) }
  .anim_func 0x08115344 : { KEEP(*(.anim_func)) }
  /DISCARD/ : { *(.comment*) *(.ARM.attributes*) *(.ARM.exidx*) *(.ARM.extab*) }
}
