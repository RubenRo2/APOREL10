"""Pruebas del selector de columnas con botón y desplegable."""

import os

import pandas as pd
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6.QtWidgets")

from matplotlib.backend_bases import (  # noqa: E402
    MouseButton,
    MouseEvent,
)
from PySide6.QtCore import QPoint, QPointF, QRect, Qt  # noqa: E402
from PySide6.QtGui import QWheelEvent  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import (  # noqa: E402
    QAbstractButton,
    QApplication,
    QMessageBox,
    QScrollArea,
)
from aporel10.gui import (  # noqa: E402
    ALTO_MIN_TABLA_FALTANTES,
    ANCHO_SELECTOR,
    FACTOR_ZOOM_RUEDA,
    RETARDO_REDIBUJADO_MS,
    MAX_FILAS_SELECTOR,
    SelectorColumnas,
    VentanaPrincipal,
    calcular_columnas,
)


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def casillas(selector):
    return selector.menu().findChildren(QAbstractButton)


def test_multiple_empieza_vacio_y_permite_varias(app):
    selector = SelectorColumnas(multiple=True)
    selector.establecer_opciones(["a", "b", "c"])
    assert selector.seleccionadas() == []

    selector.seleccionar(["a", "c"])
    assert selector.seleccionadas() == ["a", "c"]
    assert "2 de 3" in selector.text()


def test_unico_marca_la_primera_y_solo_admite_una(app):
    selector = SelectorColumnas(multiple=False)
    selector.establecer_opciones(["a", "b", "c"])
    assert selector.seleccionadas() == ["a"]

    selector.seleccionar(["c"])
    assert selector.seleccionadas() == ["c"]
    assert selector.text() == "c"


def test_avisa_una_vez_por_cada_cambio(app):
    avisos = []
    unico = SelectorColumnas(multiple=False)
    unico.establecer_opciones(["a", "b"])
    unico.seleccion_cambiada.connect(lambda: avisos.append(1))

    unico.seleccionar(["b"])
    assert len(avisos) == 1


def test_establecer_opciones_no_avisa_y_sustituye_las_anteriores(app):
    avisos = []
    selector = SelectorColumnas(multiple=True)
    selector.seleccion_cambiada.connect(lambda: avisos.append(1))

    selector.establecer_opciones(["a", "b"])
    selector.establecer_opciones(["c"])
    assert avisos == []
    assert [casilla.text() for casilla in casillas(selector)] == ["c"]


def test_sin_opciones_queda_desactivado(app):
    selector = SelectorColumnas(multiple=False)
    assert not selector.isEnabled()
    assert selector.seleccionadas() == []

    selector.establecer_opciones(["a"])
    assert selector.isEnabled()


def test_ancho_fijo_aunque_el_nombre_sea_muy_largo(app):
    nombre = "columna_con_un_nombre_larguisimo_" * 3
    selector = SelectorColumnas(multiple=False)
    selector.establecer_opciones([nombre])

    assert selector.minimumWidth() == selector.maximumWidth() == ANCHO_SELECTOR
    assert selector.seleccionadas() == [nombre]
    assert selector.toolTip() == nombre
    assert selector.text() != nombre


def test_ampersand_se_muestra_y_se_devuelve_sin_alterar(app):
    selector = SelectorColumnas(multiple=False)
    selector.establecer_opciones(["R&D"])

    assert selector.seleccionadas() == ["R&D"]
    assert casillas(selector)[0].text() == "R&&D"
    assert selector.text() == "R&&D"


def test_todas_las_opciones_visibles_sin_scroll(app):
    columnas = [f"columna_{i}" for i in range(60)]
    selector = SelectorColumnas(multiple=True)
    selector.establecer_opciones(columnas)
    menu = selector.menu()

    assert len(casillas(selector)) == 60
    assert not menu.findChildren(QScrollArea)
    pantalla = selector.screen().availableGeometry()
    assert menu.sizeHint().height() <= pantalla.height()
    assert menu.sizeHint().width() <= pantalla.width()


