[![Build Status](https://travis-ci.org/defivelo/db.svg?branch=master)](https://travis-ci.org/defivelo/db)

# L’Intranet Défi Vélo

Ce dépôt contient tout ce qui est nécessaire à faire tourner l’Intranet Défi Vélo.

Il a pour objectif de simplifier et améliorer la gestion des mois, sessions,
Qualifs, établissements, etc, et vise principalement à être utilisée par
les collaborateurs du Défi Vélo, aux différents échelons cantonaux et
inter-cantonaux.

## Local setup
1. Clone the project:

```
git clone --recursive git@gitlab.liip.ch:swing/defivelo/intranet
```

2. Open the file `docker-compose.override.example.yml` and follow the instructions in it

3. Run the command `INITIAL=1 docker-compose up`

This will start the containers and set up the initial data. To access the site,
follow the instructions in the `docker-compose.override.example.yml` file.

Note the `INITIAL` flag should not be set for subsequent container starts unless
you want to reset the database.

## Roles & permissions
After adding a new permission in `defivelo/roles.py`, run the following in vagrant to apply them:
```
./manage.py sync_roles --reset_user_permissions
```

## Automated tests

To run backend tests and lint checks, run `scripts/run_tests.sh` in the `backend` container:
* `docker-compose exec backend scripts/run_tests.sh`
* or `docker-compose run --rm backend scripts/run_tests.sh` if the `backend` service is not already running

CLI arguments are forwarded to `pytest`.
For example, running tests with `scripts/run_tests.sh cche --reuse-db` avoids
re-creating the database from scratch on each run.
