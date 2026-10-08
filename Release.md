# Releasing Scratch

Releases are Docker images built by GitHub Actions and published to
`ghcr.io/eaudeweb/scratch`. Production is a single `docker-compose.yml` on the
server that runs the `web`, `async` and `cron` services from that image (the
crontab is baked into the image too). Deploying is manual.

```
git tag 1.0.62 ──> GitHub Actions ──> ghcr.io/eaudeweb/scratch:1.0.62 ──> manual pull on prod
```

## 1. Before tagging

- Make sure the **Tests** workflow (`.github/workflows/tests.yml`) is green on
  the pull request. It runs the test suite on every pull request to `master` and
  every push to `master`, so you don't need to run it yourself.
- If you changed a scraper, run its update command once locally against a short
  range (e.g. `python manage.py update_ungm --days_ago 1`). Keep it to one run so
  the sources don't rate limit or block us.
- Check for new migrations (`python manage.py makemigrations --check --dry-run`)
  and note whether the release has any, you'll need it when deploying.
- Merge the work into `master`, and check that the Tests run on `master` is green
  before tagging.

## 2. Tag the release

Versions are plain `MAJOR.MINOR.PATCH`, without a `v` prefix. The last image on
Docker Hub was `1.0.61`, so GHCR releases start at `1.0.62`. To see the latest
tag, fetch them first (clones don't always have all of them):

```bash
git fetch --tags
git tag --sort=-v:refname | head -3
```

Tag the merge commit on `master` and push the tag:

```bash
git checkout master && git pull
git tag 1.0.62
git push origin 1.0.62
```

Pushing the tag starts the **Docker image** workflow
(`.github/workflows/docker.yml`). Follow it in the repository's Actions tab. When
it is green, the image is available as:

- `ghcr.io/eaudeweb/scratch:1.0.62`
- `ghcr.io/eaudeweb/scratch:latest`
- `ghcr.io/eaudeweb/scratch:sha-<commit>`

The workflow can also be started by hand from the Actions tab (*Run workflow*).
A manual run from a branch only produces the `sha-<commit>` tag, which is useful
for trying a build without making a release.

## 3. Deploy to production

On the server, in the directory that holds the compose file:

1. Set the new version in the `.env` file next to the compose file:

   ```bash
   SCRATCH_VERSION=1.0.62
   ```

   The compose file uses it for the `web`, `async` and `cron` images
   (`image: ghcr.io/eaudeweb/scratch:${SCRATCH_VERSION}`), so the compose file
   itself doesn't change between releases. Docker Compose reads `.env` from the
   project directory automatically. Use a version number rather than `latest`, so
   it's always clear what is deployed and a rollback is a one-line edit.

2. Pull and restart:

   ```bash
   docker compose pull
   docker compose up -d
   ```

   `pull` downloads the new image while the old containers keep running, so a
   wrong tag or a registry problem fails before anything is restarted. `up -d`
   then recreates only the services whose image changed.

3. Check that it came up:

   ```bash
   docker compose ps
   docker compose logs --tail=50 web async cron
   ```

   The Cachet status page should report all components as operational.

### Migrations, static files and the search index

`docker-entrypoint.sh` runs these steps when `web` starts, depending on its
environment variables (set in the compose file or `docker/app.env`):

| Variable | When `yes`, on every start of `web` |
|---|---|
| `DJANGO_MIGRATE` | `manage.py migrate` |
| `DJANGO_COLLECT_STATIC` | `manage.py collectstatic` |
| `DJANGO_INDEX_CONTENT` | `manage.py search_index -f --rebuild` (rebuilds every Elasticsearch index, can take a while) |

If migrations are not run automatically and the release has any, run them after
`up -d`:

```bash
docker compose exec web python manage.py migrate
```

## Rolling back

Set `SCRATCH_VERSION` in `.env` back to the previous version and run the same
`docker compose pull` and `docker compose up -d`. Migrations are not reversed by
this. If the release added any, check that the old code still works with the new
schema, or migrate back explicitly
(`python manage.py migrate app <previous_migration>`) before switching images.

## One-time setup (only when we switched from dockerhub to GitHub packages)

- **Organization settings:** GitHub Actions must be allowed to create packages
  for the `eaudeweb` organization. The first tag push creates the `scratch`
  package.
- **Access from production:** either make the `scratch` package public (the
  repository already is), or log in once on the server with a personal access
  token that has the `read:packages` scope:

  ```bash
  echo <token> | docker login ghcr.io -u <github-user> --password-stdin
  ```

- **Production compose file:** switch `image:` from `eaudeweb/scratch:...` (Docker
  Hub) to `ghcr.io/eaudeweb/scratch:${SCRATCH_VERSION}` for `web`, `async` and
  `cron`.

Images up to `1.0.61` are on Docker Hub as `eaudeweb/scratch`. Docker Hub no
longer receives new versions.
