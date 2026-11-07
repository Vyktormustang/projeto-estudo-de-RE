"""Preparação/observação de estados sintéticos; não lê/escreve saves pessoais.

Nível e EXP são campos separados em Pokemon. Não passar species/level para
set_exp_and_test_stats: seus argumentos são experience/stat.
"""
import struct
from mgba_treino_harness import PARTY, decrypted, mon, mon_facts, offset, put16, put32, u32
from test_golpes_gen9_integracao import set_exp_and_test_stats

# Bulbasaur/Charmander/Charizard: curva medium-slow, nível 10 -> 560;
# nível 11 -> 742. Helper intencionalmente limitado às fixtures v10-v13.
LEVEL10_STARTERS = (1,4,6)
LEVEL10_EXP = 560
LEVEL11_EXP = 742
IWRAM_STATE_OFFSET = 0x19000  # formato mGBA 0.10.5
MAIN_CALLBACK2_OFFSET = IWRAM_STATE_OFFSET + 0x4610
MAIN_FLAGS_OFFSET = IWRAM_STATE_OFFSET + 0x4A45
BATTLE_OUTCOME = 0x020216C8


def party_experience(state):
    block,order,valid = decrypted(mon(state))
    if not valid:
        raise ValueError('Checksum de Pokémon sintético inválido')
    return u32(block,order[0]*12+4)


def set_party_experience(state, experience):
    """Muda SOMENTE EXP criptografada e checksum no primeiro slot da fixture.

    Permite EXP incoerente deliberada para testes negativos; não valida nível.
    Recebe bytearray em memória, nunca caminho de arquivo.
    """
    if not isinstance(state,bytearray) or not 0 <= experience <= 0xFFFFFFFF:
        raise ValueError('Use bytearray sintético e EXP uint32')
    data = mon(state)
    block,order,valid = decrypted(data)
    if not valid:
        raise ValueError('Checksum de Pokémon sintético inválido')
    put32(block,order[0]*12+4,experience)
    put16(data,28,sum(struct.unpack('<24H',block))&0xFFFF)
    key = u32(data,0)^u32(data,4)
    for i in range(0,48,4):
        put32(data,32+i,u32(block,i)^key)
    state[offset(PARTY):offset(PARTY)+100] = data


def set_level10_starter_test_stats(state, *, stat=10):
    """EXP coerente para as três espécies usadas nas fábricas de batalha.

    Não generalizar a outras espécies/níveis sem consultar sua curva. Os HPs
    e atributos continuam sintéticos, como antes; apenas EXP é corrigida.
    """
    facts = mon_facts(mon(state))
    if not facts['valid'] or facts['species'] not in LEVEL10_STARTERS or facts['level'] != 10:
        raise ValueError('Helper restrito a Bulbasaur/Charmander/Charizard no nível 10')
    set_exp_and_test_stats(state,experience=LEVEL10_EXP,stat=stat)


def main_callback2(state):
    return u32(state,MAIN_CALLBACK2_OFFSET)


def in_battle(state):
    return bool(state[MAIN_FLAGS_OFFSET]&2)


def finish_victory(f, field_callback, *, limit=40):
    """Confirma mensagens com B e exige vitória + flag fora de batalha + callback.

    Não usar somente o texto da batalha: ele permanece em RAM após voltar ao
    mapa. Não força callbacks/registradores nem altera memória do emulador.
    """
    for _ in range(limit):
        st = f.state()
        if st[offset(BATTLE_OUTCOME)] == 1 and not in_battle(st) and main_callback2(st) == field_callback:
            return st
        f.pulse('B',90)
    raise AssertionError('Vitória/retorno ao mapa não observados dentro do limite')
