#!/usr/bin/env python3
"""
Cria APK base em Python sem precisar de aapt2 link ou android.jar.
Gera:
  1. AndroidManifest.xml em formato AXML binário válido
  2. resources.arsc em formato ResTable mínimo
  3. classes.dex (mínimo)
Empacota tudo como APK base alinhado a 4 bytes.
"""
import struct, zlib, zipfile, os, sys

SRC_MANIFEST = "/home/user/projeto-estudo-de-RE/apex_forge/android/AndroidManifest.xml"
ASSETS_DIR = "/home/user/projeto-estudo-de-RE/apex_forge/android/assets"
RES_ZIP = "/tmp/forja_apk_build/res.zip"
DEX_PATH = "/tmp/forja_apk_build/dex/classes.dex"
OUTPUT = "/tmp/forja_apk_build/base.apk"


# ============================================================
# AXML (Android Binary XML) writer - implementação correta
# ============================================================

def write_axml(manifest_path):
    """Converte AndroidManifest.xml de texto para AXML binário válido."""
    import xml.etree.ElementTree as ET

    tree = ET.parse(manifest_path)
    root = tree.getroot()

    # Coletar todas as strings únicas
    strings = set()

    def collect_strings(elem):
        strings.add(elem.tag)
        for k, v in elem.attrib.items():
            strings.add(k)
            # Extrair nome do atributo sem namespace para lookup
            if k.startswith('{'):
                aname = k.split('}', 1)[1]
                strings.add(aname)
            strings.add(v)
        for child in elem:
            collect_strings(child)

    collect_strings(root)

    # Adicionar strings especiais do namespace android
    strings.add("http://schemas.android.com/apk/res/android")
    strings.add("android")

    # Ordenar strings para determinismo
    string_list = sorted(strings)
    string_index = {s: i for i, s in enumerate(string_list)}

    # ===== Construir string pool =====
    # Formato: RES_XML_STRINGS_TYPE (0x0001)
    # header: type(2), headerSize(2), size(4), stringCount(4), styleCount(4),
    #         flags(4), stringsStart(4), stylesStart(4)
    # depois: stringOffsets[stringCount * 4], styleOffsets[styleCount * 4]
    # depois: dados das strings (UTF-16-LE null-terminated, como no Android real)

    string_data = bytearray()
    string_offsets = []
    strings_start = 28 + len(string_list) * 4  # após header + offsets

    for s in string_list:
        encoded = s.encode('utf-16-le')
        string_offsets.append(strings_start + len(string_data))
        string_data.extend(struct.pack('<H', len(s)))  # número de caracteres
        string_data.extend(encoded)
        string_data.extend(b'\x00\x00')  # null terminator em UTF-16-LE

    styles_start = strings_start + len(string_data)
    string_pool_size = 28 + len(string_list) * 4 + len(string_data)

    # Alinhar string pool a 4 bytes
    while string_pool_size % 4 != 0:
        string_pool_size += 1

    sp_chunk = bytearray(struct.pack('<HHIIIIII',
        0x0001,                                    # type = RES_XML_STRINGS_TYPE
        0x001c,                                    # headerSize = 28
        string_pool_size,                          # total size
        len(string_list),                          # stringCount
        0,                                         # styleCount
        0,                                         # flags = 0 (UTF-8 per spec, mas usamos UTF-16-LE como v22.0)
        strings_start,                             # stringsStart
        styles_start,                              # stylesStart
    ))
    for off in string_offsets:
        sp_chunk.extend(struct.pack('<I', off))
    sp_chunk.extend(string_data)
    while len(sp_chunk) % 4 != 0:
        sp_chunk.append(0)

    # ===== Construir XML chunks =====
    xml_chunks = bytearray()

    def write_start_namespace(prefix_idx, uri_idx):
        xml_chunks.extend(struct.pack('<HHIII',
            0x0100,  # RES_XML_START_NAMESPACE_TYPE
            0x0010,  # headerSize = 16
            0x0010,  # size = 16
            prefix_idx,
            uri_idx,
        ))

    def write_end_namespace(prefix_idx, uri_idx):
        xml_chunks.extend(struct.pack('<HHIII',
            0x0101,  # RES_XML_END_NAMESPACE_TYPE
            0x0010,
            0x0010,
            prefix_idx,
            uri_idx,
        ))

    def write_start_tag(ns_idx, name_idx, attributes):
        attr_count = len(attributes)
        attr_start = 0x0010  # attributes start right after the start tag header
        attr_size = 0x0014   # 20 bytes per attribute
        chunk_size = 0x0010 + attr_count * attr_size
        xml_chunks.extend(struct.pack('<HHIIIIIHHHHHH',
            0x0102,      # RES_XML_START_TAG_TYPE
            0x0010,      # headerSize = 16
            chunk_size,  # total size
            0,           # lineNumber
            0xFFFFFFFF,  # comment
            ns_idx,      # namespace
            name_idx,    # name
            attr_start,  # attributeStart
            attr_size,   # attributeSize
            attr_count,  # attributeCount
            0,           # idIndex
            0,           # classIndex
            0,           # styleIndex
        ))
        for (ans_idx, aname_idx, aval_idx, atype, adata) in attributes:
            xml_chunks.extend(struct.pack('<IIIII',
                ans_idx,    # attribute namespace
                aname_idx,  # attribute name
                aval_idx,   # attribute value string index
                atype,      # attribute value type
                adata,      # attribute data
            ))

    def write_end_tag(ns_idx, name_idx):
        xml_chunks.extend(struct.pack('<HHIIIII',
            0x0103,  # RES_XML_END_TAG_TYPE
            0x0010,  # headerSize = 16
            0x0010,  # size = 16
            0,       # lineNumber
            0xFFFFFFFF,  # comment
            ns_idx,  # namespace
            name_idx,  # name
        ))

    def write_end_document():
        xml_chunks.extend(struct.pack('<HH',
            0x0105,  # RES_XML_END_DOCUMENT_TYPE
            0x0008,  # headerSize = 8
        ))

    # Namespace URI for android
    android_uri_idx = string_index["http://schemas.android.com/apk/res/android"]
    android_prefix_idx = string_index["android"]

    # Walk the XML tree
    def walk(elem, parent_ns_idx=0xFFFFFFFF):
        tag_name = elem.tag
        if tag_name.startswith('{'):
            ns_uri, local_name = tag_name[1:].split('}', 1)
            ns_idx = string_index.get(ns_uri, parent_ns_idx)
            name_idx = string_index[local_name]
        else:
            ns_idx = parent_ns_idx
            name_idx = string_index[tag_name]

        # Collect attributes
        attributes = []
        for k in sorted(elem.attrib.keys()):
            v = elem.attrib[k]
            if k.startswith('{'):
                ans_uri, aname = k[1:].split('}', 1)
                ans_idx = string_index.get(ans_uri, 0xFFFFFFFF)
                aname_idx = string_index[aname]
            else:
                if k.startswith('android:'):
                    ans_idx = string_index["http://schemas.android.com/apk/res/android"]
                    aname_idx = string_index[k.replace('android:', '')]
                else:
                    ans_idx = 0xFFFFFFFF
                    aname_idx = string_index[k]
            aval_idx = string_index[v]
            attributes.append((ans_idx, aname_idx, aval_idx, 3, 0))  # type 3 = string reference

        # Write start namespace for manifest element
        if tag_name == 'manifest' or (tag_name.startswith('{') and tag_name.split('}')[1] == 'manifest'):
            write_start_namespace(android_prefix_idx, android_uri_idx)

        write_start_tag(ns_idx, name_idx, attributes)

        for child in elem:
            walk(child, ns_idx)

        write_end_tag(ns_idx, name_idx)

        # Write end namespace
        if tag_name == 'manifest' or (tag_name.startswith('{') and tag_name.split('}')[1] == 'manifest'):
            write_end_namespace(android_prefix_idx, android_uri_idx)

    walk(root)
    write_end_document()

    # ===== Montar documento AXML completo =====
    # RES_XML_FIRST_CHUNK_TYPE header (headerSize = 8)
    xml_total = 8 + len(sp_chunk) + len(xml_chunks)
    doc_header = struct.pack('<HHI',
        0x0003,  # type = RES_XML_FIRST_CHUNK_TYPE
        0x0008,  # headerSize = 8
        xml_total,  # total size
    )

    result = bytearray(doc_header)
    result.extend(sp_chunk)
    result.extend(xml_chunks)

    return bytes(result)


