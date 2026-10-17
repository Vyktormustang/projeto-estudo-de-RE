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
    # ARMv6 (saturacao e paralelismo de 16 bits): `ssat r4, #8, r0` foi lido numa
    # janela da ROM e o filtro dizia que a instrucao EXISTIA -- nao existe.
    "ssat", "usat", "ssat16", "usat16", "sel",
    "sadd8", "sadd16", "ssub8", "ssub16", "uadd8", "uadd16", "usub8", "usub16",
    "shadd8", "shadd16", "shsub8", "shsub16", "uhadd8", "uhadd16", "uhsub8",
    "uhsub16", "qadd8", "qadd16", "qsub8", "qsub16", "uadd8", "sxtb16", "uxtb16",
    "cdp2", "mcr2", "mrc2", "udf", "bkpt", "cbz", "cbnz", "ldrd", "strd",
    "sdiv", "udiv", "dmb", "dsb", "isb", "wfi", "wfe", "sev", "pld", "pli",
    "ldrex", "strex", "clz", "bfc", "bfi", "rev16", "revsh", "sxtb", "sxth",
    "uxtb", "uxth", "smlabb", "smlabt", "smlaltb", "smlaltt", "smulbb",
    "qadd", "qsub", "qdadd", "qdsub", "bxj", "eret", "rfe", "srs", "blx",
}
# ARMv5TE para cima, NOS DOIS MODOS -- familia DSP de multiplicacao (SMLAxy,
# SMULxy, SMULWy), `pkhtb`/`pkhbt` e `hint`. Medido na ROM: `orn sl, r7,
# #0x520052` (em 0x081A6798) e `smlawt r8, sl, ip, r0` (0x081C6CDC) chegavam ao
# lifter como "mnemonico nao implementado" -- como se fosse codigo do alvo que o
# lifter ainda nao cobre. Nao e': essas instrucoes nao EXISTEM no ARM7TDMI, entao
# ali a leitura passou por dado.
FORA_DO_ARMV4T_SEMPRE = {
    "orn", "orns", "hint", "pkhbt", "pkhtb",
    "smlabb", "smlabt", "smlatb", "smlatt", "smlalbb", "smlalbt", "smlaltb",
    "smlaltt", "smlawb", "smlawt", "smulbb", "smulbt", "smultb", "smultt",
    "smulwb", "smulwt", "smulwy", "smlalwy",
}
# Coprocessador: o ARM7TDMI DECODIFICA estas instrucoes e as deixa INDEFINIDAS
# quando nao ha coprocessador ligado -- e o GBA nao liga nenhum. Entao qualquer
# `ldc`/`stc`/`cdp`/`mcr`/`mrc` aqui e' dado lido como codigo, NOS DOIS MODOS.
# A pergunta e' por PREFIXO porque a forma vem colada no nome: a comparacao por
# igualdade deixou passar `ldcl` (3 vezes na ROM) e `stcl` (3 vezes). Medido: as 6
# estavam em janelas THUMB; em ARM nao ha nenhuma na ROM (varredura r17), mas a
# regra vale nos dois modos -- a mensagem "falta traduzir" seria falsa ali tambem.
# Conferido com keystone+capstone: `ldc`/`ldcl`/`stcl`/`cdp`/`mcr`/`mrc`/`ldc2`/
# `mcrr` decodificam com esses nomes, e nenhuma instrucao VALIDA do ARMv4T comeca
# com esses prefixos (nao ha' falso positivo).
FORMAS_DE_COPROCESSADOR = ("ldc", "stc", "cdp", "mcr", "mrc")
TAMANHO_THUMB1 = 2      # toda instrucao Thumb que o ARM7TDMI executa
TAMANHO_THUMB2 = 4      # codificacao de 32 bits: prefixos 11101/11110/11111


