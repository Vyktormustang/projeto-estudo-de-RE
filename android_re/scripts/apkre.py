#!/usr/bin/env python3
"""
apkre — toolkit de Engenharia Reversa de APK (pipeline reprodutível).

Filosofia do projeto (mesma do gba-re): FATO / INFERÊNCIA / HIPÓTESE sempre
rotulados, tudo por comando reproduzível, nada de "achismo" no relatório.

Subcomandos:
  triage       hashes, header do manifest, SDK, assinatura, censo de arquivos, entropia
  components   activities/services/receivers/providers, exported, intent-filters, deep links
  permissions  permissões + risco + onde são exercidas no código
  code         censo de DEX/classes/pacotes, fingerprint de SDKs, métodos por classe
  strings      URLs/domínios/emails/segredos/IDs de API no DEX e nos resources
  native       inventário ELF, exports JNI, imports, disassembly (capstone/SLEIGH)
  features     inferência de funcionalidades por regras (rules/*.json)
  all          roda tudo e escreve reports/
  self-test    testa as funções puras com fixtures sintéticas (não precisa de APK)

Uso:
  apkre.py all --apk caminho.apk --out reports --rules rules
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.0"
ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


# --------------------------------------------------------------------------
# infra
# --------------------------------------------------------------------------
def silence_logging() -> None:
    """androguard fala MUITO (loguru). Silencia sem esconder erros nossos."""
    try:
        from loguru import logger

        logger.remove()
    except Exception:
        pass


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str | os.PathLike) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def shannon_entropy(b: bytes) -> float:
    if not b:
        return 0.0
    counts = collections.Counter(b)
    total = len(b)
    return -sum((n / total) * math.log2(n / total) for n in counts.values())


def jdump(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def md_table(rows: list[list[str]], header: list[str]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join("" if c is None else str(c).replace("|", "\\|") for c in r) + " |")
    return "\n".join(out)


def load_apk(path: str):
    silence_logging()
    from androguard.core.apk import APK

    return APK(path)


def manifest_xml(apk):
    return apk.get_android_manifest_xml()


def attr(el, name: str):
    """Lê android:<name> do elemento AXML (com fallback para atributo sem namespace)."""
    return el.get(ANDROID_NS + name, el.get(name))


def norm_bool(value) -> bool | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in ("true", "1", "0xffffffff"):
        return True
    if s in ("false", "0", "0x0"):
        return False
    return None


def component_records(xml_root) -> list[dict]:
    """Extrai componentes + intent-filters + deep links do manifest AXML."""
    recs: list[dict] = []
    app = xml_root.find("application")
    if app is None:
        return recs
    mapping = {
        "activity": "activity",
        "activity-alias": "activity-alias",
        "service": "service",
        "receiver": "receiver",
        "provider": "provider",
    }
    for tag, kind in mapping.items():
        for el in app.findall(tag):
            rec = {
                "type": kind,
                "name": attr(el, "name"),
                "exported_raw": attr(el, "exported"),
                "permission": attr(el, "permission"),
                "process": attr(el, "process"),
                "intent_filters": [],
                "deep_links": [],
                "authorities": attr(el, "authorities"),
                "grant_uri_permissions": norm_bool(attr(el, "grantUriPermissions")),
                "direct_boot_aware": norm_bool(attr(el, "directBootAware")),
            }
            for f in el.findall("intent-filter"):
                flt = {
                    "priority": attr(f, "priority"),
                    "auto_verify": norm_bool(attr(f, "autoVerify")),
                    "actions": [attr(a, "name") for a in f.findall("action")],
                    "categories": [attr(c, "name") for c in f.findall("category")],
                    "data": [
                        {k: attr(d, k) for k in ("scheme", "host", "path", "pathPrefix", "pathPattern", "mimeType", "port")}
                        for d in f.findall("data")
                    ],
                }
                rec["intent_filters"].append(flt)
                for d in flt["data"]:
                    if d.get("scheme") and (d.get("host") or d.get("path") or d.get("pathPrefix")):
                        rec["deep_links"].append(
                            {
                                "scheme": d.get("scheme"),
                                "host": d.get("host"),
                                "path": d.get("path") or d.get("pathPrefix") or d.get("pathPattern"),
                                "action": ",".join(a for a in flt["actions"] if a),
                            }
                        )
            # exported: explícito > inferência (Android <12 com intent-filter => exportado)
            explicit = norm_bool(rec["exported_raw"])
            if explicit is None:
                has_filter = bool(rec["intent_filters"])
                has_perm = bool(rec["permission"])
                inferred = has_filter and not has_perm
                rec["exported"] = inferred
                rec["exported_basis"] = "INFERIDO (sem android:exported; targetSdk>=31 exige explícito)"
            else:
                rec["exported"] = explicit
                rec["exported_basis"] = "EXPLÍCITO no manifest"
            recs.append(rec)
    return recs


def dex_objects(apk, path: str):
    silence_logging()
    from androguard.core.dex import DEX

    zf = zipfile.ZipFile(path)
    out = []
    for name in zf.namelist():
        if name.endswith(".dex"):
            data = zf.read(name)
            out.append((name, DEX(data)))
    return out


def class_name(d) -> str:
    try:
        return d.get_name()
    except Exception:
        return "?"


def method_names(d) -> list[str]:
    try:
        return [m.get_name() for m in d.get_methods()]
    except Exception:
        return []


# --------------------------------------------------------------------------
# triage
# --------------------------------------------------------------------------
def cmd_triage(apk_path: str, out: Path) -> dict:
    apk = load_apk(apk_path)
    zf = zipfile.ZipFile(apk_path)
    files = []
    for info in zf.infolist():
        data = b"" if info.is_dir() else zf.read(info.filename)
        files.append(
            {
                "name": info.filename,
                "size": info.file_size,
                "compressed": info.compress_size,
                "sha256": sha256_bytes(data) if data else "",
                "entropy": round(shannon_entropy(data), 4) if data else 0.0,
            }
        )
    ext = collections.Counter()
    for f in files:
        suffix = Path(f["name"]).suffix.lower()
        if suffix:
            ext[suffix] += 1
    certs = []
    for c in apk.get_certificates():
        certs.append(
            {
                "subject": dict(c.subject.native) if hasattr(c.subject, "native") else str(c.subject),
                "issuer": dict(c.issuer.native) if hasattr(c.issuer, "native") else str(c.issuer),
                "serial": str(c.serial_number),
                "algo": str(c.signature_algo),
                "sha256": c.sha256.hex() if hasattr(c.sha256, "hex") else str(c.sha256),
                "not_before": str(c.not_valid_before),
                "not_after": str(c.not_valid_after),
            }
        )
    dex_total = sum(f["size"] for f in files if f["name"].endswith(".dex"))
    result = {
        "tool": f"apkre {VERSION}",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "apk": {
            "path": str(apk_path),
            "size_bytes": os.path.getsize(apk_path),
            "sha256": sha256_file(apk_path),
            "md5": hashlib.md5(open(apk_path, "rb").read()).hexdigest(),
        },
        "identity": {
            "package": apk.get_package(),
            "app_name": apk.get_app_name(),
            "version_name": apk.get_androidversion_name(),
            "version_code": apk.get_androidversion_code(),
            "min_sdk": apk.get_min_sdk_version(),
            "target_sdk": apk.get_target_sdk_version(),
            "compile_sdk": attr(manifest_xml(apk), "compileSdkVersion"),
            "main_activity": apk.get_main_activity(),
            "install_location": attr(manifest_xml(apk), "installLocation"),
        },
        "signature": {
            "v1_signed": bool(zf.namelist() and any(n.startswith("META-INF/") and n.endswith((".SF", ".RSA", ".DSA", ".EC")) for n in zf.namelist())),
            "certificates": certs,
        },
        "sdk_features": apk.get_features(),
        "native_libraries_declared": apk.get_libraries(),
        "file_census": {
            "total_entries": len(files),
            "dex_count": sum(1 for f in files if f["name"].endswith(".dex")),
            "dex_total_bytes": dex_total,
            "native_so_count": sum(1 for f in files if f["name"].endswith(".so")),
            "by_extension": dict(ext.most_common(25)),
            "largest": sorted(
                [{"name": f["name"], "size": f["size"], "entropy": f["entropy"]} for f in files],
                key=lambda x: -x["size"],
            )[:15],
            "high_entropy_entries": sorted(
                [
                    {"name": f["name"], "size": f["size"], "entropy": f["entropy"]}
                    for f in files
                    if f["entropy"] > 7.5 and f["size"] > 4096
                ],
                key=lambda x: -x["size"],
            )[:20],
        },
        "files": sorted(files, key=lambda x: -x["size"]),
    }
    jdump(result, out / "triage.json")

    lines = [
        "# Triagem do APK",
        "",
        f"- arquivo: `{result['apk']['path']}`",
        f"- sha256: `{result['apk']['sha256']}`",
        f"- md5: `{result['apk']['md5']}`",
        f"- tamanho: {result['apk']['size_bytes']} bytes",
        "",
        md_table(
            [["package", result["identity"]["package"]],
             ["app_name", result["identity"]["app_name"]],
             ["versionName", result["identity"]["version_name"]],
             ["versionCode", result["identity"]["version_code"]],
             ["minSdk / targetSdk", f"{result['identity']['min_sdk']} / {result['identity']['target_sdk']}"],
             ["compileSdk", result["identity"]["compile_sdk"]],
             ["main activity", result["identity"]["main_activity"]]],
            ["campo", "valor"],
        ),
        "",
        "## Assinatura",
        "",
        md_table(
            [[c["subject"].get("common_name", c["subject"]), c["issuer"].get("common_name", c["issuer"]), c["algo"], c["sha256"][:32] + "…"] for c in certs],
            ["subject CN", "issuer CN", "algoritmo", "cert sha256"],
        ),
        "",
        "## Censo de arquivos",
        "",
        md_table(
            [[k, v] for k, v in [
                ("entradas", result["file_census"]["total_entries"]),
                ("dex", result["file_census"]["dex_count"]),
                ("dex bytes", result["file_census"]["dex_total_bytes"]),
                (".so", result["file_census"]["native_so_count"]),
            ]],
            ["métrica", "valor"],
        ),
        "",
        "Extensões: " + ", ".join(f"`{k}`×{v}" for k, v in result["file_census"]["by_extension"].items()),
    ]
    (out / "triage.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


# --------------------------------------------------------------------------
# components
# --------------------------------------------------------------------------
def cmd_components(apk_path: str, out: Path) -> dict:
    apk = load_apk(apk_path)
    recs = component_records(manifest_xml(apk))
    counts = collections.Counter(r["type"] for r in recs)
    exported = [r for r in recs if r["exported"]]
    deeplinks = [{"component": r["name"], "type": r["type"], **dl} for r in recs for dl in r["deep_links"]]
    schemes = collections.Counter(d["scheme"] for d in deeplinks)
    authorities = [{"name": r["name"], "authorities": r["authorities"]} for r in recs if r["type"] == "provider"]

    result = {
        "counts": dict(counts),
        "exported_count": len(exported),
        "exported_without_permission": [
            {"type": r["type"], "name": r["name"], "basis": r["exported_basis"]}
            for r in exported
            if not r["permission"]
        ],
        "components": recs,
        "deep_links": deeplinks,
        "schemes": dict(schemes.most_common()),
        "providers": authorities,
    }
    jdump(result, out / "components.json")

    lines = [
        "# Componentes do manifest",
        "",
        md_table([[k, v] for k, v in sorted(counts.items())], ["tipo", "quantidade"]),
        f"\nexportados: **{len(exported)}** de {len(recs)}",
        "",
        "## Deep links / schemes",
        "",
    ]
    if deeplinks:
        lines.append(md_table([[d["scheme"], d["host"], d["path"], d["component"]] for d in deeplinks], ["scheme", "host", "path", "componente"]))
    else:
        lines.append("_nenhum deep link com scheme+host_")
    lines += ["", "## Componentes exportados sem `permission`", ""]
    rows = [[r["type"], r["name"], r["exported_basis"]] for r in exported if not r["permission"]]
    lines.append(md_table(rows, ["tipo", "nome", "base da classificação"]) if rows else "_nenhum_")
    lines += ["", "## Providers", ""]
    rows = [[p["name"], p["authorities"]] for p in authorities]
    lines.append(md_table(rows, ["provider", "authorities"]) if rows else "_nenhum_")
    (out / "components.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


# --------------------------------------------------------------------------
# permissions
# --------------------------------------------------------------------------
DANGEROUS = {
    "android.permission.READ_SMS": "high", "android.permission.SEND_SMS": "high",
    "android.permission.RECEIVE_SMS": "high", "android.permission.READ_CONTACTS": "high",
    "android.permission.WRITE_CONTACTS": "high", "android.permission.GET_ACCOUNTS": "medium",
    "android.permission.READ_CALL_LOG": "high", "android.permission.CALL_PHONE": "high",
    "android.permission.CAMERA": "medium", "android.permission.RECORD_AUDIO": "high",
    "android.permission.ACCESS_FINE_LOCATION": "high", "android.permission.ACCESS_COARSE_LOCATION": "medium",
    "android.permission.ACCESS_BACKGROUND_LOCATION": "high",
    "android.permission.WRITE_EXTERNAL_STORAGE": "medium", "android.permission.READ_EXTERNAL_STORAGE": "medium",
    "android.permission.MANAGE_EXTERNAL_STORAGE": "high",
    "android.permission.REQUEST_INSTALL_PACKAGES": "high",
    "android.permission.REQUEST_DELETE_PACKAGES": "medium",
    "android.permission.QUERY_ALL_PACKAGES": "high",
    "android.permission.PACKAGE_USAGE_STATS": "high",
    "android.permission.SYSTEM_ALERT_WINDOW": "high",
    "android.permission.BIND_ACCESSIBILITY_SERVICE": "critical",
    "android.permission.BIND_DEVICE_ADMIN": "critical",
    "android.permission.BIND_NOTIFICATION_LISTENER_SERVICE": "critical",
    "android.permission.MANAGE_ACCOUNTS": "medium", "android.permission.AUTHENTICATE_ACCOUNTS": "medium",
    "android.permission.USE_CREDENTIALS": "medium",
    "android.permission.RECEIVE_BOOT_COMPLETED": "low", "android.permission.WAKE_LOCK": "low",
    "android.permission.FOREGROUND_SERVICE": "low", "android.permission.POST_NOTIFICATIONS": "low",
    "android.permission.INTERNET": "low", "android.permission.ACCESS_NETWORK_STATE": "low",
    "android.permission.ACCESS_WIFI_STATE": "low", "android.permission.GET_PACKAGE_SIZE": "low",
    "android.permission.VIBRATE": "low", "android.permission.INSTALL_PACKAGES": "critical",
    "android.permission.DELETE_PACKAGES": "high", "android.permission.UPDATE_PACKAGES_WITHOUT_USER_ACTION": "critical",
    "android.permission.READ_PHONE_STATE": "high", "android.permission.AD_ID": "medium",
    "android.permission.BLUETOOTH": "low", "android.permission.NFC": "medium",
}

API_HINTS = {
    "REQUEST_INSTALL_PACKAGES": [r"PackageInstaller", r"ACTION_INSTALL_PACKAGE", r"ACTION_VIEW"],
    "QUERY_ALL_PACKAGES": [r"getInstalledPackages", r"getInstalledApplications", r"queryIntentActivities"],
    "PACKAGE_USAGE_STATS": [r"UsageStatsManager"],
    "SYSTEM_ALERT_WINDOW": [r"TYPE_APPLICATION_OVERLAY", r"TYPE_SYSTEM_ALERT"],
    "WRITE_EXTERNAL_STORAGE": [r"getExternalStorageDirectory", r"Environment\.", r"/sdcard"],
    "READ_PHONE_STATE": [r"getDeviceId", r"getImei", r"getSubscriberId"],
    "ACCESS_FINE_LOCATION": [r"requestLocationUpdates", r"getLastKnownLocation"],
    "GET_ACCOUNTS": [r"AccountManager", r"getAccountsByType"],
}


def cmd_permissions(apk_path: str, out: Path) -> dict:
    apk = load_apk(apk_path)
    perms = sorted(apk.get_permissions())
    declared = sorted(apk.get_declared_permissions())
    # onde cada permissão é exercida: procura indícios nos DEX (string pool = rápido)
    dex_strings: set[str] = set()
    for _name, d in dex_objects(apk, apk_path):
        try:
            dex_strings.update(d.get_strings())
        except Exception:
            pass
    hints = {}
    for p in perms:
        short = p.rsplit(".", 1)[-1]
        pats = API_HINTS.get(short, [])
        found = sorted({s for pat in pats for s in dex_strings if re.search(pat, s)})[:15]
        hints[p] = found
    result = {
        "permissions": [{"name": p, "risk": DANGEROUS.get(p, "low/unknown"), "api_evidence": hints[p]} for p in perms],
        "declared_permissions": declared,
        "protection_level": {"critical": sum(1 for p in perms if DANGEROUS.get(p) == "critical")},
    }
    jdump(result, out / "permissions.json")
    rows = [[p["name"].replace("android.permission.", ""), p["risk"], ", ".join(p["api_evidence"][:3])] for p in result["permissions"]]
    (out / "permissions.md").write_text(
        "# Permissões\n\n"
        + md_table(rows, ["permissão", "risco", "evidência de uso no DEX (amostra)"])
        + f"\n\ndeclaradas pelo app: {', '.join(declared) if declared else '_nenhuma_'}\n",
        encoding="utf-8",
    )
    return result


# --------------------------------------------------------------------------
# code map
# --------------------------------------------------------------------------
SDK_SIGNATURES = {
    "AndroidX / Jetpack": [r"^Landroidx/"],
    "Kotlin stdlib": [r"^Lkotlin/"],
    "Kotlin coroutines": [r"^Lkotlinx/coroutines/"],
    "Jetpack Compose": [r"^Landroidx/compose/"],
    "Material Components": [r"^Lcom/google/android/material/"],
    "Firebase": [r"^Lcom/google/firebase/"],
    "Google Play Services": [r"^Lcom/google/android/gms/"],
    "Google Play Billing": [r"^Lcom/android/billingclient/"],
    "OkHttp / Retrofit": [r"^Lokhttp3/", r"^Lretrofit2/"],
    "Glide / Coil": [r"^Lcom/bumptech/glide/", r"^Lcoil/"],
    "Room / SQLite": [r"^Landroidx/room/", r"^Landroid/database/sqlite/"],
    "WorkManager": [r"^Landroidx/work/"],
    "ExoPlayer / Media3": [r"^Landroidx/media3/", r"^Lcom/google/android/exoplayer2/"],
    "WebView / Chrome Custom Tabs": [r"^Landroid/webkit/", r"^Landroidx/browser/"],
    "Facebook SDK": [r"^Lcom/facebook/"],
    "Adjust / AppsFlyer (attribution)": [r"^Lcom/adjust/", r"^Lcom/appsflyer/"],
    "Sentry / Crashlytics (crash)": [r"^Lio/sentry/", r"^Lcom/google/firebase/crashlytics/"],
    "Unity (motor de jogo)": [r"^Lcom/unity3d/"],
    "Flutter": [r"^Lio/flutter/"],
    "React Native": [r"^Lcom/facebook/react/"],
    "Stockfish / UCI (xadrez)": [r"(?i)stockfish", r"(?i)\buci\b", r"(?i)bestmove"],
    "Chess engine/board (xadrez)": [r"(?i)chess", r"(?i)fen\b", r"(?i)pgn\b", r"(?i)perft"],
    "Root / superuser checks": [r"(?i)supersu", r"(?i)/system/xbin/su", r"(?i)magisk"],
    "Emulador / anti-fraude": [r"(?i)isEmulator", r"(?i)goldfish", r"(?i)genymotion"],
}


def cmd_code(apk_path: str, out: Path) -> dict:
    apk = load_apk(apk_path)
    dexes = dex_objects(apk, apk_path)
    all_classes: list[str] = []
    per_dex = []
    method_total = 0
    for name, d in dexes:
        try:
            classes = [class_name(c) for c in d.get_classes()]
            methods = sum(1 for _ in d.get_methods())
        except Exception as exc:  # DEX corrompido/parcial não derruba o pipeline
            classes, methods = [], 0
            per_dex.append({"dex": name, "error": str(exc)})
        method_total += methods
        all_classes.extend(classes)
        per_dex.append({"dex": name, "classes": len(classes), "methods": methods})

    # pacotes de topo (3 níveis quando existirem)
    pkgs = collections.Counter()
    for c in all_classes:
        plain = c.lstrip("L").rstrip(";").replace("/", ".")
        parts = plain.split(".")
        pkgs[".".join(parts[:2])] += 1

    sdk_hits = {}
    joined = "\n".join(all_classes)
    for label, pats in SDK_SIGNATURES.items():
        n = sum(len(re.findall(p, joined)) for p in pats)
        if n:
            sdk_hits[label] = n

    # classes "quentes" por nome (instalador, licença, rede, conta)
    hot = collections.Counter()
    hot_patterns = {
        "instalação de APK": r"(?i)(install|installer|packageinstall|sapk)",
        "download": r"(?i)(download|fetch|requests)",
        "atualização/updater": r"(?i)(update|updater|upgrade)",
        "licença/compra": r"(?i)(billing|purchase|license|premium|subscription)",
        "conta/auth": r"(?i)(login|auth|account|token|oauth)",
        "rede/API": r"(?i)(api|http|rest|jsonrpc|endpoint)",
        "anti-análise/proteção": r"(?i)(root|emulator|integrity|tamper|obfuscat|proguard)",
    }
    for c in all_classes:
        for label, pat in hot_patterns.items():
            if re.search(pat, c):
                hot[label] += 1
    examples = {label: sorted({c for c in all_classes if re.search(pat, c)})[:8] for label, pat in hot_patterns.items()}

    result = {
        "totals": {"classes": len(all_classes), "methods": method_total, "dex_files": len(dexes)},
        "per_dex": per_dex,
        "top_packages": dict(pkgs.most_common(30)),
        "sdk_fingerprint": dict(sorted(sdk_hits.items(), key=lambda kv: -kv[1])),
        "hot_area_class_counts": dict(hot),
        "hot_area_examples": examples,
    }
    jdump(result, out / "code_map.json")
    (out / "code_map.md").write_text(
        "# Mapa de código (DEX)\n\n"
        + md_table(
            [["classes", result["totals"]["classes"]], ["métodos", result["totals"]["methods"]], ["dex", result["totals"]["dex_files"]]],
            ["métrica", "valor"],
        )
        + "\n\n## SDKs / bibliotecas identificadas (por prefixo de classe)\n\n"
        + md_table([[k, v] for k, v in result["sdk_fingerprint"].items()], ["SDK", "ocorrências"])
        + "\n\n## Pacotes de topo\n\n"
        + md_table([[k, v] for k, v in result["top_packages"].items()], ["pacote", "classes"])
        + "\n\n## Áreas quentes (contagem de classes por heurística de nome)\n\n"
        + md_table([[k, v] for k, v in hot.items()], ["área", "classes"])
        + "\n",
        encoding="utf-8",
    )
    return result


# --------------------------------------------------------------------------
# strings / intel
# --------------------------------------------------------------------------
URL_RE = re.compile(r"https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=%]{4,200}")
DOMAIN_RE = re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:com|net|org|io|app|dev|co|br|es|tv|gg|xyz|info|me|cloud|site|link|eu|uk|de|fr|ru|cn|jp)\b", re.I)
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
SECRET_PATTERNS = {
    "google_api_key": r"AIza[0-9A-Za-z\-_]{35}",
    "aws_access_key": r"AKIA[0-9A-Z]{16}",
    "private_key_block": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "jwt": r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}",
    "slack_token": r"xox[abprs]-[0-9A-Za-z\-]{10,}",
    "github_token": r"gh[pousr]_[A-Za-z0-9]{20,}",
    "stripe_key": r"(?:sk|pk)_(?:live|test)_[0-9A-Za-z]{10,}",
    "firebase_url": r"https://[a-z0-9\-]+\.firebaseio\.com",
    "s3_bucket": r"https?://[a-z0-9.\-]+\.s3[.\-][a-z0-9.\-]*amazonaws\.com",
}
NOISE_DOMAINS = {
    "schemas.android.com", "www.w3.org", "example.com", "localhost", "xml.org",
    "java.sun.com", "www.apache.org", "apache.org", "json-schema.org", "kotlinlang.org",
    "developer.android.com", "www.google.com", "google.com", "play.google.com",
}


def interesting_domain(d: str) -> bool:
    d = d.lower()
    return d not in NOISE_DOMAINS and not d.endswith(".w3.org")


def cmd_strings(apk_path: str, out: Path, top: int = 40) -> dict:
    apk = load_apk(apk_path)
    dexes = dex_objects(apk, apk_path)
    corpus = collections.Counter()
    for _n, d in dexes:
        try:
            corpus.update(d.get_strings())
        except Exception:
            pass
    res_strings: list[str] = []
    try:
        res_strings = list(apk.get_strings())
    except Exception:
        pass

    all_strings = list(corpus) + res_strings
    urls = collections.Counter(u.rstrip("/") for s in all_strings for u in URL_RE.findall(s))
    domains = collections.Counter(d.lower() for s in all_strings for d in DOMAIN_RE.findall(s) if interesting_domain(d))
    emails = sorted({e for s in all_strings for e in EMAIL_RE.findall(s)})[:25]
    ips = sorted({i for s in all_strings for i in IP_RE.findall(s) if not i.startswith(("0.", "127.", "255."))})[:25]
    secrets = {}
    for label, pat in SECRET_PATTERNS.items():
        hits = sorted({m for s in all_strings for m in re.findall(pat, s)})
        if hits:
            secrets[label] = hits[:10]

    result = {
        "string_pool_size": len(all_strings),
        "urls": dict(urls.most_common(top)),
        "domains": dict(domains.most_common(top)),
        "emails": emails,
        "public_ips": ips,
        "secret_pattern_hits": secrets,
    }
    jdump(result, out / "strings.json")
    (out / "strings.md").write_text(
        "# Strings & inteligência de rede\n\n"
        f"pool analisado: {len(all_strings)} strings\n\n"
        "## Domínios mais frequentes\n\n"
        + md_table([[d, n] for d, n in list(result["domains"].items())[:30]], ["domínio", "ocorrências"])
        + "\n\n## URLs\n\n"
        + md_table([["`" + u + "`", n] for u, n in list(result["urls"].items())[:30]], ["URL", "ocorrências"])
        + "\n\n## E-mails\n\n"
        + ("- " + "\n- ".join(emails) if emails else "_nenhum_")
        + "\n\n## Possíveis segredos/IDs (padrão de chave)\n\n"
        + (md_table([[k, ", ".join(v) if not k.startswith("private") else f"{len(v)} bloco(s)"] for k, v in secrets.items()], ["tipo", "achado"]) if secrets else "_nenhum_")
        + "\n",
        encoding="utf-8",
    )
    return result


# --------------------------------------------------------------------------
# native
# --------------------------------------------------------------------------
def elf_summary(data: bytes) -> dict:
    from elftools.elf.elffile import ELFFile
    import io

    f = io.BytesIO(data)
    elf = ELFFile(f)
    sym = elf.get_section_by_name(".dynsym")
    exports, imports = [], []
    if sym is not None:
        for s in sym.iter_symbols():
            if not s.name:
                continue
            shndx = s["st_shndx"]
            defined = isinstance(shndx, int) or (isinstance(shndx, str) and shndx != "SHN_UNDEF")
            (exports if (defined and s["st_info"]["bind"] in ("STB_GLOBAL", "STB_WEAK")) else imports).append(s.name)
    return {
        "class": elf.header.e_type,
        "machine": elf.header.e_machine,
        "bits": elf.elfclass,
        "endianness": elf.header.e_ident["EI_DATA"],
        "exports": exports,
        "imports": imports,
        "sections": [s.name for s in elf.iter_sections()],
    }


def jni_to_java(sym: str) -> str:
    """Java_com_pkg_Classe_metodo -> com.pkg.Classe#metodo (nível de confiança: heurístico)."""
    if not sym.startswith("Java_"):
        return sym
    body = sym[len("Java_"):]
    # separador de assinatura sobrecarregada: __ (double underscore)
    body = body.split("__")[0]
    # escapes JNI: _1 = '_', _2 = ';', _3 = '['; '_' sozinho = separador de pacote
    tmp = re.sub(r"_1", "\x00", body)
    tmp = re.sub(r"_2", "\x01", tmp)
    tmp = re.sub(r"_3", "\x02", tmp)
    parts = tmp.split("_")
    restored = [p.replace("\x00", "_").replace("\x01", ";").replace("\x02", "[") for p in parts]
    if len(restored) >= 2:
        return ".".join(restored[:-1]) + "#" + restored[-1]
    return ".".join(restored)


