"""Recuperación y validación de modelos Pickle guardados por APOREL10.
"""

import pickle
from pathlib import Path

import numpy as np

from aporel10.save_model import EXTENSION_MODELO, VERSION_ESQUEMA


class ErrorCargarModelo(ValueError):
    """Archivo inaccesible, incompatible o con información incompleta."""


def _numero_finito(valor, campo):
    """Valida los valores numéricos de los metadatos."""
    if isinstance(valor, (bool, str, bytes)):
        raise ErrorCargarModelo(f"El campo '{campo}' debe ser numérico.")
    try:
        numero = float(valor)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ErrorCargarModelo(
            f"El campo '{campo}' debe ser numérico."
        ) from exc
    if not np.isfinite(numero):
        raise ErrorCargarModelo(f"El campo '{campo}' no es finito.")
    return numero


def validar_contenido_modelo(contenido):
    """Comprueba que un .pkl incluye un modelo entrenado y sus metadatos."""
    if not isinstance(contenido, dict):
        raise ErrorCargarModelo(
            "El archivo no contiene un modelo APOREL10 válido."
        )

    obligatorios = (
        "version_esquema", "modelo", "tipo_modelo", "coeficientes",
        "intercepto", "columnas_entrada", "columna_salida", "formula",
        "metricas_entrenamiento", "metricas_test", "descripcion", "entorno",
    )
    faltantes = [clave for clave in obligatorios if clave not in contenido]
    if faltantes:
        raise ErrorCargarModelo(
            "Falta información obligatoria del modelo: "
            + ", ".join(faltantes) + "."
        )

    if type(contenido["version_esquema"]) is not int or (
        contenido["version_esquema"] != VERSION_ESQUEMA
    ):
        raise ErrorCargarModelo(
            "La versión del formato de modelo no es compatible."
        )

    entradas = contenido["columnas_entrada"]
    salida = contenido["columna_salida"]
    if (
        not isinstance(entradas, list)
        or not entradas
        or any(not isinstance(c, str) or not c.strip() for c in entradas)
        or len(set(entradas)) != len(entradas)
        or not isinstance(salida, str)
        or not salida.strip()
        or salida in entradas
    ):
        raise ErrorCargarModelo("Las columnas del modelo no son válidas.")

    if not isinstance(contenido["formula"], str) or not contenido["formula"].strip():
        raise ErrorCargarModelo("La fórmula del modelo no es válida.")
    if not isinstance(contenido["descripcion"], str):
        raise ErrorCargarModelo("La descripción del modelo debe ser texto.")

    entorno = contenido["entorno"]
    if not isinstance(entorno, dict) or not all(
        isinstance(entorno.get(campo), str)
        for campo in ("python", "scikit_learn", "numpy", "pandas")
    ):
        raise ErrorCargarModelo("Falta información del entorno del modelo.")

    for conjunto in ("entrenamiento", "test"):
        metricas = contenido[f"metricas_{conjunto}"]
        if not isinstance(metricas, dict) or not {"r2", "ecm"} <= metricas.keys():
            raise ErrorCargarModelo(f"Faltan métricas de {conjunto}.")
        _numero_finito(metricas["r2"], f"r2 de {conjunto}")
        ecm = _numero_finito(metricas["ecm"], f"ecm de {conjunto}")
        if ecm < 0:
            raise ErrorCargarModelo(f"El ECM de {conjunto} no es válido.")

    modelo = contenido["modelo"]
    if (
        not callable(getattr(modelo, "predict", None))
        or not hasattr(modelo, "coef_")
        or not hasattr(modelo, "intercept_")
        or contenido["tipo_modelo"] != type(modelo).__name__
    ):
        raise ErrorCargarModelo("El estimador no es válido o no está entrenado.")

    try:
        coeficientes = np.asarray(contenido["coeficientes"], dtype=float)
        coef_modelo = np.asarray(modelo.coef_, dtype=float).ravel()
        intercepto = _numero_finito(contenido["intercepto"], "intercepto")
        intercepto_modelo = _numero_finito(
            modelo.intercept_, "intercepto del estimador"
        )
    except (ValueError, TypeError, OverflowError) as exc:
        raise ErrorCargarModelo(
            "Los coeficientes del modelo son inválidos."
        ) from exc

    if (
        coeficientes.ndim != 1
        or len(coeficientes) != len(entradas)
        or len(coef_modelo) != len(entradas)
        or not np.isfinite(coeficientes).all()
        or not np.isfinite(coef_modelo).all()
        or not np.allclose(coeficientes, coef_modelo)
        or not np.isclose(intercepto, intercepto_modelo)
    ):
        raise ErrorCargarModelo(
            "Los coeficientes no coinciden con las columnas o el estimador."
        )
    if getattr(modelo, "n_features_in_", len(entradas)) != len(entradas):
        raise ErrorCargarModelo("El estimador no coincide con las entradas.")


def cargar_modelo(ruta):
    """Carga un .pkl y devuelve el resultado en el formato utilizado por la GUI.

    Incluye el contenido original para que un guardado posterior conserve los
    metadatos y cambie exclusivamente la descripción.
    """
    if ruta is None or not str(ruta).strip():
        raise ErrorCargarModelo("Debes seleccionar un archivo de modelo.")

    ruta_archivo = Path(ruta)
    if ruta_archivo.suffix.lower() != EXTENSION_MODELO:
        raise ErrorCargarModelo(
            f"El archivo debe tener extensión {EXTENSION_MODELO}."
        )

    try:
        with ruta_archivo.open("rb") as archivo:
            contenido = pickle.load(archivo)
    except Exception as exc:
        raise ErrorCargarModelo(
            f"No se pudo leer el archivo de modelo '{ruta_archivo}': {exc}"
        ) from exc

    try:
        validar_contenido_modelo(contenido)
    except ErrorCargarModelo:
        raise
    except Exception as exc:
        raise ErrorCargarModelo(
            "El archivo contiene información de modelo incompatible."
        ) from exc

    return {
        "modelo": contenido["modelo"],
        "entradas": contenido["columnas_entrada"].copy(),
        "salida": contenido["columna_salida"],
        "formula": contenido["formula"],
        "metricas": {
            "entrenamiento": contenido["metricas_entrenamiento"].copy(),
            "test": contenido["metricas_test"].copy(),
        },
        "descripcion": contenido["descripcion"],
        "_contenido_guardado": contenido,
    }