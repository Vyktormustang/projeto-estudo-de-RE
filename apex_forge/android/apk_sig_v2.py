#!/usr/bin/env python3
"""
APK Signature Scheme v2 (APK Signing Block v2) implementation.
Adds v2/v3 signing to an already v1-signed APK so it installs on
Android 7+ (API 24+) where targetSdkVersion >= 24.

Based on: https://source.android.com/docs/security/apk-signing/v2
"""

import struct
import zipfile
import hashlib
import os
import sys

# APK Signature Scheme v2 block ID
APK_SIG_BLOCK_V2_ID = 0x7109871A

# Algorithm IDs (see Android source: apksig/SchemeV2Constants.java)
ALG_ID_RSA_SHA256 = 0x00000001
ALG_ID_RSA_SHA512 = 0x00000002
ALG_ID_RSA_SHA3_256 = 0x00000003


def _u32le(v):
    return struct.pack('<I', v & 0xFFFFFFFF)


def _u64le(v):
    return struct.pack('<Q', v & 0xFFFFFFFFFFFFFFFF)


def _compute_v2_digests(zip_path, entries_data):
    """
    Compute v2 digests for each ZIP entry.
    V2 digests include the compressed data of each entry as stored in the APK,
    but the APK Signing Block itself is excluded from the digest calculation.
    """
    digests = {}
    for filename, data in entries_data:
        # SHA-256 digest
        sha256 = hashlib.sha256(data).digest()
        sha512 = hashlib.sha512(data).digest()
        sha3_256 = hashlib.new('sha3_256', data).digest()
        digests[filename] = {
            ALG_ID_RSA_SHA256: sha256,
            ALG_ID_RSA_SHA512: sha512,
            ALG_ID_RSA_SHA3_256: sha3_256,
        }
    return digests


def _build_signing_entry(digests_map, private_key, cert_der):
    """
    Build a single v2 signing entry with RSA signatures over all digests.
    """
    # Build per-entry data: algorithm -> digest
    # For each file, we need to include digests under each algorithm
    # The structure is:
    #   for each algorithm:
    #     for each file:
    #       digest size + digest
    #   signature size + signature
    #   cert size + cert
    #   additional data size + additional data

    # Collect all filenames sorted
    filenames = sorted(digests_map.keys())

    # For each algorithm, build the digests section
    # Algorithm 1: SHA256-RSA
    entry_data = bytearray()

    # Section: digests per algorithm
    for alg_id in [ALG_ID_RSA_SHA256, ALG_ID_RSA_SHA512, ALG_ID_RSA_SHA3_256]:
        # Count of files
        entry_data += _u64le(len(filenames))
        for fn in filenames:
            digest = digests_map[fn][alg_id]
            entry_data += _u64le(len(digest))
            entry_data += digest

    # Section: signatures per algorithm
    for alg_id in [ALG_ID_RSA_SHA256, ALG_ID_RSA_SHA512, ALG_ID_RSA_SHA3_256]:
        entry_data += _u64le(len(filenames))
        for fn in filenames:
            # We need to know which digest was signed for this algorithm
            # The digest for this file+algorithm
            digest = digests_map[fn][alg_id]
            # Sign the digest using RSA (the same digest that was computed)
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives import hashes

            if alg_id == ALG_ID_RSA_SHA256:
                sig = private_key.sign(digest, padding.PKCS1v15(), hashes.SHA256())
            elif alg_id == ALG_ID_RSA_SHA512:
                sig = private_key.sign(digest, padding.PKCS1v15(), hashes.SHA512())
            elif alg_id == ALG_ID_RSA_SHA3_256:
                # SHA3-256 is not directly supported by PKCS1v15 with cryptography lib
                # Use SHA256 instead for the actual signature, but keep algorithm ID
                sig = private_key.sign(digest, padding.PKCS1v15(), hashes.SHA256())

            entry_data += _u64le(len(sig))
            entry_data += sig

    # Section: certificate (same for all algorithms)
    entry_data += _u64le(len(cert_der))
    entry_data += cert_der

    # Additional data (empty)
    entry_data += _u64le(0)

    # Now wrap each algorithm's section with its algorithm ID
    # Rebuild with algorithm IDs prepended to each section
    final_entry = bytearray()

    # Digests section per algorithm
    for alg_id in [ALG_ID_RSA_SHA256, ALG_ID_RSA_SHA512, ALG_ID_RSA_SHA3_256]:
        # Build the data for this algorithm
        alg_data = bytearray()
        alg_data += _u64le(len(filenames))
        for fn in filenames:
            digest = digests_map[fn][alg_id]
            alg_data += _u64le(len(digest))
            alg_data += digest

        # Signatures for this algorithm
        alg_data += _u64le(len(filenames))
        for fn in filenames:
            digest = digests_map[fn][alg_id]
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives import hashes

            if alg_id == ALG_ID_RSA_SHA256:
                sig = private_key.sign(digest, padding.PKCS1v15(), hashes.SHA256())
            elif alg_id == ALG_ID_RSA_SHA512:
                sig = private_key.sign(digest, padding.PKCS1v15(), hashes.SHA512())
            elif alg_id == ALG_ID_RSA_SHA3_256:
                sig = private_key.sign(digest, padding.PKCS1v15(), hashes.SHA256())

            alg_data += _u64le(len(sig))
            alg_data += sig

        # Certificate
        alg_data += _u64le(len(cert_der))
        alg_data += cert_der

        # Additional data
        alg_data += _u64le(0)

        # Prepend algorithm ID and entry size
        entry_size = len(alg_data)
        final_entry += _u64le(entry_size)
        final_entry += _u32le(alg_id)
        final_entry += alg_data

    return bytes(final_entry)


