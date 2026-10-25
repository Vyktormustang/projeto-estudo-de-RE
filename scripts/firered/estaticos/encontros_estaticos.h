#ifndef GUARD_ENCONTROS_ESTATICOS_H
#define GUARD_ENCONTROS_ESTATICOS_H

#include "global.h"

struct Sprite;
struct ObjectEvent;
struct ObjectEventTemplate;

// Faixa de "flags virtuais" dos encontros estáticos (acima das SPECIAL_FLAGS,
// que terminam em 0x407F). FLAG_ESTATICO_BASE + espécie responde, via
// Pokédex, se a espécie já foi capturada — usada no campo flag do objeto.
#define FLAG_ESTATICO_BASE 0x5000

void EstaticoPrepararEncontro(void);
void EstaticoCriarInimigo(void);
bool8 EstaticoFlagVirtual(u16 idx, bool8 *valor);
void EstaticoConfigurarSprite(const struct ObjectEventTemplate *template,
                              struct Sprite *sprite, u8 objectEventId);
void EstaticoReconfigurarSprite(struct ObjectEvent *objectEvent,
                                struct Sprite *sprite, u8 objectEventId);

#endif // GUARD_ENCONTROS_ESTATICOS_H
