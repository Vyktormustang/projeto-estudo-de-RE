"""Desmontador com descoberta recursiva para ARM7TDMI (GBA).

Ideia central: nao existe "desmontar a ROM" de forma confiavel por varredura
linear (dados sao lidos como codigo e vice-versa). O caminho honesto e seguir o
fluxo real de execucao a partir de um ponto de entrada conhecido:

    entrada -> ramificacoes -> chamadas (bl) -> destino das chamadas -> ...

e, a cada `ldr rX, [pc, #N]` (carregamento literal), olhar o que esta no pool:
se o valor parece um ponteiro de codigo (impar, dentro da ROM), ele tambem e
uma semente.

Toda decisao fica registrada: de onde veio cada semente, o que terminou cada
funcao, e o que ficou fora -- sem supor nada sobre trechos nunca alcancados.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import capstone
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, CS_OPT_DETAIL

from . import rom as rom_mod

# Grupos de instrucoes do capstone que interessam aqui.
GRUPO_SALTO = (capstone.CS_GRP_JUMP,)
GRUPO_CHAMADA = (capstone.CS_GRP_CALL,)
GRUPO_RETORNO = (capstone.CS_GRP_RET,)



# ---------------------------------------------------------------------------
# O alvo e ARM7TDMI (ARMv4T). Instrucao que NAO existe nessa arquitetura so
# pode significar uma coisa: a varredura entrou em DADOS e os leu como codigo
# (ou pulou para uma tabela). Em vez de levantar isso como se fosse codigo --
# o que produziria C bonito e completamente falso -- a varredura PARA ali e
# registra o motivo. Foi assim que apareceram `strd`, `cbnz`, `it`, `cdp2` e
# sufixos `.w` vindos de dados, com aparencia perfeitamente plausivel.
# ---------------------------------------------------------------------------
FORA_DO_ARM7TDMI = {
    "cdp2", "mcr2", "mrc2", "udf", "bkpt", "cbz", "cbnz", "ldrd", "strd",
    "sdiv", "udiv", "dmb", "dsb", "isb", "wfi", "wfe", "sev", "pld", "pli",
    "ldrex", "strex", "clz", "bfc", "bfi", "rev16", "revsh", "sxtb", "sxth",
    "uxtb", "uxth", "smlabb", "smlabt", "smlaltb", "smlaltt", "smulbb",
    "qadd", "qsub", "qdadd", "qdsub", "bxj", "eret", "rfe", "srs", "blx",
}
FORA_DO_V4T_SO_NO_THUMB = {
    "adr", "rev", "mrs", "msr", "umull", "umlal", "smull", "smlal", "swp",
    "swpb", "ldc", "stc", "mcr", "mrc", "cdp", "ldmib", "stmib", "mul",
}
SUFIXOS_THUMB2 = (".w", ".n")


def impossivel_no_arm7tdmi(ins, modo: str) -> str | None:
    """Motivo pelo qual a instrucao nao pode executar num ARM7TDMI, ou None."""
    mnemonic = ins.mnemonic.lower()
    for sufixo in SUFIXOS_THUMB2:
        if sufixo in mnemonic:
            return f"forma larga do Thumb-2 ({mnemonic})"
    base = mnemonic.split(".")[0]
    if base.startswith("it"):
        return f"IT block ({base}): nao existe no ARMv4T"
    if base in FORA_DO_ARM7TDMI:
        return f"{base}: instrucao inexistente no ARM7TDMI"
    for prefixo in ("ldc2", "stc2", "cdp2", "mcr2", "mrc2", "blx", "bxns", "vc"):
        if base.startswith(prefixo):
            return f"{base}: coprocessador 2 nao existe no ARM7TDMI"
    if modo == "thumb" and base in FORA_DO_V4T_SO_NO_THUMB:
        return f"{base}: existe no ARM do ARMv4T, mas nao no Thumb-1"
    return None

@dataclass
class Instrucao:
    """Uma instrucao desmontada."""

    endereco: int
    bytes_: bytes
    mnemonic: str
    operadores: str
    modo: str
    alvo: int | None = None      # destino imediato (desvio/chamada), quando existe

    def __str__(self) -> str:
        return (f"{self.endereco:08x}  {self.bytes_.hex():<10} "
                f"{self.mnemonic:<8} {self.operadores}").rstrip()


@dataclass
class FuncaoDesmontada:
    """Uma funcao descoberta, com o que se sabe dela."""

    entrada: int
    modo: str
    instrucoes: list[Instrucao] = field(default_factory=list)
    chamadas: list[tuple[int, int]] = field(default_factory=list)   # (end. bl, destino)
    terminacao: str = "indefinida"
    semente: str = "?"               # de onde veio esta funcao

    @property
    def fim(self) -> int:
        if not self.instrucoes:
            return self.entrada
        ultima = self.instrucoes[-1]
        return ultima.endereco + len(ultima.bytes_)

    @property
    def tamanho(self) -> int:
        return self.fim - self.entrada

    def texto(self) -> list[str]:
        cab = (f"func {self.entrada:08X} ({self.modo}, {self.tamanho} B, "
               f"semente: {self.semente}, fim: {self.terminacao})")
        return [cab] + [f"    {i}" for i in self.instrucoes]


@dataclass
class Desmontagem:
    """Resultado de uma descoberta recursiva."""

    base: int
    funcoes: dict[int, FuncaoDesmontada] = field(default_factory=dict)
    dados_lidos: dict[int, int] = field(default_factory=dict)      # pool -> valor
    avisos: list[str] = field(default_factory=list)

    @property
    def total_instrucoes(self) -> int:
        return sum(len(f.instrucoes) for f in self.funcoes.values())

    def arestas(self) -> list[tuple[int, int]]:
        """Grafo de chamadas (origem -> destino), sem duplicatas."""
        vistos, saida = set(), []
        for f in self.funcoes.values():
            for _, destino in f.chamadas:
                if (f.entrada, destino) not in vistos:
                    vistos.add((f.entrada, destino))
                    saida.append((f.entrada, destino))
        return sorted(saida)

    def texto(self) -> str:
        linhas = [f"desmontagem: {len(self.funcoes)} funcoes, "
                  f"{self.total_instrucoes} instrucoes, {len(self.arestas())} arestas"]
        for f in sorted(self.funcoes.values(), key=lambda x: x.entrada):
            linhas.extend(f.texto())
            linhas.append("")
        return "\n".join(linhas)

    def para_json(self) -> str:
        return json.dumps(
            {
                "base": f"0x{self.base:08X}",
                "funcoes": [
                    {
                        "entrada": f"0x{f.entrada:08X}",
                        "modo": f.modo,
                        "tamanho": f.tamanho,
                        "semente": f.semente,
                        "terminacao": f.terminacao,
                        "chamadas": [f"0x{d:08X}" for _, d in f.chamadas],
                        "instrucoes": [
                            {"endereco": f"0x{i.endereco:08X}", "bytes": i.bytes_.hex(),
                             "asm": f"{i.mnemonic} {i.operadores}".strip()}
                            for i in f.instrucoes
                        ],
                    }
                    for f in sorted(self.funcoes.values(), key=lambda x: x.entrada)
                ],
                "arestas": [[f"0x{a:08X}", f"0x{b:08X}"] for a, b in self.arestas()],
                "dados_lidos": {f"0x{k:08X}": f"0x{v:08X}" for k, v in self.dados_lidos.items()},
                "avisos": self.avisos,
            },
            indent=2,
            ensure_ascii=False,
        )


def _capstone(modo: str) -> Cs:
    cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB if modo == "thumb" else CS_MODE_ARM)
    cs.detail = True
    cs.skipdata = False
    return cs


def desmontar_por_sementes(
    imagem: bytes,
    base: int = rom_mod.ROM_BASE,
    sementes: dict[int, str] | None = None,
    seguir_pool: bool = True,
    max_funcoes: int = 20_000,
) -> Desmontagem:
    """Descoberta recursiva a partir das sementes informadas.

    `sementes` mapeia endereco (ja sem bit0) -> "thumb"/"arm". Se nada for dado,
    comeca pelo vetor de boot da imagem.
    """
    saida = Desmontagem(base=base)
    fila: list[tuple[int, str, str]] = []
    for endereco, modo in (sementes or {}).items():
        fila.append((endereco & ~1, modo, "informada"))

    if not fila:
        alvo = _entrada_de_boot(imagem, base)
        if alvo is None:
            # Numa ROM de GBA o processador SEMPRE comeca em ARM no inicio do
            # cartucho (0x08000000), com o branch de entrada nos 4 primeiros
            # bytes. A heuristica de 0xC0 pode falhar (a ROM de estudo tem zeros
            # ali), mas isso nao impede a descoberta -- entao o padrao e o reset.
            saida.avisos.append("sem stub em 0xC0; usando o vetor de reset "
                                "(0x08000000, ARM) como semente")
            fila.append((base, "arm", "vetor de reset"))
        else:
            # O vetor de boot e executado em ARM (`ldr r0,[pc,#0]; bx r0`), e o
            # bit0 do valor carregado diz o modo do destino -- convencao do ARM.
            fila.append((alvo & ~1, "thumb" if alvo & 1 else "arm", "vetor de boot"))

    while fila and len(saida.funcoes) < max_funcoes:
        entrada, modo, origem = fila.pop(0)
        if entrada in saida.funcoes or not (base <= entrada < base + len(imagem)):
            continue
        funcao, novas = _seguir_funcao(imagem, base, entrada, modo, origem,
                                       saida.dados_lidos if seguir_pool else None)
        saida.funcoes[entrada] = funcao
        for destino, modo_destino in novas.items():
            if destino not in saida.funcoes:
                fila.append((destino, modo_destino, f"referencia de 0x{entrada:08X}"))
    return saida


def _entrada_de_boot(imagem: bytes, base: int) -> int | None:
    """Le o vetor de boot (ARM em 0x000000C0 -> ldr r0,[pc,#0]; bx r0) se existir."""
    off = 0xC0 - (rom_mod.ROM_BASE - base)
    if off < 0 or off + 12 > len(imagem):
        return None
    palavra = int.from_bytes(imagem[off:off + 4], "little")
    if (palavra & 0xFFFF0FFF) != 0xE59F0000:
        return None                     # nao e `ldr r0, [pc, #0]`
    return int.from_bytes(imagem[off + 8:off + 12], "little")


def _seguir_funcao(imagem: bytes, base: int, entrada: int, modo: str, origem: str,
                   dados: dict[int, int] | None
                   ) -> tuple[FuncaoDesmontada, dict[int, str]]:
    """Percorre uma funcao ate o retorno, coletando chamadas e novas sementes.

    Ponto delicado ja verificado na pratica: o destino de um `bl` do Thumb vem
    SEM o bit0, entao o alvo e sempre PAR. Usar a paridade para decidir o modo
    desmonta a funcao inteira em ARM e produz lixo que PARECE codigo. A regra
    correta e herdar o modo de quem chama (`bl` do Thumb -> destino Thumb;
    `bl` do ARM -> destino ARM; so `blx` troca de modo).
    """
    cs = _capstone(modo)
    funcao = FuncaoDesmontada(entrada=entrada, modo=modo, semente=origem)
    novas: dict[int, str] = {}
    visitados: set[int] = set()
    pendente = [entrada]
    limite = base + len(imagem)

    while pendente:
        atual = pendente.pop()
        while base <= atual < limite and atual not in visitados:
            visitados.add(atual)
            instrucoes = list(cs.disasm(imagem[atual - base:atual - base + 4], atual, count=1))
            if not instrucoes:
                funcao.terminacao = f"codigo invalido em 0x{atual:08X}"
                break
            ins = instrucoes[0]
            motivo = impossivel_no_arm7tdmi(ins, modo)
            if motivo is not None:
                # Nao inventa codigo: registra onde parou e por que.
                funcao.terminacao = (f"parou em 0x{atual:08X}: {motivo} "
                                     f"(provavel dado lido como codigo)")
                break
            funcao.instrucoes.append(Instrucao(ins.address, ins.bytes,
                                               ins.mnemonic, ins.op_str, modo,
                                               alvo=_destino_imediato(ins)))

            # 1) `ldr rX, [pc, #N]` -> o valor do pool pode ser ponteiro de codigo
            if dados is not None:
                for destino in _literais(ins, modo):
                    valor = _ler32(imagem, base, destino)
                    if valor is None:
                        continue
                    dados[destino] = valor
                    apontado = _ponteiro_de_codigo(ins, valor, imagem, base, modo, cs)
                    if apontado:
                        endereco, modo_alvo = apontado
                        novas[endereco] = modo_alvo

            # 2) chamadas: destino entra na fila como nova funcao
            if ins.group(capstone.CS_GRP_CALL):
                alvo = _destino_imediato(ins)
                if alvo is not None:
                    funcao.chamadas.append((ins.address, alvo))
                    # modo: herda de quem chama; blx (ARM) troca para Thumb
                    modo_alvo = "thumb" if (modo == "thumb" or ins.mnemonic == "blx") else "arm"
                    novas[alvo & ~1] = modo_alvo
                atual = ins.address + len(ins.bytes)
                continue

            # 3) retornos: fim da funcao
            if _eh_retorno(ins):
                funcao.terminacao = f"{ins.mnemonic} {ins.op_str}".strip()
                break

            # 4) saltos: incondicional local continua; condicional anota e segue
            if ins.group(capstone.CS_GRP_JUMP):
                alvo = _destino_imediato(ins)
                if alvo is not None and not _condicional(ins):
                    if base <= alvo < limite:
                        atual = alvo
                        continue
                    funcao.terminacao = f"salto para fora: 0x{alvo:08X}"
                    break
                if alvo is not None and base <= alvo < limite:
                    pendente.append(alvo)
                if _termina_fluxo(ins):
                    funcao.terminacao = f"{ins.mnemonic} {ins.op_str}".strip()
                    break
            atual = ins.address + len(ins.bytes)

    if funcao.terminacao == "indefinida":
        funcao.terminacao = "limite de leitura (sem retorno encontrado)"
    funcao.instrucoes.sort(key=lambda i: i.endereco)
    return funcao, novas


def _ponteiro_de_codigo(ins, valor: int, imagem: bytes, base: int, modo: str, cs):
    """`ldr rX,[pc,#N]` + `bx rX` = chamada por tabela; o valor e ponteiro de codigo.

    Aqui SIM a paridade vale: o bit0 do valor diz o modo do destino (ARM/Thumb).
    Sem o par `ldr`+`bx`, um valor par nao e tratado como codigo (dado e dado).
    """
    if not (base <= (valor & ~1) < base + len(imagem)):
        return None
    if valor & 1:
        return valor & ~1, "thumb"
    if not _eh_retorno(ins) and _segue_bx(imagem, base, ins, modo, cs):
        return valor, "arm"
    return None


def _segue_bx(imagem: bytes, base: int, ins, modo: str, cs) -> bool:
    """A instrucao seguinte e `bx rX` para o MESMO registrador? (padrao de tabela)"""
    if ins.mnemonic != "ldr" or not ins.operands:
        return False
    destino = ins.operands[0].reg
    off = ins.address + len(ins.bytes) - base
    seguintes = list(cs.disasm(imagem[off:off + 4], ins.address + len(ins.bytes), count=1))
    return bool(seguintes) and seguintes[0].mnemonic == "bx" and \
        seguintes[0].operands and seguintes[0].operands[0].reg == destino


def _condicional(ins) -> bool:
    """Salto condicional (b<cond>, cbz, cbnz)?"""
    return ins.mnemonic.startswith("b") and ins.mnemonic not in ("b", "bl", "blx", "bx")


def _destino_imediato(ins) -> int | None:
    """Endereco absoluto alvo, quando o operando e imediato."""
    for operando in ins.operands:
        if operando.type == capstone.arm.ARM_OP_IMM:
            return operando.imm & 0xFFFFFFFF
    return None


def _literais(ins, modo: str) -> list[int]:
    """Enderecos de pool lidos por `ldr rX, [pc, #N]` (e `add rX, pc, #N`)."""
    pc = ins.address + (4 if modo == "thumb" else 8)
    alvos = []
    for operando in ins.operands:
        if operando.type != capstone.arm.ARM_OP_MEM:
            continue
        base_reg = getattr(operando.mem, "base", 0)
        if base_reg == capstone.arm.ARM_REG_PC:
            alvos.append((pc + operando.mem.disp) & 0xFFFFFFFC)
    return alvos


def _eh_retorno(ins) -> bool:
    """`bx lr`, `pop {..., pc}`, `mov pc, lr`, `ldr pc, [...]`."""
    if ins.mnemonic == "bx":
        return ins.op_str.strip() == "lr"
    if ins.mnemonic.startswith("pop") or ins.mnemonic.startswith("ldm"):
        return "pc" in ins.op_str
    if ins.mnemonic in ("mov", "add") and ins.op_str.startswith("pc,"):
        return True
    if ins.mnemonic == "ldr" and ins.op_str.startswith("pc,"):
        return True
    return False


def _termina_fluxo(ins) -> bool:
    """Instrucao que sempre encerra o fluxo local (branch incondicional indireto)."""
    return ins.mnemonic in ("bx", "blx") or (
        ins.mnemonic == "b" and _destino_imediato(ins) is None)


def _ler32(imagem: bytes, base: int, endereco: int) -> int | None:
    off = endereco - base
    if off < 0 or off + 4 > len(imagem):
        return None
    return int.from_bytes(imagem[off:off + 4], "little")
