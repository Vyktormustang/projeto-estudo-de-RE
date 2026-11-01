"""Testes sem ROM comercial para o instalador do treino."""
import hashlib
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import treino_ev as mod


class TreinoPatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = bytearray(mod.ROM_SIZE)
        base[0xAC:0xB0] = b"BPRE"
        base[mod.HOOK_OFFSET:mod.HOOK_OFFSET + len(mod.ORIGINAL_HOOK)] = mod.ORIGINAL_HOOK
        base[mod.PAYLOAD_OFFSET:mod.PAYLOAD_OFFSET + mod.PAYLOAD_SPACE] = b"\xff" * mod.PAYLOAD_SPACE
        cls.rom = bytes(base)
        cls.payload = mod.PAYLOAD_PATH.read_bytes()

    def validate_synthetic(self, rom):
        with mock.patch.object(mod, "BASE_SHA256", hashlib.sha256(rom).hexdigest()):
            mod.validate_source(rom)

    def test_payload_e_hook_compilados_tem_hash_e_entrada_thumb(self):
        mod.validate_payload(self.payload)
        self.assertEqual(mod.HOOK[:4], bytes.fromhex("004b1847"))
        self.assertEqual(struct.unpack_from("<I", mod.HOOK, 4)[0], mod.ROM_START + mod.PAYLOAD_OFFSET + 1)
        self.assertEqual(self.payload[:2], bytes.fromhex("1fb5"))

    def test_instala_somente_no_hook_e_na_regiao_livre(self):
        with mock.patch.object(mod, "BASE_SHA256", hashlib.sha256(self.rom).hexdigest()):
            result = mod.apply_patch(self.rom, self.payload)
        self.assertEqual(result[mod.HOOK_OFFSET:mod.HOOK_OFFSET + 8], mod.HOOK)
        self.assertEqual(result[mod.PAYLOAD_OFFSET:mod.PAYLOAD_OFFSET + len(self.payload)], self.payload)
        mod.verify_output(self.rom, result, self.payload)
        self.assertEqual(self.rom[mod.HOOK_OFFSET:mod.HOOK_OFFSET + 8], mod.ORIGINAL_HOOK)

    def test_rejeita_hash_ou_tamanho_incorreto(self):
        for rom in (b"", self.rom[:-1], self.rom):
            with self.subTest(size=len(rom)), self.assertRaises(mod.PatchError):
                mod.validate_source(rom)

    def test_rejeita_prologo_ou_cabecalho_alterado(self):
        for offset in (0xAC, mod.HOOK_OFFSET):
            data = bytearray(self.rom)
            data[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(mod.PatchError):
                self.validate_synthetic(bytes(data))

    def test_rejeita_area_ocupada(self):
        data = bytearray(self.rom)
        data[mod.PAYLOAD_OFFSET + 3500] = 0
        with self.assertRaises(mod.PatchError):
            self.validate_synthetic(bytes(data))

    def test_rejeita_ponteiro_alinhado_para_area_reservada(self):
        data = bytearray(self.rom)
        struct.pack_into("<I", data, 0x100, mod.ROM_START + mod.PAYLOAD_OFFSET + 9)
        with self.assertRaisesRegex(mod.PatchError, "Referência"):
            self.validate_synthetic(bytes(data))

    def test_rejeita_payload_alterado_ou_excessivo(self):
        for payload in (b"", self.payload[:-1], self.payload + b"x", b"a" * (mod.PAYLOAD_SPACE + 1)):
            with self.subTest(size=len(payload)), self.assertRaises(mod.PatchError):
                mod.validate_payload(payload)

    def test_verificador_pega_diferenca_externa(self):
        with mock.patch.object(mod, "BASE_SHA256", hashlib.sha256(self.rom).hexdigest()):
            result = bytearray(mod.apply_patch(self.rom, self.payload))
        for index in (0x400, mod.HOOK_OFFSET, mod.PAYLOAD_OFFSET, mod.PAYLOAD_OFFSET + len(self.payload)):
            damaged = result.copy()
            damaged[index] ^= 1
            with self.subTest(index=index), self.assertRaises(mod.PatchError):
                mod.verify_output(self.rom, bytes(damaged), self.payload)

    def test_criacao_nao_sobrescreve_arquivos_ou_links(self):
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            source, destination = d / "origem.gba", d / "nova.gba"
            source.write_bytes(b"original")
            mod.write_new_file(source, destination, b"saida")
            self.assertEqual(source.read_bytes(), b"original")
            self.assertEqual(destination.read_bytes(), b"saida")
            for target in (source, destination):
                with self.subTest(target=target), self.assertRaises(mod.PatchError):
                    mod.write_new_file(source, target, b"sobrescrita")
            hard = d / "hardlink.gba"
            os.link(source, hard)
            with self.assertRaises(mod.PatchError):
                mod.write_new_file(source, hard, b"sobrescrita")
            symbolic = d / "simbolico.gba"
            symbolic.symlink_to(source)
            with self.assertRaises(mod.PatchError):
                mod.write_new_file(source, symbolic, b"sobrescrita")
            dangling = d / "ausente.gba"
            dangling.symlink_to(d / "outro.gba")
            with self.assertRaises(mod.PatchError):
                mod.write_new_file(source, dangling, b"sobrescrita")
            self.assertEqual(source.read_bytes(), b"original")
            self.assertEqual(destination.read_bytes(), b"saida")

    def test_erro_de_origem_nao_cria_arquivo_de_saida(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "incompativel.gba"
            destination = Path(directory) / "nao_criar.gba"
            source.write_bytes(b"incompativel")
            self.assertEqual(mod.main(["--rom", str(source), "--saida", str(destination)]), 1)
            self.assertFalse(destination.exists())
            self.assertEqual(source.read_bytes(), b"incompativel")


if __name__ == "__main__":
    unittest.main()
