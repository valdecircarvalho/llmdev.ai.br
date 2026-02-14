# Deploy na Cloudflare Pages

Este projeto ja esta pronto para deploy como site estatico Hugo.

## 1) Criar projeto Pages (Git)
- Cloudflare Dashboard -> Workers & Pages -> Create -> Pages -> Connect to Git.
- Repositorio: este projeto.
- Production branch: `main` (ou a branch principal que voce usa).

## 2) Configuracao de build
- Framework preset: `Hugo`
- Build command: `hugo --gc --minify`
- Build output directory: `public`

## 3) Dominio customizado
No projeto Pages -> `Custom domains`:
- `llmdev.ai.br`
- `www.llmdev.ai.br`

Defina `llmdev.ai.br` como canonico e redirecione `www` para raiz.

## 4) Preview por branch/PR
Com Git conectado, o Pages cria URLs de preview automaticamente para branches e pull requests.

## 5) Checklist de validacao
- `https://llmdev.ai.br` abre com HTTPS valido.
- `https://www.llmdev.ai.br` redireciona para `https://llmdev.ai.br`.
- Novo push dispara deploy automatico.
- URL de preview e criada para PR/branch.
- `sitemap.xml` e links canonicos nao apontam para `example.com`.

## 6) Comando local de verificacao
```bash
hugo --gc --minify
```
