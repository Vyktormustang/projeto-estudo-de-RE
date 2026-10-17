# Notas de trabalho (operacional)

Caderno curto: só o que preciso para retomar rápido. Explicação completa vai
para `RELATORIO_o_que_ja_sabemos.md` e `README.md` **no fim** do trabalho.

## Rodar

```bash
P=/home/user/projeto-estudo-de-RE/.venv/bin/python
$P -m pytest tests/ -q                       # 90 testes
$P ferramentas/aplicar_patch_pokebolas.py ROM.gba -o NOVA.gba --json r.json
$P ferramentas/aplicar_manifesto.py ROM.gba patches/exemplo_dados.json -o NOVA.gba
$P ferramentas/aplicar_manifesto.py ROM.gba patches/exemplo_texto.json -o NOVA.gba
```

ROM de trabalho (fora do repo, fora do git):
`/home/user/gba-re/rom/pokemon_firered_bpre_trabalho.gba`
sha256 `6035a98f…`, 16 777 216 B, `POKEMON FIRE` / `BPRE`.
Ela **pode sumir** com o ambiente: rebaixar do Drive (`14JCEJp6LFgdkzKMOtI5-l3XvowJ1SxnC`).

## Endereços confirmados (medidos)

| o quê | onde |
|---|---|
| `gSaveBlock1Ptr` / `gSaveBlock2Ptr` | `0x03005008` / `0x0300500C` |
| `encryptionKey` | `[0x0300500C]+0xF20` |
| `gBagPockets` (5 × `{ptr, cap}` de 8 B) | `0x0203988C` |
| pockets em SaveBlock1 | `+0x310` 42 · `+0x3B8` 30 · **`+0x430` 13 bolas** · `+0x464` 58 · `+0x54C` 43 |
| `GetBagItemQuantity` / `SetBagItemQuantity` | `0x08099DA0` / `0x08099DBC` |
| `GetPcItemQuantity` / `SetPcItemQuantity` | `0x08099DD8` / `0x08099DDC` (PC **não** cifra) |
| `ItemId_GetPocket` / `ItemId_GetPrice` | `0x0809A9D8` / `0x0809A900` |
| `AddBagItem` / `RemoveBagItem` | `0x0809A084` / `0x0809A1D8` |
| `ClearItemSlots` / `ResetBag` | `0x0809A274` / `0x0809A2DC` |
| `AddPCItem` (`pcItems` @`0x298`) | `0x0809A3C8` — **não é bag** |
| `gItems` (passo 0x2C) | `0x083DB028` |
| `NewGameInitData` | `0x08054A60` |
| `bl ResetBag` dentro dela (hook do patch) | `0x08054B06` |
| literal do dinheiro inicial (3000) | `0x08054B60` (lido por `0x08054AD4`) |
| espaço livre grande | `0x088001C7` 5 242 425 B · `0x08EB0B20` 1 373 408 B · `0x0871A905` 939 771 B |

## Armadilhas (cada uma já custou tempo)

- **`0x298` é `pcItems`, não bag.** `0x0809A3C8` é `AddPCItem`; `0x08099DD8/DC`
  são as versões de PC, sem cifra.
- **Desmontar em endereço errado produz lixo convincente.** `0x08099D70..9F` é
  dado; a função começa em `0x08099DA0`. Antes de concluir que "não faz sentido",
  conferir o prólogo (`push` com `lr`).
- **`0x0804C058` é boot, antes do save.** Escrita ali é sobrescrita.
  `ResetBag` zera as 5 pockets → escrever **depois** dele.
- **`0x08111374` parece chamar `ResetBag`, mas é dado.** O chamador real é só
  `0x08054B06`.
- **`bl` é relativo**: montar para o endereço de destino, nunca para `0`.
- **`achar_espaco_livre` com mínimo pequeno pega padding** (81 B em `0x081BA4E6`).
  Mínimo 4 KiB.
- **`esperado` lido da própria imagem é tautológico**: a 2ª aplicação passa.
  Usar constante (`bl ResetBag` montado).
- **Pool de literais é compartilhado?** Conferir todos os `ldr [pc]` da função
  antes de editar o valor. No dinheiro inicial, só `0x08054AD4` usa `0x08054B60`.
- **Soma de offset do `gItems`**: `base + id*0x2C + campo`. `4*0x2C = 0xB0`;
  `+0x10` = `0xE8`, não `0xD8`. A guarda do patch pegou.
- **`complemento` = soma `0xA0..0xBC`**, não `0x00..0xBC`.
- **`/tmp` e `.venv` não persistem**; o git sim.

## Três tipos de patch, três verificações

| patch | arquivo | verificação | provado? |
|---|---|---|---|
| lógica (99 Poké Bolas no jogo novo) | `ferramentas/aplicar_patch_pokebolas.py` | emulação do stub + `GetBagItemQuantity` + `ItemId_GetPocket` | sim, no emulador |
| dado (preço 200→1, dinheiro 3000→999999) | `patches/exemplo_dados.json` | `ItemId_GetPrice` do jogo | sim, no emulador |
| texto (POKé BOLA→BOLA NOVA) | `patches/exemplo_texto.json` | decodificação com o charset da §9.5 | **não por emulação** |

- **Não provado**: que o boot real chegue com `gBagPockets` apontado; que a tela
  exiba; **nada foi jogado** (sem emulador de console no ambiente).
- `CopyItemName` **não foi localizado** (os candidatos `0x0809A7B0`/`0x0809A7D8`
  são outros acessores de pocket) — por isso o texto é verificado por
  decodificação.
- **Dígitos não estão na tabela medida**: `texto.codificar("TM01")` é recusado.
  Medir antes de patch de nome com número.

## Próximos passos

1. Medir os dígitos do charset (`0xA1`..`0xAA`?) e o `CopyItemName`.
2. Um patch de **constante de comportamento** que não seja só dado: ex. limite de
   itens por pocket (o `999`/`0x3E7` em `0x0809A0D8`).
3. Fim do trabalho: consolidar tudo em `RELATORIO` (§11 cresce) e `README`;
   aí sim atualizar o corpo do PR com o resumo.
