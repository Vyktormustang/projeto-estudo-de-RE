package br.com.xadrezstudio;

import android.content.Context;
import android.content.res.AssetManager;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;

/**
 * Servidor HTTP mínimo (só 127.0.0.1) que entrega os arquivos de assets/www.
 *
 * Existe porque o WebView não carrega WebAssembly de file:// — com uma origem
 * http:// tudo (ES modules, Worker, wasm) se comporta como no navegador.
 * Não escuta fora do loopback e não aceita caminhos com "..".
 */
public class ServidorLocal {

    private final AssetManager assets;
    private ServerSocket servidor;
    private Thread thread;
    private volatile boolean rodando;
    private int porta;

    public ServidorLocal(Context contexto) {
        this.assets = contexto.getAssets();
    }

    public int porta() {
        return porta;
    }

    public void iniciar() throws IOException {
        for (int candidata = 8791; candidata <= 8810; candidata++) {
            try {
                ServerSocket s = new ServerSocket();
                s.setReuseAddress(true);
                s.bind(new InetSocketAddress(InetAddress.getByName("127.0.0.1"), candidata));
                this.servidor = s;
                this.porta = candidata;
                break;
            } catch (IOException ocupada) {
                // porta em uso: tenta a próxima
            }
        }
        if (this.servidor == null) {
            throw new IOException("nenhuma porta livre entre 8791 e 8810");
        }

        rodando = true;
        thread = new Thread(new Runnable() {
            @Override
            public void run() {
                while (rodando) {
                    try {
                        final Socket cliente = servidor.accept();
                        Thread atendimento = new Thread(new Runnable() {
                            @Override
                            public void run() {
                                atender(cliente);
                            }
                        });
                        atendimento.setDaemon(true);
                        atendimento.start();
                    } catch (IOException erro) {
                        if (!rodando) break;
                    }
                }
            }
        }, "xadrez-http");
        thread.setDaemon(true);
        thread.start();
    }

    public void parar() {
        rodando = false;
        try {
            if (servidor != null) servidor.close();
        } catch (IOException ignorado) {
            // fechando de qualquer forma
        }
    }

    private void atender(Socket cliente) {
        Socket socket = cliente;
        try {
            socket.setSoTimeout(20000);
            BufferedReader entrada = new BufferedReader(
                    new InputStreamReader(socket.getInputStream(), "UTF-8"));

            String linha = entrada.readLine();
            if (linha == null || linha.length() == 0) {
                return;
            }
            String[] partes = linha.split(" ");
            String caminho = partes.length > 1 ? partes[1] : "/";

            int interrogacao = caminho.indexOf('?');
            if (interrogacao >= 0) {
                caminho = caminho.substring(0, interrogacao);
            }
            if (caminho.equals("/") || caminho.length() == 0) {
                caminho = "/index.html";
            }
            if (caminho.startsWith("/")) {
                caminho = caminho.substring(1);
            }
            if (caminho.contains("..")) {
                responder(socket, 400, "text/plain; charset=utf-8", "caminho inválido".getBytes("UTF-8"));
                return;
            }

            byte[] dados;
            try {
                dados = lerAsset("www/" + caminho);
            } catch (IOException naoExiste) {
                responder(socket, 404, "text/plain; charset=utf-8", "não encontrado".getBytes("UTF-8"));
                return;
            }
            responder(socket, 200, tipoDe(caminho), dados);
        } catch (IOException ignorado) {
            // conexão caiu: nada a fazer
        } finally {
            try { socket.close(); } catch (IOException ignorado) { }
        }
    }

    private void responder(Socket socket, int codigo, String tipo, byte[] corpo) throws IOException {
        OutputStream saida = socket.getOutputStream();
        String cabecalho = "HTTP/1.1 " + codigo + (codigo == 200 ? " OK" : " Erro") + "\r\n"
                + "Content-Type: " + tipo + "\r\n"
                + "Content-Length: " + corpo.length + "\r\n"
                + "Cache-Control: no-store\r\n"
                + "Access-Control-Allow-Origin: *\r\n"
                + "Connection: close\r\n\r\n";
        saida.write(cabecalho.getBytes("UTF-8"));
        saida.write(corpo);
        saida.flush();
    }

    private byte[] lerAsset(String nome) throws IOException {
        InputStream entrada = assets.open(nome);
        try {
            ByteArrayOutputStream acumulado = new ByteArrayOutputStream();
            byte[] buffer = new byte[8192];
            int lidos;
            while ((lidos = entrada.read(buffer)) > 0) {
                acumulado.write(buffer, 0, lidos);
            }
            return acumulado.toByteArray();
        } finally {
            entrada.close();
        }
    }

    private static String tipoDe(String caminho) {
        String nome = caminho.toLowerCase();
        if (nome.endsWith(".html")) return "text/html; charset=utf-8";
        if (nome.endsWith(".js") || nome.endsWith(".mjs")) return "text/javascript; charset=utf-8";
        if (nome.endsWith(".css")) return "text/css; charset=utf-8";
        if (nome.endsWith(".json")) return "application/json; charset=utf-8";
        if (nome.endsWith(".wasm")) return "application/wasm";
        if (nome.endsWith(".svg")) return "image/svg+xml";
        if (nome.endsWith(".png")) return "image/png";
        if (nome.endsWith(".ico")) return "image/x-icon";
        if (nome.endsWith(".woff2")) return "font/woff2";
        return "application/octet-stream";
    }
}
