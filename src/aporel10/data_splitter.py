"""Módulo para separar un dataset en conjuntos de entrenamiento y test."""

from numbers import Integral, Real

import pandas as pd

MIN_FILAS = 5


class ErrorSeparacionDatos(Exception):
    """Excepción lanzada cuando no se puede separar el dataset."""


def separar_datos(
    datos: pd.DataFrame,
    porcentaje_test: float = 20,
    semilla: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa el dataset en un conjunto de entrenamiento y otro de test.

    Las filas se reparten de forma aleatoria pero reproducible: con el mismo
    dataset, porcentaje y semilla se obtienen siempre los mismos conjuntos.

    Args:
        datos (pd.DataFrame): Dataset que se va a separar.
        porcentaje_test (float): Porcentaje de filas para el conjunto de
            test, entre 1 y 99. El resto va al de entrenamiento.
        semilla (int): Semilla de la separación aleatoria.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: Conjuntos de entrenamiento y test,
            en ese orden. Conservan el índice original de las filas.

    Raises:
        ErrorSeparacionDatos: Si el porcentaje no está entre 1 y 99, si la
            semilla no es un entero válido, si el dataset tiene menos de 5
            filas o si alguno de los conjuntos quedaría vacío.
    """
    if (isinstance(porcentaje_test, bool)
            or not isinstance(porcentaje_test, Real)
            or not 1 <= porcentaje_test <= 99):
        raise ErrorSeparacionDatos(
            "El porcentaje de test debe ser un número entre 1 y 99."
        )

    if isinstance(semilla, bool) or not isinstance(semilla, Integral):
        raise ErrorSeparacionDatos("La semilla debe ser un número entero.")

    # numpy solo acepta semillas entre [0, 2**32 - 1].
    if not 0 <= semilla < 2**32:
        raise ErrorSeparacionDatos(
            "La semilla debe ser un entero entre 0 y 4294967295."
        )

    if len(datos) < MIN_FILAS:
        raise ErrorSeparacionDatos(
            f"El dataset tiene {len(datos)} filas y se necesitan al menos "
            f"{MIN_FILAS} para separarlo."
        )

    n_test = round(len(datos) * porcentaje_test / 100)
    n_entrenamiento = len(datos) - n_test

    if n_test == 0:
        raise ErrorSeparacionDatos(
            f"Con un {porcentaje_test} % el conjunto de test quedaría vacío. "
            "Aumenta el porcentaje de test."
        )
    if n_entrenamiento == 0:
        raise ErrorSeparacionDatos(
            f"Con un {porcentaje_test} % el conjunto de entrenamiento quedaría "
            "vacío. Reduce el porcentaje de test."
        )

    # Garantiza que ninguna fila termine termine en ambos conjuntos
    mezclados = datos.sample(frac=1, random_state=semilla)
    test = mezclados.iloc[:n_test]
    entrenamiento = mezclados.iloc[n_test:]
    return entrenamiento, test