def forma_impossivel_no_thumb1(ins, modo: str) -> str | None:
    """Motivo para uma FORMA que nao existe no Thumb-1 -- sem mexer na leitura.

    Existe porque a mesma regra foi testada em dois papeis, e eles nao sao o
    mesmo:

      * como filtro do desmontador (que PARA a leitura no ponto), ela derruba a
        cobertura de forma medida: -46 475 instrucoes e -26 tabelas de casos na
        ROM de estudo, porque bloco de dado tem byte com cara de Thumb-2 e a
        leitura que parava no primeiro deles nao chegava mais ao codigo depois;
      * como motivo do lifter, ela so' troca um texto FALSO ("forma aritmetica nao
        implementada", como se faltasse implementar) por um verdadeiro (a
        instrucao nao existe no alvo: aqui a leitura passou por dado).

    Entao ela vive aqui: quem levanta o C pergunta, o desmontador nao. Medido na
    ROM: `adc r4, r4, #0xd000` (0x0845A3B6) e `adc r6, r4, #0xf00` (0x0845A3BA),
    em janelas Thumb, num trecho que termina em "codigo invalido". As duas tem
    QUATRO bytes; `44 f5 50 44` e' uma codificacao de 32 bits.
    """
    if modo != "thumb":
        return None
    # A pergunta certa e' sobre a CODIFICACAO, nao sobre o texto que o capstone
    # MOSTRA. Duas tentativas anteriores perguntaram pelo nome + pelos operandos
    # impressos, e as duas erraram feio (esta escrito aqui porque a terceira vez
    # seria a mesma coisa):
    #   * `lsls`/`lsrs`/`asrs` + imediato EXISTEM no Thumb-1 (formatos 1 e 3 do
    #     mapa de opcodes): a lista errada derrubou 11 testes e quebrou o
    #     reconhecimento das tabelas de casos (`lsls rI, rI, #2`);
    #   * `rsbs r0, r1, #0` e' o `neg` do Thumb-1, escrito em DOIS bytes (`48 42`):
    #     o `#0` que o capstone mostra nao esta codificado em lugar nenhum. A
    #     regra por operando marcou 1 750 instrucoes validas como inexistentes e
    #     o C levantado NAO COMPILOU (rodada r12 -- o erro era do filtro, nao da
    #     ROM).
    # O que separa os dois casos e' o tamanho: Thumb do ARM7TDMI e' 16 bits, e a
    # codificacao de 32 bits comeca com prefixos que no Thumb-1 sao indefinidos --
    # se a leitura chegou num deles, ela passou por dado.
    # EXCECAO MEDIDA: o `bl` do Thumb-1 TAMBEM e' uma codificacao de 32 bits
    # (prefixo 11110), e o ARM7TDMI executa -- e' assim que o Thumb chama
    # sub-rotina. Sem esta excecao a regra recusava 23 chamadas do corpus e o
    # levantado parava de reproduzir a verdade-terreno.
    if len(ins.bytes) >= TAMANHO_THUMB2 and ins.mnemonic.lower().split(".")[0] != "bl":
        return ("codificacao de 32 bits do Thumb-2: o ARM7TDMI executa so' as "
                "formas Thumb de 16 bits (e o `bl` de 32 bits, que o capstone "
                "escreve sem sufixo)")
    return None
