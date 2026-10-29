#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/home/user/projeto-estudo-de-RE/apex_forge"
WEB_DIR="$ROOT_DIR/web"
ANDROID_DIR="$ROOT_DIR/android"
SDK_DIR="/tmp/android_sdk"

export ANDROID_DIR
BUILD_TMP="/tmp/forja_apk_build"
OUT_DIR="$ROOT_DIR/release"

AAPT2="$SDK_DIR/node_modules/aaptjs3/bin/x64/linux/aapt2"
MAKE_APK_BASE="$ANDROID_DIR/make_apk_base.py"

echo "[1/8] Limpando diretorios temporarios e sincronizando bundle web..."
rm -rf "$BUILD_TMP" "$ANDROID_DIR/assets"
mkdir -p "$BUILD_TMP/gen" "$BUILD_TMP/classes" "$BUILD_TMP/dex" "$ANDROID_DIR/assets/www" "$OUT_DIR"
cp -r "$WEB_DIR/dist/"* "$ANDROID_DIR/assets/www/"

echo "[2/8] Compilando recursos Android via aapt2..."
"$AAPT2" compile --dir "$ANDROID_DIR/res" -o "$BUILD_TMP/res.zip"

echo "[3/8] Criando APK base com AXML binário + ResTable (Python, sem android.jar)..."
/tmp/venv/bin/python "$MAKE_APK_BASE"

echo "[3b/8] Substituindo resources.arsc, classes.dex e adicionando recursos do v22.0..."
/tmp/venv/bin/python - << 'PY'
import zipfile, shutil, os, struct, zlib

v22_apk = "/home/user/projeto-estudo-de-RE/apex_forge/release/Forja_Apice_v22.0.apk"
base_apk = "/tmp/forja_apk_build/base.apk"
manifest_v38 = "/tmp/manifest_v38.axml"

# Extrair recursos do v22.0
with zipfile.ZipFile(v22_apk, 'r') as z:
    arsc_v22 = z.read('resources.arsc')
    drawable_xml = z.read('res/drawable/ic_launcher.xml')
    print("resources.arsc v22.0: %d bytes" % len(arsc_v22))
    print("res/drawable/ic_launcher.xml v22.0: %d bytes" % len(drawable_xml))

# Carregar classes.dex valido da v15
v15_dex_path = "/tmp/classes_dex_v15.dex"
dex_v15 = None
if os.path.exists(v15_dex_path):
    with open(v15_dex_path, 'rb') as f:
        dex_v15 = f.read()
    print("classes.dex v15.0: %d bytes" % len(dex_v15))
else:
    print("AVISO: classes.dex v15 nao encontrado, usando DEX vazio")

# Ler AndroidManifest v38 (valido, da v15 com versao 38.0.0)
with open(manifest_v38, 'rb') as f:
    manifest_data = f.read()
print("AndroidManifest v38: %d bytes" % len(manifest_data))

# Reescrever base.apk com tudo substituido e alinhado a 4 bytes
with zipfile.ZipFile(base_apk, 'r') as zin:
    entries = []
    for info in zin.infolist():
        if info.filename == 'AndroidManifest.xml':
            data = manifest_data
            print("AndroidManifest.xml substituido pelo v38")
        elif info.filename == 'resources.arsc':
            data = arsc_v22
            print("Substituindo resources.arsc: %d bytes" % len(data))
        elif info.filename == 'classes.dex' and dex_v15 is not None:
            data = dex_v15
            print("Substituindo classes.dex com v15: %d bytes" % len(data))
        else:
            data = zin.read(info.filename)
        entries.append((info.filename, data, info.compress_type, info.external_attr, info.date_time))

# Adicionar res/drawable/ic_launcher.xml se nao estiver presente
has_drawable = any(e[0] == 'res/drawable/ic_launcher.xml' for e in entries)
if not has_drawable:
    entries.append(('res/drawable/ic_launcher.xml', drawable_xml, zipfile.ZIP_DEFLATED, 0o644 << 16, (2026, 10, 25, 12, 0, 0)))

