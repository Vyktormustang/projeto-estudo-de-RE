"""Corpus de verdade conhecida para validar o descompilador.

Nao temos a ROM comercial aqui (e ela nao deve ser baixada por questoes legais),
entao a unica forma honesta de provar que o pipeline funciona e construir um
binario ARM/Thumb REAL cuja fonte nos conhecemos: escrevemos C, compilamos com o
compilador cruzado (zig cc -> thumb-freestanding-eabi), empacotamos como imagem
GBA sintetica e entao tratamos esse binario como se fosse a ROM alvo.

O que isso prova: que o desmontador, o descompilador e o verificador funcionam
em codigo ARM/Thumb de verdade, com controle de fluxo, memoria, literais e
chamadas. O que NAO prova: que os numeros valem para a ROM do usuario (para isso
o pipeline tem de rodar sobre ela, na maquina do usuario, com a copia dele).

O codigo C abaixo e autoral e trivial de proposito: cada funcao isola uma classe
de construcao que o descompilador precisa reconstruir.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from . import rom as rom_mod

CORPUS_C = r"""
/* Corpus de teste do gbadecomp (codigo autoral, dominio trivial).
   Inclui as rotinas de apoio aritmetico (__aeabi_*) escritas aqui mesmo: numa
   ROM real elas tambem fazem parte do binario, e sem elas o linker nao fecha
   (o ARM7TDMI nao tem divisao em hardware nem multiplicacao de 64 bits em uma
   instrucao para todos os casos). */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned long long u64;

__attribute__((noinline, used)) u32 __aeabi_uidiv(u32 num, u32 den) {
    u32 q = 0, r = 0;
    int i;
    if (den == 0) { return 0xFFFFFFFFu; }
    for (i = 31; i >= 0; i--) {
        r = (r << 1) | ((num >> i) & 1u);
        if (r >= den) { r = r - den; q = q | (1u << i); }
    }
    return q;
}

/* Multiplicacao de 32x32 -> 64 bits SEM libcall: quebra em metades de 16 bits,
   porque o produto de dois valores de 16 bits cabe em 32 (instrucao muls) e
   assim nao se chama a si mesma (o compilador chamaria __aeabi_lmul de novo). */
__attribute__((noinline, used)) u64 mul32(u32 a, u32 b) {
    u32 al = a & 0xFFFFu, ah = a >> 16, bl = b & 0xFFFFu, bh = b >> 16;
    u32 lo = al * bl;
    u32 mid = al * bh + ah * bl;
    u32 hi = ah * bh;
    return (u64)lo + ((u64)mid << 16) + ((u64)hi << 32);
}

__attribute__((noinline, used)) u64 __aeabi_lmul(u64 a, u64 b) {
    u32 al = (u32)a, ah = (u32)(a >> 32);
    u32 bl = (u32)b, bh = (u32)(b >> 32);
    u64 lo = mul32(al, bl);
    u64 mid = mul32(al, bh) + mul32(ah, bl);
    u64 hi = mul32(ah, bh);
    return lo + (mid << 32) + (hi << 32) * 0;
}

/* Funcao de entrada do corpus: chama todas as demais, como um `main` de ROM
   faria. Sem isto o corpus nao e alcancavel a partir do vetor de boot e a
   descoberta recursiva (a mesma que roda na ROM de verdade) so acharia a
   primeira funcao. Fica na secao .text.entrada, que o script de link coloca
   exatamente em CODE_BASE. */
/* Prototipos das funcoes do corpus (definidas abaixo): C exige declaracao
   antes do uso, e assim main_teste pode chama-las todas. */
int soma(int a, int b);
int fat(int n);
int maximo(int a, int b);
int abs_dif(int a, int b);
u32 conta_bits(u32 x);
u32 mistura(u32 a, u32 b);
int mascara(u32 v, int lo, int hi);
int soma_const(int x);
u32 soma_vetor(const u16 *v, int n);
void limpa(volatile u32 *p, int n);
void escreve_u16(volatile u16 *p, u16 v);
int campo_offsets(const int *p);
int classifica(int x);
int if_aninhado(int x, int y);
int chama_soma(int x);
int loop_decrescente(int n);
u32 divide(u32 a, u32 b);
int ternario(int a, int b);
u32 poe_bit(u32 v, int bit);
int troca(int a, int b);
u32 distancia_adr(int ignora);

