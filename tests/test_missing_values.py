
"""Pruebas de detección, estrategias de tratamiento y casos de error."""

import numpy as np
import pandas as pd
import pytest

from aporel10.column_selector import validar_seleccion
from aporel10.missing_values import (
    ErrorPreprocesado,
    aplicar_preprocesado,
    detectar_valores_inexistentes,
    normalizar_columnas,
)


@pytest.fixture
def conjuntos():
    entrenamiento = pd.DataFrame({
        "x": [1.0, np.nan, 9.0],
        "y": [10.0, 20.0, np.nan],
        "ignorada": [np.nan, 2.0, 3.0],
    }, index=[11, 12, 13])
    test = pd.DataFrame({
        "x": [np.nan, 100.0],
        "y": [np.nan, 200.0],
        "ignorada": [4.0, np.nan],
    }, index=[21, 22])
    return entrenamiento, test


def test_detecta_nulos_y_vacios_solo_en_columnas_seleccionadas():
    datos = pd.DataFrame({
        "x": [1, np.nan, "", "   ", None],
        "y": [2, 3, 4, 5, 6],
        "otra": [None, None, None, None, None],
    })
    original = datos.copy(deep=True)

    assert detectar_valores_inexistentes(datos, ["x", "y"]) == {
        "x": 4, "y": 0,
    }
    pd.testing.assert_frame_equal(datos, original)


def test_recuento_independiente_para_entrenamiento_y_test(conjuntos):
    entrenamiento, test = conjuntos
    assert detectar_valores_inexistentes(entrenamiento, ["x", "y"]) == {
        "x": 1, "y": 1,
    }
    assert detectar_valores_inexistentes(test, ["x", "y"]) == {
        "x": 1, "y": 1,
    }


def test_sin_nulos_se_obtienen_ceros():
    datos = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
    assert detectar_valores_inexistentes(datos, ["x", "y"]) == {
        "x": 0, "y": 0,
    }


def test_normalizacion_con_numeros_en_texto_y_espacios():
    datos = pd.DataFrame({
        "x": [" 1.5 ", "", "  ", "3"],
        "y": [10, 20, 30, 40]
    })
    original = datos.copy(deep=True)
    normalizado = normalizar_columnas(datos, ["x"])

    assert normalizado["x"].iloc[0] == 1.5
    assert pd.isna(normalizado["x"].iloc[1])
    assert pd.isna(normalizado["x"].iloc[2])
    assert normalizado["x"].iloc[3] == 3.0
    pd.testing.assert_frame_equal(datos, original)
    validar_seleccion(datos, ["x"], "y")


def test_eliminar_filas_con_nulos_solo_en_columnas_elegidas(conjuntos):
    entrenamiento, test = conjuntos
    original_entrenamiento = entrenamiento.copy(deep=True)
    original_test = test.copy(deep=True)

    (entrenamiento_limpio, test_limpio,
     afectados_entrenamiento, afectados_test) = aplicar_preprocesado(
        entrenamiento, test, ["x", "y"], "eliminar")

    assert afectados_entrenamiento == 2
    assert afectados_test == 1
    assert entrenamiento_limpio.index.tolist() == [11]
    assert test_limpio.index.tolist() == [22]
    # El nulo de "ignorada" no supone eliminar la fila 22.
    assert pd.isna(test_limpio.loc[22, "ignorada"])
    pd.testing.assert_frame_equal(entrenamiento, original_entrenamiento)
    pd.testing.assert_frame_equal(test, original_test)


def test_eliminar_cuenta_filas_no_celdas():
    entrenamiento = pd.DataFrame({
        "x": [np.nan, 2],
        "y": [np.nan, 4]
    })
    test = pd.DataFrame({
        "x": [1, np.nan],
        "y": [2, np.nan]
    })
    (entrenamiento_limpio, test_limpio,
     afectados_entrenamiento, afectados_test) = aplicar_preprocesado(
        entrenamiento, test, ["x", "y"], "eliminar"
    )
    assert (afectados_entrenamiento, afectados_test) == (1, 1)


