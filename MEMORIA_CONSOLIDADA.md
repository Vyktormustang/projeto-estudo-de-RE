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

Relatório reproduzível: `reports/ciclo_01_loop_principal_e_tasks.md`. Evidência
deste ciclo é disassembly estático da ROM com o hash acima; não houve PC trace
dinâmico novo. **Próxima ação:** ligar a criação do `ListMenu` do menu de pausa
à task/callback que lê a navegação e escolhe a ação da tabela já referenciada em
`0x083A7344`, sem alargar a análise a código não necessário.
