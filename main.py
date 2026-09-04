"""Entry point del aplicativo.

Ejecuta la UI del Panel principal.
"""

from __future__ import annotations

from src.ui.panel import Panel


def main() -> None:
    """Inicia la aplicación."""
    panel = Panel()
    panel.ejecutar()


if __name__ == "__main__":
    main()
