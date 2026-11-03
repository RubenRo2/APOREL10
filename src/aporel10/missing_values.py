
"""Detección y tratamiento de valores inexistentes en datos de regresión."""

from math import isfinite

import pandas as pd


class ErrorPreprocesado(Exception):
    """Error al detectar o tratar valores inexistentes."""


def _validar_columnas(datos: pd.DataFrame, columnas: list[str]) -> None:
    """Comprueba que se haya elegido alguna columna y que todas existan."""
    if not columnas:
        raise ErrorPreprocesado("Debe seleccionar al menos una columna.")

    if len(columnas) != len(set(columnas)):
        raise ErrorPreprocesado("Hay columnas seleccionadas repetidas.")

    faltantes = [col for col in columnas if col not in datos.columns]
    if faltantes:
        raise ErrorPreprocesado(
            f"Columnas inexistentes: {', '.join(faltantes)}"
        )


def _marcar_vacios(serie: pd.Series) -> pd.Series:
    """Interpreta cadenas vacías o compuestas de espacios como valores nulos."""
    vacios = serie.map(
        lambda valor: isinstance(valor, str) and not valor.strip()
    )
    return serie.mask(vacios)


def detectar_valores_inexistentes(datos: pd.DataFrame, columnas: list[str]) -> dict[str, int]:
    """Cuenta NaN, None y celdas vacías por columna, sin modificar los datos."""
    _validar_columnas(datos, columnas)
    return {
        columna: int(_marcar_vacios(datos[columna]).isna().sum())
        for columna in columnas
    }


def normalizar_columnas(datos: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """Devuelve una copia con columnas seleccionadas numéricas y vacíos como NaN.

    Los textos numéricos son válidos, pero no se convierten textos arbitrarios
    en NaN silenciosamente: esos valores generan un error explícito.
    """
    _validar_columnas(datos, columnas)
    copia = datos.copy(deep=True)

    for columna in columnas:
        try:
            copia[columna] = pd.to_numeric(
                _marcar_vacios(copia[columna]), errors="raise"
            ).astype(float)
        except (ValueError, TypeError) as error:
            raise ErrorPreprocesado(
                f"La columna '{columna}' contiene valores no numéricos."
            ) from error     
    return copia


def _validar_constante(valor_constante: object) -> float:
    """Valida que el valor constante sea un número real y finito."""
    if isinstance(valor_constante, bool) or valor_constante is None:
        raise ErrorPreprocesado("El valor constante debe ser numérico.")
    
    try:
        if isinstance(valor_constante, str):
            valor_constante = valor_constante.strip().replace(",", ".")
        numero = float(valor_constante)
    except (ValueError, TypeError, OverflowError) as error:
        raise ErrorPreprocesado(
            "El valor constante debe ser numérico."
        ) from error
    
    if not isfinite(numero):
        raise ErrorPreprocesado("El valor constante debe ser un número finito.")
    return numero


def aplicar_preprocesado(
    entrenamiento: pd.DataFrame,test: pd.DataFrame,
    columnas: list[str],estrategia: str,valor_constante: object = None,
) -> tuple[pd.DataFrame, pd.DataFrame, int, int]:
    
    """Trata nulos de ambos conjuntos sin modificar los DataFrames recibidos.

    Estrategias: 'eliminar', 'media', 'mediana' y 'constante'. La media o
    mediana se calcula exclusivamente con entrenamiento y se aplica también
    a test. Los conteos representan filas para 'eliminar' y celdas para
    las estrategias de relleno. Se rechaza cualquier resultado vacío.

    Devuelve una tupla con entrenamiento limpio, test limpio, número de
    elementos afectados en entrenamiento y número de elementos afectados
    en test, en ese orden.
    """
    estrategias = {"eliminar", "media", "mediana", "constante"}
    if estrategia not in estrategias:
        raise ErrorPreprocesado(f"Estrategia desconocida: {estrategia!r}.")

    _validar_columnas(entrenamiento, columnas)
    _validar_columnas(test, columnas)
    if entrenamiento.empty or test.empty:
        raise ErrorPreprocesado(
            "Los conjuntos de entrenamiento y test no pueden estar vacíos."
        )

    constante = (
        _validar_constante(valor_constante)
        if estrategia == "constante" else None
    )

    entrenamiento_limpio = normalizar_columnas(entrenamiento, columnas)
    test_limpio = normalizar_columnas(test, columnas)

    if estrategia == "eliminar":
        entrenamiento_limpio = entrenamiento_limpio.dropna(subset=columnas)
        test_limpio = test_limpio.dropna(subset=columnas)
        if entrenamiento_limpio.empty or test_limpio.empty:
            raise ErrorPreprocesado(
                "Eliminar las filas con valores inexistentes dejaría vacío "
                "el conjunto de entrenamiento o el de test."
            )
        return (
            entrenamiento_limpio,
            test_limpio,
            len(entrenamiento) - len(entrenamiento_limpio),
            len(test) - len(test_limpio),
        )

    afectados_entrenamiento = int(entrenamiento_limpio[columnas].isna().sum().sum())
    afectados_test = int(test_limpio[columnas].isna().sum().sum())

    if estrategia == "constante":
        valores = {columna: constante for columna in columnas}
    else:
        valores = {}
        for columna in columnas:
            serie = entrenamiento_limpio[columna]
            if not serie.notna().any():
                raise ErrorPreprocesado(
                    f"No es posible calcular la {estrategia} de '{columna}' "
                    "con los valores del conjunto de entrenamiento."
                )
            valor = serie.mean() if estrategia == "media" else serie.median()
            if not isfinite(float(valor)):
                raise ErrorPreprocesado(
                    f"No es posible calcular la {estrategia} de '{columna}' "
                    "con los valores del conjunto de entrenamiento."
                )
            valores[columna] = valor

    entrenamiento_limpio[columnas] = (entrenamiento_limpio[columnas].fillna(value=valores))
    test_limpio[columnas] = test_limpio[columnas].fillna(value=valores)

    return (
        entrenamiento_limpio,
        test_limpio,
        afectados_entrenamiento,
        afectados_test,
    )
