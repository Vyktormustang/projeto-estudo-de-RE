# hypotheses.md — Hipóteses, evidências e testes pendentes

Regras: cada entrada tem ID, estado (CONFIRMADO | PROVÁVEL | HIPÓTESE | DESCONHECIDO),
evidência que sustenta, hipótese alternativa mais plausível e teste capaz de refutar.
Nada é promovido de confiança "porque parece lógico".

## Pendentes

| ID | Afirmação | Estado | Evidência | Alternativa plausível | Teste de refutação |
|----|-----------|--------|-----------|-----------------------|--------------------|
| H-0001a | ROM deriva de Pokémon FireRed (BPRE, USA) Rev 0 | CONFIRMADO | cabeçalho completo válido (título "POKEMON FIRE", game code BPRE, logo Nintendo idêntico, checksum OK, maker "01", versão 0) + tamanho 16 MiB + libs do SDK | — | — |
| H-0001b | Variante = tradução PT-BR ("(BR)") | **CONFIRMADO** (ciclo 3; reforço dinâmico ciclo 19: tela de título renderiza "POKéMON FIRE RED BR") | texto decodificado: 'você'×719, 'Você'×577, 'ção'×174, 'está'×345, 'Está'×53, 'Olá'×40, diálogos PT completos ("Você não pode pegar um POKéMON de outra pessoa", "Saudações! Este é o sistema de ajuda"…); charset Gen3 + remap de acentos PT-BR | — (refutou-se a alternativa) | — |
| H-0006 | Tradução remapeou a tabela de acentos do charset | **CONFIRMADO** (parcial) | descoberta por sondas curinga: 0x1B='é' (POKéMON, byte-3 sempre 0x1B), 0x1C='ê' (Você 556/556), 0x17='á' (está/fácil/vários), 0x19='ç' (opções/criança/Saudações), 0xF4='ã' (não/botão 17/17), 0xF5='õ' (botões 4/4), 0x68='â' (importância — confiança média) | — | sondas p/ acentos restantes (ó, í, ú, maiúsculos) |
| H-0007 | A tradução repontou/blocou dados → offsets de decomp BPRE não valem aqui | PROVÁVEL | natureza de traduções (texto expandido); hashes totalmente divergentes | tradução in-place (improvável p/ PT>EN) | medir 3 tabelas nesta ROM e comparar com BPRE conhecido |
| H-0002 | Toolchain = Nintendo AGB SDK (compilador padrão da era) | PROVÁVEL | init em 0x08000204 é o padrão canônico do SDK (mov r0,#0x12 → IRQ mode; msr CPSR; ldr sp — configuração de pilhas); strings de versão de biblioteca compiladas: FLASH1M_V103, RFU_V1024 | toolchain não-SDK com init imitado | Fase 2: assinaturas de runtime do compilador (prólogos, div/ldm), símbolos AgbMain |
| H-0003 | Código predominantemente Thumb | **CONFIRMADO** (ciclo 4) | (a) boot muda p/ Thumb após apenas 13 instr. ARM (`bx r1` p/ 0x080003A4); (b) censo capstone: 44.758 BL diretos → 7.565 alvos, 78% com prólogo canônico `push{…,lr}` (0xB5); (c) em TODAS as 384 páginas, branches decodificados como ARM atingem prólogos ARM (0xE92D) com taxa 0.0 — ou seja, não há massa de código ARM na região varrida; (d) ARM confirmado pontualmente no boot e no IRQ dispatcher (0x08000248) | — | refutou qualquer hipótese de código ARM massivo; procurar ARM residual só em ISR/ponteiros (Fase 2+) |
| H-0008 | Arquitetura de boot = padrão SDK Nintendo | **CONFIRMADO** (ciclo 4) | literais do boot medidos na ROM: SP_IRQ=0x03007FA0, SP_USR=0x03007E40; `[0x03007FFC]←0x08000248` (célula padrão de handler); desassembly de 0x08000248 = dispatcher clássico IE/IF/IME; entry principal Thumb em **0x080003A4** | — | — |
| H-0009 | "Ilhas ARM" do ciclo 2 (regex 0xEB em 0x1E0000/0x4B0000) | **REFUTADA p/ 0x4B0000** / enfraquecida p/ 0x1E0000 | censo ciclo 4: 0x4B0000 tem hit de prólogo 0,0026 → dados que imitavam ARM BL na heurística de bytes; 0x1E0000 tem código Thumb misturado a dados (hit 0,117; 453 branches) | — | — |
| H-0010 | Array de slots 0x28 B em 0x03005090 = sistema de objetos (sprites/field objects ou similar) | **HIPÓTESE — rotas de observação esgotadas nesta plataforma (ciclo 22: region0 só SAVE; SET_MEMORY_MAPS=0 descs; EWRAM inexposta no mGBA-libretro headless)** | par alocador/liberador (0x0807741C / 0x08077508) com flag ativa+4, ponteiro+0, byte de template+7, zero 0x20 B em +8, campo+5==0xFE propaga p/ filho — estrutura de pool de entidades | pool de tasks/anim/window; não dá p/ decidir por estática | Fase 4: alocar em runtime contando slots (mGBA watchpoint) OU rastrear leitores do campo+0 |
| H-0011 | Há código Thumb além de 0x160000 (região do censo) | CONFIRMADO (ciclo 6, quantificada) | censo ampliado 0x0–0xEC0000 executado (67 s): 88.782 BL → 51.268 alvos mas só 5.978 prólogos limpos; top-8 inalterado; massa extra é dados com ilhas Thumb (0x1D–0x1E e 0x4B-pseudo) → **quase todo código real está em 0x0–0x160000** | — | — |
| H-0012 | O maior SCC do callgraph (585 nós) é o núcleo da máquina de estados de jogo (scripts/overworld + engine compartilhada) | HIPÓTESE | callgraph ciclo 6: 5.981 nós, 21.314 arestas únicas; 5.266 SCCs; maior SCC com ~10% de todo o código — padrão típico de engines dispatcher+engine central | kernel de runtime C (refutável por assinatura: runtime C tende a folhas, não a ciclos gigantes) | ler membros do SCC e buscar tabelas de estado/strings de erro internas (ciclo 7) |
| H-0013 | Os 34 handlers de cada dispatcher 34c são stubs Thumb sem prólogo (por isso fora do CSV), com tail branch p/ continuação comum | CONFIRMADO p/ handler[0] das 2 tabelas (estrutura); **HIPÓTESE** quanto ao mecanismo do despachante resolver o bit 0 | sondas ciclo 6 em 0x0803FC90 e 0x08040424: Thumb coerente (`ldr/ldrb…b #0x803FD3E` próprio; ARM decodifica como lixo); entradas da tabela são pares (bit0=0) | despachante usa `ldr pc, [tbl]` com OR 1 posterior, ou `mov pc,r0` exige Thumb-bit via ajuste prévio — inspeção pendente do despachante | ler os bytes do despachante 0x0803FBE8 procurando `+1`/`orr` antes do salto; amostrar mais 5 handlers |
| H-0014 | DISPATCHER_34c_tbl0803FC08 = **GET accessor** de struct com layout status@+0x50, nivel@+0x54, hp@+0x56, maxHP@+0x58, 5 stats@+0x5A..+0x62 (layout de dados de unidade/"mon"); casos 4–8 leem campo indexado via 0x08044674 (sel 1..5); casos 10–28 via helper 0x0803FD44 (subdados/caixa) | **CONFIRMADO** (estrutural, ciclo 8) | helper 0x0803FD44 lido: 4 substructs sel 0..3 + recompute de checksum (0x0803E3E8: soma sel 0..3) + flags bad-egg ([r8+0x13]|=5, sub+7|=0x40) + XOR decrypt (0x0803F91C: `[+0x20]^=[+4]`) + jump table de **84 casos** @0x0803FDD8 → assinatura inequívoca de GetBoxMonData | — | — |
| H-0015 | DISPATCHER_34c_tbl0804039C = **SET espelho** do H-0014 (mesmas 34 posições; strb +0x54/+0x55; u16 de [r2]; caso[10]=no-op; casos 11–28 via 0x080404D0) | **CONFIRMADO** (ciclo 9) | corpo do helper 0x080404D0 lido: cabeça idêntica ao GET (4 substructs, decrypt, checksum vs [r7+0x1C], bad-egg, fixup encrypt 0x0803F8F8) + dispatch ≤0x50 c/ tabela própria | — | — |
| H-0017 | ENTRY_THUMB_main = esqueleto AgbMain-like: init (waitstate 0x4014, paleta, ~12 inits) → zera EWRAM 0x02000000+0x1C000 (memzero_ewram_like) → loop {per_frame_update_like 0x080005E8; checagem soft-reset A+B+START+SELECT via [0x030030F0+0x28]&1 && (v&0xE)==0xE com trio de chamadas 0x081E09D4/0x081E08F8/0x080008D8; game_loop_body_like 0x080582E0 retornando flag} | CONFIRMADO (estrutural, ciclo 9) | `dis 0x080003A4/-0x08000444`: sequência completa acima medida instrução a instrução | — | ler 0x080582E0 (despacho de callbacks/tasks — deve ligar-se ao hub indireto) |
| H-0016 | Hub de outdegree 0x0808CFF8 (117 callees) = controller de task/estado indireto (invisível por BL) | **BLOQUEADO-para-estática → requer dinâmica (ciclo 13)** | ciclo 13: busca exaustiva NEGATIVA: 0 refs de literal (par/Thumb+1), 0 ADR, 0 calls BL, 0 branches diretos/b.w, 0 ponteiros p/ o nó; o "117 callees" é artefato de atribuição: NO gap de 7.956 B (hub→próximo nó 0x0808EF0C) vivem várias funções sem prólogo cujos sites foram somados ao hub. Chunk 0x0808CFF8–0x0808EF0B só tem entradas dinâmicas (blx/ponteiros de registro), com 252 ponteiros **intra-chunk** (literal pools/switch internos) | — | mGBA: PC-trace/watchpoint na instalação do ponteiro (escritores de slots 0x03000E80/arr03005090) |
| H-0004 | Imagem contém modificações vs. qualquer dump limpo | CONFIRMADO | CRC32 7a6ef5f5, MD5 4ec27a4b..., SHA-1 00b40312..., SHA-256 6035a98f... ≠ No-Intro Rev 0/Rev 1 | — | — |
| H-0005 | Save type = Flash 1M (128 KiB), lib FLASH1M_V103 | CONFIRMADO | string "FLASH1M_V103" @ 0x006fbf14; bate com No-Intro "Save Type: Flash1M_v103" e dump report gbhwdb (MX29L010) | — | validar em emulador (Fase 4): TIPO de save detectado |

## Confirmadas / refutadas

Ver coluna Estado da tabela acima. CONFIRMADO: H-0001a, H-0001b, H-0003, H-0004,
H-0005, H-0006 (parcial), H-0008, H-0011. REFUTADA: H-0009.

## Como adicionar uma entrada

1. Registre a evidência reproduzível (comando + saída + hash do artefato).
2. Anote a alternativa mais plausível ANTES de testar.
3. Execute o teste; se indisponível, anote comando exato e saída esperada.
4. Atualize o estado e preserve o histórico (não sobrescreva evidências).

### Observações dinâmicas da build (Ciclo 21)

- Pós-título, esta hack abre **direta** o tutorial CONTROLE (START), sem
  menu clássico exposto — característica da ROM, não da emulação.
- Textos do tutorial exibidos corretamente em PT-BR (font/caréteres OK).
