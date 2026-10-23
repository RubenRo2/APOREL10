"""Pruebas unitarias para la validación de selección de columnas."""

import pandas as pd
import pytest

from aporel10.column_selector import ErrorSeleccionColumnas, validar_seleccion


@pytest.fixture
def df_prueba() -> pd.DataFrame:
    """Crea un dataset inventado solo para las pruebas."""
    return pd.DataFrame({
        "edad": [25, 30, 35],
        "salario": [2000.5, 3000.0, 4000.5],
        "departamento": ["Ventas", "IT", "RRHH"],  # <-- Columna de texto (inválida)
        "experiencia": [2, 5, 8]
    })
    

def test_seleccion_valida(df_prueba):
    """Comprueba que una selección correcta no da ningún error."""
    validar_seleccion(df_prueba, entradas=["edad", "salario"], salida="experiencia")
    validar_seleccion(df_prueba, entradas=["experiencia"], salida="edad")
    

def test_error_falta_entrada(df_prueba):
    """Verifica que salta error si no mandamos entradas."""
    with pytest.raises(ErrorSeleccionColumnas, match="entrada"):
        validar_seleccion(df_prueba, entradas=[], salida="experiencia")
        

def test_error_falta_salida(df_prueba):
    """Verifica que salta error si no mandamos salida."""
    with pytest.raises(ErrorSeleccionColumnas, match="salida"):
        validar_seleccion(df_prueba, entradas=["edad"], salida="")
        

def test_error_salida_en_entrada(df_prueba):
    """Verifica que salte error si intentan usar la salida como entrada."""
    with pytest.raises(ErrorSeleccionColumnas, match="también como entrada"):
        validar_seleccion(df_prueba, entradas=["edad"], salida="edad")
            
    with pytest.raises(ErrorSeleccionColumnas, match="también como entrada"):
        validar_seleccion(df_prueba, entradas=["edad", "salario"], salida="edad")


def test_error_columna_inexistente(df_prueba):
    """Verifica que salte error si la columna no existe en los datos."""
    with pytest.raises(ErrorSeleccionColumnas, match="Columnas inexistentes"):
        validar_seleccion(df_prueba, entradas=["edad"], salida="nose_algo")


def test_error_columna_no_numerica(df_prueba):
    """Verifica que salte error al usar texto (departamento) en la regresión."""
    with pytest.raises(ErrorSeleccionColumnas, match="Solo se admiten columnas numéricas"):
        validar_seleccion(df_prueba, entradas=["edad", "departamento"], salida="salario")