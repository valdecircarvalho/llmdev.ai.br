# Repository Guidelines

## Project Structure & Module Organization
This repository is a Hugo site for `llmdev.ai.br` using the `til` theme.
- `content/`: Markdown content (`posts/`, `notes/`, and pages like `about.md`).
- `hugo.toml`: Site configuration (menus, params, outputs, theme selection).
- `assets/`, `static/`, `layouts/`: Site-level assets and template overrides.
- `themes/til/`: Theme source (layouts, Tailwind/CSS, TypeScript, lint/format config).
- `public/`: Generated output from Hugo builds. Treat as build artifacts.
- `github.com/michenriksen/hugo-theme-til/`: Upstream theme snapshot/reference.

## Build, Test, and Development Commands
Run from repository root unless noted.
- `hugo server --gc --disableFastRender`: Start local dev server.
- `hugo --gc --minify`: Production-style static build to `public/`.
- `npm install`: Install root JS dependency (`vis-network`) when needed.
- `cd themes/til && npm install`: Install theme tooling dependencies.
- `cd themes/til && npm run dev`: Run theme dev pipeline (Hugo server + Tailwind watch).
- `cd themes/til && npm run format`: Format theme files via Prettier.

## Coding Style & Naming Conventions
- Content files: kebab-case names (for example, `hello-world.md`).
- Front matter: keep fields consistent with existing content and `hugo.toml`.
- Templates/HTML/TS/CSS in `themes/til/`: use Prettier defaults (`printWidth: 120`) and Tailwind class sorting.
- TypeScript: keep code under `themes/til/assets/ts/`; follow ESLint config using `@typescript-eslint/parser`.
- Prefer small, focused changes and preserve existing Hugo/TOML style.

## Testing Guidelines
There is no dedicated automated test suite in this repo today.
- Validate changes with `hugo --gc --minify` and ensure build succeeds.
- For UI/template edits, run `hugo server` and manually verify affected pages.
- For theme TS/CSS edits, run `cd themes/til && npm run dev` and check rendered output.

## Commit & Pull Request Guidelines
Current history is minimal (`Initial commit`), so follow clear, conventional commit style.
- Recommended commit format: `type(scope): short imperative summary` (for example, `feat(content): add ai-native-landscape note`).
- Keep commits atomic and include related config/content updates together.
- PRs should include: objective, key files changed, local verification steps, and screenshots for visual/theme changes.
