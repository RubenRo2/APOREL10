"""Interfaz gráfica de la aplicación (PySide6)."""

from math import ceil
import sys
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                               QLineEdit, QMainWindow, QMessageBox,
                               QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget, QComboBox,
                               QGroupBox, QSizePolicy, QAbstractItemView,
                               QFrame, QHeaderView, QScrollArea,
                               QAbstractButton, QButtonGroup, QCheckBox,
                               QGridLayout, QMenu, QRadioButton,
                               QWidgetAction)
from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap

from matplotlib.backend_bases import MouseButton
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from aporel10.data_loader import ErrorImportacionDatos, cargar_datos
from aporel10.column_selector import ErrorSeleccionColumnas, validar_seleccion
from aporel10.data_splitter import ErrorSeparacionDatos, separar_datos
from aporel10.model import ErrorRegresion, entrenar_regresion_lineal, preparar_grafico_variable
from aporel10.missing_values import (
    ErrorPreprocesado,
    aplicar_preprocesado,
    detectar_valores_inexistentes,
    normalizar_columnas,
)


# Solo se muestran en el explorador los formatos que admite data_loader.
FILTRO_DATOS = "Datos (*.csv *.xlsx *.xls *.sqlite *.db)"
VELOCIDAD_SCROLL = 5  # Píxeles de avance por cada clic de la rueda del ratón
# Igual, pero para el desplazamiento de la ventana completa
VELOCIDAD_SCROLL_VENTANA = 30
ANCHO_SELECTOR = 140  # Ancho fijo de los botones de selección de columnas
ANCHO_MAX_OPCION = 220  # Píxeles a partir de los que se recorta un nombre
MAX_FILAS_SELECTOR = 12  # Filas por columna antes de abrir otra columna
ALTO_MIN_TABLA_FALTANTES = 150  # Crece con las filas para no tener scroll
ALTO_TABLA_METRICAS = 80  # Cabecera y dos filas, sin hueco ni scroll
ALTO_FILA_METRICAS = 24
ANCHO_TABLA_METRICAS = 380
ALTO_GRAFICO = 520
FACTOR_ZOOM_RUEDA = 0.85  # Rango visible tras cada paso de la rueda
INTERVALO_ANIMACION_MS = 16  # Unos 60 fotogramas por segundo
AVANCE_ZOOM = 0.35  # Parte del zoom pendiente aplicada en cada fotograma
TOLERANCIA_ZOOM = 0.002  # Distancia relativa a la que el zoom termina
RETARDO_REDIBUJADO_MS = 120  # Pausa del gesto antes de redibujar nítido
MAX_HUECO_VISTA_PREVIA = 0.25  # Parte vacía tolerada durante un gesto
MAX_AUMENTO_VISTA_PREVIA = 1.5  # Aumento tolerado antes de verse borroso


