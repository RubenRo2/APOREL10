"""Interfaz gráfica de la aplicación (PySide6)."""

import sys
from pathlib import Path

from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                               QMainWindow, QPushButton, QVBoxLayout, QWidget)

# Solo se muestran en el explorador los formatos que admite data_loader.
FILTRO_DATOS = "Datos (*.csv *.xlsx *.xls *.sqlite *.db)"


class VentanaPrincipal(QMainWindow):
    """Ventana principal de la aplicación."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("APOREL10 - Regresión lineal")
        self.resize(1000, 600)

        self.boton_cargar = QPushButton("Cargar datos...")
        self.etiqueta_ruta = QLabel("Ningún archivo cargado")

        fila_carga = QHBoxLayout()
        fila_carga.addWidget(self.boton_cargar)
        fila_carga.addWidget(self.etiqueta_ruta, stretch=1)

        contenido = QWidget()
        layout = QVBoxLayout(contenido)
        layout.addLayout(fila_carga)
        layout.addStretch()
        self.setCentralWidget(contenido)

        self.boton_cargar.clicked.connect(self.elegir_archivo)

    def elegir_archivo(self) -> None:
        """Abre el explorador de archivos para elegir un dataset."""
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar dataset", "", FILTRO_DATOS)
        if not ruta:
            return  # el usuario cerró el explorador sin elegir nada
        self.etiqueta_ruta.setText(str(Path(ruta).resolve()))


def ejecutar() -> None:
    """Abre la ventana principal y espera a que el usuario la cierre."""
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())