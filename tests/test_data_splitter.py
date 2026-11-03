"""Pruebas unitarias para la separación en entrenamiento y test."""

import numpy as np
import pandas as pd
import pytest

from aporel10.data_splitter import ErrorSeparacionDatos, separar_datos


@pytest.fixture
def df_prueba() -> pd.DataFrame:
    """Crea un dataset inventado de 100 filas solo para las pruebas."""
    return pd.DataFrame({
        "x": range(100),
        "y": [valor * 2.5 for valor in range(100)],
    })


def df_con_filas(n: int) -> pd.DataFrame:
    """Crea un dataset con el número de filas indicado."""
    return pd.DataFrame({"x": range(n), "y": range(n)})


# 1. Tamaños de los conjuntos 

def test_tamanos_por_defecto(df_prueba):
    """Sin indicar nada, separa un 80 % para entrenamiento y un 20 % para test."""
    entrenamiento, test = separar_datos(df_prueba)

    assert len(entrenamiento) == 80
    assert len(test) == 20


@pytest.mark.parametrize("porcentaje, n_entrenamiento, n_test", [
    (20, 80, 20),
    (30, 70, 30),
    (1, 99, 1),
    (99, 1, 99),
    (12.5, 88, 12),
])
def test_tamanos_segun_porcentaje(df_prueba, porcentaje, n_entrenamiento, n_test):
    """Los tamaños corresponden al porcentaje de test indicado."""
    entrenamiento, test = separar_datos(df_prueba, porcentaje_test=porcentaje)

    assert len(entrenamiento) == n_entrenamiento
    assert len(test) == n_test


def test_minimo_de_filas_admitido():
    """Con exactamente 5 filas la separación se realiza."""
    entrenamiento, test = separar_datos(df_con_filas(5), porcentaje_test=20)

    assert len(entrenamiento) == 4
    assert len(test) == 1


# 2. Contenido de los conjuntos ---

def test_ninguna_fila_en_los_dos_conjuntos(df_prueba):
    """Ninguna fila aparece a la vez en entrenamiento y en test."""
    entrenamiento, test = separar_datos(df_prueba)

    assert entrenamiento.index.intersection(test.index).empty


def test_no_se_pierde_ninguna_fila(df_prueba):
    """Entre los dos conjuntos están todas las filas del dataset original."""
    entrenamiento, test = separar_datos(df_prueba)

    juntos = pd.concat([entrenamiento, test]).sort_index()
    pd.testing.assert_frame_equal(juntos, df_prueba)


def test_conserva_las_columnas(df_prueba):
    """Los dos conjuntos tienen las mismas columnas que el dataset original."""
    entrenamiento, test = separar_datos(df_prueba)

    assert list(entrenamiento.columns) == ["x", "y"]
    assert list(test.columns) == ["x", "y"]


def test_no_modifica_el_dataset_original(df_prueba):
    """La separación no cambia el DataFrame que recibe."""
    copia = df_prueba.copy()

    separar_datos(df_prueba)

    pd.testing.assert_frame_equal(df_prueba, copia)


# 3. Reproducibilidad ---

def test_misma_semilla_misma_separacion(df_prueba):
    """Con el mismo dataset, porcentaje y semilla se obtienen los mismos conjuntos."""
    entrenamiento_1, test_1 = separar_datos(df_prueba, 20, semilla=7)
    entrenamiento_2, test_2 = separar_datos(df_prueba, 20, semilla=7)

    pd.testing.assert_frame_equal(entrenamiento_1, entrenamiento_2)
    pd.testing.assert_frame_equal(test_1, test_2)


def test_distinta_semilla_distinta_separacion(df_prueba):
    """Con otra semilla las filas se reparten de otra forma."""
    _, test_1 = separar_datos(df_prueba, 20, semilla=1)
    _, test_2 = separar_datos(df_prueba, 20, semilla=2)

    assert set(test_1.index) != set(test_2.index)


def test_la_separacion_es_aleatoria(df_prueba):
    """El test no son simplemente las primeras filas del archivo."""
    _, test = separar_datos(df_prueba)

    assert list(test.index) != list(range(20))


@pytest.mark.parametrize("semilla", [0, 2**32 - 1, np.int64(5)])
def test_semillas_validas_en_los_limites(df_prueba, semilla):
    """Se aceptan las semillas de los extremos y los enteros de numpy."""
    entrenamiento, test = separar_datos(df_prueba, semilla=semilla)

    assert len(entrenamiento) == 80
    assert len(test) == 20


# 4. Errores ---

@pytest.mark.parametrize("porcentaje", [
    0, 100, -5, 0.5, 99.5, float("nan"), "20", None, True,
])
def test_error_porcentaje_no_valido(df_prueba, porcentaje):
    """El porcentaje tiene que ser un número entre 1 y 99."""
    with pytest.raises(ErrorSeparacionDatos, match="entre 1 y 99"):
        separar_datos(df_prueba, porcentaje_test=porcentaje)


@pytest.mark.parametrize("semilla", [3.5, "42", None, True])
def test_error_semilla_no_entera(df_prueba, semilla):
    """La semilla tiene que ser un número entero."""
    with pytest.raises(ErrorSeparacionDatos, match="número entero"):
        separar_datos(df_prueba, semilla=semilla)


@pytest.mark.parametrize("semilla", [-1, 2**32])
def test_error_semilla_fuera_de_rango(df_prueba, semilla):
    """La semilla tiene que estar en el rango que admite numpy."""
    with pytest.raises(ErrorSeparacionDatos, match="entre 0 y"):
        separar_datos(df_prueba, semilla=semilla)


@pytest.mark.parametrize("n_filas", [0, 1, 4])
def test_error_menos_de_5_filas(n_filas):
    """Un dataset con menos de 5 filas no se puede separar."""
    with pytest.raises(ErrorSeparacionDatos, match="al menos 5"):
        separar_datos(df_con_filas(n_filas))


def test_error_test_quedaria_vacio():
    """Con 5 filas y un 1 % el conjunto de test se quedaría sin filas."""
    with pytest.raises(ErrorSeparacionDatos, match="test quedaría vacío"):
        separar_datos(df_con_filas(5), porcentaje_test=1)


def test_error_entrenamiento_quedaria_vacio():
    """Con 5 filas y un 99 % el conjunto de entrenamiento se quedaría sin filas."""
    with pytest.raises(ErrorSeparacionDatos, match="entrenamiento quedaría vacío"):
        separar_datos(df_con_filas(5), porcentaje_test=99)