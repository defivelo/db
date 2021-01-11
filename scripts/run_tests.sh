#!/bin/sh -e

./scripts/check_migrations.sh
pytest "${@:-defivelo}"
flake8 defivelo
