"""
Prueba de concepto de regresión lineal con scikit-learn.

Construye dos modelos sobre el dataset de ejemplo data/housing.csv:
uno simple (una columna de entrada) y otro múltiple (varias columnas).
Para cada uno muestra la fórmula, el ECM y el R² en entrenamiento y
test, y hace una predicción para un valor de entrada nuevo.

Ejecución desde la raíz del proyecto:
    uv run python prototipos/prueba_sklearn.py
"""

from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

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


def formula(modelo: LinearRegression, entradas: list[str]) -> str:
    """Devuelve la fórmula del modelo con los nombres de columnas."""
    coefs, independiente = modelo.coef_, modelo.intercept_
    texto = f"{SALIDA} = {coefs[0]:.4f} * {entradas[0]}"
    for coef, nombre in zip(coefs[1:], entradas[1:]):
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
    x_ent, y_ent = entrenamiento[entradas], entrenamiento[SALIDA]
    x_test, y_test = test[entradas], test[SALIDA]

    modelo = LinearRegression()
    modelo.fit(x_ent, y_ent)

    print("Fórmula:")
    print(f"  {formula(modelo, entradas)}")

    pred_ent = modelo.predict(x_ent)
    pred_test = modelo.predict(x_test)
    print(f"{'':14}{'ECM':>20}{'R²':>10}")
    print(f"{'Entrenamiento':14}{mean_squared_error(y_ent, pred_ent):>20,.2f}"
          f"{r2_score(y_ent, pred_ent):>10.4f}")
    print(f"{'Test':14}{mean_squared_error(y_test, pred_test):>20,.2f}"
          f"{r2_score(y_test, pred_test):>10.4f}")

    # Se pasa un DataFrame para conservar los nombres de las columnas.
    nuevo = pd.DataFrame([valor_nuevo], columns=entradas)
    print(f"Predicción para {valor_nuevo}:")
    print(f"  {SALIDA} = {modelo.predict(nuevo)[0]:,.2f}")


def main() -> None:
    datos = cargar_datos(RUTA_DATOS)
    entrenamiento, test = separar_datos(datos, porcentaje_test=20, semilla=42)
    print(f"Filas: {len(datos)} (entrenamiento {len(entrenamiento)}, "
          f"test {len(test)})")

    print("\n=== Regresión lineal simple (scikit-learn) ===")
    probar_modelo(entrenamiento, test, ENTRADAS_SIMPLE, {"median_income": 5.0})

    print("\n=== Regresión lineal múltiple (scikit-learn) ===")
    probar_modelo(entrenamiento, test, ENTRADAS_MULTIPLE, {
        "longitude": -122.25, "latitude": 37.85, "housing_median_age": 30.0,
        "total_rooms": 2000.0, "total_bedrooms": 400.0, "population": 1000.0,
        "households": 380.0, "median_income": 5.0,
    })


if __name__ == "__main__":
    main()
