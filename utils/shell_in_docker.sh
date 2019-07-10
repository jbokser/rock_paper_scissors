#!/usr/bin/env bash

# Parametros
IMG_NAME=rock_paper_scissors

# Compruebo la disponibilidad de comandos
function check () {
    if ! [ -x "$(command -v $1)" ]; then
        echo "Error: '$1' is not installed." >&2
        exit 1
    fi
}
check 'docker'
check 'dirname'
check 'realpath'

# Compruebo si tengo permisos para correr docker
if ! [ -w /var/run/docker.sock ] ; then
     echo "Do not have permission to run docker." >&2
     echo "Maybe should try sudo." >&2
     exit 1
fi

# Me paro en el directorio de trabajo
DIR="$(dirname "$0")"
FULL_DIR="$(realpath "$DIR")"
cd $DIR

# Si la imagen de docker no existe la ensamblo con un DockerFile
if [[ "$(docker images -q $IMG_NAME:latest 2> /dev/null)" == "" ]]; then
    docker build -t $IMG_NAME:latest -f- $DIR <<EOF
FROM ubuntu:18.04
RUN apt-get update && apt-get install -y python3 python3-pip
COPY shell.json /opt
COPY shell.py /opt
COPY requirements.txt /opt
RUN pip3 install -r /opt/requirements.txt
RUN rm -f /opt/requirements.txt
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8
CMD /opt/shell.py
EOF
fi

# Corro una instancia de docker interactiva y desechable
docker run -it --rm \
    -v $FULL_DIR/shell.json:/opt/shell.json \
    -v $FULL_DIR/shell.py:/opt/shell.py \
    $IMG_NAME /opt/shell.py "$@"
