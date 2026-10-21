# Ciclo 17 — Camada de acesso a dados de Pokémon: BoxMon e registro de equipe

**Estado:** análise estática local concluída para os despachantes e a fronteira entre dados persistentes e campos da equipe. Sem validação dinâmica.

## Pergunta e escolha do recorte

Depois dos ciclos concentrados em mapas/scripts, este ciclo inicia um domínio de dados/estado do jogo. O inventário local aponta a camada Pokémon como bom ponto de entrada: o índice de callsites registra 1.363 chamadas BL para `0x0803FBE8` e 728 para `0x0804037C`. Isso mede referências estáticas no índice, não chamadas executadas. O callgraph só de BL não representa os saltos por tabela usados pelos despachantes.

`names_registry.json` e H-0014/H-0015 já sugeriam que esses endereços seriam accessors GET/SET. Usei-os como pistas e conferi os bytes da ROM local nesta etapa; os nomes e a semântica em C abaixo vêm de cruzamento separado com upstream.

## Identidade, ferramentas e limites

- ROM analisada, somente leitura: `google_drive/Pokemon - Fire Red (BR).gba`
- Tamanho: `16.777.216` bytes (16 MiB)
- SHA-256: `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`
- Mapeamento ROM usado: `VA GBA = offset no arquivo + 0x08000000`.
- Análise local: Capstone 5.0.7, modo Thumb, sondagem de tabelas com `scripts/gba_table_probe.py` e asserts Python diretamente sobre os bytes. Capstone foi instalado temporariamente em `/tmp/capstone-py`.
- Ghidra e CLI REA não estavam instalados/disponíveis nesta sessão; não são atribuídos achados a essas ferramentas. Por ser código nativo, uma importação controlada da região Thumb no Ghidra e comparação de decompilação permanece como validação pendente.
- Não foi executado emulador/debugger, não foi lido nem alterado o save, e nenhum comportamento dinâmico é afirmado.

## Evidência da ROM local

### 1. Dois níveis de dispatch: campos de equipe e campos BoxMon

`0x0803FBE8` recebe o registro em `r0` e o ID do campo em `r1`. O fluxo local calcula `r1 - 0x37`, aceita o intervalo `0..0x21` e indexa uma tabela de 34 ponteiros em `0x0803FC08`, finalizando com `mov pc, r0`. Em termos numéricos, os casos especiais da equipe cobrem IDs `55..88` (`0x37..0x58`). Fora desse intervalo, o ramo comum chama `0x0803FD44` com o ID original: os demais campos são tratados pela camada BoxMon.

O setter espelho começa em `0x0804037C`: mesma normalização `r1 - 0x37`, mesmo intervalo de 34 casos e tabela em `0x0804039C`. Fora da faixa, encaminha ao helper `0x080404D0`.

As duas tabelas foram lidas da ROM e validadas: todos os ponteiros caem dentro da imagem. O GET compartilha o handler de `0x0803FD36` para os casos de equipe que encaminham ao BoxMon. No SET, o índice 10 (campo 65) aponta ao retorno sem escrita em `0x080404C8`; índices 11–28 encaminham ao setter BoxMon em `0x080404C0`.

| ID(s) do campo | Evidência local no dispatch de equipe | Interpretação do nome (cruzamento upstream) |
|---|---|---|
| 55 (`0x37`) | GET lê palavra em `+0x50`; SET lê 4 bytes de entrada e grava nesse campo | status |
| 56 (`0x38`) | GET lê byte `+0x54`; SET grava byte | nível |
| 57–58 (`0x39–0x3A`) | GET lê halfwords `+0x56`, `+0x58`; SET grava halfwords | HP atual, HP máximo |
| 59–63 (`0x3B–0x3F`) | GET chama `0x08044674` com seletores 1–5; se resultado for zero, segue para os halfwords `+0x5A..+0x62`. SET grava nesses cinco halfwords | atributos de ataque/defesa/velocidade/ataques especiais; `0x08044674` corresponde a `GetDeoxysStat` na fonte comparada |
| 64 (`0x40`) | GET lê byte `+0x55`; SET grava byte | mail/anexo de equipe |
| 65 (`0x41`) | GET encaminha ao BoxMon; SET não escreve | species-or-egg no enum upstream; setter é deliberadamente no-op neste caminho |
| 66–83 (`0x42–0x53`) | GET encaminha ao BoxMon; SET encaminha, mas o helper tem tabela só até 80. Caso 66 aponta ao epílogo comum sem gravação; 81–83 ficam fora da tabela | 66 é IVS agregado, 67–80 ribbons individuais e 81–83 campos derivados no enum upstream |
| 84–88 (`0x54–0x58`) | GET lê e SET grava os mesmos halfwords `+0x5A,+0x5C,+0x5E,+0x60,+0x62`, sem passar pelo helper especial do GET 59–63 | campos alternativos de stats no enum upstream |