# ATENCAO ao editar esta lista: agora que ela PARA a leitura (fim da funcao),
# uma entrada errada custa instrucoes de verdade. A versao anterior tinha "adr" e
# "mul", que EXISTEM no Thumb-1 -- e o estrago apareceu na medicao: **56 funcoes
# terminavam em `adr`** por causa disso. `02 a0` e' `adr r0, #8`, que no Thumb-1 e'
# `add r0, pc, #8`; `48 43` e' `muls r0, r1, r0`, do Thumb-1 tambem. O que NAO
# existe no Thumb-1 (e fica): `rev`/`swp`/`mrs`/`msr`/`umull`/`smull` (ARMv5),
# `ldmib`/`stmib` e `blx` (ARMv5T). As de COPROCESSADOR sairam daqui: elas sao
# dado nos DOIS modos, e quem responde por elas e' `FORMAS_DE_COPROCESSADOR`.
FORA_DO_V4T_SO_NO_THUMB = {
    "rev", "mrs", "msr", "umull", "umlal", "smull", "smlal", "swp",
    "swpb", "ldmib", "stmib",
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
    if base in FORA_DO_ARM7TDMI or base in FORA_DO_ARMV4T_SEMPRE:
        return f"{base}: instrucao inexistente no ARM7TDMI"
    # NEON/VFP: o ARM7TDMI do GBA nao tem FPU nem vetoriais. Qualquer mnemonic
    # comecando com "v" aqui e dado lido como codigo (visto: vhadd.u8, vrev64.8).
    if base.startswith("v"):
        return f"{base}: NEON/VFP nao existe no ARM7TDMI"
    for prefixo in ("addw", "subw", "movw", "movt", "sbfx", "ubfx", "bfi", "bfc",
                    "blx", "bxns", "vc"):
        if base.startswith(prefixo):
            return f"{base}: forma larga que nao existe no ARM7TDMI"
    if base.startswith(FORMAS_DE_COPROCESSADOR):
        # FORA do ramo do Thumb: vale nos dois modos (ver acima). O modo entra so'
        # no texto, porque a razao e' a mesma -- o GBA nao tem coprocessador.
        onde = "no Thumb-1" if modo == "thumb" else "no ARM do ARM7TDMI"
        return (f"{base}: coprocessador {onde} -- o GBA nao tem coprocessador "
                f"nenhum, entao a instrucao nao executa: aqui a leitura passou "
                f"por dado")
    if modo == "thumb":
        if base in FORA_DO_V4T_SO_NO_THUMB:
            return f"{base}: existe no ARM do ARMv4T, mas nao no Thumb-1"
        if base in ("stmdb", "ldmdb", "stmib", "ldmib"):
            return (f"{base}: no Thumb-1 os blocos so' existem como `push`/`pop`/"
                    f"`stmia`/`ldmia` -- isto e' a forma do Thumb-2")
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
    tabelas: list[TabelaCasos] = field(default_factory=list)
    # `mov pc, rX` em que o idioma de tabela de casos NAO foi reconhecido, com o
    # motivo MEDIDO (`_tabela_de_casos_ou_motivo`). Sem isto o relatorio so'
    # podia dizer "salto calculado nao reconhecido": as quatro recusas da ROM de
    # estudo parecem a mesma coisa de longe e nao sao.
    tabelas_recusadas: list[tuple[int, str]] = field(default_factory=list)
    # `adr`+`bx` de troca de modo cujo alvo NAO e' rotina: (site, alvo, modo do
    # alvo, forma, endereco de saida). Na ROM de estudo os dois casos sao ILHAS
    # de codigo ARM embutidas no corpo Thumb, e o endereco de saida cai DENTRO da
    # propria janela -- chamar de funcao perderia a continuacao.
    ilhas: list[tuple[int, int, str, str, int | None]] = field(default_factory=list)
    # Saltos para endereco ABAIXO da entrada: a leitura saiu desta funcao (bloco
    # comum de outra rotina). Ver a regra no ponto 4 de _seguir_funcao.
    saidas: list[tuple[int, int]] = field(default_factory=list)

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
        tabelas = [f"    {t.texto()}" for t in self.tabelas]
        saidas = [f"    saida: desvio em 0x{e:08X} -> 0x{a:08X} (fora da funcao, "
                  f"para tras)" for e, a in self.saidas]
        return [cab] + tabelas + saidas + [f"    {i}" for i in self.instrucoes]


@dataclass
class TabelaCasos:
    """Tabela de saltos lida da ROM (o `switch` que o compilador gerou).

    `alvos` sao os enderecos dos corpos dos casos, lidos da propria tabela -- nao
    deduzidos: se a tabela tem 6 entradas, foram lidos 6 enderecos da ROM.
    """

    endereco: int          # onde esta o `mov pc, rX`
    tabela: int            # endereco da tabela na imagem
    alvos: list[int]
    indice_endereco: int   # onde esta o `adds rI, rI, rB`
    indice_reg: int = -1   # registrador do indice (id do capstone)
    deslocamento: int | None = None
    # De onde saiu o numero de casos. O guarda do `switch` do compilador NAO e'
    # sempre `cmp rX, #k`: em duas tabelas da ROM de estudo (0x0805234C e
    # 0x08050F5C, 268 casos cada) o limite vem de um `ldr rY, [pc, #N]` e o
    # `cmp` compara com registrador -- o numero continua medivel (esta' na ROM),
    # mas so' se a sonda disser de onde ele veio.
    guarda: int | None = None
    guarda_fonte: str = ""

    def texto(self) -> str:
        escala = f", indice x{1 << self.deslocamento}" if self.deslocamento is not None else ""
        return (f"tabela de casos em 0x{self.tabela:08X}: {len(self.alvos)} casos{escala}; "
                f"salto em 0x{self.endereco:08X}; {self.guarda_fonte}")


@dataclass
class Descartado:
    """Endereco tentado como funcao que NAO tem codigo do ARM7TDMI no inicio.

    Existe por um motivo concreto: um ponteiro lido de pool (ou um desvio vindo
    de dado lido como codigo) pode apontar para uma tabela. O endereco entra na
    fila como candidato a funcao e nao decodifica -- nem como Thumb, nem como
    ARM -- ou decodifica para instrucao que o GBA nao tem (Thumb-2: `cbnz`,
    `it`, `addw`...). Antes isso virava uma "funcao" de corpo vazio que contava
    como completa: um erro silencioso. Agora nao entra na lista de funcoes e
    tambem nao desaparece -- fica aqui, com o motivo e os bytes, para auditoria.
    """

    entrada: int
    modo: str
    semente: str = "?"
    motivo: str = "?"
    bytes_: bytes = b""

    def texto(self) -> str:
        return (f"descartado 0x{self.entrada:08X} ({self.modo}, semente: {self.semente})"
                f": {self.motivo} | bytes iniciais: {self.bytes_.hex(' ')}")


@dataclass
class Desmontagem:
    """Resultado de uma descoberta recursiva."""

    base: int
    funcoes: dict[int, FuncaoDesmontada] = field(default_factory=dict)
    dados_lidos: dict[int, int] = field(default_factory=dict)      # pool -> valor
    descartes: dict[int, Descartado] = field(default_factory=dict)
    avisos: list[str] = field(default_factory=list)
    # Contabilidade da regra do salto para tras (ver _seguir_funcao, ponto 4):
    # quantos saltos sairam de uma funcao e quantos desses trechos, por nao
    # estarem cobertos por nenhuma outra, voltaram como semente propria.
    saidas_para_tras: int = 0
    saidas_recuperadas: int = 0

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
        recusadas = [item for f in self.funcoes.values() for item in f.tabelas_recusadas]
        if recusadas:
            tabelas = [t for f in self.funcoes.values() for t in f.tabelas]
            linhas.append(f"  tabelas de casos: {len(tabelas)} reconhecidas "
                          f"({sum(len(t.alvos) for t in tabelas)} casos lidos da ROM); "
                          f"{len(recusadas)} `mov pc, rX` recusados (motivo completo no JSON)")
        if self.descartes:
            linhas.append(f"  {len(self.descartes)} enderecos tentados como funcao e "
                          f"descartados: nenhuma instrucao valida do ARM7TDMI no inicio "
                          f"(provavel ponteiro para tabela; lista completa no JSON)")
        if self.saidas_para_tras:
            linhas.append(f"  {self.saidas_para_tras} saltos saem da funcao para tras "
                          f"(bloco comum de outra rotina); desses, "
                          f"{self.saidas_recuperadas} trechos nao cobertos por ninguem "
                          f"voltaram como semente propria")
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
                        "saidas": [f"0x{a:08X}" for _, a in f.saidas],
                        "tabelas": [
                            {"salto": f"0x{t.endereco:08X}", "tabela": f"0x{t.tabela:08X}",
                             "casos": len(t.alvos), "deslocamento": t.deslocamento,
                             "alvos": [f"0x{a:08X}" for a in t.alvos]}
                            for t in f.tabelas],
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
                "descartes": [
                    {"entrada": f"0x{d.entrada:08X}", "modo": d.modo, "semente": d.semente,
                     "motivo": d.motivo, "bytes": d.bytes_.hex(" ")}
                    for d in sorted(self.descartes.values(), key=lambda x: x.entrada)
                ],
                "saidas_para_tras": self.saidas_para_tras,
                "saidas_recuperadas": self.saidas_recuperadas,
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

    def _drenar_fila() -> None:
        """Processa a fila ate esvaziar (a fila e mutada aqui dentro)."""
        while fila and len(saida.funcoes) < max_funcoes:
            entrada, modo, origem = fila.pop(0)
            if (entrada in saida.funcoes or entrada in saida.descartes
                    or not (base <= entrada < base + len(imagem))):
                continue
            _uma_funcao(entrada, modo, origem)

    def _uma_funcao(entrada: int, modo: str, origem: str) -> None:
        funcao, novas, origens = _seguir_funcao(imagem, base, entrada, modo, origem,
                                                 saida.dados_lidos if seguir_pool else None)
        if not funcao.instrucoes:
            # NENHUMA instrucao do ARM7TDMI no endereco: isto nao e funcao.
            # Nao entra na lista (nao inventa codigo) e nao some (fica em
            # descartes com o motivo e os bytes). O bug que isto conserta: antes
            # essas entradas ficavam em `funcoes` com corpo vazio e, como nao
            # havia recusa nenhuma, contavam como COMPLETAS -- 83 funcoes
            # "levantadas" que nao tinham uma linha de C (achado por conferencia
            # do .c gerado contra o resumo impresso: 7634 + 83 = 7717).
            inicio = entrada - base
            saida.descartes[entrada] = Descartado(
                entrada=entrada, modo=modo, semente=origem,
                motivo=funcao.terminacao, bytes_=imagem[inicio:inicio + 8])
            return   # era `continue` quando este corpo era o proprio laco
        saida.funcoes[entrada] = funcao
        for destino, modo_destino in novas.items():
            if destino not in saida.funcoes and destino not in saida.descartes:
                fila.append((destino, modo_destino, origens.get(destino, "referencia")))

    _drenar_fila()

    # -- segunda passada: trecho alcancado SO por salto para tras -------------
    # A regra do ponto 4 impede uma funcao de engolir a anterior, mas o preco
    # seria deixar de fora um trecho alcancado apenas por um desses saltos. Aqui
    # ele volta como semente -- e SOMENTE se nenhuma funcao o cobriu, porque
    # recobrir e exatamente o defeito que a regra foi consertar. Cada passada
    # acrescenta funcoes ou descartes, entao isto termina.
    while True:
        cobertos = {i.endereco for f in saida.funcoes.values() for i in f.instrucoes}
        orfaos = sorted(
            {(alvo, f.modo, f"salto para tras em 0x{e:08X}")
             for f in saida.funcoes.values() for e, alvo in f.saidas
             if alvo not in cobertos and alvo not in saida.funcoes
             and alvo not in saida.descartes})
        if not orfaos:
            break
        fila.extend(orfaos)
        antes = len(saida.funcoes)
        _drenar_fila()
        saida.saidas_recuperadas += len(saida.funcoes) - antes

    saida.saidas_para_tras = sum(len(f.saidas) for f in saida.funcoes.values())
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
                   ) -> tuple[FuncaoDesmontada, dict[int, str], dict[int, str]]:
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
    origens: dict[int, str] = {}          # de onde veio cada candidato a funcao
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
                        origens[endereco] = (f"ponteiro de pool em "
                                             f"0x{ins.address:08X}")

            # 1b) `adr rD, #imm` + `bx rD` -> veneer de troca de modo
            veneer = _veneer_de_modo(ins, imagem, base, modo, cs)
            if veneer:
                endereco, modo_alvo, forma, saida = veneer
                if forma == "retorno":
                    # rotina do outro modo: devolve pelo `lr`, entao e' funcao
                    novas[endereco] = modo_alvo
                    origens[endereco] = (f"veneer `adr`+`bx` em 0x{ins.address:08X} "
                                         f"(troca para {modo_alvo})")
                else:
                    # ilha embutida (ou forma nao reconhecida): NAO vira funcao.
                    # Fica registrada com a medicao para a recusa poder dizer o
                    # que e' -- e para nao ser "consertada" por engano depois.
                    funcao.ilhas.append((ins.address, endereco, modo_alvo, forma, saida))

            # 2) chamadas: destino entra na fila como nova funcao
            if ins.group(capstone.CS_GRP_CALL):
                alvo = _destino_imediato(ins)
                if alvo is not None:
                    funcao.chamadas.append((ins.address, alvo))
                    # modo: herda de quem chama; blx (ARM) troca para Thumb
                    modo_alvo = "thumb" if (modo == "thumb" or ins.mnemonic == "blx") else "arm"
                    novas[alvo & ~1] = modo_alvo
                    origens[alvo & ~1] = (f"chamada ({ins.mnemonic}) em "
                                          f"0x{ins.address:08X}")
                atual = ins.address + len(ins.bytes)
                continue

            # 3) retornos: fim da funcao
            if _eh_retorno(ins):
                if _eh_salto_calculado(ins):
                    # `mov pc, rX`: salto calculado. Se for tabela de casos
                    # RECONHECIDA (criterios em _tabela_de_casos), os corpos dos
                    # casos sao parte DESTA funcao -- entram na fila, como os
                    # alvos de um desvio condicional. Sem isso eles ficam fora
                    # da desmontagem e a funcao nao tem como virar `switch`.
                    anteriores = sorted(
                        (i for i in funcao.instrucoes if i.endereco < ins.address),
                        key=lambda i: i.endereco)
                    tabela, por_que = _tabela_de_casos_ou_motivo(
                        imagem, base, anteriores, ins, cs)
                    if tabela is None:
                        funcao.tabelas_recusadas.append((ins.address, por_que))
                    if tabela is not None:
                        funcao.tabelas.append(tabela)
                        # Mesma regra do ponto 4: alvo de tabela abaixo da
                        # entrada e de OUTRA rotina (a tabela veio de dado lido
                        # como codigo, ou o `mov pc` pertence a rotina maior).
                        pendente.extend(a for a in tabela.alvos if a >= entrada)
                        funcao.saidas.extend((ins.address, a) for a in tabela.alvos
                                             if a < entrada)
                funcao.terminacao = f"{ins.mnemonic} {ins.op_str}".strip()
                break

            # 4) saltos: incondicional local continua; condicional anota e segue
            #
            # REGRA DO SALTO PARA TRAS (medida na ROM real, nao suposta): desvio
            # para endereco ABAIXO da entrada desta funcao nao e continuacao dela
            # -- e a leitura saindo para um bloco comum (o epilogo/laco de outra
            # rotina, ou o comeco de uma rotina maior que comeca antes). Seguir
            # esse salto produzia "funcoes" de 1 722 instrucoes que engoliam 651
            # instrucoes da funcao ANTERIOR: o mesmo endereco aparecia em tres
            # funcoes e, pior, o `push` que guarda o retorno estava antes da
            # entrada, entao o `pop {r1}; bx r1` do fim ficava sem marcador e
            # virava "desvio indireto por registrador sem origem conhecida" --
            # 65 dos 100 `bx rN` recusados vinham exatamente dai. Aqui o salto e
            # registrado como SAIDA (com o endereco de quem saltou) e a leitura
            # da corrente atual termina; os destinos que nao estiverem cobertos
            # por nenhuma outra funcao voltam como semente na segunda passada.
            if ins.group(capstone.CS_GRP_JUMP):
                alvo = _destino_imediato(ins)
                if alvo is not None and base <= alvo < entrada:
                    funcao.saidas.append((ins.address, alvo))
                    if not _condicional(ins):
                        funcao.terminacao = f"salto para fora (para tras): 0x{alvo:08X}"
                        break
                elif alvo is not None and not _condicional(ins):
                    if base <= alvo < limite:
                        atual = alvo
                        continue
                    funcao.terminacao = f"salto para fora: 0x{alvo:08X}"
                    break
                elif alvo is not None and base <= alvo < limite:
                    pendente.append(alvo)
                if _termina_fluxo(ins):
                    funcao.terminacao = f"{ins.mnemonic} {ins.op_str}".strip()
                    break
            atual = ins.address + len(ins.bytes)

    if funcao.terminacao == "indefinida":
        funcao.terminacao = "limite de leitura (sem retorno encontrado)"
    funcao.instrucoes.sort(key=lambda i: i.endereco)
    return funcao, novas, origens


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
    if ins.mnemonic not in ("ldr", "adr") or not ins.operands:
        return False
    destino = ins.operands[0].reg
    off = ins.address + len(ins.bytes) - base
    seguintes = list(cs.disasm(imagem[off:off + 4], ins.address + len(ins.bytes), count=1))
    return bool(seguintes) and seguintes[0].mnemonic == "bx" and \
        seguintes[0].operands and seguintes[0].operands[0].reg == destino


