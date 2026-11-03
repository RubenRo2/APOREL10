"""Aplicación para crear, guardar, cargar y usar modelos de regresión."""

from importlib.metadata import version

__version__ = version("aporel10")


def main() -> None:
    # Se importa aquí dentro para que importar el paquete (por ejemplo, desde
    # las pruebas) no cargue la interfaz gráfica.
    from aporel10.gui import ejecutar

    ejecutar()