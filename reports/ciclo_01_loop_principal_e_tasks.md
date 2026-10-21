# Ciclo 01 — loop principal → callbacks de frame → tasks

**Data:** 2026-10-21

**ROM analisada:** `google_drive/Pokemon - Fire Red (BR).gba`

**Identidade:** SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`, 16 MiB. Hash conferido nesta sessão e igual ao de `inventory.json` e `reports/pokemon_firered_bpre_trabalho_ident.json`.

## Resultado

A ligação entre o loop de frames e o executor de tasks estática foi fechada. O caminho confirmado é:

```text
entry Thumb 0x080003A4
  → loop principal em 0x0800041A–0x080004AA
  → serviço de frame 0x080004B0
  → dispatcher de callbacks globais 0x08000510
  → callback2 em gMain (quando registrado): 0x08078B9C
  → executor de tasks 0x08077578
  → callback indireto de cada task (BX R1 em 0x081E3BAC)
```

O loop também chama diretamente `0x0807194C` a cada volta. Esse é um dispatcher de estado separado, indexado pelo byte `0x03000FC4`; não é o executor geral de tasks.

## Evidência reproduzível

### 1. Loop de frames

Disassembly Thumb da ROM-base:

- `0x0800041A`: chama `0x080005E8`.
- `0x0800047E`: chama `0x080004B0`.
- `0x08000482`: chama `0x08058274`.
- `0x0800049E`: chama `0x0805486C` (atualização dos contadores de tempo).
- `0x080004A2`: chama `0x0807194C`.
- `0x080004A6`: chama `0x08000890`.
- `0x080004AA`: branch de retorno para `0x0800041A`.

Há caminhos condicionais no loop, incluindo uma chamada adicional a `0x080004B0` em `0x0800044E`. `0x08000890` permanece identificado apenas como provável gate/espera de frame; este ciclo não tenta lhe atribuir um nome mais específico.

### 2. Serviço de frame e callbacks globais

`0x080004B0` chama `0x0800B178`; se o resultado for zero, chama `0x08000510`.

`0x08000510` carrega a estrutura global em `0x030030F0`, lê os ponteiros nas posições `+0` e `+4`, e, se não nulos, os despacha por `0x081E3BA8`. O corpo de `0x081E3BA8` é `BX R0`, confirmando chamada indireta do ponteiro em `R0`. Antes disso, `0x08000510` passa por dois gates (`0x080F5118` e `0x0813B870`); a função exata desses gates não foi estabelecida.

`0x08000544` grava o argumento em `[0x030030F0 + 4]` e zera o byte em `[0x030030F0 + 0x438]`; portanto, é o setter do callback nessa posição da estrutura (nome convencional provável: `SetMainCallback2`).

### 3. Registro e execução de `0x08078B9C`

Em `0x08078AEE`, uma instrução `LDR` carrega do literal em `0x08078B14` o valor `0x08078B9D`; logo depois, `0x08078AF0` chama `0x08000544`. O bit baixo do ponteiro indica Thumb; o destino de código é `0x08078B9C`. Assim, a rotina é registrada como callback no campo `+4` da estrutura global.

O corpo em `0x08078B9C` chama, nesta ordem:

1. `0x08077578`
2. `0x08006B5C`
3. `0x08006BA8`
4. `0x080704D0`

A evidência fecha a ligação do dispatcher global de callback ao primeiro executor da fila de tasks; não se inferem aqui os nomes semânticos das outras três rotinas.

### 4. Executor de tasks `0x08077578`

O corpo executa `0x080775A8` para obter o índice inicial. Se o retorno for `0x10`, termina. Caso contrário, calcula o endereço do registro como `0x03005090 + índice × 0x28`, carrega o ponteiro de callback do início do registro, chama `0x081E3BAC` e lê o próximo índice em `registro + 6`. Continua até encontrar `0xFF`.

O corpo de `0x081E3BAC` é `BX R1`; como `R1` contém o ponteiro carregado do registro, isso confirma a invocação indireta do callback da task. O layout e a iteração sustentam a identificação estrutural de `0x08077578` como executor de tasks, não apenas um candidato baseado no nome ou em notas históricas.

O array em `0x03005090`, stride `0x28`, também aparece nas rotinas de inicialização/alocação/liberação já examinadas. `0x080773BC` é a inicialização do array e `0x0807741C` é um ponto de criação/alocação usado, entre outros contextos, pela rotina em `0x08078888`.

### 5. Dispatcher de estado separado

`0x0807194C` lê `0x03000FC4`, limita o índice a `0..7` e consulta a tabela em `0x0807196C`. É chamado diretamente pelo loop em `0x080004A2`. Isso é evidência de uma máquina de estados de oito casos e não de que essa rotina percorra `gTasks` ou invoque os callbacks da tabela de tasks.

## Fatos, inferências e lacunas

**Confirmado por instruções/dados da ROM:**

- O hash da cópia analisada confere com o inventário.
- O loop principal retorna a `0x0800041A` e chama o dispatcher `0x0807194C`.
- O serviço `0x080004B0` chega condicionalmente ao dispatcher global de callbacks `0x08000510`.
- `0x08078B9C` é instalado no campo `+4` da estrutura `0x030030F0` a partir do caminho em `0x08078AEE–0x08078AF0`.
- `0x08078B9C` chama `0x08077578`, cujo corpo percorre registros do array de tasks e invoca seus callbacks indiretamente.
- `0x0807194C` e `0x08077578` têm funções distintas no fluxo observado.

**Inferência de nome, não necessária à conclusão estrutural:**

- `0x08000544` corresponde ao setter convencional de `MainCallback2`, pelo campo escrito e pelo uso observado.
- `0x08078B9C` parece ser um callback de atualização do mundo/jogo, mas o nome funcional exato não foi confirmado neste relatório.

**Ainda em aberto:**

- O significado preciso dos gates `0x080F5118` e `0x0813B870`.
- A interpretação funcional das rotinas `0x08006B5C`, `0x08006BA8` e `0x080704D0` neste caminho.
- O caminho de input da opção de pausa: criação do task do `ListMenu`, callback de processamento, leitura de A/B e seleção da ação.
- Validação dinâmica/PC trace desta cadeia completa; as conclusões acima são estáticas e reproduzíveis a partir do SHA informado.

## Próximo passo

Seguir a criação do `ListMenu` e o callback de input usado pelo menu nativo de pausa, ligando o task criado (incluindo a posição no array) à rotina de leitura/seleção e à tabela de ações já referenciada em `0x083A7344`. Usar uma pergunta estreita por vez e manter explícitas as fronteiras entre evidência estática, medições anteriores e hipóteses.
