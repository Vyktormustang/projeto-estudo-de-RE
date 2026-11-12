# Skills de agente — o que está instalado e como usar

> Documento de governança. Existe porque o agente agora **descobre e instala
> skills sozinho** — e instalar código de terceiros sem auditoria é risco.
> Regra do projeto (ver `HANDOFF.md` §4): FATO/HIPÓTESE rotulados, nada sem
> evidência. Vale igual para skills.

## 1. O que é o CLI

`skills` (pacote npm `skills`, mantido por `vercel-labs`) é o gerenciador de
pacotes do ecossistema aberto de *agent skills*. Uma skill é uma pasta com
`SKILL.md` (frontmatter `name` + `description` + instruções em markdown),
opcionalmente com scripts/referências.

```bash
npx skills --version        # 1.8.1 (12/11/2026)
npx skills add <owner/repo> --skill <nome> [-g] [-y]
npx skills find <query> [--owner <owner>]
npx skills list -g
npx skills check            # procura atualizações, não instala
npx skills update           # aplica atualizações
npx skills remove <nome> -g
npx skills use <owner/repo>@<skill>   # usa sem instalar (injeta o SKILL.md)
```

Diretório canônico: `~/.agents/skills/<nome>/`, com symlinks por agente
(`~/.claude/skills/<nome>` etc.) e registro em `~/.agents/.skill-lock.json`
(guarda `source`, `skillPath` e `skillFolderHash` — serve de auditoria de
integridade).

## 2. Instalado neste ambiente

| Skill | Origem | Escopo | Caminho | Auditoria |
|---|---|---|---|---|
| `find-skills` | `vercel-labs/skills` (oficial) | global (usuário) | `~/.agents/skills/find-skills/SKILL.md` | 1 arquivo, 5472 B, **só markdown**; sem scripts, sem dependências, sem rede; hash idêntico ao do repositório oficial; `skillFolderHash` `7bc223e2…` no lock |

O `find-skills` **não executa nada**: ele ensina o agente a (1) identificar o
domínio da tarefa, (2) conferir o leaderboard do `skills.sh`, (3) buscar com
`npx skills find`, (4) verificar qualidade/origem antes de recomendar,
(5) apresentar opções com contagem de instalação, (6) instalar só com
consentimento.

## 3. Como o agente usa isso nas próximas tarefas

Feito **antes** de escrever código novo, quando a tarefa tem cara de "problema
já resolvido por alguém":

1. **Triagem** — a tarefa é de domínio com skill conhecida? (testes, docs,
   CI, refactor, design, git, changelog…)
2. **Já tenho?** `npx skills list -g` primeiro. Nunca instalar duplicata.
3. **Buscar** — leaderboard `https://skills.sh` e/ou `npx skills find "<query>"`.
   Alternativa quando o registro estiver fora: busca por código no GitHub
   (`gh api search/code -f q='filename:SKILL.md <termo>'`).
4. **Auditar antes de instalar** (§4).
5. **Instalar** com escopo global e avisar o usuário o que mudou.
6. **Usar** — carregar o `SKILL.md` e seguir as instruções; ao final, dizer
   **qual skill foi usada** e o que ela mudou no resultado.
7. **Se nada serve**: dizer que não existe skill adequada e seguir com as
   capacidades gerais. Não inventar skill, não instalar "quase relacionada".

Critério de uso: a skill precisa **melhorar** o resultado (precisão,
velocidade ou cobertura). Se ela só repete o que já sei fazer, não vale o
custo de contexto nem o risco.

## 4. Checklist de segurança (obrigatório)

Antes de instalar qualquer skill:

- [ ] **Origem**: owner/repo existe, é ativo, tem estrelas/histórico? Prefira
      `vercel-labs`, `anthropics`, `microsoft`, `google-*`, `nvidia`.
- [ ] **Instalações**: ≥ 1K no `skills.sh` é bom sinal; < 100 exige motivo
      forte. Popularidade não é prova de segurança — só reduz o risco.
- [ ] **Conteúdo**: leia o `SKILL.md` inteiro e **liste os arquivos**.
      Markdown = baixo risco. Scripts (`install.sh`, `*.py`, `postinstall` em
      `package.json`) = risco alto, exigem leitura linha a linha.
- [ ] **Rede/credenciais**: a skill pede token, `curl | bash`, upload de
      arquivo, acesso a `~/.ssh`, `.env`, git credentials? Se sim → recusar
      por padrão.
- [ ] **Escopo**: ela escreve fora do projeto (`~/.bashrc`, PATH, cron)?
      Instalar em vez disso no escopo global com `-g` é o padrão aqui.
- [ ] **Duplicata**: já existe skill local cobrindo o mesmo tema? Não instalar.
- [ ] **Pós-instalação**: `diff` contra o repo oficial ou conferir
      `skillFolderHash` no `.skill-lock.json`.
- [ ] **Reversível**: `npx skills remove <nome> -g` sempre disponível.

Automatizado por `scripts/skills_audit.py` (§6).

## 5. Restrições deste sandbox (FATO, testado 12/11/2026)

O ambiente só tem saída de rede para `github.com`, `codeload.github.com`,
`api.github.com`, `registry.npmjs.org`, `pypi.org`, `files.pythonhosted.org`.
Consequências práticas:

- `https://skills.sh` (leaderboard + API de busca) **não responde** daqui
  (curl → `000`). A busca do CLI depende dele, então
  `npx skills find "<query>"` retorna `No skills found` **mesmo havendo
  resultados** — é falso negativo, não ausência de skill.
- `npx skills add` e `npx skills use` **funcionam** (clonam do GitHub).
- `npx skills check` funciona e cai para clone do Git quando a API do GitHub
  está indisponível.
- **Fallback de descoberta**: usar o `fetch_page`/`web_search` para ler
  `https://www.skills.sh/search?q=<termo>` e confirmar instalador/contagem, e
  `gh api search/code -f q='filename:SKILL.md <termo>'` para achar candidatos
  no GitHub. Foi assim que validei que `find-skills` é o #1 do leaderboard
  (4,3M instalações).

## 6. Auditoria automatizada

```bash
python3 scripts/skills_audit.py              # audita o que está instalado
python3 scripts/skills_audit.py --json       # saída legível por máquina
python3 scripts/skills_audit.py --path ~/.agents/skills/nova-skill   # pré-instalação
python3 scripts/skills_audit.py --self-test  # testa o próprio auditor
```

Sai com código ≠ 0 se achar risco **alto** — serve para portão de CI ou para
checagem manual antes de aprovar uma instalação.

## 7. Manutenção

- `npx skills check` de vez em quando; `npx skills update -g -y` para aplicar.
- Skill atualizada muda de hash: o `.skill-lock.json` registra — se o
  `updatedAt` mudar e o hash também, **re-auditar** antes de confiar.
- Remover: `npx skills remove <nome> -g`.
- Telemetria: o CLI envia dados anônimos de uso; `DO_NOT_TRACK=1` ou
  `DISABLE_TELEMETRY=1` desliga.

## 8. Página do registro (para consulta fora do sandbox)

- Diretório: https://skills.sh
- `find-skills`: https://skills.sh/vercel-labs/skills/find-skills
- CLI + docs: https://github.com/vercel-labs/skills

## 9. Levantamentos já feitos

- `docs/SKILLS_VIDEO.md` — skills mais usadas para criar/editar vídeo com
  agentes (panorama por etapa, com verificação de origem e a armadilha dos
  repositórios-espelho que inflam a contagem de instalações).
