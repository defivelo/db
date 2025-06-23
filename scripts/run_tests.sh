#!/bin/sh -e

./scripts/check_migrations.sh
pytest "${@:-defivelo}" "${@:-apps}"

ruff format --check defivelo apps fabfile.py
ruff check defivelo apps fabfile.py
