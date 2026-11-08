#!/usr/bin/env python3
"""Inspeção de APK/XAPK sem Java.

Por que existe: o sandbox não tem java/apktool/jadx (e o apt está bloqueado),
mas o androguard (Python puro) lê manifesto binário, recursos e DEX.

XAPK não é um APK: é um ZIP que contém vários APKs (base + splits de ABI/densidade)
e um manifest.json. Este script entende os dois formatos.

Uso:
  python3 inspecionar_apk.py arquivo.apk [--dex] [--strings TERMO]
"""
import argparse, json, logging, sys, zipfile, collections, pathlib

logging.disable(logging.CRITICAL)


def eh_xapk(z: zipfile.ZipFile) -> bool:
    nomes = z.namelist()
    return any(n.endswith(".apk") for n in nomes) and "AndroidManifest.xml" not in nomes


def descrever_apk(caminho: str) -> dict:
    from androguard.core.apk import APK
    a = APK(caminho)
    return {
        "pacote": a.get_package(),
        "versao": a.get_androidversion_name(),
        "versionCode": a.get_androidversion_code(),
        "minSdk": a.get_min_sdk_version(),
        "targetSdk": a.get_target_sdk_version(),
        "permissões": sorted(a.get_permissions()),
        "activities": a.get_activities(),
        "services": a.get_services(),
        "receivers": a.get_receivers(),
        "providers": a.get_providers(),
        "main_activity": a.get_main_activity(),
        "assinado": a.is_signed(),
        # androguard 4.x: não existe is_debuggable()/get_libs(); o atributo é
        # get_libraries() e o debuggable vem do próprio manifesto.
        "debuggable": a.get_attribute_value("application", "debuggable"),
        "bibliotecas nativas": sorted(a.get_libraries() or []),
    }


def dump_dex(caminho_apk: str, termo: str | None) -> None:
    from androguard.core.dex import DEX
    z = zipfile.ZipFile(caminho_apk)
    dexes = sorted(n for n in z.namelist() if n.endswith(".dex"))
    print(f"\n  DEX: {len(dexes)} arquivo(s)")
    total_c = total_m = 0
    classes_por_pkg = collections.Counter()
    achados = []
    for n in dexes:
        d = DEX(z.read(n))
        cs = d.get_classes()
        total_c += len(cs)
        for c in cs:
            total_m += len(c.get_methods())
            classe = c.get_name().lstrip("L")
            classes_por_pkg[classe.rsplit("/", 1)[0] if "/" in classe else "(raiz)"] += 1
        if termo:
            t = termo.lower().encode()
            for s in d.get_strings():
                if t in s.lower():
                    achados.append((n, s.decode("utf-8", "replace")))
    print(f"  classes: {total_c} | métodos: {total_m}")
    print("  top pacotes de código:")
    for k, v in classes_por_pkg.most_common(8):
        print(f"    {k}: {v}")
    if termo:
        print(f'\n  strings contendo "{termo}": {len(achados)}')
        for origem, s in achados[:40]:
            print(f"    [{origem}] {s[:160]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivo")
    ap.add_argument("--dex", action="store_true", help="só o resumo do DEX (mais lento)")
    ap.add_argument("--strings", metavar="TERMO", help="procura o termo nas strings do DEX")
    a = ap.parse_args()

    caminho = pathlib.Path(a.arquivo)
    if not caminho.is_file():
        print(f"[ERRO] não existe: {caminho}")
        return 2
    print(f"[arquivo] {caminho.name} — {caminho.stat().st_size:,} B")

    with zipfile.ZipFile(caminho) as z:
        if z.testzip() is not None:
            print("[ERRO] ZIP corrompido")
            return 2
        xapk = eh_xapk(z)
        if xapk:
            print("[formato] XAPK (APK base + splits)")
            base = [n for n in z.namelist() if n.endswith(".apk") and "config." not in n]
            splits = [n for n in z.namelist() if n.endswith(".apk") and "config." in n]
            print(f"  base: {base}")
            print(f"  splits ({len(splits)}):", splits[:12])
            if "manifest.json" in z.namelist():
                try:
                    m = json.loads(z.read("manifest.json"))
                    for k in ("package_name", "version_name", "version_code", "min_sdk_version"):
                        if k in m:
                            print(f"  {k}: {m[k]}")
                except Exception as e:
                    print(f"  [aviso] manifest.json ilegível: {e}")
            destino = pathlib.Path("/tmp") / f"_{caminho.stem}_base.apk"
            destino.write_bytes(z.read(base[0]))
            print(f"  base extraído para {destino}")
            cam = str(destino)
        else:
            print("[formato] APK")
            cam = str(caminho)

    info = descrever_apk(cam)
    print("\n[manifesto]")
    for k, v in info.items():
        if isinstance(v, list):
            print(f"  {k}: {len(v)}")
            for x in v[:10]:
                print(f"    - {x}")
            if len(v) > 10:
                print(f"    ... +{len(v)-10}")
        else:
            print(f"  {k}: {v}")

    if a.dex or a.strings:
        dump_dex(cam, a.strings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
