# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Scratch is a Django 4.1 app (single Django app: `app/`, project package: `scratch/`) that scrapes public procurement tenders and contract awards from **TED** (EU), **UNGM** (UN) and **IUCN**, indexes them in Elasticsearch, and emails users about new tenders, keyword matches, favorites, deadlines and renewals. Login is via LDAP (`django-auth-ldap`) plus the default model backend.

## Running locally (Docker)

The stack is defined in `docker-compose.yml`: `web` (uWSGI on :8000), `async` (django-q `qcluster`), `cron`, `db` (Postgres 15), `elasticsearch` (7.17), `redis`, `tika`, `smtp`, plus Cachet status-page services. Setup:

```bash
cp docker-compose.override.yml.example docker-compose.override.yml
for f in app db redis tika cachet; do cp docker/$f.env.example docker/$f.env; done   # LDAP vars in app.env must be filled manually
docker-compose up -d
docker compose exec web sh
python manage.py migrate
python manage.py load_initial_data        # CPV codes, TED countries, UNSPSC codes (--reverse to remove)
python manage.py runserver 0.0.0.0:8000
```

If Elasticsearch fails bootstrap checks: `sudo sysctl -w vm.max_map_count=262144`. Rebuild the search index with `python manage.py search_index -f --rebuild` (the entrypoint does this when `DJANGO_INDEX_CONTENT=yes`).

All configuration comes from environment variables read via `getenv.env(...)` in `scratch/settings.py`.

## Tests

Tests need a reachable Postgres and Elasticsearch (Elasticsearch documents are synced on model save).

```bash
python manage.py test --settings=scratch.test_settings                         # all
python manage.py test app.tests.test_ted_parser --settings=scratch.test_settings  # one module
python manage.py test app.tests.test_ted_parser.TestClassName.test_method --settings=scratch.test_settings
```

- Test fixtures (sample TED XML, UNGM/IUCN HTML, PDFs/DOCX) live in `app/tests/parser_files/`; model factories are in `app/factories.py` (factory_boy).
- Tests touching `Keyword` should extend `app.tests.base.BaseTestCase`, which disconnects the Keyword post_save/post_delete signals (otherwise they enqueue a django-q task that re-saves every tender).
- CI (`.github/workflows/tests.yml`, on pull requests to and pushes to `master`) runs `./manage.py check` then `./manage.py test app/tests --settings=scratch.test_settings` against Postgres, Elasticsearch and Redis service containers, and builds the production image without pushing it (catches Dockerfile/`requirements-dep.txt` breakage). `.github/workflows/docker.yml` builds and pushes the image to GHCR on version tags; see `Release.md`.

There is no configured linter/formatter.

## Architecture

**Ingestion pipeline.** Each source has a worker/parser in `app/parsers/` (`ted.py`: `TEDWorker`/`TEDParser`; `ungm.py`: `UNGMWorker`; `iucn.py`: `IUCNWorker`) and a management command that drives it (`update_ted`, `update_ungm`, `update_iucn`, each with `--days_ago`). Without `--days_ago`, workers resume from the last `WorkerLog` entry for that source.
- TED downloads daily XML archives (using `TEDReleaseCalendar` to know release dates) and parses both the legacy TED XML schema and the newer eForms **UBL** schema (`TEDParser.is_ubl_format` picks the path; `_parse_notice` vs `_parse_ubl_notice`, and separate award-update methods for each). Changes to TED parsing usually need to be handled in both paths.
- UNGM/IUCN scrape HTML with BeautifulSoup; IUCN also extracts text from PDF/DOCX notices.
- Tender documents are downloaded into `TenderDocument` (`MEDIA_ROOT/documents`); their text is extracted via the Tika server for full-text search (`add_documents` re-downloads missing files).
- Update commands are wrapped in `@log_tenders_update(TenderSource.X)` (`app/utils.py`), which opens/resolves an incident in Cachet; on failure they call `send_error_email`.

**Keyword matching.** `Tender.save()` scans title/description for `Keyword` values and sets `has_keywords`/`keywords`. Adding or deleting a `Keyword` triggers (via signals wired in `app/apps.py` → `app/signals.py`) an async django-q task that re-saves all tenders.

**Search.** `app/documents.py` defines django-elasticsearch-dsl indices `tenders`, `awards`, `tender_documents` (auto-synced from the models). The search view in `app/views/tenders.py` queries all three.

**Notifications.** `app/notifications.py` builds emails from templates in `app/templates/mails/`; shared logic for the `notify_*` commands is in `app/management/commands/base/notify.py`. Commands support a `--digest` mode. Scheduled runs are defined in `crontab` (executed by the `cron` container).

**Running commands from the UI.** The management page (`ManagementView` in `app/views/management.py`) lists commands from `settings.RUNNABLE_COMMANDS` and lets superusers run them as django-q async tasks, tracked in the `Task` model. To expose a command there, add it to `RUNNABLE_COMMANDS` and have it subclass `BaseParamsUI` (`app/management/commands/base/params.py`), overriding `get_parameters()` to describe its form inputs (names must match the argparse option names).

**Views.** List pages are rendered server-side, with data loaded by DataTables-style AJAX endpoints that subclass `BaseAjaxListingView` (`app/views/base.py`), which handles filtering, ordering (`order_fields` by column index) and pagination.

**Status server.** `status/server.py` runs a tiny HTTP server on :8080 in each container as a health check for the Cachet URL monitor (`config/`).
