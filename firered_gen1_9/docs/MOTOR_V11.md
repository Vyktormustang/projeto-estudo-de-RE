# Motor v11 — correção isolada de Eerie Spell

**02/11/2026 — etapa concluída; projeto ainda parcial.** Esta versão corrige um defeito demonstrado no motor v10, sem habilitar golpes novos, modificar IA ou alterar o formato do save. Testes exclusivamente sintéticos em mGBA 0.10.5, sem saves pessoais. ROMs permanecem fora do Git.

## Fato reproduzido e correção

`Eerie Spell` (ID interno **720**) no helper `hook_post_hit_v10` procurava o **primeiro slot com golpe e PP**, não o último golpe usado pelo alvo. O comentário no código mencionava o último golpe, mas o laço não consultava histórico algum.

Reprodução automatizada: alvo adormecido com golpes `(33, 150, 45, 39)`, PPs `(10,10,10,10)` e último golpe registrado `45` (Growl, slot 2, índices começando em zero). O usuário atua primeiro com Eerie Spell:

| ROM | PPs do alvo após o turno |
|---|---|
| v10, defeito reproduzido | `(7,10,10,10)` — drena Tackle, slot errado |
| v11, correção | `(10,10,7,10)` — drena Growl, slot 2 |

A fixture v10 é criada na própria ROM v10; a fixture v11 é criada separadamente na ROM v11. Não há reaproveitamento de save states entre versões. Além da injeção controlada de histórico, um teste de dois turnos verifica o histórico registrado naturalmente: o alvo usa Splash e, no turno seguinte, perde três PPs adicionais por Eerie Spell.

O novo helper:

- Consulta `gLastMoves[target]` em `0x020215D4`, identificado pelo comando nativo Spite (`0xAD`, função `0x080628DC`, literal `0x08062A54`).
- Reduz até três PPs somente do slot correspondente, com piso zero. Histórico ausente, inválido, não encontrado no moveset ou golpe já sem PP não provocam busca por outro slot.
- Não drena após falha, Protect, imunidade, alvo ausente/desmaiado ou com Substitute presente no pós-impacto.
- Sincroniza o PP na estrutura criptografada da equipe e no controller; espera o controller antes de `moveend`.
- Respeita os mesmos indicadores de golpes temporários usados por Spite/ppreduce nativos: Transform (`status2 & 0x00200000`) e Mimic (`gDisableStructs[b].mimickedMoves`, nibble alto de `+0x18`). Nesses casos altera apenas os PPs temporários de batalha, não os originais da equipe.
- Encadeia todos os demais golpes ao helper original `0x090D0061`.

## Hipótese descartada: Mighty Cleave

A ausência de uma comparação explícita por ID `794` no hook v10 **não prova ausência da mecânica**. A tabela já tem `flags=0x31`, sem o bit de bloqueio por Protect. No teste v10, Protect bloqueou Tackle (HP do alvo `480 → 480`), mas Mighty Cleave acertou (`480 → 464`). O teste correspondente também passa em v11. **Nenhum byte de Mighty Cleave foi alterado.**

## Escopo de bytes

O aplicador valida o hash completo de entrada, o hash do payload, o callasm anterior e a região livre antes de escrever. O teste reconstrói a saída e restaura as três regiões abaixo, exigindo igualdade integral com a entrada:

| Região (offset de arquivo) | Escrita |
|---|---|
| `0x10CD428..0x10CD42C` | callasm pós-impacto do script padrão v10, redirecionado ao wrapper v11 |
| `0x10D6000..0x10D6005` | `waitstate; goto moveend` — seis bytes |
| `0x10D6100..0x10D626B` | payload Thumb-1 de 364 bytes |

Entrada Thumb do wrapper: `0x090D6101`. **Nenhuma reserva nova de EWRAM.** Nenhuma tabela de golpes, aprendizados, itens/TMs/HMs, encontros, eventos ou treino foi modificada. O restante do motor v10 permanece byte a byte igual. A preservação estrutural não equivale a uma campanha completa testada.

## Hashes SHA-256

| Artefato | SHA-256 |
|---|---|
| Entrada `motor_v10.gba` | `a533d1812812e2348bbe62a95a8c3817dd9d8372a89ff283f0e747c6c7ddeb09` |
| Saída `motor_v11.gba`, 33.554.432 bytes | `1a147ee909183cc2e3bbba0599a4d70f0b0185b01d3e4941a1f27e6c4a9eee5b` |
| `patches/motor_v11/payload.bin`, 364 bytes | `0264257315bfe35e6012808c3d6e21bf98d60e372c81dc5843976b8271940dfc` |

