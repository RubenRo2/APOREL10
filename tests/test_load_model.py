"""Pruebas de la carga de modelos guardados, sin ficheros externos ni interfaz."""

import pickle

import pandas as pd
import pytest

from aporel10.load_model import ErrorCargarModelo, cargar_modelo
from aporel10.model import (
    actualizar_descripcion,
    entrenar_regresion_lineal,
    predecir_modelo,
)
from aporel10.save_model import guardar_modelo


@pytest.fixture
def resultado():
    """Modelo entrenado con datos escritos en la propia prueba."""
    entrenamiento = pd.DataFrame({
        "a": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "b": [2.0, 1.0, 4.0, 3.0, 6.0, 5.0],
        "y": [5.1, 4.2, 11.3, 9.7, 16.4, 13.9],
    })
    test = pd.DataFrame({"a": [7.0, 8.0], "b": [8.0, 7.0],
                         "y": [21.5, 18.0]})
    return entrenar_regresion_lineal(entrenamiento, test, ["a", "b"], "y")


def test_guardar_y_cargar_conserva_la_informacion(resultado, tmp_path):
    actualizar_descripcion(resultado, "Modelo de prueba")
    ruta = guardar_modelo(resultado, tmp_path / "modelo.pkl")

    cargado = cargar_modelo(ruta)

    assert cargado["entradas"] == ["a", "b"]
    assert cargado["salida"] == "y"
    assert cargado["formula"] == resultado["formula"]
    assert cargado["metricas"] == resultado["metricas"]
    assert cargado["descripcion"] == "Modelo de prueba"


def test_modelo_cargado_predice_igual_que_el_original(resultado, tmp_path):
    ruta = guardar_modelo(resultado, tmp_path / "modelo.pkl")
    cargado = cargar_modelo(ruta)
    valores = {"a": 3.7, "b": 12.25}

    assert (predecir_modelo(cargado, valores)
            == predecir_modelo(resultado, valores))


def test_conserva_una_descripcion_vacia(resultado, tmp_path):
    ruta = guardar_modelo(resultado, tmp_path / "modelo.pkl")

    assert cargar_modelo(ruta)["descripcion"] == ""


def test_modificar_la_descripcion_y_guardar_de_nuevo(resultado, tmp_path):
    ruta = guardar_modelo(resultado, tmp_path / "modelo.pkl")
    cargado = cargar_modelo(ruta)

    actualizar_descripcion(cargado, "Descripción nueva")
    guardar_modelo(cargado, ruta)
    recargado = cargar_modelo(ruta)

    assert recargado["descripcion"] == "Descripción nueva"
    assert (list(recargado["modelo"].coef_)
            == list(resultado["modelo"].coef_))
    assert recargado["entradas"] == resultado["entradas"]
    assert recargado["salida"] == resultado["salida"]
    assert recargado["formula"] == resultado["formula"]
    assert recargado["metricas"] == resultado["metricas"]


def test_ruta_con_espacios_tildes_y_enie(resultado, tmp_path):
    carpeta = tmp_path / "Modelos de año ñ"
    carpeta.mkdir()
    ruta = guardar_modelo(resultado, carpeta / "mi modelo.pkl")

    assert cargar_modelo(ruta)["salida"] == "y"


def test_error_si_el_archivo_esta_danado(tmp_path):
    ruta = tmp_path / "roto.pkl"
    ruta.write_bytes(b"esto no es un modelo")

    with pytest.raises(ErrorCargarModelo):
        cargar_modelo(ruta)


def test_error_si_falta_informacion_del_modelo(tmp_path):
    ruta = tmp_path / "incompleto.pkl"
    with ruta.open("wb") as archivo:
        pickle.dump({"modelo": None}, archivo)

    with pytest.raises(ErrorCargarModelo, match="Falta información"):
        cargar_modelo(ruta)


def test_error_si_el_archivo_no_existe(tmp_path):
    with pytest.raises(ErrorCargarModelo):
        cargar_modelo(tmp_path / "no_existe.pkl")


def test_error_si_la_extension_no_es_pkl(tmp_path):
    ruta = tmp_path / "modelo.json"
    ruta.write_text("{}", encoding="utf-8")

    with pytest.raises(ErrorCargarModelo, match="extensión"):
        cargar_modelo(ruta)