def test_media_entrenamiento_se_aplica_a_ambos_conjuntos(conjuntos):
    entrenamiento, test = conjuntos
    (entrenamiento_limpio, test_limpio,
     afectados_entrenamiento, afectados_test) = aplicar_preprocesado(
        entrenamiento, test, ["x", "y"], "media")

    assert entrenamiento_limpio.loc[12, "x"] == 5.0
    assert entrenamiento_limpio.loc[13, "y"] == 15.0
    assert test_limpio.loc[21, "x"] == 5.0
    assert test_limpio.loc[21, "y"] == 15.0
    assert (afectados_entrenamiento, afectados_test) == (2, 2)
    assert len(entrenamiento_limpio) == 3
    assert len(test_limpio) == 2


def test_mediana_entrenamiento_se_aplica_a_ambos_conjuntos():
    entrenamiento = pd.DataFrame({
        "x": [1, 2, 100, np.nan],
        "y": [10, 20, 30, 40]
    })
    test = pd.DataFrame({
        "x": [np.nan, 1000],
        "y": [50, 60]
    })
    (entrenamiento_limpio, test_limpio,
     afectados_entrenamiento, afectados_test) = aplicar_preprocesado(
        entrenamiento, test, ["x"], "mediana"
    )
    assert entrenamiento_limpio.loc[3, "x"] == 2.0
    assert test_limpio.loc[0, "x"] == 2.0
    assert afectados_entrenamiento == 1
    assert afectados_test == 1


@pytest.mark.parametrize(
    "constante, valor",
    [(0, 0.0), ("-2.5", -2.5), ("1,25", 1.25)]
)
def test_rellenar_con_valor_constante(conjuntos, constante, valor):
    entrenamiento, test = conjuntos
    (entrenamiento_limpio, test_limpio,
     afectados_entrenamiento, afectados_test) = aplicar_preprocesado(
        entrenamiento, test, ["x", "y"], "constante", constante
    )
    assert entrenamiento_limpio.loc[12, "x"] == valor
    assert test_limpio.loc[21, "y"] == valor
    assert (afectados_entrenamiento, afectados_test) == (2, 2)


@pytest.mark.parametrize(
    "constante",
    ["abc", "", None, True, "nan", "inf", "-inf"]
)
def test_constante_invalida_no_aplica_ningun_cambio(conjuntos, constante):
    entrenamiento, test = conjuntos
    antes_entrenamiento = entrenamiento.copy(deep=True)
    antes_test = test.copy(deep=True)

    with pytest.raises(ErrorPreprocesado, match="constante"):
        aplicar_preprocesado(
            entrenamiento, test, ["x", "y"], "constante", constante
        )

    pd.testing.assert_frame_equal(entrenamiento, antes_entrenamiento)
    pd.testing.assert_frame_equal(test, antes_test)


@pytest.mark.parametrize("estrategia", ["media", "mediana"])
def test_error_si_entrenamiento_no_contiene_datos_para_estadistica(estrategia):
    entrenamiento = pd.DataFrame({
        "x": [np.nan, np.nan],
        "y": [1, 2]
    })
    test = pd.DataFrame({
        "x": [6.0, np.nan],
        "y": [3, 4]
    })
    original = entrenamiento.copy(deep=True)

    with pytest.raises(ErrorPreprocesado, match="entrenamiento"):
        aplicar_preprocesado(entrenamiento, test, ["x"], estrategia)

    pd.testing.assert_frame_equal(entrenamiento, original)


@pytest.mark.parametrize("conjunto_vacio", ["entrenamiento", "test"])
def test_eliminacion_que_dejaria_vacio_un_conjunto_no_aplica(conjunto_vacio):
    entrenamiento = pd.DataFrame({
        "x": [1.0, 2.0],
        "y": [5.0, 6.0]
    })
    test = pd.DataFrame({
        "x": [1.0, 2.0],
        "y": [7.0, 8.0]
    })

    if conjunto_vacio == "entrenamiento":
        entrenamiento["x"] = np.nan
    else:
        test["x"] = np.nan

    original_entrenamiento = entrenamiento.copy(deep=True)
    original_test = test.copy(deep=True)

    with pytest.raises(ErrorPreprocesado, match="vacío"):
        aplicar_preprocesado(entrenamiento, test, ["x"], "eliminar")

    pd.testing.assert_frame_equal(entrenamiento, original_entrenamiento)
    pd.testing.assert_frame_equal(test, original_test)


