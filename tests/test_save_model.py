"""Pruebas unitarias sobre el guardado del modelo"""

import pickle

import numpy as np
import pandas as pd
import pytest

from aporel10.model import entrenar_regresion_lineal
from aporel10.save_model import (
    EXTENSION_MODELO,
    VERSION_ESQUEMA,
    ErrorGuardarModelo,
    validar_extension,
    guardar_modelo,
)


def _crear_resultado_modelo(descripcion=None):
    train = pd.DataFrame({
        "x1": [1.0, 2.0, 3.0, 4.0, 5.0],
        "x2": [2.0, 1.0, 4.0, 3.0, 6.0],
        "y": [5.0, 6.0, 11.0, 12.0, 17.0],
    })
    test = pd.DataFrame({
        "x1": [6.0, 7.0],
        "x2": [5.0, 8.0],
        "y": [18.0, 23.0],
    })
    resultado = entrenar_regresion_lineal(train, test, ["x1", "x2"], "y")
    if descripcion is not None:
        resultado["descripcion"] = descripcion
    return resultado, test


def test_guardar_modelo_incluye_toda_la_informacion_y_predice(tmp_path):
    resultado, test = _crear_resultado_modelo("Modelo de prueba")
    ruta = tmp_path / "mi_modelo.pkl"

    ruta_guardada = guardar_modelo(resultado, ruta)

    assert ruta_guardada == ruta
    assert ruta_guardada.exists()

    with ruta_guardada.open("rb") as archivo:
        contenido = pickle.load(archivo)

    assert contenido["version_esquema"] == VERSION_ESQUEMA
    assert contenido["tipo_modelo"] == "LinearRegression"
    assert contenido["columnas_entrada"] == ["x1", "x2"]
    assert contenido["columna_salida"] == "y"
    assert contenido["formula"] == resultado["formula"]
    assert contenido["metricas_entrenamiento"] == (
        resultado["metricas"]["entrenamiento"]
    )
    assert contenido["metricas_test"] == resultado["metricas"]["test"]
    assert contenido["descripcion"] == "Modelo de prueba"
    assert len(contenido["coeficientes"]) == 2
    assert isinstance(contenido["intercepto"], float)
    assert {"python", "scikit_learn", "numpy", "pandas"}.issubset(
        contenido["entorno"]
    )

    pred_original = resultado["modelo"].predict(test[["x1", "x2"]])
    pred_cargada = contenido["modelo"].predict(test[["x1", "x2"]])
    np.testing.assert_allclose(pred_original, pred_cargada)


def test_guardar_modelo_no_incluye_datos_ni_graficos(tmp_path):
    resultado, _ = _crear_resultado_modelo("")

    resultado["datos_entrenamiento"] = pd.DataFrame({"x1": [1, 2]})
    resultado["datos_test"] = pd.DataFrame({"x1": [3, 4]})
    ruta = tmp_path / "sin_datos.pkl"

    guardar_modelo(resultado, ruta)

    with ruta.open("rb") as archivo:
        contenido = pickle.load(archivo)

    assert "grafico" not in contenido
    assert "datos_entrenamiento" not in contenido
    assert "datos_test" not in contenido
    assert not any(
        isinstance(valor, pd.DataFrame) for valor in contenido.values()
    )


def test_guardar_modelo_añade_extension_automaticamente(tmp_path):
    resultado, _ = _crear_resultado_modelo()
    ruta_sin_ext = tmp_path / "modelo_v1.0"

    ruta_guardada = guardar_modelo(resultado, ruta_sin_ext)

    assert ruta_guardada.name == f"modelo_v1.0{EXTENSION_MODELO}"
    assert ruta_guardada.exists()


def test_guardar_modelo_espacios_y_tildes(tmp_path):
    resultado, _ = _crear_resultado_modelo(
        "Descripción con ñ y tildes: Àprùébáñós pórfá")
    carpeta = tmp_path / "carpeta con espacios y año áéíóú"
    carpeta.mkdir()
    ruta = carpeta / "modelo_regresióñ.pkl"

    ruta_guardada = guardar_modelo(resultado, ruta)

    assert ruta_guardada.exists()
    with ruta_guardada.open("rb") as archivo:
        contenido = pickle.load(archivo)
    assert contenido["descripcion"] == "Descripción con ñ y tildes: Àprùébáñós pórfá"


def test_guardar_modelo_descripcion_vacia(tmp_path):
    resultado, _ = _crear_resultado_modelo()
    ruta = tmp_path / "sin_descripcion.pkl"

    guardar_modelo(resultado, ruta)

    with ruta.open("rb") as archivo:
        contenido = pickle.load(archivo)
    assert contenido["descripcion"] == ""


def test_guardar_modelo_ruta_invalida(tmp_path):
    resultado, _ = _crear_resultado_modelo()
    ruta_inexistente = tmp_path / "carpeta_que_no_existe" / "modelo.pkl"

    with pytest.raises(ErrorGuardarModelo):
        guardar_modelo(resultado, ruta_inexistente)


def test_guardar_modelo_incompleto(tmp_path):
    ruta = tmp_path / "invalido.pkl"

    with pytest.raises(ErrorGuardarModelo):
        guardar_modelo({"formula": "y = 2*x"}, ruta)


def test_validar_extension_rechaza_ruta_vacia():
    with pytest.raises(ErrorGuardarModelo):
        validar_extension("   ")
