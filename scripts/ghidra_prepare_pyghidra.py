#!/usr/bin/env python3
"""Importa uma ROM de GBA no Ghidra usando PyGhidra (funciona só com JRE).

Por que este script existe
--------------------------
A distribuição do Ghidra exige um **JDK completo** no launcher
(`support/analyzeHeadless` → `launch.sh ... jdk` → `LaunchSupport -jdk_home`).
Sem `javac` o launcher recusa o Java e nada roda — mesmo que o Java 21+ de
runtime esteja perfeito.

Este script contorna isso de forma legítima:

* inicia o Ghidra pela API oficial **PyGhidra** (`pip install pyghidra`),
  apontando `java_home` diretamente (o setter público da classe
  `PyGhidraLauncher`), sem passar pelo `LaunchSupport`;
* importa a ROM com `ProgramLoader` + `BinaryLoader` em 0x08000000 e
  linguagem `ARM:LE:32:v4t`;
* monta o mapa de memória do GBA, rótulos e seeds ARM/Thumb via JPype;
* roda a auto-análise e o descompilador nativos;
* grava as mesmas evidências JSON do script Java (`gba_prepare_*.json`),
  permitindo o cross-check com `scripts/gba_rom_header.py`.

O que **não** funciona sem JDK: scripts `.java` (o Ghidra os compila em tempo de
execução e precisa de `javac`). Por isso a versão Java
(`scripts/ghidra_scripts/GbaPrepareProgram.java`) continua sendo o caminho
principal quando há JDK; este script é o caminho alternativo com JRE.

Uso
---
    python3 scripts/ghidra_prepare_pyghidra.py rom/sua_rom.gba
    python3 scripts/ghidra_prepare_pyghidra.py rom/sua_rom.gba --no-analysis
    python3 scripts/ghidra_prepare_pyghidra.py --self-test

Códigos de saída: 0 ok · 1 falha · 2 uso/ambiente · 3 pré-requisitos ausentes
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from gba_rom_header import arm_branch_target, parse_header  # noqa: E402

ROM_BASE = 0x08000000
LANGUAGE_ID = "ARM:LE:32:v4t"
ROM_BLOCK_NAME = "GBA_ROM"

EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_PREREQ = 0, 1, 2, 3

REGIONS = [
    ("GBA_EWRAM_256K", 0x02000000, 0x00040000, True, True, False, "EWRAM (256 KB) - GBATEK"),
    ("GBA_IWRAM_32K", 0x03000000, 0x00008000, True, True, False, "IWRAM (32 KB) - GBATEK"),
    ("GBA_IO_REGISTERS", 0x04000000, 0x00000400, True, True, False, "I/O mapeado - GBATEK"),
    ("GBA_PALETTE_RAM", 0x05000000, 0x00000400, True, True, False, "Paleta (1 KB) - GBATEK"),
    ("GBA_VRAM_96K", 0x06000000, 0x00018000, True, True, False, "VRAM (96 KB) - GBATEK"),
    ("GBA_OAM", 0x07000000, 0x00000400, True, True, False, "OAM (1 KB) - GBATEK"),
]

MIRRORS = [
    ("GBA_ROM_MIRROR_0A", 0x0A000000, 0x02000000, True, False, True, "mirror de barramento da ROM"),
    ("GBA_ROM_MIRROR_0C", 0x0C000000, 0x02000000, True, False, True, "mirror de barramento da ROM"),
    ("GBA_ROM_MIRROR_0E", 0x0E000000, 0x02000000, True, False, True, "mirror de barramento da ROM"),
]

LABELS = [
    (0x08000000, "gba_cart_header", "CONFIRMADO", "cabecalho do cartucho (0xC0 bytes) - GBATEK 9.2"),
    (0x080000A0, "gba_game_title", "CONFIRMADO", "titulo do jogo, 12 bytes - GBATEK"),
    (0x080000AC, "gba_game_code", "CONFIRMADO", "codigo do jogo, 4 bytes - GBATEK"),
    (0x080000B0, "gba_maker_code", "CONFIRMADO", "codigo do fabricante, 2 bytes - GBATEK"),
    (0x080000BC, "gba_header_checksum_word", "CONFIRMADO",
     "palavra que contem versao (0xBC) e complemento (0xBD) - GBATEK"),
    (0x080000C0, "gba_word_at_0xC0", "OBSERVADO", "palavra logo apos o cabecalho, sem interpretacao"),
    (0x04000000, "REG_DISPCNT", "CONFIRMADO", "display control - GBATEK"),
    (0x04000004, "REG_DISPSTAT", "CONFIRMADO", "display status - GBATEK"),
    (0x04000006, "REG_VCOUNT", "CONFIRMADO", "scanline atual - GBATEK"),
    (0x04000130, "REG_KEYINPUT", "CONFIRMADO", "teclas, ativo-baixo - GBATEK"),
    (0x04000200, "REG_IE", "CONFIRMADO", "interrupt enable - GBATEK"),
    (0x04000202, "REG_IF", "CONFIRMADO", "interrupt flags - GBATEK"),
    (0x04000208, "REG_IME", "CONFIRMADO", "interrupt master enable - GBATEK"),
    (0x020258B8, "gBagSlots_slot0", "CONFIRMADO", "slot 0 da mochila {id:u16, qty:u16} - README do projeto"),
    (0x08000A38, "SetGpuReg", "CONFIRMADO", "rotina por-frame usada no hook v3 - README"),
    (0x03003118, "gKeysMirror_HIPOTESE", "HIPOTESE", "espelho de teclas contexto-dependente - HANDOFF"),
]


def log(msg: str) -> None:
    print(f"[pyghidra] {msg}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# bootstrap do Ghidra (JRE é suficiente)
# ---------------------------------------------------------------------------
def find_ghidra_dir(explicit: str | None) -> Path | None:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("GHIDRA_INSTALL_DIR"):
        candidates.append(Path(os.environ["GHIDRA_INSTALL_DIR"]))
    home = Path.home()
    candidates += [
        home / ".local/opt/re-tools/ghidra_12.1.4_PUBLIC",
        Path("/opt/ghidra_12.1.4_PUBLIC"),
        Path("/usr/share/ghidra"),
    ]
    candidates += sorted(home.glob("ghidra_*_PUBLIC"), reverse=True)
    candidates += sorted((home / "opt").glob("ghidra_*_PUBLIC"), reverse=True)
    candidates += sorted((home / ".local/opt").glob("ghidra_*_PUBLIC"), reverse=True)
    for candidate in candidates:
        if (candidate / "support/LaunchSupport.jar").is_file():
            return candidate
    return None


def find_java_home(explicit: str | None) -> Path | None:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("JAVA_HOME"):
        candidates.append(Path(os.environ["JAVA_HOME"]))
    candidates += [
        Path.home() / ".local/opt/re-tools/jdk-21",
        Path("/usr/lib/jvm/default-java"),
    ]
    candidates += sorted((Path.home() / ".local/opt/re-tools").glob("jdk*"))
    candidates += sorted((Path.home() / ".local/opt").glob("jdk*"))
    for candidate in candidates:
        if (candidate / "bin/java").is_file():
            return candidate
    # último recurso: java do PATH
    java_bin = shutil.which("java")
    if java_bin:
        home = Path(java_bin).resolve().parent.parent
        if (home / "bin/java").is_file():
            return home
    return None


def start_ghidra(ghidra_dir: Path, java_home: Path | None, verbose: bool = False):
    try:
        from pyghidra.launcher import HeadlessPyGhidraLauncher
    except ImportError:
        log("PyGhidra não está instalado. Rode: python3 -m pip install pyghidra")
        sys.exit(EXIT_PREREQ)

    os.environ["GHIDRA_INSTALL_DIR"] = str(ghidra_dir)
    launcher = HeadlessPyGhidraLauncher(verbose=verbose, install_dir=ghidra_dir)

    # O launcher padrão chama `LaunchSupport -jdk_home` e recusa JRE.
    # O setter público `java_home` pula essa validação (aceita JRE 21+).
    if java_home is not None:
        launcher.java_home = java_home
        if not (java_home / "bin/javac").is_file():
            log(f"usando JRE {java_home} (sem javac): scripts Java não rodam, este motor roda")

    try:
        launcher.start()
    except Exception as exc:  # noqa: BLE001
        log(f"falha ao iniciar o Ghidra: {exc}")
        sys.exit(EXIT_PREREQ)

    from java.lang import System

    log(
        "Ghidra iniciado: java %s em %s"
        % (System.getProperty("java.version"), System.getProperty("java.home"))
    )
    return launcher


# ---------------------------------------------------------------------------
# import + preparação do programa
# ---------------------------------------------------------------------------
def import_rom(rom: Path, project_dir: Path, project_name: str, mirrors: bool) -> tuple:
    from java.io import File
    from java.lang import Object
    from ghidra.formats.gfilesystem import FileSystemService
    from ghidra.program.model.lang import LanguageID
    from ghidra.program.util import DefaultLanguageService
    from pyghidra.api import open_project, program_loader, task_monitor

    project_dir.mkdir(parents=True, exist_ok=True)
    project = open_project(project_dir, project_name, create=True)
    monitor = task_monitor()

    language = DefaultLanguageService.getLanguageService().getLanguage(LanguageID(LANGUAGE_ID))
    if language is None:
        raise RuntimeError(f"linguagem {LANGUAGE_ID} não existe nesta instalação do Ghidra")

    fsrl = FileSystemService.getInstance().getLocalFS().getLocalFSRL(File(str(rom)))
    results = (
        program_loader()
        .source(fsrl)
        .loaders("BinaryLoader")
        .addLoaderArg("-loader-baseAddr", f"0x{ROM_BASE:08X}")
        .addLoaderArg("-loader-blockName", ROM_BLOCK_NAME)
        .language(language)
        .project(project)
        .projectFolderPath("/")
        .monitor(monitor)
        .load()
    )

    consumer = Object()
    program = results.getPrimaryDomainObject(consumer)
    log(f"importado: {program.getName()} "
        f"({program.getMemory().getBlock(ROM_BLOCK_NAME).getSize()} bytes)")
    return project, program, consumer, results


def java_addr(program, offset: int):
    return program.getAddressFactory().getDefaultAddressSpace().getAddress(offset)


def create_regions(program, mirrors: bool) -> dict:
    from pyghidra.api import transaction

    created, existing, warnings = [], [], []
    memory = program.getMemory()
    with transaction(program, "GBA: mapa de memoria"):
        for name, start, size, r, w, x, note in list(REGIONS) + (MIRRORS if mirrors else []):
            block = memory.getBlock(name)
            if block is not None:
                existing.append({"name": name, "start": f"0x{block.getStart().getOffset():08X}",
                                 "size": block.getSize()})
                continue
            address = java_addr(program, start)
            if memory.getBlock(address) is not None:
                warnings.append(f"{name}: 0x{start:08X} ja mapeado")
                continue
            try:
                block = memory.createUninitializedBlock(name, address, size, False)
                block.setPermissions(r, w, x)
                block.setComment(note)
                created.append({"name": name, "start": f"0x{start:08X}", "size": size,
                                "read": r, "write": w, "execute": x, "note": note})
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"{name}: {type(exc).__name__}: {exc}")
    return {"created": created, "existing": existing, "warnings": warnings}


def apply_labels(program) -> list:
    from pyghidra.api import transaction
    from ghidra.program.model.listing import CodeUnit
    from ghidra.program.model.symbol import SourceType

    out = []
    table = program.getSymbolTable()
    listing = program.getListing()
    with transaction(program, "GBA: rotulos"):
        for address, name, confidence, comment in LABELS:
            addr = java_addr(program, address)
            try:
                symbol = table.createLabel(addr, name, SourceType.USER_DEFINED)
                listing.setComment(addr, CodeUnit.PLATE_COMMENT, f"[{confidence}] {comment}")
                out.append({"address": f"0x{address:08X}", "name": name,
                            "confidence": confidence, "ok": True})
            except Exception as exc:  # noqa: BLE001
                out.append({"address": f"0x{address:08X}", "name": name,
                            "confidence": confidence, "ok": False, "error": str(exc)})
    return out


def read_header(program) -> dict:
    memory = program.getMemory()
    addr = java_addr(program, ROM_BASE)
    block = memory.getBlock(addr)
    if block is None or block.getSize() < 0xC0:
        return {"available": False, "reason": "bloco da ROM ausente ou menor que 0xC0"}
    from jpype import JArray, JByte

    buf = JArray(JByte)(0xC0)
    memory.getBytes(addr, buf)
    data = bytes((int(b) & 0xFF) for b in buf)
    header = parse_header(data)
    if block.getSize() >= 0xC4:
        header["word_at_0xC0"] = f"0x{memory.getInt(java_addr(program, ROM_BASE + 0xC0)) & 0xFFFFFFFF:08X}"
    else:
        header["word_at_0xC0"] = None
    return header


def set_thumb_context(program, address: int) -> str:
    from pyghidra.api import transaction
    from java.math import BigInteger

    language = program.getLanguage()
    register = language.getRegister("TMode") or language.getRegister("TBmode")
    if register is None:
        raise RuntimeError(f"registrador de contexto Thumb ausente em {language.getLanguageID()}")
    addr = java_addr(program, address)
    with transaction(program, "GBA: contexto Thumb"):
        program.getProgramContext().setValue(register, addr, addr, BigInteger.valueOf(1))
    return register.getName()


def seed_entry_points(program, rom_size: int) -> list:
    from pyghidra.api import task_monitor, transaction
    from ghidra.app.cmd.function import CreateFunctionCmd
    from ghidra.program.disassemble import Disassembler
    from ghidra.program.model.symbol import SourceType

    memory = program.getMemory()
    monitor = task_monitor()
    seeds = []
    first = memory.getInt(java_addr(program, ROM_BASE)) & 0xFFFFFFFF
    target = arm_branch_target(ROM_BASE, first)
    seeds.append({"address": f"0x{ROM_BASE:08X}", "word": f"0x{first:08X}",
                  "decoded_target": None if target is None else f"0x{target:08X}"})
    if target is None or not (ROM_BASE <= target < ROM_BASE + rom_size):
        return seeds

    with transaction(program, "GBA: seed ARM"):
        cmd = CreateFunctionCmd("gba_entry_arm", java_addr(program, target), None,
                                SourceType.USER_DEFINED)
        created = bool(cmd.applyTo(program, monitor))
    seeds.append({"address": f"0x{target:08X}", "mode": "ARM", "method": "branch-decode",
                  "confidence": "CONFIRMADO", "created": created})

    # heuristica Thumb: ldr rX,[pc,#imm] -> literal impar
    thumb = None
    try:
        word = memory.getInt(java_addr(program, target)) & 0xFFFFFFFF
        if (word & 0xFFFFF000) == 0xE59F0000:
            literal_addr = target + 8 + (word & 0xFFF)
            if ROM_BASE <= literal_addr < ROM_BASE + rom_size - 4:
                value = memory.getInt(java_addr(program, literal_addr)) & 0xFFFFFFFF
                if value & 1 and ROM_BASE <= (value & ~1) < ROM_BASE + rom_size:
                    thumb = value & ~1
    except Exception:  # noqa: BLE001
        thumb = None

    if thumb is None:
        seeds.append({"mode": "Thumb", "skipped": "nenhum ponteiro Thumb por ldr literal"})
        return seeds

    try:
        register = set_thumb_context(program, thumb)
        with transaction(program, "GBA: seed Thumb"):
            disassembler = Disassembler.getDisassembler(program, monitor, None)
            disassembler.disassemble(java_addr(program, thumb), None)
            cmd = CreateFunctionCmd("gba_entry_thumb_guess", java_addr(program, thumb), None,
                                    SourceType.USER_DEFINED)
            created = bool(cmd.applyTo(program, monitor))
        seeds.append({"address": f"0x{thumb:08X}", "mode": "Thumb",
                      "method": "arm-ldr-literal-bit0", "context_register": register,
                      "confidence": "HIPOTESE", "created": created})
    except Exception as exc:  # noqa: BLE001
        seeds.append({"address": f"0x{thumb:08X}", "mode": "Thumb", "error": str(exc)})
    return seeds


def run_analysis(program) -> dict:
    from pyghidra.api import analyze, task_monitor

    start = time.time()
    log("auto-análise em andamento (pode demorar em ROMs grandes)...")
    try:
        log_text = analyze(program, task_monitor())
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "seconds": round(time.time() - start, 1), "log_lines": len(log_text.splitlines())}


def summarize(program) -> dict:
    manager = program.getFunctionManager()
    rom_block = program.getMemory().getBlock(ROM_BLOCK_NAME)
    rom_end = ROM_BASE + (rom_block.getSize() if rom_block else 0)

    functions = []
    iterator = manager.getFunctions(True)
    while iterator.hasNext() and len(functions) < 60:
        function = iterator.next()
        entry = function.getEntryPoint().getOffset()
        if ROM_BASE <= entry < rom_end:
            functions.append({"name": function.getName(), "entry": f"0x{entry:08X}",
                              "body_size": int(function.getBody().getNumAddresses())})

    symbols = 0
    iterator = program.getSymbolTable().getAllSymbols(True)
    while iterator.hasNext():
        iterator.next()
        symbols += 1

    anchors = {}
    for _, name, confidence, _ in LABELS:
        found = program.getSymbolTable().getGlobalSymbols(name)
        if found and not found.isEmpty():
            anchors[name] = f"0x{found.get(0).getAddress().getOffset():08X}"
        else:
            anchors[name] = None

    return {
        "function_count": manager.getFunctionCount(),
        "symbol_count": symbols,
        "reference_destination_count": program.getReferenceManager().getReferenceDestinationCount(),
        "reference_source_count": program.getReferenceManager().getReferenceSourceCount(),
        "rom_functions": functions,
        "anchors": anchors,
    }


def decompile_entry(program, function_name: str = "gba_entry_arm", limit: int = 4000) -> dict:
    from ghidra.app.decompiler import DecompInterface
    from pyghidra.api import task_monitor

    table = program.getSymbolTable()
    found = table.getGlobalSymbols(function_name)
    if not found or found.isEmpty():
        return {"ok": False, "reason": f"símbolo {function_name} não existe"}
    address = found.get(0).getAddress()
    function = program.getFunctionManager().getFunctionAt(address)
    if function is None:
        return {"ok": False, "reason": f"não há função em {address}"}

    interface = DecompInterface()
    interface.openProgram(program)
    try:
        result = interface.decompileFunction(function, 60, task_monitor())
        if not result.decompileCompleted():
            return {"ok": False, "reason": result.getErrorMessage()}
        code = result.getDecompiledFunction().getC()
        return {"ok": True, "function": function_name,
                "address": f"0x{address.getOffset():08X}",
                "c_code": code[:limit]}
    finally:
        interface.dispose()


# ---------------------------------------------------------------------------
# self-test (sem ROM comercial e sem Ghidra)
# ---------------------------------------------------------------------------
def offline_self_test() -> int:
    from gba_rom_header import self_test as header_self_test

    failures = 0
    if header_self_test() != 0:
        failures += 1
    vectors = [(0x08000000, 0xEA00002E, 0x080000C0), (0x08000000, 0xEAFFFFFE, 0x08000000)]
    for pc, word, expected in vectors:
        got = arm_branch_target(pc, word)
        if got != expected:
            print(f"[self-test] FALHA branch 0x{word:08X}: {got!r} != {expected!r}")
            failures += 1
    if failures == 0:
        print("[self-test] OK  motor Python: cabeçalho + branch conferem")
        return EXIT_OK
    return EXIT_FAIL


# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Importa ROM de GBA no Ghidra via PyGhidra (funciona sem JDK).")
    parser.add_argument("rom", nargs="?", type=Path, help="ROM .gba")
    parser.add_argument("--ghidra-dir", help="instalação do Ghidra (padrão: GHIDRA_INSTALL_DIR)")
    parser.add_argument("--java-home", help="JRE/JDK a usar (padrão: JAVA_HOME ou ~/.local/opt)")
    parser.add_argument("--project-dir", type=Path,
                        default=Path.home() / ".local/opt/re-tools/ghidra-projects")
    parser.add_argument("--project-name", default="")
    parser.add_argument("--evidence", type=Path, default=REPO_ROOT / "reports/ghidra")
    parser.add_argument("--no-analysis", action="store_true", help="não roda auto-análise")
    parser.add_argument("--mirrors", action="store_true", help="mapeia 0x0A/0x0C/0x0E")
    parser.add_argument("--decompile", action="store_true", help="descompila a entrada ARM")
    parser.add_argument("--json", action="store_true", help="imprime o relatório JSON no stdout")
    parser.add_argument("--self-test", action="store_true", help="testes offline")
    args = parser.parse_args(argv)

    if args.self_test:
        return offline_self_test()
    if args.rom is None:
        parser.print_usage(sys.stderr)
        log("erro: informe a ROM (ou --self-test)")
        return EXIT_USAGE
    if not args.rom.is_file():
        log(f"erro: ROM não encontrada: {args.rom}")
        return EXIT_USAGE

    ghidra_dir = find_ghidra_dir(args.ghidra_dir)
    if ghidra_dir is None:
        log("Ghidra não encontrado. Rode scripts/setup_re_tools.sh ou defina GHIDRA_INSTALL_DIR.")
        return EXIT_PREREQ
    java_home = find_java_home(args.java_home)
    if java_home is None:
        log("Java não encontrado. Rode scripts/setup_re_tools.sh ou defina JAVA_HOME.")
        return EXIT_PREREQ

    start_ghidra(ghidra_dir, java_home)

    project_name = args.project_name or f"gba_{time.strftime('%Y%m%d_%H%M%S')}"
    rom_size = args.rom.stat().st_size
    import hashlib

    sha = hashlib.sha256(args.rom.read_bytes()).hexdigest()
    report = {
        "schema": "gba-prepare/pyghidra-v1",
        "engine": "pyghidra",
        "rom": str(args.rom),
        "rom_size": rom_size,
        "rom_sha256": sha,
        "language_id": LANGUAGE_ID,
        "ghidra_dir": str(ghidra_dir),
        "java_home": str(java_home),
        "project": f"{args.project_dir}/{project_name}",
    }

    project = None
    program = None
    consumer = None
    results = None
    try:
        project, program, consumer, results = import_rom(
            args.rom, args.project_dir, project_name, args.mirrors)
        report["rom_block"] = {
            "name": ROM_BLOCK_NAME,
            "size": int(program.getMemory().getBlock(ROM_BLOCK_NAME).getSize()),
            "start": f"0x{ROM_BASE:08X}",
        }
        report["header"] = read_header(program)
        regions = create_regions(program, args.mirrors)
        report["regions"] = regions
        report["labels"] = apply_labels(program)
        report["seeds"] = seed_entry_points(program, rom_size)

        if not args.no_analysis:
            report["analysis_run"] = run_analysis(program)
        report["summary"] = summarize(program)
        if args.decompile:
            report["decompiled"] = decompile_entry(program)

        args.evidence.mkdir(parents=True, exist_ok=True)
        out = args.evidence / "gba_prepare_pyghidra.json"
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        log(f"evidência escrita: {out}")

        # salvar o programa no projeto
        from pyghidra.api import task_monitor
        results.save(task_monitor())
        log(f"programa salvo no projeto {report['project']}")
    finally:
        if program is not None and consumer is not None:
            program.release(consumer)
        if project is not None:
            project.close()

    summary = report.get("summary", {})
    log(f"funções: {summary.get('function_count')} | símbolos: {summary.get('symbol_count')} "
        f"| refs: {summary.get('reference_destination_count')}/{summary.get('reference_source_count')}")
    header = report.get("header", {})
    if header.get("available"):
        log(f"cabeçalho: {header.get('title')!r} {header.get('game_code')!r} "
            f"complemento {'OK' if header.get('complement_ok') else 'FALHA'}")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
