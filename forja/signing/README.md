# Assinatura do APK FORJA

## Estado atual (v39.0.0)

| Campo | Valor |
|---|---|
| Keystore | `forja.p12` (PKCS#12, RSA 2048) |
| Alias | `forja` |
| Senha do keystore/chave | `forja-ci-offline-2026` |
| Validade | 30/10/2026 → 22/10/2056 |
| SHA-256 do certificado | `15:E9:23:0C:8A:25:99:DB:FB:A2:2B:11:A3:87:18:95:12:55:93:1F:E4:E6:29:EB:04:C8:AA:A1:D8:73:8B:7C` |
| Schemes | v1 + v2 + v3 (apksigner) |

O certificado versionado está em `forja-cert.pem` (só a parte pública) e o
keystore empacotado em base64 está em `forja.p12.b64`.

## Por que ele está versionado (e o risco)

O build precisa assinar. A via correta é guardar o keystore em **segredos do
repositório** (`FORJA_KEYSTORE_B64`, `FORJA_KS_PASS`, `FORJA_KEY_PASS`,
`FORJA_KS_ALIAS`). O token usado para configurar o repositório não tinha
permissão de *admin* para criar segredos (HTTP 403), então o workflow usa este
fallback versionado.

⚠ **Consequência:** este repositório é público — qualquer pessoa com acesso ao
`forja.p12.b64` + senha pode assinar um APK que o Android aceitaria como
atualização do FORJA. Para um app pessoal, offline e sem dados sensíveis o
impacto é baixo, mas **não é a configuração ideal**.

### Como fechar isso (2 minutos, no seu GitHub)

1. Settings → Secrets and variables → Actions → New repository secret:
   - `FORJA_KEYSTORE_B64` = conteúdo de `forja/signing/forja.p12.b64`
   - `FORJA_KS_PASS` = `forja-ci-offline-2026`
   - `FORJA_KEY_PASS` = `forja-ci-offline-2026`
   - `FORJA_KS_ALIAS` = `forja`
2. Avisar que eu removo `forja.p12.b64` do repositório (o workflow passa a
   falhar de propósito se o segredo faltar).

## Continuidade de atualização

O Android só aceita instalar por cima (atualização) um APK assinado com o
**mesmo certificado**. Se este keystore mudar, a instalação será limpa:
desinstale a versão anterior — o Cofre (localStorage) é apagado junto, então
exporte o JSON antes.

> O APK v38.0 foi assinado com outro certificado (`77d64be4…159b` no dossiê
> v15). Portanto **a instalação do v39 por cima do v38 não é possível**: é
> instalação limpa, como já ocorreu na v15.
