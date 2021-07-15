#!/bin/sh -e

./scripts/check_migrations.sh
pytest "${@:-defivelo}" "${@:-apps}"
flake8 defivelo apps
