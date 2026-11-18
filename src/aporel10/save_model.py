"""Guardado de modelos entrenados en archivos Pickle (.pkl)."""

from pathlib import Path
import pickle
import platform

import numpy as np
import pandas as pd
import sklearn


EXTENSION_MODELO = ".pkl"
VERSION_ESQUEMA = 1


class ErrorGuardarModelo(Exception):
    """Error al validar o guardar un modelo"""


def validar_extension(ruta):
    """Devuelve la ruta asegurando que termina con la extensión .pkl."""
    if ruta is None or not str(ruta).strip():
        raise ErrorGuardarModelo(
            "La ruta de guardado no puede estar vacía"
        )

    ruta_path = Path(ruta)

    if ruta_path.suffix.lower() != EXTENSION_MODELO:
        ruta_path = ruta_path.with_name(
            f"{ruta_path.name}{EXTENSION_MODELO}"
        )

    return ruta_path


def construir_contenido_modelo(resultado_modelo):
    """Construye el diccionario serializable del modelo sin datos ni gráficos."""
    if not isinstance(resultado_modelo, dict):
        raise ErrorGuardarModelo(
            "El modelo a guardar debe ser un diccionario válido."
        )

    claves_obligatorias = (
        "modelo",
        "entradas",
        "salida",
        "formula",
        "metricas",
    )

    faltantes = [
        clave for clave in claves_obligatorias
        if clave not in resultado_modelo
    ]

    if faltantes:
        raise ErrorGuardarModelo(
            "Faltan campos obligatorios en el modelo: "
            + ", ".join(faltantes)
            + "."
        )

    modelo = resultado_modelo["modelo"]

    if not hasattr(modelo, "coef_") or not hasattr(modelo, "intercept_"):
        raise ErrorGuardarModelo(
            "El estimador no está entrenado o no tiene coeficientes válidos."
        )

    metricas = resultado_modelo["metricas"]
    if (
        not isinstance(metricas, dict)
        or "entrenamiento" not in metricas
        or "test" not in metricas
    ):
        raise ErrorGuardarModelo(
            "El modelo debe incluir métricas de entrenamiento y de test."
        )

    for conjunto in ("entrenamiento", "test"):
        datos_metricas = metricas[conjunto]
        if (
            not isinstance(datos_metricas, dict)
            or "r2" not in datos_metricas
            or "ecm" not in datos_metricas
        ):
            raise ErrorGuardarModelo(
                f"Las métricas de {conjunto} deben incluir 'r2' y 'ecm'."
            )

    descripcion = resultado_modelo.get("descripcion", "")

    if descripcion is None:
        descripcion = ""

    if not isinstance(descripcion, str):
        raise ErrorGuardarModelo(
            "La descripción del modelo debe ser una cadena de texto."
        )

    # Un modelo recuperado conserva su información original: el usuario solo
    # puede cambiar la descripción. No reescribimos el entorno de origen.
    if "_contenido_guardado" in resultado_modelo:
        original = resultado_modelo["_contenido_guardado"]
        if not isinstance(original, dict):
            raise ErrorGuardarModelo("Los metadatos originales no son válidos.")
        return {**original, "descripcion": descripcion}

    return {
        "version_esquema": VERSION_ESQUEMA,
        "modelo": modelo,
        "tipo_modelo": type(modelo).__name__,
        "coeficientes": [float(c) for c in np.ravel(modelo.coef_)],
        "intercepto": float(modelo.intercept_),
        "columnas_entrada": list(resultado_modelo["entradas"]),
        "columna_salida": str(resultado_modelo["salida"]),
        "formula": str(resultado_modelo["formula"]),
        "metricas_entrenamiento": {
            "r2": float(metricas["entrenamiento"]["r2"]),
            "ecm": float(metricas["entrenamiento"]["ecm"]),
        },
        "metricas_test": {
            "r2": float(metricas["test"]["r2"]),
            "ecm": float(metricas["test"]["ecm"]),
        },
        "descripcion": descripcion,
        "entorno": {
            "python": platform.python_version(),
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }


def guardar_modelo(resultado_modelo, ruta):
    """Guarda el modelo y sus metadatos en un archivo .pkl y devuelve la ruta."""
    ruta_destino = validar_extension(ruta)
    contenido = construir_contenido_modelo(resultado_modelo)

    try:
        with ruta_destino.open("wb") as archivo:
            pickle.dump(
                contenido,
                archivo,
                protocol=pickle.HIGHEST_PROTOCOL,
            )
    except (OSError, pickle.PicklingError, TypeError) as exc:
        raise ErrorGuardarModelo(
            f"No se pudo guardar el modelo en '{ruta_destino}': {exc}"
        ) from exc

    return ruta_destino