def calcular_columnas(n_opciones: int, alto_fila: int, ancho_celda: int,
                      alto_disponible: int, ancho_disponible: int) -> int:
    """Calcula cuántas columnas necesita la rejilla para caber sin scroll."""
    filas = max(1, min(MAX_FILAS_SELECTOR, alto_disponible // alto_fila))
    columnas_maximas = max(1, ancho_disponible // ancho_celda)
    return min(ceil(n_opciones / filas), columnas_maximas)


class ComboSinRueda(QComboBox):
    """Desplegable que deja pasar la rueda para no cambiar valor con scroll."""

    def wheelEvent(self, event) -> None:
        event.ignore()


class SelectorColumnas(QPushButton):
    """Botón con un desplegable que muestra todas las columnas sin scroll."""

    seleccion_cambiada = Signal()

    def __init__(self, multiple: bool) -> None:
        super().__init__()
        self._multiple = multiple
        self._casillas: list[tuple[str, QAbstractButton]] = []
        self._menu = QMenu(self)
        self.setMenu(self._menu)
        self.setFixedWidth(ANCHO_SELECTOR)
        self.establecer_opciones([])

    def establecer_opciones(self, columnas: list[str]) -> None:
        """Sustituye las opciones; un selector único marca la primera."""
        self._menu.clear()
        self._casillas = []
        if columnas:
            self._menu.addAction(self._crear_accion(columnas))
        self.setEnabled(bool(columnas))
        self._actualizar_texto()

    def seleccionadas(self) -> list[str]:
        """Devuelve las columnas marcadas, en el orden del dataset."""
        return [
            nombre for nombre, casilla in self._casillas
            if casilla.isChecked()
        ]

    def seleccionar(self, columnas: list[str]) -> None:
        """Marca exactamente las columnas indicadas."""
        for nombre, casilla in self._casillas:
            casilla.setChecked(nombre in columnas)

    def _crear_accion(self, columnas: list[str]) -> QWidgetAction:
        """Coloca las opciones en una rejilla que cabe en la pantalla."""
        contenedor = QWidget()
        rejilla = QGridLayout(contenedor)
        grupo = QButtonGroup(contenedor)
        grupo.setExclusive(not self._multiple)

        for nombre in columnas:
            casilla = self._crear_casilla(nombre)
            grupo.addButton(casilla)
            self._casillas.append((nombre, casilla))
        if not self._multiple:
            self._casillas[0][1].setChecked(True)

        tamanos = [c.sizeHint() for _, c in self._casillas]
        margen = 2 * rejilla.contentsMargins().left()
        zona = self.screen().availableGeometry()
        n_columnas = calcular_columnas(
            len(columnas),
            max(t.height() for t in tamanos) + rejilla.verticalSpacing(),
            max(t.width() for t in tamanos) + rejilla.horizontalSpacing(),
            zona.height() - margen,
            zona.width() - margen,
        )
        n_filas = ceil(len(columnas) / n_columnas)
        for i, (_, casilla) in enumerate(self._casillas):
            rejilla.addWidget(casilla, i % n_filas, i // n_filas)
            casilla.toggled.connect(self._al_alternar)
            if not self._multiple:
                casilla.clicked.connect(self._cerrar_menu)

        accion = QWidgetAction(self._menu)
        accion.setDefaultWidget(contenedor)
        return accion

    def _crear_casilla(self, nombre: str) -> QAbstractButton:
        casilla = QCheckBox() if self._multiple else QRadioButton()
        casilla.setText(self._texto_visible(
            nombre, casilla.fontMetrics(), ANCHO_MAX_OPCION))
        casilla.setToolTip(nombre)
        return casilla

    def _al_alternar(self, marcada: bool) -> None:
        # In an exclusive group each change also unchecks the previous option
        if self._multiple or marcada:
            self._actualizar_texto()
            self.seleccion_cambiada.emit()

    def _cerrar_menu(self) -> None:
        self._menu.close()

    def _actualizar_texto(self) -> None:
        marcadas = self.seleccionadas()
        self.setToolTip(", ".join(marcadas))
        if not self._casillas:
            self.setText("Sin columnas")
        elif len(marcadas) == 1:
            self.setText(self._texto_visible(
                marcadas[0], self.fontMetrics(), ANCHO_SELECTOR - 50))
        elif marcadas:
            self.setText(f"{len(marcadas)} de {len(self._casillas)} columnas")
        else:
            self.setText("Seleccionar...")

    @staticmethod
    def _texto_visible(nombre: str, metricas, ancho: int) -> str:
        """Recorta el nombre y evita que Qt interprete & como atajo."""
        recortado = metricas.elidedText(
            nombre, Qt.TextElideMode.ElideRight, ancho)
        return recortado.replace("&", "&&")


class CanvasGrafica(FigureCanvas):
    """Lienzo que se mueve arrastrando y hace zoom con la rueda del ratón.

    Redibujar la figura tarda demasiado para seguir al ratón, así que durante
    el gesto se transforma la última imagen y al terminar se redibuja.
    """

    def __init__(self, figura: Figure) -> None:
        super().__init__(figura)
        self._ejes_arrastrados = None
        self._vista_inicial = None
        self._dibujado = None
        self._vista_previa = None
        self._objetivo_zoom = None
        self._redibujado = QTimer(self)
        self._redibujado.setSingleShot(True)
        self._redibujado.setInterval(RETARDO_REDIBUJADO_MS)
        self._redibujado.timeout.connect(self.draw_idle)
        self._animacion_zoom = QTimer(self)
        self._animacion_zoom.setInterval(INTERVALO_ANIMACION_MS)
        self._animacion_zoom.timeout.connect(self._avanzar_zoom)
        self.mpl_connect("button_press_event", self._empezar_arrastre)
        self.mpl_connect("motion_notify_event", self._arrastrar)
        self.mpl_connect("button_release_event", self._terminar_arrastre)
        self.mpl_connect("scroll_event", self._zoom_con_rueda)

    def recordar_vista(self) -> None:
        """Toma la vista actual como inicial; llamar tras cada redibujado."""
        self._ejes_arrastrados = None
        self._cancelar_zoom()
        if self.figure.axes:
            ejes = self.figure.axes[0]
            self._vista_inicial = (ejes.get_xlim(), ejes.get_ylim())
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self._vista_inicial = None
            self.unsetCursor()

    def restablecer_vista(self) -> None:
        """Vuelve a la vista recordada."""
        if self._vista_inicial is None:
            return
        self._cancelar_zoom()
        ejes = self.figure.axes[0]
        ejes.set_xlim(self._vista_inicial[0])
        ejes.set_ylim(self._vista_inicial[1])
        self.draw_idle()

    def zoom_en_curso(self) -> bool:
        """Indica si la animación del zoom sigue avanzando."""
        return self._animacion_zoom.isActive()

    def draw(self) -> None:
        self._vista_previa = None
        self._redibujado.stop()
        super().draw()
        if self.figure.axes:
            ejes = self.figure.axes[0]
            self._dibujado = (
                ejes.get_xlim(), ejes.get_ylim(), tuple(ejes.bbox.extents))
        else:
            self._dibujado = None

    def paintEvent(self, event) -> None:
        if self._vista_previa is None:
            super().paintEvent(event)
        else:
            self._pintar_vista_previa()

    def wheelEvent(self, event) -> None:
        # Outside the axes the wheel keeps scrolling the window
        if self.inaxes(self.mouseEventCoords(event)) is None:
            event.ignore()
        else:
            super().wheelEvent(event)

    def _pintar_vista_previa(self) -> None:
        """Coloca la última imagen donde caen sus datos en la vista actual."""
        x_dibujado, y_dibujado, (x0, y0, x1, y1) = self._dibujado
        ejes = self.figure.axes[0]
        x_vista, y_vista = ejes.get_xlim(), ejes.get_ylim()
        imagen = self._vista_previa
        ratio = self.device_pixel_ratio

        # Rectangle of the axes in the image, inset to leave the spines out
        origen = QRectF(x0, imagen.height() - y1, x1 - x0, y1 - y0)
        ancho, alto = origen.width() / ratio, origen.height() / ratio
        izquierda, arriba = origen.x() / ratio, origen.y() / ratio
        zona = QRectF(izquierda, arriba, ancho, alto)
        escala_x = (x_dibujado[1] - x_dibujado[0]) / (x_vista[1] - x_vista[0])
        escala_y = (y_dibujado[1] - y_dibujado[0]) / (y_vista[1] - y_vista[0])
        destino = QRectF(
            izquierda + ancho * (x_dibujado[0] - x_vista[0])
            / (x_vista[1] - x_vista[0]),
            arriba + alto * (y_vista[1] - y_dibujado[1])
            / (y_vista[1] - y_vista[0]),
            ancho * escala_x,
            alto * escala_y,
        )
        margen_x, margen_y = escala_x / ratio, escala_y / ratio
        destino.adjust(margen_x, margen_y, -margen_x, -margen_y)
        origen.adjust(1, 1, -1, -1)
        zona.adjust(1 / ratio, 1 / ratio, -1 / ratio, -1 / ratio)

        pintor = QPainter(self)
        pintor.drawPixmap(self.rect(), imagen, imagen.rect())
        pintor.setClipRect(zona)
        pintor.fillRect(zona, QColor.fromRgbF(*ejes.get_facecolor()))
        pintor.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        pintor.drawPixmap(destino, imagen, origen)
        pintor.end()

    def _mostrar_cambio_de_vista(self, ejes) -> None:
        if (self._dibujado is None or self._draw_pending
                or self._vista_agotada(ejes)):
            self.draw_idle()
            return
        if self._vista_previa is None:
            alto, ancho = memoryview(self.buffer_rgba()).shape[:2]
            self._vista_previa = QPixmap.fromImage(QImage(
                self.buffer_rgba(), ancho, alto,
                QImage.Format.Format_RGBA8888))
        self._redibujado.start()
        self.update()

    def _vista_agotada(self, ejes) -> bool:
        """Indica si la imagen ya deja mucho hueco o se vería borrosa."""
        pares = (
            (self._dibujado[0], ejes.get_xlim()),
            (self._dibujado[1], ejes.get_ylim()),
        )
        for dibujado, vista in pares:
            ancho_vista = vista[1] - vista[0]
            hueco = (max(0, dibujado[0] - vista[0])
                     + max(0, vista[1] - dibujado[1]))
            if (hueco / ancho_vista > MAX_HUECO_VISTA_PREVIA
                    or (dibujado[1] - dibujado[0]) / ancho_vista
                    > MAX_AUMENTO_VISTA_PREVIA):
                return True
        return False

    def _empezar_arrastre(self, evento) -> None:
        if evento.inaxes is None or evento.button != MouseButton.LEFT:
            return
        self._cancelar_zoom()
        self._ejes_arrastrados = evento.inaxes
        self._ejes_arrastrados.start_pan(evento.x, evento.y, evento.button)
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def _arrastrar(self, evento) -> None:
        if self._ejes_arrastrados is None:
            return
        self._ejes_arrastrados.drag_pan(
            MouseButton.LEFT, None, evento.x, evento.y)
        self._mostrar_cambio_de_vista(self._ejes_arrastrados)

    def _terminar_arrastre(self, evento) -> None:
        if self._ejes_arrastrados is None or evento.button != MouseButton.LEFT:
            return
        self._ejes_arrastrados.end_pan()
        self._ejes_arrastrados = None
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.draw_idle()

    def _zoom_con_rueda(self, evento) -> None:
        ejes = evento.inaxes
        if ejes is None:
            return
        # Touchpads report steps far larger than one wheel notch
        pasos = max(-1.0, min(1.0, evento.step))
        factor = FACTOR_ZOOM_RUEDA ** pasos
        x_min, x_max, y_min, y_max = (
            self._objetivo_zoom or (*ejes.get_xlim(), *ejes.get_ylim()))
        self._objetivo_zoom = (
            evento.xdata + (x_min - evento.xdata) * factor,
            evento.xdata + (x_max - evento.xdata) * factor,
            evento.ydata + (y_min - evento.ydata) * factor,
            evento.ydata + (y_max - evento.ydata) * factor,
        )
        if not self._animacion_zoom.isActive():
            self._animacion_zoom.start()

    def _avanzar_zoom(self) -> None:
        ejes = self.figure.axes[0]
        actual = (*ejes.get_xlim(), *ejes.get_ylim())
        objetivo = self._objetivo_zoom
        tolerancia = ((actual[1] - actual[0]) * TOLERANCIA_ZOOM,
                      (actual[3] - actual[2]) * TOLERANCIA_ZOOM)
        terminado = all(
            abs(objetivo[i] - actual[i]) < tolerancia[i // 2]
            for i in range(4))
        if terminado:
            nuevo = objetivo
            self._cancelar_zoom()
        else:
            nuevo = tuple(
                a + (o - a) * AVANCE_ZOOM for a, o in zip(actual, objetivo))
        ejes.set_xlim(nuevo[:2])
        ejes.set_ylim(nuevo[2:])
        self._mostrar_cambio_de_vista(ejes)

    def _cancelar_zoom(self) -> None:
        self._animacion_zoom.stop()
        self._objetivo_zoom = None


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

        self.tabla.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tabla.setMinimumHeight(300)

        fila_carga = QHBoxLayout()
        fila_carga.addWidget(self.boton_cargar)
        fila_carga.addWidget(self.etiqueta_ruta, stretch=1)

        # 2º Selección de variables
        grupo_variables = QGroupBox("Selección de Variables")
        grupo_variables.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout_variables = QHBoxLayout(grupo_variables)

        self.selector_entradas = SelectorColumnas(multiple=True)
        self.selector_salida = SelectorColumnas(multiple=False)
        self.boton_validar = QPushButton("Validar variables")

        layout_variables.addWidget(QLabel("Entradas (Features):"))
        layout_variables.addWidget(self.selector_entradas)
        layout_variables.addSpacing(10)
        layout_variables.addWidget(QLabel("Salida (Target):"))
        layout_variables.addWidget(self.selector_salida)
        layout_variables.addSpacing(10)
        layout_variables.addWidget(self.boton_validar)

        # 3º Separación de datos
        grupo_separacion = QGroupBox("Separación de Datos (Train/Test)")
        grupo_separacion.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
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
        self.etiqueta_separacion.setWordWrap(True)
        self.etiqueta_separacion.setMinimumWidth(170)

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
        fila_variables_separacion = QHBoxLayout()
        fila_variables_separacion.addWidget(grupo_variables)
        fila_variables_separacion.addWidget(grupo_separacion, stretch=1)
        layout_principal.addLayout(fila_variables_separacion, stretch=0)
        layout_principal.addWidget(self.grupo_preprocesado, stretch=0)
        layout_principal.addWidget(self.grupo_modelo, stretch=0)
        # Permitir desplazamiento para que cada sección conserve su altura
        desplazamiento = QScrollArea()
        desplazamiento.setWidgetResizable(True)
        desplazamiento.setFrameShape(QFrame.Shape.NoFrame)
        desplazamiento.verticalScrollBar().setSingleStep(
            VELOCIDAD_SCROLL_VENTANA)
        desplazamiento.setWidget(contenido)

        self.setCentralWidget(desplazamiento)

    def _crear_panel_preprocesado(self) -> None:
        """Construye específicamente el grupo de preprocesado de datos."""
        self.grupo_preprocesado = QGroupBox(
            "Valores inexistentes y preprocesado")
        self.grupo_preprocesado.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.grupo_preprocesado.setEnabled(False)
        layout_preprocesado = QVBoxLayout(self.grupo_preprocesado)

        self.etiqueta_faltantes = QLabel(
            "Separa los datos para analizar los valores inexistentes.")
        self.tabla_faltantes = QTableWidget(0, 3)
        self.tabla_faltantes.setHorizontalHeaderLabels(
            ["Columna", "Entrenamiento", "Test"])

        self.tabla_faltantes.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.tabla_faltantes.setFixedHeight(ALTO_MIN_TABLA_FALTANTES)
        self._quitar_scroll(self.tabla_faltantes)
        self.tabla_faltantes.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)

        layout_preprocesado.addWidget(self.etiqueta_faltantes)

        fila_tratamiento = QHBoxLayout()
        fila_tratamiento.addWidget(QLabel("Tratamiento:"))

        self.combo_estrategia = ComboSinRueda()
        self.combo_estrategia.view().setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.combo_estrategia.view().verticalScrollBar().setSingleStep(
            VELOCIDAD_SCROLL)

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

        self.etiqueta_estado_preprocesado = QLabel("Preprocesado pendiente")
        self.etiqueta_disponibilidad_modelo = QLabel(
            "Creación del modelo: no disponible")

        self.etiqueta_estado_preprocesado.setWordWrap(True)

        columna_tratamiento = QVBoxLayout()
        columna_tratamiento.addLayout(fila_tratamiento)
        columna_tratamiento.addWidget(self.etiqueta_estado_preprocesado)
        columna_tratamiento.addWidget(self.etiqueta_disponibilidad_modelo)
        columna_tratamiento.addStretch()

        fila_preprocesado = QHBoxLayout()
        fila_preprocesado.addWidget(self.tabla_faltantes, stretch=1)
        fila_preprocesado.addLayout(columna_tratamiento, stretch=1)
        layout_preprocesado.addLayout(fila_preprocesado)

    @staticmethod
    def _quitar_scroll(tabla: QTableWidget) -> None:
        """Oculta las barras de una tabla que muestra todas sus filas."""
        politica = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        tabla.setVerticalScrollBarPolicy(politica)
        tabla.setHorizontalScrollBarPolicy(politica)

    def _ajustar_alto_faltantes(self) -> None:
        """Da a la tabla la altura justa para mostrar todas las filas."""
        tabla = self.tabla_faltantes
        necesario = (
            tabla.horizontalHeader().sizeHint().height()
            + tabla.verticalHeader().length()
            + 2 * tabla.frameWidth()
        )
        tabla.setFixedHeight(max(ALTO_MIN_TABLA_FALTANTES, necesario))

    def _crear_panel_modelo(self) -> None:
        """Construye el panel de resultados de la regresión lineal."""
        self.grupo_modelo = QGroupBox("Modelo de regresión lineal")
        layout_modelo = QVBoxLayout(self.grupo_modelo)
        columna_resultados = QVBoxLayout()

        # Botón de creación
        self.boton_crear_modelo = QPushButton("Crear modelo")
        self.boton_crear_modelo.setEnabled(False)
        self.boton_vista_inicial = QPushButton("Vista inicial")
        self.boton_vista_inicial.setToolTip(
            "Deshace el movimiento y el zoom de la gráfica")
        self.boton_vista_inicial.setEnabled(False)
        fila_botones = QHBoxLayout()
        fila_botones.addWidget(self.boton_crear_modelo)
        fila_botones.addWidget(self.boton_vista_inicial)
        fila_botones.addStretch()
        columna_resultados.addLayout(fila_botones)

        # Fórmula del modelo
        self.etiqueta_formula = QLabel("No se ha creado ningún modelo.")
        self.etiqueta_formula.setWordWrap(True)
        self.etiqueta_formula.setTextFormat(Qt.TextFormat.PlainText)
        self.etiqueta_formula.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        columna_resultados.addWidget(self.etiqueta_formula)

        # Tabla de métricas
        self.tabla_metricas = QTableWidget(2, 3)
        self.tabla_metricas.setHorizontalHeaderLabels(
            ["Métrica", "Entrenamiento", "Test"]
        )
        self.tabla_metricas.verticalHeader().setVisible(False)
        self.tabla_metricas.verticalHeader().setDefaultSectionSize(
            ALTO_FILA_METRICAS)
        self.tabla_metricas.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabla_metricas.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tabla_metricas.setFixedSize(
            ANCHO_TABLA_METRICAS, ALTO_TABLA_METRICAS)
        self._quitar_scroll(self.tabla_metricas)

        for fila, nombre in enumerate(("R²", "ECM")):
            self.tabla_metricas.setItem(
                fila, 0, QTableWidgetItem(nombre)
            )
            for columna in (1, 2):
                valor = QTableWidgetItem("—")
                # Right-aligned so the digits line up when comparing
                valor.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight
                    | Qt.AlignmentFlag.AlignVCenter
                )
                self.tabla_metricas.setItem(fila, columna, valor)

        columna_resultados.addStretch()

        fila_resultados = QHBoxLayout()
        fila_resultados.addWidget(self.tabla_metricas)
        fila_resultados.addSpacing(15)
        fila_resultados.addLayout(columna_resultados, stretch=1)

        # Gráfico integrado
        self.figura_modelo = Figure(
            figsize=(7, 5.2),
            facecolor="#252525",
        )
        self.canvas_modelo = CanvasGrafica(self.figura_modelo)
        self.canvas_modelo.setMinimumHeight(ALTO_GRAFICO)

                # Selector de visualización. Solo estará activo tras entrenar.
        self.combo_vista_modelo = ComboSinRueda()
        self.combo_vista_modelo.addItem(
            "Regresión por variable", "variable"
        )
        self.combo_vista_modelo.addItem(
            "Reales vs. predichos", "predichos"
        )
        self.combo_vista_modelo.setEnabled(False)

        self.combo_variable_modelo = ComboSinRueda()
        self.combo_variable_modelo.setEnabled(False)
        self.etiqueta_variable_modelo = QLabel("Variable de entrada:")

        fila_selector = QHBoxLayout()
        fila_selector.addWidget(QLabel("Visualización:"))
        fila_selector.addWidget(self.combo_vista_modelo)
        fila_selector.addSpacing(12)
        fila_selector.addWidget(self.etiqueta_variable_modelo)
        fila_selector.addWidget(self.combo_variable_modelo)
        fila_selector.addStretch()

        self.etiqueta_contexto_grafico = QLabel("")
        self.etiqueta_contexto_grafico.setWordWrap(True)

        layout_modelo.addLayout(fila_resultados)
        layout_modelo.addLayout(fila_selector)
        layout_modelo.addWidget(self.etiqueta_contexto_grafico)
        layout_modelo.addWidget(self.canvas_modelo, stretch=1)

    def _conectar_señales(self) -> None:
        """Agrupa todas las conexiones de botones y eventos de texto."""
        self.boton_cargar.clicked.connect(self.elegir_archivo)
        self.boton_vista_inicial.clicked.connect(
            self.canvas_modelo.restablecer_vista)
        self.boton_validar.clicked.connect(self.validar_variables)
        self.boton_separar.clicked.connect(self.separar)
        self.boton_aplicar.clicked.connect(self.aplicar_preprocesado_gui)
        self.boton_crear_modelo.clicked.connect(self.crear_modelo_gui)
        self.combo_vista_modelo.currentIndexChanged.connect(
            self.actualizar_grafico_modelo
        )
        self.combo_variable_modelo.currentIndexChanged.connect(
            self.actualizar_grafico_modelo
        )

        self.combo_estrategia.currentIndexChanged.connect(
            self.actualizar_opcion_constante)
        self.selector_entradas.seleccion_cambiada.connect(
            self.descartar_seleccion)
        self.selector_salida.seleccion_cambiada.connect(
            self.descartar_seleccion)
        self.entrada_porcentaje.textChanged.connect(
            self.actualizar_porcentaje_entrenamiento)

    def _aplicar_estilos(self) -> None:
        """Aplica las reglas QSS a la ventana, incluyendo los paneles."""
        self.setStyleSheet("""
            QWidget { background-color: #1e1e1e; color: #e0e0e0;}
            QTableWidget {
                background-color: #252525;
                color: white;
                gridline-color: #444;
                border: 1px solid #555;
            }
            QHeaderView::section {
                background-color: #3b3b3b;
                color: #8ab4f8;
                border: 1px solid #555;
                padding: 4px;
                font-weight: bold;
            }

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
            QPushButton:disabled { color: #777777; border: 1px solid #444; }

            SelectorColumnas { text-align: left; }
            QMenu { border: 1px solid #555; }

            QComboBox, QLineEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                font-size: 11px;
                outline: none;
            }

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

            /* --- NUEVO: Estilo moderno para barras de desplazamiento --- */
            QScrollBar:vertical {
                border: none;
                background-color: #1e1e1e;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                min-height: 20px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {background-color: #8ab4f8;}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }

            QScrollBar:horizontal {
                border: none;
                background-color: #1e1e1e;
                height: 8px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #555555;
                min-width: 20px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover { background-color: #8ab4f8;}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }

        """)

    # ----------------------------LÓGICA DE EVENTOS----------------------------
    def elegir_archivo(self) -> None:
        """Abre el explorador de archivos para elegir un dataset."""
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar dataset", "", FILTRO_DATOS)
        if not ruta:
            return  # el usuario cerró el explorador sin elegir nada
        self.cargar_archivo(ruta)

    def actualizar_porcentaje_entrenamiento(self, texto: str) -> None:
        """Muestra el porcentaje de entrenamiento complementario al de test."""
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
        self.selector_entradas.establecer_opciones(columnas)
        self.selector_salida.establecer_opciones(columnas)

    def limpiar_interfaz(self) -> None:
        """Quita el dataset de la interfaz y la deja como al abrirla."""
        self.datos = None
        self.ruta_datos = None
        self.etiqueta_ruta.setText("Ningún archivo cargado")

        # clear() only empties the cells; the row and column counts remain
        self.tabla.clear()
        self.tabla.setRowCount(0)
        self.tabla.setColumnCount(0)

        self.selector_entradas.establecer_opciones([])
        self.selector_salida.establecer_opciones([])

        self.entrada_porcentaje.setText("20")
        self.entrada_semilla.setText("42")
        self.descartar_seleccion()

    def descartar_seleccion(self) -> None:
        """Anula la selección; hay que validarla y separar de nuevo."""
        self.entradas = None
        self.salida = None
        self.boton_separar.setEnabled(False)
        self.invalidar_separacion()

    def invalidar_separacion(self) -> None:
        """Descarta la separación y todo lo creado a partir de ella."""
        self.datos_entrenamiento = None
        self.datos_test = None
        self.preprocesado: str | None = None
        self.modelo = None
        # Indica si las columnas estan libres de nulos
        self.datos_listos_para_modelo = False

        self.etiqueta_separacion.setText("Datos sin separar")
        self.grupo_preprocesado.setEnabled(False)
        self.tabla_faltantes.setRowCount(0)
        self._ajustar_alto_faltantes()

        self.etiqueta_faltantes.setText(
            "Separa los datos para analizar los valores inexistentes.")
        self.etiqueta_estado_preprocesado.setText("Preprocesado pendiente")
        self.etiqueta_disponibilidad_modelo.setText(
            "Creación del modelo: no disponible")
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
            QMessageBox.warning(
                self, "Atención", "Primero debes cargar un archivo de datos.")
            return

        # 1. Extraer los textos que el usuario ha seleccionado en la interfaz
        entradas_seleccionadas = self.selector_entradas.seleccionadas()
        salida = self.selector_salida.seleccionadas()
        salida_seleccionada = salida[0] if salida else ""

        # 2. Enviar a tu función blindada con try/except
        try:
            validar_seleccion(
                self.datos, entradas_seleccionadas, salida_seleccionada)
        except ErrorSeleccionColumnas as error:
            # Si la lógica detecta un fallo, mostramos el mensaje exacto que
            # programaste
            self.descartar_seleccion()
            QMessageBox.warning(self, "Error de Selección", str(error))
            return

        # The split is only available after a confirmed selection
        self.entradas = entradas_seleccionadas
        self.salida = salida_seleccionada
        self.boton_separar.setEnabled(True)
        QMessageBox.information(
            self, "Éxito",
            "Las variables seleccionadas son válidas y están listas "
            "para entrenar.")

    def separar(self) -> None:
        """Separa en entrenamiento y test según porcentaje y semilla."""
        # A new split always discards the previous one and what was built on it
        self.invalidar_separacion()

        try:
            porcentaje_test = float(
                self.entrada_porcentaje.text().strip().replace(",", "."))
        except ValueError:
            QMessageBox.warning(self, "Error en el porcentaje",
                                "El porcentaje de test debe ser un número "
                                "entre 1 y 99.")
            return

        try:
            semilla = int(self.entrada_semilla.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Error en la semilla",
                                "La semilla debe ser un número entero.")
            return

        # Range checks, minimum rows and empty sets are done by data_splitter
        try:
            entrenamiento, test = separar_datos(
                self.datos, porcentaje_test, semilla)
        except ErrorSeparacionDatos as error:
            QMessageBox.warning(self, "Error al separar los datos", str(error))
            return

        # Normalizar las columnas seleccionadas sin modificar los datos
        # originales
        columnas = self.entradas + [self.salida]

        try:
            entrenamiento = normalizar_columnas(entrenamiento, columnas)
            test = normalizar_columnas(test, columnas)
        except ErrorPreprocesado as error:
            QMessageBox.warning(
                self, "Error al analizar los datos", str(error))
            return

        self.datos_entrenamiento = entrenamiento
        self.datos_test = test

        # Detectar los valores inexistentes tras la separación
        self.actualizar_deteccion()

        self.etiqueta_separacion.setText(
            f"Entrenamiento: {len(entrenamiento)} filas | "
            f"Test: {len(test)} filas")
        QMessageBox.information(
            self, "Separación realizada",
            "Los datos se han separado correctamente.\n\n"
            f"Entrenamiento: {len(entrenamiento)} filas\n"
            f"Test: {len(test)} filas")

    def actualizar_opcion_constante(self, _indice: int) -> None:
        """Habilita el campo constante solo para su estrategia."""
        self.entrada_constante.setEnabled(
            self.combo_estrategia.currentData() == "constante")

    def actualizar_deteccion(self) -> None:
        """Muestra los nulos por columna y actualiza el estado del modelo."""
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
        self._ajustar_alto_faltantes()

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
                f"Valores inexistentes: {total_entrenamiento} en "
                f"entrenamiento "
                f"y {total_test} en test."
            )
            self.etiqueta_estado_preprocesado.setText(
                "Elige una estrategia y pulsa Aplicar preprocesado."
            )
            self.etiqueta_disponibilidad_modelo.setText(
                "Creación del modelo: no disponible hasta tratar los nulos"
            )

    def aplicar_preprocesado_gui(self) -> None:
        """Aplica la estrategia elegida y comunica el resultado de ambos."""
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

        self.combo_vista_modelo.setEnabled(False)
        self.combo_variable_modelo.blockSignals(True)
        self.combo_variable_modelo.clear()
        self.combo_variable_modelo.blockSignals(False)
        self.combo_variable_modelo.setEnabled(False)
        self.etiqueta_contexto_grafico.setText("")

        self.figura_modelo.clear()
        self.canvas_modelo.recordar_vista()
        self.boton_vista_inicial.setEnabled(False)
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

            # Vista inicial: primera entrada, manteniendo las demás
            # en sus medias del conjunto de entrenamiento.
            grafico = preparar_grafico_variable(
                resultado["modelo"],
                self.datos_entrenamiento,
                self.datos_test,
                resultado["entradas"],
                resultado["salida"],
                resultado["entradas"][0],
            )
            self.dibujar_grafico_modelo(grafico)

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

        # Cargar las columnas seleccionables sin disparar redibujados.
        self.combo_vista_modelo.blockSignals(True)
        self.combo_variable_modelo.blockSignals(True)

        self.combo_vista_modelo.setCurrentIndex(0)
        self.combo_variable_modelo.clear()
        self.combo_variable_modelo.addItems(resultado["entradas"])

        self.combo_variable_modelo.blockSignals(False)
        self.combo_vista_modelo.blockSignals(False)

        multiple = len(resultado["entradas"]) > 1

        self.combo_vista_modelo.setEnabled(multiple)
        self.combo_variable_modelo.setEnabled(multiple)
        self.etiqueta_variable_modelo.setEnabled(multiple)

        self.etiqueta_contexto_grafico.setText(
            "Recta del modelo completo: las otras variables se "
            "mantienen en sus medias de entrenamiento. "
            "Los puntos muestran valores reales sin ajustar."
        )

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

    
    def actualizar_grafico_modelo(self, _indice: int = -1) -> None:
        """Cambia la vista o la columna sin reentrenar el modelo."""
        if self.resultado_modelo is None:
            return

        por_variable = (
            self.combo_vista_modelo.currentData() == "variable"
        )
        multiple = len(self.resultado_modelo["entradas"]) > 1

        self.combo_variable_modelo.setEnabled(por_variable and multiple)
        self.etiqueta_variable_modelo.setEnabled(por_variable and multiple)

        try:
            if por_variable:
                grafico = preparar_grafico_variable(
                    self.modelo,
                    self.datos_entrenamiento,
                    self.datos_test,
                    self.resultado_modelo["entradas"],
                    self.resultado_modelo["salida"],
                    self.combo_variable_modelo.currentText(),
                )

                self.etiqueta_contexto_grafico.setText(
                    "Recta del modelo completo: las otras variables se "
                    "mantienen en sus medias de entrenamiento. "
                    "Los puntos muestran valores reales sin ajustar."
                )

            else:
                grafico = self.resultado_modelo["grafico"]

                self.etiqueta_contexto_grafico.setText(
                    "La diagonal representa predicciones perfectas (y = x)."
                )

            self.dibujar_grafico_modelo(grafico)

        except Exception as error:
            QMessageBox.warning(
                self,
                "Error al actualizar la gráfica",
                str(error),
            )


    def dibujar_grafico_modelo(self, grafico: dict) -> None:
        """Dibuja los datos preparados por el módulo model."""
        self.figura_modelo.clear()
        ejes = self.figura_modelo.add_subplot(111)
        ejes.set_facecolor("#252525")

        if grafico["tipo"] in ("simple", "variable"):
            
            ejes.set_title(
                f"Efecto de {grafico['eje_x']} sobre {grafico['eje_y']}",
                color="#e0e0e0",
            )

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
                label="Recta condicional del modelo",
                color="#ff5252",
                linewidth=3,
                zorder=10,
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
        # Above the axes: "best" recomputes on each draw and would hide data
        ejes.legend(
            loc="lower left",
            bbox_to_anchor=(0, 1.01),
            borderaxespad=0,
            ncols=3,
            facecolor="#333333",
            edgecolor="#777777",
            labelcolor="white",
        )

        self.figura_modelo.tight_layout()
        self.canvas_modelo.recordar_vista()
        self.boton_vista_inicial.setEnabled(True)
        self.canvas_modelo.draw_idle()


def ejecutar() -> None:
    """Abre la ventana principal y espera a que el usuario la cierre."""
    app = QApplication(sys.argv)
    ventana = VentanaPrincipal()
    ventana.showMaximized()
    sys.exit(app.exec())