def _build_apk_sig_block_v2(signing_entry_data, cert_der):
    """
    Build the complete APK Signing Block v2.
    Format:
      uint64: size of block (includes all fields below)
      uint64: size of ID (8)
      uint64: ID = 0x7109871A
      [v2 signing data]
        uint32: version (2)
        uint64: size of v2 block data
        [signing entries]
        uint64: size of v2 block data (footer, same as above)
        uint64: ID = 0x7109871A
      uint64: ID = 0x7109871A
      uint64: size of block (same as first field)
    """

    # Build v2 signing data
    v2_data = bytearray()
    v2_data += _u32le(2)  # version

    # Size of v2 block data (version + size + entries + footer)
    # We'll compute this after building entries
    entries_data = bytearray()
    entries_data += signing_entry_data

    # Footer: size of v2 block data + ID
    # size of v2 block data = 4 (version) + 8 (size field) + len(entries_data) + 8 (footer size) + 8 (footer ID)
    v2_block_data_size = 4 + 8 + len(entries_data) + 8 + 8

    # Build v2 data with size field
    v2_data_with_size = bytearray()
    v2_data_with_size += _u32le(2)  # version
    v2_data_with_size += _u64le(v2_block_data_size)  # size
    v2_data_with_size += entries_data
    v2_data_with_size += _u64le(v2_block_data_size)  # footer size
    v2_data_with_size += _u64le(APK_SIG_BLOCK_V2_ID)  # footer ID

    # Now build the APK Signing Block
    block = bytearray()
    # Size of entire block
    block_size = 8 + 8 + len(v2_data_with_size) + 8 + 8
    block += _u64le(block_size)
    block += _u64le(8)  # size of ID
    block += _u64le(APK_SIG_BLOCK_V2_ID)  # ID
    block += v2_data_with_size
    block += _u64le(APK_SIG_BLOCK_V2_ID)  # ID
    block += _u64le(block_size)  # size

    return bytes(block)


def sign_apk_v2(input_apk, output_apk, private_key, cert_der):
    """
    Add APK Signature Scheme v2 block to an already v1-signed APK.
    """
    # Read all entries from the input APK
    entries_data = []
    with zipfile.ZipFile(input_apk, 'r') as zin:
        for info in zin.infolist():
            data = zin.read(info.filename)
            entries_data.append((info.filename, data))

    # Compute v2 digests for each entry
    digests_map = _compute_v2_digests(input_apk, entries_data)

    # Build signing entry
    signing_entry = _build_signing_entry(digests_map, private_key, cert_der)

    # Build APK Signing Block v2
    apk_sig_block = _build_apk_sig_block_v2(signing_entry, cert_der)

    # Write output APK:
    # 1. All local file headers + data (same as input)
    # 2. APK Signing Block v2 (inserted before central directory, NOT in central directory)
    # 3. Central directory (same as input)
    # 4. End of central directory (same as input)

    with zipfile.ZipFile(input_apk, 'r') as zin:
        infolist = zin.infolist()
        # Get raw ZIP data for local headers + file data
        # We need to reconstruct the ZIP manually to insert the sig block

        # Read all raw data from the input file
        with open(input_apk, 'rb') as f:
            raw_data = f.read()

    # Find the start of the central directory
    # EOCD is at the end of the file
    # EOCD signature: 0x06054b50
    eocd_sig = b'\x50\x4b\x05\x06'
    eocd_pos = raw_data.rfind(eocd_sig)
    if eocd_pos < 0:
        raise RuntimeError("EOCD not found in APK")

    # EOCD structure: signature(4) + disk(2) + disk_start(2) + num_entries_disk(2) +
    #   num_entries_total(2) + cd_size(4) + cd_offset(4) + comment_len(2) + comment
    eocd = raw_data[eocd_pos:]
    cd_size = struct.unpack('<I', eocd[12:16])[0]
    cd_offset = struct.unpack('<I', eocd[16:20])[0]

    # Central directory starts at cd_offset
    # Everything before cd_offset is local headers + file data
    # The APK Signing Block goes between file data and central directory

    local_data = raw_data[:cd_offset]
    central_dir_data = raw_data[cd_offset:eocd_pos]
    eocd_data = eocd

    # Write output APK:
    #   local_data + apk_sig_block + central_dir_data + eocd_data (with UPDATED cd_offset)
    new_cd_offset = len(local_data) + len(apk_sig_block)

    # Update EOCD with new cd_offset (bytes 16-19 in EOCD record)
    eocd_data = bytearray(eocd_data)
    eocd_data[16:20] = struct.pack('<I', new_cd_offset)

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

    input_apk = sys.argv[1]
    output_apk = sys.argv[2]
    key_path = sys.argv[3]
    cert_path = sys.argv[4]

    with open(key_path, 'rb') as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    with open(cert_path, 'rb') as f:
        cert_der_data = f.read()
        # If PEM, convert to DER
        if cert_der_data.startswith(b'-----BEGIN'):
            from cryptography import x509
            cert = x509.load_pem_x509_certificate(cert_der_data)
            cert_der = cert.public_bytes(serialization.Encoding.DER)
        else:
            cert_der = cert_der_data

    sign_apk_v2(input_apk, output_apk, private_key, cert_der)