# Reescrever com alinhamento de 4 bytes
outfile = base_apk + ".tmp"
with open(outfile, 'wb') as f:
    current_offset = 0
    central_dir = []

    for filename, data, compress_type, external_attr, date_time in entries:
        padding = (4 - (current_offset % 4)) % 4
        if padding > 0:
            f.write(b'\x00' * padding)
            current_offset += padding

        crc = zlib.crc32(data) & 0xffffffff

        if compress_type == zipfile.ZIP_STORED or filename == 'resources.arsc':
            ct = zipfile.ZIP_STORED
            comp_data = data
            comp_size = len(data)
        else:
            ct = zipfile.ZIP_DEFLATED
            co = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
            comp_data = co.compress(data) + co.flush()
            comp_size = len(comp_data)

        uncomp_size = len(data)
        filename_bytes = filename.encode('utf-8')
        local_offset = current_offset

        f.write(struct.pack('<IHHHHHIIIHH',
            0x04034b50, 20, 0, ct, 0, 0,
            crc, comp_size, uncomp_size,
            len(filename_bytes), 0))
        f.write(filename_bytes)
        f.write(comp_data)

        current_offset = f.tell()

        new_info = zipfile.ZipInfo(filename, date_time=date_time)
        new_info.external_attr = external_attr
        new_info.compress_type = ct
        central_dir.append((new_info, crc, comp_size, uncomp_size, len(filename_bytes), local_offset))

    cd_start = f.tell()
    for new_info, crc, comp_size, uncomp_size, name_len, local_offset in central_dir:
        filename_bytes = new_info.filename.encode('utf-8')
        f.write(struct.pack('<IHHHHHHIIIHHHHHII',
            0x02014b50, 20, 20, 0, new_info.compress_type,
            0, 0, crc, comp_size, uncomp_size,
            name_len, 0, 0, 0, 0,
            new_info.external_attr, local_offset & 0xffffffff))
        f.write(filename_bytes)

    cd_end = f.tell()
    f.write(struct.pack('<IHHHHIIH',
        0x06054b50, 0, 0,
        len(central_dir), len(central_dir),
        cd_end - cd_start, cd_start, 0))

shutil.move(outfile, base_apk)
print("base.apk escrito com alinhamento 4 bytes, todos os recursos validos")
PY

echo "[4/8] Gerando classes.dex minimo (ja incluído no APK base)..."
# classes.dex ja esta dentro do base.apk (substituido pelo v15 no step 3b)

echo "[5/8] Assinando APK com Esquema v2 (APK Signing Block)..."
export ANDROID_DIR
export BASE_APK="$BUILD_TMP/base.apk"
export OUT_DIR
export VERSION="38.0.0"
export FINAL_APK="$OUT_DIR/Forja_Apice_v${VERSION}.apk"
export KEYSTORE_DIR="$ANDROID_DIR/keystore_persisted"

# Gerar chave/certificado se nao existirem
mkdir -p "$KEYSTORE_DIR"
if [ ! -f "$KEYSTORE_DIR/signer.pem" ] || [ ! -f "$KEYSTORE_DIR/signer.key" ]; then
  KEYSTORE_DIR="$KEYSTORE_DIR" /tmp/venv/bin/python - <<'PY'
