
"""Prueba de concepto de persistencia de modelos: pickle, joblib y JSON.

Ejecutar desde la raiz del repositorio:
    python prototipos/persistencia_regresion.py housing.csv

IMPORTANTE: cargar archivos .pkl o .joblib de origen desconocido es inseguro.
Este prototipo solo recupera archivos que acaba de generar localmente.
"""

import json
import pickle
import platform
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


COLUMNA_OBJETIVO = "median_house_value"
VERSION_ESQUEMA = 1
CARPETA_MODELOS = Path(__file__).resolve().parent / "modelos_guardados"


def calcular_metricas(y_real, y_pred):
    mse = mean_squared_error(y_real, y_pred)
    return {
        "mae": float(mean_absolute_error(y_real, y_pred)),
        "mse": float(mse),
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2_score(y_real, y_pred)),
    }


def entrenar_modelo(ruta_csv):
    datos = pd.read_csv(ruta_csv)

    # Para esta prueba usamos solo predictores numericos.
    columnas_entrada = [
        col for col in datos.select_dtypes(include="number").columns
        if col != COLUMNA_OBJETIVO
    ]
    if not columnas_entrada or COLUMNA_OBJETIVO not in datos.columns:
        raise ValueError("El CSV no contiene las columnas esperadas")

    x = datos[columnas_entrada]
    y = datos[COLUMNA_OBJETIVO]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
    )

    # El imputador se ajusta solo con los datos de entrenamiento.
    modelo = Pipeline([
        ("imputacion", SimpleImputer(strategy="median")),
        ("regresion", LinearRegression()),
    ])
    modelo.fit(x_train, y_train)

    regresion = modelo.named_steps["regresion"]
    formula = f"{COLUMNA_OBJETIVO} = {regresion.intercept_:.10g}"
    formula += "".join(
        f" {coef:+.10g} * {columna}"
        for columna, coef in zip(columnas_entrada, regresion.coef_)
    )

    contenido = {
        "version_esquema": VERSION_ESQUEMA,
        "modelo": modelo,  # Objeto real entrenado de scikit-learn.
        "tipo_modelo": "Pipeline(SimpleImputer, LinearRegression)",
        "columnas_entrada": columnas_entrada,
        "columna_salida": COLUMNA_OBJETIVO,
        "formula": formula,
        "metricas_entrenamiento": calcular_metricas(
            y_train, modelo.predict(x_train)
        ),
        "metricas_test": calcular_metricas(y_test, modelo.predict(x_test)),
        "descripcion": "Regresion lineal del valor mediano de viviendas de California.",
        "preprocesamiento": "Imputacion de medianas aprendidas en entrenamiento",
        "entrenamiento": {
            "filas_entrenamiento": int(len(x_train)),
            "filas_test": int(len(x_test)),
            "proporcion_test": 0.2,
            "semilla": 42,
            "columnas_excluidas": [
                col for col in datos.columns
                if col not in columnas_entrada + [COLUMNA_OBJETIVO]
            ],
        },
        "entorno": {
            "python": platform.python_version(),
            "scikit_learn": sklearn.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
    }
    return contenido, x_test


def guardar_pickle(contenido, ruta):
    with ruta.open("wb") as archivo:
        pickle.dump(contenido, archivo, protocol=pickle.HIGHEST_PROTOCOL)


def cargar_pickle(ruta):
    # Solo usar con archivos de origen confiable. La validacion posterior
    # NO impide la ejecucion de codigo que pueda ocurrir en pickle.load.
    with ruta.open("rb") as archivo:
        contenido = pickle.load(archivo)

    campos = {
        "version_esquema", "modelo", "tipo_modelo", "columnas_entrada",
        "columna_salida", "formula", "metricas_entrenamiento",
        "metricas_test", "descripcion", "preprocesamiento",
        "entrenamiento", "entorno",
    }
    if not isinstance(contenido, dict) or not campos.issubset(contenido):
        raise ValueError("Estructura del archivo de modelo no valida")
    if contenido["version_esquema"] != VERSION_ESQUEMA:
        raise ValueError("Version del esquema no compatible")
    if not isinstance(contenido["modelo"], Pipeline):
        raise ValueError("El objeto recuperado no es un Pipeline")
    return contenido


def guardar_json_comparativo(contenido, ruta):
    """JSON solo con parametros y metadatos; NO incluye el objeto modelo."""
    modelo = contenido["modelo"]
    regresion = modelo.named_steps["regresion"]
    imputacion = modelo.named_steps["imputacion"]
    representacion = {
        clave: valor for clave, valor in contenido.items() if clave != "modelo"
    }
    representacion["coeficientes"] = [float(c) for c in regresion.coef_]
    representacion["intercepto"] = float(regresion.intercept_)
    representacion["medianas_imputacion"] = {
        columna: float(mediana)
        for columna, mediana in zip(
            contenido["columnas_entrada"], imputacion.statistics_
        )
    }
    with ruta.open("w", encoding="utf-8") as archivo:
        json.dump(representacion, archivo, ensure_ascii=False, indent=2,
                  allow_nan=False)


def predecir_desde_json(ruta, x):
    """Reproduce predicciones con operaciones numericas, no carga el modelo."""
    with ruta.open("r", encoding="utf-8") as archivo:
        info = json.load(archivo)
    columnas = info["columnas_entrada"]
    x_limpio = x[columnas].fillna(info["medianas_imputacion"])
    coeficientes = np.asarray(info["coeficientes"], dtype=float)
    return x_limpio.to_numpy(dtype=float) @ coeficientes + info["intercepto"]


def main():
    ruta_csv = (
        Path(sys.argv[1]) if len(sys.argv) > 1
        else Path(__file__).resolve().parents[1] / "housing.csv"
    )
    CARPETA_MODELOS.mkdir(parents=True, exist_ok=True)

    contenido_original, x_test = entrenar_modelo(ruta_csv)
    ruta_pickle = CARPETA_MODELOS / "modelo_regresion.pkl"
    ruta_joblib = CARPETA_MODELOS / "modelo_regresion.joblib"
    ruta_json = CARPETA_MODELOS / "modelo_regresion.json"

    guardar_pickle(contenido_original, ruta_pickle)
    joblib.dump(contenido_original, ruta_joblib)
    guardar_json_comparativo(contenido_original, ruta_json)

    # Se cargan solo los archivos generados por esta ejecucion.
    contenido_cargado = cargar_pickle(ruta_pickle)
    contenido_joblib = joblib.load(ruta_joblib)

    pred_original = contenido_original["modelo"].predict(x_test)
    pred_pickle = contenido_cargado["modelo"].predict(x_test)
    pred_joblib = contenido_joblib["modelo"].predict(x_test)
    pred_json = predecir_desde_json(ruta_json, x_test)

    for nombre, prediccion in (
        ("pickle", pred_pickle),
        ("joblib", pred_joblib),
        ("json (parametros)", pred_json),
    ):
        np.testing.assert_allclose(pred_original, prediccion,
                                   rtol=1e-12, atol=1e-8)
        print(f"Predicciones equivalentes con {nombre}: SI")

    for nombre, ruta in (
        ("pickle", ruta_pickle), ("joblib", ruta_joblib),
        ("json", ruta_json),
    ):
        print(f"Archivo {nombre}: {ruta.stat().st_size} bytes")

    print("\nInformacion recuperada del archivo .pkl:")
    for campo in (
        "tipo_modelo", "descripcion", "columnas_entrada",
        "columna_salida", "formula", "metricas_entrenamiento",
        "metricas_test", "preprocesamiento", "entorno",
    ):
        print(f"{campo}: {contenido_cargado[campo]}")
    print("Primeras 3 predicciones:", pred_pickle[:3].tolist())


if __name__ == "__main__":
    main()