A sequência de offsets locais estabelece uma extensão de equipe a partir de `+0x50`: 4 bytes, 1 byte, 1 byte, depois halfwords em `+0x56..+0x62`. O tamanho `0x64` e os nomes dos campos são uma identificação semântica corroborada pela estrutura upstream, não símbolos presentes na ROM.

### 2. BoxMon: campos simples, bloco cifrado e checksum

O helper local GET `0x0803FD44` aceita IDs `0..0x53` (84 entradas; tabela em `0x0803FDD8`). IDs maiores que 10 passam primeiro por uma preparação: resolve os quatro subblocos (`0x0803F940`, seletores 0–3), decifra (`0x0803F91C`), calcula checksum (`0x0803E3E8`) e compara com o halfword em `[registro+0x1C]`. Em mismatch, o GET marca bits `0x05` em `[registro+0x13]` e `0x40` no byte `+7` do subbloco 3, mas segue ao caso solicitado; ao sair, IDs maiores que 10 passam pelo caminho de recifra `0x0803F8F8`.

A rotina de XOR percorre 12 palavras de 32 bits a partir de `+0x20` e aplica, em duas operações, o XOR com os valores de `[registro+0x04]` e `[registro+0x00]`. Isso equivale à chave `OT ID XOR personalidade` sobre 48 bytes. A rotina de checksum resolve quatro subblocos e soma seis halfwords de cada, reduzindo o acumulador para 16 bits: 24 halfwords no total.

O setter local `0x080404D0` usa tabela em `0x08040564` com 81 entradas (`0..0x50`). Para IDs acima de 10, decifra e confere checksum. Em incompatibilidade, define bits no byte `+0x13` e no subbloco 3 (`+7`), recifra e retorna sem aplicar a alteração solicitada. No caminho válido para `field>10`, grava o dado do caso, recalcula o checksum em `+0x1C` e recifra; campos `0..10` seguem os handlers simples sem esse ciclo. IDs fora de `0..0x50` não entram na tabela de escrita.

A tabela de GET contém 84 casos, mas a de SET apenas 81. O limite superior distinto é observável localmente. A explicação de que os três últimos campos de GET são derivados/read-only vem do enum e dos `switch` upstream, não é inferida apenas do tamanho das tabelas.

### 3. Offsets BoxMon observáveis e estrutura proposta

Os handlers locais de GET acessam diretamente personalidade em `+0x00`, OT ID em `+0x04`, flags em `+0x13`, idioma em `+0x12`, OT name a partir de `+0x14`, markings em `+0x1B`, checksum em `+0x1C` e o separador em `+0x1E`. O bloco cifrado começa em `+0x20`. Os flags e offsets de checksum/secure data também são usados no prólogo dos helpers.

Cruzando os campos e larguras com `struct BoxPokemon` upstream, a disposição proposta é:

| Offset | Largura/conteúdo | Fronteira de evidência |
|---:|---|---|
| `+0x00` | personalidade, u32 | leitura direta local; rótulo upstream |
| `+0x04` | OT ID, u32 | leitura direta local; rótulo upstream |
| `+0x08..+0x11` | nickname, 10 bytes | intervalo/semântica confirmados pela estrutura upstream; handler local copia a saída e consulta flags |
| `+0x12` | idioma, u8 | leitura direta local |
| `+0x13` | flags de sanidade/ovo, u8 | leitura e escrita direta local; nomes dos bits cruzados upstream |
| `+0x14..+0x1A` | nome do OT, 7 bytes | cópia local a partir de `+0x14`; largura/nome confirmados upstream |
| `+0x1B` | markings, u8 | leitura direta local |
| `+0x1C` | checksum, u16 | leitura/comparação/escrita local |
| `+0x1E` | word separador/desconhecida, u16 | leitura local; nome semântico “unknown” só no upstream |
| `+0x20..+0x4F` | 48 bytes cifrados | base e tamanho derivados localmente do loop de 12 palavras; quatro subblocos de 12 bytes cruzados upstream |

