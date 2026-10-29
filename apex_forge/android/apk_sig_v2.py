#!/usr/bin/env python3
"""
APK Signature Scheme v2 (APK Signing Block v2) implementation.
Adds v2 signing to an already v1-signed APK so it installs on
Android 7+ (API 24+) where targetSdkVersion >= 24.

Based on: https://source.android.com/docs/security/apks-signing/v2
APK Signing Block format (from Android source: apksig/ApkSigBlock.java):

APK Signing Block := Size (uint64)
                     ID (uint64) = 0x7109871A
                     (ID, Value)*
                     ID (uint64) = 0x7109871A
                     Size (uint64)

Each (ID, Value) pair:
  ID (uint64)
  Size (uint64)   -- size of Value only
  Value (bytes)

Scheme v2 entry (ID = 0x7109871A, Value contains):
  uint32: version (2)
  uint64: v2_data_size  -- size of everything after this field until end ID
    SigningEntry[] entries
  uint64: v2_data_size  -- footer copy
  uint64: ID = 0x7109871A  -- footer copy

SigningEntry:
  uint64: entry_size  -- size of algorithm_id + entry_data
  uint32: algorithm_id
  byte[] entry_data

Entry data for each algorithm:
  uint64: num_digests
  for each: uint64 digest_size, byte[] digest
  uint64: num_signatures
  for each: uint64 signature_size, byte[] signature
  uint64: cert_size
  byte[] cert (DER encoded X.509)
  uint64: additional_data_size
  byte[] additional_data
"""

import struct
import zipfile
import hashlib
import os
import sys

# APK Signature Scheme block ID
APK_SIG_BLOCK_ID = 0x7109871A

# Algorithm IDs (from Android source: apksig/SchemeV2Constants.java)
ALG_ID_RSA_SHA256 = 0x00000001
ALG_ID_RSA_SHA512 = 0x00000002
ALG_ID_RSA_SHA3_256 = 0x00000003


def _u32le(v):
    return struct.pack('<I', v & 0xFFFFFFFF)


def _u64le(v):
    return struct.pack('<Q', v & 0xFFFFFFFFFFFFFFFF)


def _compute_v2_digests(entries_data):
    """
    Compute v2 digests for each ZIP entry.
    V2 digests are computed over the compressed data of each entry as stored
    in the APK (the exact bytes between the local header and the next entry).
    The APK Signing Block itself is excluded from digest calculation.
    """
    digests = {}
    for filename, data in entries_data:
        digests[filename] = {
            ALG_ID_RSA_SHA256: hashlib.sha256(data).digest(),
            ALG_ID_RSA_SHA512: hashlib.sha512(data).digest(),
            ALG_ID_RSA_SHA3_256: hashlib.new('sha3_256', data).digest(),
        }
    return digests


def _build_entry_data_for_alg(digests_map, filenames, private_key, cert_der, alg_id):
    """
    Build entry data for a single algorithm:
      uint64: num_digests
      for each: uint64 digest_size, byte[] digest
      uint64: num_signatures
      for each: uint64 signature_size, byte[] signature
      uint64: cert_size
      byte[] cert
      uint64: additional_data_size (0)
      byte[] additional_data (empty)
    """
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives import hashes

    data = bytearray()

    # Digests section
    data += _u64le(len(filenames))
    for fn in filenames:
        digest = digests_map[fn][alg_id]
        data += _u64le(len(digest))
        data += digest

    # Signatures section
    data += _u64le(len(filenames))
    for fn in filenames:
        digest = digests_map[fn][alg_id]
        if alg_id == ALG_ID_RSA_SHA256:
            sig = private_key.sign(digest, padding.PKCS1v15(), hashes.SHA256())
        elif alg_id == ALG_ID_RSA_SHA512:
            sig = private_key.sign(digest, padding.PKCS1v15(), hashes.SHA512())
        elif alg_id == ALG_ID_RSA_SHA3_256:
            sig = private_key.sign(digest, padding.PKCS1v15(), hashes.SHA256())
        else:
            sig = private_key.sign(digest, padding.PKCS1v15(), hashes.SHA256())
        data += _u64le(len(sig))
        data += sig

    # Certificate section
    data += _u64le(len(cert_der))
    data += cert_der

    # Additional data (empty)
    data += _u64le(0)

    return bytes(data)


def _build_signing_entries(digests_map, private_key, cert_der):
    """
    Build all signing entries (one per algorithm).
    Each entry: uint64 entry_size | uint32 algorithm_id | byte[] entry_data
    """
    filenames = sorted(digests_map.keys())
    entries = bytearray()

    for alg_id in [ALG_ID_RSA_SHA256, ALG_ID_RSA_SHA512, ALG_ID_RSA_SHA3_256]:
        entry_data = _build_entry_data_for_alg(
            digests_map, filenames, private_key, cert_der, alg_id
        )
        entry_size = 4 + len(entry_data)  # algorithm_id (4) + entry_data
        entries += _u64le(entry_size)
        entries += _u32le(alg_id)
        entries += entry_data

    return bytes(entries)


def _build_v2_signing_data(signing_entries):
    """
    Build Scheme v2 signing data (the Value inside the APK Signing Block entry):
      uint32: version (2)
      uint64: v2_data_size  -- size of everything after this field
        signing_entries
      uint64: v2_data_size  -- footer copy
      uint64: ID = 0x7109871A  -- footer copy
    """
    v2_data_size = len(signing_entries) + 8 + 8  # entries + footer size + footer ID

    data = bytearray()
    data += _u32le(2)  # version
    data += _u64le(v2_data_size)  # size field
    data += signing_entries
    data += _u64le(v2_data_size)  # footer size copy
    data += _u64le(APK_SIG_BLOCK_ID)  # footer ID copy

    return bytes(data)


