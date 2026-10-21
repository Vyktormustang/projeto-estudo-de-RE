# Follow-up — tentativa de configurar REA + Ghidra

**Data:** 2026-10-21. **Resultado:** REA CLI instalado temporariamente e verificado; configuração operacional do provider Ghidra bloqueada por falta do binário Ghidra/JDK e pela política de saída de rede desta sessão. Nenhuma análise nativa nova foi atribuída a REA ou Ghidra.

## O que foi feito

- Ambiente: branch `arena/d3a71171-projeto-estudo-de-re`; ROM local SHA-256 `6035a98faf09f5f6db880f0ab436c54f35e33c5738d899345d8242930da0b4ae`.
- Node `v22.22.3` e npm `10.9.8` já estavam presentes.
- Instalei `rea-agents@6.7.0` por npm em `/tmp/rea-install` (não no repositório). `rea --help` e `rea doctor --json` executaram.
- `rea doctor` reconheceu Node 22, mas retornou `healthy:false`: Ghidra não configurado (`GHIDRA_INSTALL_DIR` ausente), skill ausente e nenhum cliente de agente/registro MCP detectado.
- `rea setup --dry-run --format json` retornou `plannedActions: []`; não havia cliente suportado detectado no ambiente para registrar integração. Não criei configurações fictícias nem alterei arquivos de configuração de clientes inexistentes.
- As consultas Arena `list_connector_tools` para `rea` e `ghidra` retornaram `unsupported`; portanto, não existe conector dessas ferramentas nesta sessão.
- Tentei `rea inspect-artifact` no `.gba`. Resultado explícito: `target_unavailable`, `unsupported binary format`; a ROM não foi analisada pelo provider.

## Bloqueios técnicos concretos

1. O diagnóstico do REA exige uma instalação extraída do Ghidra **12.1.x** e Java. `java`/`analyzeHeadless` não existem no PATH.
2. A API oficial do GitHub informou Ghidra 12.1.4, asset `ghidra_12.1.4_PUBLIC_20260921.zip`, tamanho 569.649.598 bytes e SHA-256 `ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db`. A URL de release no domínio permitido `github.com` redireciona o arquivo para `objects.githubusercontent.com`; a conexão a esse host foi recusada pela restrição de rede do ambiente (`SSL_ERROR_SYSCALL`). Não baixei nem instalei um arquivo incompleto, e não tentei contornar a allowlist.
3. A ROM é uma imagem GBA com CPU ARM7TDMI/ARMv4T e código ARM/Thumb. O caminho genérico `--target-format raw-binary --architecture arm` do REA escolhe `ARM:LE:32:v7`; o código do pacote também não admite substituir o language ID em uma importação raw-binary. Isso não é uma configuração apropriada para afirmar análise correta desta ROM. Com o binário disponível, será preciso importar com a linguagem ARMv4T correta, base ROM `0x08000000` e tratamento dos dois modos, e então validar um caminho REA que preserve essa configuração. A CLI rejeita override de linguagem no modo raw-binary; não posso afirmar, sem testar, que ela aceitará um projeto raw criado manualmente.

## Limite do que esta tentativa prova

- REA CLI ficou disponível apenas neste sandbox/turno, em `/tmp`; a instalação temporária não é uma instalação persistente do projeto nem uma integração MCP do Arena.
- Nenhuma decompilação, xref ou resultado de função do Ghidra foi obtido.
- A observação do erro de formato não classifica o conteúdo da ROM nem substitui a análise nativa.
- A análise Capstone dos ciclos anteriores permanece evidência estática auxiliar. A lacuna de Ghidra registrada nos relatórios anteriores continua aberta.
- Não alterei a ROM, o save, nem as alterações preexistentes em `HANDOFF.md`, `REA.md` ou `README.md`.

## Pré-condições para concluir a configuração

É necessário que um Ghidra 12.1.x e um JDK compatível estejam acessíveis localmente (ou que a aquisição de release assets GitHub seja permitida no sandbox). Depois, apontar `GHIDRA_INSTALL_DIR` para a instalação extraída, importar a ROM em projeto com linguagem/mapeamento explicitamente conferidos e executar `rea doctor` novamente. Só após o diagnóstico e uma importação válida será retomada a verificação Ghidra dos ciclos 17–18.
