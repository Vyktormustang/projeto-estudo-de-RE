// Executor de ferramentas binutils/gcc (arm-none-eabi) compiladas para WASM.
// Uso: node wtool.mjs <as|ld|cc1|objcopy> <host_cwd> [args...]
//   WT_STDIN=1  -> passa o stdin do host como stdin da ferramenta
// Saidas: qualquer arquivo novo criado no MEMFS + os alvos de -o / -Map.
import { readFile, writeFile, mkdir, readdir, stat, access } from "node:fs/promises";
import path from "node:path";
import { constants as FSC } from "node:fs";

const PKG = "/tmp/pkg/package/wasm";
const tool = process.argv[2];
const cwdHost = path.resolve(process.argv[3]);
const args = process.argv.slice(4);

const GLUE = { as: "arm-none-eabi-as", ld: "arm-none-eabi-ld", objcopy: "arm-none-eabi-objcopy", cc1: "cc1-arm" }[tool];
if (!GLUE) { console.error("tool desconhecida: " + tool); process.exit(2); }

const wasmBinary = await readFile(`${PKG}/${GLUE}.wasm`);
const factory = (await import(`${PKG}/${GLUE}.mjs`)).default;

let log = "";
let stdinBuf = null;
if (process.env.WT_STDIN === "1") {
  const chunks = [];
  for await (const c of process.stdin) chunks.push(c);
  stdinBuf = Buffer.concat(chunks);
}

const moduleArgs = {
  wasmBinary,
  noInitialRun: true,
  print: (m) => { log += m + "\n"; },
  printErr: (m) => { log += m + "\n"; },
};
if (stdinBuf) {
  let i = 0;
  moduleArgs.stdin = () => (i < stdinBuf.length ? stdinBuf[i++] : null);
}

const mod = await factory(moduleArgs);
const FS = mod.FS;

function ensureDir(dir) {
  const parts = dir.split("/").filter(Boolean);
  let cur = "";
  for (const p of parts) { cur += "/" + p; try { FS.mkdir(cur); } catch {} }
}
// caminho do host -> caminho no MEMFS (absolutos ficam como estao)
function vfsOf(p) {
  const q = p.replace(/\\/g, "/");
  return q.startsWith("/") ? path.posix.normalize(q) : path.posix.normalize("/work/" + q);
}
async function mountDir(hostDir, vfsDir) {
  ensureDir(vfsDir);
  let ents;
  try { ents = await readdir(hostDir, { withFileTypes: true }); } catch { return; }
  for (const e of ents) {
    const hp = path.join(hostDir, e.name);
    const mp = vfsDir + "/" + e.name;
    if (e.isDirectory()) await mountDir(hp, mp);
    else if (e.isFile()) { try { FS.writeFile(mp, new Uint8Array(await readFile(hp))); } catch {} }
  }
}
async function mountOne(a) {
  const hp = path.resolve(cwdHost, a);
  let st;
  try { st = await stat(hp); } catch { return false; }
  const vp = vfsOf(a);
  if (st.isDirectory()) { await mountDir(hp, vp); return true; }
  ensureDir(path.posix.dirname(vp));
  FS.writeFile(vp, new Uint8Array(await readFile(hp)));
  return true;
}

const CON_ARG = new Set(["-o", "-I", "-iquote", "-isystem", "-L", "-l", "-T", "-Map", "--Map",
  "-D", "-U", "-include", "-imacros", "-Xlinker", "-Xassembler", "--defsym"]);

ensureDir("/work");

// Monta os .include (recursivo) que o assembler vai precisar no MEMFS.
async function montaIncludes(texto) {
  const vistos = new Set();
  const fila = [];
  const varre = (txt) => {
    for (const m of txt.matchAll(/\.include\s+"([^"]+)"/g)) fila.push(m[1]);
    for (const m of txt.matchAll(/\.incbin\s+"([^"]+)"/g)) fila.push(m[1]);
  };
  varre(texto);
  while (fila.length) {
    const rel = fila.shift();
    if (vistos.has(rel)) continue;
    vistos.add(rel);
    let dados;
    try { dados = await readFile(path.resolve(cwdHost, rel)); } catch { continue; }
    const vp = vfsOf(rel);
    ensureDir(path.posix.dirname(vp));
    FS.writeFile(vp, new Uint8Array(dados));
    if (rel.endsWith(".inc") || rel.endsWith(".s")) varre(dados.toString("utf8"));
  }
}

