# Eternatus battle assets (FireRed BR)

These assets replace only internal species slot 252 (the first legacy `OLD_UNOWN_*` placeholder). The other placeholder slots remain unchanged. The `MODS > POKEMON` selector sorts all 387 visible names alphabetically.

- `front.4bpp`, `back.4bpp`: 64×64 GBA 4bpp tile graphics, 2048 bytes each.
- `normal.pal`, `shiny.pal`: 16-color BGR555 palettes, including transparent index 0.
- `icon.4bpp`: 32×32 party/menu icon, raw 4bpp tiles.
- `icon.pal`: dedicated raw icon palette.
- `source/`: source front/back sprites, standard and shiny variants.

Source images are from the PokeAPI sprites repository, species 890: `https://github.com/PokeAPI/sprites` (paths `sprites/pokemon/890.png`, `sprites/pokemon/back/890.png`, and the corresponding `shiny/` paths). `scripts/prepare_eternatus_assets.py` regenerates the binary assets; it requires Pillow. Once generated, the ROM builder itself consumes the binary files and does not require Pillow.

The ROM's Gen III move database does not contain Eternatus's later-generation signature moves. Its learnset therefore uses available adaptations: Dragon Tail → Dragon Claw, Poison Tail → Sludge Bomb, Venoshock → Acid, Cross Poison → Poison Gas, Dragon Pulse → Dragon Breath, Dynamax Cannon → Dragon Rage, and Eternabeam → Hyper Beam. It is available only through the selector; no encounter or Eternamax form is added.
