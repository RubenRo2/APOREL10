"""Pruebas del módulo de regresión, sin ficheros externos ni interfaz."""

import numpy as np
import pandas as pd
import pytest

from aporel10.model import (
    ErrorRegresion,
    actualizar_descripcion,
    entrenar_regresion_lineal,
    formatear_prediccion,
    generar_formula,
    interpretar_valores_prediccion,
    predecir_modelo,
)


def test_regresion_simple_ajusta_solo_entrenamiento():
    entrenamiento = pd.DataFrame({
        "x": [0., 1., 2., 3.],
        "y": [1., 3., 5., 7.],
    })
    test = pd.DataFrame({
        "x": [4., 5.],
        "y": [9., 12.],
    })

    resultado = entrenar_regresion_lineal(
        entrenamiento, test, ["x"], "y"
    )

    assert resultado["modelo"].coef_[0] == pytest.approx(2.)
    assert resultado["modelo"].intercept_ == pytest.approx(1.)
    assert resultado["formula"] == "y = 2.0000 * x + 1.0000"

    assert resultado["metricas"]["entrenamiento"]["r2"] == pytest.approx(1.)
    assert resultado["metricas"]["entrenamiento"]["ecm"] == pytest.approx(0.)
    assert resultado["metricas"]["test"]["ecm"] == pytest.approx(0.5)
    assert resultado["metricas"]["test"]["r2"] == pytest.approx(7 / 9)

    assert resultado["grafico"]["tipo"] == "simple"
    assert len(resultado["grafico"]["linea_x"]) == 100
    assert len(resultado["grafico"]["test_y"]) == len(test)


def test_regresion_multiple_con_coeficiente_negativo():
    entrenamiento = pd.DataFrame({
        "a": [0., 0., 1., 1., 2., 2.],
        "b": [0., 1., 0., 1., 0., 1.],
    })

    entrenamiento["salida"] = (
        10 - 2 * entrenamiento["a"] + 3 * entrenamiento["b"]
    )

    test = pd.DataFrame({
        "a": [3., 4.],
        "b": [1., 0.],
        "salida": [7., 2.],
    })

    resultado = entrenar_regresion_lineal(
        entrenamiento,
        test,
        ["a", "b"],
        "salida",
        decimales=2,
    )

    assert resultado["formula"] == (
        "salida = - 2.00 * a + 3.00 * b + 10.00"
    )
    assert "+ -" not in resultado["formula"]

    assert resultado["metricas"]["entrenamiento"]["r2"] == pytest.approx(1.)
    assert resultado["metricas"]["test"]["r2"] == pytest.approx(1.)
    assert resultado["metricas"]["test"]["ecm"] == pytest.approx(0.)

    assert resultado["grafico"]["tipo"] == "multiple"

    np.testing.assert_allclose(
        resultado["grafico"]["test_real"], [7., 2.]
    )
    np.testing.assert_allclose(
        resultado["grafico"]["test_predicho"], [7., 2.]
    )


def test_formula_con_intercepto_negativo():
    entrenamiento = pd.DataFrame({
        "x": [0., 1., 2., 3.],
        "y": [-5., -9., -13., -17.],
    })

    test = pd.DataFrame({
        "x": [4., 5.],
        "y": [-21., -25.],
    })

    resultado = entrenar_regresion_lineal(
        entrenamiento, test, ["x"], "y", decimales=2
    )

    assert resultado["formula"] == "y = - 4.00 * x - 5.00"
    assert "+ -" not in resultado["formula"]


@pytest.mark.parametrize("conjunto,columna", [
    ("entrenamiento", "x"),
    ("test", "y"),
])
def test_rechaza_valores_inexistentes(conjunto, columna):
    entrenamiento = pd.DataFrame({
        "x": [1., 2., 3.],
        "y": [2., 4., 6.],
    })

    test = pd.DataFrame({
        "x": [4., 5.],
        "y": [8., 10.],
    })

    datos = (
        entrenamiento
        if conjunto == "entrenamiento"
        else test
    )
    datos.loc[datos.index[0], columna] = np.nan

    with pytest.raises(ErrorRegresion, match=conjunto):
        entrenar_regresion_lineal(
            entrenamiento, test, ["x"], "y"
        )


def test_rechaza_columnas_no_numericas():
    entrenamiento = pd.DataFrame({
        "x": ["a", "b", "c"],
        "y": [1, 2, 3],
    })

    test = pd.DataFrame({
        "x": ["d", "e"],
        "y": [4, 5],
    })

    with pytest.raises(ErrorRegresion, match="numéricas"):
        entrenar_regresion_lineal(
            entrenamiento, test, ["x"], "y"
        )


def test_rechaza_infinitos():
    entrenamiento = pd.DataFrame({
        "x": [1., np.inf, 3.],
        "y": [2., 4., 6.],
    })

    test = pd.DataFrame({
        "x": [4., 5.],
        "y": [8., 10.],
    })

    with pytest.raises(ErrorRegresion, match="infinitos"):
        entrenar_regresion_lineal(
            entrenamiento, test, ["x"], "y"
        )


