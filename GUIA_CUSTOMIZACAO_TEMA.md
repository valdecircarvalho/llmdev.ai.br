# Guia de Customizacao do Theme `til`

Este projeto usa Hugo com o tema `til` (`theme = "til"` em `hugo.toml`).  
A forma mais segura de customizar e sobrescrever arquivos no projeto raiz, sem editar `themes/til` diretamente.

## 1. Onde mexer primeiro

- Configuracao geral: `hugo.toml`
- Conteudo: `content/posts/`, `content/notes/`, paginas como `content/about.md`
- Overrides de layout: `layouts/` (no projeto raiz)
- Assets proprios: `assets/` e `static/` (no projeto raiz)

Regra importante: arquivo no raiz com o mesmo caminho do tema tem prioridade sobre `themes/til/...`.

## 2. Customizacao por configuracao (`hugo.toml`)

Comece por aqui antes de alterar HTML/CSS:

- Menu principal: secao `[menus]`
- Home, notas, rodape e robots: `[params.home]`, `[params.notes]`, `[params.footer]`, `[params.robotstxt]`
- Destaques:
  - `showGraph = true/false`
  - `recentPostsLimit` e `recentNotesLimit`
  - `creativeCommonsLicense`

Exemplo:

```toml
[params.home]
  showRecentPosts = true
  recentPostsLimit = 5
```

## 3. Override de layouts sem fork do tema

Para alterar parcial/template do tema:

1. Copie do tema para o mesmo caminho no raiz.
2. Edite apenas o necessario.

Exemplo:

```bash
mkdir -p layouts/partials
cp themes/til/layouts/partials/header.html layouts/partials/header.html
```

Voce pode fazer o mesmo para:
- `layouts/_default/single.html`
- `layouts/partials/footer.html`
- `layouts/shortcodes/*.html`

## 4. CSS e JS personalizados

O tema carrega:
- CSS: `resources.Get "css/index.css"`
- JS: `resources.Get "ts/main.ts"`

Entao voce pode sobrescrever criando no raiz:
- `assets/css/index.css`
- `assets/ts/main.ts`

Sugestao pratica:
- copie o arquivo original do tema
- ajuste cores, tipografia e componentes gradualmente

```bash
mkdir -p assets/css assets/ts
cp themes/til/assets/css/index.css assets/css/index.css
cp themes/til/assets/ts/main.ts assets/ts/main.ts
```

## 5. Fluxo de desenvolvimento

- Subir site local: `hugo server --gc --disableFastRender`
- Build de validacao: `hugo --gc --minify`
- Se mexer em toolchain do tema:  
  `cd themes/til && npm install && npm run dev`

## 6. Boas praticas para manutencao

- Evite editar `themes/til` direto (dificulta atualizar tema).
- Prefira overrides pequenos e isolados.
- Documente cada override em commit/PR (qual arquivo, motivo e impacto visual).
- Ao finalizar mudancas visuais, valide home, lista de posts/notas e pagina individual.