def _fim_do_bloco(endereco: int, modo: str, imagem: bytes, base: int,
                  limite: int = 600) -> tuple[str, int | None]:
    """Como o bloco que comeca em `endereco` termina? ("retorno" | "ilha" | "?").

    A pergunta existe porque o par `adr`+`bx` de troca de modo aparece em DUAS
    formas na ROM de estudo, e so' uma delas e' funcao:

      * `... ; bx lr` -- ROTINA do outro modo; ela devolve pelo `lr` de quem
        chamou a janela, entao o `bx` e' chamada de cauda (caso de 0x081DC014);
      * `add rD, pc, #imm` + `bx rD` -- o bloco sai para um endereco FIXO, e na
        ROM esse endereco cai DENTRO da propria janela que fez a troca
        (0x081DC0B0 volta para 0x081DC132; 0x081DC240 volta para 0x081DC43C).
        Isso e' ILHA de codigo ARM embutida no corpo Thumb -- nao funcao.
        Tratar como funcao e chamar de cauda PERDERIA a continuacao: o C
        devolveria r0 e nao executaria o resto da rotina.

    Medir isso antes de semear e' o que separa "fechei 3 recusas" de "escondi 3
    recusas atras de C errado".
    """
    cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB if modo == "thumb" else CS_MODE_ARM)
    cs.detail = True
    atual = endereco
    limite_addr = base + len(imagem)
    for _ in range(limite):
        if not (base <= atual < limite_addr):
            return "?", None
        lidas = list(cs.disasm(imagem[atual - base:atual - base + 4], atual, count=1))
        if not lidas:
            return "?", None
        ins = lidas[0]
        if impossivel_no_arm7tdmi(ins, modo) is not None:
            return "?", None
        if _eh_retorno(ins):
            return "retorno", None
        seguinte = list(cs.disasm(imagem[ins.address + len(ins.bytes) - base:
                                          ins.address + len(ins.bytes) - base + 4],
                                  ins.address + len(ins.bytes), count=1))
        # `add rD, pc, #imm` + `bx rD`: saida para endereco FIXO
        if (ins.mnemonic in ("add", "sub") and len(ins.operands) >= 3
                and ins.operands[1].type == capstone.arm.ARM_OP_REG
                and ins.operands[1].reg == capstone.arm.ARM_REG_PC
                and ins.operands[2].type == capstone.arm.ARM_OP_IMM
                and seguinte and seguinte[0].mnemonic == "bx"):
            pc = ins.address + (4 if modo == "thumb" else 8)
            valor = pc + ins.operands[2].imm
            if ins.mnemonic == "sub":
                valor = pc - ins.operands[2].imm
            return "ilha", valor
        if (ins.group(capstone.CS_GRP_JUMP) and not ins.group(capstone.CS_GRP_CALL)
                and not _condicional(ins)):
            # Salto INCONDICIONAL: seguir so' quando e' para a FRENTE e o alvo
            # esta' perto -- e' o idioma de "pular para o epilogo comum", que a
            # ilha 0x081DC240 usa (`beq` + `bl` + `b 0x081DC424`, e o epilogo em
            # 0x081DC424 termina em `add r0, pc, #1; bx r0`). Salto para tras ou
            # longe nao e' seguido: ali a forma nao pode ser prevista sem o
            # grafo, e prever seria adivinhar. Desvio CONDICIONAL continua sendo
            # seguido no fall-through -- a ilha 0x081DC0B0 tem um laco (`bgt`)
            # no meio do caminho para a saida.
            alvo = _destino_imediato(ins)
            if alvo is None or alvo <= ins.address or alvo - ins.address > 0x400:
                return "?", None
            atual = alvo
            continue
        atual = ins.address + len(ins.bytes)
    return "?", None


