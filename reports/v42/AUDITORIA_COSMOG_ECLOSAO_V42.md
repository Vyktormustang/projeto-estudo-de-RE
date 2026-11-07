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

## Caminho que fecha isso

1. **Shim próprio.** `tools/gba_shim` lê memória pelo barramento (`gs_read16`) sem
   serializar; só o *restore* seria caro, não a leitura por passo. Falta provar que
   o estado do core libretro carrega no shim (os tamanhos já diferem: 528.448 B do
   libretro contra 397.312 B do shim).
2. **Patch de instrumentação**: desviar o decremento de ciclos (só contador, sem
   escrever o ovo) para *medir* quanto falta e então validar a eclosão real com
   orçamento conhecido. Não substitui a eclosão real.
3. **Um único bloco longo**: ~20 h de máquina. Viável fora desta sessão.

## Ambiente desta sessão (transparência)

A sessão foi reiniciada no meio do trabalho (novo branch, `arena/b956a89e`). O reset
apagou três coisas que **não são versionadas por design**:

* a **ROM V42** (`google_drive/`) e os **save-states** (`emu/*.bin`) — sem eles, a
  suíte nativa **não roda** aqui; `v42/scripts/run_cosmog_tests.sh` sai com código 2
  e mensagem "ROM ausente", em vez de falhar em falso;
* o `tools/gba_shim/build/` (shim e fonte do mGBA) — **reconstruído nesta sessão**:
  `make -C tools/gba_shim libmgba` + `shim`, e o core libretro pelo script daqui;
* as dependências Python `capstone`, `keystone-engine` e `unicorn` — reinstaladas em
  `.venv` local (`pip install` no sistema é bloqueado por PEP 668).

Com tudo reconstruído, a bateria principal do repositório voltou a **0 de 17 falhas**
(log `logs/tests_20261107_192734.log`); sem as dependências, eram 12 falhas — nenhuma
delas era regressão de código.

**Consequência:** os números de 202 s e 4/4 acima foram medidos na sessão anterior,
com a ROM presente, e estão nos logs citados. Nesta sessão a suíte nativa não pôde
ser reexecutada — o que **não** invalida os resultados, mas também não os reconfirma.

## Estado honesto

* Eclosão: **NÃO CERTIFICADA**. Nenhum claim de que o ovo eclode.
* Posse simultânea de Solgaleo e Lunala no mesmo save: **NÃO TESTADA** (depende da
  eclosão para o ramo por reprodução).
* Campanha completa desde o início: **NÃO TESTADA** — chegadas e pais são sintéticos.
* Retirada do pai pela interface: **NÃO TESTADA**.

O que mudou de fato nesta rodada: a suíte nativa do Cosmog **saiu de "nunca
executada" para 4/4 verde**, e a eclosão deixou de ser "não tentada" para "tentada,
medida e bloqueada por custo de harness" — com o número que falta.