def test_si_ya_no_hay_nulos_no_hace_cambios():
    entrenamiento = pd.DataFrame({
        "x": [1.0, 2.0],
        "y": [3.0, 4.0]
    })
    test = pd.DataFrame({
        "x": [5.0],
        "y": [6.0]
    })
    (entrenamiento_limpio, test_limpio,
     afectados_entrenamiento, afectados_test) = aplicar_preprocesado(
        entrenamiento, test, ["x", "y"], "media"
    )
    assert (afectados_entrenamiento, afectados_test) == (0, 0)
    pd.testing.assert_frame_equal(entrenamiento_limpio, entrenamiento)
    pd.testing.assert_frame_equal(test_limpio, test)


def test_no_trata_valores_inexistentes_de_columnas_no_seleccionadas(conjuntos):
    entrenamiento, test = conjuntos
    (entrenamiento_limpio, test_limpio,
     afectados_entrenamiento, afectados_test) = aplicar_preprocesado(
        entrenamiento, test, ["x"], "constante", 0
    )
    assert pd.isna(entrenamiento_limpio.loc[13, "y"])
    assert pd.isna(entrenamiento_limpio.loc[11, "ignorada"])
    assert pd.isna(test_limpio.loc[21, "y"])


@pytest.mark.parametrize("columnas", [[], ["no_existe"], ["x", "x"]])
def test_error_columnas_no_validas(conjuntos, columnas):
    entrenamiento, test = conjuntos
    with pytest.raises(ErrorPreprocesado):
        aplicar_preprocesado(entrenamiento, test, columnas, "media")


def test_error_estrategia_desconocida(conjuntos):
    entrenamiento, test = conjuntos
    with pytest.raises(ErrorPreprocesado, match="Estrategia desconocida"):
        aplicar_preprocesado(entrenamiento, test, ["x"], "moda")


def test_relleno_media_con_dtype_nullable_int():
    entrenamiento = pd.DataFrame({
        "x": pd.Series([1, pd.NA, 2], dtype="Int64")
    })
    test = pd.DataFrame({
        "x": pd.Series([pd.NA, 5], dtype="Int64")
    })
    (entrenamiento_limpio, test_limpio,
     afectados_entrenamiento, afectados_test) = aplicar_preprocesado(
        entrenamiento, test, ["x"], "media"
    )
    assert entrenamiento_limpio.loc[1, "x"] == 1.5
    assert test_limpio.loc[0, "x"] == 1.5


def test_nulos_solo_en_test_se_rellenan_con_entrenamiento():
    entrenamiento = pd.DataFrame({
        "x": [2.0, 4.0],
        "y": [1.0, 2.0]
    })
    test = pd.DataFrame({
        "x": [np.nan, 1000.0],
        "y": [3.0, 4.0]
    })
    (entrenamiento_limpio, test_limpio,
     afectados_entrenamiento, afectados_test) = aplicar_preprocesado(
        entrenamiento, test, ["x"], "media"
    )
    assert test_limpio.loc[0, "x"] == 3.0
    assert afectados_entrenamiento == 0
    assert afectados_test == 1


def test_no_se_modifica_el_archivo_original(tmp_path):
    ruta = tmp_path / "ejemplo.csv"
    pd.DataFrame({
        "x": [1, np.nan, 3, 4],
        "y": [2, 4, 6, 8]
    }).to_csv(ruta, index=False)

    contenido_original = ruta.read_bytes()
    datos = pd.read_csv(ruta)
    entrenamiento = datos.iloc[:2]
    test = datos.iloc[2:]

    aplicar_preprocesado(
        entrenamiento, test, ["x", "y"], "constante", 0
    )
    assert ruta.read_bytes() == contenido_original


def test_aplicar_preprocesado_devuelve_tupla():
    entrenamiento = pd.DataFrame({"x": [1.0, np.nan]})
    test = pd.DataFrame({"x": [np.nan, 2.0]})

    resultado = aplicar_preprocesado(
        entrenamiento, test, ["x"], "constante", 0
    )

    assert type(resultado) is tuple
    assert len(resultado) == 4
    assert isinstance(resultado[0], pd.DataFrame)
    assert isinstance(resultado[1], pd.DataFrame)
    assert resultado[2:] == (1, 1)
