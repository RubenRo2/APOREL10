# Elección de la librería para la regresión lineal

## 1. Pruebas y comparativa

El equipo ha investigado tres opciones: **scikit-learn**, **statsmodels** y **numpy**. numpy se descartó al inicio
porque no tiene un modelo que se entrene y luego prediga, ni métricas de error. Con las otras dos hemos realizado
 una prueba de concepto:

| Aspecto evaluado | Con scikit-learn | Con statsmodels |
| :--- | :--- | :--- |
| **Uso y documentación** | **Excelente.** Muchos ejemplos para principiantes. | **Correcta.** Más técnica. |
| **Regresión simple y múltiple** | Soportadas sin problemas. | **Trabajo extra:** `add_constant` a mano. |
| **Obtener la fórmula** | Directa con `coef_` e `intercept_`. | Directa con `params`, con nombres. |
| **Métricas de error** | **Completa.** ECM y R² para cualquier conjunto. | **Incompleta.** Sin R² de test. |
| **Instalación con uv** | `uv add scikit-learn` | `uv add statsmodels` |

## 2. Librería seleccionada y justificación

**Librería elegida:** scikit-learn.

**¿Por qué?**
Las dos librerías obtuvieron exactamente los mismos resultados, así que la decisión se ha basado en la facilidad de
uso. Se ha descartado statsmodels porque obliga a hacer a mano pasos que scikit-learn ya resuelve, como añadir el
término independiente o calcular el R² de test. Sus análisis estadísticos avanzados no los necesita el proyecto.

Se ha seleccionado scikit-learn porque permite crear, entrenar y evaluar un modelo con muy pocas líneas de código y
su documentación está pensada para principiantes. Ha quedado añadida al proyecto con `uv add scikit-learn`.

## 3. Prueba de concepto: pasos, resultados e interpretación

Los scripts están en `prototipos/` (`prueba_sklearn.py` y `prueba_statsmodels.py`) y siguen los mismos pasos:

1. **Carga de datos:** `data/housing.csv` (20 640 filas) con el módulo de importación de la historia #10.
2. **Separación:** 80 % entrenamiento (16 512 filas) y 20 % test (4 128 filas).
3. **Valores nulos:** se rellenan con la mediana del conjunto de entrenamiento.
4. **Entrenamiento:** para predecir `median_house_value`, un modelo **simple** (solo `median_income`) y otro
   **múltiple** (las 8 columnas numéricas).
5. **Evaluación:** fórmula del modelo, ECM y R² en entrenamiento y test, y predicción de un valor nuevo.

| Modelo | ECM entrenamiento | ECM test | R² entrenamiento | R² test |
| :--- | ---: | ---: | ---: | ---: |
| **Simple** | 6 991 447 170 | 7 091 157 772 | 0,48 | 0,46 |
| **Múltiple** | 4 811 134 398 | 5 059 656 033 | 0,64 | 0,61 |

Fórmula del modelo simple: `median_house_value = 41933.8494 * median_income + 44459.7292`. Con un ingreso medio
de 5, predice un valor de vivienda de **254 129**.

**Interpretación:**

- **Coeficientes:** cada unidad más de ingreso medio sube el valor de la vivienda unos 41 934. El término
  independiente es lo que predice el modelo cuando la entrada vale 0.
- **ECM:** es el error al cuadrado, por eso es tan grande. Su raíz da un error típico en test de unos 84 000
  (simple) y 71 000 (múltiple).
- **R²:** el modelo simple explica cerca de la mitad de la variación de los precios y el múltiple algo más del 60 %.
- **Entrenamiento frente a test:** test sale algo peor porque son datos que el modelo no ha visto. Como la
  diferencia es pequeña, el modelo no ha memorizado los datos y funciona bien con datos nuevos.

## 4. Dificultades encontradas durante las pruebas y cómo se resolvieron

1. **Valores vacíos:** `total_bedrooms` tenía 207 huecos y ninguna librería entrena con ellos. Los rellenamos con
   la mediana usando el módulo de preprocesado del proyecto.
2. **Columna de texto:** `ocean_proximity` no se puede usar directamente en una regresión lineal, así que la
   dejamos fuera de la prueba.
3. **Término independiente en statsmodels:** hubo que añadirlo a mano con `add_constant` y, al predecir un solo
   valor, con `has_constant="add"`. En scikit-learn no ocurrió, ya que lo calcula automáticamente.
4. **R² de test en statsmodels:** como no lo calcula, tuvimos que programarlo. En scikit-learn basta con `r2_score`.