static volatile u32 area_teste[64];

__attribute__((noinline, used, section(".text.entrada")))
int main_teste(void) {
    u32 s = 0;
    int i;
    s += (u32)soma(7, 35);
    s += (u32)fat(5);
    s += (u32)maximo(4, 9);
    s += (u32)abs_dif(9, 4);
    s += conta_bits(0xFFu);
    s += mistura(0xAABBCCDDu, 0x11223344u);
    s += (u32)mascara(0xF0F0F0u, 4, 11);
    s += (u32)soma_const(1);
    for (i = 0; i < 4; i++) { ((volatile u16 *)area_teste)[i] = (u16)(i + 1); }
    s += soma_vetor((const u16 *)area_teste, 4);
    limpa(area_teste, 4);
    escreve_u16((volatile u16 *)area_teste, 0xBEEFu);
    s += (u32)campo_offsets((const int *)area_teste);
    s += (u32)classifica(150);
    s += (u32)if_aninhado(5, 3);
    s += (u32)chama_soma(1);
    s += (u32)loop_decrescente(5);
    s += divide(100u, 7u);
    s += (u32)ternario(9, 4);
    s += poe_bit(0u, 7);
    s += (u32)troca(3, 9);
    s += distancia_adr(0);
    s += (u32)(mul32(1000u, 1000u) & 0xFFFFu);
    s += (u32)(__aeabi_lmul(1000ull, 1000ull) & 0xFFFFu);
    return (int)s;
}

__attribute__((noinline, used)) int soma(int a, int b) { return a + b; }

__attribute__((noinline, used)) int fat(int n) {
    int r = 1;
    while (n > 1) { r = (int)((u32)r * (u32)n); n = n - 1; }
    return r;
}

__attribute__((noinline, used)) int maximo(int a, int b) {
    if (a > b) { return a; }
    return b;
}

__attribute__((noinline, used)) int abs_dif(int a, int b) {
    if (a >= b) { return a - b; }
    return b - a;
}

__attribute__((noinline, used)) u32 conta_bits(u32 x) {
    u32 n = 0;
    while (x != 0) { n += (x & 1u); x = x >> 1; }
    return n;
}

__attribute__((noinline, used)) u32 mistura(u32 a, u32 b) {
    return (a & 0xFF00FF00u) | ((b & 0x00FF00FFu) ^ (a >> 8));
}

__attribute__((noinline, used)) int mascara(u32 v, int lo, int hi) {
    u32 m = ((1u << (hi - lo + 1)) - 1u) << lo;
    return (int)((v & m) >> lo);
}

__attribute__((noinline, used)) int soma_const(int x) {
    return x + 119303;  /* forca pool de literais */
}

__attribute__((noinline, used)) u32 soma_vetor(const u16 *v, int n) {
    u32 s = 0;
    int i;
    for (i = 0; i < n; i++) { s += v[i]; }
    return s;
}

__attribute__((noinline, used)) void limpa(volatile u32 *p, int n) {
    int i;
    for (i = 0; i < n; i++) { p[i] = 0; }
}

__attribute__((noinline, used)) void escreve_u16(volatile u16 *p, u16 v) {
    *p = v;
}

__attribute__((noinline, used)) int campo_offsets(const int *p) {
    return p[1] + p[4] * 3;
}

__attribute__((noinline, used)) int classifica(int x) {
    if (x < 10) { return 1; }
    else if (x < 100) { return 2; }
    else if (x < 1000) { return 3; }
    return 4;
}

__attribute__((noinline, used)) int if_aninhado(int x, int y) {
    if (x > 0) {
        if (y > 0) { return x + y; }
        return x - y;
    }
    if (y > 0) { return y - x; }
    return 0;
}

__attribute__((noinline, used)) int chama_soma(int x) {
    return soma(x, 100) + 1;   /* chamada interna: exercita o stub do verificador */
}

__attribute__((noinline, used)) int loop_decrescente(int n) {
    int s = 0;
    while (n > 0) { s += n; n--; }
    return s;
}

__attribute__((noinline, used)) u32 divide(u32 a, u32 b) {
    if (b == 0) { return 0; }
    return __aeabi_uidiv(a, b); /* chamada fora da funcao: exercita o stub */
}