O helper de seleção local faz chamada com divisor constante `0x18` e usa dispatch de 24 destinos a partir de `0x0803F964`; upstream identifica a seleção como `personalidade % 24` e dá os 24 arranjos. A existência e extensão da seleção são locais; a tabela nominal completa de permutações ainda não foi transcrita neste ciclo.

## Cruzamento semântico upstream — separado da prova local

Foi comparado com `pret/pokefirered` no commit `ce6406d8c2eaf46d543c8a2606de0c3cb1951982` (snapshot obtido via codeload). SHA-256 dos arquivos usados:

- `include/pokemon.h`: `a6881fee07ae10f57ebf3ec7af1cabd2e900d8ba8d3da644313c087d16e1617e`
- `include/constants/pokemon.h`: `9cabd203100ae7246bc595b7295e7e04145f6292abfab83c3bd0597a2cfbcfb5`
- `src/pokemon.c`: `116a470cd9ebfa226aa8d85c2eb63591e176d726837c67baaa1ac6260d50f2ec`

O cruzamento associa `0x0803FBE8`/`0x0804037C` a `GetMonData`/`SetMonData`, e `0x0803FD44`/`0x080404D0` a `GetBoxMonData`/`SetBoxMonData`. O enum upstream atribui os campos da equipe a partir de 55 e nomeia os campos BoxMon de 0 a 83. `include/pokemon.h` define `BoxPokemon` com 0x50 bytes e `Pokemon` com extensão até 0x64; seus tamanhos/offsets coincidem com os acessos observados na ROM local. `src/pokemon.c` também identifica o helper especial de stats como `GetDeoxysStat` e descreve os quatro subblocos permutáveis.

Isso é um cruzamento semântico com uma árvore upstream mutável, fixada aqui pelo commit e hashes acima; não prova que a ROM brasileira foi compilada dessa árvore, nem substitui a evidência local descrita antes.

## Reprodutibilidade e verificações

- Hash/tamanho local confirmados antes da leitura.
- `PYTHONPATH=/tmp/capstone-py python3 scripts/gba_table_probe.py 'google_drive/Pokemon - Fire Red (BR).gba' --table 0x0803FC08 --n 34 --insns 5` — os casos demonstram leituras em offsets `+0x50`, `+0x54`, `+0x56`, `+0x58` e encaminhamentos.
- Inspeção equivalente das tabelas `0x0804039C` (34), `0x0803FDD8` (84) e `0x08040564` (81), além dos prólogos, handlers e saídas comuns dos quatro helpers.
- Asserts sobre ROM local passaram: hash esperado; dispatch GET/SET de 34 posições; mapeamento de casos diretos e encaminhados; tabelas BoxMon de 84/81 entradas; ponteiros dentro da ROM; limites numéricos `0x37..0x58`, `0x53` e `0x50`; offsets e caminhos críticos de XOR/checksum.
- Índice local de callsites: `reports/pokemon_firered_bpre_trabalho_callsites.tsv`, SHA-256 `fc298f65c6aa7e950205400c997d2498cddb42bc10d140af3a527d87a535b4d7`; contagem: 1.363 alvos BL `0x0803FBE8`, 728 alvos BL `0x0804037C`. É índice estático existente, não número de execuções.
- Callgraph local continua com a limitação declarada de capturar apenas BL direto; a transferência via `mov pc, r0` faz parecer menos conectados os caminhos mediados por tabelas.

## Questões abertas e próximo recorte

1. Ainda não foi identificado na ROM local um caller representativo até o fim (menu de equipe, PC/caixas, batalha, Pokédex ou evolução); o grande conjunto de callsites precisa ser clusterizado e seguido por caminhos curtos.
2. Não foi localizado nesta etapa o conjunto de dados de espécies/moves nem seguido o carregador que os liga ao accessor; é preciso localizar tabelas e conferir registros em bytes locais.
3. Faltam análise individual dos casos BoxMon, incluindo as 24 permutações e campos derivados, e comparação mais ampla das rotas de leitura/escrita.
4. Persistência em save, transferência entre party e PC, recalculação de stats e estado real de execução ainda não foram rastreados.
5. Sem Ghidra/REA e sem emulação nesta sessão; nenhuma conclusão dinâmica ou de alcançabilidade em runtime.

O ciclo 17 confirma uma camada estrutural de acesso/serialização de dados de Pokémon; não encerra os subsistemas de equipe, PC, batalha nem o roteiro geral da ROM. Próximo: seguir um conjunto mínimo de callsites locais até um consumidor de equipe/armazenamento e localizar o catálogo local de espécies, mantendo desconhecidos explícitos.