def cmd_native(apk_path: str, out: Path) -> dict:
    zf = zipfile.ZipFile(apk_path)
    so_entries = [n for n in zf.namelist() if n.endswith(".so")]
    libs = []
    for name in sorted(so_entries):
        data = zf.read(name)
        rec = {"path": name, "size": len(data), "sha256": sha256_bytes(data), "entropy": round(shannon_entropy(data), 3)}
        try:
            info = elf_summary(data)
            rec.update(
                {
                    "arch": f"{info['machine']}/{info['bits']}bit",
                    "elf_class": info["class"],
                    "exports": info["exports"][:60],
                    "export_count": len(info["exports"]),
                    "imports": info["imports"][:60],
                    "import_count": len(info["imports"]),
                    "jni_entries": [jni_to_java(e) for e in info["exports"] if e.startswith("Java_")],
                    "sections": info["sections"],
                }
            )
        except Exception as exc:
            rec["error"] = f"{type(exc).__name__}: {exc}"
        libs.append(rec)

    # disassembly amostral com capstone (Ghidra/SLEIGH complementa offline — ver ghidra/)
    disasm = {}
    try:
        import capstone
    except Exception:
        capstone = None
    if capstone:
        for name in sorted(so_entries):
            if "arm64" not in name:
                continue
            data = zf.read(name)
            try:
                from elftools.elf.elffile import ELFFile
                import io

                elf = ELFFile(io.BytesIO(data))
                text = elf.get_section_by_name(".text")
                if text is None:
                    continue
                code = text.data()
                md = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM)
                md.detail = False
                listing = []
                for ins in md.disasm(code, text["sh_addr"]):
                    listing.append(f"{ins.address:08x}  {ins.mnemonic:<8} {ins.op_str}")
                    if len(listing) >= 400:
                        break
                disasm[name] = "\n".join(listing)
            except Exception as exc:
                disasm[name] = f"erro: {exc}"
    (out / "native").mkdir(parents=True, exist_ok=True)
    for name, listing in disasm.items():
        (out / "native" / (name.replace("/", "_") + ".disasm.txt")).write_text(listing + "\n", encoding="utf-8")

    result = {"libraries": libs, "abi_dirs": sorted({n.split('/')[1] for n in so_entries})}
    jdump(result, out / "native.json")
    (out / "native.md").write_text(
        "# Bibliotecas nativas (ELF)\n\n"
        + md_table(
            [[l["path"], l["size"], l.get("arch", "?"), l.get("export_count", 0), l.get("import_count", 0), len(l.get("jni_entries", []))] for l in libs],
            ["path", "bytes", "arch", "exports", "imports", "JNI"],
        )
        + "\n\n## Entradas JNI\n\n"
        + ("\n".join(f"- `{j}` ({l['path']})" for l in libs for j in l.get("jni_entries", [])) or "_nenhuma_")
        + "\n\n## Imports (libc/outros) por lib\n\n"
        + "\n".join(f"### {l['path']}\n\n`" + "`, `".join(l.get("imports", [])[:25]) + "`\n" for l in libs)
        + "\n> Disassembly amostral (400 instruções de `.text`) em `reports/native/*.disasm.txt`. "
          "Para decompilação de verdade use `ghidra/headless_run.sh`.\n",
        encoding="utf-8",
    )
    return result


