export BACKEND_CONTAINER := "backend"

set allow-duplicate-recipes
set positional-arguments

default:
  just --list

# Run the development server
start *args:
  docker compose up "$@" -d

# Run bash in backend container
alias exec := bash
bash *args:
  docker compose exec {{BACKEND_CONTAINER}} bash "$@"

alias django := manage
alias dj := manage
# Run a Django manage.py command
manage *args:
  docker compose exec {{BACKEND_CONTAINER}} python manage.py "$@"

# Run manage.py shell_plus
alias shell := shell_plus
alias sp := shell_plus
shell_plus *args:
  docker compose exec {{BACKEND_CONTAINER}} python manage.py shell_plus "$@"

alias t := test
# Run the tests suite
test *args:
  docker compose exec {{BACKEND_CONTAINER}} pytest "$@"

alias validate := lint
alias l := lint
# Lint the code
lint:
  docker compose exec {{BACKEND_CONTAINER}} ruff check defivelo apps fabfile.py
  docker compose exec {{BACKEND_CONTAINER}} ruff format --check defivelo apps fabfile.py

alias fix := format
# Fix styling offenses and format code
format *args:
  docker compose exec {{BACKEND_CONTAINER}} ruff format defivelo apps fabfile.py "$@"
  docker compose exec {{BACKEND_CONTAINER}} ruff check --select I --fix defivelo apps fabfile.py

alias c := compile
# Compile the requirements files
compile:
  docker compose exec {{BACKEND_CONTAINER}} bash -c 'cd requirements; pip-compile base.in'
  docker compose exec {{BACKEND_CONTAINER}} bash -c 'cd requirements; pip-compile dev.in'
  docker compose exec {{BACKEND_CONTAINER}} bash -c 'cd requirements; pip-compile staging.in'
  docker compose exec {{BACKEND_CONTAINER}} bash -c 'cd requirements; pip-compile test.in'

compile-upgrade:
  docker compose exec {{BACKEND_CONTAINER}} bash -c 'cd requirements; pip-compile --upgrade base.in'
  docker compose exec {{BACKEND_CONTAINER}} bash -c 'cd requirements; pip-compile --upgrade dev.in'
  docker compose exec {{BACKEND_CONTAINER}} bash -c 'cd requirements; pip-compile --upgrade staging.in'
  docker compose exec {{BACKEND_CONTAINER}} bash -c 'cd requirements; pip-compile --upgrade test.in'

alias i := install
# Install pip and npm dependencies
install file='requirements/dev.txt':
  docker compose exec {{BACKEND_CONTAINER}} pip install -r {{file}}

alias mm := makemigrations
# Generate database migrations
makemigrations *args:
  docker compose exec {{BACKEND_CONTAINER}} python manage.py makemigrations "$@"

alias m := migrate
# Migrate the database
migrate *args:
  docker compose exec {{BACKEND_CONTAINER}} python manage.py migrate "$@"

make *args:
  docker compose exec {{BACKEND_CONTAINER}} make "$@"

fab *args:
  docker compose exec {{BACKEND_CONTAINER}} fab "$@"

alias messages := translate
# Make messages and compile them
translate:
	docker compose exec {{BACKEND_CONTAINER}} python manage.py makemessages -a -i "requirements/*" -i "node_modules/*"
	docker compose exec {{BACKEND_CONTAINER}} python manage.py makemessages -a -d djangojs -i "node_modules/*" -i "static/*"
	docker compose exec {{BACKEND_CONTAINER}} python manage.py compilemessages

import? 'override.justfile'