__attribute__((noinline, used)) int ternario(int a, int b) {
    return (a > b) ? (a - b) : (b - a);
}

__attribute__((noinline, used)) u32 poe_bit(u32 v, int bit) {
    return v | (1u << bit);
}

__attribute__((noinline, used)) int troca(int a, int b) {
    int t = a; a = b; b = t;
    return a - b;
}

/* `adr` -- endereco calculado a partir do PC. O compilador moderno NAO emite
   esta instrucao (prefere `ldr rX, [pc, #N]`: verificado, as duas formas usuais
   de escrever isso em C viram carga do pool), mas a ROM de estudo foi compilada
   com o agbcc da epoca e tem 168 delas, todas em janelas Thumb. Entra por asm de
   proposito.

   A funcao devolve a DIFERENCA entre dois `adr`: e' o unico jeito de o caso
   valer nos dois binarios (o original e o C levantado e recompilado, que tem
   outro layout -- um endereco absoluto lido daqui apontaria para outra coisa la).
   A diferenca e' fixa (os dois rotulos distam 4 bytes) e NAO e' trivial de
   acertar: `.balign 4` no comeco garante que o primeiro `adr` fique em endereco
   ≡ 2 (mod 4), e e' exatamente ai que a regra do ARM ARM importa -- o PC do
   `adr` e' `(endereco + 4) & ~3`, nao `endereco + 4`. Com a regra errada, o
   resultado sai 2 em vez de 4 (o emulador confirma o valor absoluto no teste
   `test_adr_do_levantador_bate_com_o_emulador`).

   O `.word` tem bytes `b0 bf` (que no Thumb-1 nao existem) para a leitura parar
   nele em vez de desmontar o dado como codigo. */
__attribute__((noinline, used)) u32 distancia_adr(int ignora) {
    u32 um, outro;
    (void)ignora;
    __asm__ volatile(
        ".balign 4\n\t"
        ".short 0x46c0\n\t"      /* `mov r8, r8`: 2 bytes, poe o `adr` em 2 mod 4 */
        "adr %0, 1f\n\t"
        "adr %1, 2f\n\t"
        "b 3f\n\t"
        ".balign 4\n"
        "1:\n\t.word 0xB0BFBFB0\n\t"
        "2:\n"
        "3:\n"
        : "=r"(um), "=r"(outro));
    return outro - um;
}
"""

ENTRADA = "main_teste"    # simbolo que fica em CODE_BASE (vetor de boot aponta para ele)
ROM_TAMANHO = 0x40000  # 256 KiB: code + espaco livre 0xFF (exercita o scan de freespace)
BOOT_BASE = 0x080000C0   # stub ARM de boot (12 bytes, escrito a mao)
CODE_BASE = 0x080000CC   # inicio de .text, logo apos o stub

LINKER_SCRIPT = """
/* Script de link do corpus de teste: coloca o codigo exatamente onde ele
   ficaria numa ROM de GBA (0x080000CC), de modo que os enderecos do binario
   sejam ABSOLUTOS e iguais aos da imagem final. */