# --------------------------------------------------------------------------
# features por regras
# --------------------------------------------------------------------------
DEFAULT_RULES = {
    "generic": {
        "label": "Genéricas (qualquer app)",
        "rules": [
            {"id": "net.http", "name": "Comunicação HTTP(S)", "patterns": ["OkHttpClient", "HttpURLConnection", "Retrofit"]},
            {"id": "store.billing", "name": "Compras no app", "patterns": ["BillingClient", "com.android.billingclient", "getBuyIntent"]},
            {"id": "auth.account", "name": "Login/contas", "patterns": ["AccountManager", "oauth", "SignInActivity"]},
            {"id": "storage.db", "name": "Persistência local", "patterns": ["SQLiteOpenHelper", "androidx.room", "DataStore"]},
            {"id": "media.player", "name": "Áudio/vídeo", "patterns": ["MediaPlayer", "ExoPlayer", "MediaSession"]},
            {"id": "push.fcm", "name": "Notificações push", "patterns": ["FirebaseMessagingService", "firebase.messaging"]},
            {"id": "install.apk", "name": "Instalação de APK (sideload)", "patterns": ["PackageInstaller", "ACTION_INSTALL_PACKAGE", "application/vnd.android.package-archive"]},
            {"id": "webview", "name": "Conteúdo web embutido", "patterns": ["android.webkit.WebView", "WebViewClient", "loadUrl"]},
            {"id": "firebase", "name": "Firebase presente", "patterns": ["com.google.firebase", "FirebaseApp"]},
            {"id": "compose", "name": "Jetpack Compose", "patterns": ["androidx.compose", "ComposeView"]},
            {"id": "protect.root", "name": "Checagem de root/integridade", "patterns": ["isRooted", "superuser", "SafetyNet", "PlayIntegrity"]},
        ],
    },
    "chess": {
        "label": "Xadrez",
        "rules": [
            {"id": "chess.engine.uci", "name": "Motor UCI (bestmove/uciok)", "patterns": ["bestmove", "uciok", "go depth", "position fen"]},
            {"id": "chess.engine.native", "name": "Motor em biblioteca nativa", "patterns": ["Stockfish", "EngineLoader", "loadEngine", "nativeEval"]},
            {"id": "chess.fen", "name": "FEN (posição serializada)", "patterns": ["setFen", "fromFen", "toFen", "fenString", "currentFen"]},
            {"id": "chess.pgn", "name": "PGN (notação de partida)", "patterns": ["pgnGame", "loadPgn", "PgnReader", "[Event "]},
            {"id": "chess.clock", "name": "Relógio/incremento", "patterns": ["TimeControl", "incrementMillis", "ClockView", "flagFall"]},
            {"id": "chess.premove", "name": "Pre-move", "patterns": ["premove", "PreMove", "queuedMove"]},
            {"id": "chess.board", "name": "Renderização do tabuleiro", "patterns": ["BoardView", "ChessBoard", "PieceSet", "SquareView"]},
            {"id": "chess.moves", "name": "Geração de lances/legalidade", "patterns": ["generateLegalMoves", "MoveGenerator", "isLegalMove", "perft"]},
            {"id": "chess.puzzle", "name": "Puzzles/táticas", "patterns": ["PuzzleRush", "puzzleId", "TacticPuzzle", "solvePuzzle"]},
            {"id": "chess.lesson", "name": "Lições/curso", "patterns": ["LessonActivity", "MoveTrainer", "courseId"]},
            {"id": "chess.online", "name": "Jogo online (matchmaking/socket)", "patterns": ["matchmaking", "GameSocket", "seekGame", "gameId"]},
            {"id": "chess.rating", "name": "Rating/Elo/Glicko", "patterns": ["glicko", "ratingDeviation", "eloRating", "kFactor"]},
            {"id": "chess.analysis", "name": "Análise pós-jogo/avaliação", "patterns": ["GameReview", "evaluationBar", "AccuracyReport", "BlunderReport", "brilliantMove"]},
        ],
    },
}


