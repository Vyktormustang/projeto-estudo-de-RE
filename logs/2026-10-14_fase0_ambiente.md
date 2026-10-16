# FASE 0 — Verificação do ambiente (2026-10-14, ~16:22 UTC)

Todas as saídas abaixo foram capturadas de comandos reais neste ambiente.

## Sistema operacional

```
$ uname -a
Linux e2b.local 6.1.158+ #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux
$ cat /etc/os-release (resumo)
PRETTY_NAME="Debian GNU/Linux 13 (trixie)"   VERSION_ID="13"
```

**DIVERGÊNCIA COM O BRIEFING (importante):** o briefing pede Windows; o ambiente de
execução real é Linux (sandbox). Decisão: scripts multiplataforma; quando o usuário
quiser executar na própria máquina Windows, serão fornecidos equivalentes em
PowerShell/CMD. Nenhuma etapa depende de Windows.

## Recursos

```
RAM total: 1.9 GB (1.5 GB disponível)   Swap: 0
Disco /: 25 GB total, 21 GB livres (17%)
CPU: 2 × Intel Xeon @ 2.60 GHz
```

Implicação: Ghidra pesado fica apertado em RAM (rodaria com -Xmx1g); análise de
ROM GBA (≤32 MB) é viável. Depende de decisão na Fase 2.

## Toolchain disponível

| Ferramenta | Estado |
|---|---|
| Python | 3.13.16 (`/usr/local/bin/python3`), pip 26.2.1 |
| capstone-py | 5.0.7 (instalado nesta sessão; ver scripts/setup_env.sh) |
| Java | OpenJDK 11 — **atenção: Ghidra ≥ 11 exige JDK 17** (Ghidra 10.x aceita 11) |
| Git | 2.47.3 |
| Internet | OK (HTTP 200 em github.com, 2026-10-14) |
| radare2 / devkitARM / gdb-multiarch / mGBA / xxd | AUSENTES (não instalar sem necessidade concreta) |
| strings, file, objdump(x86) | presentes |

## ROM

Busca por `*.gba *.agb *.bin *.zip *.7z *.rar *.sav` em /home/user: **0 arquivos**.
Workspace estava vazio. **Status: AGUARDANDO_ROM.**

## Manifesto de artefatos criados neste ciclo (SHA-256)

```
c2a6e75e397c95db3a954dba2ac80442ef32795a7997908e5e01fb1c82a5c4b9  README.md
7df66abdb4c952dcd4e96f633bae8a988a001d5d8f8d8a5956e88ea897cdaf8d  functions.csv
1184d0e6219c159cc83dcaf3c307d76c12a8d4519a302f907f10d6f8de8be7d3  hypotheses.md
77f3e6f20a9e36fc9c6eeb065bf9f77eef936e08efa8dd933081cd72156f5f86  scripts/gba_ident.py
4b96a9ad7cea381be39f69f67d89c3b2206b336597a25bd862c7bbe9ffdca832  scripts/setup_env.sh
0aa75c5c0bea1cacf7eb86ce00ce576ca9a44dcf77e0fe9ffb8a400f989d9e65  tests/fixture_sintetico.gba (SINTÉTICA)
```

(inventory.json era versão pré-teste neste hash; após --update-inventory foi
atualizado e passa a conter os próprios hashes dos relatórios.)

## Testes executados neste ciclo

1. `python3 scripts/gba_ident.py --self-test -v --keep-fixture` → **16/16 PASS** (exit 0).
   - Bug real encontrado e corrigido durante o teste: fixture colava bytes ASCII do
     bloco aleatório na string de controle; extrator estava correto, fixture foi corrigida.
2. Análise completa da fixture sintética → relatórios em `reports/` (exit 0).
3. Casos de erro: arquivo inexistente / <0xC0 bytes / .zip → exit 3 com mensagem clara;
   sem argumentos → help + exit 2 (verificado; pipeline `tail` mascarou o código num
   teste, revalidado sem pipe).
