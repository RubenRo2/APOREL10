"""
Prueba de concepto de regresión lineal con statsmodels.

Construye dos modelos sobre el dataset de ejemplo data/housing.csv:
uno simple (una columna de entrada) y otro múltiple (varias columnas).
Para cada uno muestra la fórmula, el ECM y el R² en entrenamiento y
test, y hace una predicción para un valor de entrada nuevo.

Ejecución desde la raíz del proyecto:
    uv run python prototipos/prueba_statsmodels.py
"""

from pathlib import Path

import pandas as pd
import statsmodels.api as sm
from statsmodels.tools.eval_measures import mse

from aporel10.data_loader import cargar_datos
from aporel10.data_splitter import separar_datos
from aporel10.missing_values import aplicar_preprocesado

RUTA_DATOS = Path(__file__).resolve().parents[1] / "data" / "housing.csv"
SALIDA = "median_house_value"
ENTRADAS_SIMPLE = ["median_income"]
ENTRADAS_MULTIPLE = [
    "longitude", "latitude", "housing_median_age", "total_rooms",
    "total_bedrooms", "population", "households", "median_income",
]


def r2(y_real: pd.Series, y_pred: pd.Series) -> float:
    """R² de un conjunto; statsmodels no lo ofrece para test."""
    residuos = ((y_real - y_pred) ** 2).sum()
    total = ((y_real - y_real.mean()) ** 2).sum()
    return 1 - residuos / total


def formula(resultado, entradas: list[str]) -> str:
    """Devuelve la fórmula del modelo con los nombres de columnas."""
    coefs = resultado.params[entradas]
    independiente = resultado.params["const"]
    texto = f"{SALIDA} = {coefs.iloc[0]:.4f} * {entradas[0]}"
    for coef, nombre in zip(coefs.iloc[1:], entradas[1:]):
        texto += f" {'-' if coef < 0 else '+'} {abs(coef):.4f} * {nombre}"
    signo = "-" if independiente < 0 else "+"
    return texto + f" {signo} {abs(independiente):.4f}"


def probar_modelo(
    entrenamiento: pd.DataFrame,
    test: pd.DataFrame,
    entradas: list[str],
    valor_nuevo: dict[str, float],
) -> None:
    """Entrena, muestra fórmula y métricas y predice un valor nuevo."""
    # Nulos: mediana de entrenamiento, aplicada también a test.
    entrenamiento, test, _, _ = aplicar_preprocesado(
        entrenamiento, test, entradas + [SALIDA], "mediana"
    )
    # statsmodels no añade el término independiente: hay que pedirlo.
    x_ent = sm.add_constant(entrenamiento[entradas])
    x_test = sm.add_constant(test[entradas])
    y_ent, y_test = entrenamiento[SALIDA], test[SALIDA]

    resultado = sm.OLS(y_ent, x_ent).fit()

    print("Fórmula:")
    print(f"  {formula(resultado, entradas)}")

    pred_ent = resultado.predict(x_ent)
    pred_test = resultado.predict(x_test)
    print(f"{'':14}{'ECM':>20}{'R²':>10}")
    print(f"{'Entrenamiento':14}{mse(y_ent, pred_ent):>20,.2f}"
          f"{resultado.rsquared:>10.4f}")
    print(f"{'Test':14}{mse(y_test, pred_test):>20,.2f}"
          f"{r2(y_test, pred_test):>10.4f}")
    print("p-valores de los coeficientes:")
    for nombre, p in resultado.pvalues.items():
        print(f"  {nombre:20} {p:.3g}")

    # has_constant="add" fuerza la constante aunque solo haya una fila.
    nuevo = sm.add_constant(
        pd.DataFrame([valor_nuevo], columns=entradas), has_constant="add"
    )
    print(f"Predicción para {valor_nuevo}:")
    print(f"  {SALIDA} = {resultado.predict(nuevo).iloc[0]:,.2f}")


def main() -> None:
    datos = cargar_datos(RUTA_DATOS)
    entrenamiento, test = separar_datos(datos, porcentaje_test=20, semilla=42)
    print(f"Filas: {len(datos)} (entrenamiento {len(entrenamiento)}, "
          f"test {len(test)})")

    print("\n=== Regresión lineal simple (statsmodels) ===")
    probar_modelo(entrenamiento, test, ENTRADAS_SIMPLE, {"median_income": 5.0})

    print("\n=== Regresión lineal múltiple (statsmodels) ===")
    probar_modelo(entrenamiento, test, ENTRADAS_MULTIPLE, {
        "longitude": -122.25, "latitude": 37.85, "housing_median_age": 30.0,
        "total_rooms": 2000.0, "total_bedrooms": 400.0, "population": 1000.0,
        "households": 380.0, "median_income": 5.0,
    })


if __name__ == "__main__":
    main()