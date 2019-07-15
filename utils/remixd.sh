#!/usr/bin/env bash

# Parametros
SOURCE=../source
URL=https://remix.ethereum.org

# Compruebo la disponibilidad de comandos
function check () {
    if ! [ -x "$(command -v $1)" ]; then
        echo "Error: '$1' is not installed." >&2
        exit 1
    fi
}
check 'remixd'
check 'dirname'

# Me paro en el directorio de trabajo
cd "$(dirname "$0")"

# Corro remixd
remixd -s $SOURCE --remix-ide $URL &
echo remixd PID=$!
