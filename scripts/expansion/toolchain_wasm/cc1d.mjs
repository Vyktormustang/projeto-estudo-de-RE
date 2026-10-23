// Daemon do cc1 (GCC 14.2 em WASM): compila o modulo WebAssembly UMA vez e
// reaproveita para cada arquivo, eliminando ~1.7s de instanciacao por chamada.
import { readFile } from "node:fs/promises";
import net from "node:net";

const SOCK = process.argv[2];
const PKG = "/tmp/pkg/package/wasm";
const STATS = process.env.CC1_STATS === "1";

const wasmBinary = await readFile(`${PKG}/cc1-arm.wasm`);
const factory = (await import(`${PKG}/cc1-arm.mjs`)).default;
const compilado = await WebAssembly.compile(wasmBinary);

const instancia = async (argv, stdinBuf) => {
  let log = "";
  const moduleArgs = {
    noInitialRun: true,
    print: (m) => { log += m + "\n"; },
    printErr: (m) => { log += m + "\n"; },
    instantiateWasm: (info, cb) => {
      WebAssembly.instantiate(compilado, info).then((i) => cb(i, compilado));
      return {};
    },
  };
  if (stdinBuf) {
    let i = 0;
    moduleArgs.stdin = () => (i < stdinBuf.length ? stdinBuf[i++] : null);
  }
  const mod = await factory(moduleArgs);
  ensureDir(mod.FS, "/work");
  let code = 0;
  try { mod.callMain(argv); } catch (e) {
    if (e && typeof e === "object" && "status" in e) code = e.status ?? 0;
    else { log += `\n[cc1d] ${e?.message ?? e}\n`; code = code || 1; }
  }
  return { code, log, FS: mod.FS };
};

function ensureDir(FS, dir) {
  const parts = dir.split("/").filter(Boolean);
  let cur = "";
  for (const p of parts) { cur += "/" + p; try { FS.mkdir(cur); } catch {} }
}

const servidor = net.createServer((sock) => {
  let buf = "";
  sock.on("data", async (d) => {
    buf += d.toString("utf8");
    const nl = buf.indexOf("\n");
    if (nl < 0) return;
    const linha = buf.slice(0, nl);
    buf = buf.slice(nl + 1);
    let resp;
    try {
      const job = JSON.parse(linha);
      const argv = job.argv;
      // arquivos de entrada textuais (o .i vem por stdin normalmente)
      const std = job.stdin ? Buffer.from(job.stdin, "base64") : null;
      const outVfs = job.out;
      const t0 = Date.now();
      const { code, log, FS } = await instancia(argv, std);
      ensureDir(FS, "/work");
      let out = null;
      try { out = Buffer.from(FS.readFile(outVfs)).toString("base64"); } catch {}
      resp = { code, log, out, ms: Date.now() - t0 };
      if (STATS) process.stderr.write(`[cc1d] ${job.tag ?? ""} ${resp.ms}ms code=${code}\n`);
    } catch (e) {
      resp = { code: 1, log: String(e && e.stack || e), out: null };
    }
    sock.end(JSON.stringify(resp) + "\n");
  });
});
servidor.listen(SOCK, () => process.stderr.write(`[cc1d] ouvindo em ${SOCK}\n`));
