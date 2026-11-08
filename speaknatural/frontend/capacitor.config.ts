import type { CapacitorConfig } from '@capacitor/cli';

/**
 * Configuração do APK Android.
 *
 * server.androidScheme: 'https' é o padrão do Capacitor 6, mas o app acessa o
 * servidor Python por HTTP puro na rede local (192.168.x.x:8000). Por isso:
 *   - cleartext: true  -> permitir http:// (ver android/app/src/main/AndroidManifest.xml)
 *   - allowMixedContent: true -> a WebView (https interno) pode chamar http local
 *
 * O endereço do servidor NÃO fica aqui: ele é escolhido pelo usuário na tela
 * "Servidor" do app e salvo no próprio celular (localStorage).
 */
const config: CapacitorConfig = {
  appId: 'br.speaknatural.app',
  appName: 'SpeakNatural',
  webDir: 'dist',
  android: {
    allowMixedContent: true,
    captureInput: true,
    webContentsDebuggingEnabled: false,
  },
  server: {
    androidScheme: 'https',
    cleartext: true,
  },
};

export default config;
