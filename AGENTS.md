# AGENTS.md

This file provides guidance to coding agents working in this repository.

## Project

Django intranet for **Défi Vélo**, a Swiss bike-education organization. Manages seasons, sessions, qualifications, organizations, users and timesheets across Swiss cantons. UI is in French (`fr`) and German (`de`); user-visible strings must use `gettext_lazy` (`_()`).

## Stack

- Python 3.11, Django 4.2, PostgreSQL 15
- Auth: `django-allauth` (email-only login, no signups — see `defivelo/accounts.py`)
- Permissions: `django-role-permissions` (see `defivelo/roles.py`)
- Forms: `django-crispy-forms` + `bootstrap3`
- Translations: `django-parler` (model translation), Django i18n (UI)
- Lint/format: `ruff` (config in `pyproject.toml`, line length 88)
- Tests: `pytest` + `pytest-django` (`defivelo/settings/test.py`)
- Local dev runs in Docker; `just` wraps `docker compose exec backend …`

## Local setup

Clone **with submodules** (`locale/`, `ext/bootstrap-datetimepicker`, `ext/moment` are submodules — see `.gitmodules`):
```sh
git clone --recursive <repo>
```
Copy `docker-compose.override.example.yml` to `docker-compose.override.yml` and uncomment one of its configurations (minimal vs. pontsun). First boot uses the `INITIAL=1` flag to install deps and migrate:
```sh
INITIAL=1 docker compose up
```
Do **not** set `INITIAL=1` on subsequent starts unless you want to reset the database (the flag is read in `entrypoint.sh`).

## Common commands

All commands assume the `backend` container is running (`just start` / `docker compose up`). Use `docker compose run --rm backend …` if it is not.

```sh
just start                  # docker compose up -d
just manage <cmd>           # ./manage.py <cmd>   (aliases: dj, django)
just migrate                # ./manage.py migrate
just makemigrations         # ./manage.py makemigrations  (alias: mm)
just shell_plus             # ./manage.py shell_plus  (alias: shell, sp)
just test [pytest args]     # pytest                 (alias: t)
just lint                   # ruff check + ruff format --check
just format                 # ruff format + ruff check --fix  (alias: fix)
just translate              # makemessages (django + djangojs) + compilemessages
just compile                # pip-compile all requirements/*.in
just install                # pip install -r requirements/dev.txt
```

The full CI test sequence is `scripts/run_tests.sh` — it runs `scripts/check_migrations.sh` (fails on missing migrations), then `pytest defivelo apps`, then `ruff format --check` and `ruff check`. To run a single test: `just test path/to/test_file.py::TestClass::test_name --reuse-db` (`--reuse-db` avoids recreating the DB).

After changing `defivelo/roles.py`, sync permissions:
```sh
docker compose exec backend ./manage.py sync_roles --reset_user_permissions
```

To work against a production-like dataset: `docker compose exec backend fab prod import-db && ./manage.py migrate && ./manage.py set_fake_passwords` (sets every password to `password`).

## Architecture

### Settings layering
`defivelo/settings/{base,dev,staging,test}.py`. `base.py` reads everything from env vars via `get_env_variable` (see `defivelo/settings/__init__.py`). `manage.py` defaults to `dev`; pytest is pinned to `test` via `setup.cfg`. Env files live in `envdir/` (and `envdir/tests/` for tests).

### Apps layout
`INSTALLED_APPS` auto-discovers every directory under `apps/` (`base.py`). Key apps:

- **`apps.challenge`** — domain core. Models split across `models/{season,session,qualification,availability,invoices,settings}.py`. A `Season` groups `Session`s; each Session has `Qualification`s (rides); `HelperSessionAvailability` tracks helper signups; `Invoice`/`InvoiceLine` handles billing; `AnnualStateSetting` holds per-canton per-year config. State machine for seasons in `apps/common/__init__.py` (`DV_SEASON_STATE_*`: planning → open → running → finished → archived) — different roles get different RW access at each state.
- **`apps.orga`** — Organizations (schools/establishments).
- **`apps.user`** — User profiles, custom export, signals; custom `createsuperuser` in `apps/user/management/commands/`.
- **`apps.salary`** — Timesheets and yearly invoicing (`timesheets_overview.py`).
- **`apps.article`** — Homepage news.
- **`apps.info`** — Static info pages.
- **`apps.common`** — Shared constants/forms/views. Notably `DV_STATES` (the active Swiss cantons), `DV_STATE_COLORS`, season constants, language constants.
- **`apps.email_outbox`** — Mounted under `/admin/` in `defivelo/urls.py`.

`defivelo/` itself holds project glue: `urls.py`, `roles.py`, `accounts.py` (allauth adapter that disables signup), `bootstrap3.py` (custom field renderers), `context_processors.py`, `templatetags/`, project-wide `views/` and `templates/`.

### URL conventions
Public-by-default routing uses `i18n_patterns` (locale prefix in URL) for `season/`, `orga/`, `user/`, `info/`, `finance/`. Admin, login, license and `article/` are mounted without locale prefix. `django-stronghold` middleware forces login on everything except `STRONGHOLD_PUBLIC_URLS` (admin, accounts, AGPL).