def test_rechaza_entradas_vacias_duplicadas_y_salida_como_entrada():
    entrenamiento = pd.DataFrame({
        "x": [1., 2., 3.],
        "y": [2., 4., 6.],
    })

    test = pd.DataFrame({
        "x": [4., 5.],
        "y": [8., 10.],
    })

    casos = (
        ([], "y"),
        (["x", "x"], "y"),
        (["y"], "y"),
    )

    for entradas, salida in casos:
        with pytest.raises(ErrorRegresion):
            entrenar_regresion_lineal(
                entrenamiento, test, entradas, salida
            )


def test_rechaza_conjuntos_con_menos_de_dos_filas():
    entrenamiento = pd.DataFrame({
        "x": [1., 2., 3.],
        "y": [2., 4., 6.],
    })

    test = pd.DataFrame({
        "x": [4.],
        "y": [8.],
    })

    with pytest.raises(ErrorRegresion, match="al menos 2 filas"):
        entrenar_regresion_lineal(
            entrenamiento, test, ["x"], "y"
        )


def test_formula_rechaza_numero_de_columnas_incorrecto():
    entrenamiento = pd.DataFrame({
        "x": [0., 1., 2.],
        "y": [1., 3., 5.],
    })

    test = pd.DataFrame({
        "x": [3., 4.],
        "y": [7., 9.],
    })

    resultado = entrenar_regresion_lineal(
        entrenamiento, test, ["x"], "y"
    )

    with pytest.raises(ErrorRegresion, match="coeficientes"):
        generar_formula(
            resultado["modelo"],
            ["x", "otro"],
            "y",
        )


def _entrenar_modelo_simple():
    entrenamiento = pd.DataFrame({
        "x": [0., 1., 2., 3.],
        "y": [1., 3., 5., 7.],
    })
    test = pd.DataFrame({
        "x": [4., 5.],
        "y": [9., 11.],
    })

    return entrenar_regresion_lineal(entrenamiento, test, ["x"], "y")


def test_modelo_nuevo_se_crea_con_descripcion_vacia():
    resultado = _entrenar_modelo_simple()

    assert resultado["descripcion"] == ""


def test_descripcion_se_guarda_en_el_modelo():
    resultado = _entrenar_modelo_simple()

    actualizar_descripcion(resultado, "Predice y a partir de x.")

    assert resultado["descripcion"] == "Predice y a partir de x."


def test_descripcion_refleja_cada_cambio():
    resultado = _entrenar_modelo_simple()

    actualizar_descripcion(resultado, "Primera versión")
    actualizar_descripcion(resultado, "Primera versión\ncorregida")

    assert resultado["descripcion"] == "Primera versión\ncorregida"


def test_modelo_nuevo_no_hereda_la_descripcion_anterior():
    anterior = _entrenar_modelo_simple()
    actualizar_descripcion(anterior, "Modelo anterior")

    nuevo = _entrenar_modelo_simple()

    assert nuevo["descripcion"] == ""
    assert anterior["descripcion"] == "Modelo anterior"


def test_descripcion_rechaza_modelo_inexistente_y_no_texto():
    with pytest.raises(ErrorRegresion, match="ningún modelo"):
        actualizar_descripcion(None, "Texto")

    with pytest.raises(ErrorRegresion, match="texto"):
        actualizar_descripcion(_entrenar_modelo_simple(), 123)


# --- Predicción ---

def _modelo_para_predecir():
    """Modelo entrenado con datos inventados (no siguen una recta exacta)."""
    entrenamiento = pd.DataFrame({
        "a": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "b": [2.0, 1.0, 4.0, 3.0, 6.0, 5.0],
        "y": [5.1, 4.2, 11.3, 9.7, 16.4, 13.9],
    })
    test = pd.DataFrame({"a": [7.0, 8.0], "b": [8.0, 7.0],
                         "y": [21.5, 18.0]})
    return entrenar_regresion_lineal(entrenamiento, test, ["a", "b"], "y")


def test_prediccion_coincide_con_el_calculo_a_mano():
    resultado = _modelo_para_predecir()
    modelo = resultado["modelo"]
    c1, c2 = modelo.coef_
    esperado = c1 * 2.5 + c2 * (-1.0) + modelo.intercept_

    prediccion = predecir_modelo(resultado, {"a": 2.5, "b": -1.0})

    assert prediccion == pytest.approx(esperado)


def test_prediccion_con_entradas_a_cero_es_el_termino_independiente():
    resultado = _modelo_para_predecir()

    prediccion = predecir_modelo(resultado, {"a": 0.0, "b": 0.0})

    assert prediccion == pytest.approx(resultado["modelo"].intercept_)


@pytest.mark.parametrize("texto, esperado", [
    ("3.5", 3.5), ("3,5", 3.5), (" -2 ", -2.0),
])
def test_acepta_punto_o_coma_como_separador_decimal(texto, esperado):
    valores = interpretar_valores_prediccion(["a", "b"],
                                             {"a": texto, "b": "0"})

    assert valores["a"] == esperado


def test_error_indica_las_variables_que_faltan():
    with pytest.raises(ErrorRegresion, match="Faltan valores para: a, b"):
        interpretar_valores_prediccion(["a", "b"], {"a": " ", "b": ""})


def test_error_indica_la_variable_no_numerica():
    with pytest.raises(ErrorRegresion, match="no son números válidos: b"):
        interpretar_valores_prediccion(["a", "b"], {"a": "1", "b": "dos"})


def test_formato_del_resultado_con_los_decimales_de_la_formula():
    assert formatear_prediccion("y", 12.345678) == "y = 12.3457"