def _build_apk_signing_block(v2_signing_data):
    """
    Build the complete APK Signing Block:
      uint64: block_size  -- size from first ID to last Size
      uint64: 8  -- ID size
      uint64: APK_SIG_BLOCK_ID  -- header ID
        uint64: entry_id  -- = APK_SIG_BLOCK_ID
        uint64: entry_size  -- size of (algorithm_id + v2_signing_data)
        uint32: algorithm_id  -- = APK_SIG_BLOCK_ID
        byte[] v2_signing_data
      uint64: APK_SIG_BLOCK_ID  -- footer ID
      uint64: block_size  -- footer size copy
    """
    entry_id = APK_SIG_BLOCK_ID
    # entry_size = algorithm_id (4 bytes) + v2_signing_data
    entry_size = 4 + len(v2_signing_data)

    # block_size = 8 (ID size) + 8 (ID value)
    #            + 8 (entry ID) + 8 (entry size) + entry_size
    #            + 8 (footer ID) + 8 (footer size)
    block_size = 8 + 8 + 8 + 8 + entry_size + 8 + 8

    block = bytearray()
    block += _u64le(block_size)
    block += _u64le(8)  # ID size
    block += _u64le(APK_SIG_BLOCK_ID)  # header ID

    # Entry inside the block: entry_id + entry_size + algorithm_id + entry_data
    block += _u64le(entry_id)
    block += _u64le(entry_size)
    block += _u32le(APK_SIG_BLOCK_ID)  # algorithm_id within the entry
    block += v2_signing_data

    # Footer
    block += _u64le(APK_SIG_BLOCK_ID)  # footer ID
    block += _u64le(block_size)  # footer size copy

    return bytes(block)


def _find_cd_offset(raw_data):
    """Find the central directory offset from the EOCD record."""
    eocd_sig = b'\x50\x4b\x05\x06'
    eocd_pos = raw_data.rfind(eocd_sig)
    if eocd_pos < 0:
        raise RuntimeError("EOCD not found in APK")
    # EOCD: signature(4) + disk(2) + disk_start(2) + num_entries_disk(2) +
    #       num_entries_total(2) + cd_size(4) + cd_offset(4) + comment_len(2)
    cd_offset = struct.unpack('<I', raw_data[eocd_pos + 16:eocd_pos + 20])[0]
    cd_size = struct.unpack('<I', raw_data[eocd_pos + 12:eocd_pos + 16])[0]
    return cd_offset, cd_size, eocd_pos


def sign_apk_v2(input_apk, output_apk, private_key, cert_der):
    """
    Add APK Signature Scheme v2 block to an already v1-signed APK.
    The v2 block is inserted between local file data and central directory.
    """
    # Read all entries from the input APK (for digest computation)
    entries_data = []
    with zipfile.ZipFile(input_apk, 'r') as zin:
        for info in zin.infolist():
            data = zin.read(info.filename)
            entries_data.append((info.filename, data))

    # Compute v2 digests
    digests_map = _compute_v2_digests(entries_data)

    # Build signing entries
    signing_entries = _build_signing_entries(digests_map, private_key, cert_der)

    # Build v2 signing data
    v2_signing_data = _build_v2_signing_data(signing_entries)

    # Build APK Signing Block
    apk_sig_block = _build_apk_signing_block(v2_signing_data)

    # Read raw APK data
    with open(input_apk, 'rb') as f:
        raw_data = f.read()

    # Find central directory position
    cd_offset, cd_size, eocd_pos = _find_cd_offset(raw_data)

    # Everything before cd_offset is local headers + file data
    # The APK Signing Block goes between file data and central directory
    local_data = raw_data[:cd_offset]
    central_dir_data = raw_data[cd_offset:eocd_pos]
    eocd_data = bytearray(raw_data[eocd_pos:])

    # New central directory offset after inserting v2 block
    new_cd_offset = len(local_data) + len(apk_sig_block)

    # Update EOCD: cd_offset is at bytes 16-19
    eocd_data[16:20] = struct.pack('<I', new_cd_offset)

    # Write output APK: local_data + apk_sig_block + central_dir + eocd
    with open(output_apk, 'wb') as f:
        f.write(local_data)
        f.write(apk_sig_block)
        f.write(central_dir_data)
        f.write(eocd_data)

    print(f"APK v2 signed: {output_apk} ({os.path.getsize(output_apk)} bytes)")


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: python apk_sig_v2.py <input_apk> <output_apk> <signer_key.pem> <signer_cert.pem>")
        sys.exit(1)

    from cryptography.hazmat.primitives import serialization
    from cryptography import x509

    input_apk = sys.argv[1]
    output_apk = sys.argv[2]
    key_path = sys.argv[3]
    cert_path = sys.argv[4]

    with open(key_path, 'rb') as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    with open(cert_path, 'rb') as f:
        cert_data = f.read()
        if cert_data.startswith(b'-----BEGIN'):
            cert = x509.load_pem_x509_certificate(cert_data)
            cert_der = cert.public_bytes(serialization.Encoding.DER)
        else:
            cert_der = cert_data

    sign_apk_v2(input_apk, output_apk, private_key, cert_der)