### Permissions & cantons
Four roles in `defivelo/roles.py`: `Collaborator` (helpers), `Coordinator` (school-side), `StateManager` (per-canton project lead), `PowerUser` (bureau / all cantons). `has_permission` and `user_cantons` are memoized — clear cache implications when changing permissions in tests.

Most data is canton-scoped. `user_cantons(user)` returns either `DV_STATES` (PowerUser) or the user's managed cantons (StateManager via `user.managedstates`). Querysets in views typically filter by these.

### Templates & assets
Templates in each app's `templates/`, plus project-wide ones in `defivelo/templates/`. `django-compressor` with `sassc` compiles SCSS at request time (offline compression disabled — see `COMPRESS_OFFLINE = False` comment in `base.py` about dynamic blocks). The `bootstrap3` field renderers are customized in `defivelo/bootstrap3.py`.

## Domain glossary

Field/variable names follow these business terms — knowing them makes the models readable. All authoritative definitions live in `defivelo/roles.py` and `apps/challenge/models/qualification.py`.

**Roles** (`defivelo/roles.py:45-148`):
- **Collaborator** — field helpers; "Moniteur·trice 1, 2 ou Intervenant·e".
- **Chargé·e de projet** (`state_manager`) — manages one or more cantons. Cantons come from `user.managedstates` via `user_cantons(user)`.
- **Coordina·teur·trice** (`coordinator`) — school-side; "Coordinateur d'établissement".
- **Bureau de coordination** (`power_user`) — central office; `cantons_all=True`.

**Session structure** (`apps/challenge/models/`): a `Season` groups `Session`s; each `Session` runs for an `Organization` (school) on a day and contains one or more `Qualification`s (typically one per class).

**People on a Qualif** (`qualification.py:96-191`):
- **Moniteur·trice 2 (M2)** — `Qualification.leader`, FK, exactly one. Limited to `profile.formation == FORMATION_M2`. Lead monitor.
- **Moniteur·trice 1 (M1)** — `Qualification.helpers`, M2M. Junior monitors. The related-name `qualifs_mon1` on `User` refers to this.
- **Intervenant·e** — `Qualification.actor`, FK, one. Limited to users with a non-empty `profile.actor_for` (category-C activities).
- **n_helpers** — `MonitorNumberEnum` (1/2/3): 1 → just M2; 2 → M2 + 1×M1; 3 → M2 + 2×M1 (`qualification.py:75-93`).
- **Moniteur·trice + / Photographe** — `Session.superleader`, optional, scoped to the whole session (`session.py:69-71`).
- **Moniteur·trice de secours** — backup; an availability status only (`CHOSEN_AS_REPLACEMENT`), not a Qualif FK.

**Activities** (`qualification.py:38-46`) — three categories per Qualif: **A · Agilité**, **B · Mécanique**, **C · Rencontre** (the slot the Intervenant fills).

**Availability vocabulary** (`apps/challenge/__init__.py:34-46`) mirrors the same terms via `CHOSEN_AS_*`: `_ACTOR`, `_HELPER` (=M1), `_LEADER` (=M2), `_REPLACEMENT`.

**Note on naming overlap**: `Season.leader` is also labelled "Chargé·e de projet" but here it's the FK pointing at the `state_manager` user responsible for the season — not an M2. Same word, different layer.

## Conventions

- **Always run `just lint` (or `just format`) before committing** — CI fails on `ruff check` or `ruff format --check`. Migrations directories and `defivelo/settings/*.py` have ruff exceptions (see `pyproject.toml`).
- **Migrations**: never leave model changes without a migration; `scripts/check_migrations.sh` enforces this in CI. Migration files are excluded from lint/format.
- **Translations** are managed by **Weblate** (`translate.liip.ch`) — do **not** hand-edit `.po` files. The shape of the workflow, as evidenced by git history:
  - `locale/` is a git submodule pointing at `intranet-i18n.git`. Weblate reads source strings (likely from the `translation` branch of this repo) and pushes translator output into that submodule.
  - An automation account `i18n writing to this repo` then lands `i18n: Auto update of ./locale` commits — one-line submodule-pointer bumps (`locale | 2 +-`) — onto multiple long-lived branches (`main`, `translation`, `staging`). That is how fresh translations reach the app. (Historically these commits were authored directly by `Weblate server (translate.liip.ch)`; the role moved to the bot account in 2024.)
  - A long-lived **`translation`** branch exists for translation-only hotfixes (small submodule-pointer bumps that need to land outside the normal feature-branch flow).
  - When you add user-facing strings, mark them with `gettext_lazy` and run `just translate` to refresh source `.po`s in the submodule. Translators then work in Weblate; the pointer bump comes back automatically. Don't bump the submodule pointer in a feature branch unless the task is specifically about translations — the bot handles routine bumps.
- **Imports** use ruff's isort with sections: future / stdlib / **django** / third-party / **first-party (`defivelo`)** / local. `apps` is third-party for isort (configured via `known-first-party = ["defivelo"]` only).
- **Inclusive French**: user-facing French strings use **midpoint inclusive notation** (e.g. `Moniteur·trice`, `Chargé·e de projet`, `Intervenant·e`, `Coordina·teur·trice`, `participant·es`, `enseignant·e`). Use the typographic middle dot `·` (U+00B7), not a period or hyphen. Match the surrounding model `verbose_name`s when adding new strings. (See DEFIVELO-282 / DEFIVELO-283 in git history for the inclusive-language rollout.)
