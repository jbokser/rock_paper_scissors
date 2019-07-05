#!/usr/bin/env bash

# Compruebo la disponibilidad de comandos
function check () {
    if ! [ -x "$(command -v $1)" ]; then
        echo "Error: '$1' is not installed." >&2
        exit 1
    fi
}
check 'asciinema'
check 'date'
check 'dirname'

# Me paro en el directorio de trabajo
cd "$(dirname "$0")"

# Parametros
TITLE="Ejemplo de uso de 'shell.py' para el contrato 'RockPaperScissors' - $(date +"%Y-%m-%d")"
CMD=./shell_in_docker.sh

# Archivos de trabajo
BASE_FILE=shell.cast
TODAY=$(date +"%Y-%m-%d-%H-%M")
OUT_FILE=$TODAY-$BASE_FILE
TMP_OUT_FILE=.$OUT_FILE

# Corro asciinema
echo "Recording '$CMD' session..."
echo
asciinema rec -i 1 -t "$TITLE" -c "$CMD" -q "$TMP_OUT_FILE" -e ''

# Paso de temporal a definitivo y borro temporal
echo Creating $OUT_FILE ...
cat "$TMP_OUT_FILE" > "$OUT_FILE"
rm -f "$TMP_OUT_FILE"
echo Done!
echo