@pytest.mark.parametrize("n, esperado", [
    (1, 1),
    (MAX_FILAS_SELECTOR, 1),
    (MAX_FILAS_SELECTOR + 1, 2),
    (MAX_FILAS_SELECTOR * 3, 3),
])
def test_calcular_columnas_reparte_por_filas(n, esperado):
    assert calcular_columnas(n, 20, 100, 2000, 2000) == esperado


def test_calcular_columnas_respeta_la_altura_disponible():
    assert calcular_columnas(10, 20, 100, 100, 2000) == 2


def test_calcular_columnas_respeta_el_ancho_disponible():
    assert calcular_columnas(100, 20, 100, 2000, 300) == 3


def test_calcular_columnas_con_pantalla_minima_devuelve_al_menos_una():
    assert calcular_columnas(5, 20, 100, 1, 1) == 1


@pytest.fixture
def ventana(app, monkeypatch, tmp_path):
    avisos = []
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    monkeypatch.setattr(
        QMessageBox, "warning", lambda *args: avisos.append(args[2]))
    ruta = tmp_path / "datos.csv"
    pd.DataFrame({
        "x": [1.0, 2.0, 3.0, 4.0],
        "z": [2.0, 1.0, 4.0, 3.0],
        "y": [5.0, 6.0, 7.0, 8.0],
    }).to_csv(ruta, index=False)

    ventana = VentanaPrincipal()
    ventana.avisos = avisos
    ventana.cargar_archivo(str(ruta))
    yield ventana
    ventana.close()


def test_cargar_archivo_rellena_los_dos_selectores(ventana):
    assert len(casillas(ventana.selector_entradas)) == 3
    assert ventana.selector_entradas.seleccionadas() == []
    assert ventana.selector_salida.seleccionadas() == ["x"]


def test_validar_usa_la_seleccion_de_los_selectores(ventana):
    ventana.selector_entradas.seleccionar(["x", "z"])
    ventana.selector_salida.seleccionar(["y"])
    ventana.validar_variables()

    assert ventana.entradas == ["x", "z"]
    assert ventana.salida == "y"
    assert ventana.boton_separar.isEnabled()


def test_validar_sin_entradas_muestra_error(ventana):
    ventana.selector_salida.seleccionar(["y"])
    ventana.validar_variables()

    assert ventana.avisos
    assert not ventana.boton_separar.isEnabled()


@pytest.mark.parametrize("selector, columnas", [
    ("selector_entradas", ["z"]),
    ("selector_salida", ["z"]),
])
def test_cambiar_la_seleccion_descarta_la_validacion(
        ventana, selector, columnas):
    ventana.selector_entradas.seleccionar(["x"])
    ventana.selector_salida.seleccionar(["y"])
    ventana.validar_variables()
    assert ventana.boton_separar.isEnabled()

    getattr(ventana, selector).seleccionar(columnas)
    assert ventana.entradas is None
    assert not ventana.boton_separar.isEnabled()


def test_limpiar_interfaz_vacia_los_selectores(ventana):
    ventana.limpiar_interfaz()

    assert casillas(ventana.selector_entradas) == []
    assert casillas(ventana.selector_salida) == []
    assert not ventana.selector_entradas.isEnabled()
    assert not ventana.selector_salida.isEnabled()


def abrir_menu(selector):
    menu = selector.menu()
    menu.popup(selector.mapToGlobal(selector.rect().bottomLeft()))
    QApplication.processEvents()
    return menu


def pulsar(casilla):
    QTest.mouseClick(casilla, Qt.MouseButton.LeftButton)
    QApplication.processEvents()


def test_multiple_sigue_abierto_tras_pulsar_varias(app):
    selector = SelectorColumnas(multiple=True)
    selector.establecer_opciones(["a", "b", "c"])
    menu = abrir_menu(selector)
    primera, segunda, _ = casillas(selector)

    pulsar(primera)
    pulsar(segunda)
    assert menu.isVisible()
    assert selector.seleccionadas() == ["a", "b"]
    menu.close()


