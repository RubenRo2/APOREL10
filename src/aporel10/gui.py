"""Interfaz gráfica de la aplicación (PySide6)."""

import sys
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QMessageBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget, QListWidget, QComboBox, QGroupBox, QSizePolicy,
                               QAbstractItemView, QHeaderView, QScrollArea)
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from aporel10.data_loader import ErrorImportacionDatos, cargar_datos
from aporel10.column_selector import ErrorSeleccionColumnas, validar_seleccion
from aporel10.data_splitter import ErrorSeparacionDatos, separar_datos
from aporel10.model import ErrorRegresion, entrenar_regresion_lineal
from aporel10.missing_values import (
    ErrorPreprocesado,
    aplicar_preprocesado,
    detectar_valores_inexistentes,
    normalizar_columnas,
)


# Solo se muestran en el explorador los formatos que admite data_loader.
FILTRO_DATOS = "Datos (*.csv *.xlsx *.xls *.sqlite *.db)"
VELOCIDAD_SCROLL = 5 # Píxeles de avance por cada clic de la rueda del ratón


class VentanaPrincipal(QMainWindow):
    """Ventana principal de la aplicación."""

    def __init__(self):
        
        super().__init__()
        self.setWindowTitle("APOREL10 - Regresión lineal")
        self.resize(1000, 700)

        # 1. Inicialización del estado interno
        self._inicializar_estado()
        
        # 2. Creación y ensamblaje de la interfaz
        self._crear_interfaz()
        
        # 3. Conexión de eventos y señales
        self._conectar_señales()
        
        # 4. Aplicación de estilos visuales
        self._aplicar_estilos()   
        
        
    def _inicializar_estado(self) -> None:
        """Define las variables de estado que usará la aplicación."""
        self.datos: pd.DataFrame | None = None
        self.ruta_datos: Path | None = None

        self.entradas: list[str] | None = None
        self.salida: str | None = None

        self.datos_entrenamiento: pd.DataFrame | None = None
        self.datos_test: pd.DataFrame | None = None

        self.preprocesado = None
        self.modelo = None
        self.resultado_modelo = None
        self.datos_listos_para_modelo = False
    
    
    def _crear_interfaz(self) -> None:
        """Crea todos los widgets y los organiza en layouts modulares."""
        
        # 1º Carga de datos
        self.boton_cargar = QPushButton("Cargar datos...")
        self.etiqueta_ruta = QLabel("Ningún archivo cargado")
        self.tabla = QTableWidget()
        
        self.tabla.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tabla.setMinimumHeight(200)
        
        fila_carga = QHBoxLayout()
        fila_carga.addWidget(self.boton_cargar)
        fila_carga.addWidget(self.etiqueta_ruta, stretch=1)
        
        # 2º Selección de variables
        grupo_variables = QGroupBox("Selección de Variables")
        grupo_variables.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout_variables = QHBoxLayout(grupo_variables)
        
        self.lista_entradas = QListWidget()
        self.lista_entradas.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.lista_entradas.setMaximumHeight(70)
        self.lista_entradas.setMinimumHeight(70) 
        self.lista_entradas.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.lista_entradas.verticalScrollBar().setSingleStep(VELOCIDAD_SCROLL)
        
        self.combo_salida = QComboBox()
        self.combo_salida.view().setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.combo_salida.view().verticalScrollBar().setSingleStep(VELOCIDAD_SCROLL)
        
        self.boton_validar = QPushButton("Validar variables")
        self.boton_validar.setFixedWidth(270)
        
        self.combo_salida.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.combo_salida.setMinimumWidth(250)
        
        layout_derecha = QVBoxLayout()
        
        fila_salida = QHBoxLayout()
        fila_salida.addWidget(QLabel("Salida (Target):"))
        fila_salida.addWidget(self.combo_salida)
        
        layout_derecha.addLayout(fila_salida)
        layout_derecha.addWidget(self.boton_validar, 0, Qt.AlignmentFlag.AlignRight)
        layout_derecha.addStretch() # Evita que se expandan hacia abajo

        layout_variables.addWidget(QLabel("Entradas (Features):"))
        layout_variables.addWidget(self.lista_entradas, stretch=3)
        layout_variables.addLayout(layout_derecha, stretch=2)
        
        # 3º Separación de datos
        grupo_separacion = QGroupBox("Separación de Datos (Train/Test)")
        grupo_separacion.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout_separacion = QHBoxLayout(grupo_separacion)
        
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

        layout_separacion.addWidget(QLabel("Test (%):"))
        layout_separacion.addWidget(self.entrada_porcentaje)
        layout_separacion.addWidget(self.etiqueta_entrenamiento)
        layout_separacion.addWidget(QLabel("Semilla:"))
        layout_separacion.addWidget(self.entrada_semilla)
        layout_separacion.addWidget(self.boton_separar)
        layout_separacion.addWidget(self.etiqueta_separacion, stretch=1)
        
        # 4º Preprocesado
        self._crear_panel_preprocesado()
        self._crear_panel_modelo()
        
        # 5º Ensamblaje final 
        contenido = QWidget()
        layout_principal = QVBoxLayout(contenido)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)
        
        layout_principal.addLayout(fila_carga)
        layout_principal.addWidget(self.tabla, stretch=10)   
        layout_principal.addWidget(grupo_variables, stretch=0)   
        layout_principal.addWidget(grupo_separacion, stretch=0)   
        layout_principal.addWidget(self.grupo_preprocesado, stretch=0)
        layout_principal.addWidget(self.grupo_modelo, stretch=0)
        # Permitir desplazamiento para visualizar el gráfico
        desplazamiento = QScrollArea()
        desplazamiento.setWidgetResizable(True)

        self.setCentralWidget(contenido)

   
    def _crear_panel_preprocesado(self) -> None:
        """Construye específicamente el grupo de preprocesado de datos."""
        self.grupo_preprocesado = QGroupBox("Valores inexistentes y preprocesado")
        self.grupo_preprocesado.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.grupo_preprocesado.setEnabled(False)
        layout_preprocesado = QVBoxLayout(self.grupo_preprocesado)

        self.etiqueta_faltantes = QLabel("Separa los datos para analizar los valores inexistentes.")
        self.tabla_faltantes = QTableWidget(0, 3)
        self.tabla_faltantes.setHorizontalHeaderLabels(["Columna", "Entrenamiento", "Test"])
        
        self.tabla_faltantes.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.tabla_faltantes.setMaximumHeight(100)

        layout_preprocesado.addWidget(self.etiqueta_faltantes)
        layout_preprocesado.addWidget(self.tabla_faltantes)
        self.tabla_faltantes.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tabla_faltantes.verticalScrollBar().setSingleStep(VELOCIDAD_SCROLL)

        fila_tratamiento = QHBoxLayout()
        fila_tratamiento.addWidget(QLabel("Tratamiento:"))

        self.combo_estrategia = QComboBox()
        self.combo_estrategia.view().setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.combo_estrategia.view().verticalScrollBar().setSingleStep(VELOCIDAD_SCROLL)
        
        self.combo_estrategia.addItem("Eliminar filas", "eliminar")
        self.combo_estrategia.addItem("Rellenar con media", "media")
        self.combo_estrategia.addItem("Rellenar con mediana", "mediana")
        self.combo_estrategia.addItem("Rellenar con constante", "constante")
        fila_tratamiento.addWidget(self.combo_estrategia)

        self.entrada_constante = QLineEdit()
        self.entrada_constante.setPlaceholderText("Valor numérico")
        self.entrada_constante.setMaximumWidth(135)
        self.entrada_constante.setEnabled(False)
        fila_tratamiento.addWidget(self.entrada_constante)

        self.boton_aplicar = QPushButton("Aplicar preprocesado")
        self.boton_aplicar.setEnabled(False)
        fila_tratamiento.addWidget(self.boton_aplicar)
        fila_tratamiento.addStretch()

        layout_preprocesado.addLayout(fila_tratamiento)

        self.etiqueta_estado_preprocesado = QLabel("Preprocesado pendiente")
        self.etiqueta_disponibilidad_modelo = QLabel("Creación del modelo: no disponible")

        layout_preprocesado.addWidget(self.etiqueta_estado_preprocesado)
        layout_preprocesado.addWidget(self.etiqueta_disponibilidad_modelo)


    def _crear_panel_modelo(self) -> None:
        """Construye el panel de resultados de la regresión lineal."""
        self.grupo_modelo = QGroupBox("Modelo de regresión lineal")
        layout_modelo = QVBoxLayout(self.grupo_modelo)

        # Botón de creación
        self.boton_crear_modelo = QPushButton("Crear modelo")
        self.boton_crear_modelo.setEnabled(False)
        layout_modelo.addWidget(self.boton_crear_modelo)

        # Fórmula del modelo
        self.etiqueta_formula = QLabel("No se ha creado ningún modelo.")
        self.etiqueta_formula.setWordWrap(True)
        self.etiqueta_formula.setTextFormat(Qt.TextFormat.PlainText)
        self.etiqueta_formula.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout_modelo.addWidget(self.etiqueta_formula)

        # Tabla de métricas
        self.tabla_metricas = QTableWidget(2, 3)
        self.tabla_metricas.setHorizontalHeaderLabels(
            ["Métrica", "Entrenamiento", "Test"]
        )
        self.tabla_metricas.verticalHeader().setVisible(False)
        self.tabla_metricas.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabla_metricas.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tabla_metricas.setMaximumHeight(105)

        for fila, nombre in enumerate(("R²", "ECM")):
            self.tabla_metricas.setItem(
                fila, 0, QTableWidgetItem(nombre)
            )
            for columna in (1, 2):
                self.tabla_metricas.setItem(
                    fila, columna, QTableWidgetItem("—")
                )

        layout_modelo.addWidget(self.tabla_metricas)

        # Gráfico integrado
        self.figura_modelo = Figure(
            figsize=(7, 4),
            facecolor="#252525",
        )
        self.canvas_modelo = FigureCanvas(self.figura_modelo)
        self.canvas_modelo.setMinimumHeight(300)

        layout_modelo.addWidget(self.canvas_modelo)    
    
     
    def _conectar_señales(self) -> None:
        """Agrupa todas las conexiones de botones y eventos de texto."""
        self.boton_cargar.clicked.connect(self.elegir_archivo)
        self.boton_validar.clicked.connect(self.validar_variables)
        self.boton_separar.clicked.connect(self.separar)
        self.boton_aplicar.clicked.connect(self.aplicar_preprocesado_gui)
        self.boton_crear_modelo.clicked.connect(self.crear_modelo_gui)
        
        self.combo_estrategia.currentIndexChanged.connect(self.actualizar_opcion_constante)
        self.lista_entradas.itemSelectionChanged.connect(self.descartar_seleccion)
        self.combo_salida.currentTextChanged.connect(self.descartar_seleccion)
        self.entrada_porcentaje.textChanged.connect(self.actualizar_porcentaje_entrenamiento)
        
    
    def _aplicar_estilos(self) -> None:
        """Aplica las reglas QSS a la ventana, incluyendo los paneles."""
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: #e0e0e0;}
            QTableWidget { background-color: #252525; color: white;gridline-color: #444; border: 1px solid #555;}
            QHeaderView::section { background-color: #3b3b3b; color: #8ab4f8; border: 1px solid #555; padding: 4px; font-weight: bold;}
            
            QPushButton { padding: 6px 12px; border-radius: 4px; background-color: #3b3b3b; border: 1px solid #555; }
            QPushButton:hover { background-color: #505050; border: 1px solid #8ab4f8; color: #8ab4f8; }
            QPushButton:pressed { background-color: #222222; border: 1px solid #333; color: #aaaaaa;}
            QPushButton:disabled { color: #777777; border: 1px solid #444; }
            
            QListWidget, QComboBox, QLineEdit { background-color: #2b2b2b; color: white; border: 1px solid #555; border-radius: 4px; font-size: 11px; outline: none; }
            QListWidget::item:selected { background-color: #8ab4f8; color: #111111; border-radius: 2px; }
            QListWidget::item { padding: 1px 9px; height: 18px; border: none; margin: 0px;}
            
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                border: 1px solid #555;
                outline: none;
            }
            
            QComboBox QAbstractItemView::item {
                padding: 2px 6px; 
                min-height: 20px;
            }
            
            QComboBox QAbstractItemView::item:selected {
                background-color: #8ab4f8;
                color: #111111;
            }
            
            QGroupBox {
                border: 1px solid #555;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                font-weight: bold;
                color: #8ab4f8;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
            
            /* --- NUEVO: Estilo moderno para las barras de desplazamiento --- */
            QScrollBar:vertical { border: none; background-color: #1e1e1e; width: 8px; margin: 0px;}
            QScrollBar::handle:vertical { background-color: #555555; min-height: 20px; border-radius: 5px; margin: 2px;}
            QScrollBar::handle:vertical:hover {background-color: #8ab4f8;}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px;}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none;}
            
            QScrollBar:horizontal { border: none; background-color: #1e1e1e; height: 8px; margin: 0px;}
            QScrollBar::handle:horizontal { background-color: #555555; min-width: 20px; border-radius: 5px; margin: 2px;}
            QScrollBar::handle:horizontal:hover { background-color: #8ab4f8;}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px;}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none;}
            
        """)
        
    # ------------------------------------------------------------LÓGICA DE EVENTOS------------------------------------------------------------
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

        self.invalidar_modelo()


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
        self.actualizar_boton_modelo()

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
        self.invalidar_modelo()
    
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

    def actualizar_boton_modelo(self) -> None:
        """Habilita la creación solo cuando se cumplen los requisitos."""
        listo = (
            bool(self.entradas)
            and bool(self.salida)
            and self.datos_entrenamiento is not None
            and self.datos_test is not None
            and self.datos_listos_para_modelo
        )

        self.boton_crear_modelo.setEnabled(bool(listo))


    def invalidar_modelo(self) -> None:
        """Descarta un modelo anterior y limpia sus resultados visuales."""
        self.modelo = None
        self.resultado_modelo = None

        self.etiqueta_formula.setText(
            "No se ha creado ningún modelo."
        )

        for fila in range(2):
            for columna in (1, 2):
                self.tabla_metricas.item(
                    fila, columna
                ).setText("—")

        self.figura_modelo.clear()
        self.canvas_modelo.draw_idle()

        self.actualizar_boton_modelo()


    def crear_modelo_gui(self) -> None:
        """Solicita el entrenamiento y muestra los resultados."""
        if not self.boton_crear_modelo.isEnabled():
            return

        try:
            resultado = entrenar_regresion_lineal(
                self.datos_entrenamiento,
                self.datos_test,
                self.entradas,
                self.salida,
            )

            self.dibujar_grafico_modelo(
                resultado["grafico"]
            )

        except ErrorRegresion as error:
            QMessageBox.warning(
                self,
                "Error al crear el modelo",
                str(error),
            )
            return

        except Exception as error:
            QMessageBox.critical(
                self,
                "Error al crear el modelo",
                f"No se ha podido mostrar el modelo: {error}",
            )
            return

        # Sustituir el modelo anterior
        self.modelo = resultado["modelo"]
        self.resultado_modelo = resultado

        # Mostrar la fórmula
        self.etiqueta_formula.setText(
            resultado["formula"]
        )

        # Mostrar las métricas
        for columna, conjunto in (
            (1, "entrenamiento"),
            (2, "test"),
        ):
            metricas = resultado["metricas"][conjunto]

            self.tabla_metricas.item(
                0, columna
            ).setText(
                f"{metricas['r2']:.4f}"
            )

            self.tabla_metricas.item(
                1, columna
            ).setText(
                f"{metricas['ecm']:,.4f}"
            )

        QMessageBox.information(
            self,
            "Modelo creado",
            "El modelo de regresión lineal "
            "se ha creado correctamente.",
        )

    def dibujar_grafico_modelo(self, grafico: dict) -> None:
        """Dibuja los datos preparados por el módulo model."""
        self.figura_modelo.clear()
        ejes = self.figura_modelo.add_subplot(111)
        ejes.set_facecolor("#252525")

        if grafico["tipo"] == "simple":
            ejes.scatter(
                grafico["train_x"],
                grafico["train_y"],
                label="Entrenamiento",
                color="tab:blue",
                s=16,
                alpha=0.65,
            )

            ejes.scatter(
                grafico["test_x"],
                grafico["test_y"],
                label="Test",
                color="tab:orange",
                marker="x",
                s=22,
                alpha=0.8,
            )

            ejes.plot(
                grafico["linea_x"],
                grafico["linea_y"],
                label="Recta de ajuste",
                color="tab:red",
                linewidth=2,
            )

            ejes.set_xlabel(grafico["eje_x"])
            ejes.set_ylabel(grafico["eje_y"])

        else:
            ejes.scatter(
                grafico["train_real"],
                grafico["train_predicho"],
                label="Entrenamiento",
                color="tab:blue",
                s=16,
                alpha=0.65,
            )

            ejes.scatter(
                grafico["test_real"],
                grafico["test_predicho"],
                label="Test",
                color="tab:orange",
                marker="x",
                s=22,
                alpha=0.8,
            )

            ejes.plot(
                [
                    grafico["linea_min"],
                    grafico["linea_max"],
                ],
                [
                    grafico["linea_min"],
                    grafico["linea_max"],
                ],
                label="Predicción perfecta",
                color="tab:red",
                linestyle="--",
                linewidth=2,
            )

            ejes.set_xlabel("Valor real")
            ejes.set_ylabel("Valor predicho")

        # Aplicar el estilo oscuro
        ejes.tick_params(colors="#e0e0e0")
        ejes.xaxis.label.set_color("#e0e0e0")
        ejes.yaxis.label.set_color("#e0e0e0")

        for borde in ejes.spines.values():
            borde.set_color("#777777")

        ejes.grid(alpha=0.2)
        ejes.legend(
            facecolor="#333333",
            edgecolor="#777777",
            labelcolor="white",
        )

        self.figura_modelo.tight_layout()
        self.canvas_modelo.draw_idle()

def ejecutar() -> None:
    """Abre la ventana principal y espera a que el usuario la cierre."""
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.showMaximized()
    sys.exit(app.exec())