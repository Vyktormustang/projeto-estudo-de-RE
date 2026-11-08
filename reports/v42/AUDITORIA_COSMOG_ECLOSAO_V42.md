# Cosmog V42 — eclosão e suíte nativa consolidada

**07/11/2026.** Execução nativa feita **pela primeira vez** neste ambiente: o core
`mgba_libretro.so` foi compilado aqui a partir da fonte mGBA vendorizada via
`tools/gba_shim`.

**Âncora de reprodutibilidade = o tarball**, não o `.so` compilado: mGBA 0.10.5,
`mgba.tar.gz` com SHA-256 `91d6fbd32abcbdf030d58d3f562de25ebbc9d56040d513ff8e5c19bee9dacf14`
(confere com `tools/gba_shim/mgba_tree.sha256`, verificado no `make fetch`). O `.so`
tem 2.842.664 B em dois builds independentes, mas **hash diferente** — a compilação
não é bit-reprodutível. Citar o hash do `.so` como identidade seria enganoso; o
tarball + a receita (`v42/scripts/build_libretro_core.sh`) são a identidade real.

ROM: `6997366bea7056778e3183595d2e2f84c62a98576430db71b9459962e5bbd99a` (V42 exata).
Nenhum save pessoal; nada foi escrito na ROM.

## O que passou (FATO)

| Teste | Resultado | Tempo |
|---|---|---|
| `test_cosmog_v42` (3 estruturais) | **3/3 OK** | 0,245 s |
| `test_cosmog_v42_mgba::test_native_daycare_contracts` | **OK** | ~27 s |
| `test_cosmog_v42_mgba::test_native_daycare_deposit_and_egg` | **OK** | ~119 s |
| `test_cosmog_v42_mgba::test_capture_persistence_and_full_evolution_branches` | **OK** | — |
| `test_cosmog_v42_mgba::test_evolution_boundary_clock_and_everstone_contracts` | **OK** | — |

Suíte nativa completa: **4/4 OK em 202,102 s** (log `logs/cosmog_20261107_173221.log`).
Agregador `v42/scripts/run_cosmog_tests.sh`: **0 falhas**.

Contratos de creche observados: compatibilidade 20 para 789×132 e 132×789; 0 para
789×789, 132×132 e 151×132; 20 para 1×132. Ovo de espécie 789, nível 5, gerado por
chamada nativa.

Depósito pela interface: os dois pais (789 e 132) entram na creche, a flag de ovo
pendente (`0x266`) aparece após **1.280 passos manuais**, o ovo é retirado do NPC,
e o conjunto sobrevive a SAVE/Continuar com PID distinto do pai.

## O que NÃO foi concluído — e por quê

**Eclosão do ovo.** O teste novo `tests/test_cosmog_hatch_v42_mgba.py` foi escrito e
chega até a incubação, mas **não fecha** neste ambiente:

* O ovo de Cosmog tem **120 ciclos** e cada ciclo custa **255 passos** → ~**30.600
  passos** manuais.
* Cada passo exige uma serialização completa do estado (`retro_serialize`, 528.448 B)
  para detectar mudança de coordenada: **~2,4 s por passo** (medido: 167 passos em
  396 s). O total daria **~20 horas**.
* O caminho alternativo — leitura direta de memória via `retro_get_memory_data` /
  memory maps — **não existe neste core**: `RETRO_ENVIRONMENT_SET_MEMORY_MAPS` (cmd
  36) nunca é emitido. Instrumentei o callback de ambiente e os comandos vistos são
  `52, 16, 10, 11, 65587, 15, 27, 9, 65572, 65578, 17` — **36 não está lá**.

**Correção de um erro meu, registrada:** a primeira versão do teste dava "eclodiu"
quando o *contador de ciclos* do ovo decrementava. Ovo continua ovo até o **bit 30
do IV32** (marcador de ovo) ser desligado. Critério corrigido; **não houve eclosão
falsa**.

## Caminho que fechou isso (medições desta sessão)

O gargalo declarado acima (2,4 s por passo, ~20 h) **não era o gargalo real**. Com o
teste já em rajadas (`BURST_FRAMES=48`, `SAMPLE_FRAMES=8`), a taxa medida é de
**~40 passos/s** — os ~30.600 passos cabem em **~13-15 minutos**. O que faltava era
**orçamento** e a **leitura correta do fim da caminhada**, não velocidade.

Fatos medidos:

* `HATCH_EGG_PICKED steps_to_egg=768` — ovo recebido do NPC, reprodutível.
* Caminhada real de vaivém horizontal em y=22, x∈[16,34], ~40 passos/s.
* **Quatro rodadas independentes travaram em (28,22) por volta de 30.720 passos**, sem
  andar em nenhuma direção. 30.720 = 120 ciclos × 256 — o orçamento exato do ovo.
  Interpretação: **é a cutscene de eclosão assumindo o controle**, não falha de rota.