Fontes: `patches/motor_v11/{entry.s,motor_v11.c,payload.ld}`. Aplicador: `scripts/motor_v11.py`. Catálogo permanece `data/learnsets_motor_v10.csv`, **15.008 linhas / 708 das 729 omissões restauradas**. Continuam pendentes **Simple Beam, Ally Switch, Instruct e Revival Blessing (21 linhas)**. Os rascunhos de um gerador que habilitaria Simple Beam/Instruct não foram incorporados: não há implementação validada desses golpes nesta versão.

## Testes executados — 28/28, nenhum pulado nas duas execuções abaixo

- **5 estruturais:** hash/vetor Thumb, recusa de ROM/payload divergentes, preservação exata fora das três escritas e proteção de saída existente, inclusive symlink, hardlink e symlink pendente.
- **8 dirigidos mGBA:** reprodução v10; slot correto e checksum; histórico inválido/ausente e limites PP 0/1/2/3; Transform/Mimic; Protect/imunidade; Substitute; Mighty Cleave/Tackle; histórico natural em dois turnos.
- **6 regressões herdadas v10, executadas na v11:** famílias A–E e estojo/229 TMs/save sintético, incluindo duplas nas fixtures existentes.
- **9 regressões de treino EV/IV na v11.**

```sh
# Na raiz do repositório, sempre com saída inexistente.
python3 firered_gen1_9/scripts/motor_v11.py \
  --rom /caminho/motor_v10.gba --saida /caminho/nova_motor_v11.gba

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
MOTOR_V11_BASE=/caminho/motor_v10.gba \
MOTOR_V11_ROM=/caminho/nova_motor_v11.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_motor_v11*.py' -v
# 19/19 (5 + 8 + 6), execução registrada: 253,877 s

PYTHONPATH=firered_gen1_9:firered_gen1_9/tests \
TREINO_TEST_ROM=/caminho/nova_motor_v11.gba \
MGBA_CORE=/caminho/mgba_libretro.so \
python3 -m unittest discover -s firered_gen1_9/tests -p 'test_treino_ev_mgba.py' -v
# 9/9, execução registrada: 22,524 s
```

Compilação usada (`python3 -m ziglang version`: `0.17.0`):

```sh
python3 -m ziglang cc -target thumb-freestanding-eabi -mcpu=arm7tdmi \
  -mthumb -Os -fno-builtin -nostdlib -Wall -Wextra -Werror \
  -Wl,--nmagic -Wl,-e,entry_post_hit_v11 \
  -Wl,-T,firered_gen1_9/patches/motor_v11/payload.ld \
  firered_gen1_9/patches/motor_v11/entry.s \
  firered_gen1_9/patches/motor_v11/motor_v11.c -o /tmp/motor_v11.elf
python3 -m ziglang objcopy -O binary /tmp/motor_v11.elf /tmp/payload_v11.bin
sha256sum /tmp/payload_v11.bin
```

## Limites e próximos passos

- Não há implementação de IA moderna, Pledges combinados ou dos quatro golpes adiados. Nenhuma alegação de fidelidade integral a Scarlet/Violet.
- Eerie Spell foi testado em singles; as regressões herdadas incluem duplas, mas não validam especificamente todas as interações de Eerie Spell em duplas. Soundproof, Substitute que se quebra no impacto, golpes copiados por outros mecanismos, travas multi-turno após esgotar PP e histórico após trocas merecem testes dedicados.
- Não foram feitas campanha completa, migração de saves pessoais, link entre jogadores ou Teachy TV completa nesta etapa.
- A exploração estática local identificou a tabela de comandos de IA em `0x081F026C` (referência `0x08004E00`) e a seleção de ação `0x08004C90` chamada em `0x0803DEC0`. Esses endereços são pontos de investigação, **não correções nem provas de qualidade da IA**.
- Próxima prioridade recomendada: ampliar os testes de interações dos golpes já habilitados antes de aumentar o catálogo. Reler `HANDOFF.md` apenas como histórico da outra ROM; não transferir offsets do BAG_MOD para esta base.

Use saves normais feitos pelo menu, com backup separado; não migre save states antigos para v11. O pacote do Drive não foi atualizado nesta etapa; o registro atual está no repositório e no comentário de VYK-57.
