# DevLog CLI

Consola para guardar notas de desarrollo en SQLite, buscarlas por etiqueta y exportarlas
a Markdown. Funciona totalmente en local: sin cuentas, sin servidor y sin conexion a
internet.

## Requisitos

- Python 3.11 o superior
- [uv](https://docs.astral.sh/uv/) (recomendado) o `venv` + `ensurepip`

## Instalacion

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Alternativa sin `uv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m ensurepip --upgrade
python3 -m pip install -e ".[dev]"
```

## Uso

```bash
devlog add "CORS error in staging" --content "El servidor rechaza el preflight OPTIONS." --tag bug --tag api
devlog add "Idea: cachear respuestas" -t idea
devlog list
devlog search bug
devlog search bug api
devlog export --output notas.md
```

Tambien se puede ejecutar como modulo: `python -m devlog --help`.

### Comandos

| Comando | Que hace |
|---------|----------|
| `devlog add TITULO` | Crea una nota. `--content/-c` para el cuerpo, `--content-file RUTA` para leerlo de un archivo (`-` lee la entrada estandar), `--tag/-t` repetible para las etiquetas. |
| `devlog list` | Muestra todas las notas, de la mas nueva a la mas antigua, una por linea. |
| `devlog search ETIQUETA...` | Muestra las notas que tienen **todas** las etiquetas indicadas. La coincidencia es exacta. |
| `devlog export` | Exporta todas las notas a un archivo Markdown. `--output/-o` elige la ruta y `--force` sobrescribe sin preguntar. |

### Codigos de salida

| Codigo | Significado |
|--------|-------------|
| `0` | Operacion completada (incluye un listado vacio y una exportacion sin notas). |
| `1` | Error operativo: almacen danado o bloqueado, destino no escribible. |
| `2` | Error de uso o de validacion: titulo vacio, argumentos incorrectos. |
| `3` | La busqueda no encontro resultados. |

## Donde se guardan las notas

Las notas viven en un unico archivo SQLite: `~/.devlog/notes.db`, el mismo desde
cualquier carpeta. La ruta se puede sobrescribir con la variable de entorno
`DEVLOG_DB_PATH`, que es lo que usan las pruebas para no tocar nunca tus notas reales:

```bash
DEVLOG_DB_PATH=/tmp/devlog-pruebas.db devlog list
```

La herramienta crea el archivo y su esquema la primera vez, y nunca borra, reinicia ni
reconstruye un almacen existente.

## Formato de la exportacion

```markdown
# Notas de DevLog

2026-10-21 09:32 · 2 notas

---

## #12 · CORS error in staging

- **Creado**: 2026-10-21 09:30
- **Etiquetas**: `api`, `bug`

El servidor rechaza el preflight OPTIONS.
Revisar el header Access-Control-Allow-Origin.
```

El cuerpo de cada nota se escribe tal cual, con sus saltos de linea y sus listas.

## Pruebas

```bash
source .venv/bin/activate
pytest -q
```

Las pruebas usan un almacen temporal propio y no necesitan red.
