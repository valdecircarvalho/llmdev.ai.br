# CMS do Blog (FastAPI + React)

## Estrutura
- API: `/Users/vcarva/workdir/projetos/llmdev.ai.br/apps/cms-api`
- Web: `/Users/vcarva/workdir/projetos/llmdev.ai.br/apps/cms-web`
- Infra: `/Users/vcarva/workdir/projetos/llmdev.ai.br/infra/docker-compose.yml`

## Pré-requisitos
- Docker + Docker Compose
- Repositório com remoto `origin` configurado
- Fine-grained PAT no GitHub com permissão de escrita no repositório (`Contents: Read and write`)

## Configuração
1. Crie o arquivo `/Users/vcarva/workdir/projetos/llmdev.ai.br/apps/cms-api/.env` a partir do exemplo:
   - `cp /Users/vcarva/workdir/projetos/llmdev.ai.br/apps/cms-api/.env.example /Users/vcarva/workdir/projetos/llmdev.ai.br/apps/cms-api/.env`
2. Gere hash bcrypt da senha administrativa:

```bash
docker compose run --rm api python -c "import bcrypt; print(bcrypt.hashpw(b'SUA_SENHA', bcrypt.gensalt()).decode())"
```

3. Atualize variáveis no `.env`:
   - `CMS_ADMIN_PASSWORD_HASH`
   - `CMS_JWT_SECRET`
   - `CMS_ALLOWED_ORIGIN`
   - `CMS_SECURE_COOKIE`
   - `CMS_GIT_REMOTE_URL` (ex: `https://github.com/OWNER/REPO.git`)
   - `CMS_GIT_TOKEN` (Fine-grained PAT)

Importante para Docker Compose:
- hashes bcrypt têm `$`, então use aspas simples no `.env` para evitar interpolação.
- Exemplo:

```env
CMS_ADMIN_PASSWORD_HASH='$2b$12$...'
```

## Subir stack

```bash
cd /Users/vcarva/workdir/projetos/llmdev.ai.br/infra
docker compose up --build -d
```

Painel ficará disponível em `http://localhost:8080`.

## Endpoints principais
Base: `/api/v1`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /content`
- `GET /content/{id}`
- `POST /content`
- `PUT /content/{id}`
- `DELETE /content/{id}`
- `GET /git/status`
- `POST /git/publish`
- `GET /health`

## Fluxo operacional
1. Login no painel.
2. Criar/editar notas e posts.
3. Salvar (apenas arquivos locais do repositório).
4. Publicar para executar `git add content/`, `git commit`, `git push` via HTTPS autenticado por PAT.
5. Cloudflare Pages faz deploy após o push.

## Segurança
- O painel exige senha única e JWT.
- Cookies são `HttpOnly` e podem ser `Secure` via env.
- Login com limitação de tentativas por IP.
- Ações de conteúdo e publicação são auditadas no SQLite.
- O token do GitHub fica apenas em variável de ambiente (`CMS_GIT_TOKEN`) e não é gravado nos arquivos do repositório.

## Dados persistidos
- Banco SQLite em volume Docker `cms_data` (`/data/app.db` dentro do container da API).
- Conteúdo continua sendo os arquivos `.md` em `/content/notes` e `/content/posts`.
