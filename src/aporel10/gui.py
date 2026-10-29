"""Interfaz gráfica de la aplicación (PySide6)."""

import sys
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QMessageBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget, QListWidget, QComboBox, QGroupBox)

from aporel10.data_loader import ErrorImportacionDatos, cargar_datos
from aporel10.column_selector import ErrorSeleccionColumnas, validar_seleccion
from aporel10.data_splitter import ErrorSeparacionDatos, separar_datos
from aporel10.missing_values import (
    ErrorPreprocesado,
    aplicar_preprocesado,
    detectar_valores_inexistentes,
    normalizar_columnas,
)


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

        # Confirmed column selection; None until "Validar variables" succeeds
        self.entradas: list[str] | None = None
        self.salida: str | None = None

        # Result of "Separar datos"; None until the split is done
        self.datos_entrenamiento: pd.DataFrame | None = None
        self.datos_test: pd.DataFrame | None = None

        # Later steps of the workflow, built from the current split
        self.preprocesado = None
        self.modelo = None

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

        # Controles del preprocesado
        self.grupo_preprocesado = QGroupBox("Valores inexistentes y preprocesado")
        self.grupo_preprocesado.setEnabled(False)
        layout_preprocesado = QVBoxLayout(self.grupo_preprocesado)

        # Información sobre valores inexistentes
        self.etiqueta_faltantes = QLabel(
            "Separa los datos para analizar los valores inexistentes."
        )

        self.tabla_faltantes = QTableWidget(0, 3)
        self.tabla_faltantes.setHorizontalHeaderLabels(
            ["Columna", "Entrenamiento", "Test"]
        )
        self.tabla_faltantes.setMaximumHeight(145)

        layout_preprocesado.addWidget(self.etiqueta_faltantes)
        layout_preprocesado.addWidget(self.tabla_faltantes)

        # Selección de estrategia
        fila_tratamiento = QHBoxLayout()
        fila_tratamiento.addWidget(QLabel("Tratamiento:"))

        self.combo_estrategia = QComboBox()
        self.combo_estrategia.addItem("Eliminar filas", "eliminar")
        self.combo_estrategia.addItem("Rellenar con media", "media")
        self.combo_estrategia.addItem("Rellenar con mediana", "mediana")
        self.combo_estrategia.addItem("Rellenar con constante", "constante")
        fila_tratamiento.addWidget(self.combo_estrategia)

        # Campo para el valor constante
        self.entrada_constante = QLineEdit()
        self.entrada_constante.setPlaceholderText("Valor numérico")
        self.entrada_constante.setMaximumWidth(135)
        self.entrada_constante.setEnabled(False)
        fila_tratamiento.addWidget(self.entrada_constante)

        # Botón para aplicar el preprocesado
        self.boton_aplicar = QPushButton("Aplicar preprocesado")
        self.boton_aplicar.setEnabled(False)
        fila_tratamiento.addWidget(self.boton_aplicar)
        fila_tratamiento.addStretch()

        layout_preprocesado.addLayout(fila_tratamiento)

        # Información sobre el resultado
        self.etiqueta_estado_preprocesado = QLabel("Preprocesado pendiente")
        self.etiqueta_disponibilidad_modelo = QLabel(
            "Creación del modelo: no disponible"
        )

        layout_preprocesado.addWidget(self.etiqueta_estado_preprocesado)
        layout_preprocesado.addWidget(self.etiqueta_disponibilidad_modelo)

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
        layout.addWidget(self.grupo_preprocesado, stretch=0)

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
        self.boton_separar.clicked.connect(self.separar)

        #Preprocesado
        self.boton_aplicar.clicked.connect(self.aplicar_preprocesado_gui)
        self.combo_estrategia.currentIndexChanged.connect(self.actualizar_opcion_constante)

        # Changing the selection means it has to be confirmed again
        self.lista_entradas.itemSelectionChanged.connect(self.descartar_seleccion)
        self.combo_salida.currentTextChanged.connect(self.descartar_seleccion)
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
        self.descartar_seleccion()
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
        self.descartar_seleccion()

    def descartar_seleccion(self) -> None:
        """Anula la selección confirmada; hay que validarla y separar de nuevo."""
        self.entradas = None
        self.salida = None
        self.boton_separar.setEnabled(False)
        self.invalidar_separacion()

    def invalidar_separacion(self) -> None:
        """Descarta la separación y todo lo que se haya creado a partir de ella."""
        self.datos_entrenamiento = None
        self.datos_test = None
        self.preprocesado: str | None = None
        self.modelo = None
        self.datos_listos_para_modelo = False #Indica si las columnas estan libres de nulos
        
        self.etiqueta_separacion.setText("Datos sin separar")
        self.grupo_preprocesado.setEnabled(False)
        self.tabla_faltantes.setRowCount(0)

        self.etiqueta_faltantes.setText("Separa los datos para analizar los valores inexistentes.")
        self.etiqueta_estado_preprocesado.setText("Preprocesado pendiente")
        self.etiqueta_disponibilidad_modelo.setText("Creación del modelo: no disponible")
        self.boton_aplicar.setEnabled(False)


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
        except ErrorSeleccionColumnas as error:
            # Si la lógica detecta un fallo, mostramos el mensaje exacto que programaste
            self.descartar_seleccion()
            QMessageBox.warning(self, "Error de Selección", str(error))
            return

        # The split is only available after a confirmed selection
        self.entradas = entradas_seleccionadas
        self.salida = salida_seleccionada
        self.boton_separar.setEnabled(True)
        QMessageBox.information(self, "Éxito", "Las variables seleccionadas son válidas y están listas para entrenar.")

    def separar(self) -> None:
        """Separa los datos en entrenamiento y test con el porcentaje y la semilla indicados."""
        # A new split always discards the previous one and what was built on it
        self.invalidar_separacion()

        try:
            porcentaje_test = float(self.entrada_porcentaje.text().strip().replace(",", "."))
        except ValueError:
            QMessageBox.warning(self, "Error en el porcentaje",
                                "El porcentaje de test debe ser un número entre 1 y 99.")
            return

        try:
            semilla = int(self.entrada_semilla.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Error en la semilla",
                                "La semilla debe ser un número entero.")
            return

        # Range checks, minimum rows and empty sets are done by data_splitter
        try:
            entrenamiento, test = separar_datos(self.datos, porcentaje_test, semilla)
        except ErrorSeparacionDatos as error:
            QMessageBox.warning(self, "Error al separar los datos", str(error))
            return

        # Normalizar las columnas seleccionadas sin modificar los datos originales
        columnas = self.entradas + [self.salida]

        try:
            entrenamiento = normalizar_columnas(entrenamiento, columnas)
            test = normalizar_columnas(test, columnas)
        except ErrorPreprocesado as error:
            QMessageBox.warning(self, "Error al analizar los datos", str(error))
            return

        self.datos_entrenamiento = entrenamiento
        self.datos_test = test

        # Detectar los valores inexistentes tras la separación
        self.actualizar_deteccion()

        self.etiqueta_separacion.setText(
            f"Entrenamiento: {len(entrenamiento)} filas | Test: {len(test)} filas")
        QMessageBox.information(
            self, "Separación realizada",
            "Los datos se han separado correctamente.\n\n"
            f"Entrenamiento: {len(entrenamiento)} filas\n"
            f"Test: {len(test)} filas")

    def actualizar_opcion_constante(self, _indice: int) -> None:
        """Habilita el campo constante solo para su estrategia."""
        self.entrada_constante.setEnabled(self.combo_estrategia.currentData() == "constante")


    def actualizar_deteccion(self) -> None:
        """Muestra los nulos de cada columna y actualiza el estado del modelo."""
        if self.datos_entrenamiento is None or self.datos_test is None:
            return

        columnas = self.entradas + [self.salida]

        conteo_entrenamiento = detectar_valores_inexistentes(
            self.datos_entrenamiento, columnas
        )
        conteo_test = detectar_valores_inexistentes(
            self.datos_test, columnas
        )

        self.tabla_faltantes.setRowCount(len(columnas))

        for fila, columna in enumerate(columnas):
            for indice, texto in enumerate((
                columna,
                str(conteo_entrenamiento[columna]),
                str(conteo_test[columna]),
            )):
                self.tabla_faltantes.setItem(
                    fila, indice, QTableWidgetItem(texto)
                )

        total_entrenamiento = sum(conteo_entrenamiento.values())
        total_test = sum(conteo_test.values())

        self.grupo_preprocesado.setEnabled(True)
        self.datos_listos_para_modelo = (
            total_entrenamiento + total_test == 0
        )
        self.boton_aplicar.setEnabled(
            not self.datos_listos_para_modelo
        )

        if self.datos_listos_para_modelo:
            self.etiqueta_faltantes.setText(
                "No hay valores inexistentes en las columnas seleccionadas. "
                "Puedes continuar sin preprocesar."
            )
            self.etiqueta_estado_preprocesado.setText(
                "No quedan valores inexistentes."
            )
            self.etiqueta_disponibilidad_modelo.setText(
                "Creación del modelo: disponible"
            )
        else:
            self.etiqueta_faltantes.setText(
                f"Valores inexistentes: {total_entrenamiento} en entrenamiento "
                f"y {total_test} en test."
            )
            self.etiqueta_estado_preprocesado.setText(
                "Elige una estrategia y pulsa Aplicar preprocesado."
            )
            self.etiqueta_disponibilidad_modelo.setText(
                "Creación del modelo: no disponible hasta tratar los nulos"
            )


    def aplicar_preprocesado_gui(self) -> None:
        """Aplica la estrategia elegida y comunica el resultado de ambos conjuntos."""
        if self.datos_entrenamiento is None or self.datos_test is None:
            return
    
        estrategia = self.combo_estrategia.currentData()
        valor_constante = (
            self.entrada_constante.text()
            if estrategia == "constante" else None
        )
    
        try:
            (
                entrenamiento_limpio,
                test_limpio,
                afectados_entrenamiento,
                afectados_test,
            ) = aplicar_preprocesado(
                self.datos_entrenamiento,
                self.datos_test,
                self.entradas + [self.salida],
                estrategia,
                valor_constante,
            )
    
        except ErrorPreprocesado as error:
            QMessageBox.warning(
                self, "Error de preprocesado", str(error)
            )
            return
    
        # Actualizar los datos solo después de completar el tratamiento
        self.datos_entrenamiento = entrenamiento_limpio
        self.datos_test = test_limpio
        self.preprocesado = estrategia
        self.modelo = None
    
        self.etiqueta_separacion.setText(
            f"Entrenamiento: {len(entrenamiento_limpio)} filas | "
            f"Test: {len(test_limpio)} filas"
        )
    
        self.actualizar_deteccion()
    
        unidad = (
            "filas eliminadas"
            if estrategia == "eliminar"
            else "valores rellenados"
        )
    
        mensaje = (
            f"Entrenamiento: {afectados_entrenamiento} {unidad}.\n"
            f"Test: {afectados_test} {unidad}."
        )
    
        self.etiqueta_estado_preprocesado.setText(
            "Preprocesado aplicado correctamente. "
            + mensaje.replace("\n", " | ")
        )
    
        QMessageBox.information(
            self, "Preprocesado aplicado", mensaje
        )


def ejecutar() -> None:
    """Abre la ventana principal y espera a que el usuario la cierre."""
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    ejecutar()