# ============================================================
# resources.arsc writer (minimal, mas com pacote válido)
# ============================================================

def write_resources_arsc():
    """Cria um resources.arsc mínimo válido com pacote android."""
    PACKAGE_SIZE = 0x0100
    HEADER_SIZE = 8
    TOTAL_SIZE = HEADER_SIZE + PACKAGE_SIZE

    # RES_TABLE_HEADER
    header = struct.pack('<HHI', 0x0002, HEADER_SIZE, TOTAL_SIZE)

    # RES_TABLE_PACKAGE header
    pkg_header = struct.pack('<HH', 0x0002, PACKAGE_SIZE)

    # RES_TABLE_PACKAGE body
    pkg_body = struct.pack('<IIIIIIII',
        1,          # id
        PACKAGE_SIZE,  # typeCount
        PACKAGE_SIZE,  # typeCount (again)
        PACKAGE_SIZE,  # typeStrings offset
        PACKAGE_SIZE,  # lastPublicType index
        PACKAGE_SIZE,  # keyStrings offset
        PACKAGE_SIZE,  # lastPublicKey index
        PACKAGE_SIZE,  # packageSize
    )

    # Nome do pacote: "android\0" em UTF-16-LE, preenchido com zeros até 128 bytes
    name = 'android\0'.encode('utf-16-le') + b'\x00\0' * ((128 - 16) // 2)
    package = pkg_header + pkg_body + name
    while len(package) < PACKAGE_SIZE:
        package += b'\x00'

    aresc = header + package
    assert len(aresc) == TOTAL_SIZE
    return aresc


# ============================================================
# DEX generator
# ============================================================

def generate_minimal_dex(dex_path):
    """Gera classes.dex mínimo válido (DEX v035 com header vazio)."""
    import struct
    magic = b'dex\n035\0'
    checksum = b'\x00\x00\x00\x00'
    signature = b'\x00' * 20
    header = magic + checksum + signature
    header += struct.pack('<IIIIIIIIIIIIIIIIIIII',
        0x70,      # fileSize
        0x70,      # headerSize
        0x12345678, # endianTag
        0, 0,      # linkSize, linkOff
        0,         # mapOff
        0, 0,      # stringIdsSize, stringIdsOff
        0, 0,      # typeIdsSize, typeIdsOff
        0, 0,      # protoIdsSize, protoIdsOff
        0, 0,      # fieldIdsSize, fieldIdsOff
        0, 0,      # methodIdsSize, methodIdsOff
        0, 0,      # classDefsSize, classDefsOff
        0, 0,      # padding
    )
    os.makedirs(os.path.dirname(dex_path), exist_ok=True)
    with open(dex_path, 'wb') as f:
        f.write(header)
        while f.tell() % 4 != 0:
            f.write(b'\x00')


# ============================================================
# Main
# ============================================================

def main():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    # Generate minimal DEX
    generate_minimal_dex(DEX_PATH)

    # 1. AXML manifest
    axml_data = write_axml(SRC_MANIFEST)

    # 2. resources.arsc
    arsc_data = write_resources_arsc()

    # 3. classes.dex
    with open(DEX_PATH, 'rb') as f:
        dex_data = f.read()

    # 4. Assets
    asset_entries = []
    if os.path.isdir(ASSETS_DIR):
        for root, dirs, files in os.walk(ASSETS_DIR):
            for fname in files:
                fpath = os.path.join(root, fname)
                arcname = os.path.relpath(fpath, ASSETS_DIR)
                with open(fpath, 'rb') as f:
                    asset_entries.append(('assets/' + arcname, f.read()))

    # 5. Compiled resources from aapt2 (res.zip)
    res_entries = []
    if os.path.exists(RES_ZIP):
        with zipfile.ZipFile(RES_ZIP, 'r') as z:
            for info in z.infolist():
                fname = info.filename
                if fname.endswith('.flat'):
                    continue
                if fname.startswith('res/') and not fname.endswith('/'):
                    res_entries.append((fname, z.read(info.filename)))

    # Build APK base (aligned to 4 bytes)
    all_entries = [
        ('AndroidManifest.xml', axml_data, zipfile.ZIP_DEFLATED),
        ('resources.arsc', arsc_data, zipfile.ZIP_STORED),
        ('classes.dex', dex_data, zipfile.ZIP_DEFLATED),
    ] + [(f, d, zipfile.ZIP_STORED) for f, d in res_entries] + [(f, d, zipfile.ZIP_DEFLATED) for f, d in asset_entries]

    with open(OUTPUT, 'wb') as f:
        current_offset = 0
        central_dir = []

        for filename, data, compress_type in all_entries:
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

            new_info = zipfile.ZipInfo(filename, date_time=(2026, 10, 25, 12, 0, 0))
            new_info.external_attr = 0o644 << 16
            new_info.compress_type = ct
            central_dir.append((new_info, crc, comp_size, uncomp_size, len(filename_bytes), local_offset))

        # Central directory
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

        # End of central directory
        f.write(struct.pack('<IHHHHIIH',
            0x06054b50, 0, 0,
            len(central_dir), len(central_dir),
            cd_end - cd_start, cd_start, 0))

    print("Base APK written: %s (%d bytes)" % (OUTPUT, os.path.getsize(OUTPUT)))


if __name__ == '__main__':
    main()