#!/bin/sh -e

./scripts/check_migrations.sh
[ "$#" -eq 0 ] && set -- defivelo apps
pytest -n auto "$@"

ruff format --check defivelo apps fabfile.py
ruff check defivelo apps fabfile.py
