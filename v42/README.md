# V42 — auditoria do motor Gen 1–9

Esta pasta traz para o `main` o que é **reproduzível** da auditoria da V42. Ela não
contém o motor: o código dele (`firered_gen1_9/`, 10,1 MiB / 708 arquivos) vive no
PR #9 e é extraído sob demanda pelo script daqui, sem ser versionado.

## Por que existe

O `.deb` do mGBA no Debian exige GLIBC 2.38 e quebra neste ambiente, então a suíte
nativa do motor nunca tinha rodado aqui. A fonte do mGBA **é vendorizada** pelo
próprio repositório (`tools/gba_shim`), então basta compilar o core libretro.

## Como rodar

```sh
# 0) dependências Python (o pip do sistema é bloqueado por PEP 668)
python3 -m venv .venv
.venv/bin/pip install capstone keystone-engine unicorn
export PATH="$PWD/.venv/bin:$PATH"

# 1) fonte do mGBA + shim (uma vez; fica em tools/gba_shim/build/, fora do Git)
make -C tools/gba_shim libmgba shim PYTHON_BIN=python3

# 2) core libretro
CORE=$(bash v42/scripts/build_libretro_core.sh)

# 3) a suíte (precisa da ROM — ver abaixo)
bash v42/scripts/run_cosmog_tests.sh
```

A ROM **não** é versionada, e nem os save-states. `COSMOG_V42_ROM` precisa apontar
para a V42 exata (`6997366b…bd99a`); os testes recusam qualquer outro SHA. Sem ela,
o script sai com código 2 e a mensagem "ROM ausente" — de propósito, para não
confundir falta de insumo com regressão.

## Resultado da rodada de 07/11/2026

| Suíte | Resultado |
|---|---|
| `test_cosmog_v42` (estruturais) | **3/3 OK** |
| `test_cosmog_v42_mgba` (nativas) | **4/4 OK** em 202 s |
| `test_cosmog_hatch_v42_mgba` (eclosão, novo) | **bloqueado por custo** — ver abaixo |

Antes dessa rodada, a suíte nativa estava **"nunca executada"** desde a publicação.
Agora está verde.

## A eclosão não fecha — e o número é este

O ovo de Cosmog tem **120 ciclos × 255 passos = ~30.600 passos**. Cada passo exige
serializar o estado inteiro (528.448 B) só para ler a coordenada: **~2,4 s/passo**,
medido. Dá **~20 h**. O caminho barato (leitura direta de memória) não existe neste
core: `RETRO_ENVIRONMENT_SET_MEMORY_MAPS` (cmd 36) **nunca é emitido** — instrumentei
o callback e registrei os comandos recebidos (`52, 16, 10, 11, 65587, 15, 27, 9,
65572, 65578, 17`).

Detalhes, incluindo um erro meu que foi corrigido (confundir "contador de ciclos
mudou" com "eclodiu"), em
[`reports/v42/AUDITORIA_COSMOG_ECLOSAO_V42.md`](../reports/v42/AUDITORIA_COSMOG_ECLOSAO_V42.md).

## O que continua NÃO certificado

- Eclosão do ovo (bloqueada por custo de harness, não por bug).
- Solgaleo e Lunala no mesmo save.
- Campanha completa desde o início (chegadas e pais são sintéticos).
- Retirada do pai pela interface da creche.

## Arquivos

| Arquivo | O que é |
|---|---|
| `scripts/build_libretro_core.sh` | compila `mgba_libretro.so` da fonte vendorizada |
| `scripts/run_cosmog_tests.sh` | agrega estruturais + nativas + eclosão |
| `tests/test_cosmog_hatch_v42_mgba.py` | teste de eclosão (chega ao laço e mede) |
