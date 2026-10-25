# FireRed Gen 1-9 — documento de entrega (E9)

Build final produzida a partir do **FireRed de verdade** (`pret/pokefirered`,
descompilação oficial), modificando **somente o necessário** para comportar
as 9 gerações (1025 espécies). Todo o resto do jogo foi preservado.

> **🇧🇷 NOVA ENTREGA (2026-10-25): versão traduzida para PT-BR.**
> A build abaixo nesta seção é a entrega original em inglês (E9).
> A versão atual, com o jogo inteiro em português do Brasil (T1-T8:
> interface, batalha, descrições de golpes/itens/habilidades, as 1.025
> entradas da Pokédex em métrico, todos os diálogos dos 430 mapas,
> Fame Checker, Sistema de AJUDA e nomes de área), está em:
>
> - **Link público (Google Drive):**
>   <https://drive.google.com/file/d/1R0A1slLvh4OchEkJ7NHtbIqIrxkgeWZB/view>
> - Download direto:
>   `https://drive.google.com/uc?id=1R0A1slLvh4OchEkJ7NHtbIqIrxkgeWZB&export=download`
>
> | campo | valor |
> |---|---|
> | arquivo | `pokefirered_gen1-9_ptbr.gba` — 16 777 216 bytes |
> | md5 | `6971baf2ecfd89beca050f44961addbf` |
> | sha256 | `ae5f1dff3d6ae72354b76c39ffebdcf27b78f9f5054a6705ae77173fd48b00d9` |
> | sha1 | `c71db48ff735af2eab73d8dd0501c69c979deefc` |
>
> Nomes de **espécies, golpes, itens e habilidades ficam em inglês**
> (decisão de projeto); todo o resto é PT-BR. Detalhes e provas:
> [`PLANO_TRADUCAO_PTBR.md`](PLANO_TRADUCAO_PTBR.md) e
> `reports/firered_t2…t8/`.

## Download

- **Link público (Google Drive):**
  <https://drive.google.com/file/d/1P3F4sLYEik4mBwidRFkJmSERjM8A2HyD/view>
- Download direto:
  `https://drive.google.com/uc?id=1P3F4sLYEik4mBwidRFkJmSERjM8A2HyD&export=download`

| campo | valor |
|---|---|
| arquivo | `pokefirered_gen1-9.gba` — 16 777 216 bytes |
| md5 | `7fcfdf53cc541f8dd571436ba8887759` |
| sha256 | `b2874f30abc9805a4de90f97e058908a292baa5fbd10816e183abec1d29ec2d8` |
| base | `pret/pokefirered`, compilado com `make -j2 MODERN=1` |

Conferir o hash depois de baixar (PowerShell, na pasta do download):

```powershell
Get-FileHash .\pokefirered_gen1-9.gba -Algorithm SHA256
Get-FileHash .\pokefirered_gen1-9.gba -Algorithm MD5
```

## Como jogar no Windows

1. Baixe o arquivo pelo link acima.
2. Instale o emulador **mGBA** (site oficial: mgba.io) — é gratuito.
3. Abra o mGBA → `File > Load ROM…` → escolha `pokefirered_gen1-9.gba`.
4. Jogue normalmente. Saves e savestates funcionam como num FireRed comum.

Não é preciso patch, baserom nem nenhuma outra ferramenta.

## O que mudou (etapas E1-E7)