ENTRY(_start)
SECTIONS {
  . = %(base)#x;
  .text : { *(.text.entrada) *(.text) *(.text.*) }
  .rodata : { *(.rodata) *(.rodata.*) }
  .data : { *(.data) *(.data.*) }
  .bss : { *(.bss) *(.bss.*) *(COMMON) }
  /DISCARD/ : { *(.ARM.exidx*) *(.ARM.attributes) *(.comment) *(.note*) *(.eh_frame*) }
}
"""


@dataclass
class FuncaoCorpus:
    nome: str
    addr: int
    tamanho: int
    modo: str
    fonte_linha: int

    @property
    def addr_hex(self) -> str:
        return f"0x{self.addr:08X}"


@dataclass
class Corpus:
    rom_path: str
    sha256: str
    total_funcoes: int
    funcoes: list[FuncaoCorpus]
    comando_compilacao: str
    compilador: str
    c_fonte: str

    def to_json(self) -> dict:
        return {
            "rom_path": self.rom_path,
            "sha256": self.sha256,
            "total_funcoes": self.total_funcoes,
            "comando_compilacao": self.comando_compilacao,
            "compilador": self.compilador,
            "funcoes": [asdict(f) | {"addr_hex": f.addr_hex} for f in self.funcoes],
        }


def achar_zig() -> str | None:
    """Localiza o binario do zig (instalado via `pip install ziglang`)."""
    if z := shutil.which("zig"):
        return z
    try:
        import importlib.util

        spec = importlib.util.find_spec("ziglang")
        if spec and spec.origin:
            candidato = Path(spec.origin).parent / "zig"
            if candidato.exists():
                return str(candidato)
    except Exception:
        return None
    return None


def compilar_thumb(fonte_c: str, out_o: Path, opt: str = "-Os", zig: str | None = None) -> str:
    """Compila C para THUMB do ARM7TDMI e devolve o comando usado."""
    zig = zig or achar_zig()
    if not zig:
        raise RuntimeError(
            "compilador cruzado nao encontrado. Instale com: pip install ziglang"
        )
    c_file = out_o.with_suffix(".c")
    c_file.write_text(fonte_c, encoding="utf-8")
    cmd = [
        zig, "cc",
        "-target", "thumb-freestanding-eabi",
        "-mcpu=arm7tdmi",
        opt,
        "-fno-common", "-ffreestanding", "-fno-unwind-tables",
        "-fno-asynchronous-unwind-tables",
        "-c", str(c_file), "-o", str(out_o),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"falha ao compilar:\n{proc.stderr[-3000:]}")
    return " ".join(cmd)


def linkar_thumb(obj: Path, elf_out: Path, base: int = CODE_BASE, zig: str | None = None) -> str:
    """Linka o objeto com lld num script que fixa o codigo no endereco de ROM.

    Sem esta etapa os `bl` ficam como placeholder (relocacao nao resolvida) e
    qualquer emulacao ou analise de chamada enxerga alvo errado. Este foi um
    erro real encontrado durante o desenvolvimento.
    """
    zig = zig or achar_zig()
    if not zig:
        raise RuntimeError("compilador cruzado nao encontrado (pip install ziglang)")
    script = elf_out.with_suffix(".ld")
    script.write_text(LINKER_SCRIPT % {"base": base}, encoding="utf-8")
    cmd = [
        zig, "cc",
        "-target", "thumb-freestanding-eabi",
        "-mcpu=arm7tdmi",
        "-nostdlib", "-ffreestanding",
        f"-Wl,-T,{script}",
        str(obj), "-o", str(elf_out),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"falha ao linkar:\n{proc.stderr[-3000:]}")
    return " ".join(cmd)


def _secoes_texto(obj: Path) -> tuple[bytes, list[tuple[str, int, int]]]:
    """Devolve (bytes de .text, [(nome, valor, tamanho)] das funcoes)."""
    from elftools.elf.elffile import ELFFile

    with obj.open("rb") as fh:
        elf = ELFFile(fh)
        text = b""
        for sec in elf.iter_sections():
            if sec.name == ".text":
                text = sec.data()
                break
        symtab = elf.get_section_by_name(".symtab")
        funcoes: list[tuple[str, int, int]] = []
        for sym in symtab.iter_symbols():
            if sym["st_info"]["type"] == "STT_FUNC" and sym["st_size"] > 0:
                funcoes.append((sym.name, sym["st_value"], sym["st_size"]))
    return text, funcoes


def _cabecalho_gba(titulo: str, codigo: str, entrada: int) -> bytes:
    """Monta o cabecalho de 0xC0 bytes. A logo da Nintendo NAO e reproduzida:
    a area fica zerada de proposito (fixture sintetica, marcada como tal)."""
    header = bytearray(0xC0)
    # ramo ARM inicial: b <entrada>   (offset em palavras, -2 de pipeline)
    offset = (entrada - rom_mod.ROM_BASE - 8) // 4
    header[0:4] = (0xEA000000 | (offset & 0x00FFFFFF)).to_bytes(4, "little")
    header[0xA0:0xAC] = titulo.ljust(12, "\x00")[:12].encode("ascii")
    header[0xAC:0xB0] = codigo.ljust(4, "\x00")[:4].encode("ascii")
    header[0xB0:0xB2] = b"01"
    header[0xB2] = 0x00                     # complement check (calculado abaixo)
    header[0xB4] = 0x00                     # versao do software
    # Formula oficial: a soma comeca em 0xA0 (o logo e o ramo inicial ficam de
    # fora). Antes somava 0x00..0xBC, o que gerava um byte de complemento que
    # "batia" com o verificador do projeto -- igualmente errado -- e nao com a
    # especificacao. Achado ao construir o patcher.
    soma = sum(header[0xA0:0xBD]) & 0xFF
    header[0xBD] = (0x100 - ((soma + 0x19) & 0xFF)) & 0xFF
    return bytes(header)


def construir(
    destino_rom: str | Path,
    opt: str = "-Os",
    zig: str | None = None,
    titulo: str = "GBADECOMP",
    codigo_jogo: str = "TSYN",
) -> Corpus:
    """Compila o corpus, linka, e empacota uma imagem GBA sintetica valida.

    Ordem: C -> .o -> ELF linkado (enderecos absolutos, `bl` resolvidos) ->
    objcopy binario -> header + stub ARM + codigo -> preenchimento 0xFF.
    """
    destino = Path(destino_rom)
    destino.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        obj = Path(tmp) / "corpus.o"
        cmd_c = compilar_thumb(CORPUS_C, obj, opt=opt, zig=zig)
        elf = Path(tmp) / "corpus.elf"
        cmd_link = linkar_thumb(obj, elf, base=CODE_BASE, zig=zig)
        binario = Path(tmp) / "corpus.bin"
        proc = subprocess.run(
            [zig or achar_zig(), "objcopy", "-O", "binary", str(elf), str(binario)],
            capture_output=True, text=True,
        )
        if proc.returncode != 0 or not binario.exists():
            raise RuntimeError(f"falha no objcopy: {proc.stderr[-2000:]}")
        blob_codigo = binario.read_bytes()
        simbolos = _simbolos_funcao(elf)

    if not blob_codigo:
        raise RuntimeError("compilador nao produziu codigo")

    # --- montagem da imagem -------------------------------------------------
    # 0x0000-0x00BF  cabecalho GBA (logo Nintendo NAO reproduzida: area zerada)
    # 0x00C0-0x00CB  stub ARM de boot: ldr r0,[pc,#0]; bx r0; .word entry|1
    # 0x00CC-...     codigo Thumb linkado
    stub = bytes.fromhex("00009fe5") + bytes.fromhex("10ff2fe1")
    # o literal aponta para o endereco real da entrada (lido do ELF), e nao para
    # um valor suposto: se o layout mudar, aqui acusa em vez de gerar imagem quebrada.
    alvo_entrada = next((v & ~1 for n, v, _t in simbolos if n == ENTRADA), None)
    if alvo_entrada != CODE_BASE:
        raise RuntimeError(f"entrada {ENTRADA} deveria estar em "
                           f"0x{CODE_BASE:08X}, mas esta em {alvo_entrada}")
    literal = (alvo_entrada | 1).to_bytes(4, "little")
    header = _cabecalho_gba(titulo, codigo_jogo, BOOT_BASE)

    imagem = bytearray(header)
    imagem += stub
    imagem += literal
    assert len(imagem) == CODE_BASE - rom_mod.ROM_BASE, "stub deve terminar em CODE_BASE"
    imagem += blob_codigo
    if len(imagem) < ROM_TAMANHO:
        imagem += b"\xFF" * (ROM_TAMANHO - len(imagem))
    else:
        imagem += b"\xFF" * 0x1000

    destino.write_bytes(bytes(imagem))

    funcoes: list[FuncaoCorpus] = []
    for nome, valor, tamanho in sorted(simbolos, key=lambda t: t[1]):
        if nome in {"_start"} or nome.startswith("__stack") or valor < CODE_BASE:
            continue   # so o codigo de fato presente na imagem empacotada
        # ATENCAO (dois detalhes ja provados na pratica): (1) em ELF ARM, simbolo
        # de funcao Thumb tem o bit0 ligado (marcador de modo) -- usar o valor cru
        # desmonta 1 byte deslocado e produz lixo; (2) no ELF LINKADO o valor ja e
        # o endereco absoluto, entao NAO se soma CODE_BASE de novo.
        addr = valor & ~1
        funcoes.append(FuncaoCorpus(nome=nome, addr=addr, tamanho=tamanho,
                                    modo="thumb", fonte_linha=_linha_do_nome(nome)))

    return Corpus(
        rom_path=str(destino),
        sha256=hashlib.sha256(destino.read_bytes()).hexdigest(),
        total_funcoes=len(funcoes),
        funcoes=funcoes,
        comando_compilacao=f"{cmd_c} && {cmd_link}",
        compilador=(achar_zig() or "?"),
        c_fonte=CORPUS_C,
    )


def _linha_do_nome(nome: str) -> int:
    for i, linha in enumerate(CORPUS_C.splitlines(), start=1):
        if f"{nome}(" in linha and "attribute" in linha:
            return i
    return 0


def _simbolos_funcao(elf: Path) -> list[tuple[str, int, int]]:
    """(nome, valor, tamanho) das funcoes definidas no ELF linkado."""
    from elftools.elf.elffile import ELFFile

    with elf.open("rb") as fh:
        elfobj = ELFFile(fh)
        symtab = elfobj.get_section_by_name(".symtab")
        return [
            (sym.name, sym["st_value"], sym["st_size"])
            for sym in symtab.iter_symbols()
            if sym["st_info"]["type"] == "STT_FUNC" and sym["st_size"] > 0
        ]

def salvar_metadados(corpus: Corpus, caminho: str | Path) -> Path:
    p = Path(caminho)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(corpus.to_json(), indent=2, ensure_ascii=False), encoding="utf-8")
    return p

# ---------------------------------------------------------------------------
# Verdade-terreno: para cada funcao do corpus, entradas e saida CONHECIDAS.
# Os valores "esperado" foram conferidos a mao (ou por aritmetica explicita em
# Python, para os casos de bit a bit) ANTES de rodar a emulacao. Nao foram
# copiados do resultado: se divergirem, o relatorio mostra a divergencia.
#
#   args        -> valores de r0..r3; "RAM+0xNN" resolve para a EWRAM
#   memoria     -> (deslocamento_na_RAM, hex) escrito ANTES da chamada
#   verificar   -> (deslocamento, tamanho, formato) conferido na RAM depois
#   sinal       -> "com" interpreta r0 como inteiro de 32 bits com sinal
# ---------------------------------------------------------------------------
VERDADE_TERRENO: list[dict] = [
    # -- rotinas de apoio aritmetico (existem tambem em ROM real) ------------
    {"funcao": "__aeabi_uidiv", "args": (100, 7), "esperado": 14},
    {"funcao": "__aeabi_uidiv", "args": (7, 7), "esperado": 1},
    {"funcao": "__aeabi_uidiv", "args": (0, 5), "esperado": 0},
    {"funcao": "__aeabi_uidiv", "args": (9, 0), "esperado": 0xFFFFFFFF},
    {"funcao": "mul32", "args": (1000, 1000), "esperado": 1_000_000},
    {"funcao": "mul32", "args": (0xFFFF, 0xFFFF), "esperado": 0xFFFE0001},
    {"funcao": "__aeabi_lmul", "args": (1000, 0, 1000, 0), "esperado": 1_000_000},
    {"funcao": "__aeabi_lmul", "args": (0xFFFFFFFF, 0, 2, 0), "esperado": 0xFFFFFFFE},
    # -- aritmetica simples -------------------------------------------------
    {"funcao": "soma", "args": (7, 35), "esperado": 42},
    {"funcao": "soma", "args": (-5, 3), "esperado": -2, "sinal": "com"},
    {"funcao": "soma", "args": (-1, -1), "esperado": -2, "sinal": "com"},
    {"funcao": "fat", "args": (5,), "esperado": 120},
    {"funcao": "fat", "args": (0,), "esperado": 1},
    {"funcao": "fat", "args": (1,), "esperado": 1},
    {"funcao": "fat", "args": (6,), "esperado": 720},
    {"funcao": "maximo", "args": (4, 9), "esperado": 9},
    {"funcao": "maximo", "args": (9, 4), "esperado": 9},
    {"funcao": "maximo", "args": (5, 5), "esperado": 5},
    {"funcao": "abs_dif", "args": (9, 4), "esperado": 5},
    {"funcao": "abs_dif", "args": (4, 9), "esperado": 5},
    {"funcao": "abs_dif", "args": (5, 5), "esperado": 0},
    {"funcao": "soma_const", "args": (1,), "esperado": 119304},
    {"funcao": "soma_const", "args": (0,), "esperado": 119303},
    {"funcao": "ternario", "args": (9, 4), "esperado": 5},
    {"funcao": "ternario", "args": (4, 9), "esperado": 5},
    {"funcao": "troca", "args": (3, 9), "esperado": 6},
    # -- endereco calculado por `adr` (ver o comentario no CORPUS_C) ---------
    {"funcao": "distancia_adr", "args": (0,), "esperado": 4},
    {"funcao": "troca", "args": (9, 3), "esperado": -6, "sinal": "com"},
    # -- laco / desvio ------------------------------------------------------
    {"funcao": "conta_bits", "args": (0xFF,), "esperado": 8},
    {"funcao": "conta_bits", "args": (0,), "esperado": 0},
    {"funcao": "conta_bits", "args": (0x80000001,), "esperado": 2},
    {"funcao": "classifica", "args": (5,), "esperado": 1},
    {"funcao": "classifica", "args": (150,), "esperado": 3},
    {"funcao": "classifica", "args": (5000,), "esperado": 4},
    {"funcao": "if_aninhado", "args": (5, 3), "esperado": 8},
    {"funcao": "if_aninhado", "args": (5, -3), "esperado": 8},
    {"funcao": "if_aninhado", "args": (-5, 3), "esperado": 8},
    {"funcao": "if_aninhado", "args": (-5, -3), "esperado": 0},
    {"funcao": "loop_decrescente", "args": (5,), "esperado": 15},
    {"funcao": "loop_decrescente", "args": (10,), "esperado": 55},
    {"funcao": "loop_decrescente", "args": (0,), "esperado": 0},
    # -- chamadas entre funcoes (prova do grafo de chamadas) ----------------
    {"funcao": "chama_soma", "args": (1,), "esperado": 102},
    {"funcao": "chama_soma", "args": (-100,), "esperado": 1},
    {"funcao": "divide", "args": (100, 7), "esperado": 14},
    {"funcao": "divide", "args": (9, 0), "esperado": 0},
    {"funcao": "divide", "args": (1000, 10), "esperado": 100},
    # -- operacoes de bit ---------------------------------------------------
    {"funcao": "mistura", "args": (0xAABBCCDD, 0x11223344), "esperado": 0xAA88FF88},
    {"funcao": "mistura", "args": (0xFFFFFFFF, 0), "esperado": 0xFFFFFFFF},
    {"funcao": "mistura", "args": (0x12345678, 0x9ABCDEF0), "esperado": 0x12AE76A6},
    {"funcao": "mascara", "args": (0xF0F0F0, 4, 11), "esperado": 15},
    {"funcao": "mascara", "args": (0xDEADBEEF, 0, 7), "esperado": 239},
    {"funcao": "mascara", "args": (0x80000000, 31, 31), "esperado": 1},
    {"funcao": "poe_bit", "args": (0, 7), "esperado": 128},
    {"funcao": "poe_bit", "args": (0x10, 0), "esperado": 0x11},
    {"funcao": "poe_bit", "args": (0, 31), "esperado": 0x80000000},
    # -- memoria: leitura ---------------------------------------------------
    {"funcao": "soma_vetor", "args": ("RAM", 4), "esperado": 24,
     "memoria": [(0, "0300050007000900")]},
    # ATENCAO: aqui a tabela estava ERRADA (300) e a emulacao mostrou 600
    # (100+200+300); corrigido o valor conferido, nao o codigo.
    {"funcao": "soma_vetor", "args": ("RAM+0x20", 3), "esperado": 600,
     "memoria": [(0x20, "6400c8002c01")]},
    {"funcao": "campo_offsets", "args": ("RAM",), "esperado": 17,
     "memoria": [(0, "0000000002000000000000000000000005000000")]},
    # -- memoria: escrita ---------------------------------------------------
    {"funcao": "limpa", "args": ("RAM+0x100", 3), "esperado": 0,
     "memoria": [(0x100, "aa" * 16)], "verificar": (0x100, 12, "hex")},
    {"funcao": "escreve_u16", "args": ("RAM+0x200", 0xBEEF), "esperado": 0xBEEF,
     "verificar": (0x200, 2, "hex")},
]
