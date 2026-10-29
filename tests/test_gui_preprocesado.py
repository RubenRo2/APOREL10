
"""Pruebas de integración de la GUI, si PySide6 está instalado."""

import os

import pandas as pd
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6.QtWidgets")

from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402
from aporel10.gui import VentanaPrincipal  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def ventana(app, monkeypatch):
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args: None)

    ventana = VentanaPrincipal()
    ventana.datos = pd.DataFrame({
        "x": [1.0, 2.0, None, 4.0, None, 6.0, 7.0, 8.0],
        "y": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0],
    })
    ventana.lista_entradas.addItems(["x", "y"])
    ventana.combo_salida.addItems(["x", "y"])
    ventana.lista_entradas.item(0).setSelected(True)
    ventana.combo_salida.setCurrentText("y")
    ventana.validar_variables()
    ventana.entrada_porcentaje.setText("50")

    yield ventana
    ventana.close()


def test_desde_separacion_hasta_preprocesado_y_repeticion(ventana):
    ventana.separar()

    assert not ventana.datos_listos_para_modelo
    assert ventana.boton_aplicar.isEnabled()
    assert ventana.tabla_faltantes.rowCount() == 2
    assert sum(
        int(ventana.tabla_faltantes.item(0, col).text())
        for col in (1, 2)
    ) == 2

    ventana.combo_estrategia.setCurrentIndex(1)
    ventana.aplicar_preprocesado_gui()

    assert ventana.preprocesado is not None
    assert ventana.datos_listos_para_modelo
    assert not ventana.boton_aplicar.isEnabled()
    assert ventana.datos_entrenamiento["x"].notna().all()
    assert ventana.datos_test["x"].notna().all()

    ventana.separar()

    assert ventana.preprocesado is None
    assert not ventana.datos_listos_para_modelo
    assert ventana.boton_aplicar.isEnabled()

    ventana.lista_entradas.item(0).setSelected(False)

    assert ventana.datos_entrenamiento is None
    assert ventana.preprocesado is None
    assert not ventana.datos_listos_para_modelo


def test_constante_invalida_no_modifica_los_conjuntos(ventana):
    ventana.separar()

    original_entrenamiento = ventana.datos_entrenamiento.copy(deep=True)
    original_test = ventana.datos_test.copy(deep=True)

    ventana.combo_estrategia.setCurrentIndex(3)
    assert ventana.entrada_constante.isEnabled()

    ventana.entrada_constante.setText("texto")
    ventana.aplicar_preprocesado_gui()

    assert ventana.preprocesado is None
    assert not ventana.datos_listos_para_modelo

    pd.testing.assert_frame_equal(
        ventana.datos_entrenamiento, original_entrenamiento
    )
    pd.testing.assert_frame_equal(
        ventana.datos_test, original_test
    )

    # Tras el error se puede corregir y volver a aplicar.
    ventana.entrada_constante.setText("7")
    ventana.aplicar_preprocesado_gui()

    assert ventana.datos_listos_para_modelo
    assert ventana.preprocesado is not None

    ventana.combo_estrategia.setCurrentIndex(0)
    assert not ventana.entrada_constante.isEnabled()


def test_sin_nulos_no_obliga_a_preprocesar(ventana):
    ventana.datos["x"] = [
        1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0
    ]
    ventana.separar()

    assert ventana.datos_listos_para_modelo
    assert not ventana.boton_aplicar.isEnabled()
    assert ventana.preprocesado is None
    assert "No hay valores inexistentes" in ventana.etiqueta_faltantes.text()
