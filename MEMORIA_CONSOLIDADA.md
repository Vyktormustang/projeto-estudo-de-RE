# MEMÓRIA CONSOLIDADA — gba-re (atualizada em 2026-10-21)

> Estado canônico para a próxima sessão. Trabalhar apenas em cópias locais da ROM;
> nunca incluir ROM/save em Git nem redistribuir conteúdo protegido. Separar fatos,
> hipóteses e resultados de emulação. Mod comprovado no mGBA, não em hardware real.

## Missão e resultado atual

**Tarefa ativa:** seletor visual de itens a partir da opção `ITENS` no fluxo do
menu nativo de pausa, não o atalho sem interface START+SELECT. O builder é
`scripts/build_any_item_selector.py`; build atual
`rom_mod/ANY_ITEM_SELECTOR_v1.gba`, SHA-256
`49020b9ee08307ef4a396919b28bca879719995eb2e5ad8e62894d36412f72a6`. A janela
padrão fica no painel direito, no lugar visual do menu; B retorna ao menu de pausa.
Após a reclamação de linhas inferiores cortadas ao rolar, `maxShowed` foi reduzido de
7 para 6; a rolagem de teste exibe seis linhas completas. Build corrigido enviado ao
Drive como `Pokemon - Fire Red (BR) - Seletor de Itens v1.1.gba`. No mGBA 0.10.5
passaram A/DOWN/B, rolagem, +2 Master Balls (bolsa nativa mostrou
x3, com 1 preexistente), +99 (x100), e o fluxo BICICLETA com quantidade única 1.
A suíte geral passou 9/9. Falta provocar intencionalmente falha por bolso cheio e
validar fora do mGBA.

O mod v3 START+SELECT continua como artefato histórico separado; não o usar como
tarefa ativa nem sobrescrever seus builds.

## Correções importantes deste ciclo

1. **BL Thumb-1:** faixa real `−0x400000 .. +0x3FFFFE` bytes, alinhado a 2.
   `scripts/gba_disasm.py::encode_bl_thumb` agora rejeita endereços desalinhados e
   fora de alcance; decode manual usa o mesmo formato. `gba_hook_code.py` valida
   por esse encoder. Self-tests cobrem limites, erros e 256 offsets vs. Capstone.
2. **Veneer em `0x08000A38`:** bytes corretos `00 4b 18 47 01 0c eb 08`.
   O `ldr r3,[pc,#0]` lê o word imediatamente em `site+4`. A versão antiga usava
   `#4`, carregando bytes de código em vez do literal.
3. **Retorno do trampoline:** após repetir os 8 bytes originais, voltar a
   `0x08000A41` (`site+8 | Thumb`). `0x08000A43` pulava a primeira instrução válida.
4. **Endereço da mochila:** `0x020258B8`. O payload deve construir `0x02020000`
   com `0x20 << 12`; a versão antiga usava `<< 16` e escrevia em `0x022058B8`.
5. **Gate:** START+SELECT (`0x000C`). A montagem usa `ands` e `cmp` contra 0x000C.
   L+R+START (`0x0308`) também disparava, mas abria a ajuda nativa; foi substituído.

O montador `scripts/apply_mod_v3.py` agora valida o veneer, o gate, o endereço da
mochila e o endereço de retorno antes de aplicar o patch. Default de ROM:
`rom/Pokemon - Fire Red (BR).gba`.

## Evidências reproduzíveis

- ROM: 16 MiB, SHA-256
  `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- Save local: 128 KiB, SHA-256
  `1817043a4d410fc18ef7724d46b98950cfcf4a6000d1655efd93f8d2cfce7567`.
  `--save-file` carrega SAVE_RAM em memória; o arquivo fonte não é sobrescrito.
- Dump no instante do trigger em `0x020258B8`:
  `01 00 63 00 02 00 63 00 04 00 63 00 0d 00 63 00 1c 00 32 00 2d 00 1e 00 32 00 1e 00 13 00 63 00`.
- Screenshot: `reports/v3_bag_startselect.png`. Depois do trigger, 3.600 frames
  sem input preservaram o conteúdo no state e a execução permaneceu estável.
- Testes atuais: `bash scripts/run_all_tests.sh` → **9/9 passam**.
- mGBA 0.10.5 foi reconstruído para GLIBC 2.36; a libc do sistema não foi
  atualizada. Build/checksum: `emu/BUILD_INFO.md`.

## Como continuar

```bash
bash scripts/run_all_tests.sh
.venv/bin/python scripts/build_any_item_selector.py \
  --base 'rom/Pokemon - Fire Red (BR).gba' \
  --out rom_mod/ANY_ITEM_SELECTOR_v1.gba