// 1) stdin
const temEntrada = args.some((a, i) => !a.startsWith("-") && !CON_ARG.has(args[i - 1] ?? ""));
if (stdinBuf) {
  const vp = tool === "cc1" ? "/work/stdin.i" : "/work/stdin.s";
  FS.writeFile(vp, new Uint8Array(stdinBuf));
  const idx = args.indexOf("-");
  if (idx >= 0) args[idx] = vp;
  else if (!temEntrada) args.push(vp);
  // GNU as resolve .include relativo ao cwd: monta os arquivos citados
  if (tool === "as") await montaIncludes(stdinBuf.toString("utf8"));
}

// 2) monta entradas e diretorios de include/lib
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  const prev = args[i - 1] ?? "";
  if (prev === "-o" || prev === "-Map" || prev === "--Map") continue;
  if (prev === "-I" || prev === "-iquote" || prev === "-isystem" || prev === "-L" || prev === "-T") {
    await mountOne(a); continue;
  }
  if (a.startsWith("-I") && a.length > 2) { await mountOne(a.slice(2)); continue; }
  if (a.startsWith("-L") && a.length > 2) { await mountOne(a.slice(2)); continue; }
  if (a.startsWith("-T") && a.length > 2) { await mountOne(a.slice(2)); continue; }
  if (a.startsWith("-")) continue;
  const ok = await mountOne(a);
  if (ok && tool === "as" && a.endsWith(".s")) {
    try { await montaIncludes(await readFile(path.resolve(cwdHost, a), "utf8")); } catch {}
  }
}

// 3) saidas declaradas
const outputs = [];
for (let i = 0; i < args.length; i++) {
  if ((args[i] === "-o" || args[i] === "-Map" || args[i] === "--Map") && i + 1 < args.length) outputs.push(args[i + 1]);
}
// objcopy usa `objcopy ENTRADA SAIDA` (sem -o). Sem isto, a .gba final nunca era
// regravada e o build "passava" entregando a ROM do build anterior.
if (tool === "objcopy") {
  const pos = [];
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a.startsWith("-")) continue;
    if (["-I", "-O", "--input-target", "--output-target", "-j", "--only-section",
         "-R", "--remove-section", "--change-section-address", "--set-section-flags",
         "-i", "--info"].includes(args[i - 1] ?? "")) continue;
    pos.push(a);
  }
  if (pos.length >= 2) outputs.push(pos[pos.length - 1]);
}
for (const o of outputs) ensureDir(path.posix.dirname(vfsOf(o)));

// 4) snapshot do host (para detectar arquivos novos)
const antes = new Set();
async function scan(hostDir, rel) {
  let ents;
  try { ents = await readdir(hostDir, { withFileTypes: true }); } catch { return; }
  for (const e of ents) {
    const r = rel ? rel + "/" + e.name : e.name;
    if (e.isDirectory()) await scan(path.join(hostDir, e.name), r);
    else antes.add(r);
  }
}
await scan(cwdHost, "");

FS.chdir("/work");
let exitCode = 0;
try {
  mod.callMain(args);
} catch (e) {
  if (e && typeof e === "object" && "status" in e) exitCode = e.status ?? 0;
  else { log += `\n[runner] abort: ${e?.message ?? e}\n`; exitCode = exitCode || 1; }
}
process.stderr.write(log);  // logs do linker/compilador vao p/ stderr

// 5) coleta: arquivos novos no MEMFS + saidas declaradas
async function walk(vdir, rel) {
  let ents;
  try { ents = FS.readdir(vdir); } catch { return; }
  for (const name of ents) {
    if (name === "." || name === "..") continue;
    const vp = vdir + "/" + name;
    const r = rel ? rel + "/" + name : name;
    let st;
    try { st = FS.stat(vp); } catch { continue; }
    if (FS.isDir(st.mode)) { await walk(vp, r); continue; }
    if (antes.has(r)) continue;
    await salva(vp, r);
  }
}
async function salva(vp, rel) {
  try {
    const bytes = FS.readFile(vp);
    const hp = path.resolve(cwdHost, rel);
    await mkdir(path.dirname(hp), { recursive: true });
    await writeFile(hp, Buffer.from(bytes));
  } catch (e) {
    process.stderr.write(`[runner] falha ao gravar ${rel}: ${e?.message ?? e}\n`);
  }
}
await walk("/work", "");

// Saidas declaradas (-o / -Map) sao SEMPRE gravadas. Antes havia um `continue`
// quando o arquivo ja existia no host, e o efeito era cruel: o linker rodava,
// reportava sucesso e o .elf/.gba ficavam congelados no build anterior.
for (const o of outputs) {
  const vp = vfsOf(o);
  try { await salva(vp, o); } catch {}
}
process.exit(exitCode);