def _veneer_de_modo(ins, imagem: bytes, base: int, modo: str, cs):
    """`adr rD, #imm` + `bx rD` que troca de MODO: alvo, modo e forma do bloco.

    Este e' o idioma que o compilador usa para chamar codigo ARM de codigo Thumb
    (e vice-versa) sem `blx`: o `adr` calcula o destino e o `bx` troca de modo
    pelo bit0. Medido na ROM de estudo: **3 pares** no universo inteiro, todos
    Thumb->ARM (`0x081DC010`, `0x081DC0A4`).

    Mesmo modo NAO e' veneer: `adr` + `bx` para o proprio modo e' salto
    calculado (despacho), e semear ali leria como codigo um alvo que a leitura
    ainda nao alcancou por outro caminho. Alvo fora da imagem tambem nao:
    e' ponteiro de RAM/IO, e o destino so' existe em tempo de execucao.
    """
    if ins.mnemonic != "adr" or len(ins.operands) < 2:
        return None
    if ins.operands[1].type != capstone.arm.ARM_OP_IMM:
        return None
    pc = (ins.address + 4) & ~3 if modo == "thumb" else ins.address + 8
    valor = pc + ins.operands[1].imm
    if not (base <= (valor & ~1) < base + len(imagem)):
        return None
    modo_alvo = "thumb" if valor & 1 else "arm"
    if modo_alvo == modo:
        return None
    if not _segue_bx(imagem, base, ins, modo, cs):
        return None
    forma, saida = _fim_do_bloco(valor & ~1, modo_alvo, imagem, base)
    return valor & ~1, modo_alvo, forma, saida


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


