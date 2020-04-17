# Utils

Carpeta con herramientas y utilidades referidas al proyecto.



## Shell

`./shell.py` es una interface simple de linea de comandos desarrollada en `python3` que permite interactuar con el *smart contract* de este proyecto. 

 ![](images/shell.gif)

`./requirements.txt` es el listado de los `packages` requeridos por  `./shell.py`. se pueden instalar corriendo el comando:

```shell
$ pip3 install -r requirements.txt
```
Otra opción es usar `./shell_in_docker.sh` que termina corriendo `./shell.py` dentro de un contenedor de `docker`. La primera vez que corra `./shell_in_docker.sh` demorara varios minutos ya que debe construir la imagen de `docker`. Se puede [ver un cast](https://asciinema.org/a/dO7kcTPaIj5Q6UXe97MYHQ4eK)  en `asciinema.org` de como sería la ejecución por primera vez.

Por otro lado el archivo `./shell.json` es quien guarda todos los datos utilizados por `./shell.py`. Las claves privadas también se guardan en este archivo pero están encriptadas.



## Remixd

`./remixd.sh` proporciona una conexión bidireccional entre la computadora local y `Remix-IDE`  [https://remix.ethereum.org](https://remix.ethereum.org) haciendo uso de `remixd` y compartiendo con el IDE la carpeta `source/` de este proyecto.



## Cast varios

Los archivos en la carpeta `casts` son los cast subidos a `asciinema.org` y el script `shell_make_cast.sh` es para simplificarme la toma de cast de `shell.py`