def test_unico_se_cierra_al_pulsar_una_opcion(app):
    selector = SelectorColumnas(multiple=False)
    selector.establecer_opciones(["a", "b"])
    menu = abrir_menu(selector)

    pulsar(casillas(selector)[1])
    assert not menu.isVisible()
    assert selector.seleccionadas() == ["b"]


def test_tabla_de_metricas_pequena_y_grafica_debajo(ventana):
    ventana.resize(1400, 1200)
    ventana.show()
    QApplication.processEvents()
    tabla = ventana.tabla_metricas
    grafica = ventana.canvas_modelo

    assert tabla.width() < grafica.width() / 2
    assert grafica.mapTo(ventana, grafica.rect().topLeft()).y() >= (
        tabla.mapTo(ventana, tabla.rect().bottomLeft()).y())
    assert tabla.verticalScrollBar().maximum() == 0
    assert tabla.horizontalScrollBar().maximum() == 0


def test_valores_de_metricas_alineados_a_la_derecha(ventana):
    alineacion = ventana.tabla_metricas.item(0, 1).textAlignment()

    assert Qt.AlignmentFlag(alineacion) & Qt.AlignmentFlag.AlignRight


def test_tablas_sin_barras_de_scroll(ventana):
    apagada = Qt.ScrollBarPolicy.ScrollBarAlwaysOff

    for tabla in (ventana.tabla_faltantes, ventana.tabla_metricas):
        assert tabla.verticalScrollBarPolicy() == apagada
        assert tabla.horizontalScrollBarPolicy() == apagada


def test_tabla_de_faltantes_crece_y_muestra_todas_las_filas(
        ventana, tmp_path):
    columnas = {f"c{i}": [float(j) for j in range(10)] for i in range(30)}
    ruta = tmp_path / "ancho.csv"
    pd.DataFrame(columnas).to_csv(ruta, index=False)
    ventana.show()
    ventana.cargar_archivo(str(ruta))
    ventana.selector_entradas.seleccionar(list(columnas)[:-1])
    ventana.selector_salida.seleccionar(["c29"])
    ventana.validar_variables()
    ventana.boton_separar.click()
    QApplication.processEvents()
    tabla = ventana.tabla_faltantes

    assert tabla.rowCount() == 30
    assert tabla.height() > ALTO_MIN_TABLA_FALTANTES
    assert tabla.verticalScrollBar().maximum() == 0

    ventana.limpiar_interfaz()
    assert tabla.height() == ALTO_MIN_TABLA_FALTANTES


GRAFICO_SIMPLE = {
    "tipo": "simple",
    "train_x": [1.0, 2.0, 3.0],
    "train_y": [1.0, 2.0, 3.0],
    "test_x": [4.0],
    "test_y": [4.0],
    "linea_x": [1.0, 4.0],
    "linea_y": [1.0, 4.0],
    "eje_x": "x",
    "eje_y": "y",
}


@pytest.fixture
def grafica(ventana):
    ventana.resize(1400, 1200)
    ventana.show()
    ventana.dibujar_grafico_modelo(GRAFICO_SIMPLE)
    QApplication.processEvents()
    ventana.canvas_modelo.draw()
    return ventana


def limites(ventana):
    ejes = ventana.figura_modelo.axes[0]
    return (*ejes.get_xlim(), *ejes.get_ylim())


def centro_de_los_ejes(ventana):
    ejes = ventana.figura_modelo.axes[0]
    return ejes.transAxes.transform((0.5, 0.5))