* Correção: a checagem "é ovo?" passou a vir **antes** de declarar falta de rota, e o
  travamento passou a ser tratado como cutscene — roda-se **frames livres** com pulso
  de `A` (a cena encadeia mensagens e o prompt de apelido, que sem toque de `A` ficam
  parados). Resultado: `HATCH_CUTSCENE_SUSPECT steps=30972` → `HATCH_OCCURRED`.

### Sobre o shim próprio (hipótese antiga, agora medida)

A dúvida registrada antes ("o estado do core libretro carrega no shim?") foi
**resolvida por medição**, e a premissa estava errada por um detalhe:

* `gs_state_size()` = **397.312 B** = `0x61000`, o tamanho exato de
  `GBASerializedState` no mGBA 0.10.5. **Não é truncamento** — é o layout que o
  mGBA define. Os 528.448 B do libretro são um *buffer* maior, não outro formato.
* A sonda `v42/scripts/probe_shim_rom.py` abre a ROM V42 no shim: `gs_load` em
  **0,018 s**, 60 frames em **0,091 s**, game code `BPRE` lido do barramento,
  `gs_read16` a **0,6 µs/leitura**.
* Consequência honesta: o shim **funciona**, mas **não era necessário** para a
  eclosão — a suíte libretro fecha o serviço em ~15 min. O shim continua valendo como
  ferramenta de instrumentação (leitura de memória sem serializar).

## Resultado final da eclosão (5ª rodada, a que fecha)

```
HATCH_EGG_PICKED steps_to_egg=768
HATCH_OCCURRED steps=30972 (cutscene concluída com frames livres)
HATCH_POS_SAVE ok flag_0x266=1 (segundo ovo na creche: esperado)
HATCH_OK {'species': 789, 'level': 5, 'iv': [26,13,2,30,14,17], 'hp': 20}
Ran 1 test in 924.590s
OK
```

**Eclosão: CERTIFICADA.** O ovo de espécie 789 gerado pela creche da V42 eclode em
**30.972 passos reais**, por caminhada de verdade, **sem editar contador de passos,
sem tocar nos dados do ovo e sem atalho nativo**. O Cosmog resultante:

| Fato | Evidência |
|---|---|
| espécie 789 | `mon_facts` no slot 1 |
| nível 5 | idem |
| deixou de ser ovo | bit 30 do IV32 desligado |
| filho ≠ pai | PID do filho difere do Cosmog da creche |
| sobrevive a SAVE/Continuar | comparação de `mon_facts` após reload |

Bateria oficial completa (`v42/scripts/run_cosmog_tests.sh`), log
`logs/cosmog_20261107_221742.log`: **estruturais PASSOU, nativos PASSOU (4/4 em
255 s), eclosão PASSOU, shim PASSOU — 0 falhas.**

### Quatro erros do próprio teste, encontrados e corrigidos (registro honesto)

1. **"Sem rota de caminhada" mascarava a eclosão.** A checagem de rota vinha antes
   da checagem de ovo, então a cutscene (que congela o andar) era lida como falha.
2. **A cutscene não se resolve com passos.** Ela é dirigida por frames e encadeia
   mensagens + prompt de apelido, que só avançam com `A`.
3. **Exigir `flag 0x266 == 0` depois do save** era errado: os dois pais ficam na
   creche durante 31 mil passos, então o jogo **legitimamente gerou um segundo ovo**.
4. **Comparar os 100 bytes crus do mon** após reload em vez dos fatos decodificados.

Nenhum desses erros produziu falso positivo: o critério de eclosão (bit 30 do IV32)
nunca foi afrouxado, e o teste só passou quando o bit realmente caiu.

## Estado honesto (depois desta rodada)

* Eclosão: **CERTIFICADA** (acima).
* Posse simultânea de Solgaleo e Lunala no mesmo save: **NÃO TESTADA** — agora
  desbloqueada, já que o ramo por reprodução tem eclosão comprovada.
* Campanha completa desde o início: **NÃO TESTADA** — chegadas e pais são sintéticos.
* Retirada do pai pela interface: **NÃO TESTADA** (o depósito pela interface está
  provado; a *retirada*, não).
* Motor Gen 1–9 ainda **não** está neste branch: vem do PR #9 (`345efac`), extraído
  em tempo de execução por `v42/scripts/run_cosmog_tests.sh`.
* O `345efac` **não existe em todo clone**: é preciso
  `git fetch origin arena/8b7d7c0a-projeto-estudo-de-re --depth=1` antes de rodar,
  senão o script falha na extração (aconteceu nesta sessão).
