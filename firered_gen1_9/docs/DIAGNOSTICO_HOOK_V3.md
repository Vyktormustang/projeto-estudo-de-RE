# Diagnóstico do hook histórico BAG_MOD_v3

Este relatório trata da ROM FireRed BR histórica (SHA-256
`6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`), **não**
da variante mais recente Gen 1–9. Não aplique estes offsets a outra ROM. O
arquivo `BAG_MOD_v3.gba` descrito no README/HANDOFF antigos não é uma solução
validada; o boot ou um state aparentemente estável não demonstram que o hook
funcionou.

## Bytes confirmados

O aplicador e os dois arquivos hexadecimais dentro de `gba-re_project (1).zip`
reproduzem o v3 histórico, SHA-256
`348025c13828517f3a4ae03cd9fe963df07fcb12ed087933b0d319d4892215a3`.
Desmontagem Capstone dos bytes reais em `0x08000A38`:

```text
08000a38  01 4b      ldr r3, [pc, #4]
08000a3a  18 47      bx  r3
08000a3c  01 0c eb 08     .word 0x08eb0c01  ; pretendido
08000a40  09 0c 5f 2c     .word 0x2c5f0c09  ; efetivamente lido
```

Em Thumb, `Align(0x08000A38 + 4, 4) + 4` é `0x08000A40`. Para carregar o
literal em `0x08000A3C`, o primeiro meio-word deve ser `00 4b`, não `01 4b`.
O v3 original faz `bx` para a palavra errada, não para o trampolim.

O próprio trampolim original também constrói `0x08000A43`. O retorno após
reexecutar os oito bytes deslocados deve ser `0x08000A41`, isto é, endereço
`0x08000A40` com o bit Thumb ligado. O retorno anterior pula a instrução
`lsrs r1, r1, #16` em `0x08000A40`.

Há ainda um problema diferente: a sequência de escrita do payload v3
constrói `0x022058B8`, não o endereço documentado `0x020258B8`. Não se deve
assumir que consertar somente o veneer e o retorno faria o mod funcionar.

## Teste em mGBA 0.10.5

`scripts/diagnostico_hook_v3.py` reconstrói e confere a ROM histórica, cria
cópias descartáveis instrumentadas e executa um jogo sintético, sem ler nem
modificar saves pessoais. O contador de 32 bits em `0x0203FFFC` é **apenas um
marcador temporário de teste**, não um endereço reservado para patches em geral.
O tamanho evita que várias chamadas por frame produzam um falso zero por
transbordamento de um byte. A ROM original foi usada como controle.

- Chamada forçada ao hook com o veneer antigo: contador **0** e PC fora do
  retorno de teste; o trampolim não executou.
- Mesma chamada, com veneer e retorno corrigidos na cópia de diagnóstico:
  contador **1**, retorno ao sentinela e valor `0x1234` preservado no registro.
- Na sessão sintética, após chegar ao quarto (verificado visualmente e pelo
  mapa `grupo 4, número 1` no SaveBlock1) e zerar
  o contador: **360, 720, 1080 e 1440 chamadas** em intervalos consecutivos de
  60 frames. A ROM sem a instrumentação manteve o word em zero por 240 frames.
  Assim, naquele cenário, a função é chamada continuamente; o veneer quebrado
  é que impede a entrada no trampolim original. Isto não prova o comportamento
  em todas as telas ou em outros jogos.

O teste **não** valida o combo nem a leitura de `REG_KEYINPUT`; tampouco afirma
que o v3 ou o novo motor Gen 1–9 estejam prontos para uso. O relatório histórico
[RETOMADA.md](https://github.com/Vyktormustang/projeto-estudo-de-RE/blob/94bbd401b10757eb588c8e8095b8534ccdf9c7c5/RETOMADA.md)
registra uma investigação anterior e um v4 separado. Sua hipótese de que o
hook só rodaria na inicialização não se confirmou no quarto sintético acima;
outros contextos não foram cobertos.

## Reprodução

É necessário fornecer a própria ROM identificada acima e um core libretro mGBA
0.10.5 compatível com o sistema. Nenhum deles é incluído neste patch.

```sh
python3 scripts/diagnostico_hook_v3.py \
  --rom 'google_drive/Pokemon - Fire Red (BR).gba' \
  --core /caminho/mgba_libretro.so
```

O script verifica o hash da entrada, usa somente cópias temporárias, nunca
grava arquivos `.sav` do usuário e relata os contadores e os PCs em JSON.
