# Skills para criar vídeo com agentes de IA — levantamento verificado

> Levantado em 12/11/2026 pelo fluxo do `find-skills`. Fonte: leaderboard e
> busca do `skills.sh` + verificação de repositório/origem via `gh api`.
> Números de instalação são os do diretório na data. **Atenção:** o ranking
> bruto está inflado por espelhos (ver §1).

## 1. Armadilha do ranking: espelhos inflam os números

O termo "video" no `skills.sh` devolve 7 cópias de `ai-video-generation`
(101-skills, magentosh, skills-shell, qu-skills, bankai-skills,
its-a-skill-issue, skills-101) com 553K–1,0M instalações **cada**.

Verificação: todas têm o mesmo conteúdo e apontam para o CLI `belt` da
`inference.sh`. O repositório original (`inference-sh/skills`, 807 estrelas)
registra **14 instalações** para a mesma skill. Os espelhos têm 23 estrelas
(101-skills) e menos. Ou seja: **1 milhão de "instalações" = uma skill
real + seis republicações**, não adoção independente.

Consequência prática: para escolher, olhar **estrelas do repo + autoria +
auditoria de segurança**, não o número de instalações isolado.

## 2. Panorama por etapa do trabalho

Criar vídeo com agente não é uma skill só — são quatro trilhas distintas.
As mais usadas em cada uma:

### A. Composição/render programático (o que hoje domina o ecossistema)

**`heygen-com/hyperframes`** — 82,8K estrelas. HTML + GSAP → vídeo (o
HyperFrames busca a timeline frame a frame, render determinístico).
É a família mais usada de todas.

| Skill | Instalações | Para quê |
|---|---|---|
| `hyperframes` | 1,5M | base: compor vídeo em HTML, legendas, transições |
| `hyperframes-cli` | 1,5M | CLI (`npx hyperframes init/check/capture`) |
| `media-use` | 1,4M | mídia: avatar, narração, trilha, stock |
| `hyperframes-creative` | 917K | direção criativa/efeitos |
| `general-video` | 661,8K | vídeo genérico |
| `remotion-to-hyperframes` | 605K | migrar projeto Remotion |
| `product-launch-video` | 539K | vídeo de lançamento de produto |
| `faceless-explainer` | 522K | explicador sem rosto (formato YouTube) |
| `music-to-video` | 419K | vídeo a partir de música |
| `slideshow` | 510K | slideshow |
| `talking-head-recut` | 408K | recut de talking head |

**`remotion-dev/skills`** — 6,9K estrelas, 13 skills; alternativa
React/TS para vídeo. `remotion-render` 325,7K, `remotion-create` 323,6K,
`remotion-studio` 285,9K, além de `remotion-captions`, `-multimedia`,
`-markup`, `-best-practices`. Melhor quando o time já é React ou quando o
vídeo precisa ser parâmetro de app (SaaS, `remotion-saas`).

### B. Edição de vídeo já existente (cortar, não gerar)

**`browser-use/video-use`** — 30,9K estrelas (o repo mais estrelado da
lista depois do HeyGen), 5,8K instalações. Metodologia para editar
material bruto: transcrição → silêncios/bordas de fala → corte, com
"áudio é primário, visual segue", confirmação antes de cortar e regras
duras de correção de produção. Usa **ffmpeg + PIL**.

**`digitalsamba/claude-code-video-toolkit`** — 2,5K estrelas. Pipeline
completo com modelos abertos: `ffmpeg` (14,3K), `moviepy` (1,4K),
`ltx2` (1,2K), `acestep` (áudio/música, 1,4K), `frontend-design`.

### C. Geração por modelo (texto/imagem → vídeo, via API paga)

**`inference-sh/skills`** — 807 estrelas, **86 skills**, o catálogo mais
completo: `ai-video-generation`, `google-veo`, `seedance`, `image-to-video`,
`p-video`, `p-video-avatar`, `ai-avatar-video`, `talking-head-production`,
`storyboard-creation`, `video-ad-specs`, `explainer-video-guide`,
`video-prompting-guide`, `remotion-render`. Tudo orquestrado pelo CLI
`belt` (exige login e créditos).

**`higgsfield-ai/skills`** — 1,9K estrelas. `higgsfield-video-explainer`
(147,7K), `higgsfield-faceless-video`, `higgsfield-generate`,
`higgsfield-soul-id` (consistência de personagem).

**`prime-skills/runcomfy-agent-skills`** — 62 estrelas: `video-edit`
(447,5K), `image-to-video` (445,7K), `video-inpainting`, `video-extend`,
`video-outpainting`, `ai-avatar-video`. Números altos, repo pequeno —
mesmo padrão de republicação; tratar como wrapper de RunComfy.

### D. Marketing / UGC / anúncio

`postplusai/postplus-skills` (`ugc-flow` 682, `shot-by-shot-analysis` 499,
`visual-hook` 287, `persona-pack` 285), `agricidaniel/claude-ads`
(`ads-creative` 4,4K), `vyralcontent/content-skills`
(`viral-short-form`), `akillness/jeo-skills` (`video-production` 479,
`remotion-video-production` 514).

## 3. Recomendação por objetivo

| Se o objetivo é… | Instalar | Comando |
|---|---|---|
| Vídeo "de verdade", editável, sem depender de API paga | HyperFrames (base + cli + media-use) | `npx skills add heygen-com/hyperframes --skill hyperframes -g -y` |
| Cortar/editar footage que já existe | `video-use` | `npx skills add browser-use/video-use --skill video-use -g -y` |
| Vídeo dentro de app React/Next | Remotion | `npx skills add remotion-dev/skills --skill remotion-create -g -y` |
| Gerar clipes com modelo (Veo, Seedance…) | `inference-sh/skills` | `npx skills add inference-sh/skills --skill ai-video-generation -g -y` |
| Avatar/apresentador falante | Higgsfield ou inference.sh | `npx skills add higgsfield-ai/skills --skill higgsfield-video-explainer -g -y` |

## 4. Antes de instalar (checklist de `docs/SKILLS.md` §4)

- [ ] **Pago/API key**: inference.sh (`belt login`), HeyGen, Higgsfield e
      RunComfy exigem conta e créditos. HyperFrames e Remotion renderizam
      local; HyperFrames tem beacon de telemetria (`events --skill=`) e
      consulta de plano (`usage --json`) — dá para desligar.
- [ ] **Node/npm** é pré-requisito de HyperFrames e Remotion. `video-use`
      precisa de **ffmpeg** e **PIL** — **não existem neste sandbox**
      (verificado: `which ffmpeg` vazio, `import PIL` falha).
- [ ] **Auditar o pacote baixado**:
      `python3 scripts/skills_audit.py --path <dir-clonado>`. HyperFrames e
      Remotion trazem muitos scripts — revisar antes.
- [ ] **Auditoria de segurança do diretório**: HyperFrames `hyperframes`
      → Snyk *Warn*; `video-use` e `remotion-create` → três passes limpos.
- [ ] Não instalar espelhos (`*/superpowers`) quando o original existe.

## 5. Comandos úteis (deste sandbox)

```bash
npx skills add <repo> --list          # inventário exato, funciona aqui
npx skills add <repo> --skill <nome> -g -y
npx skills use <repo>@<skill>         # ler o SKILL.md sem instalar
python3 scripts/skills_audit.py --path /tmp/repo/skills   # auditar antes
```

`npx skills find "video"` **não** funciona aqui (sem acesso a `skills.sh`);
usar o fallback de `docs/SKILLS.md` §5.
