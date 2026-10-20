"""Interfaz gráfica de la aplicación (PySide6)."""

import sys
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                               QMainWindow, QPushButton, QTableWidget,
                               QTableWidgetItem, QVBoxLayout, QWidget)

from aporel10.data_loader import cargar_datos

# Solo se muestran en el explorador los formatos que admite data_loader.
FILTRO_DATOS = "Datos (*.csv *.xlsx *.xls *.sqlite *.db)"


class VentanaPrincipal(QMainWindow):
    """Ventana principal de la aplicación."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("APOREL10 - Regresión lineal")
        self.resize(1000, 600)

        # Datos cargados. Los usarán los pasos siguientes del programa
        # (selección de columnas, separación, creación del modelo...).
        self.datos: pd.DataFrame | None = None
        self.ruta_datos: Path | None = None

        self.boton_cargar = QPushButton("Cargar datos...")
        self.etiqueta_ruta = QLabel("Ningún archivo cargado")
        self.tabla = QTableWidget()

        fila_carga = QHBoxLayout()
        fila_carga.addWidget(self.boton_cargar)
        fila_carga.addWidget(self.etiqueta_ruta, stretch=1)

        contenido = QWidget()
        layout = QVBoxLayout(contenido)
        layout.addLayout(fila_carga)
        layout.addWidget(self.tabla)
        self.setCentralWidget(contenido)

        self.boton_cargar.clicked.connect(self.elegir_archivo)

    def elegir_archivo(self) -> None:
        """Abre el explorador de archivos para elegir un dataset."""
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar dataset", "", FILTRO_DATOS)
        if not ruta:
            return  # el usuario cerró el explorador sin elegir nada
        self.cargar_archivo(ruta)

    def cargar_archivo(self, ruta: str) -> None:
        """Lee el archivo con el módulo de importación y muestra sus datos."""
        datos = cargar_datos(ruta)
        self.datos = datos
        self.ruta_datos = Path(ruta).resolve()
        self.etiqueta_ruta.setText(str(self.ruta_datos))
        self.mostrar_tabla(datos)

    def mostrar_tabla(self, datos: pd.DataFrame) -> None:
        """Muestra todas las filas y columnas de los datos en la tabla."""
        self.tabla.clear()
        self.tabla.setRowCount(len(datos))
        self.tabla.setColumnCount(len(datos.columns))
        self.tabla.setHorizontalHeaderLabels(
            [str(columna) for columna in datos.columns])
        for fila, valores in enumerate(datos.itertuples(index=False)):
            for columna, valor in enumerate(valores):
                texto = "" if pd.isna(valor) else str(valor)
                self.tabla.setItem(fila, columna, QTableWidgetItem(texto))


def ejecutar() -> None:
    """Abre la ventana principal y espera a que el usuario la cierre."""
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())