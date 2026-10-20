"""Estudo: da para reconstruir as tabelas de casos (`mov pc, rX`) com seguranca?

Contexto: 306 instrucoes da ROM de estudo sao salto calculado -- o lifter nao
inventa traducao e marca a funcao como PARCIAL. Antes de implementar qualquer
coisa, este script MEDE o idioma real no binario, porque implementar de cabeca
(o que eu faria escrevendo `switch` a partir de suposicoes) seria inventar.

O idioma que aparece em 304 dos 306 casos:

    add  r0, r1        ; r0 = indice*4, r1 = base da tabela (vinda do pool)
    ldr  r0, [r0]      ; r0 = tabela[indice]  <- endereco do caso, lido da ROM
    mov  pc, r0        ; salto

Para cada sitio o script responde: qual e a base da tabela, quantas entradas ela
tem, e -- o critrio que decide -- se os alvos existem como codigo ja desmontado
na propria funcao. Se os alvos nao estiverem la, um `switch` so mudaria o texto,
nao a cobertura, e nao vale o risco.

    python ferramentas/estudo_switch.py ROM.gba --censo functions.csv
"""

from __future__ import annotations

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import capstone  # noqa: E402

from gbadecomp import disasm, rom as rom_mod  # noqa: E402

PC = capstone.arm.ARM_REG_PC


def _reg(operando) -> int:
    return operando.reg


def _ler32(imagem: bytes, base: int, endereco: int) -> int | None:
    off = endereco - base
    if off < 0 or off + 4 > len(imagem):
        return None
    return int.from_bytes(imagem[off:off + 4], "little")


def _endereco_de_codigo(valor: int, base: int, tamanho: int) -> bool:
    """Endereco de codigo na imagem.

    Diferente de um ponteiro de funcao comum (que tem bit0=1 para dizer "Thumb"),
    as entradas destas tabelas sao PARES: no Thumb, `mov pc, rN` alinha o valor em
    meia-palavra e nao troca de modo -- ou seja, o bit0 nao carrega informacao.
    """
    return base <= (valor & ~1) < base + tamanho