def mover_rueda(ventana, posicion=None, notches=1):
    canvas = ventana.canvas_modelo
    if posicion is None:
        x, y = centro_de_los_ejes(ventana)
        ratio = canvas.device_pixel_ratio
        posicion = QPointF(x / ratio, canvas.height() - y / ratio)
    evento = QWheelEvent(
        posicion,
        QPointF(canvas.mapToGlobal(posicion.toPoint())),
        QPoint(),
        QPoint(0, 120 * notches),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QApplication.sendEvent(canvas, evento)
    esperar_zoom(ventana)
    return evento


def esperar_zoom(ventana):
    while ventana.canvas_modelo.zoom_en_curso():
        QTest.qWait(5)


def evento_raton(ventana, tipo, x, y, boton=MouseButton.LEFT):
    MouseEvent(tipo, ventana.canvas_modelo, x, y, boton)._process()


def arrastrar(ventana, dx, dy, boton=MouseButton.LEFT, origen=None):
    x, y = centro_de_los_ejes(ventana) if origen is None else origen
    evento_raton(ventana, "button_press_event", x, y, boton)
    evento_raton(ventana, "motion_notify_event", x + dx, y + dy, boton)
    evento_raton(ventana, "button_release_event", x + dx, y + dy, boton)


def test_boton_vista_inicial_desactivado_sin_grafica(ventana):
    assert not ventana.boton_vista_inicial.isEnabled()


def test_vista_inicial_se_activa_al_dibujar_y_no_al_limpiar(grafica):
    assert grafica.boton_vista_inicial.isEnabled()

    grafica.limpiar_interfaz()
    assert not grafica.boton_vista_inicial.isEnabled()


def test_arrastrar_mueve_sin_activar_ningun_modo(grafica):
    x_min, x_max, y_min, y_max = limites(grafica)

    arrastrar(grafica, 80, 40)
    nuevo = limites(grafica)
    assert nuevo[0] < x_min and nuevo[1] < x_max
    assert nuevo[2] < y_min and nuevo[3] < y_max
    assert nuevo[1] - nuevo[0] == pytest.approx(x_max - x_min)


def test_soltar_termina_el_movimiento(grafica):
    arrastrar(grafica, 80, 40)
    tras_soltar = limites(grafica)
    x, y = centro_de_los_ejes(grafica)

    evento_raton(grafica, "motion_notify_event", x + 200, y + 200)
    assert limites(grafica) == tras_soltar


def test_arrastrar_fuera_de_los_ejes_no_mueve(grafica):
    inicial = limites(grafica)

    arrastrar(grafica, 80, 40, origen=(1, 1))
    assert limites(grafica) == inicial


def test_boton_derecho_no_mueve(grafica):
    inicial = limites(grafica)

    arrastrar(grafica, 80, 40, boton=MouseButton.RIGHT)
    assert limites(grafica) == inicial


def test_rueda_acerca_y_aleja(grafica):
    inicial = limites(grafica)
    ancho_inicial = inicial[1] - inicial[0]

    evento = mover_rueda(grafica)
    x_min, x_max, _, _ = limites(grafica)
    assert evento.isAccepted()
    assert x_max - x_min == pytest.approx(ancho_inicial * FACTOR_ZOOM_RUEDA)

    mover_rueda(grafica, notches=-1)
    assert limites(grafica) == pytest.approx(inicial)


def test_rueda_fuera_de_los_ejes_deja_pasar_el_scroll(grafica):
    inicial = limites(grafica)

    evento = mover_rueda(grafica, posicion=QPointF(1, 1))
    assert not evento.isAccepted()
    assert limites(grafica) == inicial


def test_rueda_sin_grafica_deja_pasar_el_scroll(ventana):
    ventana.resize(1400, 1200)
    ventana.show()
    QApplication.processEvents()

    assert not mover_rueda(ventana, posicion=QPointF(50, 50)).isAccepted()


def test_boton_vista_inicial_deshace_movimiento_y_zoom(grafica):
    inicial = limites(grafica)
    arrastrar(grafica, 80, 40)
    mover_rueda(grafica)
    assert limites(grafica) != pytest.approx(inicial)

    grafica.boton_vista_inicial.click()
    assert limites(grafica) == pytest.approx(inicial)


def test_nueva_grafica_usa_su_propia_vista_inicial(grafica):
    mover_rueda(grafica)
    otro = dict(GRAFICO_SIMPLE, linea_x=[1.0, 40.0], linea_y=[1.0, 40.0])
    grafica.dibujar_grafico_modelo(otro)
    grafica.canvas_modelo.draw()
    inicial = limites(grafica)
    assert inicial[1] > 10

    mover_rueda(grafica)
    grafica.boton_vista_inicial.click()
    assert limites(grafica) == pytest.approx(inicial)


def test_arrastrar_no_redibuja_la_figura_hasta_soltar(grafica):
    canvas = grafica.canvas_modelo
    x, y = centro_de_los_ejes(grafica)
    evento_raton(grafica, "button_press_event", x, y)
    evento_raton(grafica, "motion_notify_event", x + 20, y)

    assert canvas._vista_previa is not None
    assert canvas._redibujado.isActive()

    evento_raton(grafica, "button_release_event", x + 20, y)
    QTest.qWait(30)
    assert canvas._vista_previa is None
    assert canvas._dibujado[0] == canvas.figure.axes[0].get_xlim()


def test_pausa_en_el_gesto_redibuja_sin_soltar(grafica):
    canvas = grafica.canvas_modelo
    x, y = centro_de_los_ejes(grafica)
    evento_raton(grafica, "button_press_event", x, y)
    evento_raton(grafica, "motion_notify_event", x + 20, y)

    QTest.qWait(RETARDO_REDIBUJADO_MS + 80)
    assert canvas._vista_previa is None
    evento_raton(grafica, "button_release_event", x + 20, y)


def test_vista_previa_coincide_con_el_dibujo_real(grafica):
    canvas = grafica.canvas_modelo
    ejes = canvas.figure.axes[0]
    x, y = centro_de_los_ejes(grafica)
    x0, y0, ancho, alto = ejes.bbox.bounds
    interior = QRect(
        int(x0) + 60, canvas.height() - int(y0 + alto) + 60,
        int(ancho) - 120, int(alto) - 120)

    evento_raton(grafica, "button_press_event", x, y)
    evento_raton(grafica, "motion_notify_event", x + 40, y)
    previa = canvas.grab(interior).toImage()
    assert canvas._vista_previa is not None
    evento_raton(grafica, "button_release_event", x + 40, y)
    canvas.draw()
    real = canvas.grab(interior).toImage()

    distintos = sum(
        previa.pixelColor(i, j).value() != real.pixelColor(i, j).value()
        for i in range(0, previa.width(), 5)
        for j in range(0, previa.height(), 5))
    total = (previa.width() // 5 + 1) * (previa.height() // 5 + 1)
    assert distintos / total < 0.02


def test_mover_mucho_redibuja_para_rellenar_el_hueco(grafica):
    canvas = grafica.canvas_modelo
    ancho = canvas.figure.axes[0].bbox.width
    x, y = centro_de_los_ejes(grafica)
    evento_raton(grafica, "button_press_event", x, y)
    evento_raton(grafica, "motion_notify_event", x + ancho / 2, y)

    assert canvas._vista_previa is None
    evento_raton(grafica, "button_release_event", x + ancho / 2, y)


def test_varios_pasos_de_rueda_se_acumulan(grafica):
    inicial = limites(grafica)
    canvas = grafica.canvas_modelo
    x, y = centro_de_los_ejes(grafica)
    for _ in range(2):
        MouseEvent("scroll_event", canvas, x, y, step=1)._process()
    assert canvas.zoom_en_curso()

    esperar_zoom(grafica)
    x_min, x_max, _, _ = limites(grafica)
    assert x_max - x_min == pytest.approx(
        (inicial[1] - inicial[0]) * FACTOR_ZOOM_RUEDA ** 2)


def test_vista_inicial_cancela_el_zoom_en_curso(grafica):
    inicial = limites(grafica)
    canvas = grafica.canvas_modelo
    x, y = centro_de_los_ejes(grafica)
    MouseEvent("scroll_event", canvas, x, y, step=1)._process()

    grafica.boton_vista_inicial.click()
    assert not canvas.zoom_en_curso()
    QTest.qWait(40)
    assert limites(grafica) == pytest.approx(inicial)


def test_limpiar_durante_el_zoom_no_falla(grafica):
    canvas = grafica.canvas_modelo
    x, y = centro_de_los_ejes(grafica)
    MouseEvent("scroll_event", canvas, x, y, step=1)._process()

    grafica.limpiar_interfaz()
    assert not canvas.zoom_en_curso()
    QTest.qWait(40)
    canvas.draw()
    assert canvas._dibujado is None


GRAFICO_MULTIPLE = {
    "tipo": "multiple",
    "train_real": [1.0, 2.0, 3.0],
    "train_predicho": [1.1, 1.9, 3.2],
    "test_real": [4.0],
    "test_predicho": [3.8],
    "linea_min": 1.0,
    "linea_max": 4.0,
}


def test_vista_inicial_sin_grafica_no_hace_nada(ventana):
    ventana.canvas_modelo.restablecer_vista()
    assert not ventana.figura_modelo.axes


def test_evento_de_rueda_fuera_de_los_ejes_no_hace_zoom(grafica):
    inicial = limites(grafica)
    canvas = grafica.canvas_modelo
    # Direct call: matplotlib swallows exceptions raised inside its callbacks
    canvas._zoom_con_rueda(MouseEvent("scroll_event", canvas, 0, 0, step=1))

    assert not canvas.zoom_en_curso()
    assert limites(grafica) == inicial


def test_touchpad_no_acerca_mas_que_un_paso_de_rueda(grafica):
    inicial = limites(grafica)
    canvas = grafica.canvas_modelo
    x, y = centro_de_los_ejes(grafica)
    MouseEvent("scroll_event", canvas, x, y, step=30)._process()

    esperar_zoom(grafica)
    x_min, x_max, _, _ = limites(grafica)
    assert x_max - x_min == pytest.approx(
        (inicial[1] - inicial[0]) * FACTOR_ZOOM_RUEDA)


def test_arrastrar_cancela_el_zoom_en_curso(grafica):
    canvas = grafica.canvas_modelo
    x, y = centro_de_los_ejes(grafica)
    MouseEvent("scroll_event", canvas, x, y, step=1)._process()

    evento_raton(grafica, "button_press_event", x, y)
    assert not canvas.zoom_en_curso()
    evento_raton(grafica, "button_release_event", x, y)


def test_nueva_grafica_cancela_el_zoom_en_curso(grafica):
    canvas = grafica.canvas_modelo
    x, y = centro_de_los_ejes(grafica)
    MouseEvent("scroll_event", canvas, x, y, step=1)._process()

    grafica.dibujar_grafico_modelo(GRAFICO_SIMPLE)
    assert not canvas.zoom_en_curso()


@pytest.mark.parametrize(
    "factor, agotada",
    [(0.9, False), (1.1, False), (0.5, True), (2.0, True)],
)
def test_vista_previa_se_descarta_si_borrosa_o_con_hueco(
        grafica, factor, agotada):
    canvas = grafica.canvas_modelo
    ejes = grafica.figura_modelo.axes[0]
    x_min, x_max = ejes.get_xlim()
    centro = (x_min + x_max) / 2
    ejes.set_xlim(centro + (x_min - centro) * factor,
                  centro + (x_max - centro) * factor)

    assert canvas._vista_agotada(ejes) is agotada


@pytest.mark.parametrize("grafico", [GRAFICO_SIMPLE, GRAFICO_MULTIPLE])
def test_leyenda_queda_encima_de_los_ejes(grafica, grafico):
    grafica.dibujar_grafico_modelo(grafico)
    grafica.canvas_modelo.draw()
    ejes = grafica.figura_modelo.axes[0]
    leyenda = ejes.get_legend().get_window_extent()

    assert leyenda.y0 >= ejes.bbox.y1
    assert leyenda.y1 <= grafica.figura_modelo.bbox.y1


def test_grafica_de_varias_entradas_se_mueve_y_vuelve(grafica):
    grafica.dibujar_grafico_modelo(GRAFICO_MULTIPLE)
    grafica.canvas_modelo.draw()
    inicial = limites(grafica)

    arrastrar(grafica, 30, 10)
    assert limites(grafica) != pytest.approx(inicial)

    grafica.boton_vista_inicial.click()
    assert limites(grafica) == pytest.approx(inicial)
