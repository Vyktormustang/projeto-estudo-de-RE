# Ferramentas de APK/XAPK

Existem porque o sandbox **não alcança nenhum espelho de APK** (apkpure, apkmirror,
uptodown, aptoide, f-droid, archive.org: todos bloqueados) e **não tem java**
(apktool/jadx indisponíveis; `apt` bloqueado). O que funciona:

- **entrada de arquivo:** conector do Google Drive, teto de **100 MiB** por arquivo
- **análise:** [androguard](https://pypi.org/project/androguard/) 4.x (Python puro)

## Instalar a análise

```bash
python3 -m venv /tmp/apkenv && /tmp/apkenv/bin/pip install androguard
```

## Fluxo para arquivo acima de 100 MiB

O conector recusa > 100 MiB, então divida antes de subir:

```bash
split -b 95M DeadCells.xapk DeadCells.xapk.       # gera .aa .ab ... (use -d -a 3 para .000 .001)
sha256sum DeadCells.xapk                          # guarde este hash
```

Suba as partes no Drive, e aqui:

```bash
bash tools/apk/juntar_partes.sh <dir> saida.xapk <sha256>
```

O script ordena numericamente (não alfabeticamente — `1,10,2` quebra a maioria dos
scripts), ignora o arquivo original se ele também estiver no diretório, e confere
o SHA-256 no final.

## Inspecionar

```bash
/tmp/apkenv/bin/python tools/apk/inspecionar_apk.py arquivo.apk
/tmp/apkenv/bin/python tools/apk/inspecionar_apk.py arquivo.xapk --dex
/tmp/apkenv/bin/python tools/apk/inspecionar_apk.py arquivo.apk --strings "https://"
```

Lê manifesto binário (pacote, versão, SDK, permissões, activities/services/
receivers/providers, assinatura), e com `--dex` os DEX (classes, métodos,
distribuição por pacote, busca de strings). XAPK é desmontado: identifica base e
splits, lê `manifest.json` e extrai o APK base.

**Limite:** não executa o app (sem emulador Android) e não descompila para Java
legível (sem jadx) — a análise é estrutural, sobre manifesto, recursos e bytecode.
