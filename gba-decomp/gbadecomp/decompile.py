"""Levantamento Thumb/ARM -> C, verificavel por execucao.

Criterio de honestidade deste modulo: ele NAO tenta adivinhar estruturas de alto
nivel (`if`, `while`, nomes de variaveis). Ele traduz instrucao por instrucao
para C equivalente -- registradores como variaveis, memoria endereçada de
verdade, desvios como `goto` -- e marca explicitamente tudo o que nao souber
traduzir. O que prova que a traducao esta certa nao e a leitura do C gerado: e
compilar esse C e rodar a MESMA tabela de verdade contra ele (`--verificar`).

Limite declarado: as flags sao recalculadas como variaveis (`z`, `n`, `c`, `v`)
na hora em que a instrucao as define, o que reproduz o comportamento observavel
naquele ponto; onde o ARM deixa a flag como imprevisivel, o comportamento e
anotado no comentario em vez de inventado.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import capstone
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB, CS_OPT_DETAIL

from . import disasm as disasm_mod
from . import rom as rom_mod

TIPOS_C = """typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed int s32;

static inline u32 carrega32(u32 end) { return *(volatile u32 *)end; }
static inline u16 carrega16(u32 end) { return *(volatile u16 *)end; }
static inline u8 carrega8(u32 end) { return *(volatile u8 *)end; }
static inline s32 carrega16s(u32 end) { return (s32)(*(volatile short *)end); }
static inline s32 carrega8s(u32 end) { return (s32)(*(volatile signed char *)end); }
static inline void guarda32(u32 end, u32 v) { *(volatile u32 *)end = v; }
static inline void guarda16(u32 end, u16 v) { *(volatile u16 *)end = v; }
static inline void guarda8(u32 end, u8 v) { *(volatile u8 *)end = v; }

/* Deslocamentos com o comportamento exato do ARM7TDMI (inclusive os casos que
   costumam ser esquecidos: n = 0 nao mexe em C; n = 32 e n > 32 tem regra
   propria; ASR satura no sinal). */
static inline u32 sh_lsl(u32 v, u32 n, u32 *pc) {
    if (n == 0) { return v; }
    if (n < 32) { *pc = (v >> (32 - n)) & 1; return v << n; }
    if (n == 32) { *pc = v & 1; return 0; }
    *pc = 0; return 0;
}
static inline u32 sh_lsr(u32 v, u32 n, u32 *pc) {
    if (n == 0) { return v; }
    if (n < 32) { *pc = (v >> (n - 1)) & 1; return v >> n; }
    if (n == 32) { *pc = (v >> 31) & 1; return 0; }
    *pc = 0; return 0;
}
static inline u32 sh_ror(u32 v, u32 n, u32 *pc) {
    if (n == 0) { return v; }
    n &= 31;
    if (n == 0) { *pc = (v >> 31) & 1; return v; }   /* 32 volta no mesmo lugar */
    { u32 r = (v >> n) | (v << (32 - n)); *pc = (r >> 31) & 1; return r; }
}
static inline u32 sh_asr(u32 v, u32 n, u32 *pc) {
    s32 s = (s32)v;
    if (n == 0) { return v; }
    if (n < 32) { *pc = ((u32)s >> (n - 1)) & 1; return (u32)(s >> n); }
    *pc = (v >> 31) & 1; return (u32)(s >> 31);
}

/* Pilha de trabalho EM MEMORIA DE VERDADE, dentro da IWRAM do GBA e longe da
   pilha do proprio harness (0x03007F00). Assim `str r0,[sp,#12]` funciona sem
   traducao especial, o transbordo de registrador para a pilha sai igual ao do
   hardware e a recursao funciona. g_erro acusa desbalanceamento na saida. */
/* Fronteira de BIOS: SWI/SVC nao e codigo do jogo, e chamada ao firmware do
   GBA. Fica declarada e NAO definida de proposito -- o link acusa onde a
   traducao para no limite da BIOS, em vez de inventar o que ela faz. */
u32 bios_svc(u32 numero, u32 r0, u32 r1, u32 r2, u32 r3);

