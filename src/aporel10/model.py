
import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score


class ErrorRegresion(ValueError):
    pass


def _validar_datos(datos, nombre_conjunto, entradas, salida):
    if not isinstance(datos, pd.DataFrame):
        raise ErrorRegresion(
            f"El conjunto de {nombre_conjunto} debe ser un DataFrame."
        )

    if len(datos) < 2:
        raise ErrorRegresion(
            f"El conjunto de {nombre_conjunto} necesita al menos 2 filas "
            "para calcular R²."
        )

    columnas = entradas + [salida]
    faltantes = [col for col in columnas if col not in datos.columns]

    if faltantes:
        raise ErrorRegresion(
            f"Faltan columnas en {nombre_conjunto}: {', '.join(faltantes)}."
        )

    no_numericas = [
        col for col in columnas if not is_numeric_dtype(datos[col])
    ]

    if no_numericas:
        raise ErrorRegresion(
            f"Las columnas de {nombre_conjunto} deben ser numéricas: "
            + ", ".join(no_numericas)
            + "."
        )

    con_nulos = [
        col for col in columnas if datos[col].isna().any()
    ]

    if con_nulos:
        raise ErrorRegresion(
            f"Hay valores inexistentes en {nombre_conjunto}: "
            + ", ".join(con_nulos) + "."
        )

    valores = datos[columnas].to_numpy(dtype=float)

    if not np.isfinite(valores).all():
        raise ErrorRegresion(
            f"Hay valores infinitos o no válidos en {nombre_conjunto}."
        )


def generar_formula(modelo, entradas, salida, decimales=4):
    if not isinstance(decimales, int) or decimales < 0:
        raise ErrorRegresion(
            "El número de decimales debe ser un entero no negativo."
        )

    if len(modelo.coef_) != len(entradas):
        raise ErrorRegresion(
            "Las columnas no coinciden con los coeficientes del modelo."
        )

    formula = f"{salida} = "

    for i, (columna, coeficiente) in enumerate(
        zip(entradas, modelo.coef_)
    ):
        valor = float(coeficiente)
        negativo = (
            valor < 0 and round(abs(valor), decimales) != 0
        )

        if i == 0:
            signo = "- " if negativo else ""
        else:
            signo = " - " if negativo else " + "

        formula += (
            f"{signo}{abs(valor):.{decimales}f} * {columna}"
        )

    intercepto = float(modelo.intercept_)
    negativo = (
        intercepto < 0
        and round(abs(intercepto), decimales) != 0
    )

    signo = " - " if negativo else " + "
    formula += f"{signo}{abs(intercepto):.{decimales}f}"

    return formula


def calcular_metricas(reales, predichos):
    return {
        "r2": float(r2_score(reales, predichos)),
        "ecm": float(mean_squared_error(reales, predichos)),
    }


def preparar_grafico(
    modelo,
    entradas,
    salida,
    x_train,
    y_train,
    x_test,
    y_test,
    pred_train,
    pred_test,
):
    if len(entradas) == 1:
        minimo = min(
            float(x_train.iloc[:, 0].min()),
            float(x_test.iloc[:, 0].min()),
        )

        maximo = max(
            float(x_train.iloc[:, 0].max()),
            float(x_test.iloc[:, 0].max()),
        )

        linea_x = np.linspace(minimo, maximo, 100)
        linea_y = modelo.predict(
            pd.DataFrame({entradas[0]: linea_x})
        )

        return {
            "tipo": "simple",
            "eje_x": entradas[0],
            "eje_y": salida,
            "train_x": x_train.iloc[:, 0].to_numpy(),
            "train_y": y_train.to_numpy(),
            "test_x": x_test.iloc[:, 0].to_numpy(),
            "test_y": y_test.to_numpy(),
            "linea_x": linea_x,
            "linea_y": linea_y,
        }

    valores = np.concatenate((
        y_train.to_numpy(),
        y_test.to_numpy(),
        pred_train,
        pred_test,
    ))

    return {
        "tipo": "multiple",
        "train_real": y_train.to_numpy(),
        "train_predicho": pred_train,
        "test_real": y_test.to_numpy(),
        "test_predicho": pred_test,
        "linea_min": float(valores.min()),
        "linea_max": float(valores.max()),
    }


def entrenar_regresion_lineal(
    datos_entrenamiento,
    datos_test,
    entradas,
    salida,
    decimales=4,
):
    if not entradas:
        raise ErrorRegresion(
            "Debes seleccionar al menos una columna de entrada."
        )

    if len(set(entradas)) != len(entradas):
        raise ErrorRegresion(
            "No puede haber columnas de entrada repetidas."
        )

    if not salida or salida in entradas:
        raise ErrorRegresion(
            "Selecciona una salida distinta de las entradas."
        )

    _validar_datos(
        datos_entrenamiento, "entrenamiento", entradas, salida
    )
    _validar_datos(
        datos_test, "test", entradas, salida
    )

    x_train = datos_entrenamiento[entradas]
    y_train = datos_entrenamiento[salida]

    x_test = datos_test[entradas]
    y_test = datos_test[salida]

    try:
        modelo = LinearRegression()

        modelo.fit(x_train, y_train)

        pred_train = modelo.predict(x_train)
        pred_test = modelo.predict(x_test)

        if (
            not np.isfinite(pred_train).all()
            or not np.isfinite(pred_test).all()
        ):
            raise ErrorRegresion(
                "El modelo ha generado predicciones no válidas."
            )

        return {
            "modelo": modelo,
            "entradas": entradas.copy(),
            "salida": salida,
            "formula": generar_formula(
                modelo, entradas, salida, decimales
            ),
            "metricas": {
                "entrenamiento": calcular_metricas(
                    y_train, pred_train
                ),
                "test": calcular_metricas(
                    y_test, pred_test
                ),
            },
            "grafico": preparar_grafico(
                modelo,
                entradas,
                salida,
                x_train,
                y_train,
                x_test,
                y_test,
                pred_train,
                pred_test,
            ),
        }

    except (ValueError, TypeError, FloatingPointError) as exc:
        if isinstance(exc, ErrorRegresion):
            raise

        raise ErrorRegresion(
            f"No se ha podido entrenar el modelo: {exc}"
        ) from exc