def load_rules(rules_dir: str | None) -> dict:
    if not rules_dir:
        return DEFAULT_RULES
    p = Path(rules_dir)
    if not p.exists():
        return DEFAULT_RULES
    rules = {}
    for f in sorted(p.glob("*.json")):
        try:
            rules[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
    return rules or DEFAULT_RULES


def _plausible_string(s: str) -> bool:
    """Descarta strings que são claramente payload de regex/JSON gigante (ruído de matching)."""
    if not s or len(s) > 160:
        return False
    if re.search(r"[\\()[\]{}|]|\\u|\\x", s):
        return False
    return True


def match_rule(patterns: list[str], strings: set[str], classes: set[str]) -> dict:
    """Casa padrões com fronteira de token em strings 'plausíveis' + nomes de classe.

    Regra de ouro contra falso-positivo: padrões curtos (<=4 chars) exigem fronteira
    [^a-z0-9]; então 'fen' não casa em 'definition' nem 'rating' em 'batteryVelocity'.
    Evidência vinda de NOME DE CLASSE pesa mais que string solta (API real vs. texto).
    """
    str_hits, cls_hits = set(), set()
    for pat in patterns:
        pl = pat.lower()
        # Fronteira de token quando: padrão curto, ou todo minúsculo (palavra comum).
        # CamelCase/identificador (ex.: BoardView, getBuyIntent) casa como fragmento.
        needs_boundary = len(pl) <= 4 or (pat == pl and " " not in pat)
        if needs_boundary:
            rx = re.compile(r"(?<![a-z0-9])" + re.escape(pl) + r"(?![a-z0-9])", re.I)
        else:
            rx = re.compile(re.escape(pl), re.I)
        for c in classes:
            if rx.search(c) or rx.search(c.replace("/", ".")):
                cls_hits.add(c.lstrip("L").rstrip(";").replace("/", ".")[:90])
        for st in strings:
            if not _plausible_string(st):
                continue
            if rx.search(st):
                str_hits.add(st[:90])
        if len(cls_hits) >= 8 and len(str_hits) >= 8:
            break
    evidence = sorted(cls_hits)[:8] + sorted(str_hits)[:8]
    score = len(cls_hits) * 2 + len(str_hits)
    confidence = "CONFIRMADO" if score >= 4 else ("PROVÁVEL" if score >= 1 else "AUSENTE")
    return {
        "present": bool(evidence),
        "confidence": confidence,
        "evidence": evidence[:10],
        "class_hits": sorted(cls_hits)[:6],
        "string_hits": sorted(str_hits)[:6],
        "score": score,
    }


def cmd_features(apk_path: str, out: Path, rules_dir: str | None = None) -> dict:
    apk = load_apk(apk_path)
    dexes = dex_objects(apk, apk_path)
    strings: set[str] = set()
    classes: set[str] = set()
    for _n, d in dexes:
        try:
            strings.update(d.get_strings())
            classes.update(class_name(c) for c in d.get_classes())
        except Exception:
            pass
    try:
        strings.update(apk.get_strings())
    except Exception:
        pass

    rules = load_rules(rules_dir)
    results = []
    for group, spec in rules.items():
        for rule in spec.get("rules", []):
            m = match_rule(rule["patterns"], strings, classes)
            results.append({"group": group, "id": rule["id"], "name": rule["name"], **m})
    result = {
        "ruleset": sorted(rules),
        "corpus": {"strings": len(strings), "classes": len(classes)},
        "features": results,
        "present": [r["id"] for r in results if r["present"]],
    }
    jdump(result, out / "features.json")
    rows = []
    for r in results:
        ev = r["class_hits"][0] if r["class_hits"] else (r["string_hits"][0] if r["string_hits"] else "—")
        rows.append([r["group"], r["name"], r["confidence"], r["score"], ev])
    (out / "features.md").write_text(
        "# Funcionalidades inferidas (por regra)\n\n"
        "Confiança: **CONFIRMADO** = score >= 4 (classe de API vale 2, string vale 1) · **PROVÁVEL** = 1-3 · **AUSENTE** = 0.\n\n"
        f"Corpus: {len(strings)} strings, {len(classes)} classes.\n\n"
        + md_table(rows, ["grupo", "funcionalidade", "status", "score", "melhor evidência"])
        + "\n\n> Evidência detalhada (classe × string) em `features.json`. "
          "AUSENTE **não** prova que a funcionalidade não existe: pode estar em código nativo/ofuscado.\n",
        encoding="utf-8",
    )
    return result


# --------------------------------------------------------------------------
# all
# --------------------------------------------------------------------------
def cmd_all(apk_path: str, out: Path, rules_dir: str | None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    summary = {"tool": f"apkre {VERSION}", "apk": str(apk_path), "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    for label, fn in (
        ("triage", lambda: cmd_triage(apk_path, out)),
        ("components", lambda: cmd_components(apk_path, out)),
        ("permissions", lambda: cmd_permissions(apk_path, out)),
        ("code", lambda: cmd_code(apk_path, out)),
        ("strings", lambda: cmd_strings(apk_path, out)),
        ("native", lambda: cmd_native(apk_path, out)),
        ("features", lambda: cmd_features(apk_path, out, rules_dir)),
    ):
        print(f"[apkre] {label}...", flush=True)
        try:
            fn()
            summary[label] = "ok"
        except Exception as exc:
            summary[label] = f"ERRO: {type(exc).__name__}: {exc}"
            print(f"[apkre] !! {label}: {exc}", file=sys.stderr)
    jdump(summary, out / "run_summary.json")
    return summary


# --------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------
def self_test() -> int:
    fails = []
    # entropia
    if not (shannon_entropy(b"\x00" * 100) < 0.001):
        fails.append("entropy de bloco constante deveria ser 0")
    if not (shannon_entropy(bytes(range(256))) > 7.9):
        fails.append("entropy de 256 valores distintos deveria ser ~8")
    # bool
    if norm_bool("true") is not True or norm_bool("false") is not False or norm_bool("x") is not None:
        fails.append("norm_bool")
    # jni
    cases = {
        "Java_com_example_Foo_bar": "com.example.Foo#bar",
        "Java_com_example_Foo_nativeInit": "com.example.Foo#nativeInit",
        "Java_com_example_Foo_bar__I": "com.example.Foo#bar",
        "Java_com_example_my_1class_run": "com.example.my_class#run",
    }
    for k, v in cases.items():
        if jni_to_java(k) != v:
            fails.append(f"jni_to_java({k}) = {jni_to_java(k)} != {v}")
    # url/domain
    s = "https://api.uptodown.com/v2/apps?x=1 some.mail@example.org 8.8.8.8"
    if not URL_RE.findall(s):
        fails.append("URL_RE")
    if not [d for d in DOMAIN_RE.findall(s) if interesting_domain(d)]:
        fails.append("DOMAIN_RE")
    if not EMAIL_RE.findall(s):
        fails.append("EMAIL_RE")
    if not IP_RE.findall(s):
        fails.append("IP_RE")
    # manifest helpers com XML sintético (namespace android só no root, como no AXML real)
    import xml.etree.ElementTree as ET

    xml = ET.fromstring(
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="x"><application>'
        '<activity android:name=".Main" android:exported="true">'
        '<intent-filter android:autoVerify="true">'
        '<action android:name="android.intent.action.VIEW"/>'
        '<data android:scheme="https" android:host="x.com" android:path="/a"/>'
        "</intent-filter></activity>"
        '<service android:name=".Svc"/>'
        '<provider android:name=".Prov" android:authorities="x.y"/>'
        "</application></manifest>"
    )
    recs = component_records(xml)
    if len(recs) != 3:
        fails.append(f"component_records deveria achar 3, achou {len(recs)}")
    act = next(r for r in recs if r["type"] == "activity")
    if not act["exported"] or not act["deep_links"] or act["intent_filters"][0]["auto_verify"] is not True:
        fails.append("intent-filter/deep link/autoVerify")
    svc = next(r for r in recs if r["type"] == "service")
    if svc["exported"] is not False:
        fails.append("service sem intent-filter deveria ser não-exportado (inferido)")
    prov = next(r for r in recs if r["type"] == "provider")
    if prov["authorities"] != "x.y":
        fails.append("authorities")
    # regras default
    if "chess" not in DEFAULT_RULES:
        fails.append("ruleset chess ausente")
    # matcher: fronteira de token (anti falso-positivo) e classes valendo mais que strings
    classes = {"Lcom/x/BoardView;", "Lcom/x/premove/PremoveQueue;"}
    strings = {"batteryVelocity", "definition of terms", "bestmove e2e4", "rating"}
    m = match_rule(["rating"], strings, classes)
    if any("batteryVelocity" in e for e in m["evidence"]):
        fails.append("match_rule: 'rating' casou 'batteryVelocity' (fronteira de token quebrada)")
    if any("definition" in e for e in match_rule(["fen"], strings, classes)["evidence"]):
        fails.append("match_rule: 'fen' casou 'definition'")
    if match_rule(["BoardView"], strings, classes)["score"] < 2:
        fails.append("match_rule: hit em nome de classe deveria pontuar 2")
    if match_rule(["zzz_inexistente_zzz"], strings, classes)["confidence"] != "AUSENTE":
        fails.append("match_rule: sem evidência deveria ser AUSENTE")
    if fails:
        print("SELF-TEST FALHOU:")
        for f in fails:
            print("  -", f)
        return 1
    print("SELF-TEST OK (entropia, norm_bool, jni_to_java, regex de rede, manifest/components)")
    return 0


# --------------------------------------------------------------------------
def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="apkre", description="Toolkit de RE de APK (pipeline do projeto).")
    p.add_argument("--version", action="version", version=f"apkre {VERSION}")
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("triage", "components", "permissions", "code", "strings", "native", "features", "all"):
        s = sub.add_parser(name)
        s.add_argument("--apk", required=True, help="caminho do APK")
        s.add_argument("--out", default="reports", help="diretório de saída")
        if name == "features":
            s.add_argument("--rules", default=None, help="diretório com rules/*.json")
        if name == "all":
            s.add_argument("--rules", default=None, help="diretório com rules/*.json")
    sub.add_parser("self-test")

    args = p.parse_args(argv)
    if args.cmd == "self-test":
        return self_test()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fn = {
        "triage": lambda: cmd_triage(args.apk, out),
        "components": lambda: cmd_components(args.apk, out),
        "permissions": lambda: cmd_permissions(args.apk, out),
        "code": lambda: cmd_code(args.apk, out),
        "strings": lambda: cmd_strings(args.apk, out),
        "native": lambda: cmd_native(args.apk, out),
        "features": lambda: cmd_features(args.apk, out, getattr(args, "rules", None)),
        "all": lambda: cmd_all(args.apk, out, getattr(args, "rules", None)),
    }[args.cmd]
    res = fn()
    print(json.dumps({k: v for k, v in (res or {}).items() if k in ("counts", "totals", "features", "run_summary")} or {"ok": True}, indent=2, default=str)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
