"""Modulo para validar la selección de variables de entrada y salida"""

import pandas as pd

class ErrorSeleccionColumnas(Exception):
    """Excepcion lazada cuando la selección de columnas es invalida"""
    pass

def validar_seleccion(df: pd.DataFrame, entradas: list[str], salida: str) -> None:
    """Valida la selección de columnas para un modelo de regresión"""
    
    if not entradas:
        raise ErrorSeleccionColumnas(
            "Debe seleccionar al menos una columna de entrada (feature)"
            )
    if not salida:
            raise ErrorSeleccionColumnas(
                "Debe seleccionar al menos una columna de salida (target)"
                )
            
    if salida in entradas:
        raise ErrorSeleccionColumnas(
            f"La columna salida {salida} no puede estar también como entrada"
        )
        
    columnas_seleccionadas = entradas + [salida]
    
    #Comprueba las columas de entrada existen en el dataset, en caso contrario devuelve una excepción
    columnas_faltantes = [col for col in columnas_seleccionadas if col not in df.columns] 
    
    if columnas_faltantes:
        raise ErrorSeleccionColumnas(
            f"Columnas inexistentes en el dataset: {', '.join(columnas_faltantes)}"
        )
    
    columnas_no_numericas = [
        col for col in columnas_seleccionadas if not pd.api.types.is_numeric_dtype(df[col])
    ]
    
    # Comprueba si las columas son numéricas
    if columnas_no_numericas:
        raise ErrorSeleccionColumnas(
            "Solo se admiten columnas numéricas para regresión lineal/multiple. "
            f"Columnas inválidas: {', '.join(columnas_no_numericas)}"
        )