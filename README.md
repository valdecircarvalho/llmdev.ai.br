# llmdev.ai.br (Astro)

Blog em Astro neste mesmo repositório, com estratégia de teste de temas por branch.

## Branches

- `main`: produção
- `themes-base`: base Astro Blog limpa
- `themes-1`: tema candidato 1
- `themes-2`: tema candidato 2
- `themes-3`: tema candidato 3

## Rodar localmente

```sh
npm install
npm run dev
```

Build de validação:

```sh
npm run build
```

## Fluxo para testar temas

1. Escolha a branch de teste (`themes-1`, `themes-2` ou `themes-3`).
2. Instale e aplique o tema nessa branch.
3. Rode `npm run build` para validar.
4. Faça commit somente das mudanças desse tema.
5. Compare as branches (visual, performance, SEO e facilidade de customização).

Troca rápida de branch:

```sh
git checkout themes-1
git checkout themes-2
git checkout themes-3
```

## Stack

- [Astro](https://astro.build)
- Template inicial: `blog`
