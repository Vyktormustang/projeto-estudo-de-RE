#!/usr/bin/env bash
# Decompilação headless com Ghidra — REQUER JDK 21+ e GHIDRA_HOME apontando para uma instalação local.
# Este script existe para ser reproduzível fora deste sandbox (aqui java/Ghidra não são acessíveis).
set -euo pipefail

TARGET="${1:?uso: headless_run.sh <arquivo .so|.dex|.elf> [pasta_projeto]}"
GHIDRA_HOME="${GHIDRA_HOME:?defina GHIDRA_HOME=/caminho/ghidra_PUBLIC}"
PROJ_DIR="${2:-$(pwd)/ghidra_proj}"
PROJ_NAME="apkre"
OUT_DIR="$(pwd)/reports/ghidra"

command -v java >/dev/null 2>&1 || { echo "ERRO: java não encontrado (instale JDK 21+)"; exit 2; }
[ -x "$GHIDRA_HOME/support/analyzeHeadless" ] || { echo "ERRO: analyzeHeadless não encontrado em \$GHIDRA_HOME"; exit 2; }

mkdir -p "$PROJ_DIR" "$OUT_DIR"

# Script de export: decompila funções e grava pseudo-C.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cat > "$SCRIPT_DIR/ExportDecomp.java" <<'JAVA'
//@category apkre
import ghidra.app.decompiler.*;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import java.io.*;
public class ExportDecomp extends GhidraScript {
    @Override public void run() throws Exception {
        String out = System.getenv("APKRE_OUT");
        File f = new File(out + "/" + currentProgram.getName() + ".decomp.c");
        DecompInterface dec = new DecompInterface();
        dec.openProgram(currentProgram);
        try (PrintWriter pw = new PrintWriter(new FileWriter(f))) {
            FunctionManager fm = currentProgram.getFunctionManager();
            for (Function fn : fm.getFunctions(true)) {
                pw.println("/* ==== " + fn.getName() + " @ " + fn.getEntryPoint() + " ==== */");
                DecompileResults r = dec.decompileFunction(fn, 60, monitor);
                pw.println(r != null && r.decompileCompleted() ? r.getDecompiledFunction().getC() : "/* falhou */");
                pw.println();
            }
        }
        println("escrito: " + f.getAbsolutePath());
    }
}
JAVA

export APKRE_OUT="$OUT_DIR"
"$GHIDRA_HOME/support/analyzeHeadless" "$PROJ_DIR" "$PROJ_NAME" \
  -import "$TARGET" -overwrite \
  -scriptPath "$SCRIPT_DIR" -postScript ExportDecomp.java \
  -deleteProject 2>&1 | tail -20

echo "pseudo-C em: $OUT_DIR"
