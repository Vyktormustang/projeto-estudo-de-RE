package br.forja.apice;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.ViewGroup;
import android.view.Window;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

public final class MainActivity extends Activity {
    private static final String VIRTUAL_HOST = "forja.local";
    private static final String START_URL = "https://forja.local/index.html";
    private static final int FILE_CHOOSER_REQ_CODE = 4201;

    private WebView webView;
    private ValueCallback<Uri[]> pendingFileCallback;

    @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        Window window = getWindow();
        if (window != null) {
            window.setStatusBarColor(Color.parseColor("#080A0F"));
            window.setNavigationBarColor(Color.parseColor("#0B0E15"));
        }

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.parseColor("#080A0F"));

        webView = new WebView(this);
        webView.setBackgroundColor(Color.parseColor("#080A0F"));
        webView.setOverScrollMode(WebView.OVER_SCROLL_NEVER);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setTextZoom(100);
        settings.setCacheMode(WebSettings.LOAD_NO_CACHE);

        webView.addJavascriptInterface(new NativeBridge(this, webView), "ForjaNative");

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                if (request == null || request.getUrl() == null) {
                    return forbiddenResponse();
                }
                Uri uri = request.getUrl();
                String host = uri.getHost();
                if (host == null || !VIRTUAL_HOST.equalsIgnoreCase(host)) {
                    // Bloqueia 100% de qualquer requisicao externa
                    return forbiddenResponse();
                }

                String rawPath = uri.getPath();
                if (rawPath == null || rawPath.isEmpty() || "/".equals(rawPath)) {
                    rawPath = "/index.html";
                }
                while (rawPath.startsWith("/")) {
                    rawPath = rawPath.substring(1);
                }
                if (rawPath.contains("..")) {
                    return forbiddenResponse();
                }

                String assetPath = "www/" + rawPath;
                try {
                    InputStream stream = getAssets().open(assetPath);
                    String mime = guessMimeType(rawPath);
                    String encoding = isTextMime(mime) ? "UTF-8" : null;

                    Map<String, String> headers = new HashMap<String, String>();
                    headers.put("Access-Control-Allow-Origin", "*");
                    headers.put("Cache-Control", "no-store");

                    return new WebResourceResponse(mime, encoding, 200, "OK", headers, stream);
                } catch (Exception e) {
                    return notFoundResponse();
                }
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                if (request != null && request.getUrl() != null) {
                    String host = request.getUrl().getHost();
                    if (VIRTUAL_HOST.equalsIgnoreCase(host)) {
                        return false;
                    }
                }
                return true;
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(
                    WebView webView,
                    ValueCallback<Uri[]> filePathCallback,
                    FileChooserParams fileChooserParams
            ) {
                if (pendingFileCallback != null) {
                    pendingFileCallback.onReceiveValue(null);
                }
                pendingFileCallback = filePathCallback;

                try {
                    Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
                    intent.addCategory(Intent.CATEGORY_OPENABLE);
                    intent.setType("*/*");
                    String[] mimeTypes = new String[]{"application/json", "text/plain", "*/*"};
                    intent.putExtra(Intent.EXTRA_MIME_TYPES, mimeTypes);
                    startActivityForResult(
                            Intent.createChooser(intent, "Selecionar Backup FORJA (.json)"),
                            FILE_CHOOSER_REQ_CODE
                    );
                    return true;
                } catch (Exception e) {
                    pendingFileCallback = null;
                    return false;
                }
            }
        });

        root.addView(
                webView,
                new FrameLayout.LayoutParams(
                        ViewGroup.LayoutParams.MATCH_PARENT,
                        ViewGroup.LayoutParams.MATCH_PARENT
                )
        );
        setContentView(root);

        webView.loadUrl(START_URL);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == FILE_CHOOSER_REQ_CODE) {
            if (pendingFileCallback != null) {
                Uri[] results = null;
                if (resultCode == Activity.RESULT_OK && data != null) {
                    Uri uri = data.getData();
                    if (uri != null) {
                        results = new Uri[]{uri};
                    } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                        results = WebChromeClient.FileChooserParams.parseResult(resultCode, data);
                    }
                }
                pendingFileCallback.onReceiveValue(results);
                pendingFileCallback = null;
            }
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
            return;
        }
        moveTaskToBack(true);
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }

    private static String guessMimeType(String path) {
        String lower = path.toLowerCase(Locale.US);
        if (lower.endsWith(".html") || lower.endsWith(".htm")) return "text/html";
        if (lower.endsWith(".js") || lower.endsWith(".mjs")) return "text/javascript";
        if (lower.endsWith(".css")) return "text/css";
        if (lower.endsWith(".json")) return "application/json";
        if (lower.endsWith(".svg")) return "image/svg+xml";
        if (lower.endsWith(".png")) return "image/png";
        if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
        if (lower.endsWith(".webp")) return "image/webp";
        if (lower.endsWith(".woff2")) return "font/woff2";
        return "application/octet-stream";
    }

    private static boolean isTextMime(String mime) {
        return mime.startsWith("text/") || "application/json".equals(mime) || "image/svg+xml".equals(mime);
    }

    private static WebResourceResponse forbiddenResponse() {
        return new WebResourceResponse(
                "text/plain",
                "UTF-8",
                403,
                "Forbidden",
                null,
                new ByteArrayInputStream("Forbidden".getBytes(StandardCharsets.UTF_8))
        );
    }

    private static WebResourceResponse notFoundResponse() {
        return new WebResourceResponse(
                "text/plain",
                "UTF-8",
                404,
                "Not Found",
                null,
                new ByteArrayInputStream("Not Found".getBytes(StandardCharsets.UTF_8))
        );
    }
}
