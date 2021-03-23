#!/bin/bash


if [ ! -e "$VIRTUAL_ENV/bin" ]; then
    echo "Creating virtualenv at \"$VIRTUAL_ENV\""
    python -m venv "$VIRTUAL_ENV"
fi

if [ "$INITIAL" = "1" ]; then
    if [ ! -e "requirements/dev.txt" ]; then
        pip install pip-tools
        pip-compile requirements/dev.in
    fi

    pip install -r requirements/dev.txt

    if [ ! -e "requirements/test.txt" ]; then
        pip-compile requirements/test.in
    fi
fi

exec "${@}"