def analisar(caminho_rom: str, censo: str | None) -> dict:
    rom = rom_mod.GbaRom(caminho_rom)
    sementes: dict[int, str] = {}
    if censo:
        for span in rom_mod.carregar_funcoes_csv(censo):
            sementes.setdefault(span.addr, span.mode or "thumb")
    desmontagem = disasm.desmontar_por_sementes(rom.data, sementes=sementes or None)
    BASE = rom_mod.ROM_BASE

    cs_t = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    cs_t.detail = True          # capstone 5: detalhe se liga por propriedade
    total_sitios = 0
    idioma_ok = 0
    com_base = 0
    com_alvos_desmontados = 0
    entradas = collections.Counter()
    conferencias = collections.Counter()
    exemplos = []
    padroes_crus = collections.Counter()

    for funcao in desmontagem.funcoes.values():
        desmontados = {i.endereco for i in funcao.instrucoes}
        # (re)desmonta a funcao inteira com capstone para ter os operandos
        ultimo = max((i.endereco + len(i.bytes_) for i in funcao.instrucoes), default=funcao.entrada)
        bruto = rom.data[funcao.entrada - BASE:ultimo - BASE]
        lista = list(cs_t.disasm(bruto, funcao.entrada))
        for pos, ins in enumerate(lista):
            if not (ins.mnemonic == "mov" and ins.op_str.startswith("pc,")):
                continue
            total_sitios += 1
            if pos < 2:
                padroes_crus["mov pc sem vizinhos"] += 1
                continue
            anterior = lista[pos - 1]
            antes = lista[pos - 2]
            # idioma: ldr rX, [rX] e depois add rX, rY
            ok_ldr = (anterior.mnemonic == "ldr" and len(anterior.operands) == 2
                      and anterior.operands[0].type == capstone.arm.ARM_OP_REG
                      and anterior.operands[1].type == capstone.arm.ARM_OP_MEM
                      and anterior.operands[1].mem.base == anterior.operands[0].reg
                      and anterior.operands[1].mem.disp == 0)
            # Thumb: `adds rX, rX, rY` (3 operandos: destino, primeira parcela, base)
            ok_add = (antes.mnemonic.startswith("add") and len(antes.operands) == 3
                      and all(o.type == capstone.arm.ARM_OP_REG for o in antes.operands)
                      and antes.operands[0].reg == antes.operands[1].reg)
            if not (ok_ldr and ok_add):
                padroes_crus[f"{antes.mnemonic} | {anterior.mnemonic} | mov pc"] += 1
                continue
            idioma_ok += 1
            indice_reg = antes.operands[0].reg
            base_reg = antes.operands[2].reg
            # quanto o indice foi multiplicado antes da soma (lsls rX, rX, #N)
            deslocamento = None
            for atras in range(pos - 3, max(-1, pos - 12), -1):
                cand = lista[atras]
                if (cand.mnemonic.startswith("lsl") and len(cand.operands) == 3
                        and cand.operands[0].type == capstone.arm.ARM_OP_REG
                        and cand.operands[0].reg == indice_reg):
                    deslocamento = cand.operands[2].imm
                    break
            # procura para tras quem carregou base_reg do pool
            tabela = None
            for atras in range(pos - 3, max(-1, pos - 40), -1):
                cand = lista[atras]
                if (cand.mnemonic == "ldr" and len(cand.operands) == 2
                        and cand.operands[0].type == capstone.arm.ARM_OP_REG
                        and cand.operands[0].reg == base_reg
                        and cand.operands[1].type == capstone.arm.ARM_OP_MEM
                        and cand.operands[1].mem.base == PC):
                    # o pool guarda o ENDERECO da tabela (uma indirecao)
                    pool = ((cand.address + 4) & ~3) + cand.operands[1].mem.disp
                    valor_pool = _ler32(rom.data, BASE, pool)
                    if valor_pool is not None and BASE <= valor_pool < BASE + len(rom.data):
                        tabela = valor_pool
                    break
            if tabela is None:
                padroes_crus["base da tabela nao veio do pool"] += 1
                continue
            com_base += 1
            valores = []
            for k in range(0, 64):
                v = _ler32(rom.data, BASE, tabela + 4 * k)
                if v is None or not _endereco_de_codigo(v, BASE, len(rom.data)):
                    break
                valores.append(v & ~1)
            if not valores:
                padroes_crus["tabela sem nenhuma entrada valida"] += 1
                continue
            entradas[len(valores)] += 1
            dentro = sum(1 for v in valores if v in desmontados)
            if dentro == len(valores):
                com_alvos_desmontados += 1
            guarda = None
            for atras in range(pos - 3, max(-1, pos - 16), -1):
                cand = lista[atras]
                if (cand.mnemonic.startswith("cmp") and len(cand.operands) == 2
                        and cand.operands[1].type == capstone.arm.ARM_OP_IMM):
                    guarda = cand.operands[1].imm
                    break
            if guarda is not None:
                conferencias["guarda cmp #%d == entradas" % guarda] += (
                    1 if guarda + 1 == len(valores) else 0)
                conferencias["guarda cmp #%d != entradas" % guarda] += (
                    1 if guarda + 1 != len(valores) else 0)
            if len(exemplos) < 8:
                exemplos.append({
                    "funcao": f"0x{funcao.entrada:08X}",
                    "mov_pc": f"0x{lista[pos].address:08X}",
                    "tabela": f"0x{tabela:08X}",
                    "indice": lista[pos - 3].mnemonic + " " + lista[pos - 3].op_str
                    if pos >= 3 else "?",
                    "entradas": len(valores),
                    "indice_x": deslocamento,
                    "alvos_ja_desmontados": f"{dentro}/{len(valores)}",
                    "primeiros_alvos": [f"0x{v:08X}" for v in valores[:4]],
                })
    return {
        "sitios_de_salto_calculado": total_sitios,
        "idioma_reconhecido": idioma_ok,
        "base_da_tabela_resolvida": com_base,
        "todas_as_entradas_ja_desmontadas": com_alvos_desmontados,
        "tamanho_das_tabelas": dict(entradas.most_common()),
        "padroes_nao_reconhecidos": dict(padroes_crus.most_common()),
        "conferencia_pelo_guarda": dict(conferencias.most_common(10)),
        "exemplos": exemplos,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("rom")
    parser.add_argument("--censo")
    args = parser.parse_args(argv)
    resultado = analisar(args.rom, args.censo)
    print(f"sitios de salto calculado .......: {resultado['sitios_de_salto_calculado']}")
    print(f"idioma add/ldr/mov pc ...........: {resultado['idioma_reconhecido']}")
    print(f"base da tabela resolvida ........: {resultado['base_da_tabela_resolvida']}")
    print(f"tabelas com TODOS os alvos ja "
          f"desmontados .....................: {resultado['todas_as_entradas_ja_desmontadas']}")
    print(f"tamanho das tabelas .............: {resultado['tamanho_das_tabelas']}")
    print(f"padroes nao reconhecidos ........: {resultado['padroes_nao_reconhecidos']}")
    print(f"conferencia pelo guarda cmp .....: {resultado['conferencia_pelo_guarda']}")
    print("\nexemplos:")
    for e in resultado["exemplos"]:
        print("  ", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