def _eh_salto_calculado(ins) -> bool:
    """`mov pc, rX` / `add pc, rX` -- tabela de casos, nao retorno."""
    return (ins.mnemonic in ("mov", "add") and ins.op_str.startswith("pc,")
            and "lr" not in ins.op_str and "sp" not in ins.op_str)


def _operandos_de(imagem: bytes, base: int, instrucao, cs):
    """Re-desmonta UMA instrucao ja lida, so para ter os operandos do capstone."""
    off = instrucao.endereco - base
    lista = list(cs.disasm(imagem[off:off + len(instrucao.bytes_)],
                           instrucao.endereco, count=1))
    return lista[0] if lista else None


def _literal_do_pool(imagem: bytes, base: int, anteriores: list, registrador: int, cs):
    """Valor de um literal do pool carregado em `registrador` -- `(valor, pool)`.

    Existe porque o guarda do `switch` nao e' sempre `cmp rX, #k`. Medido na ROM
    de estudo (0x0805233C e 0x08050F4E):

        0x08052338  ldr r1, [pc, #0x18]   ; r1 = 0x0000010B, o LIMITE
        0x0805233C  cmp r5, r1
        0x0805233E  bls 0x08052344        ; dentro da faixa
        0x08052340  bl  0x08053774        ; fora da faixa: chama o tratamento

    O numero de casos continua vindo da ROM (nao de suposicao); o que muda e' o
    caminho ate ele. Devolve None quando o registrador nao foi carregado de um
    `ldr rY, [pc, #N]`.
    """
    for item in reversed(anteriores[-8:]):
        lida = _operandos_de(imagem, base, item, cs)
        if (lida is not None and lida.mnemonic.startswith("ldr")
                and len(lida.operands) == 2
                and lida.operands[0].type == capstone.arm.ARM_OP_REG
                and lida.operands[0].reg == registrador
                and lida.operands[1].type == capstone.arm.ARM_OP_MEM
                and lida.operands[1].mem.base == capstone.arm.ARM_REG_PC):
            pool = ((lida.address + 4) & ~3) + lida.operands[1].mem.disp
            valor = _ler32(imagem, base, pool)
            if valor is None:
                return None
            return valor, pool
    return None


