"""Cliente do daemon cc1 (GCC 14.2 em WASM)."""
import base64, json, os, socket, subprocess, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
SOCK = "/tmp/cc1.%d.sock"
NDAEMONS = int(os.environ.get("CC1_DAEMONS", "3"))


def _daemon(idx):
    """Garante que o daemon esta rodando; devolve o socket path."""
    caminho = SOCK % idx
    if os.path.exists(caminho):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(caminho); s.close()
            return caminho
        except OSError:
            os.unlink(caminho)
    subprocess.Popen(["node", os.path.join(AQUI, "cc1d.mjs"), caminho],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)
    for _ in range(600):
        if os.path.exists(caminho):
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(caminho); s.close()
                return caminho
            except OSError:
                pass
        time.sleep(0.05)
    raise RuntimeError("cc1d nao subiu")


def compila(argv, entrada, out_vfs="/work/out.s"):
    """Envia um trabalho ao daemon e devolve (codigo, log, bytes)."""
    job = {"argv": argv, "stdin": base64.b64encode(entrada).decode() if entrada else None,
           "out": out_vfs}
    linha = (json.dumps(job) + "\n").encode()
    ultimo = None
    # distribui entre varios daemons (o Node e single-thread; 1 daemon = 1 core)
    base = os.getpid() % NDAEMONS
    for idx in [(base + k) % NDAEMONS for k in range(NDAEMONS)]:
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(_daemon(idx))
            s.sendall(linha)
            dados = b""
            while True:
                ped = s.recv(1 << 20)
                if not ped:
                    break
                dados += ped
            s.close()
            resp = json.loads(dados.decode())
            return resp.get("code", 1), resp.get("log", ""), base64.b64decode(resp["out"]) if resp.get("out") else None
        except (ConnectionError, OSError, json.JSONDecodeError) as e:
            ultimo = e
            try:
                os.unlink(SOCK % idx)
            except OSError:
                pass
    raise RuntimeError("daemon cc1 indisponivel: %s" % ultimo)