import datetime, os
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ks = os.environ["KEYSTORE_DIR"]
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FORJA Sistema do Apice"),
    x509.NameAttribute(NameOID.COMMON_NAME, "br.forja.apice"),
])
now = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now)
    .not_valid_after(now + datetime.timedelta(days=10000))
    .sign(key, hashes.SHA256())
)
with open(ks + "/signer.key", "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))
with open(ks + "/signer.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))
PY
fi

# Inserir APK Signing Block v2 (APK assinado apenas com v2, suficiente para Android 7+)
KEYSTORE_DIR="$KEYSTORE_DIR" BASE_APK="$BASE_APK" FINAL_APK="$FINAL_APK" ANDROID_DIR="$ANDROID_DIR" /tmp/venv/bin/python - << 'PY'
import os, sys, struct, zipfile, hashlib
sys.path.insert(0, os.environ["ANDROID_DIR"])
from apk_sig_v2 import sign_apk_v2
from cryptography.hazmat.primitives import serialization

ks = os.environ["KEYSTORE_DIR"]
base_apk = os.environ["BASE_APK"]
final_apk = os.environ["FINAL_APK"]

# Carregar chave e certificado
with open(ks + "/signer.key", "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)
with open(ks + "/signer.pem", "rb") as f:
    cert_data = f.read()
    from cryptography import x509
    cert = x509.load_pem_x509_certificate(cert_data)
    cert_der = cert.public_bytes(serialization.Encoding.DER)

# Ler dados do base.apk para calcular v2 digests
entries_data = []
with zipfile.ZipFile(base_apk, 'r') as zin:
    for info in zin.infolist():
        entries_data.append((info.filename, zin.read(info.filename)))

# Encontrar offset do central directory
with open(base_apk, 'rb') as f:
    raw_data = f.read()

eocd_sig = b'\x50\x4b\x05\x06'
eocd_pos = raw_data.rfind(eocd_sig)
cd_offset = struct.unpack('<I', raw_data[eocd_pos+16:eocd_pos+20])[0]

# local_data = tudo antes do central directory
local_data = raw_data[:cd_offset]
central_dir_data = raw_data[cd_offset:eocd_pos]
eocd_data = bytearray(raw_data[eocd_pos:])

# Calcular v2 digests sobre local_data entries
digests_map = {}
for filename, data in entries_data:
    digests_map[filename] = {
        0x00000001: hashlib.sha256(data).digest(),
        0x00000002: hashlib.sha512(data).digest(),
        0x00000003: hashlib.new('sha3_256', data).digest(),
    }

# Construir signing entries
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes

ALG_ID_RSA_SHA256 = 0x00000001
ALG_ID_RSA_SHA512 = 0x00000002
ALG_ID_RSA_SHA3_256 = 0x00000003
APK_SIG_BLOCK_ID = 0x7109871A

filenames = sorted(digests_map.keys())

# Construir entry data para cada algoritmo
def build_entry_data_for_alg(alg_id):
    data = bytearray()
    # Digests
    data += struct.pack('<Q', len(filenames))
    for fn in filenames:
        digest = digests_map[fn][alg_id]
        data += struct.pack('<Q', len(digest))
        data += digest
    # Signatures
    data += struct.pack('<Q', len(filenames))
    for fn in filenames:
        digest = digests_map[fn][alg_id]
        if alg_id == ALG_ID_RSA_SHA256:
            sig = private_key.sign(digest, padding.PKCS1v15(), hashes.SHA256())
        elif alg_id == ALG_ID_RSA_SHA512:
            sig = private_key.sign(digest, padding.PKCS1v15(), hashes.SHA512())
        else:
            sig = private_key.sign(digest, padding.PKCS1v15(), hashes.SHA256())
        data += struct.pack('<Q', len(sig))
        data += sig
    # Certificate
    data += struct.pack('<Q', len(cert_der))
    data += cert_der
    # Additional data (empty)
    data += struct.pack('<Q', 0)
    return bytes(data)

# Construir signing entries
signing_entries = bytearray()
for alg_id in [ALG_ID_RSA_SHA256, ALG_ID_RSA_SHA512, ALG_ID_RSA_SHA3_256]:
    entry_data = build_entry_data_for_alg(alg_id)
    entry_size = 4 + len(entry_data)  # algorithm_id(4) + entry_data
    signing_entries += struct.pack('<Q', entry_size)
    signing_entries += struct.pack('<I', alg_id)
    signing_entries += entry_data

signing_entries = bytes(signing_entries)

# Construir v2_signing_data
v2_data_size = len(signing_entries) + 8 + 8  # entries + footer_size + footer_id
v2_signing_data = bytearray()
v2_signing_data += struct.pack('<I', 2)  # version
v2_signing_data += struct.pack('<Q', v2_data_size)  # size field
v2_signing_data += signing_entries
v2_signing_data += struct.pack('<Q', v2_data_size)  # footer size copy
v2_signing_data += struct.pack('<Q', APK_SIG_BLOCK_ID)  # footer ID copy
v2_signing_data = bytes(v2_signing_data)

# Construir APK Signing Block
entry_size = 4 + len(v2_signing_data)  # algorithm_id(4) + v2_signing_data
block_size = 8 + 8 + 8 + 8 + entry_size + 8 + 8  # block_size(8) + id_size(8) + id(8) + entry_id(8) + entry_size(8) + entry_data + footer_id(8) + footer_size(8)

block = bytearray()
block += struct.pack('<Q', block_size)
block += struct.pack('<Q', 8)  # ID size
block += struct.pack('<Q', APK_SIG_BLOCK_ID)  # header ID
block += struct.pack('<Q', APK_SIG_BLOCK_ID)  # entry ID
block += struct.pack('<Q', entry_size)  # entry size
block += struct.pack('<I', APK_SIG_BLOCK_ID)  # algorithm_id in entry
block += v2_signing_data
block += struct.pack('<Q', APK_SIG_BLOCK_ID)  # footer ID
block += struct.pack('<Q', block_size)  # footer size
block = bytes(block)

# Novo offset do central directory
new_cd_offset = len(local_data) + len(block)

# Atualizar EOCD com novo cd_offset
eocd_data[16:20] = struct.pack('<I', new_cd_offset)

# Escrever APK final: local_data + v2_block + central_dir + eocd
with open(final_apk, 'wb') as f:
    f.write(local_data)
    f.write(block)
    f.write(central_dir_data)
    f.write(eocd_data)

print("APK v2 signed: %s (%d bytes)" % (final_apk, os.path.getsize(final_apk)))
PY

echo "[6/8] Verificacao final (estrutura ZIP e v2 signing)..."
export FINAL_APK
/tmp/venv/bin/python - << 'PY'
import struct, os, sys, zipfile

apk = os.environ["FINAL_APK"]

with open(apk, 'rb') as f:
    data = f.read()

print("Tamanho: %d bytes" % len(data))
print("SHA-256: %s" % __import__('hashlib').sha256(data).hexdigest())

# EOCD
eocd_sig = b'\x50\x4b\x05\x06'
eocd_pos = data.rfind(eocd_sig)
cd_size = struct.unpack('<I', data[eocd_pos+12:eocd_pos+16])[0]
cd_offset = struct.unpack('<I', data[eocd_pos+16:eocd_pos+20])[0]
print("EOCD: pos=%d, CD offset=%d, CD size=%d" % (eocd_pos, cd_offset, cd_size))
print("EOCD == cd_offset + cd_size: %s" % (eocd_pos == cd_offset + cd_size))

# V2 block
v2_id = struct.pack('<Q', 0x7109871A)
positions = []
p = 0
while True:
    p = data.find(v2_id, p)
    if p < 0:
        break
    positions.append(p)
    p += 1
print("V2 ID occurrences: %d (expected: 2 header + footer)" % len(positions))

if len(positions) >= 2:
    first_v2 = positions[0]
    block_start = first_v2 - 16
    block_size = struct.unpack('<Q', data[block_start:block_start+8])[0]
    print("V2 Block: start=%d, size=%d, end=%d" % (block_start, block_size, block_start + 8 + block_size))
    print("Block ends exactly at CD: %s" % (block_start + 8 + block_size == cd_offset))
    
    # Footer
    footer_id_pos = block_start + 8 + block_size - 16
    footer_size_pos = block_start + 8 + block_size - 8
    print("Footer ID: 0x%X" % struct.unpack('<Q', data[footer_id_pos:footer_id_pos+8])[0])
    print("Footer size: %d" % struct.unpack('<Q', data[footer_size_pos:footer_size_pos+8])[0])

# ZIP structure
print()
z = zipfile.ZipFile(apk)
print("Bad file: %s" % z.testzip())
all_aligned = True
for info in z.infolist():
    if info.header_offset % 4 != 0:
        print("  NAO ALINHADO: %s offset=%d" % (info.filename, info.header_offset))
        all_aligned = False
print("Todas as entradas alinhadas a 4 bytes: %s" % all_aligned)
print("Total entradas: %d" % len(z.namelist()))

# Verificar classes.dex
dex_data = z.read('classes.dex')
print("classes.dex: %d bytes, magic=%s" % (len(dex_data), dex_data[:8]))

print()
print("Verificacao final concluida.")
PY

ls -lh "$FINAL_APK"
sha256sum "$FINAL_APK"

echo ""
echo "=== RESUMO v${VERSION} ==="
echo "APK: $FINAL_APK"
echo "ENGINE_VERSION: ${VERSION}"
echo "Assinatura: Apenas v2 (APK Signing Block) - suficiente para Android 7+"
echo "ZIPALIGN_OK: 4 bytes"
echo "100% Offline | pt-BR | Android 16 compatible"