def _tabela_de_casos(imagem: bytes, base: int, anteriores: list, ins, cs):
    """Reconhece o idioma de tabela de casos e devolve o que leu da ROM.

    Idioma (304 dos 306 sitios da ROM de estudo, ver ferramentas/estudo_switch.py):

        lsls rI, rI, #2          ; indice * 4
        ldr  rB, [pc, #N]        ; rB = base da tabela, vinda do pool
        adds rI, rI, rB          ; rI = indice*4 + base
        ldr  rI, [rI]            ; rI = tabela[indice]  <- endereco do caso
        mov  pc, rI              ; salto

    Criterios de aceitacao (sem eles isto seria adivinhacao):
      1. as tres instrucoes anteriores batem com o idioma, na ordem;
      2. a base da tabela vem de um `ldr rB, [pc, #N]` e o valor E um endereco
         dentro da imagem;
      3. TODAS as entradas lidas sao enderecos de codigo alinhados na imagem;
      4. existe um guarda `cmp rX, #k` antes, e k+1 E IGUAL ao numero de
         entradas lidas -- confirmacao independente: o guarda diz quantos casos
         existem, a tabela tem de ter exatamente essa quantidade;
      5. a primeira instrucao de cada alvo existe no ARM7TDMI (nao para no
         filtro de dado-lido-como-codigo).

    Devolve None se QUALQUER criterio falhar: ai a funcao continua marcada como
    parcial, em vez de o desmontador inventar codigo. O motivo MEDIDO de cada
    recusa sai por `_tabela_de_casos_ou_motivo` -- "nao reconheci" sem dizer o
    que foi medido ja' custou uma rodada neste projeto (o relatorio de desvio
    dizia "rotulo inexistente" para endereco desmontado).
    """
    return _tabela_de_casos_ou_motivo(imagem, base, anteriores, ins, cs)[0]


