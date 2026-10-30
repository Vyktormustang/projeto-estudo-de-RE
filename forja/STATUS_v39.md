# FORJA v39.0.0 — estado do projeto (30/10/2026)

## Resumo em uma linha

A **fábrica do APK** está pronta e provada: cada push gera `Forja_Apice_v39.0.0.apk`
assinado (v1+v2+v3), zero permissões, com Release automática. Falta apenas o
**código-fonte do app v38** entrar no repositório para o fix entrar junto.

## Evidência do último build (GitHub Actions, run 41079791656)

| Item | Valor |
|---|---|
| Resultado | ✅ 22/22 passos verdes |
| APK | `Forja_Apice_v39.0.0.apk` — 46 089 bytes |
| SHA-256 | `fc040f48267c8133d8de112babcc5ae0bac34fd5ece8fc0b8606cd55b0de6cf3` |
| MD5 | `54e6a05b843b0d7ae5059dea815224f5` |
| Certificado (SHA-256) | `15:E9:23:0C:8A:25:99:DB:FB:A2:2B:11:A3:87:18:95:12:55:93:1F:E4:E6:29:EB:04:C8:AA:A1:D8:73:8B:7C` |
| Assinatura | `apksigner verify` OK — v1 + v2 + v3 |
| Alinhamento | `zipalign -c -p 4` OK |
| Permissões | `uses-permission = 0` (offline de verdade) |
| Conteúdo | `AndroidManifest.xml`, `classes.dex`, `resources.arsc`, `assets/www/index.html` |
| Release | `forja-v39.0.0-canario` (pre-release, download direto) |

Download:
`https://github.com/Vyktormustang/projeto-estudo-de-RE/releases/download/forja-v39.0.0-canario/Forja_Apice_v39.0.0.apk`

> O SHA-256 muda a cada build com o mesmo conteúdo: o `zip` grava o horário dos
> arquivos, então os bytes não são reprodutíveis bit a bit (o conteúdo lógico é).
> Se precisar de reprodutibilidade bit-exata, é um ajuste pequeno no
> `build_apk.sh` (timestamps fixos + `SOURCE_DATE_EPOCH`).

> O APK é **pequeno (45 KB)** de propósito: é o build de canário — shell WebView
> + núcleo do xadrez. O v38 tinha 536 KB porque carregava as 240 lições, o
> xadrez completo e o Cofre. Nada disso se perdeu; ele nunca esteve aqui.

## O que foi construído

1. **`forja/web`** — app TypeScript + Vite.
   - `src/forja.ts`: núcleo determinístico — Elo (K 40/20/10, piso 100),
     categorias do plano v23, precisão de partida, SM-2, repetição espaçada
     (ISI ≈ 15%), Cofre com saneamento de JSON do disco.
   - `src/forja.test.ts`: **20 testes**, todos verdes (`vitest`).
   - `src/main.ts`: UI de canário que exercita o núcleo dentro do WebView.
2. **`forja/android`** — shell WebView offline: zero `<uses-permission>`,
   navegação limitada a `file:///android_asset/`, DOM storage ligado (Cofre),
   back do sistema navega no histórico, ícones gerados por script (sem assets
   de terceiros).
3. **`forja/tools/build_apk.sh`** — pipeline sem Gradle:
   `aapt2 compile/link → javac → d8 → zip → zipalign -p 4 → apksigner`.
   Autoverifica e imprime SHA-256/MD5/tamanho.
4. **`.github/workflows/forja-apk.yml`** — CI completo com artifact + Release,
   smoke test de conteúdo e dump de permissões.

## O bloqueio (honesto)

O Drive da conta tem **42 arquivos FORJA: só APKs e dossiês**. Não existe, em
lugar nenhum acessível, o código-fonte do v38 (React/TS), nem changelog do
v16→v38. O dossiê mais recente é o da **v15.0** e o plano mais recente é o
**v23.0** (xadrez Chess.com).

Sem o fonte, "consertar o que o v38 tentou fixar" viraria um **quarto build
empilhado às cegas** — exatamente o padrão que produziu `v38.0` →
`v38.0_FIXADO` → `v38.0_FIXADO_v2` em três horas.

### Para eu fechar o fix no v39

1. **Fonte**: subir o projeto no GitHub (ou dizer o repo) — eu clono, porto para
   `forja/web/src/` e o CI passa a publicar o app completo, assinado.
2. **Sintoma**: qual problema motivou o `FIXADO`? E o que segue quebrado no
   `FIXADO_v2`? (protocolo em `forja/FIX_v39.md`)
3. **Segredos** (opcional, 2 min): adicionar `FORJA_KEYSTORE_B64`,
   `FORJA_KS_PASS`, `FORJA_KEY_PASS`, `FORJA_KS_ALIAS` no GitHub — aí eu removo
   o keystore versionado (hoje público, o que é uma fraqueza conhecida e
   documentada em `forja/signing/README.md`).

## Instalação no aparelho

1. Abra o link da Release no celular e baixe o `.apk`.
2. Autorize "instalar de fontes desconhecidas" quando o Android pedir.
3. Instalação **limpa** (certificado novo): desinstale o v38 antes.
   O Cofre do v38 (localStorage) não é migrado automaticamente — exporte o JSON
   antes de desinstalar, se quiser preservar progresso.