```

Teste dinâmico de seletor: restaurar `/tmp/fieldboot.bin` com mGBA, START, seis
DOWN, A em `ITENS`; testar A/DOWN/B e observar a janela alinhada à direita.
`AddBagItem` é o caminho usado para respeitar bolso/capacidade; a lista de
quantidade para empilháveis é 1–99. Itens únicos/chave usam 1 com base em
`ItemId_GetImportance` ou bolso-chave (inclui HMs importantes). Prova visual
mais recente: `/tmp/final_native_balls_x100.png` (adicionou 99 Master Balls a 1
preexistente, total 100) e `/tmp/native_balls_after_add2_right.png` (x3 após +2).
Capturas temporárias ficam em `/tmp` e não são artefatos de repositório.

O mod v3 é reproduzível separadamente com `python3 scripts/apply_mod_v3.py`.
O save original do Drive deve permanecer intocado. Não afirmar validação em hardware
real antes de teste independente.

## Trilha de compreensão do código — estado em 2026-10-21

A ROM-base `google_drive/Pokemon - Fire Red (BR).gba` teve SHA-256
`6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`, igual ao
`inventory.json`.

**Ciclo 01 fechado estaticamente:** `0x080003A4` → loop `0x0800041A–0x080004AA`
→ serviço condicional de frame `0x080004B0` → dispatcher global de callbacks
`0x08000510` → callback2 `0x08078B9C` (registrado em `0x08078AEE–0x08078AF0`)
→ executor de tasks `0x08077578` → callbacks das tasks via `BX R1` em
`0x081E3BAC`. O array de tasks começa em `0x03005090`, tem stride `0x28`; a
iteração segue o link em `+6` até `0xFF`. O helper `0x081E3BA8` é `BX R0` e
executa os callbacks globais.

Separação importante: `0x0807194C`, chamado diretamente pelo loop, lê o estado
`0x03000FC4` e despacha oito casos pela tabela `0x0807196C`; não é o executor de
tasks. `0x0805486C` atualiza contadores de tempo. Não inferir os nomes funcionais
exatos das outras rotinas de `0x08078B9C` sem novas evidências.

Relatórios reproduzíveis: `reports/ciclo_01_loop_principal_e_tasks.md`,
`reports/ciclo_02_menu_pausa_e_listmenu.md` e
`reports/ciclo_03_menu_pausa_ate_bolsa.md`. O handler de pausa em `0x0806F280`
não chama `ListMenu_ProcessInput`; um fluxo ListMenu separado foi achado em
`0x08046AB8` (3 itens, IDs 0/1/5), sem elo provado com a pausa.

**Ciclo 03 fechou estaticamente um caminho do menu até a Bolsa:** `0x0806F188`
cria a task de desenho e registra o follow-up; `0x0806F168` a troca para
`0x0806F1F0`; essa task chama o callback em `0x020370F0` por `0x081E3BA8`.
A escolha do item ID 2 obtém `0x0806F481` da entrada `0x083A7354`; o callback
espera o fade, instala `0x08126EB0` com `SetMainCallback2` e retorna 1 para
encerrar a task. Nomes convencionais foram cruzados com o fonte upstream
`pret/pokefirered/src/start_menu.c` (blob `88cc377c…`); instruções e ponteiros
foram conferidos na ROM-base. Não houve PC trace dinâmico novo.

**Ciclo 04 fechado: input da Bolsa → retorno por B ao menu de pausa.**
`0x08126EB0` prepara a chamada local a `0x0811EA44`, passando o callback de task
Thumb `0x0811FB29` e o callback de retorno Thumb `0x080568A9`; a inicialização
registra `0x0811EBD1` como callback2 e cria uma task com o handler recebido. A
rotina local `0x0811FB28` corresponde funcionalmente ao handler de input da
Bolsa (nome upstream: `Task_BagMenu_HandleInput`). Seu helper `0x0811FEFC`
normaliza B para o código 2; o branch em `0x0811FB28` leva a `0x0811FD88`, que
para a localização de campo prepara a saída e troca a função da task via
`0x0811FA78` para `0x0811FAB5`. Depois do fade, instala o callback de retorno
`0x080568A9`, limpa recursos e destrói a task.

`0x080568A8` chama `0x080567DC`, após gravar `0x0807E3BD` em `0x03005024`.
`0x0807E3BC` chama `0x0806F1D4`, que zera o estado de desenho e grava
`0x0806F1B9` em `0x03005024`. Esse callback desenha a pausa via `0x0806F01C`,
inicia fade-in por `0x0807E3A0`; a task de espera `0x0807E378`, ao final,
cria a task de input `0x0806F281` com prioridade `0x50`. Nomes de funções são
cruzamentos com os blobs upstream anotados em
`reports/ciclo_04_bolsa_e_retorno_ao_menu_de_pausa.md`; todos os ponteiros,
branches e chamadas acima foram confirmados no disassembly local da ROM.

**Validação dinâmica:** no driver libretro do repositório com mGBA 0.10.5,
restaurei `google_drive/viridian_masterball.state`, abri pausa com START, abri
Bolsa com DOWN+A e pressionei B. O frame final mostra a pausa reaberta.
Capturas: `reports/ciclo_04_bolsa_aberta.png` e
`reports/ciclo_04_b_bolsa_retorno_pause.png`. Isso é validação visual, não PC
trace; o driver não implementa breakpoint/trace e não houve teste em hardware
real.

Relatórios da trilha até agora: ciclos 01–04 em `reports/ciclo_01_...md` a
`reports/ciclo_04_...md`. A análise da rota pedida está fechada; PC trace e
hardware real permanecem fora da validação atual.