def _tabela_de_casos_ou_motivo(imagem: bytes, base: int, anteriores: list, ins, cs):
    """A mesma funcao, devolvendo `(tabela, motivo)` -- motivo vazio se aceitou.

    Existe para a sonda (`ferramentas/diagnosticar_tabela.py`) e para o relatorio:
    dizer "nao reconheci a tabela" nao distingue nada, e as quatro recusas da ROM
    de estudo parecem todas a mesma coisa de longe.
    """
    # ATENCAO: `anteriores` vem em ordem de ENDERECO, nao em ordem de travessia
    # -- a travessia segue desvios e volta, entao a lista da funcao nao esta
    # ordenada quando esta funcao e chamada (bug real: olhar para o fim da lista
    # nao reconheceu nenhuma das 309 tabelas).
    if len(anteriores) < 3:
        return None, (f"so' {len(anteriores)} instrucoes antes do "
                      f"`{ins.mnemonic} {ins.op_str}` nesta janela")
    anterior = _operandos_de(imagem, base, anteriores[-1], cs)
    antes = _operandos_de(imagem, base, anteriores[-2], cs)
    if anterior is None or antes is None:
        return None, (f"nao consegui reler as instrucoes anteriores "
                      f"(0x{anteriores[-2].endereco:08X}, "
                      f"0x{anteriores[-1].endereco:08X})")
    # `ldr rI, [rI]` (offset zero) e `adds rI, rI, rB`
    if not (anterior.mnemonic == "ldr" and len(anterior.operands) == 2
            and all(o.type == capstone.arm.ARM_OP_REG or o.type == capstone.arm.ARM_OP_MEM
                    for o in anterior.operands)
            and anterior.operands[0].type == capstone.arm.ARM_OP_REG
            and anterior.operands[1].type == capstone.arm.ARM_OP_MEM
            and anterior.operands[1].mem.base == anterior.operands[0].reg
            and anterior.operands[1].mem.disp == 0):
        return None, (f"a instrucao anterior a 0x{ins.address:08X} nao e' "
                      f"`ldr rI, [rI]` (medido: `{anterior.mnemonic} "
                      f"{anterior.op_str}` em 0x{anterior.address:08X})")
    if not (antes.mnemonic.startswith("add") and len(antes.operands) == 3
            and all(o.type == capstone.arm.ARM_OP_REG for o in antes.operands)
            and antes.operands[0].reg == antes.operands[1].reg
            and antes.operands[0].reg == anterior.operands[0].reg):
        return None, (f"a instrucao antes dela nao e' `adds rI, rI, rB` "
                      f"(medido: `{antes.mnemonic} {antes.op_str}` em "
                      f"0x{antes.address:08X})")
    registrador_base = antes.operands[2].reg
    registrador_indice = antes.operands[0].reg

    # onde o indice foi multiplicado (so para o comentario do C)
    deslocamento = None
    for atras in anteriores[-6:-2]:
        candidata = _operandos_de(imagem, base, atras, cs)
        if (candidata is not None and candidata.mnemonic.startswith("lsl")
                and len(candidata.operands) == 3
                and candidata.operands[0].type == capstone.arm.ARM_OP_REG
                and candidata.operands[0].reg == registrador_indice
                and candidata.operands[2].type == capstone.arm.ARM_OP_IMM):
            deslocamento = candidata.operands[2].imm
            break

    # a base da tabela vem de um `ldr rB, [pc, #N]` (dentro desta funcao)
    tabela = None
    for atras in reversed(anteriores[-40:]):
        candidata = _operandos_de(imagem, base, atras, cs)
        if (candidata is not None and candidata.mnemonic == "ldr"
                and len(candidata.operands) == 2
                and candidata.operands[0].type == capstone.arm.ARM_OP_REG
                and candidata.operands[0].reg == registrador_base
                and candidata.operands[1].type == capstone.arm.ARM_OP_MEM
                and candidata.operands[1].mem.base == capstone.arm.ARM_REG_PC):
            pool = ((candidata.address + 4) & ~3) + candidata.operands[1].mem.disp
            valor = _ler32(imagem, base, pool)
            if valor is not None and base <= valor < base + len(imagem):
                tabela = valor
            break
    if tabela is None:
        return None, ("nenhum `ldr rB, [pc, #N]` nas 40 instrucoes anteriores "
                      "carrega a base da tabela dentro da imagem")

    # guarda `cmp rX, #k` (imediato) ou `cmp rX, rY` com rY carregado de um
    # literal do pool -- diz quantos casos existem, sem depender da tabela
    guarda = None
    guarda_fonte = ""
    for posicao in range(len(anteriores) - 1, max(len(anteriores) - 18, 0) - 1, -1):
        atras = anteriores[posicao]
        candidata = _operandos_de(imagem, base, atras, cs)
        if (candidata is None or not candidata.mnemonic.startswith("cmp")
                or len(candidata.operands) != 2):
            continue
        segundo = candidata.operands[1]
        if segundo.type == capstone.arm.ARM_OP_IMM:
            guarda = segundo.imm
            guarda_fonte = f"guarda imediato em 0x{candidata.address:08X}"
            break
        if segundo.type != capstone.arm.ARM_OP_REG:
            continue
        # forma por registrador: so' vale se o proximo passo for um desvio
        # condicional (e' ele que usa o resultado do `cmp`) e se o limite vier de
        # um literal do pool, lido da ROM
        if posicao + 1 >= len(anteriores):
            continue
        seguinte = _operandos_de(imagem, base, anteriores[posicao + 1], cs)
        if (seguinte is None or not seguinte.group(capstone.CS_GRP_JUMP)
                or seguinte.mnemonic in ("b", "bl", "bx")):
            continue
        fonte = _literal_do_pool(imagem, base, anteriores[:posicao], segundo.reg, cs)
        if fonte is None:
            continue
        valor, pool = fonte
        if not 0 <= valor <= 0x10000:
            continue
        guarda = valor
        guarda_fonte = (f"guarda por registrador em 0x{candidata.address:08X}, "
                        f"limite 0x{valor:X} lido do pool em 0x{pool:08X}")
        break
    if guarda is None:
        return None, ("nao existe `cmp rX, #k` nem `cmp rX, rY` com rY vindo de "
                      "literal do pool nas 18 instrucoes anteriores: sem o guarda "
                      "nao ha como saber quantos casos a tabela tem")

    alvos = []
    for indice in range(guarda + 1):
        valor = _ler32(imagem, base, tabela + 4 * indice)
        if valor is None or not (base <= (valor & ~1) < base + len(imagem)):
            return None, (f"a entrada {indice} da tabela (0x{tabela:08X}, guarda "
                          f"`cmp rX, #0x{guarda:X}`) nao e' endereco de codigo "
                          f"dentro da imagem")
        alvos.append(valor & ~1)

    # cada alvo tem de comecar com instrucao que EXISTE no ARM7TDMI
    for indice, alvo in enumerate(alvos):
        inicio = alvo - base
        lidas = list(cs.disasm(imagem[inicio:inicio + 4], alvo, count=1))
        if not lidas:
            return None, (f"o alvo {indice} (0x{alvo:08X}) nao decodifica como "
                          f"instrucao")
        motivo = impossivel_no_arm7tdmi(lidas[0], "thumb")
        if motivo is not None:
            return None, (f"o alvo {indice} (0x{alvo:08X}) comeca em "
                          f"`{lidas[0].mnemonic} {lidas[0].op_str}`: {motivo}")

    return TabelaCasos(endereco=ins.address, tabela=tabela, alvos=alvos,
                       indice_endereco=antes.address, indice_reg=registrador_indice,
                       deslocamento=deslocamento, guarda=guarda,
                       guarda_fonte=guarda_fonte), ""


def _termina_fluxo(ins) -> bool:
    """Instrucao que sempre encerra o fluxo local (branch incondicional indireto)."""
    return ins.mnemonic in ("bx", "blx") or (
        ins.mnemonic == "b" and _destino_imediato(ins) is None)


def _ler32(imagem: bytes, base: int, endereco: int) -> int | None:
    off = endereco - base
    if off < 0 or off + 4 > len(imagem):
        return None
    return int.from_bytes(imagem[off:off + 4], "little")