#define PILHA_BASE 0x03005000u
#define PILHA_TOPO (PILHA_BASE + 0x800u)
static int g_erro;
"""

# Mnemonicos que DEFINEM flags (o 's' faz parte do nome). Em ARM, `add` nao
# define flags e `adds` define -- tratar os dois igual corrompe as flags e o
# desvio seguinte. Em Thumb-1 quase tudo define flags; `add`/`sub`/`mov` com
# registrador alto NAO definem.
# O capstone nomeia r9/r10/r11 como sb/sl/fp em parte dos modos. Sao OUTROS
# NOMES para os mesmos registradores: se o C declarasse `r10` e `sl` como
# variaveis separadas, o codigo leria uma e escreveria na outra -- erro que so
# aparece em execucao. Tudo e normalizado para r0..r12, sp, lr, pc.
ALIASES_REG = {"sb": "r9", "sl": "r10", "fp": "r11", "ip": "r12",
               "r13": "sp", "r14": "lr", "r15": "pc"}

SETA_FLAGS = {
    "movs", "adds", "subs", "adcs", "sbcs", "rsbs", "ands", "orrs", "eors",
    "bics", "mvns", "muls", "lsls", "lsrs", "asrs", "cmp", "cmn", "tst", "teq",
}
BASES_CONHECIDAS = SETA_FLAGS | {
    "mov", "add", "sub", "and", "orr", "eor", "bic", "mvn", "mul", "lsl", "lsr",
    "asr", "rsb", "adc", "sbc", "neg", "ldr", "ldrb", "ldrh", "ldrsb", "ldrsh",
    "str", "strb", "strh", "ldm", "ldmia", "stm", "stmia", "push", "pop", "nop",
    "svc", "swi", "bkpt", "mrs", "msr", "rev", "rev16", "revsh", "umull", "sdiv",
}

CONDICOES = {
    "eq": "z", "ne": "!z", "cs": "c", "hs": "c", "cc": "!c", "lo": "!c",
    "mi": "n", "pl": "!n", "vs": "v", "vc": "!v",
    "hi": "(c && !z)", "ls": "(!c || z)",
    "ge": "(n == v)", "lt": "(n != v)", "gt": "(!z && (n == v))", "le": "(z || (n != v))",
}


@dataclass
class FuncaoDec:
    """Uma funcao levantada para C."""

    endereco: int
    nome: str
    modo: str
    corpo: str
    nao_levantadas: list[str] = field(default_factory=list)
    externos: list[str] = field(default_factory=list)   # alvos de chamada sem corpo
    balanceamento: str = "desconhecido"
    # De ONDE veio esta janela de codigo (chamada, ponteiro de pool, salto para
    # tras...). Vai no cabecalho do C: sem isso, uma janela que comeca no MEIO
    # de um corpo parece funcao completa, e o C dela nao tem nem prologo.
    semente: str = "?"
    terminacao: str = "indefinida"                      # como o fluxo terminou
    declaracoes: list[str] = field(default_factory=list)  # temporarios do switch

    @property
    def completa(self) -> bool:
        return not self.nao_levantadas

    @property
    def tem_corpo(self) -> bool:
        return bool(self.corpo.strip())

    @property
    def parcial(self) -> bool:
        """Tem corpo, mas com lacuna registrada (ex.: salto calculado)."""
        return self.tem_corpo and not self.completa

    def assinatura(self) -> str:
        return f"u32 {self.nome}(u32 r0, u32 r1, u32 r2, u32 r3)"


def _terminacao_notavel(terminacao: str) -> bool:
    """A terminacao so interessa ao leitor quando NAO e um retorno normal.

    `bx lr` / `pop {pc}` / `mov pc, lr` sao o caso comum e nao dizem nada. Ja
    "parou em 0x...", "salto para fora", "codigo invalido" e "limite de leitura"
    sao informacao de verdade: dizem onde a leitura do fluxo parou e por que.
    """
    marcadores = ("parou em", "codigo invalido", "limite de leitura", "salto para fora")
    return any(m in terminacao for m in marcadores)


@dataclass
class CodigoC:
    """Resultado do levantamento de uma imagem inteira."""

    funcoes: list[FuncaoDec] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    chamadores: dict[str, list[str]] = field(default_factory=dict)

    @property
    def completas(self) -> list[FuncaoDec]:
        return [f for f in self.funcoes if f.completa]

    @property
    def incompletas(self) -> list[FuncaoDec]:
        """Funcoes sem corpo (so prototipo) -- nao ha C para ler."""
        return [f for f in self.funcoes if not f.completa]

    @property
    def parciais(self) -> list[FuncaoDec]:
        """Funcoes com corpo e lacuna marcada dentro do proprio C."""
        return [f for f in self.funcoes if f.parcial]

    def texto(self, nome_arquivo: str = "gbadecomp_lift.c") -> str:
        linhas = [
            "/* C levantado mecanicamente do binario pelo modulo decompile.py.",
            "   Sem nomes inventados e sem estruturas de alto nivel: uma instrucao",
            "   por linha, desvios como `goto`, flags explicitas. O nome de cada",
            "   funcao guarda o endereco de origem no binario (fn_08000258). */",
            "",
            TIPOS_C,
        ]
        # Prototipo para TODAS as funcoes (inclusive as nao levantadas): assim o
        # arquivo compila sozinho e o que falta fica explicito -- o link e que
        # acusa as que nao tem corpo, em vez de o compilador reclamar de chamada
        # sem declaracao e mascarar o problema.
        completas = [f for f in sorted(self.funcoes, key=lambda x: x.endereco) if f.completa]
        for f in sorted(self.funcoes, key=lambda x: x.endereco):
            if not f.tem_corpo:
                linhas.append(f"/* 0x{f.endereco:08X}: NAO levantada -- sem corpo aqui */")
                linhas.append(f"__attribute__((noinline, used)) "
                              f"u32 {f.nome}(u32 r0, u32 r1, u32 r2, u32 r3);")
        for f in sorted(self.funcoes, key=lambda x: x.endereco):
            # noinline+used: sem isso o compilador embute as funcoes nas chamadas
            # e elimina os simbolos, e a verificacao por endereco deixa de existir.
            linhas.append(f"__attribute__((noinline, used)) "
                          f"u32 {f.nome}(u32 r0, u32 r1, u32 r2, u32 r3);")
        externos = sorted({nome for f in self.funcoes for nome in f.externos})
        if externos:
            linhas.append("")
            linhas.append(f"/* {len(externos)} alvos de chamada que NAO foram "
                          f"descobertos como funcao (dado lido como codigo ou trecho "
                          f"nao alcancado): declarados, sem corpo. */")
            for nome in externos:
                linhas.append(f"u32 {nome}(u32 r0, u32 r1, u32 r2, u32 r3);")
        for f in sorted(self.funcoes, key=lambda x: x.endereco):
            if not f.tem_corpo:
                linhas.append(f"/* 0x{f.endereco:08X}: NAO levantada -- "
                              f"{'; '.join(f.nao_levantadas)} */")
                continue
            linhas.append("")
            if f.parcial:
                linhas.append(f"/* PARCIAL (0x{f.endereco:08X}): o corpo abaixo tem "
                              f"lacunas marcadas -- em execucao, marca g_erro:")
                for motivo in f.nao_levantadas[:6]:
                    linhas.append(f"     {motivo}")
                linhas.append("   */")
            quem_chama = self.chamadores.get(f.nome, [])
            if quem_chama:
                resumo = ", ".join(quem_chama[:6])
                if len(quem_chama) > 6:
                    resumo += f", ... (+{len(quem_chama) - 6})"
                linhas.append(f"/* chamada por {len(quem_chama)}: {resumo} */")
            origem = (f"/* origem: 0x{f.endereco:08X} ({f.modo}), "
                      f"semente: {f.semente}, pilha: {f.balanceamento}")
            if _terminacao_notavel(f.terminacao):
                origem += f", fim: {f.terminacao}"
            linhas.append(origem + " */")
            linhas.append(f"__attribute__((noinline, used)) "
                          f"u32 {f.nome}(u32 r0, u32 r1, u32 r2, u32 r3) {{")
            # Todos os registradores do ARM7TDMI viram variaveis C com o MESMO
            # nome que o desmontador usa (r0..r12, ip, lr, sp, pc). `lr` so
            # carrega o endereco de retorno salvo na pilha; o codigo levantado
            # nunca o desreferencia (o retorno real e `return r0;`).
            linhas.append("    u32 r4 = 0, r5 = 0, r6 = 0, r7 = 0, r8 = 0, "
                          "r9 = 0, r10 = 0, r11 = 0, r12 = 0, lr = 0;")
            # `pc` existe so para o C compilar: escrever em pc e RETORNO
            # (mov pc,lr / ldr pc,[sp]) ou desvio indireto -- e desvio indireto
            # nao e levantado em silencio, vira "nao levantada" com o motivo.
            linhas.append("    u32 pc = 0;  /* escrever em pc = retorno/desvio: "
                          "tratado explicitamente, ver comentarios */")
            linhas.append("    u32 z = 0, n = 0, c = 0, v = 0;")
            linhas.append("    u32 sp = PILHA_TOPO, sp0 = sp;")
            for declaracao in f.declaracoes:
                linhas.append(f"    {declaracao}")
            linhas.append("    (void)r1; (void)r2; (void)r3;")
            for linha in f.corpo.splitlines():
                linhas.append(f"    {linha}")
            linhas.append("    if (sp != sp0) { g_erro |= 1; }")
            linhas.append("    return r0;")
            linhas.append("}")
        linhas.append("")
        return "\n".join(linhas)


class _Emissor:
    """Traduz as instrucoes de UMA funcao para linhas de C."""

    def __init__(self, funcao, imagem: bytes, base: int, nomes: dict[int, str],
                 indice: "IndiceDeJanelas | None" = None):
        self.f = funcao
        self.imagem = imagem
        self.base = base
        self.nomes = nomes
        self.indice = indice
        self.linhas: list[str] = []
        self.nao_levantadas: list[str] = []
        self.rotulos: dict[int, str] = {}
        self.externos: set[str] = set()     # alvos de chamada sem funcao descoberta
        self._flags_recentes = None         # (indice da instrucao, descritor)
        self._indice_instrucao = 0
        self.lr_regs: set[str] = set()      # registradores que carregam o retorno
        # Modelo de pilha por endereco (mesma semantica do hardware): guarda, para
        # cada slot, se ali foi salvo o endereco de retorno.
        self.pilha: dict[int, str] = {}     # slot -> o que esta guardado ali
        self.sp_modelo = 0                  # espelho em Python do g_sp do C
        self.cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB if funcao.modo == "thumb" else CS_MODE_ARM)
        self.cs.detail = True
        # Rotulo SO para endereco que foi de fato desmontado dentro da funcao.
        # Marcar qualquer alvo do intervalo gerava `goto` para rotulo inexistente
        # (nao compila) quando aquele trecho nunca foi percorrido.
        desmontados = {i.endereco for i in funcao.instrucoes}
        self.enderecos_desmontados = desmontados
        for ins in funcao.instrucoes:
            if ins.alvo is not None and ins.alvo in desmontados:
                self.rotulos.setdefault(ins.alvo, f"L_{ins.alvo:08X}")
        # Tabelas de casos: cada alvo lido da tabela E um destino de salto, logo
        # precisa de rotulo (as instrucoes desses alvos foram desmontadas dentro
        # desta funcao -- o desmontador segue a tabela, ver disasm._tabela_de_casos).
        self.tabelas = {t.endereco: t for t in funcao.tabelas}
        # So emite `switch` quando da para fazer isso sem inventar: todos os
        # alvos precisam existir como endereco desmontado DESTA funcao (senao o
        # `goto` apontaria para rotulo inexistente e o C nao compilaria) e a
        # escala do indice precisa ter sido vista (o `lsls` antes da soma).
        self.tabelas_emitidas = {}
        for t in funcao.tabelas:
            if t.deslocamento is None or not all(a in desmontados for a in t.alvos):
                continue
            for alvo in t.alvos:
                self.rotulos.setdefault(alvo, f"L_{alvo:08X}")
            self.tabelas_emitidas[t.endereco] = t
        self.capturas = {t.indice_endereco: t for t in self.tabelas_emitidas.values()}

    # -- utilitarios ------------------------------------------------------
    def _rotulo(self, endereco: int) -> str:
        return self.rotulos.setdefault(endereco, f"L_{endereco:08X}")

    def _nome(self, id_registrador: int) -> str:
        return ALIASES_REG.get(self.cs.reg_name(id_registrador),
                               self.cs.reg_name(id_registrador))

    def _reg(self, operando) -> str:
        return self._nome(operando.reg)

    def _emitir(self, texto: str) -> None:
        self.linhas.append(texto)

    def levantar(self) -> FuncaoDec:
        # Invariante de honestidade: funcao sem instrucao nenhuma NAO pode sair
        # como "completa". Sem corpo e sem motivo, o resumo mentiria -- foi
        # exatamente o caso das 83 entradas fantasma da ROM real.
        if not self.f.instrucoes:
            self.nao_levantadas.append(
                "nenhuma instrucao desmontavel no endereco (bytes que nao sao "
                "codigo do ARM7TDMI)")
        for indice, ins in enumerate(self.f.instrucoes):
            self._indice_instrucao = indice
            if ins.endereco in self.rotulos:
                self._emitir(f"{self._rotulo(ins.endereco)}: ;")
            if ins.endereco in self.capturas:
                tabela = self.capturas[ins.endereco]
                # Guardar o indice ANTES do `adds` (que soma a base da tabela):
                # depois do `ldr rI, [rI]` o registrador ja nao tem mais o indice.
                self._emitir(f"idx_{tabela.endereco:08X} = "
                             f"{self._nome(tabela.indice_reg)};")
            try:
                decodificada = list(self.cs.disasm(ins.bytes_, ins.endereco, count=1))[0]
                self._traduzir(decodificada)
            except _NaoLevantado as exc:
                self.nao_levantadas.append(f"0x{ins.endereco:08X} {ins.mnemonic} "
                                           f"{ins.operadores}: {exc}")
                self._emitir(f"/* NAO LEVANTADO: {ins.mnemonic} {ins.operadores} */")
        return FuncaoDec(
            endereco=self.f.entrada,
            nome=self.nomes.get(self.f.entrada, f"fn_{self.f.entrada:08X}"),
            modo=self.f.modo,
            corpo="\n".join(l for l in self.linhas if l),
            nao_levantadas=self.nao_levantadas,
            externos=sorted(self.externos),
            balanceamento=("balanceada" if self.sp_modelo == 0
                           else f"desequilibrada ({self.sp_modelo} slots)"),
            semente=self.f.semente,
            terminacao=self.f.terminacao,
            declaracoes=[f"u32 idx_{t.endereco:08X} = 0;  /* indice da tabela de "
                         f"casos em 0x{t.tabela:08X} */"
                         for t in sorted(self.tabelas_emitidas.values(),
                                         key=lambda x: x.endereco)],
        )

    # -- traducao ---------------------------------------------------------
    def _traduzir(self, ins) -> None:
        """Traduz UMA instrucao, ja tratando condicao (ARM) e definicao de flags."""
        completo = ins.mnemonic
        cond, base, define_flags = _separar_condicao(completo, self.f.modo)
        self._condicao = cond
        self._define_flags = define_flags
        # Nao limpar aqui: o teste de indice (`indice_atual - 1`) ja garante que
        # so a instrucao IMEDIATAMENTE anterior pode ser fundida.
        antes = len(self.linhas)
        try:
            self._traduzir_base(ins, base)
        finally:
            self._condicao = None
            self._define_flags = False
        if cond and define_flags:
            # `addeq`/`subsne`... so mexe nas flags se a condicao valer: depois
            # disso, fundir o desvio seguinte com estes operandos seria errado.
            self._flags_recentes = None
        if cond and len(self.linhas) > antes:
            # Instrucao condicional no ARM: so executa (e so mexe em flags) se a
            # condicao valer. Envolver em `if` preserva as duas coisas.
            corpo = self.linhas[antes:]
            del self.linhas[antes:]
            self.linhas.append(f"if ({CONDICOES[cond]}) {{")
            self.linhas.extend(f"    {linha}" for linha in corpo)
            self.linhas.append("}")

    def _traduzir_base(self, ins, m: str) -> None:
        op = ins.operands

        # Antes de QUALQUER despacho por mnemonico: a FORMA da instrucao existe
        # no alvo? O `adc` existe no ARMv4T (o mnemonic cai num tratador mais
        # abaixo) e mesmo assim `adc r4, r4, #0xd000` e' do Thumb-2 -- se a
        # checagem ficasse so no fim da cadeia, o tratador responderia "forma
        # aritmetica nao implementada" e a resposta seria falsa (sugere falta de
        # trabalho no levantador, quando o que houve foi leitura passando por
        # dado). Medido: 0x0845A3B6 e 0x0845A3BA na ROM de estudo.
        forma_impossivel = disasm_mod.forma_impossivel_no_thumb1(ins, self.f.modo)
        if forma_impossivel is not None:
            raise _NaoLevantado(
                f"instrucao que nao existe no ARM7TDMI ({forma_impossivel}): "
                f"aqui a leitura passou por dado, nao por codigo")

        if m in ("push", "pop"):
            return self._pilha(ins, m)
        if m in ("b", "bl", "blx") or m in [f"b{c}" for c in CONDICOES]:
            return self._desvio(ins)
        if m.startswith("ldr") and op and self._reg(op[0]) == "pc":
            # Epilogo classico do compilador ARM: `ldr pc, [sp], #4`.
            alvo = next((o for o in op if o.type == capstone.arm.ARM_OP_MEM), None)
            if alvo is not None and self._nome(alvo.mem.base) in ("sp", "lr"):
                self._emitir("return r0;  /* ldr pc = retorno */")
                return
            raise _NaoLevantado("ldr em pc (salto por tabela nao modelado)")
        if m.startswith("ldr") or m.startswith("str"):
            return self._memoria(ins, m)
        if m == "bx":
            return self._bx(ins)
        if m in ("movs", "mov"):
            if self._reg(op[0]) == "pc":
                origem = self._nome(op[1].reg) if op[1].type == capstone.arm.ARM_OP_REG \
                    else "?"
                if origem == "lr":
                    self._emitir("return r0;  /* mov pc, lr */")
                    return
                # `mov pc, rN` = salto CALCULADO (tabela de casos). Quando a
                # tabela foi RECONHECIDA e lida da ROM (criterios em
                # disasm._tabela_de_casos), o C sai com `switch` de verdade e os
                # destinos que o proprio binario declara. Quando nao, traduzir
                # como atribuicao seria mentira silenciosa: fica marcado e a
                # funcao sai PARCIAL.
                tabela = self.tabelas_emitidas.get(ins.address)
                if tabela is not None and tabela.deslocamento is None:
                    # A tabela foi reconhecida mas o `lsls rI, rI, #N` que escala o
                    # indice nao ficou medido: sem ele a escala do `switch` seria
                    # suposicao. (Antes disto, `1 << None` estourava TypeError -- o
                    # caminho so' nao apareceu porque nenhuma das 375 tabelas da ROM
                    # de estudo chega aqui sem deslocamento medido.)
                    raise _NaoLevantado("tabela de casos reconhecida sem o `lsls` "
                                        "do indice: escala nao medida")
                if tabela is not None:
                    self._emitir(f"/* tabela de casos em 0x{tabela.tabela:08X}: "
                                 f"{len(tabela.alvos)} casos lidos da ROM "
                                 f"(indice x{1 << tabela.deslocamento}); "
                                 f"{_comentario(tabela.guarda_fonte)} */")
                    self._emitir(f"switch (idx_{tabela.endereco:08X} >> "
                                 f"{tabela.deslocamento}) {{")
                    for numero, destino in enumerate(tabela.alvos):
                        self._emitir(f"    case {numero}: goto {self._rotulo(destino)};")
                    self._emitir("    default: g_erro |= 2; break;   /* fora da tabela */")
                    self._emitir("}")
                    self._emitir("return r0;   /* inalcancavel: todo caso salta */")
                    return
                self._emitir(f"/* PC calculado em {origem}: tabela de casos nao "
                             f"reconhecida */")
                self._emitir("g_erro |= 2;")
                self._emitir("return r0;")
                self.nao_levantadas.append(
                    f"0x{ins.address:08X} mov pc, {origem}: salto calculado "
                    f"(tabela de casos) nao modelado")
                return
            destino, fonte = self._reg(op[0]), op[1]
            if fonte.type == capstone.arm.ARM_OP_IMM:
                self._emitir(f"{destino} = 0x{fonte.imm & 0xFFFFFFFF:X}u;")
            else:
                self._emitir(f"{destino} = {self._reg(fonte)};")
            if self._define_flags:
                self._flags_logicas(destino)
            return
        if m in ("adds", "subs", "cmp", "cmn", "add", "sub", "adcs", "sbcs",
                 "rsbs", "rsb", "adc", "sbc"):
            return self._aritmetica(ins, m)
        if m in ("ands", "orrs", "eors", "bics", "mvns", "tst", "teq", "and",
                 "orr", "eor", "bic", "mvn"):
            return self._logica(ins, m)
        if m in ("lsls", "lsrs", "asrs", "lsl", "lsr", "asr", "ror", "rors",
                 "rorn"):
            return self._deslocamento(ins, m)
        if m in ("muls", "mul"):
            # ATENCAO: `muls Rd, Rn, Rm` (3 operandos, forma que o compilador
            # emite) calcula Rn * Rm e grava em Rd -- NAO e Rd * Rn. Na forma de
            # 2 operandos (Thumb/ARM `mul Rd, Rm`) e que Rd entra na conta.
            destino = self._reg(op[0])
            a, b = ((self._reg(op[1]), self._reg(op[2])) if len(op) >= 3
                    else (self._reg(op[0]), self._reg(op[1])))
            self._emitir(f"{destino} = {a} * {b};")
            if self._define_flags:
                # No ARM7TDMI o MUL define N e Z; C e V ficam IMPREVISIVEIS.
                # Nao inventamos valor para eles: so N e Z sao atualizados.
                self._emitir(f"z = ({destino} == 0); n = ({destino} >> 31);")
            return
        if m in ("stm", "stmia", "ldm", "ldmia"):
            return self._multipla(ins, m)
        if m in ("svc", "swi"):
            numero = (op[0].imm if op and op[0].type == capstone.arm.ARM_OP_IMM else 0)
            self._emitir(f"r0 = bios_svc(0x{numero:X}u, r0, r1, r2, r3);  "
                         f"/* chamada de BIOS */")
            return
        if m in ("ror", "rors", "rorn"):
            return self._deslocamento(ins, "asrs" if False else m)
        if m == "adr":
            return self._adr(ins)
        if m == "nop":
            self._emitir(";")
            return
        # Nao e' tudo "nao implementado": instrucao que NAO EXISTE no ARM7TDMI e'
        # outra coisa -- e' dado lido como codigo, e dizer "falta implementar"
        # manda quem le procurar defeito no lifter (mesmo defeito de relato do
        # desvio para fora: 20 das 189 lacunas diziam isso).
        impossivel = disasm_mod.impossivel_no_arm7tdmi(ins, self.f.modo)
        if impossivel is not None:
            raise _NaoLevantado(
                f"instrucao que nao existe no ARM7TDMI ({impossivel}): aqui a "
                f"leitura passou por dado, nao por codigo")
        raise _NaoLevantado("mnemonico nao implementado (a instrucao existe no "
                            "ARMv4T; falta traduzir)")

    def _adr(self, ins) -> None:
        """`adr rD, #imm` -- o endereco e' calculado a partir do PC desta instrucao.

        No Thumb-1 `adr` e' `add rD, pc, #imm*4` e o PC vale (endereco + 4) com o
        bit 1 zerado; no ARM, endereco + 8. O valor e' uma CONSTANTE conhecida em
        tempo de traducao (nao ha carga nenhuma), por isso sai como literal -- do
        mesmo jeito que o literal lido do pool, para o C ficar legivel.
        Medido na ROM de estudo: 168 ocorrencias, todas em janelas Thumb, e todas
        recusadas antes disto.
        """
        op = ins.operands
        if (not op or op[0].type != capstone.arm.ARM_OP_REG
                or len(op) < 2 or op[1].type != capstone.arm.ARM_OP_IMM):
            raise _NaoLevantado("adr sem registrador e imediato")
        pc = (ins.address + 4) & ~3 if self.f.modo == "thumb" else ins.address + 8
        valor = pc + op[1].imm
        self._emitir(f"{self._reg(op[0])} = 0x{valor:08X}u;  "
                     f"/* adr: pc 0x{pc:08X} + 0x{op[1].imm:X} */")

    def _flags_logicas(self, resultado: str) -> None:
        self._emitir(f"z = ({resultado} == 0); n = ({resultado} >> 31);")
        self._anotar_flags(("resultado", resultado))

    def _anotar_flags(self, descritor) -> None:
        """Guarda como a condicao do desvio seguinte pode ser escrita direto."""
        self._flags_recentes = (self._indice_instrucao, descritor)

    def _limpar_flags(self) -> None:
        self._flags_recentes = None

    def _retornar(self) -> None:
        """Saida da funcao com conferencia de balanceamento da pilha."""
        self._emitir("if (sp != sp0) { g_erro |= 1; }")
        self._emitir("return r0;")

    def _pilha(self, ins, m) -> None:
        """PUSH/POP com a semantica exata do ARM7TDMI.

        Detalhe que ja causou erro aqui: o PUSH **desce** o sp e grava em
        enderecos crescentes (sp -= 4n; mem[sp] = 1o da lista; mem[sp+4] = 2o...).
        Por isso `push {r7,lr}` seguido de `pop {r7}` devolve o r7 (o endereco
        mais baixo) e o `pop {r1}` seguinte devolve o lr. Tratar a pilha como
        "LIFO classico" inverte tudo.
        """
        regs = [self._reg(o) for o in ins.operands if o.type == capstone.arm.ARM_OP_REG]
        n = len(regs)
        if m == "push":
            self._emitir(f"sp -= {4 * n};")
            for indice, r in enumerate(regs):
                self._emitir(f"guarda32(sp + {4 * indice}, {r});")
                self.pilha[self.sp_modelo - n + indice] = "retorno" if r == "lr" else r
            self.sp_modelo -= n
            return
        for indice, r in enumerate(regs):
            marcador = self.pilha.get(self.sp_modelo + indice)
            if r == "pc":
                self._emitir(f"sp += {4 * n};")
                self.sp_modelo += n
                self._retornar()
                return
            if r == "lr":
                self._emitir(f"(void)carrega32(sp + {4 * indice});")
                continue
            self._emitir(f"{r} = carrega32(sp + {4 * indice});")
            if marcador == "retorno":
                # `pop {r1}; bx r1` e como o codigo compilado volta: o
                # registrador recem-carregado carrega o endereco de retorno.
                self.lr_regs.add(r)
        self._emitir(f"sp += {4 * n};")
        self.sp_modelo += n

    def _bx(self, ins) -> None:
        r = self._reg(ins.operands[0])
        if r == "lr" or r in self.lr_regs:
            self._emitir("return r0;")
            return
        # SEGUNDO CAMINHO, e o que mais aparece na ROM real: `pop {rN}` (ou
        # `ldr rN, [sp, ...]`) IMEDIATAMENTE antes do `bx rN`. Este e o epilogo
        # padrao de quem compila para ARM7TDMI: em vez de `pop {pc}`, o retorno
        # passa por um registrador baixo, porque `bx` aceita registrador baixo
        # nos dois modos. Aceitar isso NAO depende do livro-caixa de slots, que
        # so fica correto quando a leitura comeca na ENTRADA da funcao -- e
        # 61 dos 96 `bx` recusados estavam em janelas que comecam no meio do
        # corpo (endereco lido de tabela de dados), onde o `push` do `lr` nao
        # existe dentro do trecho lido. A condicao e' mecanica: quem carrega o
        # registrador e' uma leitura DA PILHA, e a instrucao e' a anterior.
        anterior = self._anterior()
        if anterior is not None and _carrega_da_pilha(anterior, r):
            self._emitir(f"/* retorno pelo valor que o `{anterior.mnemonic}` "
                         f"tirou da pilha */")
            self._emitir("return r0;")
            return
        raise _NaoLevantado(self._motivo_bx_sem_origem())

    def _motivo_bx_sem_origem(self) -> str:
        """Por que este `bx rN` nao vira C -- dito com precisao, caso a caso.

        Tres situacoes MUITO diferentes caem no mesmo "sem origem conhecida", e
        junta-las faz o relatorio enganar quem le: parece falha do levantador o
        que na verdade e' uma construcao que nao tem traducao literal (o alvo e'
        um PARAMETRO, por desenho). Medido na ROM de estudo:
          * janelas de 4 bytes `bx rN` + nop (`mov r8, r8`), alinhadas a cada 4
            bytes em 0x081E3BA8.., chamadas por `bl` de dezenas de sitios: sao
            thunks "chame pelo registrador N" -- o destino vem de quem chamou;
          * `stmdb sp!, {lr}` + `add lr, pc, #0` + `bx rN` (ARM): chamada
            indireta ARM->Thumb com o endereco de retorno montado a mao (o
            `add lr, pc, #0` marca o bit do modo Thumb).
        """
        if self._indice_instrucao == 0:
            return ("thunk de salto indireto: a janela comeca em `bx rN` (com nop "
                    "de alinhamento), ou seja o destino vem NO REGISTRADOR, de "
                    "quem chamou -- traduzir exigiria inventar a assinatura")
        anterior = self._anterior()
        if anterior is not None and _monta_retorno_a_mao(anterior):
            return ("chamada indireta ARM->Thumb montada a mao (`stmdb sp!, {lr}` + "
                    "`add lr, pc, #0` + `bx rN`): o alvo veio de dado lido na ROM, "
                    "sem assinatura declarada")
        return "desvio indireto por registrador sem origem conhecida"

    def _motivo_saida(self, alvo: int, verbo: str) -> str:
        """Uma frase que diz o que foi MEDIDO sobre o destino, nao o que se supoe.

        Antes: "desvio para 0x..., que nao foi desmontado (rotulo inexistente)".
        Medido na ROM: 29 dos 130 desvios recusados apontavam para endereco
        DESMONTADO (em outra janela) -- a frase era falsa justamente sobre o
        proprio levantamento. Agora: onde o endereco esta', verificado no indice.
        """
        para_tras = _saida_para_tras(alvo, self.f.entrada)
        if para_tras:
            return f"{para_tras} -- {self._onde_esta(alvo)}"
        if verbo == "salto":
            return f"salto para fora da funcao (0x{alvo:08X}): {self._onde_esta(alvo)}"
        return (f"desvio para 0x{alvo:08X}, sem rotulo nesta janela: "
                f"{self._onde_esta(alvo)}")

    def _onde_esta(self, alvo: int) -> str:
        """Onde o destino do desvio esta desmontado -- ou se nao esta em lugar nenhum."""
        if self.indice is None:
            return "destino nao desmontado"
        return self.indice.descrever(alvo, self.f.entrada, self.f.fim)

    def _anterior(self):
        """Instrucao imediatamente anterior NA ORDEM EMITIDA (nao por endereco)."""
        indice = self._indice_instrucao - 1
        if 0 <= indice < len(self.f.instrucoes):
            return self.f.instrucoes[indice]
        return None

    def _desvio(self, ins) -> None:
        alvo = ins.operands[0].imm & 0xFFFFFFFF
        if ins.mnemonic == "b":
            # Tem de ser o conjunto de enderecos REALMENTE desmontados, nao o
            # intervalo da funcao: dentro do intervalo pode haver buraco (dado
            # entre trechos de codigo) e o `goto` sairia sem rotulo -- o C nao
            # compila. Buraco + funcao conhecida = chamada de cauda.
            if alvo in self.enderecos_desmontados:
                self._emitir(f"goto {self._rotulo(alvo)};")
            elif alvo in self.nomes:
                # Salto para a ENTRADA de outra funcao = chamada de cauda.
                self._emitir(f"/* chamada de cauda para 0x{alvo:08X} */")
                self._emitir(f"r0 = {self.nomes[alvo]}(r0, r1, r2, r3);")
                self._emitir("return r0;")
            else:
                raise _NaoLevantado(self._motivo_saida(alvo, "salto"))
            return
        if ins.mnemonic in ("bl", "blx"):
            if (alvo & ~1) not in self.nomes:
                # Chamada para endereco que NAO foi descoberto como funcao (dado
                # lido como codigo ou trecho nao alcancado). Fica declarada e sem
                # corpo -- o link acusa, em vez de o C fingir que existe.
                self.externos.add(f"fn_{alvo & ~1:08X}")
            destino = self.nomes.get(alvo & ~1, f"fn_{alvo & ~1:08X}")
            fora = "externo" if alvo & ~1 not in self.nomes else "no modulo"
            self._emitir(f"/* bl 0x{alvo:08X} ({fora}) */")
            self._emitir(f"r0 = {destino}(r0, r1, r2, r3);")
            return
        sufixo = ins.mnemonic[1:]
        cond = CONDICOES.get(sufixo)
        if cond is None:
            raise _NaoLevantado("condicao desconhecida")
        # Fusao de flags: se o desvio vem IMEDIATAMENTE depois da instrucao que
        # define as flags, a condicao pode ser escrita direto sobre os operandos
        # (`if ((s32)r0 >= (s32)r1)`) em vez de testar z/n/c/v. So vale quando e
        # a instrucao seguinte -- com instrucoes no meio os operandos podem ter
        # mudado, e ai o teste das flags continua sendo a unica leitura correta.
        if self._flags_recentes and self._flags_recentes[0] == self._indice_instrucao - 1:
            direta = _condicao_direta(sufixo, self._flags_recentes[1])
            if direta:
                alvo_certo = (alvo in self.enderecos_desmontados)
                if alvo_certo:
                    self._emitir(f"if ({direta}) goto {self._rotulo(alvo)};")
                    return
        if alvo not in self.enderecos_desmontados:
            if alvo in self.nomes:
                self._emitir(f"if ({cond}) {{ r0 = {self.nomes[alvo]}(r0, r1, r2, r3); "
                             f"return r0; }}  /* chamada de cauda condicional */")
                return
            raise _NaoLevantado(self._motivo_saida(alvo, "desvio condicional"))
        self._emitir(f"if ({cond}) goto {self._rotulo(alvo)};")

    def _aritmetica(self, ins, m: str) -> None:
        op = ins.operands
        if m in ("adds", "subs", "add", "sub", "adcs", "sbcs", "cmp", "cmn"):
            if len(op) == 2 and m in ("add", "sub") and self._reg(op[0]) == "sp":
                imediato = op[1].imm & 0xFFFFFFFF
                sinal = "-" if m == "sub" else "+"
                self._emitir(f"sp {sinal}= {imediato};  /* ajuste de pilha */")
                return
            if len(op) == 3:
                destino, a = self._reg(op[0]), self._reg(op[1])
                b = (hex(op[2].imm & 0xFFFFFFFF) if op[2].type == capstone.arm.ARM_OP_IMM
                     else self._reg(op[2]))
            elif len(op) == 2:
                destino, a = self._reg(op[0]), self._reg(op[0])
                b = (hex(op[1].imm & 0xFFFFFFFF) if op[1].type == capstone.arm.ARM_OP_IMM
                     else self._reg(op[1]))
            else:
                raise _NaoLevantado("forma inesperada")
            flags = self._define_flags
            if m in ("cmp", "cmn"):
                if m == "cmp":
                    self._anotar_flags(("cmp", a, b))
                operacao = "a_ + b_" if m == "cmn" else "a_ - b_"
                self._emitir(f"{{ u32 a_ = {a}, b_ = {b}; u32 r_ = {operacao};")
                if operacao.endswith("+"):
                    self._emitir("  c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;")
                else:
                    self._emitir("  c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;")
                self._emitir("  z = (r_ == 0); n = (r_ >> 31); }")
                return
            if m in ("adds", "add", "adcs", "adc"):
                if m == "adds":
                    self._anotar_flags(("adds", destino))
                entrada = "c" if m in ("adcs", "adc") else "0"
                self._emitir(f"{{ u32 a_ = {a}, b_ = {b} + {entrada}; u32 r_ = a_ + b_;")
                if flags:
                    self._emitir("  c = (r_ < a_); v = ((a_ ^ r_) & (b_ ^ r_)) >> 31;")
                    self._emitir("  z = (r_ == 0); n = (r_ >> 31);")
                self._emitir(f"  {destino} = r_; }}")
                return
            if m in ("sbcs", "sbc"):
                self._emitir(f"{{ u32 a_ = {a}, b_ = {b} + (c ? 0u : 1u); u32 r_ = a_ - b_;")
                if flags:
                    self._emitir("  c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;")
                    self._emitir("  z = (r_ == 0); n = (r_ >> 31);")
                self._emitir(f"  {destino} = r_; }}")
                return
            self._emitir(f"{{ u32 a_ = {a}, b_ = {b}; u32 r_ = a_ - b_;")
            if flags:
                self._emitir("  c = (a_ >= b_); v = ((a_ ^ b_) & (a_ ^ r_)) >> 31;")
                self._emitir("  z = (r_ == 0); n = (r_ >> 31);")
            self._emitir(f"  {destino} = r_; }}")
            return
        if m in ("rsbs", "rsb"):
            destino = self._reg(op[0])
            b = (hex(op[1].imm & 0xFFFFFFFF) if op[1].type == capstone.arm.ARM_OP_IMM
                 else self._reg(op[1]))
            self._emitir(f"{{ u32 a_ = {b}; u32 r_ = 0u - a_;")
            if self._define_flags:
                self._emitir("  c = (0u >= a_); v = ((0u ^ a_) & (0u ^ r_)) >> 31;")
                self._emitir("  z = (r_ == 0); n = (r_ >> 31);")
            self._emitir(f"  {destino} = r_; }}")
            return
        raise _NaoLevantado("forma aritmetica nao implementada")

    def _logica(self, ins, m: str) -> None:
        op = ins.operands
        destino = "t_" if m in ("tst", "teq") else self._reg(op[0])
        # ATENCAO: em `mvns Rd, Rm` / `mvn Rd, Rm` a FONTE e o SEGUNDO operando.
        # Usar o primeiro coincide em `mvns r3, r3` mas nao em `mvns r2, r0` --
        # esse bug gerou C que compila e roda errado, e so a emulacao pegou.
        a = self._reg(op[-1]) if m in ("mvns", "mvn") else self._reg(op[0])
        b = (hex(op[-1].imm & 0xFFFFFFFF) if op[-1].type == capstone.arm.ARM_OP_IMM
             else self._reg(op[-1]))
        if m in ("mvns", "mvn"):
            self._emitir(f"{destino} = ~{a};")
        elif m in ("tst", "teq"):
            operador = "^" if m == "teq" else "&"
            self._emitir(f"{{ u32 t_ = {a} {operador} {b};")
            self._emitir("  z = (t_ == 0); n = (t_ >> 31); }")
            return
        else:
            operador = {"ands": "&", "and": "&", "orrs": "|", "orr": "|",
                        "eors": "^", "eor": "^", "bics": "& ~", "bic": "& ~"}[m]
            self._emitir(f"{destino} = {a} {operador} {b};")
        if self._define_flags:
            self._flags_logicas(destino)

    def _deslocamento(self, ins, m: str) -> None:
        op = ins.operands
        destino = self._reg(op[0])
        # 3 operandos (imediato): `lsls rd, rs, #N` -- desloca rs.
        # 2 operandos (Thumb, por registrador): `lsls rd, rs` -- desloca o PROPRIO
        # rd, com a quantidade nos 8 bits baixos de rs.
        if len(op) >= 3:
            base = self._reg(op[1])
            quantos = (hex(op[2].imm & 0xFF) if op[2].type == capstone.arm.ARM_OP_IMM
                       else f"({self._reg(op[2])} & 0xFFu)")
        elif len(op) == 2:
            base = self._reg(op[0])
            quantos = (hex(op[1].imm & 0xFF) if op[1].type == capstone.arm.ARM_OP_IMM
                       else f"({self._reg(op[1])} & 0xFFu)")
        else:
            raise _NaoLevantado("forma de deslocamento inesperada")
        funcao_c = {"lsls": "sh_lsl", "lsl": "sh_lsl", "lsrs": "sh_lsr",
                    "lsr": "sh_lsr", "asrs": "sh_asr", "asr": "sh_asr",
                    "rors": "sh_ror", "ror": "sh_ror", "rorn": "sh_ror"}[m]
        self._emitir(f"{{ u32 c_ = c; u32 r_ = {funcao_c}({base}, {quantos}, &c_);")
        if self._define_flags:
            self._emitir(f"  c = c_; {destino} = r_; z = (r_ == 0); n = (r_ >> 31); }}")
        else:
            self._emitir(f"  {destino} = r_; }}    /* sem s: C preservado */")

    def _memoria(self, ins, m: str) -> None:
        op = ins.operands
        destino = self._reg(op[0]) if op[0].type == capstone.arm.ARM_OP_REG else None
        posicao = next((i for i, o in enumerate(op)
                        if o.type == capstone.arm.ARM_OP_MEM), None)
        if posicao is None:
            raise _NaoLevantado("sem operando de memoria")
        mem = op[posicao].mem
        base = self._nome(mem.base)

        # ATENCAO: no Thumb o PC vale (endereco + 4) com o bit1 zerado; no ARM,
        # endereco + 8. Errar isso desloca o pool de literais em 4 bytes.
        if base == "pc":
            pc = (ins.address + 4) & ~3 if self.f.modo == "thumb" else ins.address + 8
            endereco = pc + mem.disp
            valor = int.from_bytes(
                self.imagem[endereco - self.base:endereco - self.base + 4], "little")
            if destino is None:
                raise _NaoLevantado("escrita em pool literal")
            self._emitir(f"{destino} = 0x{valor:08X}u;  /* pool 0x{endereco:08X} */")
            return

        # -- endereco: base + indice + deslocamento --------------------------
        partes = [base]
        if mem.index:
            nome_indice = self._nome(mem.index)
            desloc = getattr(mem, "shift", None)
            if desloc is not None and getattr(desloc, "type", 0) not in (0, None):
                if desloc.type == capstone.arm.ARM_SFT_LSL:
                    partes.append(nome_indice if not desloc.value
                                  else f"({nome_indice} << {desloc.value})")
                else:
                    raise _NaoLevantado("offset com deslocamento diferente de LSL")
            else:
                partes.append(nome_indice)
        if mem.disp:
            partes.append(hex(mem.disp))
        expressao = " + ".join(partes)

        # -- pos-indexado? (`ldr r0, [r1], #4` -- o texto tem algo apos o `]`) --
        texto = ins.op_str
        depois = texto.split("]", 1)[1].strip() if "]" in texto else ""
        pos_indexado = bool(depois) and depois != "!"
        if pos_indexado:
            extra = op[posicao + 1] if posicao + 1 < len(op) else None
            if extra is None:
                raise _NaoLevantado("pos-indexado sem offset identificavel")
            if extra.type == capstone.arm.ARM_OP_IMM:
                acrescimo = hex(extra.imm & 0xFFFFFFFF)
            else:
                acrescimo = self._reg(extra)
            escrita_back = f"{base} = {base} + {acrescimo};"
        elif "!" in texto:
            escrita_back = f"{base} = {expressao};"
        else:
            escrita_back = None

        acesso = {
            "ldr": f"{destino} = carrega32({expressao});",
            "ldrb": f"{destino} = carrega8({expressao});",
            "ldrh": f"{destino} = carrega16({expressao});",
            "ldrsb": f"{destino} = (u32)carrega8s({expressao});",
            "ldrsh": f"{destino} = (u32)carrega16s({expressao});",
            "str": f"guarda32({expressao}, {destino});",
            "strb": f"guarda8({expressao}, (u8){destino});",
            "strh": f"guarda16({expressao}, (u16){destino});",
        }.get(m)
        if acesso is None:
            raise _NaoLevantado(f"variante de memoria {m} nao implementada")

        if escrita_back is None:
            self._emitir(acesso)
        else:
            # O acesso e o writeback usam o MESMO endereco calculado: emitir em
            # bloco evita que o compilador de C reordene a leitura depois da
            # escrita do registrador base.
            self._emitir("{ " + acesso + " " + escrita_back + " }")

    def _multipla(self, ins, m: str) -> None:
        registradores = [self._reg(o) for o in ins.operands
                         if o.type == capstone.arm.ARM_OP_REG]
        base, lista = registradores[0], registradores[1:]
        carga = m.startswith("ldm")
        escrita_back = "!" in ins.op_str
        n = len(lista)
        # Modo de enderecamento do bloco (ARM): o deslocamento inicial e o
        # delta do writeback mudam em cada um -- tratar todos como se fossem
        # "increment after" le os enderecos errados.
        sufixo = m[3:] if len(m) > 3 else "ia"
        modo = {"ia": 0, "ib": 4, "da": 4 - 4 * n, "db": -4 * n}.get(sufixo, 0)
        delta = {"ia": 4 * n, "ib": 4 * n, "da": -4 * n, "db": -4 * n}.get(sufixo, 4 * n)

        # Snapshot do endereco base: `ldmia r1!, {r0, r1, ...}` e rotina comum
        # no codigo compilado, e depois de carregar em r1 os enderecos seguintes
        # NAO podem usar o r1 novo. Sem o snapshot, os acessos seguintes vao
        # para o endereco errado -- bug silencioso classico de levantador.
        self._emitir(f"{{ u32 base_ = {base};")
        for i, r in enumerate(lista):
            desloc = modo + 4 * i
            termo = f"base_ + {desloc}" if desloc >= 0 else f"base_ - {-desloc}"
            if carga:
                self._emitir(f"    {r} = carrega32({termo});")
            else:
                self._emitir(f"    guarda32({termo}, {r});")
        if escrita_back:
            if carga and base in lista:
                # ARM: em LDM com a base na lista, o valor CARREGADO prevalece
                # sobre o writeback (comportamento definido, e o que o
                # compilador explora de proposito).
                self._emitir(f"    /* {base} esta na lista: o valor carregado "
                             f"prevalece sobre o writeback */")
            elif not carga and base in lista:
                self._emitir(f"    /* ATENCAO: STM com {base} na lista e writeback "
                             f"e marcado IMPREVISIVEL pelo manual do ARM; aqui o "
                             f"valor gravado e o original e o writeback acontece */")
                self._emitir(f"    {base} = base_ + {delta};")
            else:
                self._emitir(f"    {base} = base_ + {delta};  /* writeback */")
        self._emitir("}")


def _separar_condicao(mnemonic: str, modo: str) -> tuple[str | None, str, bool]:
    """Separa mnemonic + sufixo de condicao + sufixo S (ARM).

    Devolve (condicao, mnemonic_base, define_flags). So aceita o sufixo quando o
    que sobra e um mnemonic conhecido -- evita casar com nomes que terminam nas
    mesmas duas letras por acaso (ex.: `bls` termina em `ls`).
    """
    if modo != "arm":
        return None, mnemonic, mnemonic in SETA_FLAGS
    for cond in CONDICOES:
        if mnemonic.endswith(cond):
            resto = mnemonic[: -len(cond)]
            if resto in BASES_CONHECIDAS:
                return cond, resto, resto in SETA_FLAGS
            if resto.endswith("s") and resto[:-1] in BASES_CONHECIDAS:
                return cond, resto[:-1], True
    if mnemonic in BASES_CONHECIDAS:
        return None, mnemonic, mnemonic in SETA_FLAGS
    return None, mnemonic, False


def _condicao_direta(sufixo: str, descritor) -> str | None:
    """Como escrever a condicao sem passar pelas flags, quando e equivalente.

    Regras (validadas pela bateria de execucao do corpus): para `cmp A, B` as
    comparacoes com e sem sinal sao exatamente as definidas pelo ARM; para
    instrucoes que ESCREVEM o resultado (subs/adds/ands/movs/deslocamentos) so
    eq/ne/mi/pl valem, lidas do proprio destino -- carry e overflow nao sao
    expressos com seguranca sem recomputar a operacao.
    """
    tipo = descritor[0]
    if tipo == "cmp":
        _, a, b = descritor
        return {
            "eq": f"{a} == {b}", "ne": f"{a} != {b}",
            "cs": f"{a} >= {b}", "hs": f"{a} >= {b}",
            "cc": f"{a} < {b}", "lo": f"{a} < {b}",
            "hi": f"{a} > {b}", "ls": f"{a} <= {b}",
            "ge": f"(s32){a} >= (s32){b}", "lt": f"(s32){a} < (s32){b}",
            "gt": f"(s32){a} > (s32){b}", "le": f"(s32){a} <= (s32){b}",
        }.get(sufixo)
    if tipo in ("subs", "adds", "resultado"):
        destino = descritor[1]
        return {"eq": f"{destino} == 0", "ne": f"{destino} != 0",
                "mi": f"(s32){destino} < 0", "pl": f"(s32){destino} >= 0"}.get(sufixo)
    return None


def _monta_retorno_a_mao(instrucao) -> bool:
    """`add lr, pc, #0` -- o retorno do interworking montado instrucao a instrucao."""
    return (instrucao.mnemonic in ("add", "adds")
            and instrucao.operadores.replace(" ", "").startswith("lr,pc,"))


def _comentario(texto: str) -> str:
    """Texto seguro para ir dentro de `/* ... */` num comentario do C gerado.

    `*/` fecha o comentario antes da hora e o C deixa de compilar -- e o texto vem
    de dado da ROM (nome de registrador, valor lido), entao nao se confia nele.
    """
    return texto.replace("*/", "* /") if texto else "(guarda nao registrado)"


def _carrega_da_pilha(instrucao, registrador: str) -> bool:
    """A instrucao carrega `registrador` de algo que esta NA PILHA?

    Cobre as tres formas que a ROM usa no epilogo: `pop {..., rN, ...}`,
    `ldr rN, [sp, ...]` e `ldmia sp!, {..., rN, ...}`. Comparar por texto e'
    proposital: o desmonte ja passou pelo capstone, entao o operando esta na
    forma canonica (`sp`, nomes de registrador em minusculas) e nao ha
    ambiguidade de codificacao.
    """
    if instrucao.mnemonic in ("pop", "ldmia", "ldm", "ldmfd"):
        return registrador in _lista_de_registradores(instrucao.operadores)
    if instrucao.mnemonic in ("ldr", "ldrb", "ldrh", "ldrsb", "ldrsh"):
        partes = instrucao.operadores.split(",", 1)
        return (len(partes) == 2 and partes[0].strip() == registrador
                and "[sp" in partes[1].replace(" ", ""))
    return False


def _lista_de_registradores(operadores: str) -> list[str]:
    """Nomes dentro de `{...}` (lista de registradores do push/pop/ldm)."""
    if "{" not in operadores:
        return []
    lista = operadores.split("{", 1)[1].split("}", 1)[0]
    return [nome.strip() for nome in lista.split(",") if nome.strip()]


def _saida_para_tras(alvo: int, entrada: int) -> str | None:
    """Motivo especifico para desvio que sai da funcao PARA TRAS.

    Desvio para endereco abaixo da entrada nao e' "rotulo inexistente" (defeito
    do lifter) nem "funcao nao descoberta": e' a leitura continuando em outra
    rotina -- o bloco/epilogo comum que o compilador compartilha entre funcoes.
    A mensagem tem de dizer isso, porque a acao de quem le e' diferente: aqui
    nao falta implementar instrucao nenhuma, falta o bloco pertencer a funcao.
    """
    if alvo < entrada:
        return (f"desvio para tras, para fora da funcao (0x{alvo:08X} < entrada "
                f"0x{entrada:08X})")
    return None


class _NaoLevantado(Exception):
    """Instrucao que este levantador nao traduz (registrada, nunca ignorada)."""


def identificador_c(nome: str) -> str:
    """Nome de simbolo -> identificador C valido, sem renomear por gosto."""
    limpo = "".join(c if (c.isalnum() or c == "_") else "_" for c in nome)
    if not limpo or limpo[0].isdigit():
        limpo = "_" + limpo
    return limpo


class IndiceDeJanelas:
    """Onde cada endereco desmontado mora -- para as mensagens nao mentirem.

    Existe por um defeito de RELATO medido na ROM: 29 dos desvios recusados
    diziam "desvio para 0x..., que nao foi desmontado (rotulo inexistente)"
    quando o endereco ESTAVA desmontado -- em outra janela. Dizer que o endereco
    nao existe desmontado e' uma afirmacao falsa sobre o proprio levantamento, e
    ela manda quem le procurar defeito onde nao tem: o que falta ali nao e'
    implementar instrucao, e' a leitura poder continuar em outra rotina.
    """

    def __init__(self, desmontagem) -> None:
        self.endereco_dono: dict[int, int] = {}
        self.faixas: list[tuple[int, int, int]] = []
        for funcao in desmontagem.funcoes.values():
            for instrucao in funcao.instrucoes:
                self.endereco_dono.setdefault(instrucao.endereco, funcao.entrada)
            if funcao.instrucoes:
                self.faixas.append((funcao.entrada, funcao.fim, funcao.entrada))
        self.faixas.sort()

    def faixa_que_contem(self, endereco: int) -> int | None:
        for entrada, fim, _ in self.faixas:
            if entrada <= endereco < fim:
                return entrada
            if entrada > endereco:
                break        # faixas ordenadas: nao ha como achar mais adiante
        return None

    def descrever(self, alvo: int, propria: int, fim_propria: int) -> str:
        """Em uma frase: onde este endereco esta (ou nao esta) desmontado."""
        if propria <= alvo < fim_propria:
            return ("dentro desta janela, em trecho nao desmontado (a leitura "
                    "parou antes de alcancar)")
        dono = self.endereco_dono.get(alvo)
        if dono is not None:
            return f"a leitura continua em INSTRUCAO da janela 0x{dono:08X}"
        dono = self.faixa_que_contem(alvo)
        if dono is not None:
            return (f"dentro da faixa da janela 0x{dono:08X}, em trecho nao "
                    f"desmontado (buraco: la a leitura parou em dado)")
        return ("fora de qualquer janela desmontada: nenhuma leitura passou por "
                "esse endereco")


def chamadores_de(desmontagem, nomes: dict[int, str]) -> dict[str, list[str]]:
    """Inverte o grafo de chamadas: quem chama cada funcao (por nome)."""
    saida: dict[str, list[str]] = {}
    for origem, destino in desmontagem.arestas():
        nome_origem = nomes.get(origem, f"fn_{origem:08X}")
        nome_destino = nomes.get(destino, f"fn_{destino:08X}")
        saida.setdefault(nome_destino, []).append(nome_origem)
    for lista in saida.values():
        lista.sort()
    return saida


def decompilar(desmontagem, imagem: bytes, base: int = rom_mod.ROM_BASE,
               nomes: dict[int, str] | None = None) -> CodigoC:
    """Levanta todas as funcoes descobertas para C."""
    # ATENCAO: ler o parametro ANTES de rebindar a variavel -- `nomes = {}` e
    # depois iterar sobre `nomes` descarta silenciosamente todos os nomes
    # fornecidos (bug real, pego pelo teste de ida e volta).
    pedidos = dict(nomes or {})
    nomes, usados = {}, {}
    for endereco, bruto in pedidos.items():
        # ATENCAO: nome repetido ou com caractere invalido gera C que nao
        # compila (duas definicoes da mesma funcao). Desempata pelo endereco --
        # e o nome original fica no comentario de origem de cada funcao.
        candidato = identificador_c(bruto)
        if candidato in usados:
            candidato = f"{candidato}_{endereco:08X}"
        usados[candidato] = endereco
        nomes[endereco] = candidato
    for endereco in desmontagem.funcoes:
        nomes.setdefault(endereco, f"fn_{endereco:08X}")
    saida = CodigoC(chamadores=chamadores_de(desmontagem, nomes))
    indice = IndiceDeJanelas(desmontagem)
    for endereco in sorted(desmontagem.funcoes):
        funcao = desmontagem.funcoes[endereco]
        emissor = _Emissor(funcao, imagem, base, nomes, indice)
        levantada = emissor.levantar()
        saida.funcoes.append(levantada)
        if not levantada.completa:
            saida.avisos.append(f"0x{endereco:08X}: {len(levantada.nao_levantadas)} "
                                f"instrucao(oes) nao levantada(s)")
    if desmontagem.dados_lidos:
        saida.avisos.append(f"{len(desmontagem.dados_lidos)} literais de pool lidos "
                            f"do binario")
    return saida
