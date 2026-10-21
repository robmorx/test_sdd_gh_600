"""Punto de entrada para `python -m devlog`."""

from __future__ import annotations

from devlog.cli import app


def main() -> None:
    """Ejecuta la aplicacion de linea de comandos."""
    app()


if __name__ == "__main__":  # pragma: no cover -Point de entrada del modulo
    main()
