package br.forja.apice;

import android.app.Activity;
import android.content.Intent;
import android.os.Build;
import android.view.HapticFeedbackConstants;
import android.view.View;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public final class NativeBridge {
    private static final String VAULT_FILE = "apex_vault_v3.json";
    private static final String VAULT_TMP = "apex_vault_v3.json.tmp";
    private static final String VAULT_BAK = "apex_vault_v3.json.bak";

    private final Activity activity;
    private final View rootView;
    private final Object fileLock = new Object();

    public NativeBridge(Activity activity, View rootView) {
        this.activity = activity;
        this.rootView = rootView;
    }

    @JavascriptInterface
    public String readVault() {
        synchronized (fileLock) {
            File primary = new File(activity.getFilesDir(), VAULT_FILE);
            String data = readFileUtf8(primary);
            if (data != null && data.trim().length() > 2) {
                return data;
            }
            File backup = new File(activity.getFilesDir(), VAULT_BAK);
            return readFileUtf8(backup);
        }
    }

    @JavascriptInterface
    public boolean writeVault(String jsonPayload) {
        if (jsonPayload == null || jsonPayload.length() < 2) {
            return false;
        }
        synchronized (fileLock) {
            File dir = activity.getFilesDir();
            File primary = new File(dir, VAULT_FILE);
            File tmp = new File(dir, VAULT_TMP);
            File bak = new File(dir, VAULT_BAK);

            FileOutputStream fos = null;
            try {
                byte[] bytes = jsonPayload.getBytes(StandardCharsets.UTF_8);
                fos = new FileOutputStream(tmp, false);
                fos.write(bytes);
                fos.flush();
                fos.getFD().sync(); // Garante gravacao fisica atomica em flash NAND
                fos.close();
                fos = null;

                if (primary.exists()) {
                    copyFile(primary, bak);
                }
                if (tmp.renameTo(primary)) {
                    return true;
                }
                // Fallback caso renameTo falhe em filesystem especifico
                copyFile(tmp, primary);
                //noinspection ResultOfMethodCallIgnored
                tmp.delete();
                return true;
            } catch (Exception e) {
                return false;
            } finally {
                if (fos != null) {
                    try {
                        fos.close();
                    } catch (IOException ignored) {
                    }
                }
            }
        }
    }

    @JavascriptInterface
    public void haptic(final String kind) {
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                try {
                    int flag = HapticFeedbackConstants.CLOCK_TICK;
                    if ("heavy".equals(kind) || "success".equals(kind)) {
                        flag = HapticFeedbackConstants.LONG_PRESS;
                    } else if ("medium".equals(kind)) {
                        flag = HapticFeedbackConstants.VIRTUAL_KEY;
                    }
                    rootView.performHapticFeedback(flag);
                } catch (Throwable ignored) {
                }
            }
        });
    }

    @JavascriptInterface
    public void setKeepScreenOn(final boolean enabled) {
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                try {
                    if (enabled) {
                        activity.getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                    } else {
                        activity.getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                    }
                } catch (Throwable ignored) {
                }
            }
        });
    }

    @JavascriptInterface
    public void shareText(final String title, final String content) {
        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                try {
                    Intent sendIntent = new Intent(Intent.ACTION_SEND);
                    sendIntent.setType("application/json");
                    sendIntent.putExtra(Intent.EXTRA_SUBJECT, title != null ? title : "Backup FORJA v3.0");
                    sendIntent.putExtra(Intent.EXTRA_TEXT, content != null ? content : "");
                    Intent chooser = Intent.createChooser(sendIntent, "Exportar Cofre FORJA v3.0");
                    activity.startActivity(chooser);
                } catch (Throwable ignored) {
                }
            }
        });
    }

    @JavascriptInterface
    public String getDeviceInfo() {
        return "Android SDK " + Build.VERSION.SDK_INT + " (" + Build.MODEL + ")";
    }

    private static String readFileUtf8(File file) {
        if (file == null || !file.exists() || !file.isFile()) {
            return null;
        }
        FileInputStream fis = null;
        try {
            fis = new FileInputStream(file);
            ByteArrayOutputStream bos = new ByteArrayOutputStream();
            byte[] buf = new byte[4096];
            int n;
            while ((n = fis.read(buf)) != -1) {
                bos.write(buf, 0, n);
            }
            return new String(bos.toByteArray(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            return null;
        } finally {
            if (fis != null) {
                try {
                    fis.close();
                } catch (IOException ignored) {
                }
            }
        }
    }

    private static void copyFile(File src, File dst) throws IOException {
        FileInputStream in = null;
        FileOutputStream out = null;
        try {
            in = new FileInputStream(src);
            out = new FileOutputStream(dst, false);
            byte[] buf = new byte[4096];
            int n;
            while ((n = in.read(buf)) != -1) {
                out.write(buf, 0, n);
            }
            out.flush();
            out.getFD().sync();
        } finally {
            if (in != null) {
                try {
                    in.close();
                } catch (IOException ignored) {
                }
            }
            if (out != null) {
                try {
                    out.close();
                } catch (IOException ignored) {
                }
            }
        }
    }
}
