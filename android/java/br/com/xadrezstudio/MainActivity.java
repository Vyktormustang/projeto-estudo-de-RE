package br.com.xadrezstudio;

import android.app.Activity;
import android.os.Bundle;
import android.view.ViewGroup;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

/**
 * Casca do app: sobe um servidor HTTP local (só loopback) servindo os arquivos de
 * assets/www e aponta o WebView para ele.
 *
 * Por que servidor e não file:// — o motor de xadrez é WebAssembly e o WebView não
 * consegue buscar .wasm por file:// (CORS). Servindo em http://127.0.0.1 tudo
 * funciona igual ao navegador: módulos ES, Web Worker e wasm.
 */
public class MainActivity extends Activity {

    private WebView web;
    private ServidorLocal servidor;

    @Override
    protected void onCreate(Bundle estado) {
        super.onCreate(estado);

        String url;
        try {
            servidor = new ServidorLocal(getApplicationContext());
            servidor.iniciar();
            url = "http://127.0.0.1:" + servidor.porta() + "/index.html?armazenamento=local";
        } catch (Exception erro) {
            // sem servidor local o app ainda abre, mas o motor não carrega
            servidor = null;
            url = "file:///android_asset/www/index.html?armazenamento=local";
        }

        web = new WebView(this);
        WebSettings cfg = web.getSettings();
        cfg.setJavaScriptEnabled(true);
        cfg.setDomStorageEnabled(true);
        cfg.setDatabaseEnabled(true);
        cfg.setMediaPlaybackRequiresUserGesture(false);
        cfg.setBuiltInZoomControls(false);
        cfg.setDisplayZoomControls(false);
        web.setWebViewClient(new WebViewClient());
        web.setBackgroundColor(0xFF312E2B);

        setContentView(web, new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));

        web.loadUrl(url);
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (servidor != null) servidor.parar();
        if (web != null) {
            web.loadUrl("about:blank");
            web.destroy();
            web = null;
        }
        super.onDestroy();
    }
}
