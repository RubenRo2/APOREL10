"""Interfaz gráfica de la aplicación (PySide6)."""

import sys

from PySide6.QtWidgets import QApplication, QMainWindow


class VentanaPrincipal(QMainWindow):
    """Ventana principal de la aplicación."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("APOREL10 - Regresión lineal")
        self.resize(1000, 600)


def ejecutar() -> None:
    """Abre la ventana principal y espera a que el usuario la cierre."""
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())