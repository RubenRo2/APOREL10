"""Interfaz gráfica de la aplicación (PySide6)."""

import sys
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QMessageBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget, QListWidget, QComboBox)

from aporel10.data_loader import ErrorImportacionDatos, cargar_datos
from aporel10.column_selector import ErrorSeleccionColumnas, validar_seleccion


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

        self.lista_entradas = QListWidget()
        self.lista_entradas.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.combo_salida = QComboBox()
        self.boton_validar = QPushButton("Validar variables")

        self.entrada_porcentaje = QLineEdit("20")
        self.entrada_porcentaje.setPlaceholderText("1-99")
        self.entrada_porcentaje.setMaximumWidth(60)
        self.etiqueta_entrenamiento = QLabel("Entrenamiento: 80 %")
        self.entrada_semilla = QLineEdit("42")
        self.entrada_semilla.setPlaceholderText("Entero")
        self.entrada_semilla.setMaximumWidth(80)
        self.boton_separar = QPushButton("Separar datos")
        self.boton_separar.setEnabled(False)
        self.etiqueta_separacion = QLabel("Datos sin separar")

        fila_carga = QHBoxLayout()
        fila_carga.addWidget(self.boton_cargar)
        fila_carga.addWidget(self.etiqueta_ruta, stretch=1)

        fila_variables = QHBoxLayout()
        #Añado stretch para que se vea bonito
        fila_variables.addWidget(QLabel("Entradas (Features):"), stretch=0)
        fila_variables.addWidget(self.lista_entradas, stretch=2)
        fila_variables.addWidget(QLabel("Salida (Target):"), stretch=0)
        fila_variables.addWidget(self.combo_salida, stretch=3)
        fila_variables.addWidget(self.boton_validar, stretch=0)

        fila_separacion = QHBoxLayout()
        fila_separacion.addWidget(QLabel("Test (%):"))
        fila_separacion.addWidget(self.entrada_porcentaje)
        fila_separacion.addWidget(self.etiqueta_entrenamiento)
        fila_separacion.addWidget(QLabel("Semilla:"))
        fila_separacion.addWidget(self.entrada_semilla)
        fila_separacion.addWidget(self.boton_separar)
        fila_separacion.addWidget(self.etiqueta_separacion, stretch=1)

        contenido = QWidget()
        layout = QVBoxLayout(contenido)

        #Añado stretch (ocupa el % de la pantalla que se le pasa) para ajustar como se ve porque me parecia muy grande
        layout.addLayout(fila_carga, stretch=0)
        layout.addWidget(self.tabla, stretch=8)
        layout.addLayout(fila_variables, stretch=2)
        layout.addLayout(fila_separacion, stretch=0)

        self.setCentralWidget(contenido)

        self.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
                background-color: #3b3b3b;
                border: 1px solid #555;
            }
            QPushButton:hover {
                background-color: #505050;
                border: 1px solid #8ab4f8;
                color: #8ab4f8;
            }
            QPushButton:pressed {
                background-color: #222222;
                border: 1px solid #333;
                color: #aaaaaa;
            }
            QPushButton:disabled {
                color: #777777;
                border: 1px solid #444;
            }
            QListWidget, QComboBox, QLineEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 11px;
                outline: none;
            }
            QListWidget::item:selected {
                background-color: #8ab4f8;
                color: #111111;
                border-radius: 2px;
            }
            QListWidget::item {
                padding: 4px 8px;
                border: none;
                margin: 0px;
            }
                """)

        self.boton_cargar.clicked.connect(self.elegir_archivo)
        self.boton_validar.clicked.connect(self.validar_variables)
        self.entrada_porcentaje.textChanged.connect(
            self.actualizar_porcentaje_entrenamiento)

    def elegir_archivo(self) -> None:
        """Abre el explorador de archivos para elegir un dataset."""
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar dataset", "", FILTRO_DATOS)
        if not ruta:
            return  # el usuario cerró el explorador sin elegir nada
        self.cargar_archivo(ruta)

    def actualizar_porcentaje_entrenamiento(self, texto: str) -> None:
        """Muestra el porcentaje de entrenamiento como complementario del de test."""
        try:
            porcentaje_test = float(texto.replace(",", "."))
        except ValueError:
            self.etiqueta_entrenamiento.setText("Entrenamiento: -- %")
            return
        if not 1 <= porcentaje_test <= 99:
            self.etiqueta_entrenamiento.setText("Entrenamiento: -- %")
            return
        self.etiqueta_entrenamiento.setText(
            f"Entrenamiento: {100 - porcentaje_test:g} %")

    def cargar_archivo(self, ruta: str) -> None:
        """Lee el archivo con el módulo de importación y muestra sus datos.

        Si el archivo no se puede leer, muestra el error y deja la interfaz
        en blanco, sin los datos que hubiera cargados antes.
        """
        try:
            datos = cargar_datos(ruta)
        except ErrorImportacionDatos as error:
            self.limpiar_interfaz()
            QMessageBox.critical(self, "Error al cargar los datos", str(error))
            return
        self.datos = datos
        self.ruta_datos = Path(ruta).resolve()
        self.etiqueta_ruta.setText(str(self.ruta_datos))
        self.mostrar_tabla(datos)

        columnas = [str(col) for col in datos.columns]
        self.lista_entradas.clear()
        self.combo_salida.clear()

        self.lista_entradas.addItems(columnas)
        self.combo_salida.addItems(columnas)

    def limpiar_interfaz(self) -> None:
        """Quita el dataset de la interfaz y la deja como al abrirla."""
        self.datos = None
        self.ruta_datos = None
        self.etiqueta_ruta.setText("Ningún archivo cargado")

        # clear() only empties the cells; the row and column counts remain
        self.tabla.clear()
        self.tabla.setRowCount(0)
        self.tabla.setColumnCount(0)

        self.lista_entradas.clear()
        self.combo_salida.clear()

        self.entrada_porcentaje.setText("20")
        self.entrada_semilla.setText("42")
        self.boton_separar.setEnabled(False)
        self.etiqueta_separacion.setText("Datos sin separar")

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

    def validar_variables(self) -> None:
        """Pasa la selección del usuario a la lógica de validación."""
        if self.datos is None:
            QMessageBox.warning(self, "Atención", "Primero debes cargar un archivo de datos.")
            return

        # 1. Extraer los textos que el usuario ha seleccionado en la interfaz
        entradas_seleccionadas = [item.text() for item in self.lista_entradas.selectedItems()]
        salida_seleccionada = self.combo_salida.currentText()

        # 2. Enviar a tu función blindada con try/except
        try:
            validar_seleccion(self.datos, entradas_seleccionadas, salida_seleccionada)
            QMessageBox.information(self, "Éxito", "Las variables seleccionadas son válidas y están listas para entrenar.")
        except ErrorSeleccionColumnas as error:
            # Si la lógica detecta un fallo, mostramos el mensaje exacto que programaste
            QMessageBox.warning(self, "Error de Selección", str(error))


def ejecutar() -> None:
    """Abre la ventana principal y espera a que el usuario la cierre."""
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    ejecutar()