| etapa | mudança |
|---|---|
| E1 | Porte da infraestrutura de dados no estilo RHH: `NUM_SPECIES` = 1026, tabelas expandidas |
| E2 | Dados das 1025 espécies (stats, tipos, habilidades, aprendizados) |
| E3 | Sistema de batalha aceitando espécies/dados novos |
| E4 | Golpes modernos (dados + efeito em batalha, provado em jogo) |
| E5 | Habilidades modernas (ex.: Earth Eater, provado em jogo) |
| E6 | Sprites/ícones/paletas das espécies novas |
| E7 | Encontros selvagens misturados (novas espécies obteníveis), habitats da Pokédex (Naive Bayes p/ #387+), 481 slots de treinador com espécies novas, evoluções modernas adaptadas |

Política de evoluções (E7-2c): evolução por **troca → nível 37**; por **item
exclusivo de outra gen → pedra equivalente ou nível 36**; amizade e nível
mantidos. 233 espécies novas com linha evolutiva funcional; nenhuma evolução
inatingível por depender de troca.

## O que NÃO mudou

- História, mapas, cidades, NPCs, scripts, textos e eventos do FireRed.
- Itens, mecânica geral de batalha das gens antigas, Pokédex de Kanto.
- Sistema de save (compatível com o formato padrão do FireRed).
- Idioma: **inglês** (o patch PT-BR foi descartado por decisão do projeto).

## Limitações honestas

- **Espeon/Umbreon inobteníveis**: evoluem por amizade de dia/noite e o
  FireRed não tem relógio (RTC). Mantido como no original.
- Golpes/habilidades modernos foram **amostrados** nas provas em jogo (não
  testados um a um); a integridade de TODOS os dados é conferida pelo
  `verificar_rom.py`.
- Balanceamento dos encontros/treinadores com espécies novas é funcional,
  não curado à mão.
- Formas regionais/megas/fenômenos pós-Gen-3 (clima de Gen 5+, Dynamax etc.)
  **não** foram portados — só o necessário para as espécies existirem,
  lutarem e evoluírem.

## Tabela CONFIRMADO / PROVÁVEL / DESCONHECIDO

| afirmação | status | evidência |
|---|---|---|
| ROM compila e boota até o overworld | CONFIRMADO | boot automatizado (preparar-estado) na build `7fcfdf53` |
| Espécie Gen 9 aparece selvagem, é capturada e entra na dex | CONFIRMADO | `prova_encontros_e7.py` APROVADO (Lechonk #915, Rota 1) |
| Golpes modernos causam o efeito certo em batalha | CONFIRMADO (amostra) | `prova_golpes_e4.py` 6/6 |
| Habilidades modernas funcionam em batalha | CONFIRMADO (amostra) | `prova_habilidades_e5.py` 3/3 (Earth Eater imune a Bulldoze) |
| Evoluções modernas acontecem em jogo | CONFIRMADO (amostra) | Magnezone (pedra), Lucario (amizade), Gigalith (nível ex-troca) — `reports/firered_e7/10-13_*.png` |
| Treinadores usam espécies novas | CONFIRMADO | 481 slots conferidos no binário (`verificar_rom.py`) |
| Todas as 1025 espécies têm dados íntegros | CONFIRMADO | `verificar_rom.py` 100% na build final |
| Jogo completável do início ao fim (Elite 4) | PROVÁVEL | mudanças não tocam scripts/progressão; não foi jogado inteiro |
| Save compatível com FireRed vanilla | DESCONHECIDO | formato não alterado, mas não testado importar/exportar saves |
| Comportamento em hardware real (cartucho/flashcart) | DESCONHECIDO | testado só no mGBA |

## Checklist de regressão por etapa (E8)

Um comando roda tudo e imprime PASS/FAIL (falha bloqueia o merge):

```bash
# Linux/WSL — exige ambiente religado por scripts/firered/setup_ambiente.sh
bash scripts/firered/rodar_regressao.sh
```

```powershell
# Windows: rodar dentro do WSL
wsl bash scripts/firered/rodar_regressao.sh
```

Etapas cobertas: self-tests dos geradores, `verificar_rom.py` na ROM real
(E2-E7), prova de golpes (E4), prova de habilidades (E5), prova de
encontro+captura (E7). Resultado da última rodada completa:
`reports/firered_e8/LEIA-ME.md` (100% PASS na build `7fcfdf53`).

## Regra do projeto

**Nenhuma ROM é versionada no Git** (`rom/` está no `.gitignore`). A
distribuição é exclusivamente pelo link do Drive acima. A build
intermediária anterior ficou no Drive como
`pokefirered_gen1-9_E7_DESATUALIZADA.gba` apenas para histórico.
